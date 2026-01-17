# Agent Core - Voice AI Agent Reasoning Engine

**Language**: Python 3.11+
**Frameworks**: FastAPI + gRPC
**Purpose**: Central reasoning and orchestration service

## 🎯 Overview

Agent Core is the brain of the Voice AI Agent system, providing:

- **Hybrid Intent Classification**: Fast rule-based matching with LLM fallback
- **LLM-Based Planning**: Generates tool execution sequences using meta-llama/llama-3.1-8b-instruct
- **Security-First Design**: Confirmation levels, rate limiting, allowlists/blocklists
- **Multi-Turn Conversations**: Session management with context tracking
- **Tool Orchestration**: Routes actions to appropriate services (web-service, tool-executor)

## 🏗️ Architecture

```
User Request
    ↓
[Intent Classifier] ──→ Rule-based patterns (fast, 85-90% confidence)
    ↓                    ↓ (if ambiguous < 70%)
    └──────────────→ LLM fallback
    ↓
[Planner] ──────────→ LLM generates 1-5 action plan
    ↓
[Tool Router] ──────→ Validates security & parameters
    ↓
[Confirmation?] ────→ Soft/Hard actions require approval
    ↓
[Execution] ────────→ Routes to web-service or tool-executor
    ↓
[Response Synthesizer] → Natural language response
    ↓
User Response
```

## 📋 Core Features

### Intent Classification (6 Types)

- **SEARCH**: Web searches, information lookup
- **BROWSE**: Website navigation, browser control
- **EXECUTE**: File operations, system commands
- **REMEMBER**: Memory storage, note-taking
- **CONVERSATION**: Greetings, small talk
- **CLARIFICATION**: Ambiguous requests

### Planning & Execution

- **LLM-Powered**: Uses OpenRouter API with LLaMA 3.1-8b-instruct
- **Safety Limits**: Maximum 5 actions per plan
- **Reasoning**: Each action includes human-readable explanation
- **Confidence Scoring**: Based on intent + plan complexity

### Security (Three-Tier Confirmation)

1. **none**: Safe read-only operations (web_search, file_read)
2. **soft**: Reversible actions (browser_click, browser_type)
3. **hard**: Destructive operations (file_write, system_command)

### Rate Limiting

- **Per-user, per-tool** using Redis token bucket
- web_search: 20/min, web_fetch: 15/min, file_write: 5/min, system_command: 3/min

### Tool Support (9 Tools)

- **Web**: web_search, web_fetch, browser_navigate, browser_click, browser_type
- **Files**: file_read, file_list, file_write
- **System**: system_command (disabled by default)

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
