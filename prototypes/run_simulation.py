#!/usr/bin/env python3
"""
Quick launcher for the Cyber Defense Simulator
Run with: python run_simulation.py
"""

import sys
import os
from pathlib import Path

# Add to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from cyber_defense_simulator.main_entry import main

if __name__ == "__main__":
    sys.exit(main())

