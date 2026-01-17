#!/bin/bash
# gRPC Protocol Buffer Build Script
# Generates Python and Rust code from .proto files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROTO_DIR="${SCRIPT_DIR}"
PYTHON_OUT_DIR="${SCRIPT_DIR}/../models/generated"
RUST_SERVICES=("voice-gateway" "tool-executor")

echo "==================================="
echo "Building gRPC Protocol Buffers"
echo "==================================="

# Create output directory if it doesn't exist
mkdir -p "${PYTHON_OUT_DIR}"

# Generate Python code
echo "Generating Python gRPC code..."
python -m grpc_tools.protoc \
  -I"${PROTO_DIR}" \
  --python_out="${PYTHON_OUT_DIR}" \
  --grpc_python_out="${PYTHON_OUT_DIR}" \
  --pyi_out="${PYTHON_OUT_DIR}" \
  "${PROTO_DIR}"/*.proto

# Fix Python imports (grpc_tools generates relative imports that don't work in packages)
echo "Fixing Python imports..."
find "${PYTHON_OUT_DIR}" -type f -name "*_pb2*.py" -exec sed -i 's/^import \([^ ]*\)_pb2/from . import \1_pb2/g' {} \;

# Create __init__.py for Python package
cat > "${PYTHON_OUT_DIR}/__init__.py" << 'EOF'
"""
Generated gRPC protocol buffer definitions for Voice AI Agent
Auto-generated - do not edit manually
"""

from . import voice_pb2, voice_pb2_grpc
from . import memory_pb2, memory_pb2_grpc
from . import agent_pb2, agent_pb2_grpc
from . import tool_pb2, tool_pb2_grpc
from . import stt_tts_pb2, stt_tts_pb2_grpc

__all__ = [
    'voice_pb2', 'voice_pb2_grpc',
    'memory_pb2', 'memory_pb2_grpc',
    'agent_pb2', 'agent_pb2_grpc',
    'tool_pb2', 'tool_pb2_grpc',
    'stt_tts_pb2', 'stt_tts_pb2_grpc',
]
EOF

echo "✓ Python gRPC code generated in ${PYTHON_OUT_DIR}"

# Generate Rust code
echo ""
echo "Generating Rust gRPC code..."
for service in "${RUST_SERVICES[@]}"; do
  SERVICE_DIR="${SCRIPT_DIR}/../../services/${service}"
  if [ -f "${SERVICE_DIR}/Cargo.toml" ]; then
    echo "  Building ${service}..."
    cd "${SERVICE_DIR}"
    cargo build --quiet 2>/dev/null || echo "  Note: ${service} will generate proto code on first build"
  else
    echo "  Skipping ${service} (Cargo.toml not found)"
  fi
done

cd "${SCRIPT_DIR}"

echo ""
echo "==================================="
echo "✓ Protocol buffer generation complete"
echo "==================================="
echo ""
echo "Generated files:"
echo "  Python: ${PYTHON_OUT_DIR}/*_pb2.py"
echo "  Python: ${PYTHON_OUT_DIR}/*_pb2_grpc.py"
echo "  Rust:   services/*/src/proto/*.rs (generated on build)"
echo ""
