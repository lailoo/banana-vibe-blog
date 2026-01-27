"""
Humanizer-zh Skill - 核心实现

从本地 SKILL.md 加载提示词，并在 Writer/Reviewer 阶段复用。
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Sequence

from ..skill_loader import get_skill_loader, load_skill

logger = logging.getLogger(__name__)

SKILL_NAME = "humanizer"
_REVIEWER_GUIDE_MAX_CHARS = 6000

_CORE_RULES_RE = re.compile(
    r"## 核心规则速查\s*(.*?)\n---",
    re.DOTALL,
)


def get_humanizer_prompt() -> str:
    """获取 Humanizer-zh 的完整技能提示词。"""
    # 使用 LangChain tool（load_skill）作为统一入口
    prompt = load_skill.invoke({"skill_name": SKILL_NAME})
    if prompt and "not found" not in prompt.lower():
        return prompt

    # tool 返回异常提示时，兜底直接读取 loader
    loader = get_skill_loader()
    skill = loader.load_skill(SKILL_NAME)
    return skill.prompt if skill else ""


def get_writing_guide() -> str:
    """
    获取写作避坑指南（精简版）。

    优先提取“核心规则速查”，避免在 Writer 阶段塞入过长提示词。
    """
    prompt = get_humanizer_prompt()
    if not prompt:
        return ""

    match = _CORE_RULES_RE.search(prompt)
    if match:
        core_rules = match.group(1).strip()
        return "## Humanizer-zh 写作避坑指南\n\n" + core_rules

    # 如果匹配失败，兜底返回较短的开头部分
    head = prompt.split("## 内容模式", 1)[0].strip()
    return head[:1500]


def _extract_core_rules(prompt: str) -> str:
    """提取“核心规则速查”段落，用于精简注入。"""
    match = _CORE_RULES_RE.search(prompt)
    if not match:
        return ""
    return match.group(1).strip()


def get_reviewer_guide(max_chars: int = _REVIEWER_GUIDE_MAX_CHARS) -> str:
    """
    获取 Reviewer 使用的 Humanizer-zh 规则摘要。

    Reviewer 需要更完整的规则，但仍需控制长度避免 token 爆炸。
    """
    prompt = get_humanizer_prompt()
    if not prompt:
        return ""

    core_rules = _extract_core_rules(prompt)
    # 取“内容模式”之后的部分作为规则主体，截断控制长度
    if "## 内容模式" in prompt:
        rules_body = prompt.split("## 内容模式", 1)[1]
    else:
        rules_body = prompt

    rules_body = rules_body.strip()[:max_chars]

    parts = ["## Humanizer-zh 检测规则（摘要）"]
    if core_rules:
        parts.append(core_rules)
    parts.append("以下为规则摘要，评估时必须遵循：")
    parts.append(rules_body)
    return "\n\n".join(parts).strip()


def detect_humanizer_issues(
    *,
    document: str,
    sections: Sequence[Dict[str, Any]],
    llm_client: Any,
) -> Dict[str, Any]:
    """
    使用 Humanizer-zh 指南检测 AI 写作痕迹并给出结构化结果。

    Returns:
        {
          "humanization_score": int(0-20),
          "issues": List[dict],
          "summary": str
        }
    """
    skill_prompt = get_humanizer_prompt()
    if not skill_prompt:
        logger.warning("Humanizer skill 未加载，跳过 AI 痕迹检测")
        return {"humanization_score": 0, "issues": [], "summary": "skill 未加载"}

    section_payload = [
        {
            "id": s.get("id", ""),
            "title": s.get("title", ""),
            # 控制长度，避免 reviewer 阶段 token 爆炸
            "content": (s.get("content", "") or "")[:4000],
        }
        for s in sections
    ]

    detection_prompt = f"""
你将作为“AI 写作痕迹审查器”，严格依据以下 Skill 指南进行检测：

{skill_prompt}

---

请审查下面的博客章节内容，识别 AI 写作痕迹，并输出 JSON（不要输出任何额外文本）：

输出格式：
{{
  "humanization_score": 0-20,
  "summary": "总体评价（一句话）",
  "issues": [
    {{
      "section_id": "章节 id（必须来自输入）",
      "issue_type": "humanization",
      "severity": "high | medium | low",
      "description": "问题描述（点名模式）",
      "suggestion": "可执行的改写建议"
    }}
  ]
}}

评分建议（0-20）：
- 20: 几乎无人机味，语言自然
- 14-19: 有少量 AI 痕迹，但整体可读
- 8-13: AI 痕迹明显，需要修订
- 0-7: 大量 AI 痕迹，建议重写

输入章节（JSON）：
{json.dumps(section_payload, ensure_ascii=False)}

全文（用于参考上下文）：
{document[:12000]}
""".strip()

    try:
        response = llm_client.chat(
            messages=[{"role": "user", "content": detection_prompt}],
            response_format={"type": "json_object"},
        )
        parsed = json.loads(response or "{}")
    except Exception as exc:  # noqa: BLE001 - 这里需要兜底
        logger.error("Humanizer 检测失败: %s", exc)
        return {"humanization_score": 0, "issues": [], "summary": "检测失败"}

    issues = parsed.get("issues") or []
    normalized_issues: List[Dict[str, Any]] = []
    valid_ids = {s.get("id", "") for s in section_payload}

    for issue in issues:
        section_id = issue.get("section_id", "")
        if section_id not in valid_ids:
            # section_id 非法时，降级为全局问题（留空交给修订节点处理）
            section_id = ""

        normalized_issues.append(
            {
                "section_id": section_id,
                "issue_type": "humanization",
                "severity": issue.get("severity", "medium"),
                "description": issue.get("description", "检测到 AI 写作痕迹"),
                "suggestion": issue.get("suggestion", "按 humanizer 指南重写"),
            }
        )

    score = parsed.get("humanization_score", 0)
    try:
        score_int = int(score)
    except (TypeError, ValueError):
        score_int = 0
    score_int = max(0, min(20, score_int))

    return {
        "humanization_score": score_int,
        "issues": normalized_issues,
        "summary": parsed.get("summary", ""),
    }
