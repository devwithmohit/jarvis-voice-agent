import grpc
from concurrent import futures
import logging
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.engines.coqui_engine import CoquiEngine
from src.cache.audio_cache import AudioCache
from config import settings

# Import generated proto files
# TODO: Generate these with: python -m grpc_tools.protoc -I../../protos --python_out=./generated --grpc_python_out=./generated ../../protos/voice.proto
# from generated import voice_pb2, voice_pb2_grpc

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TTSServicer:
    """gRPC servicer for Text-to-Speech"""

    def __init__(self):
        logger.info("Initializing TTS servicer...")
        self.engine = CoquiEngine()
        self.cache = AudioCache()
        logger.info("TTS servicer initialized successfully")

    def Synthesize(self, request, context):
        """Generate speech from text (batch)

        Args:
            request: SynthesisRequest message
            context: gRPC context

        Returns:
            AudioResponse message with complete audio
        """
        logger.info(f"Synthesis request: '{request.text[:50]}...'")

        try:
            # Extract parameters
            text = request.text
            voice_id = getattr(request, "voice_id", "")
            speed = getattr(request, "speed", 1.0)

            # Validate parameters
            if not text or not text.strip():
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("Text cannot be empty")
                return None

            if speed < 0.5 or speed > 2.0:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("Speed must be between 0.5 and 2.0")
                return None

            # Check cache first
            cached_audio = self.cache.get(text, voice_id, speed)
            if cached_audio:
                logger.info("Returning cached audio")
                # TODO: Replace with actual proto message
                # return voice_pb2.AudioResponse(
                #     audio_data=cached_audio,
                #     sample_rate=settings.sample_rate,
                #     format=settings.audio_format,
                #     duration_ms=int(len(cached_audio) / settings.sample_rate * 1000)
                # )
                return {
                    "audio_data": cached_audio,
                    "sample_rate": settings.sample_rate,
                    "format": settings.audio_format,
                    "duration_ms": int(
                        len(cached_audio) / (settings.sample_rate * 2) * 1000
                    ),
                }

            # Generate audio
            audio_bytes = self.engine.synthesize(text, voice_id, speed)

            # Cache result
            self.cache.set(text, audio_bytes, voice_id, speed)

            # TODO: Replace with actual proto message
            # return voice_pb2.AudioResponse(
            #     audio_data=audio_bytes,
            #     sample_rate=settings.sample_rate,
            #     format=settings.audio_format,
            #     duration_ms=int(len(audio_bytes) / settings.sample_rate * 1000)
            # )

            logger.info(f"Synthesis complete: {len(audio_bytes)} bytes")
            return {
                "audio_data": audio_bytes,
                "sample_rate": settings.sample_rate,
                "format": settings.audio_format,
                "duration_ms": int(
                    len(audio_bytes) / (settings.sample_rate * 2) * 1000
                ),
            }

        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Synthesis failed: {str(e)}")
            return None

    def SynthesizeStream(self, request, context):
        """Stream audio for long text

        Args:
            request: SynthesisRequest message
            context: gRPC context

        Yields:
            AudioChunk messages with audio data
        """
        logger.info(f"Stream synthesis request: '{request.text[:50]}...'")

        try:
            # Extract parameters
            text = request.text
            voice_id = getattr(request, "voice_id", "")
            speed = getattr(request, "speed", 1.0)

            # Validate parameters
            if not text or not text.strip():
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("Text cannot be empty")
                return

            # Stream audio chunks
            for audio_chunk in self.engine.synthesize_stream(text, voice_id, speed):
                # TODO: Replace with actual proto message
                # yield voice_pb2.AudioChunk(
                #     data=audio_chunk,
                #     sample_rate=settings.sample_rate,
                #     format=settings.audio_format
                # )

                logger.debug(f"Yielding chunk: {len(audio_chunk)} bytes")
                yield {
                    "data": audio_chunk,
                    "sample_rate": settings.sample_rate,
                    "format": settings.audio_format,
                }

        except Exception as e:
            logger.error(f"Stream synthesis error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Synthesis failed: {str(e)}")


def serve():
    """Start the gRPC server"""
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=4),
        options=[
            ("grpc.max_send_message_length", 50 * 1024 * 1024),  # 50MB
            ("grpc.max_receive_message_length", 50 * 1024 * 1024),  # 50MB
        ],
    )

    # TODO: Add servicer to server after proto generation
    # voice_pb2_grpc.add_TTSServiceServicer_to_server(TTSServicer(), server)

    servicer = TTSServicer()

    server.add_insecure_port(f"{settings.grpc_host}:{settings.grpc_port}")
    server.start()

    logger.info(f"TTS gRPC server started on {settings.grpc_host}:{settings.grpc_port}")
    logger.info(f"Using TTS engine: {settings.tts_engine}")
    logger.info(f"Coqui model: {settings.coqui_model}")
    logger.info(f"Cache enabled: {settings.enable_cache}")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down TTS server...")
        server.stop(grace=5)


if __name__ == "__main__":
    serve()
