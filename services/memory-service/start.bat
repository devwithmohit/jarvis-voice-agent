@echo off
REM Quick start script for Memory Service development (Windows)

echo ================================================
echo Memory Service - Quick Start
echo ================================================
echo.

REM Check Python version
echo Checking Python version...
python --version
echo.

REM Check if venv exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
python -m pip install -q --upgrade pip
pip install -q -r requirements.txt
echo Dependencies installed
echo.

REM Create .env if it doesn't exist
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.template .env
    echo Please edit .env with your database credentials
    echo.
)

REM Create data directory
echo Creating data directories...
if not exist "data\faiss_index" mkdir data\faiss_index
echo Data directories created
echo.

REM Run tests
echo Running tests...
pytest --tb=short -q
echo.

echo ================================================
echo Setup complete!
echo ================================================
echo.
echo To start the service:
echo   python src\main.py
echo.
echo Or use the Makefile (from project root):
echo   make run-memory
echo.
echo API Documentation:
echo   http://localhost:8001/docs
echo.
echo Health Check:
echo   curl http://localhost:8001/health
echo.

pause
