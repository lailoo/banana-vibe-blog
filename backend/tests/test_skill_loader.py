"""
测试 Skill Loader
"""

import pytest
from services.blog_generator.skills.skill_loader import SkillLoader, get_skill_loader


class TestSkillLoader:
    """测试 SkillLoader 类"""

    def test_skill_loader_singleton(self):
        """测试 skill loader 单例模式"""
        loader1 = get_skill_loader()
        loader2 = get_skill_loader()
        assert loader1 is loader2

    def test_load_humanizer_skill(self):
        """测试加载 humanizer skill"""
        loader = SkillLoader()
        skill = loader.load_skill("humanizer")

        assert skill is not None
        assert skill["name"] == "humanizer"
        assert "version" in skill
        assert "description" in skill
        assert "prompt" in skill
        assert len(skill["prompt"]) > 0

    def test_skill_cache(self):
        """测试 skill 缓存机制"""
        loader = SkillLoader()

        # 第一次加载
        skill1 = loader.load_skill("humanizer")

        # 第二次加载应该从缓存获取
        skill2 = loader.load_skill("humanizer")

        assert skill1 is skill2

    def test_invalid_skill(self):
        """测试加载不存在的 skill"""
        loader = SkillLoader()
        skill = loader.load_skill("nonexistent_skill")

        assert skill is None

    def test_get_skill_prompt(self):
        """测试获取 skill prompt"""
        loader = SkillLoader()
        prompt = loader.get_skill_prompt("humanizer")

        assert prompt is not None
        assert "Humanizer" in prompt
        assert "AI" in prompt

    def test_list_available_skills(self):
        """测试列出可用 skills"""
        loader = SkillLoader()
        skills = loader.list_available_skills()

        assert isinstance(skills, list)
        assert "humanizer" in skills

    def test_clear_cache(self):
        """测试清空缓存"""
        loader = SkillLoader()

        # 加载 skill
        loader.load_skill("humanizer")
        assert len(loader._skills_cache) > 0

        # 清空缓存
        loader.clear_cache()
        assert len(loader._skills_cache) == 0
