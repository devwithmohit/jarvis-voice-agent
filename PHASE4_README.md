# Phase 4: Voice Services - STT, TTS, Voice Gateway

This directory contains the voice interaction layer with Speech-to-Text (Whisper), Text-to-Speech (Coqui), and Voice Gateway (Rust) services.

## Services

### 1. STT Service (Speech-to-Text)

- **Technology**: Python + faster-whisper
- **Port**: 50052 (gRPC)
- **Features**:
  - Real-time streaming transcription
  - Batch transcription
  - Voice Activity Detection (VAD)
  - Multiple Whisper models (tiny, base, small, medium)

### 2. TTS Service (Text-to-Speech)

- **Technology**: Python + Coqui TTS
- **Port**: 50053 (gRPC)
- **Features**:
  - Natural speech synthesis
  - Streaming audio generation
  - Redis-based audio caching
  - Multiple voice profiles
  - Speed adjustment

### 3. Voice Gateway

- **Technology**: Rust
- **Port**: 50054 (gRPC)
- **Features**:
  - Wake-word detection (energy-based placeholder)
  - Audio stream orchestration
  - Real-time audio I/O
  - STT/TTS coordination

## Quick Start

### Prerequisites

```bash
# Python 3.11+
python --version

# Rust 1.75+
rustc --version

# Docker & Docker Compose
docker --version
docker-compose --version
```

### Setup

#### 1. STT Service

```bash
cd services/stt-service

# Install dependencies
pip install -r requirements.txt

# Generate proto files
chmod +x generate_proto.sh
./generate_proto.sh

# Copy environment file
cp .env.example .env

# Run locally
python src/main.py
```

#### 2. TTS Service

```bash
cd services/tts-service

# Install dependencies
pip install -r requirements.txt

# Generate proto files
chmod +x generate_proto.sh
./generate_proto.sh

# Copy environment file
cp .env.example .env

# Run locally (requires Redis)
python src/main.py
```

#### 3. Voice Gateway

```bash
cd services/voice-gateway

# Build
cargo build --release

# Run
./target/release/voice-gateway
```

### Docker Deployment

```bash
cd infra

# Build and start all services
docker-compose up -d stt-service tts-service voice-gateway

# View logs
docker-compose logs -f stt-service
docker-compose logs -f tts-service
docker-compose logs -f voice-gateway

# Stop services
docker-compose down
```

## Configuration

### STT Service (.env)

```bash
WHISPER_MODEL=base.en          # tiny.en, base.en, small.en, medium.en
DEVICE=cpu                     # or cuda
COMPUTE_TYPE=int8              # int8, float16, float32
SAMPLE_RATE=16000
GRPC_PORT=50052
SILENCE_TIMEOUT_MS=1500
```

### TTS Service (.env)

```bash
TTS_ENGINE=coqui
COQUI_MODEL=tts_models/en/ljspeech/tacotron2-DDC
USE_GPU=false
ENABLE_CACHE=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=2
GRPC_PORT=50053
SAMPLE_RATE=22050
```

### Voice Gateway

Wake-word detection currently uses simple energy-based detection. For production, integrate:

- Picovoice Porcupine (requires API key)
- openWakeWord (open-source alternative)

## API Usage

### STT Service (gRPC)

#### Streaming Transcription

```python
import grpc
from generated import voice_pb2, voice_pb2_grpc

channel = grpc.insecure_channel('localhost:50052')
stub = voice_pb2_grpc.STTServiceStub(channel)

# Stream audio chunks
def audio_generator():
    with open('audio.wav', 'rb') as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            yield voice_pb2.AudioChunk(data=chunk, sample_rate=16000)

# Get transcription
for transcript in stub.StreamTranscribe(audio_generator()):
    print(f"Transcript: {transcript.text} (final: {transcript.is_final})")
```

#### Batch Transcription

```python
with open('audio.wav', 'rb') as f:
    audio_data = f.read()

request = voice_pb2.AudioRequest(
    data=audio_data,
    language="en",
    enable_vad=True
)

result = stub.TranscribeBatch(request)
print(f"Transcript: {result.text}")
print(f"Confidence: {result.confidence}")
```

### TTS Service (gRPC)

#### Generate Speech

```python
import grpc
from generated import voice_pb2, voice_pb2_grpc

channel = grpc.insecure_channel('localhost:50053')
stub = voice_pb2_grpc.TTSServiceStub(channel)

request = voice_pb2.SynthesisRequest(
    text="Hello, this is a test of the text-to-speech system.",
    speed=1.0
)

response = stub.Synthesize(request)

# Save audio
with open('output.wav', 'wb') as f:
    f.write(response.audio_data)

print(f"Generated {len(response.audio_data)} bytes at {response.sample_rate}Hz")
```

