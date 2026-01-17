# Agent Core - Quick Reference

## 🚀 Start the Service

```bash
# Linux/Mac
./start.sh

# Windows
start.bat

# Docker
docker-compose up -d
```

## 🔗 Service URLs

- REST API: `http://localhost:8002`
- gRPC: `localhost:50052`
- Health: `http://localhost:8002/health`
- API Docs: `http://localhost:8002/docs`

## 📡 Main Endpoints

### Process Request

```bash
curl -X POST http://localhost:8002/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my_session",
    "user_id": "my_user",
    "user_input": "search for Python tutorials"
  }'
```

### Classify Intent

```bash
curl -X POST http://localhost:8002/api/v1/intent/classify \
  -H "Content-Type: application/json" \
  -d '{"user_input": "search for AI news"}'
```

### Confirm Action

```bash
curl -X POST http://localhost:8002/api/v1/action/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my_session",
    "user_id": "my_user",
    "confirmed": true
  }'
```

## 🛠️ Available Tools

| Tool             | Action         | Confirmation        |
| ---------------- | -------------- | ------------------- |
| web_search       | Search the web | none                |
| web_fetch        | Fetch webpage  | none                |
| browser_navigate | Open URL       | none                |
| browser_click    | Click element  | soft                |
| browser_type     | Type text      | soft                |
| file_read        | Read file      | none                |
| file_list        | List files     | none                |
| file_write       | Write file     | **hard**            |
| system_command   | Run command    | **hard** (disabled) |

## 🔒 Confirmation Levels

- **none**: Execute immediately (safe operations)
- **soft**: Request confirmation (reversible operations)
- **hard**: Require explicit confirmation (destructive operations)

## 📊 Intent Types

1. **SEARCH** - Web searches, lookups
2. **BROWSE** - Navigate websites, browser control
3. **EXECUTE** - File operations, system commands
4. **REMEMBER** - Store information, take notes
5. **CONVERSATION** - Greetings, small talk
6. **CLARIFICATION** - Ambiguous requests

## 🔧 Configuration

Edit `.env` file:

```env
# Required
OPENROUTER_API_KEY=your_key_here

# Optional (defaults shown)
LLM_MODEL=meta-llama/llama-3.1-8b-instruct
LLM_TEMPERATURE=0.3
REDIS_HOST=localhost
REDIS_PORT=6379
GRPC_PORT=50052
REST_PORT=8002
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_intent_classifier.py -v

# With coverage
pytest tests/ --cov=src
```

## 🐳 Docker Commands

```bash
# Build
docker-compose build

# Start
docker-compose up -d

# Logs
docker-compose logs -f agent-core

# Stop
docker-compose down

# Restart
docker-compose restart agent-core
```

## 🔍 Health Checks

```bash
# Basic
curl http://localhost:8002/health

# Detailed
curl http://localhost:8002/health/detailed

# List tools
curl http://localhost:8002/api/v1/tools

# Get config
curl http://localhost:8002/api/v1/config
```

## 📝 Common Patterns

### 1. Simple Search

```json
{
  "session_id": "session1",
  "user_id": "user1",
  "user_input": "search for Python tutorials"
}
```

### 2. File Operation (requires confirmation)

```json
{
  "session_id": "session2",
  "user_id": "user1",
  "user_input": "create a file called notes.txt"
}
```

### 3. Multi-Turn Conversation

```json
// Turn 1
{"session_id": "session3", "user_id": "user1", "user_input": "search for AI news"}

// Turn 2 (same session)
{"session_id": "session3", "user_id": "user1", "user_input": "show me more"}
```

## 🐛 Troubleshooting

| Issue                     | Solution                                |
| ------------------------- | --------------------------------------- |
| "Redis connection failed" | Start Redis: `redis-server`             |
| "LLM API error"           | Check `OPENROUTER_API_KEY` in `.env`    |
| "Rate limit exceeded"     | Wait or increase limits in `tools.yaml` |
| "Tool disabled"           | Enable in `config/tools.yaml`           |
| "Invalid parameters"      | Check parameter schema in `tools.yaml`  |

## 📚 Documentation

- **README.md** - Full documentation
- **API_EXAMPLES.md** - API usage examples
- **IMPLEMENTATION_SUMMARY.md** - Technical details
- **QUICK_REFERENCE.md** - This file

## 🔗 Dependencies

| Service        | Port       | Status          |
| -------------- | ---------- | --------------- |
| Agent Core     | 8002/50052 | ✅ This service |
| Memory Service | 50051      | Optional        |
| Tool Executor  | 50055      | Optional        |
| Web Service    | 50056      | Optional        |
| Redis          | 6379       | Required        |

## 💡 Tips

1. Use consistent `session_id` for multi-turn conversations
2. Check `needs_confirmation` in response
3. Monitor rate limits with `/api/v1/tools`
4. Use `/health/detailed` to check service status
5. Review logs for debugging: `docker-compose logs -f`

## 📞 Getting Help

1. Check logs: `docker-compose logs agent-core`
2. Test health: `curl http://localhost:8002/health`
3. Review documentation in README.md
4. Check configuration in `.env`
5. Run tests: `pytest tests/ -v`

---

**Version**: 1.0.0
**Status**: ✅ Production Ready
