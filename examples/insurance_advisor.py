"""
Insurance Advisor Agent
Demonstrates domain-specific use case with memory
"""
import logging
from typing import List, Dict

from src.memory_manager import MemoryManager, MemoryPriority

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InsuranceAdvisor:
    """Insurance consultation advisor with memory"""
    
    def __init__(self):
        self.memory = MemoryManager()
        self._load_product_knowledge()
    
    def _load_product_knowledge(self):
        """Load product knowledge into memory"""
        products = [
            {
                "name": "保额50万重疾险",
                "age":  "30岁",
                "monthly_fee": "150-200元",
                "waiting_period": "90天",
                "description": "30岁男性重疾险优先选保额50万以上、等待期90天的产品"
            },
            {
                "name": "线上重疾险",
                "underwriting": "宽松",
                "for_user": "非标体客户（甲状腺结节）",
                "description": "非标体客户（甲状腺结节）推荐核保宽松的线上重疾险"
            },
            {
                "name":  "消费型保险",
                "type": "消费型",
                "characteristic": "低保费、高杠杆",
                "description": "用户偏好低保费、高杠杆的消费型保险"
            }
        ]
        
        for product in products:
            self.memory.add_fact(
                product["description"],
                tags=["product", "recommendation"],
                priority=MemoryPriority.HIGH
            )
        
        logger.info(f"✓ Loaded {len(products)} product recommendations")
    
    def consult_customer(self, session_id: str, customer_info: Dict) -> str:
        """
        Provide insurance consultation based on customer info
        
        Args:
            session_id: Unique session identifier
            customer_info: Customer information dict
                - age: Customer age
                - has_medical_history: Whether customer has medical conditions
                - preference: Insurance preference (low-cost, long-term, etc.)
        
        Returns:
            Recommendation string
        """
        age = customer_info.get("age")
        has_medical_history = customer_info.get("has_medical_history", False)
        preference = customer_info.get("preference", "")
        
        # Store customer info in working memory
        info_text = f"客户年龄: {age}岁, 医疗历史: {'有' if has_medical_history else '无'}, 偏好:  {preference}"
        self.memory.add_interaction(session_id, "user", info_text)
        
        # Get relevant recommendations from long-term memory
        query = f"{age}岁 {'非标体' if has_medical_history else '标准体'} {preference}"
        recommendations = self. memory.long_term_memory.search_similar(query, top_k=3)
        
        # Build recommendation
        recommendation = self._build_recommendation(age, has_medical_history, recommendations)
        
        # Store recommendation in working memory
        self. memory.add_interaction(session_id, "agent", recommendation, priority=MemoryPriority.HIGH)
        
        return recommendation
    
    def _build_recommendation(self, age: int, has_medical_history: bool, 
                             similar_memories: List) -> str:
        """Build recommendation based on customer profile and knowledge"""
        
        recommendation = "根据您的信息，我为您推荐以下方案：\n\n"
        
        # Add basic recommendation based on age
        if age < 30:
            recommendation += f"1. 您年龄较年轻，建议选择消费型重疾险，高杠杆、低保费\n"
        elif 30 <= age < 40:
            recommendation += f"2. 您{age}岁，正值事业上升期，建议保额50万以上、等待期90天的重疾险\n"
        else:
            recommendation += f"3. 您{age}岁，建议选择终身重疾险，确保终身保障\n"
        
        # Add medical history considerations
        if has_medical_history: 
            recommendation += "2. 由于您有既往病史，推荐选择核保相对宽松的线上重疾险\n"
        
        # Add knowledge-based recommendations
        if similar_memories:
            recommendation += "3. 基于我们的知识库：\n"
            for memory in similar_memories:
                text = memory["memory"]["text"]
                similarity = memory["similarity"]
                if similarity > 0.5:  # Only include relevant suggestions
                    recommendation += f"   - {text}\n"
        
        recommendation += "\n请问您对哪个方案感兴趣？我可以为您详细介绍产品条款。"
        
        return recommendation
    
    def simulate_consultation(self):
        """Simulate a complete consultation session"""
        
        logger.info("\n=== Insurance Advisor Simulation ===\n")
        
        customers = [
            {
                "id": "cust_001",
                "age":  28,
                "name": "张三",
                "has_medical_history": False,
                "preference": "低保费"
            },
            {
                "id": "cust_002",
                "age": 35,
                "name": "李四",
                "has_medical_history": True,
                "preference": "核保宽松"
            },
            {
                "id":  "cust_003",
                "age": 45,
                "name": "王五",
                "has_medical_history": False,
                "preference": "终身保障"
            }
        ]
        
        for customer in customers:
            session_id = f"consultation_{customer['id']}"
            
            logger.info(f"{'='*50}")
            logger. info(f"客户:  {customer['name']} ({customer['age']}岁)")
            logger.info(f"{'='*50}")
            
            recommendation = self.consult_customer(session_id, {
                "age": customer["age"],
                "has_medical_history": customer["has_medical_history"],
                "preference": customer["preference"]
            })
            
            print(recommendation)
            print("\n")
        
        # Save all consultations
        self.memory.save_memories()
        logger.info("✓ All consultations saved\n")


if __name__ == "__main__":
    advisor = InsuranceAdvisor()
    advisor.simulate_consultation()
