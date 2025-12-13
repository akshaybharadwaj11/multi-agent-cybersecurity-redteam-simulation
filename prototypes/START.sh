#!/bin/bash
# Complete startup script - installs everything and starts dashboard

set -e

echo "🛡️  Cyber Defense Simulator - Complete Setup"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found!${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python found: $(python3 --version)"

# Create venv if needed
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate venv
echo -e "${GREEN}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}⬆️  Upgrading pip...${NC}"
pip install --upgrade pip --quiet

# Install dependencies
echo -e "${YELLOW}📥 Installing dependencies (this may take a few minutes)...${NC}"
pip install -r requirements.txt --quiet

echo -e "${GREEN}✅ Dependencies installed!${NC}"

# Check/create .env
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}📝 Creating .env file...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        cat > .env << EOF
OPENAI_API_KEY=your_key_here
LLM_MODEL=gpt-4o-mini
EOF
    fi
    echo -e "${YELLOW}⚠️  Please edit .env and add your OpenAI API key!${NC}"
    echo -e "${YELLOW}   OPENAI_API_KEY=sk-your-actual-key-here${NC}"
    echo ""
    read -p "Press Enter to continue (you can add the key later)..."
fi

# Check API key
if grep -q "your_key_here\|your_openai_api_key_here" .env 2>/dev/null; then
    echo -e "${YELLOW}⚠️  WARNING: Using placeholder API key. Simulations won't work until you add a real key.${NC}"
fi

echo ""
echo -e "${GREEN}🚀 Starting dashboard...${NC}"
echo -e "${GREEN}   URL: http://localhost:8501${NC}"
echo -e "${YELLOW}   Press Ctrl+C to stop${NC}"
echo ""

# Start dashboard
python3 start_dashboard.py

