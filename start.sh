#!/bin/bash
# Quick start script for News Mailer

echo "🚀 Starting News Mailer API..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your credentials before running again."
    exit 1
fi

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Run server
echo ""
echo "✅ Starting server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""
python news_agent_copy.py
