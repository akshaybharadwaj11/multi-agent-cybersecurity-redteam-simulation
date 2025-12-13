#!/usr/bin/env python3
"""
Run example_usage.py
Quick launcher for the example usage script
"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from cyber_defense_simulator.example_usage import main

if __name__ == "__main__":
    main()

