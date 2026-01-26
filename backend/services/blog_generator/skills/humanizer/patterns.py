"""
AI Writing Patterns - AI 写作模式定义

基于 Wikipedia "Signs of AI writing" 和 blader/humanizer 项目定义的 24 种 AI 写作模式。
"""

from typing import Dict, List, Any

# ============================================================================
# 内容模式 (CONTENT PATTERNS)
# ============================================================================

CONTENT_PATTERNS = {
    "undue_significance": {
        "name": "过度强调重要性",
        "category": "content",
        "severity": "medium",
        "keywords": [
            "stands as",
            "serves as",
            "testament",
            "reminder",
            "vital role",
            "significant role",
            "crucial role",
            "pivotal role",
            "key role",
            "pivotal moment",
            "key moment",
            "turning point",
            "underscores",
            "highlights",
            "reflects broader",
            "symbolizing",
            "ongoing",
            "enduring",
            "lasting",
            "contributing to",
            "setting the stage",
            "marking",
            "shaping",
            "represents a shift",
            "evolving landscape",
            "focal point",
            "indelible mark",
            "deeply rooted",
        ],
        "description": "LLM 通过添加关于任意方面如何代表或贡献于更广泛主题的陈述来夸大重要性",
        "example_before": "该研究所成立于1989年,标志着区域统计发展的关键时刻",
        "example_after": "该研究所成立于1989年,负责收集和发布区域统计数据",
    },
    "media_coverage": {
        "name": "过度强调媒体报道",
        "category": "content",
        "severity": "low",
        "keywords": [
            "independent coverage",
            "media outlets",
            "leading expert",
            "active social media presence",
            "widely covered",
            "garnered attention",
        ],
        "description": "LLM 过度强调知名度,经常列出来源而不提供上下文",
        "example_before": "她的观点被纽约时报、BBC、金融时报引用。她在社交媒体上拥有50万粉丝",
        "example_after": "在2024年纽约时报采访中,她认为AI监管应关注结果而非方法",
    },
    "ing_endings": {
        "name": "-ing 结尾的肤浅分析",
        "category": "content",
        "severity": "high",
        "keywords": [
            "highlighting",
            "underscoring",
            "emphasizing",
            "ensuring",
            "reflecting",
            "symbolizing",
            "contributing to",
            "cultivating",
            "fostering",
            "encompassing",
            "showcasing",
        ],
        "description": "AI 聊天机器人在句子末尾添加现在分词短语以增加虚假深度",
        "example_before": "该寺庙的配色方案与该地区的自然美景产生共鸣,象征着德克萨斯州的矢车菊、墨西哥湾和多样化的德克萨斯景观,反映了社区与土地的深厚联系",
        "example_after": "该寺庙使用蓝色、绿色和金色。建筑师表示这些颜色参考了当地的矢车菊和海湾海岸",
    },
    "promotional_language": {
        "name": "促销和广告式语言",
        "category": "content",
        "severity": "high",
        "keywords": [
            "boasts",
            "vibrant",
            "rich",
            "profound",
            "enhancing",
            "showcasing",
            "exemplifies",
            "commitment to",
            "natural beauty",
            "nestled",
            "in the heart of",
            "groundbreaking",
            "renowned",
            "breathtaking",
            "must-visit",
            "stunning",
        ],
        "description": 'LLM 难以保持中立语气,尤其是对"文化遗产"主题',
        "example_before": "坐落在埃塞俄比亚贡德尔地区的壮丽区域内,阿拉马塔拉亚科博是一个充满活力的城镇,拥有丰富的文化遗产和令人惊叹的自然美景",
        "example_after": "阿拉马塔拉亚科博是埃塞俄比亚贡德尔地区的一个城镇,以其每周集市和18世纪教堂而闻名",
    },
    "vague_attributions": {
        "name": "模糊归因和鼬鼠词",
        "category": "content",
        "severity": "medium",
        "keywords": [
            "industry reports",
            "observers have cited",
            "experts argue",
            "some critics argue",
            "several sources",
            "it is said",
            "many believe",
            "studies show",
        ],
        "description": "AI 聊天机器人将观点归因于模糊的权威,而不提供具体来源",
        "example_before": "由于其独特的特性,该河流引起了研究人员和保护主义者的兴趣。专家认为它在区域生态系统中发挥着关键作用",
        "example_after": "根据中国科学院2019年的调查,该河流支持几种特有鱼类",
    },
    "challenges_sections": {
        "name": '大纲式"挑战与未来展望"章节',
        "category": "content",
        "severity": "low",
        "keywords": [
            "despite its",
            "faces several challenges",
            "despite these challenges",
            "challenges and legacy",
            "future outlook",
            "looking ahead",
        ],
        "description": '许多 LLM 生成的文章包含公式化的"挑战"章节',
        "example_before": "尽管工业繁荣,该地区面临着城市地区典型的挑战,包括交通拥堵和水资源短缺。尽管存在这些挑战,凭借其战略位置和持续的举措,该地区继续蓬勃发展",
        "example_after": "2015年三个新IT园区开业后,交通拥堵加剧。市政公司于2022年启动了雨水排水项目以解决反复发生的洪水",
    },
}

