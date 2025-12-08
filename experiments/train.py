"""
Main Training Script for Red Team vs Blue Team RL System
Trains DQN agents with MARL coordination
"""

import os
import yaml
import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
from pathlib import Path
import argparse
from datetime import datetime

import sys
# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.environments.cyber_env import CyberSecurityEnv
from src.rl.dqn import DQNAgent
from src.rl.marl import create_marl_system, MARLEnvironment
from src.crew.agents import create_red_team_agents, create_blue_team_agents, CyberSecurityOrchestrator


def load_config(config_path: str) -> dict:
    """Load training configuration"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def setup_directories(base_dir: str = 'outputs'):
    """Create necessary directories"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_dir = Path(base_dir) / f'run_{timestamp}'
    
    dirs = {
        'checkpoints': run_dir / 'checkpoints',
        'logs': run_dir / 'logs',
        'plots': run_dir / 'plots',
        'results': run_dir / 'results'
    }
    
    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    return dirs


def plot_training_curves(
    red_rewards: list,
    blue_rewards: list,
    red_win_rates: list,
    blue_win_rates: list,
    save_dir: Path
):
    """Plot and save training curves"""
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Training Progress: Red Team vs Blue Team', fontsize=16, fontweight='bold')
    
    # Plot 1: Cumulative Rewards
    episodes = range(len(red_rewards))
    axes[0, 0].plot(episodes, red_rewards, label='Red Team', color='red', alpha=0.7)
    axes[0, 0].plot(episodes, blue_rewards, label='Blue Team', color='blue', alpha=0.7)
    
    # Add moving average
    window = 100
    if len(red_rewards) >= window:
        red_ma = np.convolve(red_rewards, np.ones(window)/window, mode='valid')
        blue_ma = np.convolve(blue_rewards, np.ones(window)/window, mode='valid')
        axes[0, 0].plot(range(window-1, len(red_rewards)), red_ma, 
                       color='darkred', linewidth=2, label='Red MA')
        axes[0, 0].plot(range(window-1, len(blue_rewards)), blue_ma, 
                       color='darkblue', linewidth=2, label='Blue MA')
    
    axes[0, 0].set_xlabel('Episode')
    axes[0, 0].set_ylabel('Cumulative Reward')
    axes[0, 0].set_title('Team Rewards Over Time')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # Plot 2: Win Rates
    axes[0, 1].plot(episodes, red_win_rates, label='Red Win Rate', color='red', linewidth=2)
    axes[0, 1].plot(episodes, blue_win_rates, label='Blue Win Rate', color='blue', linewidth=2)
    axes[0, 1].axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, label='50% (Nash Equilibrium)')
    axes[0, 1].set_xlabel('Episode')
    axes[0, 1].set_ylabel('Win Rate')
    axes[0, 1].set_title('Win Rates (100-episode moving average)')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].set_ylim([0, 1])
    
    # Plot 3: Reward Distribution
    recent_red = red_rewards[-500:] if len(red_rewards) >= 500 else red_rewards
    recent_blue = blue_rewards[-500:] if len(blue_rewards) >= 500 else blue_rewards
    
    axes[1, 0].hist(recent_red, bins=30, alpha=0.6, color='red', label='Red Team')
    axes[1, 0].hist(recent_blue, bins=30, alpha=0.6, color='blue', label='Blue Team')
    axes[1, 0].set_xlabel('Reward')
    axes[1, 0].set_ylabel('Frequency')
    axes[1, 0].set_title('Reward Distribution (Last 500 Episodes)')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # Plot 4: Learning Progress
    if len(red_rewards) >= window:
        red_improvement = np.array(red_ma) - red_ma[0]
        blue_improvement = np.array(blue_ma) - blue_ma[0]
        
        axes[1, 1].plot(range(window-1, len(red_rewards)), red_improvement, 
                       color='red', label='Red Improvement', linewidth=2)
        axes[1, 1].plot(range(window-1, len(blue_rewards)), blue_improvement, 
                       color='blue', label='Blue Improvement', linewidth=2)
        axes[1, 1].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        axes[1, 1].set_xlabel('Episode')
        axes[1, 1].set_ylabel('Improvement from Baseline')
        axes[1, 1].set_title('Learning Progress')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_dir / 'training_curves.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Training curves saved to {save_dir / 'training_curves.png'}")


