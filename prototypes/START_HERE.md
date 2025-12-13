# 🚀 START HERE - Get Running in 5 Minutes!

## Step 1: Install Dependencies

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 2: Add Your OpenAI API Key

Create a `.env` file in the project root:

```bash
# Copy the example
cp .env.example .env

# Edit .env and add your key
# OPENAI_API_KEY=sk-your-actual-key-here
```

Or create it manually:
```bash
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

## Step 3: Test It Works

```bash
# Test imports
python test_imports.py

# Should see: ✅ All imports successful!
```

## Step 4: Run Example Usage (Easiest Way!)

```bash
# Activate venv if not already
source venv/bin/activate

# Run example usage
python run_example.py

# Choose option 3 for a single episode walkthrough
# OR choose option 1 for a quick 10-episode simulation
```

## Step 5: Launch Dashboard (Best Experience!)

```bash
# Activate venv
source venv/bin/activate

# Launch dashboard
python run_dashboard.py

# Browser opens automatically at http://localhost:8501
# Click "Run Simulation" in the sidebar!
```

## What You'll See

### Example Usage Output:
- 🔴 Red Team generates attack scenarios
- 📊 Telemetry logs generated
- 🔵 Detection agent finds incidents
- 📚 RAG retrieves runbooks
- 💡 Remediation recommends actions
- 🤖 RL agent selects best action
- ⚖️ Outcomes and rewards calculated

### Dashboard Shows:
- Real-time simulation progress
- Success rates and metrics
- Learning progress charts
- Action distribution graphs
- Episode-by-episode details
- Exportable results

## Troubleshooting

**"No module named 'sentence_transformers'"**
```bash
pip install sentence-transformers
```

**"OPENAI_API_KEY is required"**
- Check `.env` file exists
- Verify API key is set correctly
- Restart the application

**Import errors**
- Make sure you're in the project root directory
- Activate virtual environment: `source venv/bin/activate`
- Reinstall: `pip install -r requirements.txt`

**Dashboard won't start**
- Check port 8501 is free
- Try: `streamlit run cyber_defense_simulator/dashboard/dashboard.py --server.port 8502`

## Quick Commands Reference

```bash
# Setup
./setup.sh

# Test
python test_imports.py

# Examples
python run_example.py

# Dashboard
python run_dashboard.py

# Simulation
python run_simulation.py --episodes 10
```

## Next Steps

1. ✅ Run `python run_example.py` and choose option 3
2. ✅ Launch dashboard and run a simulation
3. ✅ Explore the code in `cyber_defense_simulator/`
4. ✅ Customize attack types or RL parameters
5. ✅ Read full README.md for details

**You're ready to go! 🎉**

