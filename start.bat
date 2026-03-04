@echo off
REM Quick start script for News Mailer (Windows)

echo 🚀 Starting News Mailer API...
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo ⚠️  .env file not found. Copying from .env.example...
    copy .env.example .env
    echo Please edit .env with your credentials before running again.
    pause
    exit /b 1
)

REM Install dependencies
echo 📥 Installing dependencies...
pip install -q -r requirements.txt

REM Run server
echo.
echo ✅ Starting server on http://localhost:8000
echo Press Ctrl+C to stop
echo.
python news_agent_copy.py
