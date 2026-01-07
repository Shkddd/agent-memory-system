"""
Memory Summarizer:  自动生成记忆摘要
支持多种摘要方式（规则、LLM等）
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Dict
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class SummarizerStrategy(ABC):
    """摘要策略基类"""
    
    @abstractmethod
    def summarize(self, texts: List[str], max_length: int = 200) -> str:
        """
        生成摘要
        
        Args:
            texts:  待摘要的文本列表
            max_length:  摘要最大长度
            
        Returns:
            摘要文本
        """
        pass


class RuleBasedSummarizer(SummarizerStrategy):
    """基于规则的摘要器（快速、无依赖）"""
    
    def summarize(self, texts: List[str], max_length: int = 200) -> str:
        """
        简单的规则性摘要：取最长的文本 + 关键概念
        
        Args: 
            texts: 待摘要的文本列表
            max_length: 摘要最大长度
            
        Returns:
            摘要文本
        """
        if not texts:
            return ""
        
        # 选择最长的文本作为核心
        longest = max(texts, key=len)
        
        if len(longest) <= max_length:
            return longest
        
        # 超长时截断
        summary = longest[:max_length]. rstrip()
        if len(summary) < len(longest):
            summary += "..."
        
        return summary


class LLMSummarizer(SummarizerStrategy):
    """基于LLM的高质量摘要器"""
    
    def __init__(self, model:  str = "gpt-3.5-turbo", api_key: Optional[str] = None):
        """
        初始化LLM摘要器
        
        Args: 
            model: LLM模型名称
            api_key: API密钥
        """
        self.model = model
        self.api_key = api_key
        self.llm_client = None
        
        # 尝试初始化OpenAI客户端
        try:
            import openai
            if api_key:
                openai.api_key = api_key
            self.llm_client = openai
            logger.info(f"Initialized LLM Summarizer with model: {model}")
        except ImportError: 
            logger.warning("OpenAI not installed.  Falling back to rule-based summarizer.")
            self.llm_client = None
    
    def summarize(self, texts: List[str], max_length: int = 200) -> str:
        """
        使用LLM生成高质量摘要
        
        Args:
            texts: 待摘要的文本列表
            max_length: 摘要最大长度
            
        Returns:
            摘要文本
        """
        if not texts or not self.llm_client:
            # Fallback to rule-based
            return RuleBasedSummarizer().summarize(texts, max_length)
        
        combined_text = "\n".join(texts)
        
        try:
            response = self.llm_client.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"请用中文为以下内容生成摘要，不超过{max_length}字。"
                    },
                    {
                        "role": "user",
                        "content":  combined_text
                    }
                ],
                temperature=0.5,
                max_tokens=max_length // 2  # 粗估
            )
            
            summary = response.choices[0].message.content. strip()
            logger.debug(f"LLM summarized {len(texts)} texts into {len(summary)} chars")
            return summary
        
        except Exception as e: 
            logger.warning(f"LLM summarization failed: {e}. Using rule-based summarizer.")
            return RuleBasedSummarizer().summarize(texts, max_length)


class MiniLMSummarizer(SummarizerStrategy):
    """基于MiniLM的本地摘要器（离线、快速）"""
    
    def __init__(self):
        """初始化MiniLM摘要器"""
        try:
            from transformers import pipeline
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=0  # GPU if available
            )
            logger. info("Initialized MiniLM Summarizer")
        except ImportError:
            logger.warning("Transformers not installed. Falling back to rule-based summarizer.")
            self.summarizer = None
    
    def summarize(self, texts: List[str], max_length: int = 200) -> str:
        """
        使用MiniLM生成摘要（本地运行）
        
        Args:
            texts: 待摘要的文本列表
            max_length: 摘要最大长度
            
        Returns:
            摘要文本
        """
        if not texts or not self.summarizer:
            return RuleBasedSummarizer().summarize(texts, max_length)
        
        combined_text = "\n".join(texts)
        
        # BART需要至少50个tokens
        if len(combined_text) < 50:
            return RuleBasedSummarizer().summarize(texts, max_length)
        
        try:
            result = self.summarizer(
                combined_text,
                max_length=max_length // 10,
                min_length=30,
                do_sample=False
            )
            summary = result[0]['summary_text']. strip()
            logger.debug(f"MiniLM summarized {len(texts)} texts")
            return summary
        except Exception as e:
            logger. warning(f"MiniLM summarization failed: {e}")
            return RuleBasedSummarizer().summarize(texts, max_length)


class MemorySummarizer: 
    """记忆摘要管理器"""
    
    def __init__(self, strategy: SummarizerStrategy = None):
        """
        初始化摘要管理器
        
        Args:
            strategy: 摘要策略（默认使用规则式）
        """
        self.strategy = strategy or RuleBasedSummarizer()
        self.summary_history:  List[Dict] = []
    
    def summarize_memories(
        self,
        memories: List[Dict],
        max_length: int = 200,
        topic: str = "general"
    ) -> Dict:
        """
        总结一组记忆
        
        Args:
            memories: 记忆列表，每条含 'text' 字段
            max_length: 摘要最大长度
            topic: 摘要主题标签
            
        Returns: 
            摘要结果 {
                'summary': str,
                'source_count': int,
                'source_ids': List[int],
                'created_at': str,
                'topic': str
            }
        """
        if not memories:
            return {
                'summary': '',
                'source_count': 0,
                'source_ids': [],
                'created_at': datetime.now().isoformat(),
                'topic': topic
            }
        
        texts = [m. get('text', '') for m in memories if m.get('text')]
        source_ids = [m.get('id') for m in memories if 'id' in m]
        
        # 生成摘要
        summary = self.strategy.summarize(texts, max_length)
        
        result = {
            'summary': summary,
            'source_count':  len(texts),
            'source_ids': source_ids,
            'created_at': datetime. now().isoformat(),
            'topic': topic,
            'original_length': sum(len(t) for t in texts)
        }
        
        # 记录到历史
        self.summary_history.append(result)
        
        logger.info(
            f"Summarized {len(texts)} memories into {len(summary)} chars "
            f"(compression ratio: {len(summary) / max(1, result['original_length']):.2%})"
        )
        
        return result
    
    def get_summary_history(self, limit: int = 10) -> List[Dict]:
        """获取最近的摘要历史"""
        return self.summary_history[-limit:]
    
    def change_strategy(self, strategy: SummarizerStrategy):
        """切换摘要策略"""
        self.strategy = strategy
        logger.info(f"Changed summarizer strategy to {type(strategy).__name__}")
