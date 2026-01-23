# Phase 5 Quick Reference

## Services

| Service       | Port  | Technology          | Purpose                         |
| ------------- | ----- | ------------------- | ------------------------------- |
| Tool Executor | 50055 | Rust + Tokio        | Sandboxed file ops and commands |
| Web Service   | 50056 | Python + Playwright | Browser automation and search   |

---

## Tool Executor API

### File Operations

```bash
# Read File
grpcurl -plaintext -d '{"path": "/tmp/voice-agent/test.txt"}' \
  localhost:50055 tool.ToolExecutor/ReadFile

# Write File
grpcurl -plaintext -d '{"path": "/tmp/voice-agent/test.txt", "content": "Hello"}' \
  localhost:50055 tool.ToolExecutor/WriteFile

# List Directory
grpcurl -plaintext -d '{"path": "/tmp/voice-agent"}' \
  localhost:50055 tool.ToolExecutor/ListDirectory

# File Exists
grpcurl -plaintext -d '{"path": "/tmp/voice-agent/test.txt"}' \
  localhost:50055 tool.ToolExecutor/FileExists

# Get File Info
grpcurl -plaintext -d '{"path": "/tmp/voice-agent/test.txt"}' \
  localhost:50055 tool.ToolExecutor/GetFileInfo
```

### System Operations

```bash
# Execute Command
grpcurl -plaintext -d '{"command": "ls", "args": ["-la"]}' \
  localhost:50055 tool.ToolExecutor/ExecuteCommand

# Get Working Directory
grpcurl -plaintext -d '{}' \
  localhost:50055 tool.ToolExecutor/GetWorkingDirectory

# Get Environment Variable
grpcurl -plaintext -d '{"name": "PATH"}' \
  localhost:50055 tool.ToolExecutor/GetEnvironmentVariable
```

---

## Web Service API

### Browser Operations

```bash
# Navigate
grpcurl -plaintext -d '{"url": "https://www.google.com"}' \
  localhost:50056 web.WebService/Navigate

# Click Element
grpcurl -plaintext -d '{"selector": "button#search"}' \
  localhost:50056 web.WebService/ClickElement

# Type Text
grpcurl -plaintext -d '{"selector": "input[name=q]", "text": "AI"}' \
  localhost:50056 web.WebService/TypeText

# Get Text
grpcurl -plaintext -d '{"selector": "h1"}' \
  localhost:50056 web.WebService/GetText

# Get Page Content
grpcurl -plaintext -d '{}' \
  localhost:50056 web.WebService/GetPageContent

# Screenshot
grpcurl -plaintext -d '{"path": "/tmp/screenshot.png"}' \
  localhost:50056 web.WebService/Screenshot

# Wait For Selector
grpcurl -plaintext -d '{"selector": "div.result", "timeout_ms": 5000}' \
  localhost:50056 web.WebService/WaitForSelector
```

### Search & Scraping

```bash
# Search
grpcurl -plaintext -d '{"query": "AI", "engine": "google", "max_results": 5}' \
  localhost:50056 web.WebService/Search

# Extract Text
grpcurl -plaintext -d '{"selector": "div.content"}' \
  localhost:50056 web.WebService/ExtractText

# Extract Links
grpcurl -plaintext -d '{"base_url": "https://example.com"}' \
  localhost:50056 web.WebService/ExtractLinks

# Extract Metadata
grpcurl -plaintext -d '{}' \
  localhost:50056 web.WebService/ExtractMetadata
```

---

## Docker Commands

### Start Services

```bash
# Start both services
docker-compose up -d tool-executor web-service

# Start Tool Executor only
docker-compose up -d tool-executor

# Start Web Service only
docker-compose up -d web-service
```

### View Logs

```bash
# Follow all logs
docker-compose logs -f tool-executor web-service

# Follow Tool Executor logs
docker-compose logs -f tool-executor

# Follow Web Service logs
docker-compose logs -f web-service

# Last 100 lines
docker-compose logs --tail=100 tool-executor
```

### Service Management

```bash
# Check service status
docker-compose ps

# Restart services
docker-compose restart tool-executor web-service

# Stop services
docker-compose stop tool-executor web-service

# Remove services
docker-compose down
```

### Rebuild Services

```bash
# Rebuild Tool Executor
docker-compose build tool-executor

# Rebuild Web Service
docker-compose build web-service

# Rebuild and restart
docker-compose up -d --build tool-executor web-service
```

---

## Configuration Files

### Tool Executor Security

**File:** `services/tool-executor/config/security.yaml`

```yaml
# Key settings to customize:
file_operations:
  allowed_directories:
    - "/tmp/voice-agent/*" # Add your paths here
    - "~/Documents/*"

  allowed_extensions:
    read: [".txt", ".json"] # Add extensions here
    write: [".txt", ".json"]

system_commands:
  allowlist:
    - "ls" # Add commands here
    - "pwd"

  blocked_patterns:
    - "rm -rf" # Add dangerous patterns here
    - "sudo"

  timeout_seconds: 10 # Adjust timeout
```

