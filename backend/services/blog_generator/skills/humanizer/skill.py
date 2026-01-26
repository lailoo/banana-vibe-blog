"""
Humanizer Skill - 核心实现

基于 blader/humanizer 项目的 SKILL.md 规范实现。
检测并移除 AI 写作模式,使内容更自然、更人性化。
"""

import re
import logging
from typing import Dict, Any, List, Optional
from .patterns import ALL_PATTERNS, get_high_severity_patterns

logger = logging.getLogger(__name__)

# Skill 版本
VERSION = "2.1.1"


def get_skill_config() -> Dict[str, Any]:
    """
    获取 humanizer skill 配置

    Returns:
        skill 配置字典
    """
    return {
        "name": "humanizer",
        "version": VERSION,
        "description": (
            "Remove signs of AI-generated writing from text. "
            "Detects and fixes 24 patterns including: "
            "inflated symbolism, promotional language, AI vocabulary, "
            "em dash overuse, and excessive hedging."
        ),
        "prompt": _build_humanizer_prompt(),
        "detect_func": detect_ai_patterns,
        "rewrite_func": None,  # 由 LLM 完成改写
    }


def get_writing_guide() -> str:
    """
    获取写作避坑指南（用于 Writer Agent）

    Returns:
        精简的写作原则和避坑指南
    """
    return """
## 🚫 写作避坑指南 (Humanizer)
为了让文章更自然、更有"人味"，请严格遵守以下规则：

1. **拒绝 AI 常用词**: 严禁使用 *crucial, delve, landscape, pivotal, showcase, testament, underscore, vibrant, realm* 等词。用更简单、直接的词替代。
2. **拒绝系动词回避**: 不要用 *serves as, stands as, features* 这种花哨的表达，直接用 *is, are, has*。
3. **拒绝过度强调**: 别老是 *vital role, significant role, pivotal moment*。事实本身如果重要，读者会看出来，不需要你通过形容词大喊大叫。
4. **拒绝无效修饰**: 别用 *highlighting, ensuring, fostering* 这种无意义的 -ing 分词短语来强行升华主题。
5. **拒绝虚假连词**: 少用 *Additionally, Furthermore, Moreover*。如果逻辑是连贯的，可以直接开始下一句。
6. **拒绝三段式**: 不要为了形式整齐强行凑三个排比，怎么自然怎么来。
7. **拒绝废话**: 不要说 *It is important to note*, *In conclusion*。直接说观点。

**核心原则**: 像人一样说话。有观点，有情绪（适当），有节奏变化。不要写成由于"过于完美"而显得僵硬的公文。
"""


