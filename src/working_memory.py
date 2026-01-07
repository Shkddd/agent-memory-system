"""
Working Memory:  Redis-based short-term context management with sliding window
"""
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import redis

logger = logging.getLogger(__name__)

class WorkingMemory: 
    """
    Short-term memory using Redis
    - Stores recent conversation turns with sliding window
    - Session-scoped with configurable TTL
    """
    
    def __init__(self, host: str = "localhost", port:  int = 6379, 
                 db: int = 0, window_size: int = 10):
        """
        Initialize Redis working memory
        
        Args: 
            host: Redis host
            port: Redis port
            db: Redis database number
            window_size: Max conversation turns to keep
        """
        try:
            self.client = redis.Redis(
                host=host, 
                port=port, 
                db=db,
                decode_responses=False
            )
            self.client.ping()
            self.window_size = window_size
            logger.info(f"Connected to Redis at {host}:{port}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def add_context(self, session_id: str, role: str, content: str, 
                   metadata: Dict = None) -> bool:
        """
        Add a single conversation turn to working memory
        
        Args: 
            session_id: Unique session identifier
            role: "user" or "agent"
            content: Message content
            metadata: Optional metadata dict
            
        Returns:
            True if successful, False otherwise
        """
        try:
            round_data = {
                "role": role,
                "content": content,
                "timestamp":  datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            key = f"agent: working_memory:{session_id}"
            
            # Get existing context
            existing = self.client.lrange(key, 0, -1)
            existing_list = [json.loads(item) for item in existing] if existing else []
            
            # Append new turn
            existing_list.append(round_data)
            
            # Sliding window:  keep only last N turns
            if len(existing_list) > self.window_size:
                existing_list = existing_list[-self.window_size:]
            
            # Write back to Redis
            self.client.delete(key)
            for item in existing_list:
                self.client.rpush(key, json.dumps(item))
            
            # Set expiration (24 hours)
            self.client.expire(key, int(timedelta(hours=24).total_seconds()))
            
            logger. debug(f"Added context to session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding context:  {e}")
            return False
    
    def get_context(self, session_id: str) -> List[Dict]:
        """
        Retrieve all context for a session
        
        Args:
            session_id:  Session identifier
            
        Returns: 
            List of conversation turn dicts
        """
        try: 
            key = f"agent: working_memory:{session_id}"
            existing = self.client.lrange(key, 0, -1)
            return [json.loads(item) for item in existing] if existing else []
        except Exception as e: 
            logger.error(f"Error retrieving context: {e}")
            return []
    
    def get_context_text(self, session_id: str) -> str:
        """
        Get context as formatted text (for LLM prompts)
        
        Args: 
            session_id: Session identifier
            
        Returns:
            Formatted conversation string
        """
        context = self.get_context(session_id)
        if not context:
            return ""
        
        lines = []
        for turn in context:
            role = turn.get("role", "unknown").upper()
            content = turn.get("content", "")
            lines.append(f"{role}: {content}")
        
        return "\n".join(lines)
    
    def clear_memory(self, session_id: str) -> bool:
        """
        Clear all context for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful
        """
        try: 
            key = f"agent:working_memory:{session_id}"
            self.client.delete(key)
            logger.info(f"Cleared working memory for session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")
            return False
    
    def get_session_stats(self, session_id: str) -> Dict:
        """Get statistics for a session"""
        context = self.get_context(session_id)
        return {
            "session_id": session_id,
            "num_turns": len(context),
            "user_turns": sum(1 for c in context if c.get("role") == "user"),
            "agent_turns": sum(1 for c in context if c.get("role") == "agent"),
        }
