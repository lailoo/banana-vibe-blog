"""
Planner Agent - 大纲规划
"""

import json
import logging
from typing import Dict, Any

from ..prompts.prompt_manager import get_prompt_manager

logger = logging.getLogger(__name__)


class PlannerAgent:
    """
    大纲规划师 - 负责文章结构设计
    """
    
    def __init__(self, llm_client):
        """
        初始化 Planner Agent
        
        Args:
            llm_client: LLM 客户端
        """
        self.llm = llm_client
    
    def generate_outline(
        self,
        topic: str,
        article_type: str,
        target_audience: str,
        target_length: str,
        background_knowledge: str = "",
        key_concepts: list = None,
        on_stream: callable = None
    ) -> Dict[str, Any]:
        """
        生成文章大纲
        
        Args:
            topic: 技术主题
            article_type: 文章类型
            target_audience: 目标受众
            target_length: 目标长度
            background_knowledge: 背景知识
            key_concepts: 核心概念列表
            on_stream: 流式回调函数 (delta, accumulated) -> None
            
        Returns:
            大纲字典
        """
        key_concepts = key_concepts or []
        
        pm = get_prompt_manager()
        prompt = pm.render_planner(
            topic=topic,
            article_type=article_type,
            target_audience=target_audience,
            target_length=target_length,
            background_knowledge=background_knowledge,
            key_concepts=key_concepts
        )
        
        try:
            # 如果有流式回调且 LLM 支持流式，使用流式生成
            has_stream = hasattr(self.llm, 'chat_stream')
            
            if on_stream and has_stream:
                accumulated = ""
                def on_chunk(delta, acc):
                    nonlocal accumulated
                    accumulated = acc
                    on_stream(delta, acc)
                
                response = self.llm.chat_stream(
                    messages=[{"role": "user", "content": prompt}],
                    on_chunk=on_chunk
                )
            else:
                response = self.llm.chat(
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
            
            # 解析 JSON（可能包含 markdown 代码块）
            response_text = response.strip()
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                response_text = response_text[start:end].strip()
            elif '```' in response_text:
                start = response_text.find('```') + 3
                end = response_text.find('```', start)
                response_text = response_text[start:end].strip()
            
            outline = json.loads(response_text)
            
            # 验证必要字段
            required_fields = ['title', 'sections']
            for field in required_fields:
                if field not in outline:
                    raise ValueError(f"大纲缺少必要字段: {field}")
            
            # 为每个章节添加 ID (如果没有)
            for i, section in enumerate(outline.get('sections', [])):
                if 'id' not in section:
                    section['id'] = f"section_{i + 1}"
            
            return outline
            
        except json.JSONDecodeError as e:
            logger.error(f"大纲 JSON 解析失败: {e}")
            raise ValueError(f"大纲生成失败: JSON 解析错误")
        except Exception as e:
            logger.error(f"大纲生成失败: {e}")
            raise
    
    def run(self, state: Dict[str, Any], on_stream: callable = None) -> Dict[str, Any]:
        """
        执行大纲规划
        
        Args:
            state: 共享状态
            on_stream: 流式回调函数 (delta, accumulated) -> None
            
        Returns:
            更新后的状态
        """
        logger.info(f"开始生成大纲: {state.get('topic', '')}")
        
        try:
            outline = self.generate_outline(
                topic=state.get('topic', ''),
                article_type=state.get('article_type', 'tutorial'),
                target_audience=state.get('target_audience', 'intermediate'),
                target_length=state.get('target_length', 'medium'),
                background_knowledge=state.get('background_knowledge', ''),
                key_concepts=state.get('key_concepts', []),
                on_stream=on_stream
            )
            
            state['outline'] = outline
            logger.info(f"大纲生成完成: {outline.get('title', '')}, {len(outline.get('sections', []))} 个章节")
            
        except Exception as e:
            state['error'] = f"大纲生成失败: {str(e)}"
            logger.error(state['error'])
        
        return state
