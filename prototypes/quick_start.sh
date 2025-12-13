#!/bin/bash
echo "🛡️  Quick Start - Installing dependencies..."
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✅ Dependencies installed!"
echo ""
echo "📝 Next: Add your OpenAI API key to .env file"
echo "   echo 'OPENAI_API_KEY=sk-your-key' > .env"
echo ""
echo "🚀 Then run: python run_dashboard.py"
