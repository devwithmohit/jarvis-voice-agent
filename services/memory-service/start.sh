#!/usr/bin/env bash
# Quick start script for Memory Service development

set -e

echo "================================================"
echo "Memory Service - Quick Start"
echo "================================================"
echo ""

# Check Python version
echo "✓ Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "  Python version: $python_version"

# Check PostgreSQL
echo ""
echo "✓ Checking PostgreSQL connection..."
if command -v psql &> /dev/null; then
    echo "  PostgreSQL client found"
else
    echo "  ⚠ PostgreSQL client not found. Please install PostgreSQL."
fi

# Check Redis
echo ""
echo "✓ Checking Redis connection..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "  Redis is running"
    else
        echo "  ⚠ Redis is not running. Please start Redis."
    fi
else
    echo "  ⚠ Redis client not found. Please install Redis."
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "✓ Creating virtual environment..."
    python -m venv venv
    echo "  Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "✓ Activating virtual environment..."
source venv/bin/activate || source venv/Scripts/activate

# Install dependencies
echo ""
echo "✓ Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "  Dependencies installed"

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "✓ Creating .env file from template..."
    cp .env.template .env
    echo "  ⚠ Please edit .env with your database credentials"
fi

# Create data directory
echo ""
echo "✓ Creating data directories..."
mkdir -p data/faiss_index
echo "  Data directories created"

# Run tests
echo ""
echo "✓ Running tests..."
if pytest --tb=short -q; then
    echo "  All tests passed"
else
    echo "  ⚠ Some tests failed"
fi

echo ""
echo "================================================"
echo "Setup complete!"
echo "================================================"
echo ""
echo "To start the service:"
echo "  python src/main.py"
echo ""
echo "Or use the Makefile (from project root):"
echo "  make run-memory"
echo ""
echo "API Documentation:"
echo "  http://localhost:8001/docs"
echo ""
echo "Health Check:"
echo "  curl http://localhost:8001/health"
echo ""
