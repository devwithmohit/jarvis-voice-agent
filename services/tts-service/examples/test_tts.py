"""
Example script to test TTS service
"""

import grpc
import sys
import argparse
from pathlib import Path

# Add generated proto to path
sys.path.append(str(Path(__file__).parent.parent / "generated"))

# TODO: Uncomment after proto generation
# from generated import voice_pb2, voice_pb2_grpc


def test_synthesis(text: str, output_file: str, host: str = "localhost:50053"):
    """Test speech synthesis"""
    print(f"Synthesizing: '{text}'")
    print(f"Output: {output_file}")

    # TODO: Implement after proto generation
    # channel = grpc.insecure_channel(host)
    # stub = voice_pb2_grpc.TTSServiceStub(channel)
    #
    # request = voice_pb2.SynthesisRequest(
    #     text=text,
    #     speed=1.0
    # )
    #
    # response = stub.Synthesize(request)
    #
    # # Save audio
    # with open(output_file, 'wb') as f:
    #     f.write(response.audio_data)
    #
    # print(f"Generated {len(response.audio_data)} bytes")
    # print(f"Sample rate: {response.sample_rate}Hz")
    # print(f"Duration: {response.duration_ms}ms")

    print("NOTE: Proto files not generated yet. Run generate_proto.sh first.")


def test_streaming_synthesis(
    text: str, output_file: str, host: str = "localhost:50053"
):
    """Test streaming synthesis"""
    print(f"Streaming synthesis: '{text}'")

    # TODO: Implement after proto generation
    print("NOTE: Proto files not generated yet. Run generate_proto.sh first.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test TTS service")
    parser.add_argument("--text", required=True, help="Text to synthesize")
    parser.add_argument("--output", default="output.wav", help="Output file")
    parser.add_argument("--host", default="localhost:50053", help="gRPC host")
    parser.add_argument("--stream", action="store_true", help="Use streaming")

    args = parser.parse_args()

    if args.stream:
        test_streaming_synthesis(args.text, args.output, args.host)
    else:
        test_synthesis(args.text, args.output, args.host)
