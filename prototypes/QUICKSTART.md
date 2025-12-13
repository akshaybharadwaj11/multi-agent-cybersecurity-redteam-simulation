# 🚀 Quick Start Guide

Get the Cyber Defense Simulator up and running in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Step 1: Setup (One-time)

```bash
# Make setup script executable
chmod +x setup.sh

# Run setup (creates venv, installs dependencies, creates .env)
./setup.sh
```

## Step 2: Configure API Key

Edit `.env` file and add your OpenAI API key:

```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
```

## Step 3: Launch Dashboard

```bash
# Activate virtual environment
source venv/bin/activate

# Launch dashboard
python run_dashboard.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`

## Step 4: Run Your First Simulation

### Option A: From Dashboard (Recommended)
1. In the dashboard sidebar, set "Number of Episodes" to 10
2. Click "Run Simulation"
3. Watch the simulation run in real-time!
4. View results, charts, and metrics

### Option B: From Command Line
```bash
# Quick test (5 episodes)
python run_simulation.py --quick-test

# Custom run
python run_simulation.py --episodes 20 --attack-types phishing
```

## What You'll See

- **Attack Generation**: Red team creates realistic attack scenarios
- **Detection**: Blue team detects incidents from telemetry
- **RAG Retrieval**: System retrieves relevant runbooks and threat intel
- **Remediation**: AI recommends response actions
- **RL Learning**: System learns optimal strategies over time
- **Visualizations**: Charts showing learning progress, success rates, action distributions

## Troubleshooting

### "OPENAI_API_KEY is required"
- Make sure you've created `.env` file
- Add your API key: `OPENAI_API_KEY=sk-...`
- Restart the application

### Import errors
- Make sure virtual environment is activated: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

### Dashboard won't start
- Check if port 8501 is available
- Try: `streamlit run cyber_defense_simulator/dashboard/dashboard.py --server.port 8502`

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore different attack types
- Adjust RL parameters in `.env` to see how learning changes
- Check out the code in `cyber_defense_simulator/` to customize agents

## Need Help?

- Check the logs in `simulation.log`
- Review error messages in the dashboard
- Ensure all dependencies are installed correctly

Enjoy simulating! 🛡️

