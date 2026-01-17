@echo off
REM Verification script for Phase 1 completion (Windows)
REM Checks that all required files and directories exist

setlocal enabledelayedexpansion
set ERRORS=0

echo ========================================
echo Phase 1 Verification Script
echo ========================================
echo.

echo Checking core files...
call :check_file "README.md"
call :check_file "Makefile"
call :check_file ".env.example"
call :check_file ".gitignore"
call :check_file "PHASE1_COMPLETE.md"

echo.
echo Checking infrastructure...
call :check_file "infra\docker-compose.yml"
call :check_file "infra\init-db.sql"
call :check_file "infra\scripts\setup.sh"
call :check_file "infra\scripts\setup.bat"

echo.
echo Checking protocol definitions...
call :check_file "shared\proto\voice.proto"
call :check_file "shared\proto\memory.proto"
call :check_file "shared\proto\agent.proto"
call :check_file "shared\proto\tool.proto"
call :check_file "shared\proto\stt_tts.proto"
call :check_file "shared\proto\build.sh"
call :check_file "shared\proto\build.bat"

echo.
echo Checking service directories...
call :check_dir "services\api-gateway"
call :check_dir "services\voice-gateway"
call :check_dir "services\stt-service"
call :check_dir "services\tts-service"
call :check_dir "services\agent-core"
call :check_dir "services\memory-service"
call :check_dir "services\tool-executor"
call :check_dir "services\web-service"

echo.
echo Checking service scaffolding...
call :check_file "services\api-gateway\requirements.txt"
call :check_file "services\api-gateway\README.md"
call :check_file "services\memory-service\requirements.txt"
call :check_file "services\memory-service\README.md"
call :check_file "services\agent-core\requirements.txt"
call :check_file "services\agent-core\README.md"
call :check_file "services\stt-service\requirements.txt"
call :check_file "services\stt-service\README.md"
call :check_file "services\tts-service\requirements.txt"
call :check_file "services\tts-service\README.md"
call :check_file "services\web-service\requirements.txt"
call :check_file "services\web-service\README.md"
call :check_file "services\voice-gateway\Cargo.toml"
call :check_file "services\voice-gateway\README.md"
call :check_file "services\tool-executor\Cargo.toml"
call :check_file "services\tool-executor\README.md"

echo.
echo Checking documentation...
call :check_file "docs\architecture\README.md"
call :check_file "docs\security\security_model.md"

echo.
echo Checking test structure...
call :check_file "tests\integration\test_placeholder.py"
call :check_file "tests\e2e\test_placeholder.py"

echo.
echo ========================================
if %ERRORS% EQU 0 (
    echo ✓ Phase 1 verification PASSED
    echo All required files and directories exist
    echo ========================================
    exit /b 0
) else (
    echo ✗ Phase 1 verification FAILED
    echo Missing %ERRORS% file^(s^) or directory^(ies^)
    echo ========================================
    exit /b 1
)

:check_file
if exist "%~1" (
    echo ✓ %~1
) else (
    echo ✗ MISSING: %~1
    set /a ERRORS+=1
)
exit /b

:check_dir
if exist "%~1\" (
    echo ✓ %~1\
) else (
    echo ✗ MISSING: %~1\
    set /a ERRORS+=1
)
exit /b