def train_marl_system(config: dict, dirs: dict):
    """Main training loop"""
    
    print("\n" + "="*60)
    print("RED TEAM vs BLUE TEAM - Multi-Agent RL Training")
    print("="*60 + "\n")
    
    # Initialize environment
    print("Initializing environment...")
    env = CyberSecurityEnv(
        dataset_path=config.get('dataset_path'),
        n_nodes=config['environment']['n_nodes'],
        max_steps=config['environment']['max_steps'],
        use_real_traffic=config['environment']['use_real_traffic']
    )
    
    # Create MARL system
    print("Creating MARL system...")
    marl_system = create_marl_system(
        n_red_agents=config['agents']['n_red_agents'],
        n_blue_agents=config['agents']['n_blue_agents'],
        state_dim=env.state_dim,
        action_dim=10
    )
    
    red_coordinator = marl_system.red_team
    blue_coordinator = marl_system.blue_team
    
    # Training metrics
    red_episode_rewards = []
    blue_episode_rewards = []
    red_win_rates = []
    blue_win_rates = []
    red_wins = 0
    blue_wins = 0
    
    # Training loop
    print(f"\nStarting training for {config['training']['n_episodes']} episodes...")
    print(f"Checkpoint interval: {config['training']['checkpoint_interval']} episodes\n")
    
    for episode in tqdm(range(config['training']['n_episodes']), desc="Training"):
        # Reset environment
        state, _ = env.reset()
        
        # Split state for each agent (simplified - each agent sees full state)
        red_states = np.array([state] * len(red_coordinator.agents))
        blue_states = np.array([state] * len(blue_coordinator.agents))
        
        episode_red_reward = 0
        episode_blue_reward = 0
        done = False
        step = 0
        
        while not done and step < config['environment']['max_steps']:
            # Get actions from both teams
            red_actions = red_coordinator.get_team_action(red_states, evaluate=False)
            blue_actions = blue_coordinator.get_team_action(blue_states, evaluate=False)
            
            # Execute red team actions
            red_rewards_list = []
            for action in red_actions:
                next_state, reward, done, _, info = env.step_red(action)
                red_rewards_list.append(reward)
                episode_red_reward += reward
            
            # Execute blue team actions
            blue_rewards_list = []
            for action in blue_actions:
                next_state, reward, done, _, info = env.step_blue(action)
                blue_rewards_list.append(reward)
                episode_blue_reward += reward
            
            # Update next states
            next_red_states = np.array([next_state] * len(red_coordinator.agents))
            next_blue_states = np.array([next_state] * len(blue_coordinator.agents))
            
            # MARL coordination and learning
            red_success = info['attack_success_rate']
            blue_success = info['defense_success_rate']
            
            marl_system.step(
                red_states, blue_states,
                red_actions, blue_actions,
                red_success, blue_success,
                next_red_states, next_blue_states,
                done
            )
            
            # Update states
            red_states = next_red_states
            blue_states = next_blue_states
            state = next_state
            step += 1
        
        # Episode finished
        red_episode_rewards.append(episode_red_reward)
        blue_episode_rewards.append(episode_blue_reward)
        
        # Track wins
        if info['attack_success_rate'] > info['defense_success_rate'] + 0.1:
            red_wins += 1
        elif info['defense_success_rate'] > info['attack_success_rate'] + 0.1:
            blue_wins += 1
        
        # Calculate win rates (moving average over last 100 episodes)
        window = min(100, episode + 1)
        recent_red_wins = sum(1 for i in range(max(0, episode - window + 1), episode + 1)
                             if i < len(red_episode_rewards) and 
                             red_episode_rewards[i] > blue_episode_rewards[i])
        recent_blue_wins = sum(1 for i in range(max(0, episode - window + 1), episode + 1)
                              if i < len(blue_episode_rewards) and 
                              blue_episode_rewards[i] > red_episode_rewards[i])
        
        red_win_rates.append(recent_red_wins / window)
        blue_win_rates.append(recent_blue_wins / window)
        
        # Logging
        if (episode + 1) % config['training']['log_interval'] == 0:
            stats = marl_system.get_statistics()
            print(f"\nEpisode {episode + 1}/{config['training']['n_episodes']}")
            print(f"  Red Reward: {episode_red_reward:.2f} | Blue Reward: {episode_blue_reward:.2f}")
            print(f"  Red Win Rate: {stats['red_win_rate']:.2%} | Blue Win Rate: {stats['blue_win_rate']:.2%}")
            print(f"  Attack Success: {info['attack_success_rate']:.2%} | Defense Success: {info['defense_success_rate']:.2%}")
            print(f"  Epsilon (Red): {red_coordinator.agents[0].epsilon:.3f}")
        
        # Save checkpoints
        if (episode + 1) % config['training']['checkpoint_interval'] == 0:
            checkpoint_dir = dirs['checkpoints'] / f'episode_{episode + 1}'
            checkpoint_dir.mkdir(exist_ok=True)
            
            for i, agent in enumerate(red_coordinator.agents):
                agent.save(checkpoint_dir / f'red_agent_{i}.pt')
            
            for i, agent in enumerate(blue_coordinator.agents):
                agent.save(checkpoint_dir / f'blue_agent_{i}.pt')
            
            print(f"Checkpoint saved: {checkpoint_dir}")
        
        # Plot training curves
        if (episode + 1) % config['training']['plot_interval'] == 0:
            plot_training_curves(
                red_episode_rewards,
                blue_episode_rewards,
                red_win_rates,
                blue_win_rates,
                dirs['plots']
            )
    
    # Final checkpoint
    print("\n\nTraining completed! Saving final models...")
    final_dir = dirs['checkpoints'] / 'final'
    final_dir.mkdir(exist_ok=True)
    
    for i, agent in enumerate(red_coordinator.agents):
        agent.save(final_dir / f'red_agent_{i}.pt')
    
    for i, agent in enumerate(blue_coordinator.agents):
        agent.save(final_dir / f'blue_agent_{i}.pt')
    
    # Final plots
    plot_training_curves(
        red_episode_rewards,
        blue_episode_rewards,
        red_win_rates,
        blue_win_rates,
        dirs['plots']
    )
    
    # Save training statistics
    stats = {
        'total_episodes': len(red_episode_rewards),
        'final_red_win_rate': red_wins / len(red_episode_rewards),
        'final_blue_win_rate': blue_wins / len(blue_episode_rewards),
        'avg_red_reward': np.mean(red_episode_rewards[-100:]),
        'avg_blue_reward': np.mean(blue_episode_rewards[-100:]),
        'convergence_episode': None
    }
    
    # Detect convergence (when win rates stabilize around 0.5)
    for i in range(100, len(red_win_rates)):
        if abs(red_win_rates[i] - 0.5) < 0.05 and abs(blue_win_rates[i] - 0.5) < 0.05:
            stats['convergence_episode'] = i
            break
    
    with open(dirs['results'] / 'training_stats.yaml', 'w') as f:
        yaml.dump(stats, f)
    
    print("\n" + "="*60)
    print("TRAINING SUMMARY")
    print("="*60)
    print(f"Total Episodes: {stats['total_episodes']}")
    print(f"Final Red Win Rate: {stats['final_red_win_rate']:.2%}")
    print(f"Final Blue Win Rate: {stats['final_blue_win_rate']:.2%}")
    print(f"Avg Red Reward (last 100): {stats['avg_red_reward']:.2f}")
    print(f"Avg Blue Reward (last 100): {stats['avg_blue_reward']:.2f}")
    if stats['convergence_episode']:
        print(f"Convergence at episode: {stats['convergence_episode']}")
    print("="*60 + "\n")
    
    return marl_system, env, stats


def main():
    parser = argparse.ArgumentParser(description='Train Red Team vs Blue Team RL System')
    parser.add_argument('--config', type=str, default='experiments/configs/config.yaml',
                       help='Path to config file')
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    
    # Setup directories
    dirs = setup_directories()
    
    # Save config to output directory
    with open(dirs['logs'] / 'config.yaml', 'w') as f:
        yaml.dump(config, f)
    
    # Train
    marl_system, env, stats = train_marl_system(config, dirs)
    
    print(f"\nAll outputs saved to: {dirs['checkpoints'].parent}")
    print("\nTo evaluate the trained model, run:")
    print(f"python experiments/evaluate.py --checkpoint {dirs['checkpoints'] / 'final'}")


if __name__ == '__main__':
    main()