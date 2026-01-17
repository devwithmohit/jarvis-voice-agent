#!/bin/bash
# Verification script for Phase 1 completion
# Checks that all required files and directories exist

set -e

echo "========================================"
echo "Phase 1 Verification Script"
echo "========================================"
echo ""

ERRORS=0

check_file() {
    if [ -f "$1" ]; then
        echo "✓ $1"
    else
        echo "✗ MISSING: $1"
        ERRORS=$((ERRORS + 1))
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo "✓ $1/"
    else
        echo "✗ MISSING: $1/"
        ERRORS=$((ERRORS + 1))
    fi
}

echo "Checking core files..."
check_file "README.md"
check_file "Makefile"
check_file ".env.example"
check_file ".gitignore"
check_file "PHASE1_COMPLETE.md"

echo ""
echo "Checking infrastructure..."
check_file "infra/docker-compose.yml"
check_file "infra/init-db.sql"
check_file "infra/scripts/setup.sh"
check_file "infra/scripts/setup.bat"

echo ""
echo "Checking protocol definitions..."
check_file "shared/proto/voice.proto"
check_file "shared/proto/memory.proto"
check_file "shared/proto/agent.proto"
check_file "shared/proto/tool.proto"
check_file "shared/proto/stt_tts.proto"
check_file "shared/proto/build.sh"
check_file "shared/proto/build.bat"

echo ""
echo "Checking service directories..."
check_dir "services/api-gateway"
check_dir "services/voice-gateway"
check_dir "services/stt-service"
check_dir "services/tts-service"
check_dir "services/agent-core"
check_dir "services/memory-service"
check_dir "services/tool-executor"
check_dir "services/web-service"

echo ""
echo "Checking service scaffolding..."
check_file "services/api-gateway/requirements.txt"
check_file "services/api-gateway/README.md"
check_file "services/memory-service/requirements.txt"
check_file "services/memory-service/README.md"
check_file "services/agent-core/requirements.txt"
check_file "services/agent-core/README.md"
check_file "services/stt-service/requirements.txt"
check_file "services/stt-service/README.md"
check_file "services/tts-service/requirements.txt"
check_file "services/tts-service/README.md"
check_file "services/web-service/requirements.txt"
check_file "services/web-service/README.md"
check_file "services/voice-gateway/Cargo.toml"
check_file "services/voice-gateway/README.md"
check_file "services/tool-executor/Cargo.toml"
check_file "services/tool-executor/README.md"

echo ""
echo "Checking documentation..."
check_file "docs/architecture/README.md"
check_file "docs/security/security_model.md"

echo ""
echo "Checking test structure..."
check_file "tests/integration/test_placeholder.py"
check_file "tests/e2e/test_placeholder.py"

echo ""
echo "========================================"
if [ $ERRORS -eq 0 ]; then
    echo "✓ Phase 1 verification PASSED"
    echo "All required files and directories exist"
    echo "========================================"
    exit 0
else
    echo "✗ Phase 1 verification FAILED"
    echo "Missing $ERRORS file(s) or directory(ies)"
    echo "========================================"
    exit 1
fi
