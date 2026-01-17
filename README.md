# Voice AI Agent - Production System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Rust 1.75+](https://img.shields.io/badge/rust-1.75+-orange.svg)](https://www.rust-lang.org/)

**A distributed, privacy-first Voice AI Agent platform** — production-grade AI operating layer providing voice interaction, reasoning, and secure tool orchestration for real-world deployment at scale.

---

## 🎯 What This Is

This is **NOT** a chatbot. This is a distributed AI operating system that:

- 🎙️ **Voice-first interaction** with streaming STT/TTS and natural multi-turn conversations
- 🧠 **Reasoning engine** with tool orchestration (AI proposes, system executes)
- 🔐 **Privacy-first memory** with user consent and full transparency controls
- 🛡️ **Security-hardened** with sandboxed execution, rate limiting, and audit logging
- 🌐 **Tool ecosystem** for web search, browser automation, and OS-level actions

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Voice AI Agent System                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Voice Client │◄──►│ Voice Gateway│◄──►│  STT Service │  │
│  │  (Desktop)   │    │    (Rust)    │    │   (Whisper)  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                              │                               │
│                              ▼                               │
│                      ┌──────────────┐                       │
│                      │  Agent Core  │                       │
│                      │   (Python)   │                       │
│                      │  Reasoning   │                       │
│                      └──────────────┘                       │
│                              │                               │
│          ┌───────────────────┼───────────────────┐          │
│          ▼                   ▼                   ▼          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │Memory Service│    │Tool Executor │    │ Web Service  │  │
│  │  (Python)    │    │   (Rust)     │    │  (Playwright)│  │
│  │ PostgreSQL   │    │  Sandboxed   │    │   Python     │  │
│  │  + Redis     │    └──────────────┘    └──────────────┘  │
│  │  + FAISS     │                                          │
│  └──────────────┘                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Core Services

| Service            | Language | Purpose                     | Port  |
| ------------------ | -------- | --------------------------- | ----- |
| **api-gateway**    | Python   | HTTP/WebSocket entry point  | 8000  |
| **voice-gateway**  | Rust     | Audio streaming & wake-word | 9000  |
| **stt-service**    | Python   | Speech-to-Text (Whisper)    | 50053 |
| **tts-service**    | Python   | Text-to-Speech (Coqui TTS)  | 50054 |
| **agent-core**     | Python   | Reasoning & orchestration   | 50052 |
| **memory-service** | Python   | Memory management           | 50051 |
| **tool-executor**  | Rust     | Sandboxed tool execution    | 50055 |
| **web-service**    | Python   | Browser automation          | 50056 |

---

## 🚀 Quick Start

### Prerequisites

- **Docker** 20.10+ & **Docker Compose** 2.0+
- **Python** 3.11+
- **Rust** 1.75+ (with cargo)
- **PostgreSQL** 15+ (via Docker)
- **Redis** 7+ (via Docker)
- **Git**

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/voice-ai-agent.git
cd voice-ai-agent

# Copy environment configuration
cp .env.example .env
# Edit .env with your API keys and settings

# Initialize infrastructure (PostgreSQL, Redis)
make setup

