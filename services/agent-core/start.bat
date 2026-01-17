@echo off
REM Agent Core Service Startup Script for Windows

echo 🚀 Starting Agent Core Service...
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -q --upgrade pip
pip install -q -r requirements.txt

REM Check for .env file
if not exist ".env" (
    echo ⚠️  Warning: .env file not found!
    echo Creating .env from template...
    (
        echo # LLM Configuration
        echo OPENROUTER_API_KEY=your_api_key_here
        echo LLM_BASE_URL=https://openrouter.ai/api/v1
        echo LLM_MODEL=meta-llama/llama-3.1-8b-instruct
        echo LLM_TEMPERATURE=0.3
        echo LLM_MAX_TOKENS=2000
        echo.
        echo # Redis Configuration
        echo REDIS_HOST=localhost
        echo REDIS_PORT=6379
        echo REDIS_DB=1
        echo.
        echo # Service Endpoints
        echo MEMORY_SERVICE_HOST=localhost
        echo MEMORY_SERVICE_PORT=50051
        echo TOOL_EXECUTOR_HOST=localhost
        echo TOOL_EXECUTOR_PORT=50055
        echo WEB_SERVICE_HOST=localhost
        echo WEB_SERVICE_PORT=50056
        echo.
        echo # Ports
        echo GRPC_PORT=50052
        echo REST_PORT=8002
    ) > .env
    echo ✅ Created .env file - please configure your API key!
    echo.
)

echo.
echo ✅ All checks passed!
echo.
echo 🌐 Starting Agent Core REST API...
echo    - REST API: http://localhost:8002
echo    - Health: http://localhost:8002/health
echo    - API Docs: http://localhost:8002/docs
echo.
echo Press Ctrl+C to stop the service
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

REM Start the service
python src\main.py
