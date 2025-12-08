"""
Multi-Agent Reinforcement Learning (MARL) Implementation
Coordinated learning for Red Team vs Blue Team
"""

import torch
import numpy as np
from typing import List, Dict, Tuple
from .dqn import DQNAgent


class TeamCoordinator:
    """Coordinates learning and actions across team members"""
    
    def __init__(self, agents: List[DQNAgent], team_type: str):
        self.agents = agents
        self.team_type = team_type  # 'red' or 'blue'
        self.team_reward_history = []
        self.coordination_matrix = np.zeros((len(agents), len(agents)))
        
    def get_team_action(self, team_state: np.ndarray, evaluate=False) -> List[int]:
        """Get coordinated actions from all team members"""
        actions = []
        for i, agent in enumerate(self.agents):
            # Each agent sees its own state slice plus team context
            agent_state = team_state[i]
            action = agent.select_action(agent_state, evaluate)
            actions.append(action)
        return actions
    
    def compute_team_reward(
        self, 
        individual_rewards: List[float],
        team_bonus: float = 0.0
    ) -> List[float]:
        """
        Compute shaped rewards for team members
        Combines individual rewards with team-level coordination bonus
        """
        # Base: individual rewards
        shaped_rewards = list(individual_rewards)
        
        # Add team coordination bonus
        if team_bonus != 0:
            bonus_per_agent = team_bonus / len(self.agents)
            shaped_rewards = [r + bonus_per_agent for r in shaped_rewards]
        
        # Track team performance
        self.team_reward_history.append(sum(shaped_rewards))
        
        return shaped_rewards
    
    def update_coordination_matrix(self, actions: List[int], reward: float):
        """Track which action combinations work well together"""
        n_agents = len(actions)
        for i in range(n_agents):
            for j in range(i + 1, n_agents):
                # Update coordination score between agent pairs
                self.coordination_matrix[i, j] += reward / n_agents
                self.coordination_matrix[j, i] = self.coordination_matrix[i, j]
    
    def get_coordination_bonus(self, actions: List[int]) -> float:
        """Compute bonus based on learned coordination patterns"""
        bonus = 0.0
        n_agents = len(actions)
        for i in range(n_agents):
            for j in range(i + 1, n_agents):
                bonus += self.coordination_matrix[i, j]
        return bonus / (n_agents * (n_agents - 1) / 2) if n_agents > 1 else 0.0


class CentralizedCritic:
    """
    Centralized critic for CTDE (Centralized Training, Decentralized Execution)
    Uses global state information during training to improve coordination
    """
    
    def __init__(self, global_state_dim: int, n_agents: int, n_actions: int):
        self.global_state_dim = global_state_dim
        self.n_agents = n_agents
        self.n_actions = n_actions
        
        # Critic network sees global state and all agent actions
        input_dim = global_state_dim + (n_agents * n_actions)
        self.critic = torch.nn.Sequential(
            torch.nn.Linear(input_dim, 256),
            torch.nn.ReLU(),
            torch.nn.Linear(256, 128),
            torch.nn.ReLU(),
            torch.nn.Linear(128, 1)
        )
        
        self.optimizer = torch.optim.Adam(self.critic.parameters(), lr=0.001)
        self.loss_fn = torch.nn.MSELoss()
        
    def get_value(self, global_state: torch.Tensor, actions: torch.Tensor) -> torch.Tensor:
        """Estimate value of joint action given global state"""
        # One-hot encode actions
        actions_onehot = torch.nn.functional.one_hot(
            actions.long(), 
            num_classes=self.n_actions
        ).float().flatten(start_dim=1)
        
        # Concatenate global state and actions
        critic_input = torch.cat([global_state, actions_onehot], dim=1)
        return self.critic(critic_input)
    
    def update(
        self, 
        global_states: torch.Tensor,
        actions: torch.Tensor,
        rewards: torch.Tensor,
        next_global_states: torch.Tensor,
        next_actions: torch.Tensor,
        dones: torch.Tensor,
        gamma: float = 0.99
    ):
        """Update centralized critic"""
        # Current value
        current_value = self.get_value(global_states, actions)
        
        # Target value
        with torch.no_grad():
            next_value = self.get_value(next_global_states, next_actions)
            target_value = rewards + (1 - dones) * gamma * next_value
        
        # Compute loss and update
        loss = self.loss_fn(current_value, target_value)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        return loss.item()


