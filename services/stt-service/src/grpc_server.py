import grpc
from concurrent import futures
import numpy as np
import logging
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.engines.whisper_engine import WhisperEngine
from src.engines.stream_processor import StreamProcessor
from src.utils.audio import bytes_to_audio_array, validate_audio_format
from config import settings

# Import generated proto files
# TODO: Generate these with: python -m grpc_tools.protoc -I../../protos --python_out=./generated --grpc_python_out=./generated ../../protos/voice.proto
# from generated import voice_pb2, voice_pb2_grpc

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class STTServicer:
    """gRPC servicer for Speech-to-Text"""

    def __init__(self):
        logger.info("Initializing STT servicer...")
        self.whisper = WhisperEngine()
        self.stream_processor = StreamProcessor(
            sample_rate=settings.sample_rate,
            frame_duration_ms=settings.chunk_duration_ms,
        )
        logger.info("STT servicer initialized successfully")

    def StreamTranscribe(self, request_iterator, context):
        """Streaming STT with partial results

        Args:
            request_iterator: Iterator of AudioChunk messages
            context: gRPC context

        Yields:
            TranscriptChunk messages with partial/final transcriptions
        """
        logger.info("Starting streaming transcription")

        try:

            def audio_generator():
                """Extract audio data from request iterator"""
                for chunk_msg in request_iterator:
                    yield chunk_msg.data

            # Process stream and get transcriptions
            for text, is_final, confidence in self.whisper.transcribe_stream(
                audio_generator()
            ):
                # TODO: Replace with actual proto message
                # yield voice_pb2.TranscriptChunk(
                #     text=text,
                #     is_final=is_final,
                #     confidence=confidence,
                #     language="en",
                #     timestamp_ms=int(time.time() * 1000)
                # )

                # Placeholder return for now
                logger.info(
                    f"Transcribed: '{text}' (final: {is_final}, conf: {confidence:.2f})"
                )
                yield {
                    "text": text,
                    "is_final": is_final,
                    "confidence": confidence,
                    "language": "en",
                    "timestamp_ms": int(time.time() * 1000),
                }

        except Exception as e:
            logger.error(f"Streaming transcription error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Transcription failed: {str(e)}")

    def TranscribeBatch(self, request, context):
        """Batch transcription (non-streaming)

        Args:
            request: AudioRequest message with audio data
            context: gRPC context

        Returns:
            TranscriptResult message with complete transcription
        """
        logger.info(f"Batch transcription request: {len(request.data)} bytes")

        try:
            # Convert bytes to audio array
            audio_array = bytes_to_audio_array(request.data, dtype="int16")

            # Validate audio
            if not validate_audio_format(audio_array, settings.sample_rate):
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("Invalid audio format")
                return None

            # Transcribe
            text, confidence = self.whisper.transcribe_audio(
                audio_array, language=request.language or "en"
            )

            # TODO: Replace with actual proto message
            # return voice_pb2.TranscriptResult(
            #     text=text,
            #     confidence=confidence,
            #     language=request.language or "en",
            #     segments=[]  # TODO: Extract segments from Whisper
            # )

            # Placeholder return
            logger.info(
                f"Batch transcription complete: '{text}' (conf: {confidence:.2f})"
            )
            return {
                "text": text,
                "confidence": confidence,
                "language": request.language or "en",
                "segments": [],
            }

        except Exception as e:
            logger.error(f"Batch transcription error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Transcription failed: {str(e)}")
            return None


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
    # voice_pb2_grpc.add_STTServiceServicer_to_server(STTServicer(), server)

    servicer = STTServicer()

    server.add_insecure_port(f"{settings.grpc_host}:{settings.grpc_port}")
    server.start()

    logger.info(f"STT gRPC server started on {settings.grpc_host}:{settings.grpc_port}")
    logger.info(f"Using Whisper model: {settings.whisper_model}")
    logger.info(f"Device: {settings.device}, Compute type: {settings.compute_type}")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down STT server...")
        server.stop(grace=5)


if __name__ == "__main__":
    serve()
