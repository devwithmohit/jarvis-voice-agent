# Memory Service

**Language**: Python 3.11+
**Framework**: FastAPI + gRPC
**Purpose**: Manage all memory operations (short-term, long-term, episodic, semantic)

## 🎯 Overview

The Memory Service is the persistence layer of the Voice AI Agent platform, providing a four-tier memory architecture:

- **Short-term Memory**: Redis-backed session context with 24-hour TTL
- **Long-term Memory**: PostgreSQL user preferences and learned behaviors with confidence tracking
- **Episodic Memory**: Event history with automatic weekly summarization and 90-day retention
- **Semantic Memory**: FAISS vector embeddings for similarity search and semantic retrieval

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ (running)
- Redis 7+ (running)

### Installation

```bash
# 1. Navigate to service directory
cd services/memory-service

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.template .env
# Edit .env with your database credentials

# 5. Initialize database (if not done)
cd ../../infra
psql -U postgres -f init-db.sql

# 6. Run the service
cd ../services/memory-service
python src/main.py
```

The service will start:

- REST API on http://localhost:8001
- gRPC server on port 50051
- API docs at http://localhost:8001/docs

## 📋 API Endpoints

### Short-term Memory (Session Context)

```
POST   /api/v1/memory/short-term/store          # Store session context
POST   /api/v1/memory/short-term/retrieve       # Retrieve session context
DELETE /api/v1/memory/short-term/session/{id}   # Clear session
```

### Long-term Memory (Preferences & Behaviors)

```
POST /api/v1/memory/long-term/preference        # Store preference
POST /api/v1/memory/long-term/preferences       # Get preferences
POST /api/v1/memory/long-term/behavior          # Record behavior
POST /api/v1/memory/long-term/behaviors         # Get behaviors
```

### Episodic Memory (Events & Summaries)

```
POST /api/v1/memory/episodic/event              # Store event
POST /api/v1/memory/episodic/events             # Get events
GET  /api/v1/memory/episodic/recent/{user_id}   # Get recent events
POST /api/v1/memory/episodic/summary            # Generate summary
GET  /api/v1/memory/episodic/summaries/{user_id} # Get summaries
```

### Semantic Memory (Vector Search)

```
POST /api/v1/memory/semantic/add                # Add semantic memory
POST /api/v1/memory/semantic/search             # Search by similarity
GET  /api/v1/memory/semantic/user/{user_id}     # Get user memories
```

### Admin & User Control

```
POST /api/v1/admin/export                       # Export all user data
POST /api/v1/admin/delete                       # Delete all user data
GET  /api/v1/admin/summary/{user_id}            # Get data summary
GET  /api/v1/admin/health-check                 # Health check
```

## 🔧 Configuration

Edit `.env` file or set environment variables:

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=voice_agent
DB_USER=agent
DB_PASSWORD=changeme

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Memory Settings
SHORT_TERM_TTL=86400                    # 24 hours
EPISODIC_RETENTION_DAYS=90

# FAISS
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_DIMENSION=384
FAISS_INDEX_DIR=data/faiss_index

# Service Ports
GRPC_PORT=50051
API_PORT=8001
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_short_term.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_semantic.py::test_search_similar_memories -v
```

## 🏗️ Architecture

### Memory Store Implementations

1. **ShortTermStore** (`src/stores/short_term.py`)

   - Redis key-value store with TTL
   - Session context management
   - Automatic expiration

2. **LongTermStore** (`src/stores/long_term.py`)

   - PostgreSQL preferences table
   - Learned behaviors with confidence tracking
   - UPSERT operations for preferences
   - Confidence increases by 0.05 per behavior occurrence (max 0.95)

3. **EpisodicStore** (`src/stores/episodic.py`)

   - Event storage with timestamps
   - Weekly summary generation (PostgreSQL function)
   - Retention policy enforcement (90 days default)
   - Event statistics and filtering

4. **SemanticStore** (`src/stores/semantic.py`)
   - FAISS vector index (L2 distance)
   - Sentence-transformers embeddings (384 dimensions)
   - User-scoped semantic search
   - Disk persistence with automatic index rebuilding

### Database Schema

Key tables (see `infra/init-db.sql`):

- `user_preferences`: User settings and preferences
- `learned_behaviors`: Patterns with confidence scores
- `episodic_events`: Event history with details
- `episodic_summaries`: Weekly aggregated summaries

## 🐳 Docker Deployment

```bash
# Build image
docker build -t voice-agent/memory-service:latest .

