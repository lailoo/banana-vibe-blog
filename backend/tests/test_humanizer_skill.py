"""
测试 Humanizer-zh skill 的指南提取与检测解析
"""

import json

from services.blog_generator.skills.humanizer.skill import (
    detect_humanizer_issues,
    get_humanizer_prompt,
    get_writing_guide,
)


class DummyLLM:
    """用于测试的 LLM stub（返回固定 JSON）。"""

    def chat(self, messages, response_format=None):  # noqa: D401 - 测试桩
        _ = messages, response_format
        return json.dumps(
            {
                "humanization_score": 12,
                "summary": "检测到一些 AI 写作痕迹",
                "issues": [
                    {
                        "section_id": "section_1",
                        "issue_type": "humanization",
                        "severity": "medium",
                        "description": "过多使用连接词",
                        "suggestion": "删除 Additionally / Furthermore 一类词",
                    },
                    {
                        # 非法 section_id，应被降级为全局问题
                        "section_id": "unknown",
                        "issue_type": "humanization",
                        "severity": "high",
                        "description": "宣传性语言过多",
                        "suggestion": "改为具体事实描述",
                    },
                ],
            },
            ensure_ascii=False,
        )


def test_get_humanizer_prompt_and_guide():
    prompt = get_humanizer_prompt()
    assert "Humanizer-zh" in prompt

    guide = get_writing_guide()
    assert guide
    assert "写作避坑指南" in guide


def test_detect_humanizer_issues_normalizes_section_id():
    llm = DummyLLM()
    sections = [
        {"id": "section_1", "title": "标题1", "content": "Additionally, this is crucial."},
        {"id": "section_2", "title": "标题2", "content": "In conclusion, it remains to be seen."},
    ]
    document = "\n\n".join(s["content"] for s in sections)

    result = detect_humanizer_issues(document=document, sections=sections, llm_client=llm)

    assert result["humanization_score"] == 12
    assert len(result["issues"]) == 2
    # 第二条 section_id 非法，应被清空为全局问题
    assert result["issues"][1]["section_id"] == ""

