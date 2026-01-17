# API Gateway Service

**Language**: Python 3.11+
**Framework**: FastAPI
**Purpose**: HTTP/WebSocket entry point for the Voice AI Agent system

## Responsibilities

- HTTP REST API for client applications
- WebSocket connections for real-time voice streaming
- Authentication and session management
- Request routing to backend services (gRPC)
- Rate limiting and security middleware

## API Endpoints (Phase 2+)

- `POST /api/v1/auth/login` - User authentication
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/session` - Get current session info
- `WS /ws/voice` - WebSocket for voice streaming
- `GET /api/v1/memory/export` - Export user data
- `DELETE /api/v1/memory` - Delete user data

## Dependencies

See `requirements.txt`

## Running Locally

```bash
cd services/api-gateway
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Environment Variables

```
DB_HOST=localhost
DB_PORT=5432
REDIS_HOST=localhost
JWT_SECRET=your-secret-key
```

## Status

**Phase**: Not yet implemented (Phase 3+)
**Next Steps**: Implement FastAPI application structure with authentication middleware
