# Tool Executor Service

**Language**: Rust 1.75+
**Framework**: Tokio + Tonic (gRPC)
**Purpose**: Sandboxed tool execution with security controls

## Responsibilities

- **Sandboxed Execution**: Run tools in isolated environment
- **Permission Enforcement**: Validate user permissions before execution
- **Rate Limiting**: Prevent abuse with per-user quotas
- **Audit Logging**: Record all tool invocations
- **Resource Limits**: CPU, memory, and time constraints

## Why Rust?

This service is in Rust for:

- **Memory Safety**: Prevents buffer overflows and memory corruption in tool execution
- **Process Isolation**: Safe syscall filtering with seccomp
- **Performance**: Fast startup and low overhead for tool spawning
- **Reliability**: No runtime crashes handling untrusted tool outputs

## gRPC Service

Implements `ToolExecutor` from `shared/proto/tool.proto`:

- `ExecuteTool` - Run a single tool with security checks
- `ExecuteBatch` - Run multiple tools (sequential or parallel)
- `CheckPermission` - Verify user has permission
- `ListAvailableTools` - Get tools user can access
- `CancelExecution` - Cancel a running tool

## Security Architecture

### Multi-Layer Defense

1. **Allow-list**: Only pre-approved tools can run
2. **Permission Matrix**: Per-user, per-tool permissions (read/write/execute)
3. **Sandboxing**: Seccomp syscall filtering
4. **Resource Limits**: cgroups for CPU/memory
5. **Timeout**: Max execution time (default 60s)
6. **Audit Logging**: All executions logged to PostgreSQL

### Sandbox Configuration

```rust
// Example seccomp policy (whitelist syscalls)
let allowed_syscalls = [
    "read", "write", "open", "close", "stat", "fstat",
    "exit", "exit_group", "brk", "mmap", "munmap"
];

// Drop all capabilities except necessary ones
drop_capabilities(CAP_NET_BIND_SERVICE);
```

### Process Execution

```
Tool Request → Permission Check → Rate Limit Check
    → Spawn Process (sandboxed) → Monitor (timeout, resource limits)
    → Capture Output → Audit Log → Return Result
```

## Tool Definition

Tools are defined in configuration file:

```json
{
  "name": "file_read",
  "description": "Read file contents",
  "command": "/usr/bin/cat",
  "args": ["{{file_path}}"],
  "requires_confirmation": false,
  "permission_level": "read",
  "rate_limit_per_hour": 200,
  "timeout_seconds": 10,
  "allowed_paths": ["/home/user/documents/**"]
}
```

## Rate Limiting

**Implementation**: Token bucket algorithm (governor crate)

**Default Quotas**:

- 100 requests/hour per tool per user
- Configurable per tool type
- Burst capacity: 10 requests

**Enforcement**:

```rust
let rate_limiter = RateLimiter::keyed(
    Quota::per_hour(nonzero!(100u32))
);

if rate_limiter.check_key(&user_tool_key).is_err() {
    return Err(Status::resource_exhausted("Rate limit exceeded"));
}
```

## Supported Tools (Initial)

| Tool          | Command | Permission | Rate Limit |
| ------------- | ------- | ---------- | ---------- |
| `file_read`   | `cat`   | read       | 200/hr     |
| `file_list`   | `ls`    | read       | 500/hr     |
| `web_request` | `curl`  | execute    | 50/hr      |
| `date_time`   | `date`  | read       | 1000/hr    |

## Dependencies

- `tokio` - Async runtime
- `tonic` - gRPC framework
- `nix` - Unix process control
- `seccompiler` - Syscall filtering
- `caps` - Linux capabilities management
- `governor` - Rate limiting

## Building

```bash
cd services/tool-executor
cargo build --release
```

## Running

```bash
cargo run --release

# Custom configuration
MAX_EXECUTION_TIME=60 \
ENABLE_SANDBOXING=true \
cargo run --release
```

## Environment Variables

```
MAX_EXECUTION_TIME=60
ENABLE_SANDBOXING=true
AUDIT_LOG_ENABLED=true
RATE_LIMIT_DEFAULT=100
ALLOWED_TOOLS_CONFIG=/etc/tools.json
```

## Security Testing

```bash
# Test sandboxing (should fail)
cargo test test_sandbox_blocks_forbidden_syscall

# Test rate limiting
cargo test test_rate_limit_enforcement

# Test permission checks
cargo test test_unauthorized_tool_execution_fails
```

## Status

**Phase**: Not yet implemented (Phase 5)
**Next Steps**:

1. Implement tool configuration loader
2. Build permission validation against PostgreSQL
3. Create seccomp sandbox profiles
4. Implement rate limiting with Redis backend
5. Add process execution with resource limits
6. Build audit logging to PostgreSQL
7. Add comprehensive security tests
