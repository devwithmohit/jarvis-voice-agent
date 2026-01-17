@echo off
REM Setup script for Voice AI Agent development environment (Windows)

echo ========================================
echo Voice AI Agent - Setup Script
echo ========================================
echo.

REM Check prerequisites
echo Checking prerequisites...

where docker >nul 2>nul
if errorlevel 1 (
    echo Error: Docker is not installed
    echo Install from: https://docs.docker.com/get-docker/
    exit /b 1
)

where docker-compose >nul 2>nul
if errorlevel 1 (
    echo Error: Docker Compose is not installed
    echo Install from: https://docs.docker.com/compose/install/
    exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
    echo Error: Python is not installed
    echo Install Python 3.11+ from: https://www.python.org/downloads/
    exit /b 1
)

echo ✓ All prerequisites satisfied
echo.

REM Create .env file
if not exist .env (
    echo Creating .env file from .env.example...
    copy .env.example .env
    echo ✓ .env created
    echo ⚠️  Please edit .env with your configuration
) else (
    echo .env file already exists
)

echo.
echo Setup complete!
echo.
echo Next steps:
echo   1. Edit .env with your configuration
echo   2. Run 'make setup' to initialize infrastructure
echo   3. Run 'make dev' to start development environment
echo.

pause
