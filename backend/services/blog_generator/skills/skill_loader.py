"""
Skill Loader - Skills 加载器

支持按需加载专业化 skills,实现渐进式披露模式。
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# 全局 skill loader 实例
_skill_loader: Optional["SkillLoader"] = None


class SkillLoader:
    """
    Skills 加载器

    负责动态加载和缓存 skills,支持:
    - 按需加载
    - 缓存机制
    - 错误处理
    """

    def __init__(self):
        """初始化 skill loader"""
        self._skills_cache: Dict[str, Any] = {}
        logger.info("SkillLoader 初始化完成")

    def load_skill(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """
        加载指定 skill

        Args:
            skill_name: skill 名称 (如 'humanizer')

        Returns:
            skill 配置字典,包含:
            - name: skill 名称
            - version: 版本号
            - description: 描述
            - prompt: skill prompt
            - detect_func: 检测函数 (可选)
            - rewrite_func: 改写函数 (可选)

            如果 skill 不存在,返回 None
        """
        # 检查缓存
        if skill_name in self._skills_cache:
            logger.debug(f"从缓存加载 skill: {skill_name}")
            return self._skills_cache[skill_name]

        # 动态导入 skill
        try:
            logger.info(f"加载 skill: {skill_name}")
            skill_module = __import__(
                f"services.blog_generator.skills.{skill_name}.skill",
                fromlist=["get_skill_config"],
            )

            if not hasattr(skill_module, "get_skill_config"):
                logger.error(f"Skill '{skill_name}' 缺少 get_skill_config 函数")
                return None

            skill_config = skill_module.get_skill_config()

            # 验证 skill 配置
            required_fields = ["name", "version", "description", "prompt"]
            for field in required_fields:
                if field not in skill_config:
                    logger.error(f"Skill '{skill_name}' 缺少必需字段: {field}")
                    return None

            # 缓存 skill
            self._skills_cache[skill_name] = skill_config
            logger.info(
                f"Skill '{skill_name}' 加载成功 (版本: {skill_config['version']})"
            )

            return skill_config

        except ImportError as e:
            logger.error(f"Skill '{skill_name}' 不存在: {e}")
            return None
        except Exception as e:
            logger.error(f"加载 skill '{skill_name}' 失败: {e}", exc_info=True)
            return None

    def get_skill_prompt(self, skill_name: str) -> Optional[str]:
        """
        获取 skill 的 prompt

        Args:
            skill_name: skill 名称

        Returns:
            skill prompt 字符串,如果 skill 不存在返回 None
        """
        skill = self.load_skill(skill_name)
        if skill:
            return skill.get("prompt")
        return None

    def list_available_skills(self) -> list:
        """
        列出所有可用的 skills

        Returns:
            skill 名称列表
        """
        # TODO: 实现自动发现机制
        return ["humanizer"]

    def clear_cache(self):
        """清空 skill 缓存"""
        self._skills_cache.clear()
        logger.info("Skill 缓存已清空")


def get_skill_loader() -> SkillLoader:
    """
    获取全局 skill loader 实例 (单例模式)

    Returns:
        SkillLoader 实例
    """
    global _skill_loader
    if _skill_loader is None:
        _skill_loader = SkillLoader()
    return _skill_loader
