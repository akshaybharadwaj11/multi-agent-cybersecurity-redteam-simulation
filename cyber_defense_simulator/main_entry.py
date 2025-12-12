"""
Main Entry Point for Cyber Defense Simulator
Run this script to start the simulation
"""

import logging
import argparse
from pathlib import Path
from datetime import datetime
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('simulation.log')
    ]
)

logger = logging.getLogger(__name__)

from core.orchestrator import CyberDefenseOrchestrator
from core.data_models import AttackType
from core.config import Config


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Adaptive Red Team vs Blue Team Security Simulator"
    )
    
    parser.add_argument(
        "--episodes",
        type=int,
        default=Config.NUM_EPISODES,
        help="Number of simulation episodes to run"
    )
    
    parser.add_argument(
        "--attack-types",
        nargs="+",
        choices=[at.value for at in AttackType],
        help="Specific attack types to simulate"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./results",
        help="Directory to save results"
    )
    
    parser.add_argument(
        "--no-kb-init",
        action="store_true",
        help="Skip knowledge base initialization (use existing)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--quick-test",
        action="store_true",
        help="Run quick test with 5 episodes"
    )
    
    return parser.parse_args()


def main():
    """Main execution function"""
    args = parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Print banner
    print_banner()
    
    # Parse attack types
    attack_types = None
    if args.attack_types:
        attack_types = [AttackType(at) for at in args.attack_types]
    
    # Quick test mode
    if args.quick_test:
        args.episodes = 5
        logger.info("Running in quick test mode (5 episodes)")
    
    try:
        # Initialize orchestrator
        logger.info("Initializing Cyber Defense Orchestrator...")
        orchestrator = CyberDefenseOrchestrator(
            initialize_kb=not args.no_kb_init
        )
        
        # Run simulation
        logger.info(f"Starting simulation with {args.episodes} episodes")
        if attack_types:
            logger.info(f"Attack types: {[at.value for at in attack_types]}")
        
        metrics = orchestrator.run_simulation(
            num_episodes=args.episodes,
            attack_types=attack_types
        )
        
        # Save results
        output_dir = Path(args.output_dir) / datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info(f"Saving results to {output_dir}")
        orchestrator.save_results(output_dir)
        
        # Print summary
        print_summary(metrics, orchestrator)
        
        logger.info("\n✅ Simulation completed successfully!")
        logger.info(f"Results saved to: {output_dir}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Simulation interrupted by user")
        return 1
        
    except Exception as e:
        logger.error(f"\n❌ Simulation failed: {e}", exc_info=True)
        return 1


def print_banner():
    """Print welcome banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║      Adaptive Red Team vs Blue Team Security Simulator                      ║
║      Multi-Agent System with Reinforcement Learning                         ║
║                                                                              ║
║      Features:                                                               ║
║      • Synthetic Attack Generation (Red Team)                               ║
║      • LLM-Based Incident Detection (Blue Team)                             ║
║      • RAG-Enhanced Threat Intelligence                                     ║
║      • RL-Optimized Remediation Strategy                                    ║
║      • MITRE ATT&CK Framework Integration                                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_summary(metrics, orchestrator):
    """Print final summary"""
    print("\n" + "="*80)
    print("SIMULATION SUMMARY")
    print("="*80)
    
    print(f"\n📊 Overall Performance:")
    print(f"   Total Episodes:        {metrics.total_episodes}")
    print(f"   Successful Defenses:   {metrics.successful_defenses} ({metrics.successful_defenses/metrics.total_episodes:.1%})")
    print(f"   Failed Defenses:       {metrics.failed_defenses} ({metrics.failed_defenses/metrics.total_episodes:.1%})")
    print(f"   False Positives:       {metrics.false_positives}")
    print(f"   Detection Rate:        {metrics.detection_rate:.1%}")
    print(f"   Average Reward:        {metrics.average_reward:.3f}")
    
    print(f"\n🎯 Action Distribution:")
    total_actions = sum(metrics.action_distribution.values())
    for action, count in sorted(
        metrics.action_distribution.items(),
        key=lambda x: x[1],
        reverse=True
    ):
        pct = (count / total_actions * 100) if total_actions > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"   {action:20s} {count:3d} ({pct:5.1f}%) {bar}")
    
    # RL stats
    rl_stats = orchestrator.rl_agent.get_statistics()
    print(f"\n🤖 RL Agent Learning:")
    print(f"   States Explored:       {rl_stats['num_states']}")
    print(f"   Total Updates:         {rl_stats['update_count']}")
    print(f"   Final Epsilon:         {rl_stats['epsilon']:.4f}")
    print(f"   Avg Q-Value:           {rl_stats['avg_q_value']:.3f}")
    
    # Learning progress
    if len(metrics.reward_history) >= 10:
        first_10 = sum(metrics.reward_history[:10]) / 10
        last_10 = sum(metrics.reward_history[-10:]) / 10
        improvement = ((last_10 - first_10) / abs(first_10) * 100) if first_10 != 0 else 0
        print(f"\n📈 Learning Progress:")
        print(f"   First 10 Episodes:     {first_10:.3f}")
        print(f"   Last 10 Episodes:      {last_10:.3f}")
        print(f"   Improvement:           {improvement:+.1f}%")
    
    print("\n" + "="*80)


def run_demo():
    """Run a quick demo with predefined settings"""
    print_banner()
    print("\n🚀 Running Quick Demo (5 episodes with all attack types)")
    print("="*80 + "\n")
    
    orchestrator = CyberDefenseOrchestrator()
    
    attack_types = [
        AttackType.PHISHING,
        AttackType.CREDENTIAL_MISUSE,
        AttackType.LATERAL_MOVEMENT,
        AttackType.DATA_EXFILTRATION,
        AttackType.MALWARE_EXECUTION
    ]
    
    metrics = orchestrator.run_simulation(
        num_episodes=5,
        attack_types=attack_types
    )
    
    print_summary(metrics, orchestrator)
    
    output_dir = Path("./demo_results") / datetime.now().strftime("%Y%m%d_%H%M%S")
    orchestrator.save_results(output_dir)
    
    print(f"\n✅ Demo completed! Results saved to: {output_dir}")


if __name__ == "__main__":
    sys.exit(main())
