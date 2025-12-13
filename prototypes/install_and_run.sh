#!/bin/bash
# Install dependencies and run dashboard

set -e

echo "🛡️  Cyber Defense Simulator - Quick Setup & Run"
echo "================================================"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo "📥 Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No .env file found!"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env from .env.example"
    else
        echo "OPENAI_API_KEY=your_key_here" > .env
        echo "✅ Created .env file"
    fi
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your OpenAI API key!"
    echo "   OPENAI_API_KEY=sk-your-actual-key-here"
    echo ""
    read -p "Press Enter after you've added your API key, or Ctrl+C to exit..."
fi

# Check if API key is set
if grep -q "your_key_here\|your_openai_api_key_here" .env 2>/dev/null; then
    echo ""
    echo "⚠️  WARNING: You still need to add your OpenAI API key to .env"
    echo "   The dashboard will start but simulations won't work without it."
    echo ""
fi

echo ""
echo "🚀 Starting dashboard..."
echo "   Dashboard will open at: http://localhost:8501"
echo "   Press Ctrl+C to stop"
echo ""

# Run dashboard
python run_dashboard.py

