# Memory Service

**Language**: Python 3.11+
**Framework**: gRPC (asyncio)
**Purpose**: Manage all memory operations (short-term, long-term, episodic, semantic)

## Responsibilities

- **Short-term Memory**: Redis-backed session context (24-hour TTL)
- **Long-term Memory**: PostgreSQL user preferences and learned behaviors
- **Episodic Memory**: Historical event storage and weekly summaries
- **Semantic Memory**: FAISS vector embeddings for semantic search
- User transparency controls (export, delete, view)

## gRPC Service

Implements `MemoryService` from `shared/proto/memory.proto`:

- `StoreShortTerm` / `RetrieveShortTerm` / `DeleteShortTerm`
- `StoreLongTerm` / `RetrieveLongTerm` / `UpdatePreference`
- `StoreEpisode` / `RetrieveEpisodes` / `GenerateWeeklySummary`
- `SearchSemantic` / `StoreEmbedding`
- `RecordBehavior` / `GetBehaviors`
- `GetConversationContext`
- `ExportUserData` / `DeleteUserData`

## Database Schema

See `infra/init-db.sql` for PostgreSQL schema:

- `users`, `session_context`, `user_preferences`
- `learned_behaviors`, `episodic_events`, `episodic_summaries`
- `audit_log`, `user_permissions`, `rate_limits`
- `vector_embeddings`

## Vector Search

- **Model**: `all-MiniLM-L6-v2` (sentence-transformers)
- **Dimension**: 384
- **Index Type**: FAISS IVFFlat
- **Storage**: In-memory with periodic disk persistence

## Dependencies

- `sqlalchemy` - ORM for PostgreSQL
- `asyncpg` - Async PostgreSQL driver
- `redis` - Redis client
- `faiss-cpu` - Vector similarity search
- `sentence-transformers` - Text embeddings

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
