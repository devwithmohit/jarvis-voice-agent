@echo off
REM gRPC Protocol Buffer Build Script for Windows
REM Generates Python and Rust code from .proto files

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROTO_DIR=%SCRIPT_DIR%"
set "PYTHON_OUT_DIR=%SCRIPT_DIR%\..\models\generated"

echo ===================================
echo Building gRPC Protocol Buffers
echo ===================================
echo.

REM Create output directory if it doesn't exist
if not exist "%PYTHON_OUT_DIR%" mkdir "%PYTHON_OUT_DIR%"

REM Generate Python code
echo Generating Python gRPC code...
python -m grpc_tools.protoc ^
  -I"%PROTO_DIR%" ^
  --python_out="%PYTHON_OUT_DIR%" ^
  --grpc_python_out="%PYTHON_OUT_DIR%" ^
  --pyi_out="%PYTHON_OUT_DIR%" ^
  "%PROTO_DIR%\*.proto"

if errorlevel 1 (
    echo Error: Failed to generate Python code
    echo Make sure grpcio-tools is installed: pip install grpcio-tools
    exit /b 1
)

REM Create __init__.py for Python package
echo Creating Python package __init__.py...
(
echo """
echo Generated gRPC protocol buffer definitions for Voice AI Agent
echo Auto-generated - do not edit manually
echo """
echo.
echo from . import voice_pb2, voice_pb2_grpc
echo from . import memory_pb2, memory_pb2_grpc
echo from . import agent_pb2, agent_pb2_grpc
echo from . import tool_pb2, tool_pb2_grpc
echo from . import stt_tts_pb2, stt_tts_pb2_grpc
echo.
echo __all__ = [
echo     'voice_pb2', 'voice_pb2_grpc',
echo     'memory_pb2', 'memory_pb2_grpc',
echo     'agent_pb2', 'agent_pb2_grpc',
echo     'tool_pb2', 'tool_pb2_grpc',
echo     'stt_tts_pb2', 'stt_tts_pb2_grpc',
echo ]
) > "%PYTHON_OUT_DIR%\__init__.py"

echo ✓ Python gRPC code generated in %PYTHON_OUT_DIR%
echo.

REM Generate Rust code
echo Generating Rust gRPC code...
for %%s in (voice-gateway tool-executor) do (
    set "SERVICE_DIR=%SCRIPT_DIR%\..\..\services\%%s"
    if exist "!SERVICE_DIR!\Cargo.toml" (
        echo   Building %%s...
        cd "!SERVICE_DIR!"
        cargo build --quiet 2>nul || echo   Note: %%s will generate proto code on first build
        cd "%SCRIPT_DIR%"
    ) else (
        echo   Skipping %%s ^(Cargo.toml not found^)
    )
)

echo.
echo ===================================
echo ✓ Protocol buffer generation complete
echo ===================================
echo.
echo Generated files:
echo   Python: %PYTHON_OUT_DIR%\*_pb2.py
echo   Python: %PYTHON_OUT_DIR%\*_pb2_grpc.py
echo   Rust:   services\*\src\proto\*.rs ^(generated on build^)
echo.

endlocal
