# 🎯 Getting Started - Cyber Defense Simulator

## What This Project Does

This is a **multi-agent cybersecurity simulation system** that:

1. **Red Team Agent**: Generates realistic cyberattack scenarios
2. **Blue Team Detection**: Uses AI to detect incidents from logs
3. **RAG System**: Retrieves security runbooks and threat intelligence
4. **Remediation Agent**: Recommends response actions
5. **RL Agent**: Learns optimal defense strategies over time
6. **Dashboard**: Beautiful UI to visualize everything

## Quick Start (3 Steps)

### 1. Setup
```bash
chmod +x setup.sh
./setup.sh
```

### 2. Add API Key
Edit `.env` and add:
```
OPENAI_API_KEY=sk-your-key-here
```

### 3. Launch Dashboard
```bash
source venv/bin/activate
python run_dashboard.py
```

That's it! The dashboard opens at `http://localhost:8501`

## What You Can Do

### Run Simulations
- Click "Run Simulation" in the dashboard
- Choose number of episodes (5-100)
- Select attack types or use all
- Watch real-time progress
- View results and charts

### View Results
- Success rates by attack type
- Learning progress over time
- Action distribution charts
- Episode-by-episode details
- Export data as CSV/JSON

### Customize
- Edit `.env` to change RL parameters
- Modify agents in `cyber_defense_simulator/agents/`
- Adjust reward functions in `rl/reward_calculator.py`
- Add new attack types in `core/data_models.py`

## Project Structure

```
cyber_defense_simulator/
├── agents/              # AI agents (Red Team, Detection, RAG, Remediation)
├── core/                # Core logic (orchestrator, config, data models)
├── rag/                 # RAG system (vector store, embeddings, knowledge base)
├── rl/                  # Reinforcement learning (bandit, rewards)
├── simulation/          # Attack simulation (telemetry generation)
├── dashboard/           # Streamlit UI
└── tests/               # Test suite

run_dashboard.py         # Launch dashboard
run_simulation.py        # Run from command line
setup.sh                 # Setup script
.env                     # Configuration (create from .env.example)
```

## Key Features

✅ **Realistic Attacks**: MITRE ATT&CK-based scenarios  
✅ **AI Detection**: LLM-powered incident analysis  
✅ **RAG Integration**: Context-aware decision making  
✅ **RL Learning**: Adaptive defense strategies  
✅ **Beautiful UI**: Interactive dashboard with charts  
✅ **Explainable**: Full audit trail of decisions  

## Troubleshooting

**"OPENAI_API_KEY is required"**
- Check `.env` file exists
- Verify API key is set correctly
- Restart application

**Import errors**
- Activate venv: `source venv/bin/activate`
- Reinstall: `pip install -r requirements.txt`

**Dashboard won't start**
- Check port 8501 is free
- Try different port: `streamlit run ... --server.port 8502`

**Slow performance**
- Reduce episodes for testing
- Use `gpt-4o-mini` (faster/cheaper) instead of `gpt-4`
- Check API rate limits

## Next Steps

1. **Run your first simulation** (10 episodes)
2. **Explore the dashboard** charts and metrics
3. **Read the code** to understand how agents work
4. **Customize** attack types or RL parameters
5. **Experiment** with different configurations

## Support

- Check `simulation.log` for detailed logs
- Review error messages in dashboard
- See `README.md` for full documentation
- Check `QUICKSTART.md` for step-by-step guide

Happy simulating! 🛡️🤖

