# Agent Memory System

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)

A sophisticated memory management system for AI agents, enabling persistent, efficient, and intelligent memory operations across multiple agent instances.

[Features](#features) • [Quick Start](#quick-start) • [Documentation](#documentation) • [Contributing](#contributing)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Docker Deployment](#docker-deployment)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Agent Memory System is a robust, production-ready memory management framework designed for AI agents and autonomous systems. It provides a unified interface for managing different types of memories (short-term, long-term, semantic, episodic), enabling agents to learn from past interactions, make informed decisions, and maintain context across sessions.

### Key Capabilities

- **Multi-tier Memory Architecture**: Working memory (Redis) + Long-term memory (FAISS)
- **Vector Embeddings**: Semantic similarity search using sentence-transformers
- **Persistence Layer**: Save/load memory indices to disk
- **Context Management**:  Automatic sliding window for conversation context
- **Thread-Safe**:  Safe for concurrent agent operations
- **Extensible Design**: Easy to integrate with LLM APIs

---

## Features

✅ **Short-term Memory (Working Memory)**
- Redis-based session context
- Sliding window for recent conversations
- Automatic TTL-based cleanup
- Fast retrieval

✅ **Long-term Memory**
- FAISS vector indexing for similarity search
- Persistent storage to disk
- Metadata and tagging support
- Semantic search capabilities

✅ **Memory Manager**
- Unified interface for both memory layers
- Priority-based storage
- Context building for LLM prompts
- Memory statistics and monitoring

✅ **Production Ready**
- Error handling and logging
- Configuration management
- Docker deployment support
- Example implementations

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/Shkddd/agent-memory-system.git
cd agent-memory-system

# Install dependencies
pip install -r requirements.txt

# Start Redis
docker run -d -p 6379:6379 redis:latest
```

### Basic Usage

```python
from src.memory_manager import MemoryManager, MemoryPriority

# Initialize memory manager
memory = MemoryManager()

session_id = "user_001"

# Add user input
memory.add_interaction(
    session_id,
    "user",
    "我想咨询保险产品",
    priority=MemoryPriority. MEDIUM
)

# Add agent response
memory.add_interaction(
    session_id,
    "agent",
    "您好，我可以为您介绍我们的保险产品",
    priority=MemoryPriority. MEDIUM
)

# Add important fact to long-term memory
memory.add_fact(
    "30岁男性推荐保额50万以上的重疾险",
    user_id="user_001",
    tags=["insurance", "recommendation"]
)

# Get context for LLM
context = memory.get_agent_context(
    session_id,
    query="推荐什么保险产品？",
    include_long_term=True
)

print(context)

# Save memories to disk
memory.save_memories()
```

### Running Examples

```bash
# Insurance advisor example
python examples/insurance_advisor.py

# Chat with memory
python examples/chat_with_memory.py

# Run tests
pytest tests/
```

---

## Docker Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Quick Start with Docker

```bash
# Build and start services
docker-compose up -d

# Check logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Docker Architecture

The Docker setup includes:

- **Redis**: Message store and session management
- **Agent App**: Python application with memory system
- **Network**: Internal communication between services

### Configuration

Modify `.env` or `docker-compose.yml`:

```env
# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Application
LOG_LEVEL=INFO
MAX_MEMORY_SIZE=10000
```

### Volumes

Data persistence is configured in `docker-compose.yml`:

```yaml
volumes:
  - ./data:/app/data        # Memory indices
  - redis_data:/data/redis  # Redis persistence
```

### Scaling

To run multiple agent instances:

```bash
docker-compose up -d --scale app=3
```

---

## Project Structure

```
agent-memory-system/
├── src/
│   ├── __init__.py
│   ├── config.py                  # Configuration
│   ├── embedding_util.py          # Text embeddings
│   ├── working_memory.py          # Redis short-term memory
│   ├── long_term_memory.py        # FAISS long-term memory
│   ├── memory_manager.py          # Orchestration layer
│   └── agent.py                   # Agent implementation
├── tests/
│   ├── conftest.py
│   ├── test_working_memory.py
│   ├── test_long_term_memory.py
│   └── test_memory_manager.py
├── examples/
│   ├── insurance_advisor.py
��   └── chat_with_memory.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── . env.example
├── README.md
└── pytest.ini
```

---

## Configuration

### Environment Variables

Create `.env` file:

```env
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Memory Settings
MAX_WINDOW_SIZE=10
VECTOR_DIM=384
RETRIEVAL_TOP_K=3
CONTEXT_MAX_TOKENS=2000

# Logging
LOG_LEVEL=INFO
```

### Python Configuration

```python
from src.config import MemoryManagerConfig

config = MemoryManagerConfig(
    retrieval_top_k=5,
    context_max_tokens=3000
)
```

---

## API Reference

### MemoryManager

#### `add_interaction()`

Add conversation turn to memory.

```python
memory.add_interaction(
    session_id:  str,
    role: str,  # "user" or "agent"
    content: str,
    priority: MemoryPriority = MemoryPriority. MEDIUM,
    metadata: Dict = None
) -> bool
```

#### `add_fact()`

Store explicit fact in long-term memory.

```python
memory.add_fact(
    fact_text: str,
    user_id: str = None,
    tags: List[str] = None,
    priority: MemoryPriority = MemoryPriority.HIGH
) -> int
```

#### `get_agent_context()`

Retrieve combined context for LLM.

```python
memory.get_agent_context(
    session_id: str,
    query: str = None,
    include_long_term: bool = True
) -> str
```

#### `save_memories()`

Persist long-term memory to disk.

```python
memory.save_memories() -> bool
```

#### `load_memories()`

Load long-term memory from disk.

```python
memory.load_memories() -> bool
```

#### `get_stats()`

Get memory statistics.

```python
memory.get_stats() -> Dict
```

---

## Usage Examples

### Example 1: Conversation with Memory

```python
from src.memory_manager import MemoryManager

memory = MemoryManager()
session_id = "conversation_001"

# Simulate multi-turn conversation
conversations = [
    ("user", "我叫张三，今年30岁"),
    ("agent", "很高兴认识您，张三。请问您对保险感兴趣吗？"),
    ("user", "是的，我想了解重疾险"),
    ("agent", "重疾险很重要。根据您30岁的年龄，推荐保额50万以上")
]

for role, content in conversations:
    memory.add_interaction(session_id, role, content)

# Later:  retrieve context
context = memory.get_agent_context(
    session_id,
    query="用户的基本信息是什么？"
)
print(context)
```

### Example 2: Semantic Search

```python
from src.memory_manager import MemoryManager, MemoryPriority

memory = MemoryManager()

# Add domain knowledge
facts = [
    "30岁男性重疾险优先选保额50万以上、等待期90天的产品",
    "非标体客户（甲状腺结节）推荐核保宽松的线上重疾险",
    "用户偏好低保费、高杠杆的消费型保险"
]

for fact in facts:
    memory. add_fact(fact, tags=["insurance"])

# Search relevant knowledge
results = memory.long_term_memory.search_similar(
    "30岁男性买什么重疾险好？",
    top_k=2
)

for result in results:
    print(f"相似度: {result['similarity']:. 2f}")
    print(f"记忆:  {result['memory']['text']}")
```

### Example 3: Persistent Memory

```python
from src.memory_manager import MemoryManager

# Create and populate memory
memory = MemoryManager()
memory.add_fact("用户喜欢健身", user_id="user_001")
memory.add_fact("用户关心投资回报", user_id="user_001")

# Save to disk
memory.save_memories("./data/memories. faiss", "./data/memories.json")

# Later session:  load memories
new_memory = MemoryManager()
new_memory.load_memories("./data/memories.faiss", "./data/memories.json")

# Use loaded memories
context = new_memory.get_agent_context("session_002", query="用户有什么特点？")
```

---

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test
pytest tests/test_memory_manager.py -v
```

---

## Performance Considerations

### Memory Optimization

- **Working Memory**: Redis limits window to 10 turns (configurable)
- **Long-term Memory**: FAISS IndexFlatL2 for accurate search
- **Embedding Model**: `all-MiniLM-L6-v2` (384-dim, fast & accurate)

### Scaling

For production with large memory: 

- Increase FAISS index type to `IndexIVFFlat` for speed
- Use PostgreSQL for metadata storage
- Implement memory consolidation/cleanup policies
- Add caching layer for frequent queries

---

## Troubleshooting

### Redis Connection Error

```bash
# Check if Redis is running
redis-cli ping

# Start Redis
docker run -d -p 6379:6379 redis:latest
```

### Model Download Timeout

```bash
# Pre-download embedding model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### Memory Index Not Found

```python
# Create new memory if file not found
memory = MemoryManager()
memory.save_memories()  # Create new indices
```

---

## Contributing

Contributions are welcome! Please: 

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and add tests
4. Submit a pull request

---

## License

MIT License - See LICENSE file for details

---

## Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Documentation**: See docs/ folder

---

**Made with ❤️ for AI agents**
