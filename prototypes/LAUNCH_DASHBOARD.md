# 🚀 Launch Dashboard - Quick Fix

## The Problem
The dashboard at `localhost:8501` isn't running because dependencies aren't installed.

## Quick Solution (Choose One)

### Option 1: Automated Setup & Launch (Easiest!)
```bash
./install_and_run.sh
```
This will:
- Create virtual environment
- Install all dependencies
- Create .env file if needed
- Launch the dashboard

### Option 2: Manual Setup

**Step 1: Install Dependencies**
```bash
# Create virtual environment (if not exists)
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install everything
pip install --upgrade pip
pip install -r requirements.txt
```

**Step 2: Add API Key**
```bash
# Create .env file
echo "OPENAI_API_KEY=sk-your-key-here" > .env

# OR edit .env.example and copy it
cp .env.example .env
# Then edit .env and add your key
```

**Step 3: Launch Dashboard**
```bash
# Make sure venv is activated
source venv/bin/activate

# Run dashboard
python run_dashboard.py

# OR directly with streamlit
streamlit run cyber_defense_simulator/dashboard/dashboard.py
```

## Verify It's Working

After running, you should see:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

Then open your browser to `http://localhost:8501`

## Troubleshooting

**"ModuleNotFoundError: No module named 'sentence_transformers'"**
- Dependencies aren't installed
- Run: `pip install -r requirements.txt`

**"Port 8501 already in use"**
- Another Streamlit app is running
- Kill it: `pkill -f streamlit`
- Or use different port: `streamlit run ... --server.port 8502`

**"OPENAI_API_KEY is required"**
- Add your API key to `.env` file
- Format: `OPENAI_API_KEY=sk-your-key-here`

**Dashboard opens but shows errors**
- Check that all dependencies are installed
- Check `.env` file has valid API key
- Look at terminal for error messages

## Quick Test

```bash
# Test imports work
python test_imports.py

# Should see: ✅ All imports successful!
```

## Need Help?

1. Make sure virtual environment is activated
2. Check all dependencies installed: `pip list | grep streamlit`
3. Verify .env file exists and has API key
4. Check terminal output for specific errors

