"""
Reviewer Agent - 质量审核
"""

import json
import logging
from typing import Dict, Any

from ..prompts.prompt_manager import get_prompt_manager
from ..skills.humanizer import get_reviewer_guide
from ..constants import REVIEW_THRESHOLD

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
    
    def review(
        self,
        document: str,
        outline: Dict[str, Any],
        sections: list[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        审核文档
        
        Args:
            document: 完整文档
            outline: 原始大纲
            
        Returns:
            审核结果
        """
        humanizer_guide = ""
        try:
            # 懒加载 humanizer 规则摘要，注入 Reviewer prompt
            humanizer_guide = get_reviewer_guide()
        except Exception as e:  # noqa: BLE001
            logger.warning(f"加载 Humanizer-zh 规则失败: {e}")

        pm = get_prompt_manager()
        prompt = pm.render_reviewer(
            document=document,
            outline=outline,
            humanizer_guide=humanizer_guide,
            review_threshold=REVIEW_THRESHOLD,
        )
        
        try:
            response = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response)
            
            # 基于规则二次校验
            issues = result.get("issues", [])
            base_score = result.get("score", 80)
            base_score = max(0, min(100, int(base_score)))

            humanization_score = result.get("humanization_score", 0)
            try:
                humanization_score = int(humanization_score)
            except (TypeError, ValueError):
                humanization_score = 0
            humanization_score = max(0, min(20, humanization_score))

            # humanizer 作为 20 分加分项，归一化到 100
            total_score = base_score + humanization_score
            score = min(100, int(total_score * 100 / 120))
            has_high_issue = any(i.get('severity') == 'high' for i in issues)
            
            # high 问题直接不通过，或分数低于阈值不通过
            approved = (
                result.get("approved", True)
                and not has_high_issue
                and score >= REVIEW_THRESHOLD
            )
            
            return {
                "score": score,
                "approved": approved,
                "issues": issues,
                "summary": result.get("summary", ""),
                "humanization_score": humanization_score,
                "humanization_summary": result.get("humanization_summary", ""),
            }
            
        except Exception as e:
            logger.error(f"审核失败: {e}")
            # 审核失败时兜底，避免静默放行
            fallback_base = 80
            humanization_score = 0
            total_score = fallback_base + humanization_score
            fallback_score = min(100, int(total_score * 100 / 120))
            has_high_issue = False
            return {
                "score": fallback_score,
                "approved": (not has_high_issue) and fallback_score >= REVIEW_THRESHOLD,
                "issues": [],
                "summary": "审核失败，使用默认结果兜底",
                "humanization_score": humanization_score,
                "humanization_summary": "",
            }
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行质量审核
        
        Args:
            state: 共享状态
            
        Returns:
            更新后的状态
        """
        if state.get('error'):
            logger.error(f"前置步骤失败，跳过质量审核: {state.get('error')}")
            state['review_score'] = 0
            state['review_approved'] = False
            state['review_issues'] = []
            return state
        
        sections = state.get('sections', [])
        if not sections:
            logger.error("没有章节内容，跳过质量审核")
            state['review_score'] = 0
            state['review_approved'] = False
            state['review_issues'] = []
            return state
        
        outline = state.get('outline', {})
        
        # 组装文档用于审核
        document_parts = []
        for section in sections:
            document_parts.append(f"## {section.get('title', '')}\n\n{section.get('content', '')}")
        
        document = '\n\n---\n\n'.join(document_parts)
        
        logger.info("开始质量审核")
        
        result = self.review(document, outline, sections)
        
        state['review_score'] = result.get('score', 80)
        state['review_approved'] = result.get('approved', True)
        state['review_issues'] = result.get('issues', [])
        state['humanization_score'] = result.get('humanization_score', 0)
        state['humanization_summary'] = result.get('humanization_summary', "")
        
        logger.info(
            f"质量审核完成: 得分 {result.get('score', 0)}, "
            f"{'通过' if result.get('approved') else '未通过'}"
        )
        if result.get("humanization_score"):
            logger.info(f"  - Humanizer-zh 得分: {result.get('humanization_score')}/20")
        
        if result.get('issues'):
            for issue in result['issues']:
                logger.info(f"  - [{issue.get('severity', 'medium')}] {issue.get('description', '')}")
        
        return state
