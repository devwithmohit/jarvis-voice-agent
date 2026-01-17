# Voice Gateway Service

**Language**: Rust 1.75+
**Framework**: Tokio + Tonic (gRPC)
**Purpose**: High-performance audio streaming and wake-word detection

## Responsibilities

- **Audio Streaming**: Low-latency WebSocket/gRPC audio streaming
- **Wake-word Detection**: Always-listening mode with local wake-word model
- **Audio I/O**: Cross-platform microphone/speaker access
- **Protocol Translation**: WebSocket ↔ gRPC bridge

## Why Rust?

This service is in Rust for:

- **Sub-100ms Latency**: Real-time audio streaming requires minimal overhead
- **Memory Safety**: Long-running daemon handling system audio resources
- **Concurrency**: Tokio async runtime for thousands of concurrent connections
- **Stability**: No garbage collection pauses during audio processing

## gRPC Service

Implements `VoiceGateway` from `shared/proto/voice.proto`:

- `StreamAudio` - Bidirectional audio streaming
- `DetectWakeWord` - Continuous wake-word detection
- `StreamTTS` - TTS audio playback
- `HealthCheck` - Service health

## Audio Pipeline

```
Microphone → cpal → Audio Buffer (1024 samples, 16kHz mono)
    → Wake-word Detection → gRPC Stream → STT Service

TTS Service → gRPC Stream → Audio Buffer → cpal → Speaker
```

## Wake-word Detection

**Implementation**: openWakeWord (Rust bindings)
**Models**: "hey_jarvis", "hey_mycroft" (configurable)
**Threshold**: 0.5 (50% confidence)
**Performance**: < 10ms inference time on CPU

**Detection Flow**:

1. Accumulate 1-second audio windows
2. Run wake-word model inference
3. If detected, activate full transcription mode
4. Otherwise, discard audio (privacy-first)

## WebSocket Bridge

**Port**: 9000
**Protocol**: Binary WebSocket with PCM audio chunks

**Message Format**:

```json
{
  "type": "audio_chunk",
  "data": "base64_encoded_pcm",
  "timestamp": 1234567890,
  "session_id": "uuid"
}
```

## Audio Configuration

- **Sample Rate**: 16000 Hz (Whisper requirement)
- **Channels**: 1 (mono)
- **Format**: 16-bit PCM (signed integer)
- **Buffer Size**: 1024 samples (~64ms at 16kHz)
- **Latency Target**: < 100ms end-to-end

## Dependencies

- `tokio` - Async runtime
- `tonic` - gRPC framework
- `cpal` - Cross-platform audio I/O (ALSA, CoreAudio, WASAPI)
- `hound` - WAV encoding/decoding
- `tokio-tungstenite` - WebSocket support

## Building

```bash
cd services/voice-gateway
cargo build --release

# With wake-word detection
cargo build --release --features wake-word
```

## Running

```bash
cargo run --release

# Custom configuration
AUDIO_DEVICE=default \
SAMPLE_RATE=16000 \
BUFFER_SIZE=1024 \
WAKEWORD_THRESHOLD=0.5 \
cargo run --release
```

## Environment Variables

```
AUDIO_DEVICE=default
SAMPLE_RATE=16000
CHANNELS=1
BUFFER_SIZE=1024
WAKEWORD_MODEL=hey_jarvis
WAKEWORD_THRESHOLD=0.5
WEBSOCKET_PORT=9000
GRPC_PORT=50060
```

## Performance Benchmarks (Expected)

| Metric                 | Target  | Typical |
| ---------------------- | ------- | ------- |
| Audio Latency          | < 100ms | ~80ms   |
| Wake-word Inference    | < 10ms  | ~5ms    |
| Memory Usage           | < 50MB  | ~30MB   |
| CPU Usage (idle)       | < 5%    | ~2%     |
| Concurrent Connections | 1000+   | N/A     |

## Status

**Phase**: Not yet implemented (Phase 4)
**Next Steps**:

1. Implement audio capture with cpal
2. Build WebSocket server for client connections
3. Integrate openWakeWord for detection
4. Create gRPC client for STT service
5. Build TTS audio playback pipeline
6. Add comprehensive error handling and reconnection logic
