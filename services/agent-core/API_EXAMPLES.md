# Agent Core API Examples

This document provides practical examples for using the Agent Core API.

## Prerequisites

Ensure the service is running:

```bash
# Start locally
python src/main.py

# Or with Docker
docker-compose up -d
```

## Example 1: Simple Web Search

### Request

```bash
curl -X POST http://localhost:8002/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo_session_001",
    "user_id": "demo_user",
    "user_input": "search for Python asyncio tutorials"
  }'
```

### Response

```json
{
  "success": true,
  "response": "I found 5 Python asyncio tutorials for you. The top results include...",
  "plan": {
    "actions": [
      {
        "tool_name": "web_search",
        "parameters": {
          "query": "Python asyncio tutorials",
          "max_results": 5
        },
        "reasoning": "User wants to learn about asyncio in Python",
        "confirmation_level": "none"
      }
    ],
    "thought_process": "User is seeking educational resources about asyncio",
    "expected_outcome": "List of relevant tutorials",
    "confidence": 0.94,
    "needs_confirmation": false
  },
  "action_results": [
    {
      "tool_name": "web_search",
      "success": true,
      "result": {...},
      "error": null
    }
  ],
  "needs_confirmation": false
}
```

## Example 2: File Operation Requiring Confirmation

### Request

```bash
curl -X POST http://localhost:8002/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo_session_002",
    "user_id": "demo_user",
    "user_input": "create a file called notes.txt with my meeting notes"
  }'
```

### Response (Confirmation Required)

```json
{
  "success": true,
  "response": "I need your confirmation to create the file notes.txt with your meeting notes. This action will write to your filesystem. Do you want me to proceed? (yes/no)",
  "plan": {
    "actions": [
      {
        "tool_name": "file_write",
        "parameters": {
          "path": "./workspace/notes.txt",
          "content": "Meeting notes...",
          "overwrite": false
        },
        "reasoning": "User wants to save meeting notes to a file",
        "confirmation_level": "hard"
      }
    ],
    "confidence": 0.88,
    "needs_confirmation": true
  },
  "needs_confirmation": true
}
```

### Confirm the Action

```bash
curl -X POST http://localhost:8002/api/v1/action/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo_session_002",
    "user_id": "demo_user",
    "confirmed": true
  }'
```

### Confirmation Response

```json
{
  "success": true,
  "response": "I've successfully created notes.txt with your meeting notes.",
  "action_results": [
    {
      "tool_name": "file_write",
      "success": true,
      "result": "File created successfully",
      "error": null
    }
  ]
}
```

## Example 3: Multi-Turn Conversation

### Turn 1: Initial Request

```bash
curl -X POST http://localhost:8002/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo_session_003",
    "user_id": "demo_user",
    "user_input": "I want to learn about machine learning"
  }'
```

### Turn 2: Follow-up

```bash
curl -X POST http://localhost:8002/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo_session_003",
    "user_id": "demo_user",
    "user_input": "show me more beginner-friendly resources"
  }'
```

The system maintains context across turns using the `session_id`.

## Example 4: Intent Classification Only

### Request

```bash
curl -X POST http://localhost:8002/api/v1/intent/classify \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "find me information about quantum computing",
    "context": {
      "conversation_summary": "User is researching advanced physics topics"
    }
  }'
```

### Response

```json
{
  "intent_type": "SEARCH",
  "confidence": 0.91,
  "entities": {
    "query": "quantum computing"
  },
  "reasoning": "User explicitly requested to find information",
  "required_llm_fallback": false
}
```

## Example 5: Plan Creation

### Request

```bash
curl -X POST http://localhost:8002/api/v1/plan/create \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "download the Python documentation",
    "intent_type": "EXECUTE",
    "context": {
      "user_preferences": {"language": "en"}
    }
  }'
```

### Response

```json
{
  "success": true,
  "plan": {
    "actions": [
      {
        "tool_name": "web_fetch",
        "parameters": {
          "url": "https://docs.python.org",
          "extract_type": "markdown"
        },
        "reasoning": "Fetch Python documentation",
        "confirmation_level": "none"
      }
    ],
    "thought_process": "User wants to access Python documentation",
    "expected_outcome": "Python documentation content",
    "confidence": 0.89,
    "needs_confirmation": false
  },
  "error": null
}
```

## Example 6: Conversation History

### Get Conversation

```bash
curl http://localhost:8002/api/v1/conversation/demo_session_003
```

### Response

```json
{
  "session_id": "demo_session_003",
  "user_id": "demo_user",
  "messages": [
    {
      "role": "user",
      "content": "I want to learn about machine learning",
      "timestamp": "2026-01-17T10:30:00",
      "metadata": {}
    },
    {
      "role": "assistant",
      "content": "I can help you with that...",
      "timestamp": "2026-01-17T10:30:02",
      "metadata": {"plan": {...}}
    }
  ],
  "user_preferences": {},
  "current_task": "Learning machine learning"
}
```

### End Conversation

```bash
curl -X DELETE http://localhost:8002/api/v1/conversation/demo_session_003
```

## Example 7: List Available Tools

### Request

```bash
curl http://localhost:8002/api/v1/tools
```

### Response

