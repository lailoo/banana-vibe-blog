"""
视频生成服务 - 基于 Veo3 API
将静态图片转换为动画视频
"""
import requests
import time
import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class VideoAspectRatio(Enum):
    """支持的视频比例"""
    LANDSCAPE_16_9 = "16:9"
    PORTRAIT_9_16 = "9:16"


class VideoStatus(Enum):
    """任务状态"""
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class VideoResult:
    """视频生成结果"""
    url: str
    local_path: Optional[str] = None
    task_id: Optional[str] = None


class Veo3Service:
    """Veo3 视频生成服务"""

    SUPPORTED_MODELS = [
        "veo3.1-fast",
        "veo3.1-pro"
    ]

    @staticmethod
    def get_default_animation_prompt() -> str:
        """获取默认动画提示词（从 Jinja2 模板加载）"""
        from services.blog_generator.prompts.prompt_manager import get_prompt_manager
        return get_prompt_manager().render_cover_video_prompt()

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://grsai.dakka.com.cn",
        model: str = "veo3.1-fast",
        output_folder: str = "outputs/videos"
    ):
        """
        初始化视频生成服务

        Args:
            api_key: API 密钥
            api_base: API 基础 URL
            model: 默认使用的模型
            output_folder: 视频输出目录
        """
        self.api_key = api_key
        self.api_base = api_base.rstrip('/')
        self.model = model
        self.output_folder = output_folder
        
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        })
        
        # 确保输出目录存在
        Path(output_folder).mkdir(parents=True, exist_ok=True)

    def is_available(self) -> bool:
        """检查服务是否可用"""
        return bool(self.api_key)

    def generate_from_image(
        self,
        image_url: str,
        prompt: Optional[str] = None,
        aspect_ratio: VideoAspectRatio = VideoAspectRatio.LANDSCAPE_16_9,
        model: Optional[str] = None,
        download: bool = True,
        max_wait_time: int = 600,
        progress_callback: callable = None
    ) -> Optional[VideoResult]:
        """
        从图片生成动画视频

        Args:
            image_url: 首帧图片 URL
            prompt: 动画提示词（可选，默认使用信息图动画提示词）
            aspect_ratio: 视频比例
            model: 模型名称（可选）
            download: 是否下载到本地
            max_wait_time: 最大等待时间（秒）
            progress_callback: 进度回调函数 callback(progress: int, status: str)

        Returns:
            VideoResult 或 None
        """
        try:
            use_model = model or self.model
            use_prompt = prompt or self.get_default_animation_prompt()
            
            logger.info(f"开始生成视频: {image_url[:80]}...")
            
            # 提交任务
            result = self._create_video_task(
                model=use_model,
                prompt=use_prompt,
                first_frame_url=image_url,
                aspect_ratio=aspect_ratio
            )
            
            # 检查 API 返回
            if result.get('code') != 0:
                logger.error(f"API 返回错误: {result}")
                return None
            
            data = result.get('data') or {}
            task_id = data.get('id')
            if not task_id:
                logger.error(f"未获取到任务ID: {result}")
                return None
            
            logger.info(f"视频任务已提交: {task_id}")
            
            # 等待完成
            final_result = self._wait_for_completion(
                task_id, 
                max_wait_time,
                progress_callback=progress_callback
            )
            
            # 获取视频 URL
            video_data = final_result.get('data', {})
            video_url = video_data.get('url')
            if not video_url:
                logger.error("未获取到视频 URL")
                return None
            
            logger.info(f"视频生成成功: {video_url}")
            
            # 下载视频
            local_path = None
            if download:
                local_path = self._download_video(video_url)
            
            return VideoResult(
                url=video_url,
                local_path=local_path,
                task_id=task_id
            )
            
        except Exception as e:
            logger.error(f"视频生成失败: {e}", exc_info=True)
            return None

    def _create_video_task(
        self,
        model: str,
        prompt: str,
        first_frame_url: str,
        aspect_ratio: VideoAspectRatio = VideoAspectRatio.LANDSCAPE_16_9
    ) -> Dict[str, Any]:
        """创建视频生成任务"""
        if model not in self.SUPPORTED_MODELS:
            raise ValueError(f"不支持的模型: {model}. 支持的模型: {self.SUPPORTED_MODELS}")

        request_body = {
            "model": model,
            "prompt": prompt,
            "firstFrameUrl": first_frame_url,
            "aspectRatio": aspect_ratio.value,
            "webHook": "-1",  # 使用轮询方式
            "shutProgress": False
        }

        url = f"{self.api_base}/v1/video/veo"
        try:
            response = self.session.post(url, json=request_body, timeout=30)
            response.raise_for_status()
            result = response.json()
            if result is None:
                logger.error("API 返回空响应")
                return {}
            return result
        except requests.exceptions.Timeout:
            logger.error(f"API 请求超时: {url}")
            return {}
        except requests.exceptions.RequestException as e:
            logger.error(f"API 请求失败: {e}")
            return {}

    def _get_result(self, task_id: str) -> Dict[str, Any]:
        """获取任务结果"""
        url = f"{self.api_base}/v1/draw/result"
        response = self.session.post(url, json={"id": task_id})
        response.raise_for_status()
        return response.json()

    def _wait_for_completion(
        self,
        task_id: str,
        max_wait_time: int = 600,
        poll_interval: int = 5,
        progress_callback: callable = None
    ) -> Dict[str, Any]:
        """等待任务完成"""
        start_time = time.time()
        last_progress = -1

        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                raise TimeoutError(f"任务等待超时 (超过 {max_wait_time} 秒)")

            result = self._get_result(task_id)

            if result.get('code') == 0:
                data = result.get('data', {})
                status = data.get('status')
                progress = data.get('progress', 0)

                if progress != last_progress:
                    logger.info(f"视频任务进度: {progress}%")
                    last_progress = progress
                    
                    # 调用进度回调
                    if progress_callback:
                        try:
                            progress_callback(progress, status)
                        except Exception as e:
                            logger.warning(f"进度回调失败: {e}")

                if status == VideoStatus.SUCCEEDED.value:
                    return result
                elif status == VideoStatus.FAILED.value:
                    raise RuntimeError(
                        f"视频任务失败: {data.get('failure_reason')} - {data.get('error')}"
                    )
            elif result.get('code') == -22:
                raise RuntimeError(f"任务不存在: {task_id}")

            time.sleep(poll_interval)

    def _download_video(self, video_url: str) -> str:
        """下载视频到本地"""
        # 从 URL 提取文件名
        filename = video_url.split('/')[-1].split('?')[0]
        if not filename or '.' not in filename:
            filename = f"video_{int(time.time())}.mp4"

        file_path = os.path.join(self.output_folder, filename)

        response = requests.get(video_url, timeout=120, stream=True)
        response.raise_for_status()

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        file_size = os.path.getsize(file_path)
        logger.info(f"视频已保存: {file_path} (大小: {file_size / 1024 / 1024:.2f}MB)")
        return file_path