class MARLEnvironment:
    """
    Multi-Agent RL Environment coordinating Red vs Blue teams
    Implements competitive multi-agent dynamics
    """
    
    def __init__(
        self,
        red_team: TeamCoordinator,
        blue_team: TeamCoordinator,
        use_centralized_critic: bool = True
    ):
        self.red_team = red_team
        self.blue_team = blue_team
        self.use_centralized_critic = use_centralized_critic
        
        if use_centralized_critic:
            # Global state includes both teams' observations
            global_state_dim = len(red_team.agents) * red_team.agents[0].state_dim + \
                             len(blue_team.agents) * blue_team.agents[0].state_dim
            
            self.red_critic = CentralizedCritic(
                global_state_dim,
                len(red_team.agents),
                red_team.agents[0].action_dim
            )
            self.blue_critic = CentralizedCritic(
                global_state_dim,
                len(blue_team.agents),
                blue_team.agents[0].action_dim
            )
        
        self.episode_count = 0
        self.red_wins = 0
        self.blue_wins = 0
        self.draws = 0
        
    def compute_competitive_rewards(
        self,
        red_team_success: float,
        blue_team_success: float,
        red_actions: List[int],
        blue_actions: List[int]
    ) -> Tuple[List[float], List[float]]:
        """
        Compute rewards for competitive multi-agent setting
        Red team wants to maximize attack success
        Blue team wants to maximize defense success
        """
        # Base rewards from individual success rates
        base_red_reward = red_team_success
        base_blue_reward = blue_team_success
        
        # Competitive component: teams penalized by opponent's success
        red_individual = [base_red_reward - 0.5 * base_blue_reward 
                         for _ in red_actions]
        blue_individual = [base_blue_reward - 0.5 * base_red_reward 
                          for _ in blue_actions]
        
        # Team coordination bonuses
        red_coord_bonus = self.red_team.get_coordination_bonus(red_actions)
        blue_coord_bonus = self.blue_team.get_coordination_bonus(blue_actions)
        
        # Shaped rewards
        red_rewards = self.red_team.compute_team_reward(
            red_individual, 
            team_bonus=red_coord_bonus
        )
        blue_rewards = self.blue_team.compute_team_reward(
            blue_individual,
            team_bonus=blue_coord_bonus
        )
        
        return red_rewards, blue_rewards
    
    def step(
        self,
        red_states: np.ndarray,
        blue_states: np.ndarray,
        red_actions: List[int],
        blue_actions: List[int],
        red_success: float,
        blue_success: float,
        next_red_states: np.ndarray,
        next_blue_states: np.ndarray,
        done: bool
    ):
        """Execute one step of multi-agent interaction"""
        
        # Compute competitive rewards
        red_rewards, blue_rewards = self.compute_competitive_rewards(
            red_success, blue_success, red_actions, blue_actions
        )
        
        # Update coordination matrices
        avg_red_reward = np.mean(red_rewards)
        avg_blue_reward = np.mean(blue_rewards)
        self.red_team.update_coordination_matrix(red_actions, avg_red_reward)
        self.blue_team.update_coordination_matrix(blue_actions, avg_blue_reward)
        
        # Store transitions and train individual agents
        for i, agent in enumerate(self.red_team.agents):
            agent.store_transition(
                red_states[i], 
                red_actions[i],
                red_rewards[i],
                next_red_states[i],
                done
            )
            agent.train_step()
        
        for i, agent in enumerate(self.blue_team.agents):
            agent.store_transition(
                blue_states[i],
                blue_actions[i],
                blue_rewards[i],
                next_blue_states[i],
                done
            )
            agent.train_step()
        
        # Update centralized critics if enabled
        if self.use_centralized_critic and done:
            # This would be called with batched data in practice
            pass
        
        # Track wins/draws
        if done:
            self.episode_count += 1
            if red_success > blue_success + 0.1:
                self.red_wins += 1
            elif blue_success > red_success + 0.1:
                self.blue_wins += 1
            else:
                self.draws += 1
        
        return red_rewards, blue_rewards
    
    def get_statistics(self) -> Dict:
        """Get training statistics"""
        total = self.episode_count if self.episode_count > 0 else 1
        return {
            'episodes': self.episode_count,
            'red_win_rate': self.red_wins / total,
            'blue_win_rate': self.blue_wins / total,
            'draw_rate': self.draws / total,
            'red_avg_reward': np.mean(self.red_team.team_reward_history[-100:]) 
                            if self.red_team.team_reward_history else 0,
            'blue_avg_reward': np.mean(self.blue_team.team_reward_history[-100:])
                             if self.blue_team.team_reward_history else 0
        }


class CommProtocol:
    """
    Communication protocol for agent coordination
    Enables message passing between team members
    """
    
    def __init__(self, n_agents: int, message_dim: int = 16):
        self.n_agents = n_agents
        self.message_dim = message_dim
        self.message_buffer = {}
        
    def send_message(self, sender_id: int, message: np.ndarray):
        """Agent sends message to team"""
        self.message_buffer[sender_id] = message
    
    def receive_messages(self, receiver_id: int) -> np.ndarray:
        """Agent receives messages from team"""
        messages = []
        for agent_id, message in self.message_buffer.items():
            if agent_id != receiver_id:
                messages.append(message)
        
        if not messages:
            return np.zeros(self.message_dim * (self.n_agents - 1))
        
        return np.concatenate(messages)
    
    def clear(self):
        """Clear message buffer"""
        self.message_buffer = {}


def create_marl_system(
    n_red_agents: int = 4,
    n_blue_agents: int = 4,
    state_dim: int = 78,
    action_dim: int = 10
) -> MARLEnvironment:
    """Factory function to create complete MARL system"""
    
    # Create red team agents
    red_agents = [
        DQNAgent(
            state_dim=state_dim,
            action_dim=action_dim,
            agent_type='red'
        )
        for _ in range(n_red_agents)
    ]
    
    # Create blue team agents
    blue_agents = [
        DQNAgent(
            state_dim=state_dim,
            action_dim=action_dim,
            agent_type='blue'
        )
        for _ in range(n_blue_agents)
    ]
    
    # Create team coordinators
    red_coordinator = TeamCoordinator(red_agents, 'red')
    blue_coordinator = TeamCoordinator(blue_agents, 'blue')
    
    # Create MARL environment
    marl_env = MARLEnvironment(red_coordinator, blue_coordinator)
    
    return marl_env