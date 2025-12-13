# 🚀 HOW TO RUN - Complete Guide

## ✅ Dashboard is NOW RUNNING!

The dashboard should be accessible at: **http://localhost:8501**

## Quick Start (3 Options)

### Option 1: Use START.sh (Easiest - Does Everything!)
```bash
./START.sh
```
This script:
- ✅ Creates virtual environment
- ✅ Installs all dependencies
- ✅ Creates .env file
- ✅ Starts the dashboard

### Option 2: Use start_dashboard.py (Smart Launcher)
```bash
python3 start_dashboard.py
```
This Python script:
- ✅ Checks and installs missing dependencies
- ✅ Creates .env if needed
- ✅ Starts dashboard

### Option 3: Manual Start
```bash
# 1. Activate venv
source venv/bin/activate

# 2. Install deps (if not done)
pip install -r requirements.txt

# 3. Start dashboard
python3 start_dashboard.py
# OR
streamlit run cyber_defense_simulator/dashboard/dashboard.py
```

## What You'll See

### Dashboard Features:
1. **Load Results** - View previous simulation results
2. **Run Simulation** - Start new simulations from the UI
3. **Real-time Progress** - Watch simulations run
4. **Charts & Metrics** - Visualize performance
5. **Export Data** - Download results as CSV/JSON

### Example Usage:
```bash
# Run example scripts
python3 run_example.py

# Choose from menu:
# 1. Basic Simulation (10 episodes)
# 2. Specific Attack Types
# 3. Single Episode Walkthrough ⭐ (Best for first run!)
# 4. Custom RL Configuration
# 5. Analyze Results
# 6. Batch Experiments
```

## Configuration

### Add Your OpenAI API Key:
```bash
# Edit .env file
nano .env
# OR
open .env

# Add your key:
OPENAI_API_KEY=sk-your-actual-key-here
```

### Without API Key:
- Dashboard will start
- But simulations won't work
- You'll see helpful error messages

## Troubleshooting

### Dashboard Not Starting?
```bash
# Check if port 8501 is in use
lsof -i :8501

# Kill existing streamlit
pkill -f streamlit

# Try different port
streamlit run cyber_defense_simulator/dashboard/dashboard.py --server.port 8502
```

### Import Errors?
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Test imports
python3 test_imports.py
```

### Missing Dependencies?
```bash
# Install everything
pip install streamlit sentence-transformers chromadb crewai langchain langchain-openai langchain-community openai pandas pydantic python-dotenv plotly numpy scipy
```

## Verify Everything Works

```bash
# Test 1: Check imports
python3 test_imports.py
# Should see: ✅ All imports successful!

# Test 2: Check dashboard
curl http://localhost:8501
# Should get HTML response

# Test 3: Run example
python3 run_example.py
# Choose option 3 for single episode
```

## Next Steps

1. ✅ **Dashboard is running** - Open http://localhost:8501
2. 📝 **Add API key** - Edit .env file
3. 🎮 **Run simulation** - Click "Run Simulation" in dashboard
4. 📊 **View results** - See charts and metrics
5. 🔬 **Experiment** - Try different attack types and configurations

## File Structure

```
├── START.sh                    # ⭐ Complete setup & start script
├── start_dashboard.py          # Smart dashboard launcher
├── run_dashboard.py            # Simple dashboard launcher
├── run_example.py              # Example usage launcher
├── run_simulation.py           # CLI simulation launcher
├── test_imports.py             # Test script
├── .env                        # Configuration (add your API key here)
├── requirements.txt            # Dependencies
└── cyber_defense_simulator/    # Main package
    ├── dashboard/              # Streamlit UI
    ├── agents/                 # AI agents
    ├── core/                   # Core logic
    ├── rag/                    # RAG system
    ├── rl/                     # Reinforcement learning
    └── simulation/             # Attack simulation
```

## Success Indicators

✅ Dashboard loads at http://localhost:8501  
✅ No import errors in terminal  
✅ Can click "Run Simulation" button  
✅ See simulation progress  
✅ View results and charts  

**You're all set! 🎉**

