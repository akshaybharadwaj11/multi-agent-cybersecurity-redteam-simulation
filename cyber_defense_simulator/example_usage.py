"""
Basic Usage Examples for Cyber Defense Simulator
Demonstrates how to use the system programmatically
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.orchestrator import CyberDefenseOrchestrator
from core.data_models import AttackType, RemediationAction
from cyber_defense_simulator.rag.vector_store import VectorStore
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def example_1_basic_simulation():
    """
    Example 1: Run a basic simulation with default settings
    """
    print("\n" + "="*80)
    print("Example 1: Basic Simulation (10 episodes)")
    print("="*80 + "\n")
    
    # Initialize orchestrator
    orchestrator = CyberDefenseOrchestrator()
    
    # Run simulation
    metrics = orchestrator.run_simulation(num_episodes=10)
    
    # Print results
    print(f"\n📊 Results:")
    print(f"  Total Episodes: {metrics.total_episodes}")
    print(f"  Success Rate: {metrics.successful_defenses / metrics.total_episodes:.1%}")
    print(f"  Average Reward: {metrics.average_reward:.3f}")
    
    # Save results
    output_dir = Path("./results/example_1")
    orchestrator.save_results(output_dir)
    print(f"\n✅ Results saved to {output_dir}")


def example_2_specific_attacks():
    """
    Example 2: Simulate specific attack types
    """
    print("\n" + "="*80)
    print("Example 2: Specific Attack Types")
    print("="*80 + "\n")
    
    orchestrator = CyberDefenseOrchestrator()
    
    # Define attack sequence
    attack_sequence = [
        AttackType.PHISHING,
        AttackType.CREDENTIAL_MISUSE,
        AttackType.LATERAL_MOVEMENT,
        AttackType.DATA_EXFILTRATION
    ]
    
    print(f"Testing attacks: {[at.value for at in attack_sequence]}\n")
    
    # Run simulation
    metrics = orchestrator.run_simulation(
        num_episodes=len(attack_sequence) * 2,  # 2 episodes per attack type
        attack_types=attack_sequence
    )
    
    # Analyze by attack type
    print("\n📈 Results by Attack Type:")
    from collections import defaultdict
    attack_stats = defaultdict(lambda: {"success": 0, "total": 0})
    
    for episode in orchestrator.episodes:
        if episode.attack_scenario and episode.outcome:
            attack_type = episode.attack_scenario.attack_type.value
            attack_stats[attack_type]["total"] += 1
            if episode.outcome.success:
                attack_stats[attack_type]["success"] += 1
    
    for attack_type, stats in attack_stats.items():
        success_rate = stats["success"] / stats["total"] if stats["total"] > 0 else 0
        print(f"  {attack_type:20s} - Success: {stats['success']}/{stats['total']} ({success_rate:.1%})")


def example_3_single_episode_walkthrough():
    """
    Example 3: Detailed walkthrough of a single episode
    """
    print("\n" + "="*80)
    print("Example 3: Detailed Single Episode")
    print("="*80 + "\n")
    
    orchestrator = CyberDefenseOrchestrator()
    
    # Run single episode with phishing attack
    episode = orchestrator.run_episode(
        episode_number=1,
        attack_type=AttackType.PHISHING
    )
    
    # Display detailed information
    print("\n🔴 Red Team - Attack Scenario:")
    print(f"  Type: {episode.attack_scenario.attack_type.value}")
    print(f"  Target: {episode.attack_scenario.target_asset}")
    print(f"  Steps: {len(episode.attack_scenario.steps)}")
    for step in episode.attack_scenario.steps:
        print(f"    {step.step_number}. {step.technique_name} ({step.technique_id})")
    
    print("\n📊 Telemetry Generated:")
    print(f"  System Logs: {len(episode.telemetry.system_logs)}")
    print(f"  Auth Logs: {len(episode.telemetry.auth_logs)}")
    print(f"  Network Logs: {len(episode.telemetry.network_logs)}")
    print(f"  Process Logs: {len(episode.telemetry.process_logs)}")
    
    print("\n🔵 Detection - Incident Report:")
    print(f"  Severity: {episode.incident_report.severity.value}")
    print(f"  Confidence: {episode.incident_report.confidence:.2f}")
    print(f"  Summary: {episode.incident_report.summary}")
    print(f"  MITRE Techniques: {', '.join(episode.incident_report.mitre_techniques)}")
    
    print("\n📚 RAG - Retrieved Context:")
    print(f"  Runbooks: {len(episode.rag_context.runbooks)}")
    for runbook in episode.rag_context.runbooks[:2]:
        print(f"    - {runbook.title}")
    print(f"  Threat Intel: {len(episode.rag_context.threat_intel)}")
    
    print("\n💡 Remediation - Action Options:")
    for i, option in enumerate(episode.remediation_plan.options[:3], 1):
        print(f"  {i}. {option.action.value} (confidence: {option.confidence:.2f})")
        print(f"     {option.description}")
    
    print("\n🤖 RL Decision:")
    print(f"  Selected Action: {episode.rl_decision.selected_action.value}")
    print(f"  Exploration: {episode.rl_decision.is_exploration}")
    print(f"  Epsilon: {episode.rl_decision.epsilon:.4f}")
    
    print("\n⚖️ Outcome & Reward:")
    print(f"  Success: {episode.outcome.success}")
    print(f"  False Positive: {episode.outcome.false_positive}")
    print(f"  Collateral Damage: {episode.outcome.collateral_damage}")
    print(f"  Reward: {episode.reward.reward:.3f}")
    print(f"  Reward Components:")
    for component, value in episode.reward.components.items():
        print(f"    {component}: {value:.3f}")


def example_4_custom_rl_config():
    """
    Example 4: Custom RL configuration for faster learning
    """
    print("\n" + "="*80)
    print("Example 4: Custom RL Configuration")
    print("="*80 + "\n")
    
    # Create custom RL agent
    from rl.contextual_bandit import ContextualBandit
    
    all_actions = list(RemediationAction)
    custom_rl_agent = ContextualBandit(
        actions=all_actions,
        learning_rate=0.2,      # Higher learning rate
        epsilon=0.3,            # More exploration
        epsilon_decay=0.99,
        min_epsilon=0.05
    )
    
    # Initialize orchestrator
    orchestrator = CyberDefenseOrchestrator()
    
    # Replace default RL agent
    orchestrator.rl_agent = custom_rl_agent
    
    print("Running with custom RL configuration:")
    print(f"  Learning Rate: {custom_rl_agent.learning_rate}")
    print(f"  Initial Epsilon: {custom_rl_agent.epsilon}")
    print(f"  Epsilon Decay: {custom_rl_agent.epsilon_decay}\n")
    
    # Run simulation
    metrics = orchestrator.run_simulation(num_episodes=20)
    
    # Show learning progress
    print("\n📈 Learning Progress:")
    rl_stats = orchestrator.rl_agent.get_statistics()
    print(f"  Final Epsilon: {rl_stats['epsilon']:.4f}")
    print(f"  States Explored: {rl_stats['num_states']}")
    print(f"  Q-value Updates: {rl_stats['update_count']}")


def example_5_analyze_results():
    """
    Example 5: Analyze saved results
    """
    print("\n" + "="*80)
    print("Example 5: Analyzing Saved Results")
    print("="*80 + "\n")
    
    import json
    
    # Look for most recent results
    results_dir = Path("./results")
    if not results_dir.exists():
        print("No results directory found. Run example_1_basic_simulation() first.")
        return
    
    subdirs = [d for d in results_dir.iterdir() if d.is_dir()]
    if not subdirs:
        print("No simulation results found.")
        return
    
    latest = max(subdirs, key=lambda x: x.stat().st_mtime)
    print(f"Analyzing results from: {latest.name}\n")
    
    # Load metrics
    with open(latest / "metrics.json") as f:
        metrics = json.load(f)
    
    # Load episodes
    with open(latest / "episodes.json") as f:
        episodes = json.load(f)
    
    # Analysis
    print("📊 Performance Metrics:")
    print(f"  Total Episodes: {metrics['total_episodes']}")
    print(f"  Successful Defenses: {metrics['successful_defenses']}")
    print(f"  Failed Defenses: {metrics['failed_defenses']}")
    print(f"  False Positives: {metrics['false_positives']}")
    
    print("\n🎯 Action Preferences (Top 3):")
    sorted_actions = sorted(
        metrics['action_distribution'].items(),
        key=lambda x: x[1],
        reverse=True
    )
    for action, count in sorted_actions[:3]:
        pct = count / metrics['total_episodes'] * 100
        print(f"  {action:20s} {count:3d} ({pct:5.1f}%)")
    
    print("\n📈 Reward Trend:")
    if len(metrics['reward_history']) >= 10:
        first_5 = sum(metrics['reward_history'][:5]) / 5
        last_5 = sum(metrics['reward_history'][-5:]) / 5
        print(f"  First 5 episodes avg: {first_5:.3f}")
        print(f"  Last 5 episodes avg:  {last_5:.3f}")
        print(f"  Improvement: {((last_5 - first_5) / abs(first_5) * 100):+.1f}%")


def example_6_batch_experiments():
    """
    Example 6: Run batch experiments with different configurations
    """
    print("\n" + "="*80)
    print("Example 6: Batch Experiments")
    print("="*80 + "\n")
    
    configs = [
        {"name": "Conservative", "epsilon": 0.05, "learning_rate": 0.05},
        {"name": "Balanced", "epsilon": 0.15, "learning_rate": 0.1},
        {"name": "Aggressive", "epsilon": 0.3, "learning_rate": 0.2}
    ]
    
    results = []
    
    for config in configs:
        print(f"\n{'='*60}")
        print(f"Running: {config['name']} Configuration")
        print(f"{'='*60}")
        
        # Create RL agent with config
        from rl.contextual_bandit import ContextualBandit
        rl_agent = ContextualBandit(
            actions=list(RemediationAction),
            epsilon=config['epsilon'],
            learning_rate=config['learning_rate']
        )
        
        # Run simulation
        orchestrator = CyberDefenseOrchestrator()
        orchestrator.rl_agent = rl_agent
        
        metrics = orchestrator.run_simulation(num_episodes=15)
        
        results.append({
            "config": config['name'],
            "success_rate": metrics.successful_defenses / metrics.total_episodes,
            "avg_reward": metrics.average_reward
        })
    
    # Compare results
    print("\n" + "="*80)
    print("📊 Comparison of Configurations")
    print("="*80)
    print(f"{'Configuration':<15} {'Success Rate':<15} {'Avg Reward':<15}")
    print("-" * 50)
    for result in results:
        print(
            f"{result['config']:<15} "
            f"{result['success_rate']:<15.1%} "
            f"{result['avg_reward']:<15.3f}"
        )


def main():
    """Run all examples"""
    print("\n" + "#"*80)
    print("Cyber Defense Simulator - Usage Examples")
    print("#"*80)
    
    examples = [
        ("Basic Simulation", example_1_basic_simulation),
        ("Specific Attack Types", example_2_specific_attacks),
        ("Single Episode Walkthrough", example_3_single_episode_walkthrough),
        ("Custom RL Configuration", example_4_custom_rl_config),
        ("Analyze Results", example_5_analyze_results),
        ("Batch Experiments", example_6_batch_experiments)
    ]
    
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    choice = input("\nEnter example number (or 'all' to run all): ").strip().lower()
    
    if choice == 'all':
        for name, func in examples:
            try:
                func()
            except KeyboardInterrupt:
                print("\n\nExamples interrupted by user.")
                break
            except Exception as e:
                print(f"\n❌ Error in {name}: {e}")
    elif choice.isdigit() and 1 <= int(choice) <= len(examples):
        name, func = examples[int(choice) - 1]
        func()
    else:
        print("Invalid choice. Please run again and select a valid example number.")


if __name__ == "__main__":
    main()
