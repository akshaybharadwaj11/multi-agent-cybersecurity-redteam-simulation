"""
Streamlit Dashboard Entry Point
Run with: streamlit run cyber_defense_simulator/dashboard/app.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import and run the dashboard
from cyber_defense_simulator.dashboard.dashboard import main

if __name__ == "__main__":
    main()

