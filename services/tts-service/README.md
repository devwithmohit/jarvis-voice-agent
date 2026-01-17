# Text-to-Speech Service

**Language**: Python 3.11+
**Framework**: gRPC (asyncio)
**Purpose**: Convert text to natural speech using Coqui TTS

## Responsibilities

- Text-to-speech synthesis
- Multiple voice profiles
- Speed, pitch, and volume control
- Audio streaming to clients
- Voice cloning (optional)

## gRPC Service

Implements `TTSService` from `shared/proto/stt_tts.proto`:

- `Synthesize` - Generate speech from text (streaming audio)
- `ListVoices` - Get available voice profiles
- `CloneVoice` - Create custom voice from samples (optional)
- `HealthCheck` - Service health status

## Coqui TTS Configuration

**Model Options**:

- `tts_models/en/vctk/vits` - Multi-speaker VITS (109 voices)
- `tts_models/en/ljspeech/tacotron2-DDC` - Single speaker, fast
- `tts_models/en/jenny/jenny` - High-quality neural voice

**Recommended**: `tts_models/en/vctk/vits` for variety, `tts_models/en/jenny/jenny` for quality

## Audio Output

**Format**:

- Sample Rate: 22050 Hz (Coqui default)
- Channels: 1 (mono)
- Format: PCM 16-bit or MP3 (streaming)
- Chunk Size: 2048 samples

**Streaming Strategy**:

```
Text → Phoneme Conversion → TTS Model → Audio Chunks
    → Post-processing (speed/pitch) → gRPC Stream
```

## Voice Profiles

Pre-configured voices (VCTK multi-speaker):

| Voice ID | Gender | Accent   | Description  |
| -------- | ------ | -------- | ------------ |
| `p225`   | Female | English  | Professional |
| `p226`   | Male   | English  | Deep, clear  |
| `p227`   | Male   | English  | Friendly     |
| `p228`   | Female | English  | Warm         |
| `p229`   | Female | Scottish | Distinctive  |

## Performance Optimization

1. **Model Caching**: Load model once on startup
2. **Batch Inference**: Process multiple sentences together
3. **Streaming**: Stream audio chunks as generated (don't wait for full synthesis)
4. **GPU Acceleration**: CUDA if available
5. **Audio Caching**: Cache common phrases (greetings, confirmations)

## Dependencies

- `TTS` - Coqui TTS library
- `torch` - PyTorch for model inference
- `soundfile` - Audio file I/O
- `pydub` - Audio manipulation (speed, pitch)

## Running Locally

```bash
cd services/tts-service
pip install -r requirements.txt

# Download TTS model (first run)
# Model will auto-download to ~/.local/share/tts/

python -m app.main
```

## Environment Variables

```
TTS_MODEL=tts_models/en/vctk/vits
TTS_DEVICE=cpu  # or cuda
TTS_VOICE_ID=p225
TTS_SAMPLE_RATE=22050
TTS_SPEED=1.0
```

## Benchmarks (Expected)

| Model              | Device | Real-time Factor | Quality (MOS) |
| ------------------ | ------ | ---------------- | ------------- |
| ljspeech/tacotron2 | CPU    | 0.5x             | 3.8/5.0       |
| vctk/vits          | CPU    | 1.2x             | 4.2/5.0       |
| jenny/jenny        | CPU    | 0.8x             | 4.5/5.0       |
| vctk/vits          | GPU    | 0.1x             | 4.2/5.0       |

Real-time Factor < 1.0 means faster than real-time

## Optional: ElevenLabs Integration

For cloud-based high-quality TTS:

```python
# Fallback to ElevenLabs if configured
if ELEVENLABS_API_KEY:
    response = elevenlabs.generate(
        text=text,
        voice_id=ELEVENLABS_VOICE_ID,
        model="eleven_monolingual_v1"
    )
```

## Status

**Phase**: Not yet implemented (Phase 4)
**Next Steps**:

1. Implement Coqui TTS integration
2. Build voice profile manager
3. Create audio streaming pipeline
4. Add speed/pitch control post-processing
5. Implement audio caching for common phrases
6. Add ElevenLabs fallback (optional)
