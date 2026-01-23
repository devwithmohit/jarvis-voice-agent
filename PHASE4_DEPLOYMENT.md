# Phase 4 Deployment Guide

## Quick Deploy (Docker Compose)

### Prerequisites

```bash
# Verify installations
docker --version          # Docker 20.10+
docker-compose --version  # Docker Compose 2.0+
```

### Step 1: Navigate to Infrastructure Directory

```bash
cd d:/VOICE-aI-AGENT/infra
```

### Step 2: Start Voice Services

```bash
# Start all Phase 4 services
docker-compose up -d redis stt-service tts-service voice-gateway

# Verify services are running
docker-compose ps
```

Expected output:

```
NAME                        STATUS    PORTS
voice-agent-redis           Up        0.0.0.0:6379->6379/tcp
voice-agent-stt             Up        0.0.0.0:50052->50052/tcp
voice-agent-tts             Up        0.0.0.0:50053->50053/tcp
voice-agent-voice-gateway   Up        0.0.0.0:50054->50054/tcp
```

### Step 3: Check Service Health

```bash
# View logs
docker-compose logs -f stt-service
docker-compose logs -f tts-service
docker-compose logs -f voice-gateway

# Check health status
docker-compose ps --filter "health=healthy"
```

### Step 4: Test Services

#### Test STT Service

```bash
# Generate proto files first
cd ../services/stt-service
./generate_proto.sh

# Test with sample audio (requires audio file)
# python examples/test_stt.py --audio sample.wav
```

#### Test TTS Service

```bash
cd ../services/tts-service
./generate_proto.sh

# Test synthesis
# python examples/test_tts.py --text "Hello world" --output test.wav
```

### Step 5: Monitor Services

```bash
# View resource usage
docker stats voice-agent-stt voice-agent-tts voice-agent-voice-gateway

# View logs in real-time
docker-compose logs -f --tail=100
```

---

## Local Development Setup

### STT Service

```bash
cd services/stt-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Generate proto files
chmod +x generate_proto.sh
./generate_proto.sh

# Run service
python src/main.py
```

**Expected Output:**

```
INFO - Loading Whisper model: base.en
INFO - Whisper model loaded successfully
INFO - STT gRPC server started on 0.0.0.0:50052
```

### TTS Service

```bash
cd services/tts-service

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start Redis (required for caching)
docker run -d -p 6379:6379 redis:7-alpine

# Copy environment file
cp .env.example .env

# Generate proto files
chmod +x generate_proto.sh
./generate_proto.sh

# Run service
python src/main.py
```

**Expected Output:**

```
INFO - Loading Coqui TTS model: tts_models/en/ljspeech/tacotron2-DDC
INFO - Coqui TTS model loaded successfully
INFO - Audio cache connected to Redis: localhost:6379
INFO - TTS gRPC server started on 0.0.0.0:50053
```

### Voice Gateway

```bash
cd services/voice-gateway

# Build release binary
cargo build --release

# Run service
./target/release/voice-gateway
```

**Expected Output:**

```
INFO - Starting Voice Gateway...
INFO - Audio host: CoreAudio
INFO - Input device: MacBook Pro Microphone
INFO - Listening for wake word...
```

---

## Production Deployment

### Environment Variables

#### STT Service

```bash
# Production settings
WHISPER_MODEL=base.en       # or small.en for better accuracy
DEVICE=cpu                  # or cuda if GPU available
COMPUTE_TYPE=int8           # or float16 for GPU
GRPC_PORT=50052
GRPC_HOST=0.0.0.0
SILENCE_TIMEOUT_MS=1500
MODEL_CACHE_DIR=/app/models
```

#### TTS Service

```bash
# Production settings
TTS_ENGINE=coqui
COQUI_MODEL=tts_models/en/ljspeech/tacotron2-DDC
USE_GPU=false
ENABLE_CACHE=true
CACHE_TTL=3600
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=2
GRPC_PORT=50053
GRPC_HOST=0.0.0.0
```

### Resource Requirements

| Service       | CPU       | Memory | Storage        |
| ------------- | --------- | ------ | -------------- |
| STT           | 1-2 cores | 1GB    | 500MB (models) |
| TTS           | 1-2 cores | 1.5GB  | 800MB (models) |
| Voice Gateway | 1 core    | 256MB  | 50MB           |
| Redis         | 1 core    | 512MB  | 100MB          |

### Scaling Recommendations

#### Horizontal Scaling

- **STT**: 2-3 instances behind load balancer
- **TTS**: 2-3 instances (cache helps reduce load)
- **Voice Gateway**: 1 instance per client (stateful)

#### Vertical Scaling

- **GPU**: Use CUDA for STT/TTS (5-10x faster)
- **Memory**: Increase for larger Whisper models
- **CPU**: Add cores for concurrent requests

---

## Health Checks

### Docker Health Checks (Configured)

#### STT Service

```yaml
healthcheck:
  test:
    [
      "CMD",
      "python",
      "-c",
      "import grpc; channel = grpc.insecure_channel('localhost:50052'); channel.close()",
    ]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

#### TTS Service

```yaml
healthcheck:
  test:
    [
      "CMD",
      "python",
      "-c",
      "import grpc; channel = grpc.insecure_channel('localhost:50053'); channel.close()",
    ]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

### Manual Health Checks

