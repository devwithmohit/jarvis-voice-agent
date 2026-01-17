#!/bin/bash
# Agent Core Service Startup Script

set -e

echo "🚀 Starting Agent Core Service..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
if [ -f "venv/Scripts/activate" ]; then
    # Windows
    source venv/Scripts/activate
else
    # Linux/Mac
    source venv/bin/activate
fi

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Creating .env from template..."
    cat > .env << 'EOF'
# LLM Configuration
OPENROUTER_API_KEY=your_api_key_here
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=meta-llama/llama-3.1-8b-instruct
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2000

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1

# Service Endpoints
MEMORY_SERVICE_HOST=localhost
MEMORY_SERVICE_PORT=50051
TOOL_EXECUTOR_HOST=localhost
TOOL_EXECUTOR_PORT=50055
WEB_SERVICE_HOST=localhost
WEB_SERVICE_PORT=50056

# Ports
GRPC_PORT=50052
REST_PORT=8002
EOF
    echo "✅ Created .env file - please configure your API key!"
    echo ""
fi

# Check if Redis is running
echo "🔍 Checking Redis connection..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis is running"
    else
        echo "⚠️  Redis is not running. Starting Redis..."
        if command -v redis-server &> /dev/null; then
            redis-server --daemonize yes
            sleep 2
            echo "✅ Redis started"
        else
            echo "❌ Redis not found. Please install Redis:"
            echo "   - Ubuntu/Debian: sudo apt-get install redis-server"
            echo "   - macOS: brew install redis"
            echo "   - Windows: Download from https://redis.io/download"
            exit 1
        fi
    fi
else
    echo "⚠️  redis-cli not found. Assuming Redis is running..."
fi

echo ""
echo "✅ All checks passed!"
echo ""
echo "🌐 Starting Agent Core REST API..."
echo "   - REST API: http://localhost:8002"
echo "   - Health: http://localhost:8002/health"
echo "   - API Docs: http://localhost:8002/docs"
echo ""
echo "Press Ctrl+C to stop the service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start the service
python src/main.py
