"""
Example script to test STT service
"""

import grpc
import sys
import wave
import argparse
from pathlib import Path

# Add generated proto to path
sys.path.append(str(Path(__file__).parent.parent / "generated"))

# TODO: Uncomment after proto generation
# from generated import voice_pb2, voice_pb2_grpc


def test_batch_transcription(audio_file: str, host: str = "localhost:50052"):
    """Test batch transcription"""
    print(f"Testing batch transcription: {audio_file}")

    # Read audio file
    with open(audio_file, "rb") as f:
        audio_data = f.read()

    print(f"Audio size: {len(audio_data)} bytes")

    # TODO: Implement after proto generation
    # channel = grpc.insecure_channel(host)
    # stub = voice_pb2_grpc.STTServiceStub(channel)
    #
    # request = voice_pb2.AudioRequest(
    #     data=audio_data,
    #     language="en",
    #     enable_vad=True
    # )
    #
    # result = stub.TranscribeBatch(request)
    # print(f"Transcript: {result.text}")
    # print(f"Confidence: {result.confidence}")

    print("NOTE: Proto files not generated yet. Run generate_proto.sh first.")


def test_streaming_transcription(audio_file: str, host: str = "localhost:50052"):
    """Test streaming transcription"""
    print(f"Testing streaming transcription: {audio_file}")

    # TODO: Implement after proto generation
    print("NOTE: Proto files not generated yet. Run generate_proto.sh first.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test STT service")
    parser.add_argument("--audio", required=True, help="Audio file path (WAV)")
    parser.add_argument("--host", default="localhost:50052", help="gRPC host")
    parser.add_argument("--stream", action="store_true", help="Use streaming")

    args = parser.parse_args()

    if args.stream:
        test_streaming_transcription(args.audio, args.host)
    else:
        test_batch_transcription(args.audio, args.host)
