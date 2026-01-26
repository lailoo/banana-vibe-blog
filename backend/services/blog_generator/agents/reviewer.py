"""
Reviewer Agent - 质量审核
"""

import json
import logging
from typing import Dict, Any

from ..prompts.prompt_manager import get_prompt_manager
from ..skills.humanizer.skill import detect_ai_patterns, calculate_humanization_score

logger = logging.getLogger(__name__)


class ReviewerAgent:
    """
    质量审核师 - 负责内容质量把控
    """

    def __init__(self, llm_client):
        """
        初始化 Reviewer Agent

        Args:
            llm_client: LLM 客户端
        """
        self.llm = llm_client

    def review(self, document: str, outline: Dict[str, Any]) -> Dict[str, Any]:
        """
        审核文档

        Args:
            document: 完整文档
            outline: 原始大纲

        Returns:
            审核结果,包含:
            - score: 总分 (0-100)
            - approved: 是否通过
            - issues: 问题列表
            - summary: 审核摘要
            - humanization_score: 人性化得分 (0-20)
            - ai_patterns: 检测到的 AI 模式
        """
        # Step 1: 使用 humanizer skill 检测 AI 模式
        logger.info("开始 AI 写作模式检测...")
        ai_patterns = detect_ai_patterns(document, min_severity="medium")
        humanization_score = calculate_humanization_score(ai_patterns)

        logger.info(
            f"检测到 {len(ai_patterns)} 种 AI 模式, 人性化得分: {humanization_score}/20"
        )

        # Step 2: 调用原有审核逻辑
        pm = get_prompt_manager()
        prompt = pm.render_reviewer(document=document, outline=outline)

        try:
            response = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )

            result = json.loads(response)

            # Step 3: 合并审核结果和人性化检测结果
            issues = result.get("issues", [])
            base_score = result.get("score", 80)

            # 将 AI 模式转换为审核问题
            humanization_issues = self._convert_patterns_to_issues(ai_patterns)
            issues.extend(humanization_issues)

            # 计算总分: 原有100分 + 人性化20分 = 120分制,归一化到100分
            total_score = base_score + humanization_score
            final_score = min(100, int(total_score * 100 / 120))

            # 检查是否有高严重度问题
            has_high_issue = any(i.get("severity") == "high" for i in issues)

            # 审核通过条件: 无高严重度问题 且 总分 >= 91
            approved = (
                result.get("approved", True)
                and not has_high_issue
                and final_score >= 91
            )

            logger.info(
                f"审核评分: 基础分 {base_score}/100 + 人性化 {humanization_score}/20 = 总分 {final_score}/100"
            )

            return {
                "score": final_score,
                "approved": approved,
                "issues": issues,
                "summary": result.get("summary", ""),
                "humanization_score": humanization_score,
                "ai_patterns": ai_patterns[:5],  # 最多返回5个模式用于展示
            }

        except Exception as e:
            logger.error(f"审核失败: {e}")
            # 默认通过,但保留人性化检测结果
            return {
                "score": 80,
                "approved": True,
                "issues": self._convert_patterns_to_issues(ai_patterns),
                "summary": "审核完成",
                "humanization_score": humanization_score,
                "ai_patterns": ai_patterns[:5],
            }

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行质量审核

        Args:
            state: 共享状态

        Returns:
            更新后的状态
        """
        if state.get("error"):
            logger.error(f"前置步骤失败，跳过质量审核: {state.get('error')}")
            state["review_score"] = 0
            state["review_approved"] = False
            state["review_issues"] = []
            return state

        sections = state.get("sections", [])
        if not sections:
            logger.error("没有章节内容，跳过质量审核")
            state["review_score"] = 0
            state["review_approved"] = False
            state["review_issues"] = []
            return state

        outline = state.get("outline", {})

        # 组装文档用于审核
        document_parts = []
        for section in sections:
            document_parts.append(
                f"## {section.get('title', '')}\n\n{section.get('content', '')}"
            )

        document = "\n\n---\n\n".join(document_parts)

        logger.info("开始质量审核")

        result = self.review(document, outline)

        state["review_score"] = result.get("score", 80)
        state["review_approved"] = result.get("approved", True)
        state["review_issues"] = result.get("issues", [])

        # 保存人性化相关信息到 state
        state["humanization_score"] = result.get("humanization_score", 0)
        state["ai_patterns"] = result.get("ai_patterns", [])

        logger.info(
            f"质量审核完成: 得分 {result.get('score', 0)}, {'通过' if result.get('approved') else '未通过'}"
        )
        logger.info(f"  - 人性化得分: {result.get('humanization_score', 0)}/20")

        if result.get("ai_patterns"):
            logger.info(
                f"  - 检测到 {len(result.get('ai_patterns', []))} 种 AI 写作模式"
            )
            for pattern in result.get("ai_patterns", [])[:3]:  # 最多显示3个
                logger.info(
                    f"    • {pattern.get('pattern_name', '')} ({pattern.get('severity', '')}): {pattern.get('count', 0)} 次"
                )

        if result.get("issues"):
            for issue in result["issues"]:
                logger.info(
                    f"  - [{issue.get('severity', 'medium')}] {issue.get('description', '')}"
                )

        return state

    def _convert_patterns_to_issues(self, ai_patterns: list) -> list:
        """
        将检测到的 AI 模式转换为审核问题格式

        Args:
            ai_patterns: 检测到的 AI 模式列表

        Returns:
            审核问题列表
        """
        issues = []

        for pattern in ai_patterns:
            # 只转换 medium 和 high 严重度的模式
            if pattern.get("severity") not in ["medium", "high"]:
                continue

            issue = {
                "section_id": "",  # AI 模式是全文级别的
                "issue_type": "humanization",
                "severity": pattern.get("severity", "medium"),
                "description": f"AI 写作模式: {pattern.get('pattern_name', '')} (出现 {pattern.get('count', 0)} 次)",
                "suggestion": self._get_humanization_suggestion(pattern),
            }
            issues.append(issue)

        return issues

    def _get_humanization_suggestion(self, pattern: dict) -> str:
        """
        获取人性化改进建议

        Args:
            pattern: AI 模式信息

        Returns:
            改进建议
        """
        pattern_name = pattern.get("pattern_name", "")
        category = pattern.get("category", "")

        suggestions = {
            "content": "减少夸张的重要性描述,使用更具体、更客观的表述",
            "language": "使用更自然的语言,避免 AI 常用词汇,多用简单直接的表达",
            "style": "简化格式,减少过度修饰,让文本更易读",
            "communication": "移除协作式语言和谄媚语气,使用更专业的叙述方式",
            "filler": "删除填充短语和过度对冲,直接表达观点",
        }

        base_suggestion = suggestions.get(category, "参考 humanizer 规范进行改进")

        # 如果有具体示例,添加到建议中
        if pattern.get("locations"):
            first_location = pattern["locations"][0]
            context = first_location.get("context", "")
            if context:
                return f"{base_suggestion}。示例位置: ...{context}..."

        return base_suggestion