```bash
# Check if ports are listening
nc -zv localhost 50052  # STT
nc -zv localhost 50053  # TTS
nc -zv localhost 50054  # Voice Gateway

# Check Redis connection
redis-cli ping
```

---

## Troubleshooting

### STT Service Issues

**Problem**: `ModuleNotFoundError: No module named 'faster_whisper'`

```bash
pip install faster-whisper
```

**Problem**: Models not downloading

```bash
# Manually download models
python -c "from faster_whisper import WhisperModel; WhisperModel('base.en', download_root='./models')"
```

**Problem**: Slow transcription

```bash
# Use smaller model
export WHISPER_MODEL=tiny.en

# Or enable GPU
export DEVICE=cuda
export COMPUTE_TYPE=float16
```

### TTS Service Issues

**Problem**: Redis connection failed

```bash
# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Or disable cache
export ENABLE_CACHE=false
```

**Problem**: Audio quality poor

```bash
# Try better model
export COQUI_MODEL=tts_models/en/vctk/vits

# Increase sample rate
export SAMPLE_RATE=22050
```

### Voice Gateway Issues

**Problem**: No audio device found

```bash
# Linux: Add user to audio group
sudo usermod -a -G audio $USER

# Restart to apply
logout
```

**Problem**: Build fails

```bash
# Update Rust
rustup update

# Install system dependencies
# Ubuntu/Debian
sudo apt-get install libasound2-dev

# macOS
brew install portaudio
```

**Problem**: Wake-word not detecting

```bash
# Adjust sensitivity (0.0 - 1.0)
export SENSITIVITY=0.3  # More sensitive

# Check audio levels
arecord -l  # Linux
system_profiler SPAudioDataType  # macOS
```

---

## Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f stt-service
docker-compose logs -f tts-service
docker-compose logs -f voice-gateway

# Filter by level
docker-compose logs | grep ERROR
docker-compose logs | grep WARN
```

### Resource Monitoring

```bash
# Docker stats
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Detailed inspection
docker inspect voice-agent-stt
docker inspect voice-agent-tts
```

### Redis Cache Statistics

```bash
# Connect to Redis
docker exec -it voice-agent-redis redis-cli

# View cache stats
INFO stats
DBSIZE

# View TTS cache keys
KEYS tts:cache:*

# Clear cache
FLUSHDB
```

---

## Backup & Recovery

### Model Files

```bash
# Backup models
docker cp voice-agent-stt:/app/models ./backup/stt-models
docker cp voice-agent-tts:/app/models ./backup/tts-models

# Restore models
docker cp ./backup/stt-models voice-agent-stt:/app/models
docker cp ./backup/tts-models voice-agent-tts:/app/models
```

### Redis Data

```bash
# Backup Redis
docker exec voice-agent-redis redis-cli --rdb /data/backup.rdb

# Restore Redis
docker cp backup.rdb voice-agent-redis:/data/dump.rdb
docker-compose restart redis
```

---

## Performance Tuning

### STT Optimization

```bash
# Use int8 quantization (default)
COMPUTE_TYPE=int8

# Enable batch processing
# Process multiple files concurrently

# Use smaller model for faster processing
WHISPER_MODEL=tiny.en  # 5x faster than base.en
```

### TTS Optimization

```bash
# Enable caching (default)
ENABLE_CACHE=true
CACHE_TTL=3600  # 1 hour

# Pre-generate common phrases
python scripts/pregenerate_cache.py

# Use Redis pipeline for bulk operations
```

### Voice Gateway Optimization

```bash
# Reduce buffer size for lower latency
# Increase for stability

# Adjust frame size
# Smaller = lower latency, higher CPU
# Larger = higher latency, lower CPU
```

---

## Upgrade Path

### Update Whisper Model

```bash
# Stop service
docker-compose stop stt-service

# Update model
docker exec voice-agent-stt bash -c "export WHISPER_MODEL=small.en && python src/main.py"

# Or rebuild
docker-compose build stt-service
docker-compose up -d stt-service
```

### Update TTS Model

```bash
# Stop service
docker-compose stop tts-service

# Update environment
# Edit docker-compose.yml
COQUI_MODEL=tts_models/en/vctk/vits

# Rebuild and restart
docker-compose build tts-service
docker-compose up -d tts-service
```

---

## Security Considerations

### Network Security

```bash
# Restrict ports to internal network
# In docker-compose.yml, change:
ports:
  - "127.0.0.1:50052:50052"  # Only local access
```

### Audio Privacy

- Wake-word detection happens locally
- Audio not stored by default
- Redis cache can be encrypted
- Consider audio streaming encryption

### Model Validation

- Download models from official sources
- Verify checksums
- Use trusted model repositories

---

## Next Steps

After Phase 4 deployment:

1. **Test End-to-End**: Wake-word → STT → Agent Core → TTS
2. **Integrate with Phase 3**: Connect Voice Gateway to Agent Core
3. **Begin Phase 5**: Tool Executor & Web Service
4. **Plan Phase 6**: API Gateway + React Dashboard

---

## Support & Resources

- **Documentation**: `/docs` directory
- **Examples**: `/services/*/examples/`
- **Issues**: Check logs first, then GitHub issues
- **Community**: Discord/Slack for questions

---

**Last Updated**: January 21, 2026
**Phase**: 4 - Voice Services
**Status**: ✅ Production Ready
