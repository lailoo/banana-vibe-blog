"""
测试 Humanizer Skill
"""

import pytest
from services.blog_generator.skills.humanizer.skill import (
    detect_ai_patterns,
    calculate_humanization_score,
    get_skill_config,
)
from services.blog_generator.skills.humanizer.patterns import ALL_PATTERNS


class TestHumanizerSkill:
    """测试 Humanizer Skill"""

    def test_get_skill_config(self):
        """测试获取 skill 配置"""
        config = get_skill_config()

        assert config["name"] == "humanizer"
        assert "version" in config
        assert "description" in config
        assert "prompt" in config
        assert len(config["prompt"]) > 0

    def test_detect_ai_vocabulary(self):
        """测试检测 AI 词汇过度使用"""
        text = """
        Additionally, this crucial research delves into the intricate landscape of AI.
        The pivotal findings showcase the enduring impact and highlight the key insights.
        This testament to innovation underscores the vibrant ecosystem.
        """

        patterns = detect_ai_patterns(text, min_severity="medium")

        # 应该检测到 AI 词汇模式
        ai_vocab_patterns = [p for p in patterns if p["pattern_id"] == "ai_vocabulary"]
        assert len(ai_vocab_patterns) > 0
        assert ai_vocab_patterns[0]["count"] > 5  # 文本中有多个 AI 词汇

    def test_detect_copula_avoidance(self):
        """测试检测系动词回避"""
        text = """
        The gallery serves as a contemporary art space.
        The building stands as a monument to innovation.
        The system boasts advanced features.
        """

        patterns = detect_ai_patterns(text, min_severity="low")

        # 应该检测到系动词回避模式
        copula_patterns = [p for p in patterns if p["pattern_id"] == "copula_avoidance"]
        assert len(copula_patterns) > 0

    def test_detect_promotional_language(self):
        """测试检测促销语言"""
        text = """
        Nestled in the breathtaking region, this vibrant town boasts rich cultural heritage
        and stunning natural beauty. The renowned landmark showcases groundbreaking architecture.
        """

        patterns = detect_ai_patterns(text, min_severity="medium")

        # 应该检测到促销语言模式
        promo_patterns = [
            p for p in patterns if p["pattern_id"] == "promotional_language"
        ]
        assert len(promo_patterns) > 0

    def test_detect_collaborative_artifacts(self):
        """测试检测协作沟通痕迹"""
        text = """
        Let's explore this fascinating topic together. We can see how this works.
        Join us on this journey as we delve into the details.
        """

        patterns = detect_ai_patterns(text, min_severity="high")

        # 应该检测到协作痕迹模式
        collab_patterns = [
            p for p in patterns if p["pattern_id"] == "collaborative_artifacts"
        ]
        assert len(collab_patterns) > 0

    def test_no_false_positives(self):
        """测试人类写作不会误报"""
        # 简单、直接的人类写作
        text = """
        Redis is an in-memory data structure store. It supports strings, hashes, lists, and sets.
        You can use Redis as a cache or message broker. The performance is excellent.
        Installation is straightforward: download, extract, and run the server.
        """

        patterns = detect_ai_patterns(text, min_severity="high")

        # 简单的人类写作不应该检测到高严重度模式
        assert len(patterns) == 0

    def test_calculate_humanization_score_perfect(self):
        """测试计算人性化得分 - 满分情况"""
        patterns = []
        score = calculate_humanization_score(patterns)

        assert score == 20  # 满分

    def test_calculate_humanization_score_with_patterns(self):
        """测试计算人性化得分 - 有模式情况"""
        patterns = [
            {"pattern_id": "ai_vocabulary", "severity": "high", "count": 10},
            {"pattern_id": "copula_avoidance", "severity": "medium", "count": 5},
        ]

        score = calculate_humanization_score(patterns)

        # 应该有扣分
        assert score < 20
        assert score >= 0

    def test_severity_levels(self):
        """测试不同严重程度的检测"""
        text = """
        Additionally, this crucial research showcases the vibrant ecosystem.
        Let's explore this together.
        """

        # 只检测高严重度
        high_patterns = detect_ai_patterns(text, min_severity="high")

        # 检测所有严重度
        all_patterns = detect_ai_patterns(text, min_severity="low")

        # 所有模式应该包含高严重度模式
        assert len(all_patterns) >= len(high_patterns)

    def test_pattern_locations(self):
        """测试模式位置信息"""
        text = "Additionally, this is crucial for understanding the landscape."

        patterns = detect_ai_patterns(text, min_severity="low")

        # 应该有位置信息
        if patterns:
            pattern = patterns[0]
            assert "locations" in pattern
            assert len(pattern["locations"]) > 0
            assert "keyword" in pattern["locations"][0]
            assert "context" in pattern["locations"][0]


class TestPatterns:
    """测试 AI 写作模式定义"""

    def test_all_patterns_structure(self):
        """测试所有模式的结构完整性"""
        for pattern_id, pattern_config in ALL_PATTERNS.items():
            assert "name" in pattern_config
            assert "category" in pattern_config
            assert "severity" in pattern_config
            assert pattern_config["severity"] in ["low", "medium", "high"]
            assert pattern_config["category"] in [
                "content",
                "language",
                "style",
                "communication",
                "filler",
            ]

    def test_pattern_count(self):
        """测试模式数量"""
        # 应该有 24 种模式
        assert len(ALL_PATTERNS) >= 18  # 至少有主要的模式
"""
测试 Humanizer Skill 的 Writer 指导功能
"""

import pytest
from services.blog_generator.skills.humanizer.skill import get_writing_guide


class TestHumanizerWriterGuide:
    """测试 Writer 指导功能"""

    def test_get_writing_guide(self):
        """测试获取写作指南"""
        guide = get_writing_guide()

        assert guide is not None
        assert "写作避坑指南" in guide
        assert "拒绝 AI 常用词" in guide
        assert "crucial" in guide
        assert "delve" in guide
