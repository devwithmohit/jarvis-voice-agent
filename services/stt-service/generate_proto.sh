#!/bin/bash

# Generate Python gRPC code from proto files

set -e

PROTO_DIR="../../protos"
OUTPUT_DIR="./generated"

echo "Generating Python gRPC code..."

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Generate Python code
python -m grpc_tools.protoc \
    -I"$PROTO_DIR" \
    --python_out="$OUTPUT_DIR" \
    --grpc_python_out="$OUTPUT_DIR" \
    "$PROTO_DIR/voice.proto"

# Create __init__.py
touch "$OUTPUT_DIR/__init__.py"

echo "✓ Generated Python gRPC code in $OUTPUT_DIR"
echo ""
echo "Generated files:"
ls -la "$OUTPUT_DIR"