# ============================================================================
# 语言和语法模式 (LANGUAGE AND GRAMMAR PATTERNS)
# ============================================================================

LANGUAGE_PATTERNS = {
    "ai_vocabulary": {
        "name": "AI 词汇过度使用",
        "category": "language",
        "severity": "high",
        "keywords": [
            "additionally",
            "align with",
            "crucial",
            "delve",
            "emphasizing",
            "enduring",
            "enhance",
            "fostering",
            "garner",
            "highlight",
            "interplay",
            "intricate",
            "intricacies",
            "key",
            "landscape",
            "pivotal",
            "showcase",
            "tapestry",
            "testament",
            "underscore",
            "valuable",
            "vibrant",
        ],
        "description": "这些词在2023年后的文本中出现频率远高于人类写作",
        "example_before": "此外,索马里美食的一个独特特征是融入了骆驼肉。意大利殖民影响的持久证明是当地烹饪景观中广泛采用意大利面,展示了这些菜肴如何融入传统饮食",
        "example_after": "索马里美食还包括骆驼肉,被视为美味。意大利殖民时期引入的意大利面菜肴仍然很常见,尤其是在南部",
    },
    "copula_avoidance": {
        "name": '避免使用"是"(系动词回避)',
        "category": "language",
        "severity": "medium",
        "keywords": [
            "serves as",
            "stands as",
            "marks",
            "represents",
            "boasts",
            "features",
            "offers",
        ],
        "description": "LLM 用复杂的结构替代简单的系动词",
        "example_before": "Gallery 825 作为 LAAA 的当代艺术展览空间。画廊拥有四个独立空间,总面积超过3000平方英尺",
        "example_after": "Gallery 825 是 LAAA 的当代艺术展览空间。画廊有四个房间,总面积3000平方英尺",
    },
    "negative_parallelisms": {
        "name": "负面并列",
        "category": "language",
        "severity": "medium",
        "keywords": [
            "not only...but",
            "it's not just about...it's",
            "not merely...but",
            "more than just",
        ],
        "description": '"不仅...而且..."或"这不仅仅是...这是..."等结构被过度使用',
        "example_before": "这不仅仅是节拍在人声下骑行;它是侵略性和氛围的一部分。这不仅仅是一首歌,这是一个声明",
        "example_after": "沉重的节拍增加了侵略性的基调",
    },
    "rule_of_three": {
        "name": "三段式过度使用",
        "category": "language",
        "severity": "low",
        "keywords": [],  # 需要通过模式检测
        "description": "LLM 强制将想法分成三组以显得全面",
        "example_before": "该活动包括主题演讲、小组讨论和网络机会。与会者可以期待创新、灵感和行业见解",
        "example_after": "该活动包括演讲和小组讨论。会议之间也有非正式交流的时间",
    },
    "elegant_variation": {
        "name": "优雅变化(同义词循环)",
        "category": "language",
        "severity": "low",
        "keywords": [],  # 需要通过模式检测
        "description": "AI 有重复惩罚代码导致过度的同义词替换",
        "example_before": "主角面临许多挑战。主要角色必须克服障碍。中心人物最终获胜。英雄回家了",
        "example_after": "主角面临许多挑战,但最终获胜并回家",
    },
    "false_ranges": {
        "name": "虚假范围",
        "category": "language",
        "severity": "low",
        "keywords": ["from...to", "从...到"],
        "description": 'LLM 使用"从 X 到 Y"结构,其中 X 和 Y 不在有意义的尺度上',
        "example_before": "我们穿越宇宙的旅程带我们从大爆炸的奇点到宏伟的宇宙网,从恒星的诞生和死亡到暗物质的神秘舞蹈",
        "example_after": "本书涵盖大爆炸、恒星形成和当前关于暗物质的理论",
    },
}

# ============================================================================
# 风格模式 (STYLE PATTERNS)
# ============================================================================

