"""
Memory Manager:  Orchestrates working + long-term memory
"""
import logging
from enum import Enum
from typing import Dict, List, Optional

from working_memory import WorkingMemory
from long_term_memory import LongTermMemory
from config import MemoryManagerConfig

logger = logging.getLogger(__name__)

class MemoryPriority(Enum):
    """Memory storage priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class MemoryManager:
    """
    Unified interface for working + long-term memory
    Orchestrates retrieval and storage across both layers
    """
    
    def __init__(self, config: MemoryManagerConfig = None):
        """
        Initialize memory manager
        
        Args:
            config: MemoryManagerConfig instance
        """
        self.config = config or MemoryManagerConfig()
        
        # Initialize memory layers
        self.working_memory = WorkingMemory(
            host=self.config.redis.host,
            port=self.config.redis.port,
            db=self.config.redis.db,
            window_size=self.config.redis.max_window_size
        )
        
        self.long_term_memory = LongTermMemory(
            embedding_model=self.config.embedding. model_name,
            vector_dim=self.config.embedding. vector_dim
        )
        
        logger.info("Initialized MemoryManager")
    
    def add_interaction(self, session_id: str, role: str, content: str,
                       priority: MemoryPriority = MemoryPriority. MEDIUM,
                       metadata: Dict = None) -> bool:
        """
        Add conversation interaction
        
        Args:
            session_id: Session identifier
            role: "user" or "agent"
            content:  Message content
            priority: Storage priority
            metadata: Optional metadata
            
        Returns:
            True if successful
        """
        try:
            # Always store in working memory
            self.working_memory.add_context(
                session_id, 
                role, 
                content,
                metadata=metadata
            )
            
            # Store in long-term if high priority
            if priority in (MemoryPriority.HIGH, MemoryPriority. CRITICAL):
                meta = {
                    "session_id": session_id,
                    "role": role,
                    "priority": priority.name,
                    "type": "interaction",
                    **(metadata or {})
                }
                self.long_term_memory.add_memory(content, metadata=meta)
            
            logger.debug(f"Added {role} interaction to session {session_id}")
            return True
        except Exception as e:
            logger. error(f"Error adding interaction:  {e}")
            return False
    
    def add_fact(self, fact_text: str, user_id: str = None,
                tags: List[str] = None, priority: MemoryPriority = MemoryPriority.HIGH) -> int:
        """
        Store an explicit fact/rule in long-term memory
        
        Args:
            fact_text:  Fact content
            user_id: Associated user ID
            tags: Optional tags
            priority: Storage priority
            
        Returns:
            Memory ID
        """
        try: 
            metadata = {
                "type": "fact",
                "user_id": user_id,
                "tags": tags or [],
                "priority": priority.name
            }
            memory_id = self.long_term_memory.add_memory(fact_text, metadata=metadata)
            logger.info(f"Added fact (ID={memory_id}): {fact_text[: 50]}...")
            return memory_id
        except Exception as e: 
            logger.error(f"Error adding fact: {e}")
            raise
    
    def get_agent_context(self, session_id: str, query: str = None,
                         include_long_term: bool = True) -> str:
        """
        Build comprehensive context for agent/LLM
        
        Args: 
            session_id: Session identifier
            query: Optional query for long-term memory retrieval
            include_long_term: Whether to include long-term memories
            
        Returns:
            Formatted context string
        """
        try:
            context_parts = []
            
            # Add working memory (recent conversation)
            working_context = self.working_memory.get_context(session_id)
            if working_context: 
                context_parts.append("=== Recent Conversation ===")
                for turn in working_context:
                    role = turn.get("role", "unknown").upper()
                    content = turn.get("content", "")
                    context_parts. append(f"{role}: {content}")
            
            # Add long-term memory (if query provided)
            if include_long_term and query:
                similar_memories = self.long_term_memory.search_similar(
                    query,
                    top_k=self.config.retrieval_top_k
                )
                if similar_memories:
                    context_parts.append("\n=== Relevant Knowledge ===")
                    for result in similar_memories:
                        mem = result["memory"]
                        similarity = result["similarity"]
                        mem_type = mem.get("metadata", {}).get("type", "unknown")
                        text = mem.get("text", "")
                        context_parts. append(
                            f"[{mem_type} | relevance: {similarity:.2f}] {text}"
                        )
            
            # Join and truncate
            full_context = "\n".join(context_parts)
            max_chars = self.config.context_max_tokens * 4  # rough estimate
            if len(full_context) > max_chars:
                full_context = full_context[:max_chars] + "\n[... truncated ...]"
            
            return full_context
        except Exception as e:
            logger.error(f"Error building context: {e}")
            return ""
    
    def save_memories(self) -> bool:
        """Persist long-term memory to disk"""
        try:
            return self.long_term_memory. save_index(
                self.config.memory. index_path,
                self. config.memory.map_path
            )
        except Exception as e:
            logger.error(f"Error saving memories: {e}")
            return False
    
    def load_memories(self) -> bool:
        """Load long-term memory from disk"""
        try: 
            return self.long_term_memory. load_index(
                self. config.memory.index_path,
                self.config.memory. map_path
            )
        except Exception as e:
            logger.error(f"Error loading memories: {e}")
            return False
    
    def clear_session(self, session_id: str) -> bool:
        """Clear working memory for a session"""
        try:
            self.working_memory.clear_memory(session_id)
            logger.info(f"Cleared session {session_id}")
            return True
        except Exception as e: 
            logger.error(f"Error clearing session:  {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        return {
            "long_term":  self.long_term_memory. get_stats(),
            "working_memory_ready": True
        }