#### Stream Long Text

```python
request = voice_pb2.SynthesisRequest(
    text="This is a very long text that will be synthesized in chunks...",
    speed=1.0
)

with open('output.wav', 'wb') as f:
    for chunk in stub.SynthesizeStream(request):
        f.write(chunk.data)
```

## Architecture

```
┌─────────────────┐
│  Voice Gateway  │ (Rust)
│   (Port 50054)  │
└────────┬────────┘
         │
         ├─── Wake-word Detection
         │    (Energy-based / Porcupine)
         │
         ├─── Audio Capture
         │    (cpal - cross-platform audio)
         │
         ├────► STT Service (Port 50052)
         │      └─ Whisper Transcription
         │
         └────► TTS Service (Port 50053)
                └─ Coqui Speech Synthesis
                └─ Redis Cache
```

## Models

### Whisper Models (STT)

| Model     | Size   | Speed     | Accuracy |
| --------- | ------ | --------- | -------- |
| tiny.en   | 39 MB  | Very Fast | Low      |
| base.en   | 74 MB  | Fast      | Good     |
| small.en  | 244 MB | Medium    | Better   |
| medium.en | 769 MB | Slow      | Best     |

**Recommendation**: Use `base.en` for balanced performance

### Coqui TTS Models

Default: `tts_models/en/ljspeech/tacotron2-DDC`

Other options:

- `tts_models/en/ljspeech/glow-tts`
- `tts_models/en/vctk/vits`
- `tts_models/multilingual/multi-dataset/your_tts`

## Performance

### STT Service

- **Latency**: ~100-500ms per chunk (base.en model)
- **Throughput**: Real-time factor ~0.3x (processes 1s audio in 0.3s)
- **Memory**: ~500MB (base.en model loaded)

### TTS Service

- **Latency**: ~200-800ms per sentence
- **Cache hit rate**: 80-95% for common phrases
- **Memory**: ~800MB (Coqui model loaded)

### Voice Gateway

- **Wake-word latency**: <50ms
- **Audio buffer**: 1-2 seconds
- **CPU usage**: <5% when idle, <20% when processing

## Testing

### Test STT Service

```bash
cd services/stt-service

# Run tests
pytest tests/

# Test with sample audio
python examples/test_stt.py --audio sample.wav
```

### Test TTS Service

```bash
cd services/tts-service

# Run tests
pytest tests/

# Test synthesis
python examples/test_tts.py --text "Hello world"
```

### Test Voice Gateway

```bash
cd services/voice-gateway

# Run tests
cargo test

# Run with verbose logging
RUST_LOG=debug cargo run
```

## Troubleshooting

### STT Issues

**Problem**: `ModuleNotFoundError: No module named 'faster_whisper'`

```bash
pip install faster-whisper
```

**Problem**: Slow transcription

- Try smaller model (`tiny.en` or `base.en`)
- Enable GPU: set `DEVICE=cuda`
- Reduce audio quality to 16kHz

### TTS Issues

**Problem**: `ModuleNotFoundError: No module named 'TTS'`

```bash
pip install TTS
```

**Problem**: Audio quality poor

- Try different model: `tts_models/en/vctk/vits`
- Increase sample rate to 22050Hz

**Problem**: Redis connection failed

```bash
# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Or disable cache
export ENABLE_CACHE=false
```

### Voice Gateway Issues

**Problem**: No audio device found

- Check audio permissions
- On Linux: Add user to `audio` group
  ```bash
  sudo usermod -a -G audio $USER
  ```

**Problem**: Build fails

- Update Rust: `rustup update`
- Install system dependencies:

  ```bash
  # Ubuntu/Debian
  sudo apt-get install libasound2-dev

  # macOS
  brew install portaudio
  ```

## Next Steps

- **Phase 5**: Tool Executor (Rust) & Web Service (Python/Playwright)
- **Phase 6**: API Gateway + React Dashboard

## Resources

- [Whisper Documentation](https://github.com/openai/whisper)
- [faster-whisper](https://github.com/guillaumekln/faster-whisper)
- [Coqui TTS](https://github.com/coqui-ai/TTS)
- [cpal Audio Library](https://github.com/RustAudio/cpal)
- [Picovoice Porcupine](https://picovoice.ai/platform/porcupine/)
