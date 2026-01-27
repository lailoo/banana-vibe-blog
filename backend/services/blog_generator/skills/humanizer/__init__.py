"""
Humanizer Skill - 人性化写作技能
"""

from .skill import (
    detect_humanizer_issues,
    get_humanizer_prompt,
    get_reviewer_guide,
    get_writing_guide,
)

__all__ = [
    "detect_humanizer_issues",
    "get_humanizer_prompt",
    "get_reviewer_guide",
    "get_writing_guide",
]
