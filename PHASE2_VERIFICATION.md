# Phase 2 Verification Checklist

Use this checklist to verify the Memory Service implementation.

## ✅ Prerequisites

- [ ] PostgreSQL 15+ is running (port 5432)
- [ ] Redis 7+ is running (port 6379)
- [ ] Python 3.11+ is installed
- [ ] Database schema initialized (`infra/init-db.sql`)

```bash
# Check PostgreSQL
docker ps | grep postgres
# or
psql -U agent -d voice_agent -c "SELECT version();"

# Check Redis
docker ps | grep redis
# or
redis-cli ping

# Check Python
python --version  # Should be 3.11+
```

## ✅ Installation

- [ ] Virtual environment created
- [ ] Dependencies installed from requirements.txt
- [ ] .env file created from .env.template
- [ ] .env configured with correct database credentials
- [ ] Data directory exists (`data/faiss_index`)

```bash
cd services/memory-service

# Create venv
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install deps
pip install -r requirements.txt

# Setup config
cp .env.template .env
# Edit .env with your settings

# Create data directory
mkdir -p data/faiss_index
```

## ✅ Unit Tests

Run all tests to verify core functionality:

```bash
cd services/memory-service
pytest tests/ -v
```

Expected output:

- [ ] test_short_term.py: 15 tests PASSED
- [ ] test_long_term.py: 14 tests PASSED
- [ ] test_semantic.py: 16 tests PASSED
- [ ] Total: 45 tests PASSED in <5 seconds

## ✅ Service Startup

- [ ] Service starts without errors
- [ ] PostgreSQL connection successful
- [ ] Redis connection successful
- [ ] gRPC server starts on port 50051
- [ ] REST API starts on port 8001
- [ ] FAISS index initializes

```bash
python src/main.py
```

Expected console output:

```
===========================================================
Starting memory-service
===========================================================
✓ gRPC server starting on port 50051
✓ Redis connection: OK
✓ PostgreSQL connection: OK
===========================================================
✓ REST API running on http://0.0.0.0:8001
✓ Documentation available at http://0.0.0.0:8001/docs
===========================================================
```

## ✅ Health Check

- [ ] Health endpoint returns 200 OK
- [ ] All components show "healthy" status

```bash
curl http://localhost:8001/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "memory-service",
  "version": "1.0.0",
  "timestamp": "2026-01-17T...",
  "components": {
    "redis": "healthy",
    "postgresql": "healthy",
    "faiss": "healthy (0 vectors)"
  }
}
```

## ✅ API Documentation

- [ ] Swagger UI accessible
- [ ] All 22 endpoints visible
- [ ] Request/response schemas shown

```bash
# Open in browser
http://localhost:8001/docs
```

Expected:

- Memory endpoints under "memory" tag
- Admin endpoints under "admin" tag
- Try it out functionality works

## ✅ Short-term Memory Tests

Test Redis-backed session storage:

```bash
# Store context
curl -X POST http://localhost:8001/api/v1/memory/short-term/store \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_session_001",
    "key": "user_name",
    "value": "Alice",
    "ttl_seconds": 3600
  }'

# Expected: {"success": true, "message": "Context stored successfully"}

# Retrieve context
curl -X POST http://localhost:8001/api/v1/memory/short-term/retrieve \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test_session_001"}'

# Expected: {"session_id": "test_session_001", "context": {"user_name": "Alice"}}

# Clear session
curl -X DELETE http://localhost:8001/api/v1/memory/short-term/session/test_session_001
```

- [ ] Store returns success
- [ ] Retrieve returns stored value
- [ ] Clear removes data

## ✅ Long-term Memory Tests

Test PostgreSQL preferences and behaviors:

```bash
# Store preference
curl -X POST http://localhost:8001/api/v1/memory/long-term/preference \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user001",
    "category": "ui",
    "key": "theme",
    "value": "dark"
  }'

# Expected: {"success": true, "message": "Preference stored successfully"}

# Get preferences
curl -X POST http://localhost:8001/api/v1/memory/long-term/preferences \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user001"}'

# Expected: [{"category": "ui", "key": "theme", "value": "dark", ...}]

# Record behavior
curl -X POST http://localhost:8001/api/v1/memory/long-term/behavior \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user001",
    "behavior_type": "interaction_style",
    "pattern": "prefers_concise_responses",
    "confidence": 0.6
  }'

# Get behaviors
curl -X POST http://localhost:8001/api/v1/memory/long-term/behaviors \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user001", "min_confidence": 0.5}'
```

- [ ] Preference stores and retrieves
- [ ] Behavior records with confidence
- [ ] Confidence increases on repeat patterns

## ✅ Episodic Memory Tests

Test event storage and summaries:

```bash
# Store event
curl -X POST http://localhost:8001/api/v1/memory/episodic/event \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user001",
    "event_type": "command",
    "summary": "User asked about weather",
    "details": {"location": "San Francisco"}
  }'

# Get recent events
curl http://localhost:8001/api/v1/memory/episodic/recent/user001?days=7

# Generate summary
curl -X POST http://localhost:8001/api/v1/memory/episodic/summary \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user001"}'

# Get summaries
curl http://localhost:8001/api/v1/memory/episodic/summaries/user001
```

- [ ] Event stores successfully
- [ ] Recent events retrieve correctly
- [ ] Summary generates (may require multiple events)