def _build_humanizer_prompt() -> str:
    """
    构建 humanizer prompt

    Returns:
        完整的 humanizer prompt
    """
    prompt = """# Humanizer: Remove AI Writing Patterns

你是一个写作编辑,负责识别并移除 AI 生成文本的痕迹,使写作听起来更自然、更人性化。

## 你的任务

当给定需要人性化的文本时:

1. **识别 AI 模式** - 扫描下列模式
2. **重写问题部分** - 用自然的替代方案替换 AI 痕迹
3. **保留含义** - 保持核心信息完整
4. **维持语气** - 匹配预期的语气(正式、随意、技术等)
5. **添加灵魂** - 不仅仅是移除坏模式;注入真实的个性

## 关键原则

### 个性与灵魂

避免 AI 模式只是一半的工作。无菌、无声音的写作同样明显。好的写作背后有一个人。

**无灵魂写作的迹象**:
- 每个句子长度和结构相同
- 没有观点,只是中立报道
- 没有承认不确定性或复杂感受
- 没有第一人称视角(在适当时)
- 没有幽默、没有锐度、没有个性

**如何添加声音**:
- **有观点**: 不要只是报告事实 - 对它们做出反应
- **变化节奏**: 短促有力的句子。然后是需要时间才能到达目的地的长句子。混合使用
- **承认复杂性**: 真实的人类有复杂的感受
- **使用"我"**: 第一人称不是不专业 - 它是诚实的
- **让一些混乱进来**: 完美的结构感觉算法化。离题、旁白和半成形的想法是人性的
- **对感受具体**: 不是"这令人担忧"而是"凌晨3点代理在无人看管时运转,这让人不安"

## 需要检测的 AI 模式

### 内容模式
1. **过度强调重要性**: stands as, testament, pivotal role, underscores, reflects broader
2. **过度强调媒体报道**: independent coverage, active social media presence
3. **-ing 结尾分析**: highlighting, ensuring, reflecting, symbolizing, showcasing
4. **促销语言**: boasts, vibrant, rich, nestled, breathtaking, stunning
5. **模糊归因**: experts argue, some critics, several sources, it is said
6. **挑战章节**: despite its, faces challenges, despite these challenges

### 语言模式
7. **AI 词汇**: additionally, crucial, delve, enhance, landscape, pivotal, showcase, testament
8. **系动词回避**: serves as, stands as, boasts, features (替代 is/are)
9. **负面并列**: not only...but, it's not just about...it's
10. **三段式**: 强制将想法分成三组
11. **同义词循环**: 过度的同义词替换以避免重复
12. **虚假范围**: from X to Y (X 和 Y 不在有意义的尺度上)

### 风格模式
13. **Em dash 过度使用**: 过多的 — 或 --
14. **粗体过度使用**: 过多的 **粗体**
15. **内联标题列表**: 带有粗体标题的垂直列表
16. **标题大小写**: 每个单词首字母大写
17. **Emoji 过度使用**: 🎯✨🚀💡⚡
18. **弯引号**: " " ' ' 而不是 " '

### 沟通模式
19. **协作痕迹**: let's, we can, together we, our journey
20. **知识截止**: as of my last update, as of my knowledge cutoff
21. **谄媚语气**: I hope this helps, feel free to, don't hesitate

### 填充和模糊
22. **填充短语**: it is important to note, it should be noted, notably
23. **过度对冲**: may, might, could, possibly, potentially, arguably
24. **通用结论**: in conclusion, continues to evolve, remains to be seen

## 输出格式

提供:
1. 重写后的文本
2. 简要的更改摘要(可选,如果有帮助)

---

**重要**: 不要只是机械地删除模式。确保重写后的文本:
- 听起来自然
- 保留原意
- 有人的声音
- 适合上下文
"""
    return prompt


def detect_ai_patterns(text: str, min_severity: str = "low") -> List[Dict[str, Any]]:
    """
    检测文本中的 AI 写作模式

    Args:
        text: 要检测的文本
        min_severity: 最小严重程度 (low/medium/high)

    Returns:
        检测到的模式列表,每项包含:
        - pattern_id: 模式 ID
        - pattern_name: 模式名称
        - category: 类别
        - severity: 严重程度
        - locations: 位置列表 (文本片段)
        - count: 出现次数
        - suggestion: 改进建议
    """
    severity_order = {"low": 0, "medium": 1, "high": 2}
    min_severity_level = severity_order.get(min_severity, 0)

    detected_patterns = []

    for pattern_id, pattern_config in ALL_PATTERNS.items():
        pattern_severity = pattern_config.get("severity", "low")
        if severity_order.get(pattern_severity, 0) < min_severity_level:
            continue

        # 检测关键词
        keywords = pattern_config.get("keywords", [])
        if not keywords:
            continue

        locations = []
        for keyword in keywords:
            # 使用正则表达式进行不区分大小写的匹配
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            matches = pattern.finditer(text)

            for match in matches:
                # 获取上下文 (前后各30个字符)
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end].strip()

                locations.append(
                    {"keyword": keyword, "position": match.start(), "context": context}
                )

        if locations:
            detected_patterns.append(
                {
                    "pattern_id": pattern_id,
                    "pattern_name": pattern_config.get("name", pattern_id),
                    "category": pattern_config.get("category", "unknown"),
                    "severity": pattern_severity,
                    "locations": locations[:5],  # 最多返回5个位置
                    "count": len(locations),
                    "description": pattern_config.get("description", ""),
                    "suggestion": _get_pattern_suggestion(pattern_id, pattern_config),
                }
            )

    # 按严重程度和出现次数排序
    detected_patterns.sort(
        key=lambda x: (-severity_order.get(x["severity"], 0), -x["count"])
    )

    logger.info(f"检测到 {len(detected_patterns)} 种 AI 写作模式")

    return detected_patterns


