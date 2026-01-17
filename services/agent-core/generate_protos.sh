#!/bin/bash
# Generate Python gRPC code from proto files

# Create output directory
mkdir -p src/generated

# Generate Python code
python -m grpc_tools.protoc \
    -I./protos \
    --python_out=./src/generated \
    --grpc_python_out=./src/generated \
    ./protos/agent.proto

# Create __init__.py
touch src/generated/__init__.py

echo "gRPC code generated successfully in src/generated/"