# 全局服务实例
_video_service: Optional[Veo3Service] = None


def get_video_service() -> Optional[Veo3Service]:
    """获取全局视频生成服务实例"""
    return _video_service


def init_video_service(config: dict) -> Optional[Veo3Service]:
    """
    从配置初始化视频生成服务

    Args:
        config: Flask app.config 字典

    Returns:
        Veo3Service 实例或 None
    """
    global _video_service
    
    # 复用图片服务的 API Key
    api_key = config.get('NANO_BANANA_API_KEY', '')
    if not api_key:
        logger.warning("未配置 NANO_BANANA_API_KEY，视频生成服务不可用")
        return None
    
    # 视频输出目录
    output_folder = config.get('VIDEO_OUTPUT_FOLDER', '')
    if not output_folder:
        base_output = config.get('OUTPUT_FOLDER', 'outputs')
        output_folder = os.path.join(base_output, 'videos')
    
    _video_service = Veo3Service(
        api_key=api_key,
        api_base=config.get('NANO_BANANA_API_BASE', 'https://grsai.dakka.com.cn'),
        model=config.get('VEO3_MODEL', 'veo3.1-fast'),
        output_folder=output_folder
    )
    
    logger.info(f"视频生成服务已初始化: model={_video_service.model}")
    return _video_service