### Web Service Browser Config

**File:** `services/web-service/config/browser.yaml`

```yaml
# Key settings to customize:
security:
  allowed_domains:
    - "*.google.com" # Add domains here
    - "*.wikipedia.org"

  blocked_domains:
    - "*.onion" # Add blocked domains here
    - "localhost"

browser:
  headless: true # Set false for debugging
  timeout_ms: 30000 # Page load timeout

search:
  engines:
    google:
      url: "https://www.google.com/search?q={query}"
```

---

## Environment Variables

### Tool Executor

```bash
RUST_LOG=info              # debug, info, warn, error
GRPC_PORT=50055            # Server port
```

### Web Service

```bash
GRPC_PORT=50056            # Server port
GRPC_HOST=0.0.0.0          # Bind address
HEADLESS=true              # Browser mode
BROWSER_TIMEOUT_MS=30000   # Page timeout
VIEWPORT_WIDTH=1920        # Browser width
VIEWPORT_HEIGHT=1080       # Browser height
SERPAPI_KEY=               # Optional API key
```

---

## Local Development

### Tool Executor

```bash
cd services/tool-executor

# Build
cargo build

# Run
cargo run

# Run with debug logging
RUST_LOG=debug cargo run

# Run tests
cargo test

# Format code
cargo fmt

# Lint
cargo clippy
```

### Web Service

```bash
cd services/web-service

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run service
python src/main.py

# Run with debug logging
export GRPC_PORT=50056
python src/main.py

# Generate proto code
bash generate_proto.sh
```

---

## Troubleshooting

### Tool Executor

**Permission Denied:**

```bash
# Fix file permissions
sudo chown -R $(whoami) /tmp/voice-agent
chmod 755 /tmp/voice-agent
```

**Path Not Allowed:**

- Add path to `allowed_directories` in `config/security.yaml`
- Remove from `blocked_paths` if blocked

**Command Not Allowed:**

- Add command to `allowlist` in `config/security.yaml`
- Remove from `blocked_patterns` if blocked

### Web Service

**URL Not Allowed:**

- Add domain to `allowed_domains` in `config/browser.yaml`
- Remove from `blocked_domains` if blocked

**Browser Not Found:**

```bash
playwright install chromium --with-deps
```

**Page Load Timeout:**

```bash
# Increase timeout
export BROWSER_TIMEOUT_MS=60000
```

---

## Performance Tips

### Tool Executor

- Keep `allowed_directories` specific to minimize validation overhead
- Use absolute paths to avoid resolution overhead
- Monitor timeout occurrences - increase if needed
- Limit file operations to necessary directories only

### Web Service

- Use headless mode in production (HEADLESS=true)
- Increase timeout for slow websites
- Limit search results to needed amount
- Close browser when done with session
- Monitor memory usage - restart if excessive

---

## Security Best Practices

### Tool Executor

- ✅ Use allowlist approach (not blocklist)
- ✅ Restrict to minimal directories needed
- ✅ Keep allowlist of commands small
- ✅ Use timeout enforcement
- ✅ Monitor validation failures
- ✅ Regular security config reviews

### Web Service

- ✅ Use domain allowlist (not blocklist)
- ✅ Run in headless mode
- ✅ Limit redirect chains
- ✅ Enforce page size limits
- ✅ Monitor blocked URL attempts
- ✅ Use custom user agent

---

## Integration Examples

### Python Client

```python
import grpc
from generated import tool_pb2, tool_pb2_grpc, web_pb2, web_pb2_grpc

# Connect
tool_channel = grpc.insecure_channel('localhost:50055')
tool_stub = tool_pb2_grpc.ToolExecutorStub(tool_channel)

web_channel = grpc.insecure_channel('localhost:50056')
web_stub = web_pb2_grpc.WebServiceStub(web_channel)

# File operation
response = tool_stub.ReadFile(tool_pb2.FileReadRequest(
    path='/tmp/voice-agent/test.txt'
))
print(f"Content: {response.content}")

# Web search
response = web_stub.Search(web_pb2.SearchRequest(
    query='artificial intelligence',
    engine='google',
    max_results=5
))
for result in response.results:
    print(f"{result.title}: {result.url}")
```

### Rust Client

```rust
use tonic::Request;
use tool_proto::tool_executor_client::ToolExecutorClient;
use tool_proto::FileReadRequest;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut client = ToolExecutorClient::connect("http://localhost:50055").await?;

    let request = Request::new(FileReadRequest {
        path: "/tmp/voice-agent/test.txt".to_string(),
    });

    let response = client.read_file(request).await?;
    println!("Content: {}", response.into_inner().content);

    Ok(())
}
```

---

## Resources

- **Documentation**: `PHASE5_README.md`, `PHASE5_IMPLEMENTATION_SUMMARY.md`
- **Proto Definitions**: `protos/tool.proto`, `protos/web.proto`
- **Configuration**: `services/*/config/*.yaml`
- **Docker Compose**: `infra/docker-compose.yml`

---

**Quick Start**: `docker-compose up -d tool-executor web-service`