# Start development environment
make dev
```

### Makefile Commands

```bash
make setup      # Initialize project and start infrastructure
make proto      # Generate gRPC code from .proto files
make build      # Build all services
make dev        # Start development environment
make test       # Run all tests
make clean      # Clean build artifacts and containers
```

---

## 📦 Project Structure

```
voice-ai-agent/
├── services/           # Microservices
│   ├── api-gateway/       # FastAPI HTTP/WebSocket server
│   ├── voice-gateway/     # Rust audio streaming
│   ├── stt-service/       # Whisper STT integration
│   ├── tts-service/       # Coqui TTS integration
│   ├── agent-core/        # Reasoning engine (LLaMA 3)
│   ├── memory-service/    # Memory management
│   ├── tool-executor/     # Rust sandboxed execution
│   └── web-service/       # Playwright browser automation
├── shared/
│   ├── proto/             # gRPC protocol definitions
│   ├── models/            # Shared data models
│   └── utils/             # Common utilities
├── infra/
│   ├── docker/            # Dockerfiles for services
│   ├── docker-compose.yml # Local development stack
│   ├── init-db.sql        # PostgreSQL schema
│   └── scripts/           # Setup & maintenance scripts
├── docs/
│   ├── architecture/      # System design documentation
│   ├── api/               # API specifications
│   └── security/          # Security policies
├── tests/
│   ├── integration/       # Integration tests
│   └── e2e/               # End-to-end tests
├── .env.example           # Environment configuration template
├── .gitignore
├── Makefile               # Development workflow automation
└── README.md
```

---

## 🧠 Memory Architecture

### 4-Tier Memory System

1. **Short-term Memory** (Redis)

   - Live session context (24-hour TTL)
   - Conversation state and recent history
   - Real-time context for reasoning

2. **Long-term Memory** (PostgreSQL)

   - User preferences and settings
   - Learned behaviors and patterns
   - Command shortcuts and tool preferences

3. **Episodic Memory** (PostgreSQL + Time-series)

   - Historical event summaries
   - Weekly rollups of activities
   - 90-day retention policy (configurable)

4. **Semantic Memory** (FAISS Vector DB)
   - Vector embeddings of conversations/documents
   - Semantic search and retrieval
   - `all-MiniLM-L6-v2` embeddings (384 dims)

### User Transparency Controls

```python
# Users can access their memory at any time
GET /api/memory/export       # Export all user data
GET /api/memory/summary      # View memory summary
DELETE /api/memory           # Delete all user data
PUT /api/memory/preferences  # Update learning preferences
```

---

## 🔐 Security Architecture

### Defense-in-Depth Strategy

1. **Tool Execution Sandbox** (Rust `tool-executor`)

   - No raw shell access
   - Allow-list of approved tools
   - Syscall filtering with seccomp
   - Containerized isolation

2. **Permission Matrix**

   - Per-user, per-tool permissions (read/write/execute)
   - Explicit confirmation for sensitive actions
   - Escalating trust levels

3. **Rate Limiting** (Redis-backed)

   - 100 requests/hour default per tool
   - Configurable per tool type
   - User-specific quotas

4. **Audit Logging**

   - All tool invocations logged to PostgreSQL
   - User actions, timestamps, results
   - Immutable audit trail

5. **Data Encryption**
   - At-rest: PostgreSQL TDE
   - In-transit: TLS for all gRPC communication
   - Secrets: Environment variables + KMS integration

---

## 🛠️ Technology Stack

### Core Technologies

| Layer                  | Technology                    | Justification                                 |
| ---------------------- | ----------------------------- | --------------------------------------------- |
| **Voice Processing**   | Whisper (STT), Coqui TTS      | Self-hosted, offline-first, high-quality      |
| **AI/LLM**             | LLaMA 3 8B (vLLM), OpenRouter | Privacy-first self-hosting + cloud fallback   |
| **Wake-word**          | openWakeWord                  | Open-source, customizable, no licensing       |
| **API Framework**      | FastAPI (Python)              | Async, type-safe, auto-docs, gRPC support     |
| **Low-level Services** | Rust (Tokio)                  | Memory safety, sub-100ms latency, stability   |
| **Database**           | PostgreSQL 15                 | ACID compliance, JSONB, full-text search      |
| **Cache**              | Redis 7                       | Pub/sub, TTL, atomic operations               |
| **Vector DB**          | FAISS                         | High-performance, in-memory, no external deps |
| **Browser Automation** | Playwright (Python)           | Headless browsers, reliable, cross-platform   |
| **Orchestration**      | Docker + Docker Compose       | Local dev simplicity, prod-ready containers   |
| **IPC**                | gRPC (Protocol Buffers)       | Efficient, type-safe, streaming support       |

### Why Python + Rust?

**Python** is used for:

- AI reasoning and orchestration (LLM integration)
- Web APIs (FastAPI)
- Business logic (rapid iteration)
- Data pipelines (Whisper, TTS, Playwright)

**Rust** is used for:

- Voice gateway (sub-100ms audio streaming)
- Wake-word detection (always-running daemon)
- Tool executor (memory-safe command execution)
- Performance-critical paths (gRPC message broker)

**Boundary**: Python proposes, Rust executes. Clear interface contracts via gRPC.

---

## 📊 Human-Centric Learning

### What We Learn (With User Consent)

- ✅ Repeated command patterns ("always use DuckDuckGo for search")
- ✅ Explicit corrections ("No, I meant the other John")
- ✅ Tool success/failure rates
- ✅ Speech pace and command structure preferences

### What We DON'T Learn

- ❌ Emotional state inference
- ❌ Sensitive personal data extraction
- ❌ Silent background listening
- ❌ Model fine-tuning from user data

### Learning Loop

```
User Input → Intent Detection → Tool Execution → Feedback Collection
     ↑                                                    ↓
     └─────────── Behavior Adaptation ←──────────────────┘
              (No model retraining required)
