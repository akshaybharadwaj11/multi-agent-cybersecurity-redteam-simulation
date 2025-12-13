# 🔌 API Setup Guide

## Overview

The project now uses a **backend API** architecture:
- **Backend API** (FastAPI) - Handles simulation execution
- **Frontend Dashboard** (Streamlit) - Calls API instead of direct orchestrator

## Architecture

```
┌─────────────────┐         HTTP/REST         ┌─────────────────┐
│                 │ ────────────────────────> │                 │
│  Streamlit UI   │                           │  FastAPI Server │
│   (Frontend)    │ <──────────────────────── │   (Backend)     │
│                 │         JSON Response     │                 │
└─────────────────┘                           └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   Orchestrator  │
                                              │   (Simulation)  │
                                              └─────────────────┘
```

## Quick Start

### Option 1: Start Both Together (Recommended)
```bash
./start_api_and_dashboard.sh
```

This will:
1. Start API server on port 8000
2. Wait for API to be ready
3. Start dashboard on port 8501

### Option 2: Start Separately

**Terminal 1 - API Server:**
```bash
python3 start_api.py
# API available at: http://localhost:8000
# API docs at: http://localhost:8000/docs
```

**Terminal 2 - Dashboard:**
```bash
python3 start_dashboard.py
# Dashboard available at: http://localhost:8501
```

## API Endpoints

### Health Check
```
GET /health
```

### Run Simulation
```
POST /api/simulations/run
Body: {
    "num_episodes": 20,
    "attack_types": ["phishing", "credential_misuse"],
    "simulation_mode": "Red Team vs Blue Team"
}
```

### Get Simulation Status
```
GET /api/simulations/{simulation_id}/status
```

### Get Simulation Results
```
GET /api/simulations/{simulation_id}/results
```

### Load Results from Directory
```
POST /api/results/load
Body: {
    "results_dir": "./results/sim_20231212_120000"
}
```

## API Documentation

When the API server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Fallback Mode

If the API is not available, the dashboard will:
1. Try to connect to API
2. If API unavailable, fall back to **direct mode** (calls orchestrator directly)
3. Show warning message

## Benefits

✅ **Separation of Concerns** - Backend and frontend separated  
✅ **Scalability** - API can be deployed separately  
✅ **Testing** - API can be tested independently  
✅ **Multiple Clients** - Other clients can use the API  
✅ **Better Error Handling** - Centralized error handling  

## Troubleshooting

### API Not Starting
```bash
# Check if port 8000 is in use
lsof -i :8000

# Install dependencies
pip install -r requirements.txt
```

### Dashboard Can't Connect
- Make sure API server is running
- Check API health: `curl http://localhost:8000/health`
- Dashboard will fall back to direct mode if API unavailable

### API Timeout
- Simulations can take time
- API has 5-minute timeout
- Check API logs in `api.log`

## Development

### Run API in Development Mode
```bash
python3 start_api.py
# Auto-reloads on code changes
```

### Test API Directly
```bash
# Health check
curl http://localhost:8000/health

# Run simulation
curl -X POST http://localhost:8000/api/simulations/run \
  -H "Content-Type: application/json" \
  -d '{"num_episodes": 5, "simulation_mode": "Red Team vs Blue Team"}'
```

## Production Deployment

For production:
1. Use a production ASGI server (e.g., Gunicorn with Uvicorn workers)
2. Set up proper CORS origins
3. Add authentication/authorization
4. Use environment variables for configuration
5. Set up logging and monitoring

Example production command:
```bash
gunicorn cyber_defense_simulator.api.server:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