## ✅ Semantic Memory Tests

Test vector similarity search:

```bash
# Add semantic memory
curl -X POST http://localhost:8001/api/v1/memory/semantic/add \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user001",
    "text": "User prefers dark mode for the interface",
    "memory_type": "preference"
  }'

# Add another
curl -X POST http://localhost:8001/api/v1/memory/semantic/add \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user001",
    "text": "User likes concise technical responses",
    "memory_type": "preference"
  }'

# Search
curl -X POST http://localhost:8001/api/v1/memory/semantic/search \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user001",
    "query": "UI theme preferences",
    "top_k": 5
  }'

# Expected: Results with similarity scores, "dark mode" should rank high
```

- [ ] Memories add successfully
- [ ] Search returns relevant results
- [ ] Similarity scores are reasonable (>0.5 for relevant)

## ✅ Admin Functions Tests

Test user data export and deletion:

```bash
# Export user data
curl -X POST http://localhost:8001/api/v1/admin/export \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user001"}'

# Expected: Complete data dump with preferences, behaviors, events, etc.

# Get user summary
curl http://localhost:8001/api/v1/admin/summary/user001

# Expected: Statistics about user's data

# Delete user data (CAUTION!)
curl -X POST http://localhost:8001/api/v1/admin/delete \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user001", "confirm": true}'

# Expected: Deletion confirmation with counts
```

- [ ] Export returns complete data
- [ ] Summary shows statistics
- [ ] Delete removes all data (verify with export)

## ✅ Performance Tests

Quick performance checks:

```bash
# Measure latency (Unix/Mac)
time curl http://localhost:8001/health

# Measure latency (Windows PowerShell)
Measure-Command { Invoke-WebRequest http://localhost:8001/health }
```

Expected latencies:

- [ ] Health check: <50ms
- [ ] Short-term store: <50ms
- [ ] Long-term store: <100ms
- [ ] Semantic search: <300ms

## ✅ Persistence Tests

Verify data persists across restarts:

```bash
# 1. Store some data (see tests above)

# 2. Stop service (Ctrl+C)

# 3. Restart service
python src/main.py

# 4. Retrieve data (should still exist)
curl -X POST http://localhost:8001/api/v1/memory/long-term/preferences \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user001"}'
```

- [ ] PostgreSQL data persists (preferences, behaviors, events)
- [ ] FAISS index loads from disk
- [ ] Redis data may expire (expected - TTL-based)

## ✅ Error Handling Tests

Test error responses:

```bash
# Invalid session ID
curl -X POST http://localhost:8001/api/v1/memory/short-term/retrieve \
  -H "Content-Type: application/json" \
  -d '{"session_id": "nonexistent"}'

# Expected: Empty context, not error

# Invalid request
curl -X POST http://localhost:8001/api/v1/memory/long-term/preference \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'

# Expected: 422 Validation Error with details
```

- [ ] Invalid requests return appropriate HTTP codes
- [ ] Error messages are descriptive
- [ ] Service doesn't crash on bad input

## ✅ Docker Tests (Optional)

If using Docker:

```bash
# Build image
docker build -t memory-service:test .

# Run container
docker run -d -p 8001:8001 -p 50051:50051 \
  -e DB_HOST=host.docker.internal \
  -e REDIS_HOST=host.docker.internal \
  --name memory-service-test \
  memory-service:test

# Check health
curl http://localhost:8001/health

# Stop container
docker stop memory-service-test
docker rm memory-service-test
```

- [ ] Image builds successfully
- [ ] Container starts without errors
- [ ] Health check passes
- [ ] Can connect to host databases

## 📊 Final Verification Summary

All checks completed: **\_** / 11 sections

- [ ] Prerequisites (5 checks)
- [ ] Installation (5 checks)
- [ ] Unit Tests (4 checks)
- [ ] Service Startup (6 checks)
- [ ] Health Check (2 checks)
- [ ] API Documentation (3 checks)
- [ ] Short-term Memory (3 checks)
- [ ] Long-term Memory (3 checks)
- [ ] Episodic Memory (3 checks)
- [ ] Semantic Memory (3 checks)
- [ ] Admin Functions (3 checks)

---

## 🚨 Troubleshooting

### Service won't start

- Check PostgreSQL is running: `docker ps | grep postgres`
- Check Redis is running: `docker ps | grep redis`
- Verify .env has correct credentials
- Check port 8001 and 50051 are not in use

### Tests failing

- Ensure all dependencies installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (needs 3.11+)
- Run tests with verbose output: `pytest tests/ -v -s`

### Database connection errors

- Verify database exists: `psql -U agent -d voice_agent -c "SELECT 1"`
- Check schema initialized: `psql -U agent -d voice_agent -c "\dt"`
- Test connection: `psql -U agent -d voice_agent -h localhost`

### Redis connection errors

- Test Redis: `redis-cli ping`
- Check Redis is accepting connections: `redis-cli -h localhost -p 6379 ping`
- Verify no password required (or set REDIS_PASSWORD in .env)

### FAISS errors

- Ensure numpy installed: `pip install numpy`
- Check FAISS installation: `python -c "import faiss; print(faiss.__version__)"`
- Verify data directory writable: `ls -la data/faiss_index`

---

**After completing all checks, Phase 2 is verified! ✅**
