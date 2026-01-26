"""
Skills - 专业化能力模块

Skills 是可按需加载的专业化 prompt 和逻辑,用于增强 Agent 的特定能力。
基于 LangChain Skills 模式(渐进式披露)实现。
"""

from .skill_loader import SkillLoader, get_skill_loader

__all__ = ["SkillLoader", "get_skill_loader"]
