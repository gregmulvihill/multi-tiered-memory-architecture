# Multi-Tiered Memory Architecture Orchestration Agent

> **Note:** This project is currently in pre-alpha stage. It's publicly available for collaboration, but expect significant changes as the core functionality is developed and refined.

## Overview

The Multi-Tiered Memory Architecture (MTMA) Orchestration Agent is a sophisticated system designed to provide AI systems with a human-like memory architecture. It creates a unified persistence layer across multiple AI contexts, enabling continuous learning, context preservation, and coordinated multi-agent behavior.

## Key Concepts

- **Short-Term Memory**: High-performance, rapidly accessible memory with automatic decay
- **Long-Term Memory**: Persistent, semantically rich storage with sophisticated retrieval mechanisms
- **Memory Lifecycle Management**: Controlled transitions between memory tiers with explicit policies
- **World State Management**: Shared perception of the current state across LLM contexts
- **Goal-Directed Stability**: Memory locking mechanisms to ensure goal completion

## Architecture

MTMA implements a multi-layered approach to memory management:

```
┌───────────────────────────────────────────────────────────┐
│                     LLM Contexts                          │
└───────────────┬─────────────────────┬─────────────────────┘
                │                     │
┌───────────────▼─────────────────────▼─────────────────────┐
│                  Memory Controller Service                 │
└───────────────┬─────────────────────┬─────────────────────┘
                │                     │
┌───────────────▼───────┐   ┌─────────▼───────────────────┐
│  Short-Term Memory    │   │      Long-Term Memory       │
│  (Redis)              │   │                             │
│                       │   │ ┌─────────────────────────┐ │
│ - Current world state │   │ │ Document Store (MongoDB)│ │
│ - Active goals        │   │ └─────────────────────────┘ │
│ - Recent interactions │   │                             │
│ - Locked memories     │   │ ┌─────────────────────────┐ │
│                       │   │ │ Graph Database (Neo4j)  │ │
└───────────────────────┘   │ └─────────────────────────┘ │
                            │                             │
                            │ ┌─────────────────────────┐ │
                            │ │ Vector Database (Qdrant)│ │
                            │ └─────────────────────────┘ │
                            └─────────────────────────────┘
```

## Features

- Seamless continuity between LLM sessions
- Automatic decay of less important short-term memories
- Sophisticated memory consolidation from short-term to long-term storage
- Multi-dimensional indexing for optimal retrieval
- Memory transaction management for consistency
- Embedding-based semantic similarity search
- Attention mechanisms to focus on relevant memories
- Goal tracking with dependency management
- Tiered storage with optimized performance characteristics
- Self-optimization of memory operations

## Technology Stack

- **Redis**: Short-term memory with time-based expiration
- **MongoDB**: Semi-structured long-term memory storage
- **Neo4j**: Relationship mapping between memory entities
- **Qdrant/Pinecone**: Vector embeddings for semantic search
- **Kafka**: Event streaming for memory operations
- **FastAPI**: Memory service API layer
- **Python**: Core orchestration logic

## Getting Started

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Access to Redis, MongoDB, Neo4j, and a vector database

### Installation

1. Clone the repository
```bash
git clone https://github.com/gregmulvihill/multi-tiered-memory-architecture.git
cd multi-tiered-memory-architecture
```

2. Set up the environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure the environment variables
```bash
cp .env.example .env
# Edit .env with your configuration details
```

4. Start the services
```bash
docker-compose up -d
```

5. Run the orchestration agent
```bash
python src/main.py
```

## Development Roadmap

1. **Foundation Phase**: Basic Redis-based short-term memory implementation
2. **Consolidation Phase**: Long-term storage with manual migration triggers
3. **Intelligence Phase**: Automatic memory policies and enrichment
4. **Optimization Phase**: Tiered storage and advanced retrieval
5. **Self-improvement Phase**: Self-optimizing memory operations

## Contributing

As this project is in pre-alpha stage, contributions are welcome. Please feel free to open issues or submit pull requests.

## License

[MIT License](LICENSE)

## Acknowledgments

- CogentEcho.ai for the architectural vision
- Research in cognitive psychology for memory system inspiration