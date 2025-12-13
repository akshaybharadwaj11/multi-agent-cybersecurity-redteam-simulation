#!/bin/bash
# Setup script for Cyber Defense Simulator

echo "🛡️  Setting up Cyber Defense Simulator..."
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "⚠️  Please edit .env and add your OPENAI_API_KEY"
    else
        echo "OPENAI_API_KEY=your_key_here" > .env
        echo "⚠️  Please edit .env and add your OPENAI_API_KEY"
    fi
else
    echo "✓ .env file already exists"
fi

# Create necessary directories
echo "Creating data directories..."
mkdir -p data/vector_store
mkdir -p data/runbooks
mkdir -p data/mitre_attack
mkdir -p data/cve_data
mkdir -p data/logs
mkdir -p results

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your OPENAI_API_KEY"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run dashboard: python run_dashboard.py"
echo "   OR"
echo "   Run simulation: python run_simulation.py --episodes 10"

