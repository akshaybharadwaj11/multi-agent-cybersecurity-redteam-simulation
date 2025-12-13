#!/usr/bin/env python3
"""
Run Full Simulation - All Attack Types
Runs complete Red Team vs Blue Team simulation for all attack types
"""

import sys
from pathlib import Path
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('simulation.log', mode='a')
    ],
    force=True
)

logger = logging.getLogger(__name__)

from cyber_defense_simulator.core.orchestrator import CyberDefenseOrchestrator
from cyber_defense_simulator.core.data_models import AttackType

def run_full_simulation():
    """Run complete simulation for all attack types"""
    
    print("\n" + "="*80)
    print("🚀 FULL RED TEAM vs BLUE TEAM SIMULATION")
    print("="*80)
    print("\nRunning simulation for ALL attack types:")
    print("  - Phishing")
    print("  - Credential Misuse")
    print("  - Lateral Movement")
    print("  - Data Exfiltration")
    print("  - Malware Execution")
    print("  - Privilege Escalation")
    print("\nTotal: 100 episodes (automatic training + simulation)")
    print("="*80 + "\n")
    
    # All attack types
    all_attack_types = [
        AttackType.PHISHING,
        AttackType.CREDENTIAL_MISUSE,
        AttackType.LATERAL_MOVEMENT,
        AttackType.DATA_EXFILTRATION,
        AttackType.MALWARE_EXECUTION,
        AttackType.PRIVILEGE_ESCALATION
    ]
    
    try:
        # Initialize orchestrator
        logger.info("Initializing Cyber Defense Orchestrator...")
        orchestrator = CyberDefenseOrchestrator()
        logger.info("Orchestrator initialized successfully")
        
        # Run simulation with all attack types
        logger.info("Starting full simulation: 100 episodes with all attack types")
        metrics = orchestrator.run_simulation(
            num_episodes=100,
            attack_types=all_attack_types
        )
        
        # Save results
        output_dir = Path("./results") / "full_simulation_all_attacks"
        orchestrator.save_results(output_dir)
        
        # Print summary
        print("\n" + "="*80)
        print("✅ SIMULATION COMPLETE!")
        print("="*80)
        print(f"\n📊 Final Metrics:")
        print(f"  Total Episodes: {metrics.total_episodes}")
        print(f"  Successful Defenses: {metrics.successful_defenses}")
        print(f"  Failed Defenses: {metrics.failed_defenses}")
        print(f"  False Positives: {metrics.false_positives}")
        if metrics.total_episodes > 0:
            print(f"  Success Rate: {metrics.successful_defenses / metrics.total_episodes:.2%}")
            print(f"  Detection Rate: {metrics.detection_rate:.2%}")
        print(f"  Average Reward: {metrics.average_reward:.3f}")
        print(f"  Average Time to Remediate: {metrics.average_time_to_remediate:.2f} minutes")
        
        print(f"\n💾 Results saved to: {output_dir}")
        print("\n" + "="*80)
        
        return metrics, output_dir
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}", exc_info=True)
        print(f"\n❌ Simulation failed: {e}")
        raise

if __name__ == "__main__":
    try:
        metrics, output_dir = run_full_simulation()
        print("\n✅ Full simulation completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

