"""
Long-term Memory: FAISS-based vector indexing + persistence
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import faiss

from embedding_util import EmbeddingUtil

logger = logging.getLogger(__name__)

class LongTermMemory:
    """
    Long-term memory using FAISS vector index
    - Stores facts, experiences, user preferences
    - Persistent across sessions
    - Supports similarity search
    """
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2", 
                 vector_dim: int = 384):
        """
        Initialize long-term memory
        
        Args: 
            embedding_model: HuggingFace model for embeddings
            vector_dim: Embedding vector dimension
        """
        self.embedding_util = EmbeddingUtil(embedding_model)
        self.vector_dim = vector_dim
        self.index = faiss.IndexFlatL2(vector_dim)
        self.id_to_memory: Dict[int, Dict] = {}
        self.next_id = 0
        logger.info("Initialized LongTermMemory")
    
    def add_memory(self, memory_text: str, metadata: Dict = None) -> int:
        """
        Add a memory entry (fact, experience, preference)
        
        Args: 
            memory_text: Text content of the memory
            metadata: Optional metadata (type, user_id, tags, etc.)
            
        Returns:
            Memory ID
        """
        try:
            # Encode text to embedding
            embedding = self. embedding_util.get_embedding(memory_text)
            
            # Add to FAISS index
            self.index.add(np.array([embedding], dtype=np.float32))
            
            # Store memory content + metadata
            self.id_to_memory[self.next_id] = {
                "text":  memory_text,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                "id": self.next_id
            }
            
            memory_id = self.next_id
            self.next_id += 1
            
            logger. debug(f"Added memory #{memory_id}:  {memory_text[: 50]}...")
            return memory_id
        except Exception as e: 
            logger.error(f"Error adding memory: {e}")
            raise
    
    def search_similar(self, query_text: str, top_k: int = 3) -> List[Dict]:
        """
        Search for similar memories
        
        Args:
            query_text: Query text
            top_k: Number of results to return
            
        Returns: 
            List of dicts with similarity scores and memory content
        """
        try: 
            if self.index.ntotal == 0:
                logger.warning("Memory index is empty")
                return []
            
            # Encode query
            query_embedding = self.embedding_util.get_embedding(query_text)
            
            # Search
            distances, ids = self.index.search(
                np.array([query_embedding], dtype=np.float32), 
                min(top_k, self.index.ntotal)
            )
            
            results = []
            for idx, dist in zip(ids[0], distances[0]):
                if idx >= 0 and idx in self.id_to_memory:
                    # Normalize distance to similarity (0-1)
                    similarity = 1.0 / (1.0 + float(dist))
                    results. append({
                        "id":  int(idx),
                        "similarity": similarity,
                        "distance": float(dist),
                        "memory":  self.id_to_memory[idx]
                    })
            
            return results
        except Exception as e: 
            logger.error(f"Error searching similar memories: {e}")
            return []
    
    def get_memory(self, memory_id:  int) -> Optional[Dict]:
        """Get a specific memory by ID"""
        return self.id_to_memory.get(memory_id)
    
    def update_memory(self, memory_id: int, text: str = None, 
                     metadata:  Dict = None) -> bool:
        """Update memory text or metadata"""
        try:
            if memory_id not in self. id_to_memory:
                return False
            
            if text: 
                self.id_to_memory[memory_id]["text"] = text
            
            if metadata:
                self. id_to_memory[memory_id]["metadata"]. update(metadata)
            
            self.id_to_memory[memory_id]["updated_at"] = datetime.now().isoformat()
            return True
        except Exception as e: 
            logger.error(f"Error updating memory: {e}")
            return False
    
    def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory (logical delete - keeps index intact)"""
        try:
            if memory_id in self.id_to_memory:
                self.id_to_memory[memory_id]["deleted_at"] = datetime.now().isoformat()
                logger.debug(f"Deleted memory #{memory_id}")
                return True
            return False
        except Exception as e:
            logger. error(f"Error deleting memory: {e}")
            return False
    
    def save_index(self, index_path: str = "data/memory_index.faiss",
                  map_path: str = "data/memory_map.json") -> bool:
        """
        Persist memory index and metadata to disk
        
        Args: 
            index_path: Path to save FAISS index
            map_path: Path to save memory map JSON
            
        Returns:
            True if successful
        """
        try:
            # Create data directory if needed
            Path(index_path).parent.mkdir(parents=True, exist_ok=True)
            
            faiss.write_index(self. index, index_path)
            with open(map_path, "w", encoding="utf-8") as f:
                json.dump(self.id_to_memory, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved memory index to {index_path} and {map_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            return False
    
    def load_index(self, index_path: str = "data/memory_index.faiss",
                  map_path: str = "data/memory_map.json") -> bool:
        """
        Load memory index and metadata from disk
        
        Args:
            index_path: Path to FAISS index
            map_path: Path to memory map JSON
            
        Returns:
            True if successful
        """
        try: 
            self.index = faiss.read_index(index_path)
            with open(map_path, "r", encoding="utf-8") as f:
                memory_dict = json.load(f)
                # Convert string keys to int
                self.id_to_memory = {int(k): v for k, v in memory_dict.items()}
            
            # Restore next_id
            if self.id_to_memory:
                self.next_id = max(int(k) for k in self.id_to_memory.keys()) + 1
            
            logger.info(f"Loaded memory index from {index_path}")
            return True
        except FileNotFoundError:
            logger. warning(f"Memory index files not found at {index_path}")
            return False
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        return {
            "total_memories":  len(self.id_to_memory),
            "index_size": self.index.ntotal,
            "vector_dim": self.vector_dim,
            "memories_by_type": self._count_by_type()
        }
    
    def _count_by_type(self) -> Dict[str, int]:
        """Count memories by type"""
        counts = {}
        for mem in self.id_to_memory. values():
            mem_type = mem.get("metadata", {}).get("type", "unknown")
            counts[mem_type] = counts.get(mem_type, 0) + 1
        return counts
