"""
Interactive chatbot with memory system
Demonstrates multi-turn conversations with persistent memory
"""
import logging
import sys
from typing import Optional

from src.memory_manager import MemoryManager, MemoryPriority
from src.agent import MemoryAwareAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChatBot:
    """Interactive chatbot with memory"""
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize chatbot
        
        Args:
            session_id: Optional session identifier (generated if not provided)
        """
        self.session_id = session_id or "chat_session_default"
        self.memory_manager = MemoryManager()
        self.agent = MemoryAwareAgent(self.memory_manager)
        self.turn_count = 0
        
        logger.info(f"Initialized ChatBot (Session: {self.session_id})")
        
        # Initialize some knowledge
        self._initialize_knowledge()
    
    def _initialize_knowledge(self):
        """Initialize bot knowledge base"""
        knowledge_base = [
            "我是保险咨询机器人，可以为您介绍各种保险产品",
            "30岁男性重疾险优先选保额50万以上、等待期90天的产品",
            "非标体客户（甲状腺结节）推荐核保宽松的线上重疾险",
            "消费型重疾险具有低保费、高杠杆的特点",
            "终身重疾险提供终身保障，性价比较高",
        ]
        
        for fact in knowledge_base:
            self.memory_manager.add_fact(fact, tags=["insurance", "knowledge_base"])
        
        logger.info(f"✓ Initialized knowledge base with {len(knowledge_base)} facts")
    
    def process_input(self, user_input: str) -> str:
        """
        Process user input and generate response
        
        Args: 
            user_input: User message
            
        Returns:
            Agent response
        """
        self. turn_count += 1
        
        # Get context from memory
        context = self.memory_manager.get_agent_context(
            self.session_id,
            query=user_input,
            include_long_term=True
        )
        
        # Generate response
        response = self._generate_response(user_input, context)
        
        # Store interaction in memory
        self.memory_manager.add_interaction(
            self.session_id,
            "user",
            user_input,
            priority=MemoryPriority.MEDIUM
        )
        
        self.memory_manager.add_interaction(
            self.session_id,
            "agent",
            response,
            priority=MemoryPriority. MEDIUM
        )
        
        return response
    
    def _generate_response(self, user_input: str, context: str) -> str:
        """
        Generate response (simplified version)
        In production, this would call an actual LLM
        """
        # Simple rule-based responses for demo
        user_input_lower = user_input.lower()
        
        if any(keyword in user_input_lower for keyword in ["30", "30岁", "三十"]):
            return "根据您30岁的年龄，我建议选择保额50万以上、等待期90天的重疾险产品。这样既能获得充分保障，又能控制保费成本。"
        
        elif any(keyword in user_input_lower for keyword in ["保费", "多少钱", "价格", "费用"]):
            return "消费型重疾险的月保费通常在150-200元，具体取决于您选择的保额和等待期。我可以为您推荐几个产品方案。"
        
        elif any(keyword in user_input_lower for keyword in ["推荐", "建议", "哪个好", "怎么选"]):
            return "基于您的信息和市场情况，我推荐以下方案：\n1. 消费型重疾险 - 高杠杆、低保费\n2. 终身重疾险 - 终身保障、性价比高\n请告诉我您更偏好哪种？"
        
        elif any(keyword in user_input_lower for keyword in ["谢谢", "感谢", "thanks"]):
            return "不客气！如果您还有其他问题，随时可以问我。"
        
        else:
            return f"感谢您的提问。{user_input}\n\n我正在根据我们的对话历史和知识库为您提供最佳建议。请告诉我您是否需要更多信息？"
    
    def show_session_info(self):
        """Display session information"""
        stats = self.memory_manager.get_stats()
        logger.info("\n" + "="*60)
        logger.info(f"Session: {self.session_id}")
        logger.info(f"Turns: {self.turn_count}")
        logger.info(f"Long-term Memories: {stats['long_term']['total_memories']}")
        logger.info("="*60 + "\n")
    
    def save_session(self):
        """Save session to disk"""
        try:
            self.memory_manager.save_memories()
            logger.info("✓ Session saved successfully")
        except Exception as e: 
            logger.error(f"Error saving session: {e}")
    
    def clear_session(self):
        """Clear session memory"""
        self.memory_manager.clear_session(self.session_id)
        self.turn_count = 0
        logger.info("✓ Session cleared")


def run_interactive_chat():
    """Run interactive chat session"""
    
    print("\n" + "="*60)
    print("Agent Memory System - Interactive Chat")
    print("="*60 + "\n")
    print("Commands:")
    print("  'help'   - Show help information")
    print("  'info'   - Show session information")
    print("  'save'   - Save session to disk")
    print("  'clear'  - Clear session memory")
    print("  'quit'   - Exit chatbot\n")
    print("Start chatting below:\n")
    
    bot = ChatBot(session_id="interactive_session")
    
    while True: 
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "quit":
                print("\nBot: 再见！感谢您的使用。")
                bot.save_session()
                break
            
            elif user_input.lower() == "help":
                print("\nBot: 我是保险咨询机器人。您可以问我关于保险产品的问题。")
                print("     我会根据您的信息和我的知识库为您推荐最合适的产品。\n")
                continue
            
            elif user_input.lower() == "info":
                bot.show_session_info()
                continue
            
            elif user_input.lower() == "save":
                bot.save_session()
                continue
            
            elif user_input.lower() == "clear":
                bot.clear_session()
                print("Bot: 会话已清除\n")
                continue
            
            # Process normal input
            response = bot.process_input(user_input)
            print(f"Bot: {response}\n")
        
        except KeyboardInterrupt: 
            print("\n\nBot: 再见！")
            bot.save_session()
            break
        except Exception as e: 
            logger.error(f"Error processing input: {e}")
            print("Bot: 抱歉，处理您的请求时出现错误。请重试。\n")


if __name__ == "__main__":
    run_interactive_chat()
