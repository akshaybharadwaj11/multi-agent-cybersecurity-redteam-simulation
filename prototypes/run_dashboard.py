#!/usr/bin/env python3
"""
Quick launcher for the Cyber Defense Simulator Dashboard
Run with: python run_dashboard.py
"""

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    # Get the dashboard file path
    dashboard_path = Path(__file__).parent / "cyber_defense_simulator" / "dashboard" / "dashboard.py"
    
    if not dashboard_path.exists():
        print(f"Error: Dashboard file not found at {dashboard_path}")
        sys.exit(1)
    
    # Run streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", str(dashboard_path)
    ])

