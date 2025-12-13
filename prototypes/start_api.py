#!/usr/bin/env python3
"""
Start the API server for Cyber Defense Simulator
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from cyber_defense_simulator.api.server import app

if __name__ == "__main__":
    print("🚀 Starting Cyber Defense Simulator API Server...")
    print("📍 API will be available at: http://localhost:8000")
    print("📚 API docs at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