# Run container
docker run -d \
  --name memory-service \
  -p 8001:8001 \
  -p 50051:50051 \
  -e DB_HOST=postgres \
  -e DB_PASSWORD=secret \
  -e REDIS_HOST=redis \
  --network voice-agent \
  voice-agent/memory-service:latest
```

## 📊 Monitoring

### Health Check

```bash
curl http://localhost:8001/health
```

Returns status of:

- Redis connection
- PostgreSQL connection
- FAISS index

### Metrics

```bash
curl http://localhost:8001/metrics
```

Returns:

- Vector store statistics
- Active vectors count
- Unique users count

## 🔒 Data Privacy & GDPR Compliance

The service provides full user data transparency and control:

### Export User Data

```bash
POST /api/v1/admin/export
{
  "user_id": "user123"
}
```

Returns complete data across all stores:

- All preferences
- All learned behaviors
- Recent events (90 days)
- Weekly summaries
- Semantic memories

### Delete User Data

```bash
POST /api/v1/admin/delete
{
  "user_id": "user123",
  "confirm": true
}
```

Permanently deletes all user data from:

- Short-term memory (Redis)
- Long-term memory (PostgreSQL)
- Episodic memory (PostgreSQL)
- Semantic memory (FAISS)

## 🛠️ Development

### Project Structure

```
memory-service/
├── src/
│   ├── main.py              # FastAPI application
│   ├── grpc_server.py       # gRPC service implementation
│   ├── models.py            # Pydantic models
│   ├── stores/              # Memory store implementations
│   │   ├── short_term.py
│   │   ├── long_term.py
│   │   ├── episodic.py
│   │   └── semantic.py
│   ├── api/                 # REST API routes
│   │   ├── memory_routes.py
│   │   └── admin_routes.py
│   └── utils/               # Utilities
│       ├── db.py
│       └── cache.py
├── tests/                   # Unit tests
├── config.py                # Configuration management
├── requirements.txt
├── Dockerfile
└── .env.template
```

## 📝 gRPC Service

Implements `MemoryService` from `shared/proto/memory.proto`:

- `StoreShortTerm` / `RetrieveContext` / `ClearSession`
- `StoreLongTerm` / `GetPreferences` / `GetBehaviors`
- `StoreEpisode` / `GetEpisodes` / `GenerateWeeklySummary`
- `SearchSemantic` / `AddSemantic`
- `ExportUserData` / `DeleteUserData`

## 🔗 Dependencies

- `fastapi` - REST API framework
- `uvicorn` - ASGI server
- `grpcio` - gRPC framework
- `sqlalchemy` - ORM for PostgreSQL
- `redis` - Redis client
- `faiss-cpu` - Vector similarity search
- `sentence-transformers` - Text embeddings
- `pydantic` - Data validation

## Running Locally

```bash
cd services/memory-service
pip install -r requirements.txt

# Ensure PostgreSQL and Redis are running
python -m app.main
```

## Environment Variables

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=voice_agent
DB_USER=agent
DB_PASSWORD=changeme
REDIS_HOST=localhost
REDIS_PORT=6379
VECTOR_DIMENSION=384
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## Status

**Phase**: Ready for implementation (Phase 2)
**Next Steps**:

1. Create SQLAlchemy ORM models
2. Implement Redis session manager
3. Integrate FAISS vector store
4. Build gRPC server with all RPC methods
5. Add comprehensive unit tests
