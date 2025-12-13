"""
Contextual Bandit RL Agent
Learns optimal remediation actions based on incident context
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import pickle
from pathlib import Path
import logging

from cyber_defense_simulator.core.data_models import State, RemediationAction, RLDecision
from cyber_defense_simulator.core.config import Config

logger = logging.getLogger(__name__)


class ContextualBandit:
    """
    Contextual bandit for adaptive remediation strategy learning
    
    Uses epsilon-greedy policy with Q-learning updates
    """
    
    def __init__(
        self,
        actions: List[RemediationAction],
        learning_rate: float = None,
        epsilon: float = None,
        epsilon_decay: float = None,
        min_epsilon: float = None,
        discount_factor: float = None,
        q_init: float = None
    ):
        """
        Initialize contextual bandit
        
        Args:
            actions: List of possible remediation actions
            learning_rate: Learning rate (alpha)
            epsilon: Initial exploration rate
            epsilon_decay: Epsilon decay factor per episode
            min_epsilon: Minimum epsilon value
            discount_factor: Discount factor (gamma)
            q_init: Initial Q-value
        """
        self.actions = [action.value for action in actions]
        
        # Use config defaults if not provided
        config = Config.get_rl_config()
        self.learning_rate = learning_rate or config['learning_rate']
        self.epsilon = epsilon or config['epsilon']
        self.epsilon_decay = epsilon_decay or config['epsilon_decay']
        self.min_epsilon = min_epsilon or config['min_epsilon']
        self.discount_factor = discount_factor or config['discount_factor']
        
        # Q-table: state_key -> {action: q_value}
        self.q_table: Dict[str, Dict[str, float]] = {}
        self.q_init = q_init or config['q_init']
        
        # Statistics
        self.episode_count = 0
        self.update_count = 0
        self.action_counts: Dict[str, int] = {action: 0 for action in self.actions}
        
        logger.info(f"Initialized ContextualBandit with {len(self.actions)} actions")
        logger.info(f"LR={self.learning_rate}, epsilon={self.epsilon}, gamma={self.discount_factor}")
    
    def _state_to_key(self, state: State) -> str:
        """
        Convert state to hashable key for Q-table
        
        Improved state representation with finer granularity:
        - Severity: 4 levels (low, medium, high, critical)
        - Attack type: 6 types
        - Confidence: 10 bins (0-9)
        - Affected assets: 5 bins (0-2, 3-5, 6-10, 11-20, 21+)
        
        Args:
            state: Current state
            
        Returns:
            String key representation
        """
        # Finer granularity for confidence (20 bins instead of 10)
        confidence_bin = int(state.confidence_level * 20)
        
        # Better discretization for affected assets
        if state.num_affected_assets <= 2:
            assets_bin = "0-2"
        elif state.num_affected_assets <= 5:
            assets_bin = "3-5"
        elif state.num_affected_assets <= 10:
            assets_bin = "6-10"
        elif state.num_affected_assets <= 20:
            assets_bin = "11-20"
        else:
            assets_bin = "21+"
        
        return (
            f"{state.incident_severity.value}_"
            f"{state.attack_type.value}_"
            f"c{confidence_bin}_"
            f"a{assets_bin}"
        )
    
    def _get_q_values(self, state: State) -> Dict[str, float]:
        """
        Get Q-values for all actions in given state
        
        Args:
            state: Current state
            
        Returns:
            Dictionary of action -> Q-value
        """
        state_key = self._state_to_key(state)
        
        if state_key not in self.q_table:
            # Initialize Q-values for new state
            self.q_table[state_key] = {
                action: self.q_init for action in self.actions
            }
        
        return self.q_table[state_key]
    
    def select_action(self, state: State) -> RLDecision:
        """
        Select action using epsilon-greedy policy with softmax fallback
        
        Improved action selection:
        - Epsilon-greedy for exploration/exploitation balance
        - Softmax for tie-breaking when Q-values are close
        
        Args:
            state: Current state
            
        Returns:
            RLDecision with selected action and metadata
        """
        q_values = self._get_q_values(state)
        
        # Epsilon-greedy selection
        is_exploration = np.random.random() < self.epsilon
        
        if is_exploration:
            # Explore: random action
            selected_action = np.random.choice(self.actions)
        else:
            # Exploit: best action, with softmax tie-breaking for close Q-values
            max_q = max(q_values.values())
            close_actions = [a for a, q in q_values.items() if q >= max_q - 0.1]
            
            if len(close_actions) > 1:
                # Multiple actions with similar Q-values - use softmax
                q_array = np.array([q_values[a] for a in close_actions])
                exp_q = np.exp(q_array - np.max(q_array))  # Numerical stability
                probs = exp_q / exp_q.sum()
                selected_action = np.random.choice(close_actions, p=probs)
            else:
                # Clear best action
                selected_action = max(q_values.items(), key=lambda x: x[1])[0]
        
        # Update statistics
        self.action_counts[selected_action] += 1
        
        # Create decision object
        # Use model_validate with proper state serialization for Pydantic v2
        try:
            decision = RLDecision(
                state=state,
                selected_action=RemediationAction(selected_action),
                q_values=q_values.copy(),
                epsilon=self.epsilon,
                is_exploration=is_exploration
            )
        except Exception as e:
            # Fallback for Pydantic v2: validate from dict
            logger.warning(f"RLDecision validation error, using fallback: {e}")
            state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.dict()
            decision_data = {
                "state": State.model_validate(state_dict),
                "selected_action": selected_action,
                "q_values": q_values.copy(),
                "epsilon": self.epsilon,
                "is_exploration": is_exploration
            }
            decision = RLDecision(**decision_data)
        
        logger.debug(
            f"Selected action: {selected_action} "
            f"({'exploration' if is_exploration else 'exploitation'})"
        )
        
        return decision
    
    def update(
        self,
        state: State,
        action: RemediationAction,
        reward: float,
        next_state: Optional[State] = None
    ) -> float:
        """
        Update Q-values based on reward feedback
        
        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state (for Q-learning, None for bandit)
            
        Returns:
            TD error (for monitoring)
        """
        state_key = self._state_to_key(state)
        action_str = action.value
        
        # Get current Q-value
        current_q = self.q_table[state_key][action_str]
        
        if next_state is None:
            # Simple bandit update (no next state)
            target = reward
        else:
            # Q-learning update
            next_q_values = self._get_q_values(next_state)
            max_next_q = max(next_q_values.values())
            target = reward + self.discount_factor * max_next_q
        
        # TD error
        td_error = target - current_q
        
        # Update Q-value
        new_q = current_q + self.learning_rate * td_error
        self.q_table[state_key][action_str] = new_q
        
        self.update_count += 1
        
        logger.debug(
            f"Q-update: {action_str} | "
            f"Q: {current_q:.3f} -> {new_q:.3f} | "
            f"Reward: {reward:.3f} | "
            f"TD error: {td_error:.3f}"
        )
        
        return td_error
    
    def decay_epsilon(self) -> None:
        """Decay exploration rate"""
        old_epsilon = self.epsilon
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
        self.episode_count += 1
        
        # If epsilon hit minimum, log a warning
        if self.epsilon == self.min_epsilon and old_epsilon > self.min_epsilon:
            logger.warning(
                f"Epsilon reached minimum ({self.min_epsilon:.4f}). "
                f"Exploration rate is now {self.min_epsilon*100:.1f}%. "
                f"Consider increasing RL_MIN_EPSILON for continued learning."
            )
        
        if self.episode_count % 10 == 0:
            logger.info(f"Episode {self.episode_count}: epsilon = {self.epsilon:.4f}")
    
    def get_best_action(self, state: State) -> Tuple[RemediationAction, float]:
        """
        Get best action for state (pure exploitation)
        
        Args:
            state: Current state
            
        Returns:
            (best_action, q_value)
        """
        q_values = self._get_q_values(state)
        best_action, best_q = max(q_values.items(), key=lambda x: x[1])
        
        return RemediationAction(best_action), best_q
    
    def get_statistics(self) -> Dict:
        """Get training statistics"""
        return {
            "episode_count": self.episode_count,
            "update_count": self.update_count,
            "epsilon": self.epsilon,
            "num_states": len(self.q_table),
            "action_distribution": self.action_counts.copy(),
            "avg_q_value": np.mean([
                np.mean(list(q_vals.values()))
                for q_vals in self.q_table.values()
            ]) if self.q_table else 0.0
        }
    
    def save(self, filepath: Path) -> None:
        """
        Save agent to disk
        
        Args:
            filepath: Path to save file
        """
        state = {
            "q_table": self.q_table,
            "epsilon": self.epsilon,
            "episode_count": self.episode_count,
            "update_count": self.update_count,
            "action_counts": self.action_counts,
            "config": {
                "learning_rate": self.learning_rate,
                "epsilon_decay": self.epsilon_decay,
                "min_epsilon": self.min_epsilon,
                "discount_factor": self.discount_factor,
                "q_init": self.q_init
            }
        }
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(state, f)
        
        logger.info(f"Saved agent to {filepath}")
    
    @classmethod
    def load(cls, filepath: Path, actions: List[RemediationAction]) -> 'ContextualBandit':
        """
        Load agent from disk
        
        Args:
            filepath: Path to saved file
            actions: List of actions
            
        Returns:
            Loaded agent
        """
        with open(filepath, 'rb') as f:
            state = pickle.load(f)
        
        config = state['config']
        
        # Get current config's min_epsilon (may be updated)
        current_config = Config.get_rl_config()
        current_min_epsilon = current_config['min_epsilon']
        
        # Use current min_epsilon if it's higher (allows updating min_epsilon)
        min_epsilon = max(config['min_epsilon'], current_min_epsilon)
        
        # Ensure epsilon is at least min_epsilon
        loaded_epsilon = state['epsilon']
        if loaded_epsilon < min_epsilon:
            logger.info(
                f"Loaded epsilon ({loaded_epsilon:.4f}) is below current min_epsilon ({min_epsilon:.4f}). "
                f"Resetting epsilon to {min_epsilon:.4f} for continued exploration."
            )
            loaded_epsilon = min_epsilon
        
        agent = cls(
            actions=actions,
            learning_rate=config['learning_rate'],
            epsilon=loaded_epsilon,
            epsilon_decay=config['epsilon_decay'],
            min_epsilon=min_epsilon,
            discount_factor=config['discount_factor'],
            q_init=config['q_init']
        )
        
        agent.q_table = state['q_table']
        agent.episode_count = state['episode_count']
        agent.update_count = state['update_count']
        agent.action_counts = state['action_counts']
        
        logger.info(f"Loaded agent from {filepath}")
        logger.info(f"States: {len(agent.q_table)}, Episodes: {agent.episode_count}, Epsilon: {agent.epsilon:.4f}")
        
        return agent
    
    def reset_statistics(self) -> None:
        """Reset statistics but keep Q-table"""
        self.action_counts = {action: 0 for action in self.actions}
        logger.info("Reset statistics")
