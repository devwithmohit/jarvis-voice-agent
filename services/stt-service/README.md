# Speech-to-Text Service

**Language**: Python 3.11+
**Framework**: gRPC (asyncio)
**Purpose**: Real-time speech-to-text transcription using Whisper

## Responsibilities

- Real-time audio stream transcription
- Batch audio file transcription
- Language detection and multi-language support
- Word-level timestamps
- Confidence scoring

## gRPC Service

Implements `STTService` from `shared/proto/stt_tts.proto`:

- `TranscribeStream` - Real-time streaming transcription
- `TranscribeFile` - Batch file transcription
- `GetSupportedLanguages` - List available languages
- `HealthCheck` - Service health status

## Whisper Configuration

**Model Options**:

- `tiny.en` - Fast, English-only (39M params)
- `base.en` - Balanced, English-only (74M params)
- `small.en` - Good quality, English-only (244M params)
- `medium.en` - High quality, English-only (769M params)
- `large-v3` - Best quality, multilingual (1550M params)

**Recommended**: `base.en` for real-time, `small.en` for accuracy

**Implementation**: `faster-whisper` (2-4x faster than openai-whisper with CTranslate2)

## Audio Processing

**Input Format**:

- Sample Rate: 16000 Hz (Whisper requirement)
- Channels: 1 (mono)
- Bit Depth: 16-bit PCM
- Chunk Size: 1024 samples (~64ms at 16kHz)

**Streaming Pipeline**:

```
Audio Chunks → Buffer → VAD (Voice Activity Detection)
    → Whisper Transcription → Confidence Filtering → gRPC Response
```

## Voice Activity Detection (VAD)

- **Purpose**: Detect speech vs. silence to reduce unnecessary transcription
- **Implementation**: `webrtcvad` or Silero VAD
- **Threshold**: 50% voice probability
- **Benefit**: Reduce latency and compute costs

## Performance Optimization

1. **Model Caching**: Load model once on startup
2. **Batch Processing**: Accumulate 3-5 seconds of audio before transcription
3. **GPU Acceleration**: CUDA if available, fallback to CPU
4. **Quantization**: int8 for faster inference with minimal quality loss

## Dependencies

- `faster-whisper` - Optimized Whisper implementation
- `openai-whisper` - Original Whisper (fallback)
- `torch` - PyTorch for model inference
- `soundfile` - Audio file I/O

## Running Locally

```bash
cd services/stt-service
pip install -r requirements.txt

# Download Whisper model (first run)
# Model will auto-download to ~/.cache/whisper/

python -m app.main
```

## Environment Variables

```
WHISPER_MODEL=base.en
WHISPER_DEVICE=cpu  # or cuda
WHISPER_COMPUTE_TYPE=int8
STT_CHUNK_SIZE=1024
STT_BUFFER_DURATION=3.0  # seconds
```

## Benchmarks (Expected)

| Model    | Device | Real-time Factor | Accuracy (WER) |
| -------- | ------ | ---------------- | -------------- |
| tiny.en  | CPU    | 0.1x             | ~15%           |
| base.en  | CPU    | 0.3x             | ~10%           |
| small.en | CPU    | 0.8x             | ~7%            |
| base.en  | GPU    | 0.05x            | ~10%           |

Real-time Factor < 1.0 means faster than real-time

## Status

**Phase**: Not yet implemented (Phase 4)
**Next Steps**:

1. Implement audio streaming buffer
2. Integrate faster-whisper with VAD
3. Build gRPC server with async transcription
4. Add language detection
5. Optimize batch size for latency vs. throughput
6. Add comprehensive error handling
