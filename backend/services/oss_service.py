"""
阿里云 OSS 服务 - 用于上传图片获取公网 URL

Veo3 视频生成 API 需要公网可访问的图片 URL，
本服务将本地图片上传到 OSS 并返回公网 URL。
"""
import os
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class OSSService:
    """阿里云 OSS 服务"""
    
    def __init__(
        self,
        access_key_id: str = None,
        access_key_secret: str = None,
        bucket_name: str = None,
        endpoint: str = None
    ):
        """
        初始化 OSS 服务
        
        Args:
            access_key_id: 阿里云 AccessKey ID
            access_key_secret: 阿里云 AccessKey Secret
            bucket_name: OSS Bucket 名称
            endpoint: OSS Endpoint (如 oss-cn-hangzhou.aliyuncs.com)
        """
        self.access_key_id = access_key_id or os.getenv('OSS_ACCESS_KEY_ID')
        self.access_key_secret = access_key_secret or os.getenv('OSS_ACCESS_KEY_SECRET')
        self.bucket_name = bucket_name or os.getenv('OSS_BUCKET_NAME')
        self.endpoint = endpoint or os.getenv('OSS_ENDPOINT', 'oss-cn-hangzhou.aliyuncs.com')
        
        self._bucket = None
        self._initialized = False
        
        if not all([self.access_key_id, self.access_key_secret, self.bucket_name]):
            logger.warning("OSS 配置不完整，上传功能将不可用")
        else:
            self._init_client()
    
    def _init_client(self):
        """初始化 OSS 客户端"""
        try:
            import oss2
            
            auth = oss2.Auth(self.access_key_id, self.access_key_secret)
            self._bucket = oss2.Bucket(auth, self.endpoint, self.bucket_name)
            self._initialized = True
            logger.info(f"OSS 客户端初始化成功: {self.bucket_name}")
            
        except ImportError:
            logger.error("oss2 未安装，请运行: pip install oss2")
            self._initialized = False
        except Exception as e:
            logger.error(f"OSS 客户端初始化失败: {e}")
            self._initialized = False
    
    @property
    def is_available(self) -> bool:
        """检查 OSS 服务是否可用"""
        return self._initialized and self._bucket is not None
    
    def file_exists(self, remote_path: str) -> bool:
        """
        检查文件是否已存在于 OSS
        
        Args:
            remote_path: OSS 上的路径
            
        Returns:
            是否存在
        """
        if not self.is_available:
            return False
        
        try:
            return self._bucket.object_exists(remote_path)
        except Exception as e:
            logger.warning(f"检查文件是否存在失败: {e}")
            return False
    
    def upload_file(
        self,
        local_path: str,
        remote_path: str = None,
        content_type: str = None,
        skip_if_exists: bool = True
    ) -> Dict[str, Any]:
        """
        上传文件到 OSS
        
        Args:
            local_path: 本地文件路径
            remote_path: OSS 上的路径 (如 vibe-blog/covers/abc123/cover.png)
                        如果不指定，会自动生成
            content_type: 文件 MIME 类型
            skip_if_exists: 如果文件已存在，跳过上传直接返回 URL (默认 True)
            
        Returns:
            {
                'success': True,
                'url': 'https://bucket.oss-cn-hangzhou.aliyuncs.com/path/to/file.png',
                'remote_path': 'path/to/file.png',
                'skipped': True/False  # 是否跳过上传
            }
        """
        if not self.is_available:
            return {'success': False, 'error': 'OSS 服务不可用'}
        
        if not os.path.exists(local_path):
            return {'success': False, 'error': f'文件不存在: {local_path}'}
        
        try:
            import oss2
            
            # 生成远程路径
            if not remote_path:
                ext = os.path.splitext(local_path)[1]
                timestamp = datetime.now().strftime('%Y%m%d')
                unique_id = uuid.uuid4().hex[:8]
                filename = os.path.basename(local_path)
                remote_path = f"vibe-blog/images/{timestamp}/{unique_id}_{filename}"
            
            # 检查文件是否已存在
            if skip_if_exists and self.file_exists(remote_path):
                url = f"https://{self.bucket_name}.{self.endpoint}/{remote_path}"
                logger.info(f"文件已存在，跳过上传: {url}")
                return {
                    'success': True,
                    'url': url,
                    'remote_path': remote_path,
                    'skipped': True
                }
            
            # 设置 Content-Type
            headers = {}
            if content_type:
                headers['Content-Type'] = content_type
            elif local_path.lower().endswith('.png'):
                headers['Content-Type'] = 'image/png'
            elif local_path.lower().endswith(('.jpg', '.jpeg')):
                headers['Content-Type'] = 'image/jpeg'
            elif local_path.lower().endswith('.gif'):
                headers['Content-Type'] = 'image/gif'
            elif local_path.lower().endswith('.webp'):
                headers['Content-Type'] = 'image/webp'
            
            # 上传文件
            with open(local_path, 'rb') as f:
                result = self._bucket.put_object(remote_path, f, headers=headers)
            
            if result.status == 200:
                # 构建公网 URL
                url = f"https://{self.bucket_name}.{self.endpoint}/{remote_path}"
                logger.info(f"文件上传成功: {url}")
                return {
                    'success': True,
                    'url': url,
                    'remote_path': remote_path,
                    'skipped': False
                }
            else:
                return {'success': False, 'error': f'上传失败，状态码: {result.status}'}
                
        except Exception as e:
            logger.error(f"文件上传失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def upload_bytes(
        self,
        data: bytes,
        remote_path: str,
        content_type: str = 'image/png'
    ) -> Dict[str, Any]:
        """
        上传字节数据到 OSS
        
        Args:
            data: 文件字节数据
            remote_path: OSS 上的路径
            content_type: 文件 MIME 类型
            
        Returns:
            {'success': True, 'url': '...'}
        """
        if not self.is_available:
            return {'success': False, 'error': 'OSS 服务不可用'}
        
        try:
            headers = {'Content-Type': content_type}
            result = self._bucket.put_object(remote_path, data, headers=headers)
            
            if result.status == 200:
                url = f"https://{self.bucket_name}.{self.endpoint}/{remote_path}"
                logger.info(f"数据上传成功: {url}")
                return {
                    'success': True,
                    'url': url,
                    'remote_path': remote_path
                }
            else:
                return {'success': False, 'error': f'上传失败，状态码: {result.status}'}
                
        except Exception as e:
            logger.error(f"数据上传失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def delete_file(self, remote_path: str) -> bool:
        """
        删除 OSS 上的文件
        
        Args:
            remote_path: OSS 上的路径
            
        Returns:
            是否删除成功
        """
        if not self.is_available:
            return False
        
        try:
            self._bucket.delete_object(remote_path)
            logger.info(f"文件删除成功: {remote_path}")
            return True
        except Exception as e:
            logger.error(f"文件删除失败: {e}")
            return False
    
    def get_public_url(self, remote_path: str) -> str:
        """
        获取文件的公网 URL
        
        Args:
            remote_path: OSS 上的路径
            
        Returns:
            公网 URL
        """
        return f"https://{self.bucket_name}.{self.endpoint}/{remote_path}"


# 全局服务实例
_oss_service: Optional[OSSService] = None


def get_oss_service() -> Optional[OSSService]:
    """获取全局 OSS 服务实例"""
    return _oss_service


def init_oss_service(config: dict) -> Optional[OSSService]:
    """
    从配置初始化 OSS 服务
    
    Args:
        config: Flask app.config 字典
        
    Returns:
        OSSService 实例或 None
    """
    global _oss_service
    
    access_key_id = config.get('OSS_ACCESS_KEY_ID', '')
    access_key_secret = config.get('OSS_ACCESS_KEY_SECRET', '')
    bucket_name = config.get('OSS_BUCKET_NAME', '')
    
    if not all([access_key_id, access_key_secret, bucket_name]):
        logger.warning("OSS 配置不完整，OSS 服务不可用")
        return None
    
    _oss_service = OSSService(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        bucket_name=bucket_name,
        endpoint=config.get('OSS_ENDPOINT', 'oss-cn-hangzhou.aliyuncs.com')
    )
    
    if _oss_service.is_available:
        logger.info(f"OSS 服务已初始化: bucket={bucket_name}")
    
    return _oss_service
