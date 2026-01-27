"""
Skill Loader - Skills 加载器

使用 LangChain tool 实现 skills 的按需加载（progressive disclosure）。
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).resolve().parent

_FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


@dataclass(frozen=True)
class Skill:
    """Skill 定义（解析自 SKILL.md）。"""

    name: str
    description: str
    prompt: str
    metadata: Dict[str, Any]
    version: str = "1.0.0"


class SkillLoader:
    """
    Skills 加载器

    负责从 SKILL.md 解析技能并缓存结果。
    """

    def __init__(self, skills_dir: Path | None = None):
        self._skills_dir = skills_dir or SKILLS_DIR
        self._skills_cache: Dict[str, Skill] = {}

    def load_skill(self, skill_name: str) -> Optional[Skill]:
        """
        加载指定 skill。

        Args:
            skill_name: skill 名称（目录名），如 "humanizer"
        """
        if skill_name in self._skills_cache:
            return self._skills_cache[skill_name]

        skill_path = self._skills_dir / skill_name / "SKILL.md"
        if not skill_path.exists():
            logger.warning("Skill 不存在: %s", skill_path)
            return None

        skill = self._parse_skill_file(skill_path)
        if skill:
            self._skills_cache[skill_name] = skill
        return skill

    def get_skill_prompt(self, skill_name: str) -> Optional[str]:
        """获取 skill 的 prompt 内容。"""
        skill = self.load_skill(skill_name)
        return skill.prompt if skill else None

    def list_available_skills(self) -> list[str]:
        """列出可用 skills（基于目录扫描）。"""
        skills: list[str] = []
        for child in self._skills_dir.iterdir():
            if not child.is_dir():
                continue
            if (child / "SKILL.md").exists():
                skills.append(child.name)
        return sorted(skills)

    def clear_cache(self) -> None:
        """清空 skill 缓存。"""
        self._skills_cache.clear()

    def _parse_skill_file(self, skill_path: Path) -> Optional[Skill]:
        """解析 SKILL.md（包含 YAML front matter）。"""
        try:
            raw = skill_path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            logger.error("读取 skill 失败: %s", exc)
            return None

        match = _FRONT_MATTER_RE.match(raw)
        if not match:
            logger.error("Skill 缺少 front matter: %s", skill_path)
            return None

        front_matter, body = match.groups()
        try:
            meta = yaml.safe_load(front_matter) or {}
        except yaml.YAMLError as exc:
            logger.error("解析 front matter 失败: %s", exc)
            return None

        name = meta.get("name") or skill_path.parent.name
        description = meta.get("description", "")
        metadata = meta.get("metadata") or {}

        prompt = body.strip()

        return Skill(
            name=str(name),
            description=str(description),
            prompt=prompt,
            metadata=metadata,
        )


_skill_loader: Optional[SkillLoader] = None


def get_skill_loader() -> SkillLoader:
    """获取全局 SkillLoader 实例（单例）。"""
    global _skill_loader
    if _skill_loader is None:
        _skill_loader = SkillLoader()
    return _skill_loader


@tool
def load_skill(skill_name: str) -> str:
    """
    Load a specialized skill prompt by name.

    Available skills:
    - humanizer: 去除 AI 写作痕迹指南
    """

    loader = get_skill_loader()
    skill = loader.load_skill(skill_name)
    if not skill:
        available = ", ".join(loader.list_available_skills()) or "(none)"
        return f"Skill '{skill_name}' not found. Available: {available}"
    return skill.prompt

