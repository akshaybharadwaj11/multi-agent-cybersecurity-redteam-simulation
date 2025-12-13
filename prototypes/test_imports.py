#!/usr/bin/env python3
"""
Test that all imports work correctly
"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    
    try:
        from cyber_defense_simulator.core.config import Config
        print("✓ Config")
    except Exception as e:
        print(f"✗ Config: {e}")
        return False
    
    try:
        from cyber_defense_simulator.core.data_models import AttackType, RemediationAction
        print("✓ Data Models")
    except Exception as e:
        print(f"✗ Data Models: {e}")
        return False
    
    try:
        from cyber_defense_simulator.agents.red_team_agent import RedTeamAgent
        print("✓ Red Team Agent")
    except Exception as e:
        print(f"✗ Red Team Agent: {e}")
        return False
    
    try:
        from cyber_defense_simulator.agents.detection_agent import DetectionAgent
        print("✓ Detection Agent")
    except Exception as e:
        print(f"✗ Detection Agent: {e}")
        return False
    
    try:
        from cyber_defense_simulator.rag.vector_store import VectorStore
        print("✓ Vector Store")
    except Exception as e:
        print(f"✗ Vector Store: {e}")
        return False
    
    try:
        from cyber_defense_simulator.rl.contextual_bandit import ContextualBandit
        print("✓ Contextual Bandit")
    except Exception as e:
        print(f"✗ Contextual Bandit: {e}")
        return False
    
    try:
        from cyber_defense_simulator.core.orchestrator import CyberDefenseOrchestrator
        print("✓ Orchestrator")
    except Exception as e:
        print(f"✗ Orchestrator: {e}")
        return False
    
    print("\n✅ All imports successful!")
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)