STYLE_PATTERNS = {
    "em_dash_overuse": {
        "name": "Em Dash 过度使用",
        "category": "style",
        "severity": "low",
        "keywords": ["—", "--"],
        "description": "LLM 过度使用 em dash 来连接想法",
        "threshold": 3,  # 每1000字超过3个
    },
    "boldface_overuse": {
        "name": "粗体过度使用",
        "category": "style",
        "severity": "low",
        "keywords": ["**", "__"],
        "description": "LLM 过度使用粗体强调",
        "threshold": 5,  # 每段超过5个
    },
    "inline_header_lists": {
        "name": "内联标题垂直列表",
        "category": "style",
        "severity": "low",
        "keywords": [],  # 需要通过模式检测
        "description": "LLM 创建带有内联粗体标题的垂直列表",
    },
    "title_case_headings": {
        "name": "标题大小写",
        "category": "style",
        "severity": "low",
        "keywords": [],  # 需要通过模式检测
        "description": "LLM 在标题中使用标题大小写(每个单词首字母大写)",
    },
    "emoji_overuse": {
        "name": "Emoji 过度使用",
        "category": "style",
        "severity": "low",
        "keywords": ["🎯", "✨", "🚀", "💡", "⚡", "🔥", "📊", "🎨"],
        "description": "LLM 过度使用 emoji",
        "threshold": 2,  # 每段超过2个
    },
    "curly_quotes": {
        "name": "弯引号",
        "category": "style",
        "severity": "low",
        "keywords": ['"', '"', """, """],
        "description": "LLM 使用弯引号而不是直引号(技术文档中不常见)",
    },
}

# ============================================================================
# 沟通模式 (COMMUNICATION PATTERNS)
# ============================================================================

COMMUNICATION_PATTERNS = {
    "collaborative_artifacts": {
        "name": "协作沟通痕迹",
        "category": "communication",
        "severity": "high",
        "keywords": [
            "let's",
            "we can",
            "together we",
            "our journey",
            "as we explore",
            "join us",
            "let us",
        ],
        "description": "LLM 使用协作语言,好像在与读者对话",
        "example_before": "让我们一起探索这个迷人的主题",
        "example_after": "本文探讨这个主题",
    },
    "knowledge_cutoff": {
        "name": "知识截止声明",
        "category": "communication",
        "severity": "high",
        "keywords": [
            "as of my last update",
            "as of my knowledge cutoff",
            "at the time of writing",
            "as of [date]",
        ],
        "description": "LLM 添加知识截止日期声明",
        "example_before": "截至我最后更新时,该技术仍在开发中",
        "example_after": "该技术于2023年仍在开发中",
    },
    "sycophantic_tone": {
        "name": "谄媚/奴性语气",
        "category": "communication",
        "severity": "medium",
        "keywords": [
            "i hope this helps",
            "feel free to",
            "don't hesitate",
            "please let me know",
            "i'd be happy to",
        ],
        "description": "LLM 使用过度礼貌或服务性的语气",
        "example_before": "我希望这有帮助!如有任何问题,请随时询问",
        "example_after": "(删除此类语句)",
    },
}

# ============================================================================
# 填充和模糊 (FILLER AND HEDGING)
# ============================================================================

FILLER_PATTERNS = {
    "filler_phrases": {
        "name": "填充短语",
        "category": "filler",
        "severity": "medium",
        "keywords": [
            "it is important to note",
            "it should be noted",
            "it is worth mentioning",
            "notably",
            "significantly",
            "interestingly",
            "remarkably",
            "particularly",
        ],
        "description": "LLM 使用填充短语来增加字数",
        "example_before": "值得注意的是,该方法显著提高了性能",
        "example_after": "该方法提高了性能",
    },
    "excessive_hedging": {
        "name": "过度对冲",
        "category": "filler",
        "severity": "medium",
        "keywords": [
            "may",
            "might",
            "could",
            "possibly",
            "potentially",
            "arguably",
            "seemingly",
            "appears to",
            "tends to",
        ],
        "description": "LLM 过度使用对冲语言以避免明确陈述",
        "threshold": 5,  # 每段超过5个
    },
    "generic_conclusions": {
        "name": "通用积极结论",
        "category": "filler",
        "severity": "low",
        "keywords": [
            "in conclusion",
            "to sum up",
            "overall",
            "all in all",
            "continues to evolve",
            "remains to be seen",
            "only time will tell",
        ],
        "description": "LLM 使用通用的积极结论",
        "example_before": "总之,该领域继续发展,未来充满希望",
        "example_after": "(提供具体结论或删除)",
    },
}

# ============================================================================
# 合并所有模式
# ============================================================================

ALL_PATTERNS = {
    **CONTENT_PATTERNS,
    **LANGUAGE_PATTERNS,
    **STYLE_PATTERNS,
    **COMMUNICATION_PATTERNS,
    **FILLER_PATTERNS,
}


def get_pattern_by_category(category: str) -> Dict[str, Any]:
    """
    根据类别获取模式

    Args:
        category: 类别名称 (content/language/style/communication/filler)

    Returns:
        该类别的所有模式
    """
    return {k: v for k, v in ALL_PATTERNS.items() if v.get("category") == category}


def get_high_severity_patterns() -> Dict[str, Any]:
    """
    获取高严重度模式

    Returns:
        所有高严重度模式
    """
    return {k: v for k, v in ALL_PATTERNS.items() if v.get("severity") == "high"}
