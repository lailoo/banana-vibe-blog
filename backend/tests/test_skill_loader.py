"""
测试 SkillLoader 与 LangChain tool 加载能力
"""

from services.blog_generator.skills.skill_loader import SkillLoader, load_skill


def test_list_and_load_humanizer_skill():
    loader = SkillLoader()
    skills = loader.list_available_skills()

    assert "humanizer" in skills

    skill = loader.load_skill("humanizer")
    assert skill is not None
    assert skill.name
    assert "去除" in skill.description
    assert "Humanizer-zh" in skill.prompt


def test_load_skill_tool_invoke():
    prompt = load_skill.invoke({"skill_name": "humanizer"})
    assert "AI 写作痕迹" in prompt

