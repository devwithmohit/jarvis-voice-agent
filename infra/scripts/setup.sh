#!/bin/bash
# Setup script for Voice AI Agent development environment

set -e

echo "========================================"
echo "Voice AI Agent - Setup Script"
echo "========================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    echo "Install from: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed"
    echo "Install from: https://docs.docker.com/compose/install/"
    exit 1
fi

if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed"
    echo "Install Python 3.11+ from: https://www.python.org/downloads/"
    exit 1
fi

python_version=$(python --version 2>&1 | sed 's/Python //;s/\..*//')
if [ "$python_version" -lt 3 ]; then
    echo "Error: Python 3.11+ is required"
    exit 1
fi

echo "✓ All prerequisites satisfied"
echo ""

# Create .env file
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "✓ .env created"
    echo "⚠️  Please edit .env with your configuration"
else
    echo ".env file already exists"
fi

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your configuration"
echo "  2. Run 'make setup' to initialize infrastructure"
echo "  3. Run 'make dev' to start development environment"
echo ""
