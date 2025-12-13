#!/usr/bin/env python3
"""
Train RL Agent for 1000 Episodes
Runs training directly in the backend without UI
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add the cyber_defense_simulator to path
sys.path.insert(0, str(Path(__file__).parent))

from cyber_defense_simulator.core.orchestrator import CyberDefenseOrchestrator
from cyber_defense_simulator.core.data_models import AttackType
from cyber_defense_simulator.core.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'training_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)


def print_banner():
    """Print training banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║         RL Agent Training - 1000 Episodes                   ║
    ║         Multi-Agent Cybersecurity Simulation                 ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_progress(orchestrator, episode_num, total_episodes):
    """Print training progress"""
    if orchestrator.rl_agent:
        stats = orchestrator.rl_agent.get_statistics()
        logger.info(f"\n{'='*80}")
        logger.info(f"Episode {episode_num}/{total_episodes} Progress")
        logger.info(f"{'='*80}")
        logger.info(f"Total Episodes Completed: {stats['episode_count']}")
        logger.info(f"Q-Value Updates: {stats['update_count']}")
        logger.info(f"States Learned: {stats['num_states']}")
        logger.info(f"Current Epsilon: {orchestrator.rl_agent.epsilon:.4f}")
        logger.info(f"Average Q-Value: {stats['avg_q_value']:.4f}")
        logger.info(f"Action Distribution: {stats['action_distribution']}")
        logger.info(f"{'='*80}\n")


def main():
    """Main training function"""
    print_banner()
    
    num_episodes = 1000
    logger.info(f"Starting RL Agent training for {num_episodes} episodes...")
    logger.info(f"Training log will be saved to: training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    try:
        # Initialize orchestrator with knowledge base
        logger.info("Initializing Cyber Defense Orchestrator...")
        orchestrator = CyberDefenseOrchestrator(initialize_kb=True)
        
        # Get initial RL stats
        initial_stats = orchestrator.rl_agent.get_statistics()
        logger.info(f"Initial RL State:")
        logger.info(f"  - Epsilon: {orchestrator.rl_agent.epsilon:.4f}")
        logger.info(f"  - Learning Rate: {orchestrator.rl_agent.learning_rate:.4f}")
        logger.info(f"  - States: {initial_stats['num_states']}")
        logger.info(f"  - Updates: {initial_stats['update_count']}")
        
        # Cycle through different attack types for diverse training
        attack_types = [
            AttackType.PHISHING,
            AttackType.CREDENTIAL_MISUSE,
            AttackType.LATERAL_MOVEMENT,
            AttackType.DATA_EXFILTRATION,
            AttackType.MALWARE_EXECUTION,
            AttackType.PRIVILEGE_ESCALATION,
        ]
        
        logger.info(f"\n{'#'*80}")
        logger.info(f"Starting Training: {num_episodes} episodes")
        logger.info(f"Attack types: {[at.value for at in attack_types]}")
        logger.info(f"{'#'*80}\n")
        
        # Track metrics
        successful_episodes = 0
        total_reward = 0.0
        
        # Run training episodes
        for episode_num in range(1, num_episodes + 1):
            try:
                # Cycle through attack types
                attack_type = attack_types[(episode_num - 1) % len(attack_types)]
                
                # Run episode
                episode = orchestrator.run_episode(
                    episode_number=episode_num,
                    attack_type=attack_type
                )
                
                # Track metrics
                if episode.outcome and episode.outcome.success:
                    successful_episodes += 1
                if episode.reward:
                    total_reward += episode.reward.reward
                
                # Print progress every 10 episodes
                if episode_num % 10 == 0:
                    print_progress(orchestrator, episode_num, num_episodes)
                    success_rate = (successful_episodes / episode_num) * 100
                    avg_reward = total_reward / episode_num
                    logger.info(f"Progress: {episode_num}/{num_episodes} | "
                              f"Success Rate: {success_rate:.1f}% | "
                              f"Avg Reward: {avg_reward:.3f}")
                
                # Print progress every 100 episodes
                if episode_num % 100 == 0:
                    logger.info(f"\n{'#'*80}")
                    logger.info(f"Milestone: {episode_num} episodes completed!")
                    logger.info(f"{'#'*80}\n")
                    
            except Exception as e:
                logger.error(f"Error in episode {episode_num}: {e}", exc_info=True)
                continue
        
        # Final statistics
        final_stats = orchestrator.rl_agent.get_statistics()
        final_success_rate = (successful_episodes / num_episodes) * 100
        final_avg_reward = total_reward / num_episodes
        
        logger.info(f"\n{'#'*80}")
        logger.info("Training Complete!")
        logger.info(f"{'#'*80}")
        logger.info(f"Total Episodes: {num_episodes}")
        logger.info(f"Successful Defenses: {successful_episodes}")
        logger.info(f"Success Rate: {final_success_rate:.2f}%")
        logger.info(f"Average Reward: {final_avg_reward:.4f}")
        logger.info(f"\nFinal RL Agent Statistics:")
        logger.info(f"  - Episodes Trained: {final_stats['episode_count']}")
        logger.info(f"  - Q-Value Updates: {final_stats['update_count']}")
        logger.info(f"  - States Learned: {final_stats['num_states']}")
        logger.info(f"  - Final Epsilon: {orchestrator.rl_agent.epsilon:.4f}")
        logger.info(f"  - Average Q-Value: {final_stats['avg_q_value']:.4f}")
        logger.info(f"  - Action Distribution: {final_stats['action_distribution']}")
        logger.info(f"{'#'*80}\n")
        
        # Save results
        output_dir = Path("training_results") / datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving training results to: {output_dir}")
        orchestrator.save_results(output_dir)
        
        # Save RL agent state
        rl_agent_path = output_dir / "rl_agent.pkl"
        orchestrator.rl_agent.save(rl_agent_path)
        logger.info(f"RL Agent saved to: {rl_agent_path}")
        
        logger.info("\n✅ Training completed successfully!")
        logger.info(f"Results saved to: {output_dir}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Training interrupted by user")
        logger.info(f"Completed {len(orchestrator.episodes)} episodes before interruption")
        return 1
        
    except Exception as e:
        logger.error(f"\n❌ Training failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())

