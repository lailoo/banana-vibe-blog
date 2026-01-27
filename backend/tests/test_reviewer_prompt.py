"""
测试 Reviewer prompt 注入 humanizer 规则与阈值
"""

from services.blog_generator.prompts.prompt_manager import get_prompt_manager


def test_reviewer_prompt_includes_threshold_and_humanizer_guide():
    pm = get_prompt_manager()
    prompt = pm.render_reviewer(
        document="doc",
        outline={},
        humanizer_guide="HUMANIZER_GUIDE_SNIPPET",
        review_threshold=91,
    )

    assert "score >= 91" in prompt
    assert "HUMANIZER_GUIDE_SNIPPET" in prompt
    assert "humanization_score" in prompt