```

Behavior changes update PostgreSQL `learned_behaviors` table and adjust tool selection weights in Agent Core reasoning loop.

---

## 🧪 Development Workflow

### Running Tests

```bash
# Unit tests
pytest tests/unit -v

# Integration tests (requires running services)
pytest tests/integration -v

# E2E tests
pytest tests/e2e -v

# Coverage report
pytest --cov=services --cov-report=html
```

### Building Individual Services

```bash
# Python services
cd services/memory-service
pip install -r requirements.txt
python -m app.main

# Rust services
cd services/voice-gateway
cargo build --release
cargo run
```

### Protocol Buffer Development

```bash
# Edit .proto files in shared/proto/
vim shared/proto/memory.proto

# Regenerate code
make proto

# Verify generation
ls shared/models/generated/
```

---

## 📚 Documentation

- [Architecture Overview](docs/architecture/README.md) _(Phase 2)_
- [API Reference](docs/api/README.md) _(Phase 2)_
- [Security Model](docs/security/README.md) _(Phase 2)_
- [Memory System Design](docs/architecture/memory.md) _(Phase 2)_
- [Tool Development Guide](docs/tools/README.md) _(Phase 3)_

---

## 🗺️ Roadmap

### ✅ Phase 1: Foundation (Current)

- [x] Monorepo structure
- [x] Docker infrastructure (PostgreSQL, Redis)
- [x] gRPC protocol definitions
- [x] Database schemas
- [x] Development tooling (Makefile)

### 🔄 Phase 2: Memory Service (Next)

- [ ] PostgreSQL ORM models (SQLAlchemy)
- [ ] Redis session management
- [ ] FAISS vector store integration
- [ ] Memory service gRPC server
- [ ] User transparency APIs

### 📋 Phase 3: Agent Core

- [ ] Intent classification (hybrid rules + LLM)
- [ ] Conversation manager
- [ ] LLaMA 3 integration (vLLM)
- [ ] Tool router with allow-lists
- [ ] Response synthesis

### 📋 Phase 4: Voice Services

- [ ] Whisper STT integration
- [ ] Coqui TTS integration
- [ ] Rust voice gateway (WebSocket streaming)
- [ ] Wake-word detection (openWakeWord)

### 📋 Phase 5: Tool Execution

- [ ] Rust tool executor service
- [ ] Sandboxing with seccomp
- [ ] Permission system
- [ ] Rate limiting
- [ ] Audit logging

### 📋 Phase 6: Web Services

- [ ] Playwright browser automation
- [ ] Web search integration (SerpAPI/Bing)
- [ ] Content extraction
- [ ] YouTube automation

### 📋 Phase 7: Integration & Testing

- [ ] End-to-end testing suite
- [ ] Performance benchmarking
- [ ] Security auditing
- [ ] Load testing
- [ ] Documentation completion

### 📋 Phase 8: Production Hardening

- [ ] Kubernetes deployment manifests
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Monitoring (Prometheus + Grafana)
- [ ] Distributed tracing (OpenTelemetry)
- [ ] Backup and disaster recovery

---

## 🤝 Contributing

This is currently a **design and implementation project**. Contributions will be welcome after Phase 3 completion. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines _(coming soon)_.

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🔗 Links

- **Documentation**: [docs/](docs/)
- **Issue Tracker**: GitHub Issues _(coming soon)_
- **Discussions**: GitHub Discussions _(coming soon)_

---

## ⚠️ Current Status

**Status**: Phase 1 - Foundation & Project Setup
**Progress**: 60% Infrastructure Complete
**Next Milestone**: Memory Service Implementation
**Last Updated**: January 17, 2026

This system is under active development and not yet ready for production deployment. Target is 60-70% production readiness by end of Phase 7.

---

**Built with 🧠 by humans, for humans. Privacy-first. Always.**