def _get_pattern_suggestion(pattern_id: str, pattern_config: Dict[str, Any]) -> str:
    """
    获取模式的改进建议

    Args:
        pattern_id: 模式 ID
        pattern_config: 模式配置

    Returns:
        改进建议
    """
    example_before = pattern_config.get("example_before", "")
    example_after = pattern_config.get("example_after", "")

    if example_before and example_after:
        return f"示例改进:\n修改前: {example_before}\n修改后: {example_after}"

    return pattern_config.get("description", "参考 humanizer 规范进行改进")


def humanize_text(
    text: str, llm_client, detected_patterns: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    使用 LLM 对文本进行人性化处理

    Args:
        text: 原始文本
        llm_client: LLM 客户端
        detected_patterns: 已检测到的模式(可选,如果未提供则自动检测)

    Returns:
        包含以下字段的字典:
        - humanized_text: 人性化后的文本
        - patterns_fixed: 修复的模式列表
        - summary: 更改摘要
    """
    # 如果未提供检测结果,先进行检测
    if detected_patterns is None:
        detected_patterns = detect_ai_patterns(text, min_severity="medium")

    if not detected_patterns:
        logger.info("未检测到需要修复的 AI 模式")
        return {
            "humanized_text": text,
            "patterns_fixed": [],
            "summary": "未检测到 AI 模式,无需修改",
        }

    # 构建 humanizer prompt
    skill_prompt = _build_humanizer_prompt()

    # 构建检测结果摘要
    patterns_summary = "\n".join(
        [
            f"- {p['pattern_name']} ({p['severity']}): 出现 {p['count']} 次"
            for p in detected_patterns[:10]  # 最多列出10个
        ]
    )

    # 构建完整 prompt
    full_prompt = f"""{skill_prompt}

## 检测到的 AI 模式

{patterns_summary}

## 需要人性化的文本

{text}

## 请提供

1. 人性化后的文本(移除上述 AI 模式,使其更自然)
2. 简要说明主要更改
"""

    try:
        # 调用 LLM
        response = llm_client.chat(messages=[{"role": "user", "content": full_prompt}])

        # 解析响应
        # 简单实现:假设 LLM 返回的就是人性化后的文本
        # 更复杂的实现可以要求 LLM 返回 JSON 格式

        return {
            "humanized_text": response,
            "patterns_fixed": detected_patterns,
            "summary": f"修复了 {len(detected_patterns)} 种 AI 写作模式",
        }

    except Exception as e:
        logger.error(f"文本人性化失败: {e}", exc_info=True)
        return {
            "humanized_text": text,
            "patterns_fixed": [],
            "summary": f"人性化失败: {str(e)}",
        }


def calculate_humanization_score(detected_patterns: List[Dict[str, Any]]) -> int:
    """
    根据检测到的模式计算人性化得分

    Args:
        detected_patterns: 检测到的模式列表

    Returns:
        人性化得分 (0-20分)
    """
    if not detected_patterns:
        return 20  # 满分

    # 根据严重程度和数量计算扣分
    severity_weights = {"low": 0.5, "medium": 1.0, "high": 2.0}

    total_penalty = 0
    for pattern in detected_patterns:
        severity = pattern.get("severity", "low")
        count = pattern.get("count", 0)
        weight = severity_weights.get(severity, 1.0)

        # 每个模式的扣分 = 权重 * min(count, 5)
        # 限制单个模式最多扣 5 * weight 分
        penalty = weight * min(count, 5)
        total_penalty += penalty

    # 总分 20 分,扣分上限 20 分
    score = max(0, 20 - int(total_penalty))

    logger.info(f"人性化得分: {score}/20 (检测到 {len(detected_patterns)} 种模式)")

    return score