```json
{
  "tools": [
    {
      "name": "web_search",
      "description": "Search the web for information",
      "confirmation_level": "none",
      "rate_limit": "20/minute",
      "enabled": true
    },
    {
      "name": "file_write",
      "description": "Write content to a file",
      "confirmation_level": "hard",
      "rate_limit": "5/minute",
      "enabled": true
    }
  ]
}
```

## Example 8: Configuration Check

### Request

```bash
curl http://localhost:8002/api/v1/config
```

### Response

```json
{
  "llm": {
    "provider": "OpenRouter",
    "model": "meta-llama/llama-3.1-8b-instruct",
    "temperature": 0.3,
    "max_tokens": 2000
  },
  "ports": {
    "grpc": 50052,
    "rest": 8002
  },
  "services": {
    "memory": "localhost:50051",
    "tool_executor": "localhost:50055",
    "web": "localhost:50056"
  },
  "features": {
    "rate_limiting": true,
    "confirmation_required": true,
    "multi_turn_conversations": true
  }
}
```

## Example 9: Health Checks

### Basic Health

```bash
curl http://localhost:8002/health
```

### Detailed Health

```bash
curl http://localhost:8002/health/detailed
```

### Response

```json
{
  "status": "healthy",
  "service": "agent-core",
  "components": {
    "intent_classifier": "healthy",
    "planner": "healthy",
    "tool_router": "healthy",
    "conversation_manager": "healthy",
    "response_synthesizer": "healthy",
    "grpc_clients": "connected"
  },
  "config": {
    "llm_model": "meta-llama/llama-3.1-8b-instruct",
    "grpc_port": 50052,
    "rest_port": 8002
  }
}
```

## Example 10: Error Handling

### Invalid Tool Parameters

```bash
curl -X POST http://localhost:8002/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo_session_004",
    "user_id": "demo_user",
    "user_input": "search with 1000 results"
  }'
```

### Error Response

```json
{
  "success": false,
  "response": "I apologize, but some actions failed validation: web_search: Parameter 'max_results' must be <= 10",
  "error": "Some actions failed validation...",
  "needs_confirmation": false
}
```

## Python SDK Example

```python
import requests

class AgentCoreClient:
    def __init__(self, base_url="http://localhost:8002"):
        self.base_url = base_url
        self.session_id = None

    def process(self, user_input, user_id="default_user"):
        if not self.session_id:
            import uuid
            self.session_id = str(uuid.uuid4())

        response = requests.post(
            f"{self.base_url}/api/v1/process",
            json={
                "session_id": self.session_id,
                "user_id": user_id,
                "user_input": user_input
            }
        )
        return response.json()

    def confirm(self, user_id="default_user"):
        response = requests.post(
            f"{self.base_url}/api/v1/action/confirm",
            json={
                "session_id": self.session_id,
                "user_id": user_id,
                "confirmed": True
            }
        )
        return response.json()

# Usage
client = AgentCoreClient()

# Search
result = client.process("search for Python tutorials")
print(result["response"])

# File operation requiring confirmation
result = client.process("create a file called test.txt")
if result["needs_confirmation"]:
    print(result["response"])
    confirmed = client.confirm()
    print(confirmed["response"])
```

## JavaScript/Node.js Example

```javascript
const axios = require("axios");

class AgentCoreClient {
  constructor(baseUrl = "http://localhost:8002") {
    this.baseUrl = baseUrl;
    this.sessionId = null;
  }

  async process(userInput, userId = "default_user") {
    if (!this.sessionId) {
      this.sessionId = require("crypto").randomUUID();
    }

    const response = await axios.post(`${this.baseUrl}/api/v1/process`, {
      session_id: this.sessionId,
      user_id: userId,
      user_input: userInput,
    });

    return response.data;
  }

  async confirm(userId = "default_user") {
    const response = await axios.post(`${this.baseUrl}/api/v1/action/confirm`, {
      session_id: this.sessionId,
      user_id: userId,
      confirmed: true,
    });

    return response.data;
  }
}

// Usage
(async () => {
  const client = new AgentCoreClient();

  // Search
  const result = await client.process("search for Python tutorials");
  console.log(result.response);

  // File operation requiring confirmation
  const fileResult = await client.process("create a file called test.txt");
  if (fileResult.needs_confirmation) {
    console.log(fileResult.response);
    const confirmed = await client.confirm();
    console.log(confirmed.response);
  }
})();
```

## Testing Tips

1. **Use consistent session_id** for multi-turn conversations
2. **Handle confirmation prompts** - check `needs_confirmation` field
3. **Monitor rate limits** - respect per-tool limits
4. **Check health endpoints** before making requests
5. **Use detailed error messages** for debugging

## Common Patterns

### Pattern 1: Search → Refine → Execute

```
1. User: "search for Python tutorials"
2. Agent: Returns search results
3. User: "open the first one"
4. Agent: Uses browser_navigate
```

### Pattern 2: Plan → Confirm → Execute

```
1. User: "delete my old files"
2. Agent: Requests confirmation (destructive action)
3. User: "yes"
4. Agent: Executes file_write/system_command
```

### Pattern 3: Ambiguous → Clarify → Execute

```
1. User: "do it"
2. Agent: Requests clarification
3. User: "search for AI news"
4. Agent: Executes web_search
```

---

For more examples, see the unit tests in `tests/` directory.
