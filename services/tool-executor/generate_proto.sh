#!/bin/bash
# Generate Rust gRPC code from proto files

set -e

echo "Generating Rust gRPC code from tool.proto..."

# Proto file location
PROTO_DIR="../../protos"
PROTO_FILE="tool.proto"

# Output directory
OUT_DIR="src/generated"

# Create output directory
mkdir -p "$OUT_DIR"

# Generate Rust code using tonic-build
# Note: This is handled by build.rs at compile time
# This script is for reference/manual generation

echo "Proto generation is handled by build.rs during compilation"
echo "Run 'cargo build' to generate proto code"
