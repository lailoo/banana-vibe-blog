"""
Skills - 专业化能力模块

通过 LangChain tool 模式提供按需加载的技能提示词。
"""

from .skill_loader import SkillLoader, get_skill_loader, load_skill

__all__ = ["SkillLoader", "get_skill_loader", "load_skill"]

