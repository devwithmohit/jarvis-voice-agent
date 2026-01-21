#!/bin/bash
# Generate Python gRPC code from proto files

set -e

echo "Generating Python gRPC code from web.proto..."

# Proto file location
PROTO_DIR="../../protos"
PROTO_FILE="web.proto"

# Output directory
OUT_DIR="src/generated"

# Create output directory
mkdir -p "$OUT_DIR"

# Generate Python code
python -m grpc_tools.protoc \
    -I"$PROTO_DIR" \
    --python_out="$OUT_DIR" \
    --grpc_python_out="$OUT_DIR" \
    "$PROTO_DIR/$PROTO_FILE"

# Create __init__.py
touch "$OUT_DIR/__init__.py"

echo "Generated Python gRPC code in $OUT_DIR"
echo "Files created:"
echo "  - web_pb2.py"
echo "  - web_pb2_grpc.py"
