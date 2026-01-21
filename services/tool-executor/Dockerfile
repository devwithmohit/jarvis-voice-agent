FROM rust:1.75 as builder

WORKDIR /app

# Copy manifests
COPY Cargo.toml Cargo.lock ./
COPY build.rs ./

# Copy source code
COPY src ./src
COPY config ./config
COPY ../../protos ./protos

# Build dependencies (cached layer)
RUN mkdir -p src && echo "fn main() {}" > src/main.rs
RUN cargo build --release
RUN rm -f target/release/deps/tool_executor*

# Build application
COPY src ./src
RUN cargo build --release

# Runtime image
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy binary and config
COPY --from=builder /app/target/release/tool-executor /app/tool-executor
COPY config /app/config

# Create directories for allowed operations
RUN mkdir -p /tmp/voice-agent

EXPOSE 50055

# Run as non-root user
RUN useradd -m -u 1000 voice-agent && \
    chown -R voice-agent:voice-agent /app /tmp/voice-agent

USER voice-agent

CMD ["./tool-executor"]
