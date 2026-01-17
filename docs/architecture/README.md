# Voice AI Agent Architecture

## System Overview

The Voice AI Agent is a distributed, microservices-based system designed as a privacy-first AI operating layer. The architecture follows a layered approach with clear separation of concerns and secure boundaries between components.

## Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │Desktop Client│  │ Mobile Client│  │  Web Client  │            │
│  │  (Electron)  │  │   (Native)   │  │  (Browser)   │            │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘            │
└─────────┼──────────────────┼──────────────────┼────────────────────┘
          │ WebSocket/HTTP   │                  │
          └──────────────────┼──────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────────┐
│                      API GATEWAY LAYER                              │
│                    ┌───────┴────────┐                               │
│                    │  API Gateway   │ FastAPI (HTTP/WS)            │
│                    │  Port: 8000    │ Authentication, Routing      │
│                    └───────┬────────┘                               │
└────────────────────────────┼────────────────────────────────────────┘
                             │ gRPC
┌────────────────────────────┼────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                              │
│                    ┌───────┴────────┐                               │
│                    │  Agent Core    │ Python                        │
│                    │  Port: 50052   │ Reasoning Engine              │
│                    │  LLaMA 3 LLM   │ Intent Classification         │
│                    └────────────────┘ Tool Router                   │
│                      │      │      │                                │
│         ┌────────────┘      │      └────────────┐                  │
└─────────┼─────────────────────────────────────────┼─────────────────┘
          │ gRPC                                     │ gRPC
┌─────────┼─────────────────────────────────────────┼─────────────────┐
│    EXECUTION LAYER                                │                 │
│  ┌─────┴──────┐  ┌──────────────┐  ┌─────────────┴──────┐         │
│  │   Memory   │  │     Tool     │  │   Web Service      │         │
│  │  Service   │  │  Executor    │  │   Port: 50056      │         │
│  │ Port:50051 │  │ Port: 50055  │  │   Playwright       │         │
│  │ PostgreSQL │  │   Rust       │  │   Web Search       │         │
│  │  + Redis   │  │  Sandboxed   │  │   Browser Auto     │         │
│  │  + FAISS   │  └──────────────┘  └────────────────────┘         │
│  └────────────┘                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       VOICE SERVICES LAYER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │Voice Gateway │  │ STT Service  │  │ TTS Service  │            │
│  │   Rust       │  │   Whisper    │  │  Coqui TTS   │            │
│  │ Port: 9000   │  │ Port: 50053  │  │ Port: 50054  │            │
│  │Audio Stream  │  │   Python     │  │   Python     │            │
│  │Wake-word Det │  └──────────────┘  └──────────────┘            │
│  └──────────────┘                                                  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ PostgreSQL   │  │    Redis     │  │    FAISS     │            │
│  │  Port: 5432  │  │  Port: 6379  │  │  In-Memory   │            │
│  │  Long-term   │  │  Short-term  │  │   Vectors    │            │
│  │   Memory     │  │    Cache     │  │   Semantic   │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
```

## Service Communication

All inter-service communication uses gRPC with Protocol Buffers for:

- Type safety
- High performance
- Bidirectional streaming (audio, task updates)
- Code generation for multiple languages

## Data Flow: Voice Interaction

```
1. User speaks "Hey Jarvis, search for Python tutorials"
2. Voice Gateway detects wake-word → activates transcription
3. Audio stream → STT Service (Whisper) → "search for Python tutorials"
4. Agent Core receives text:
   a. Retrieve context from Memory Service (preferences, history)
   b. Classify intent: web_search
   c. Generate tool call: {"tool": "web_search", "query": "Python tutorials"}
   d. Check permissions & rate limits
5. Tool Executor validates and executes web search via Web Service
6. Results returned to Agent Core
7. Agent Core synthesizes response: "Here are the top Python tutorials..."
8. TTS Service generates audio
9. Voice Gateway streams audio back to client
```

## Security Boundaries

1. **API Gateway**: Authentication, rate limiting, input validation
2. **Agent Core**: Permission checks before tool execution
3. **Tool Executor**: Sandboxed execution, seccomp filtering
4. **Data Layer**: Encrypted at rest, TLS in transit

## Scalability Considerations

- **Horizontal Scaling**: All services are stateless (except Memory Service)
- **Database**: PostgreSQL read replicas for query scaling
- **Cache**: Redis for distributed session management
- **Load Balancing**: Kubernetes Ingress for API Gateway

## Further Documentation

- [Memory Architecture](memory.md) - Detailed memory system design
- [Security Model](../security/security_model.md) - Comprehensive security analysis
- [Service Contracts](../api/grpc_services.md) - gRPC API documentation

---

**Last Updated**: Phase 1 - January 2026
