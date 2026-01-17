# Agent Core Service

**Language**: Python 3.11+
**Framework**: gRPC (asyncio)
**Purpose**: AI reasoning engine and orchestration hub

## Responsibilities

- **Intent Classification**: Hybrid rule-based + LLM classification
- **Conversation Management**: Multi-turn context tracking
- **Reasoning Pipeline**: Plan → Propose → Verify → Respond
- **Tool Router**: Validate tools, enforce permissions, request confirmations
- **Response Synthesis**: Generate natural language responses

## gRPC Service

Implements `AgentCore` from `shared/proto/agent.proto`:

- `ProcessIntent` - Main entry point for user input
- `ExecuteTask` - Execute approved actions with streaming updates
- `ContinueConversation` - Multi-turn conversation handling
- `ProcessFeedback` - Handle user corrections and ratings
- `ConfirmAction` - User confirmation for sensitive actions

## Architecture

```
User Input → Intent Detection → Context Retrieval (Memory Service)
                ↓
      Reasoning Engine (LLM: LLaMA 3 / OpenRouter)
                ↓
      Tool Selection & Validation → Confirmation Check
                ↓
      Tool Execution (via Tool Executor) → Response Synthesis
```

## LLM Integration

**Primary**: Self-hosted LLaMA 3 8B via vLLM
**Fallback**: OpenRouter API (meta-llama/llama-3.1-8b-instruct)

**Prompt Structure**:

```
System: You are a helpful AI assistant with access to tools...
Context: {user_preferences, recent_conversation, learned_behaviors}
User: {user_input}
Available Tools: {tool_list_with_descriptions}
Response Format: {structured_json_with_tool_calls}
```

## Intent Classification

**Hybrid Approach**:

1. **Rule-based** (regex patterns) for common commands:

   - "search for X" → `web_search`
   - "play X on YouTube" → `youtube_play`
   - "remind me to X" → `set_reminder`

2. **LLM-based** for complex/ambiguous intents:
   - Zero-shot classification with few-shot examples
   - Confidence threshold: 0.8 (request clarification if lower)

## Tool Router Logic

1. Parse LLM response for tool calls
2. Validate against user permissions (`user_permissions` table)
3. Check rate limits (Redis-backed)
4. Determine if confirmation required:
   - File deletion, system commands, purchases → **Always confirm**
   - Web search, read operations → **No confirmation**
5. Return `AgentResponse` with `proposed_actions` and `requires_confirmation`

## Dependencies

- `openai` - OpenAI-compatible API client (vLLM uses same interface)
- `anthropic` - Optional Anthropic Claude fallback
- `redis` - Session state and rate limiting
- `tiktoken` - Token counting for context window management

## Running Locally

```bash
cd services/agent-core
pip install -r requirements.txt

# Start vLLM server (or use OpenRouter)
# vllm serve meta-llama/Meta-Llama-3-8B-Instruct --port 8001

python -m app.main
```

## Environment Variables

```
REDIS_HOST=localhost
OPENROUTER_API_KEY=your-key  # or leave empty for vLLM
VLLM_ENDPOINT=http://localhost:8001/v1
VLLM_MODEL=meta-llama/Meta-Llama-3-8B-Instruct
LLM_TIMEOUT=30
ENABLE_LEARNING=true
```

## Status

**Phase**: Not yet implemented (Phase 3)
**Next Steps**:

1. Implement intent classification engine
2. Build conversation manager with context window
3. Create tool router with permission checks
4. Integrate LLM (vLLM + OpenRouter fallback)
5. Implement response synthesis
6. Add comprehensive logging and tracing
