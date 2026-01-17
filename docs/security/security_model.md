# Security Model

## Threat Model

### Assets to Protect

1. User data (conversations, preferences, learned behaviors)
2. System resources (CPU, memory, network)
3. User privacy (no unauthorized data access)
4. System integrity (prevent malicious tool execution)

### Threat Actors

- Malicious users attempting privilege escalation
- Compromised client applications
- Network attackers (MITM, eavesdropping)
- Insider threats (unauthorized data access)

## Security Layers

### 1. Authentication & Authorization

**API Gateway** (Phase 3+):

- JWT-based authentication
- Session management with Redis
- Role-based access control (RBAC)

**Implementation**:

```python
from fastapi import Depends, HTTPException
from jose import jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload["user_id"]
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 2. Tool Execution Sandbox

**Tool Executor** (Rust):

- Seccomp syscall filtering (whitelist only safe syscalls)
- Linux capabilities dropped (CAP_NET_ADMIN, etc.)
- Resource limits (cgroups: CPU, memory, disk I/O)
- Filesystem isolation (chroot/containers)

**Allowed Syscalls** (whitelist):

```
read, write, open, close, stat, fstat, lstat
exit, exit_group, brk, mmap, munmap
getpid, getuid, geteuid
```

**Forbidden Syscalls** (examples):

```
execve (arbitrary command execution)
socket (network access without permission)
mount (filesystem manipulation)
ptrace (process debugging/injection)
```

### 3. Permission Matrix

**Database Schema**: `user_permissions` table

| User ID | Tool Name   | Permission Level | Granted At |
| ------- | ----------- | ---------------- | ---------- |
| uuid-1  | web_search  | execute          | 2026-01-01 |
| uuid-1  | file_read   | read             | 2026-01-01 |
| uuid-2  | file_delete | denied           | -          |

**Permission Levels**:

- `read`: Read-only operations (file contents, search results)
- `write`: Modify data (file creation, updates)
- `execute`: Run commands (web search, API calls)
- `admin`: Full access (user management, system config)

### 4. Rate Limiting

**Implementation**: Redis token bucket

```python
from redis import Redis
import time

class RateLimiter:
    def check(self, user_id: str, tool: str, limit: int = 100) -> bool:
        key = f"rate:{user_id}:{tool}:{int(time.time() / 3600)}"
        count = redis.incr(key)
        redis.expire(key, 3600)  # 1 hour
        return count <= limit
```

**Default Quotas**:

- Web search: 50 requests/hour
- File operations: 200 requests/hour
- Browser automation: 20 requests/hour

### 5. Audit Logging

**Table**: `audit_log`

Every tool execution is logged:

```sql
INSERT INTO audit_log (user_id, action, tool_name, parameters, result, ip_address)
VALUES (?, 'tool_execute', 'web_search', '{"query": "..."}', 'success', ?);
```

**Retention**: 90 days (configurable)

### 6. Data Encryption

- **At Rest**: PostgreSQL Transparent Data Encryption (TDE)
- **In Transit**: TLS 1.3 for all gRPC communication
- **Secrets**: Environment variables + optional KMS integration

**gRPC TLS Configuration**:

```python
import grpc

credentials = grpc.ssl_channel_credentials(
    root_certificates=open('ca.crt', 'rb').read()
)
channel = grpc.secure_channel('localhost:50051', credentials)
```

### 7. Input Validation

**API Gateway**:

- Pydantic models for request validation
- SQL injection prevention (parameterized queries)
- XSS protection (HTML escaping)
- Path traversal prevention (whitelist directories)

**Example**:

```python
from pydantic import BaseModel, validator

class FileReadRequest(BaseModel):
    file_path: str

    @validator('file_path')
    def validate_path(cls, v):
        if '..' in v or v.startswith('/'):
            raise ValueError("Invalid path")
        return v
```

## Security Checklist

- [ ] All gRPC services use TLS in production
- [ ] JWT secrets are rotated every 90 days
- [ ] Tool executor runs with minimal capabilities
- [ ] Rate limiting is enforced on all endpoints
- [ ] Audit logs are immutable and backed up
- [ ] User data export/deletion requests are honored within 30 days
- [ ] Dependency scanning (Snyk, Dependabot) is enabled
- [ ] Penetration testing is performed quarterly

## Incident Response

**Contact**: security@voice-ai-agent.local (placeholder)

**Process**:

1. Detect: Anomaly detection in audit logs
2. Contain: Disable affected user accounts
3. Investigate: Review logs, identify scope
4. Remediate: Patch vulnerability, restore service
5. Report: Notify affected users within 72 hours

---

**Last Updated**: Phase 1 - January 2026
**Next Review**: Before production deployment (Phase 7)
