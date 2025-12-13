"""
ULTRA IMPROVED RL - Aggressive Fix for Learning
This version has MUCH clearer signals and better exploration
"""

import logging
from typing import Dict, List
import random
import numpy as np
import pickle
from pathlib import Path

from cyber_defense_simulator.core.data_models import (
        State, RemediationAction, RLDecision, 
        Outcome, RewardFeedback
        )

from cyber_defense_simulator.core.config import Config

logger = logging.getLogger(__name__)


def simulate_outcome(
    action_taken: str,
    incident_severity: str,
    attack_type: str,
    confidence: float
) -> Outcome:
    """
    ULTRA CLEAR outcome simulation
    
    Key changes:
    1. MUCH higher base success rates (70-95%)
    2. Only a few actions are clearly bad
    3. Most reasonable actions work decently
    """
    
    # Actions that are CLEARLY BAD for any high-severity incident
    SLOW_ACTIONS = [
        RemediationAction.NOTIFY_TEAM.value,
        RemediationAction.SCAN_SYSTEM.value
    ]
    
    # Actions that are GOOD for high-severity incidents
    FAST_ACTIONS = [
        RemediationAction.BLOCK_IP.value,
        RemediationAction.ISOLATE_HOST.value,
        RemediationAction.KILL_PROCESS.value,
        RemediationAction.LOCK_ACCOUNT.value,
        RemediationAction.QUARANTINE_FILE.value,
        RemediationAction.RESET_CREDENTIALS.value
    ]
    
    # Base success probability - MUCH HIGHER
    if incident_severity in ["critical", "high"]:
        if action_taken in SLOW_ACTIONS:
            # CLEARLY BAD - too slow
            success_prob = 0.20
        elif action_taken in FAST_ACTIONS:
            # GOOD - fast action
            success_prob = 0.85
        else:
            success_prob = 0.70
    else:  # medium or low severity
        if action_taken in SLOW_ACTIONS:
            # OK for low severity
            success_prob = 0.75
        else:
            success_prob = 0.80
    
    # Small adjustments for confidence (but not too much)
    if confidence < 0.5:
        success_prob *= 0.9
    else:
        success_prob *= 1.05
    
    # Clamp
    success_prob = max(0.15, min(0.95, success_prob))
    
    # Determine success
    success = random.random() < success_prob
    
    # Minimal false positives
    false_positive = not success and confidence < 0.5 and random.random() < 0.1
    
    # Minimal collateral damage
    collateral_damage = success and random.random() < 0.05
    
    # Response time
    if action_taken in SLOW_ACTIONS:
        time_to_remediate = random.uniform(15, 30)
    else:
        time_to_remediate = random.uniform(3, 12)
    
    if success:
        time_to_remediate *= 0.8
    
    outcome = Outcome(
        incident_id="simulated",
        action_taken=RemediationAction(action_taken),
        success=success,
        false_positive=false_positive,
        collateral_damage=collateral_damage,
        attack_contained=success,
        time_to_remediate=time_to_remediate
    )
    
    logger.info(
        f"Outcome: {attack_type}({incident_severity}) + {action_taken} "
        f"= {'✅SUCCESS' if success else '❌FAIL'} (p={success_prob:.2f})"
    )
    
    return outcome


class ContextualBandit:
    """
    Contextual Bandit with aggressive exploration
    """
    
    def __init__(self, actions, **kwargs):
        """Initialize with VERY aggressive parameters"""
        self.actions = [action.value for action in actions]
        
        # AGGRESSIVE PARAMETERS
        self.learning_rate = 0.5  # VERY high - learn fast!
        self.epsilon = 0.4  # VERY high - explore a lot!
        self.initial_epsilon = 0.4
        self.epsilon_decay = 0.99  # VERY slow decay
        self.min_epsilon = 0.15  # HIGHER minimum
        self.q_init = 0.7  # VERY optimistic
        self.discount_factor = 0.95  # For compatibility (not used in bandit, but API expects it)
        
        self.q_table: Dict[str, Dict[str, float]] = {}
        self.episode_count = 0
        self.update_count = 0
        self.action_counts: Dict[str, int] = {action: 0 for action in self.actions}
        self.state_visit_counts: Dict[str, int] = {}
        
        logger.info(
            f"ContextualBandit: LR={self.learning_rate}, "
            f"ε={self.epsilon}, Q_init={self.q_init}"
        )
    
    def _state_to_key(self, state: State) -> str:
        """SIMPLIFIED state - just severity and attack type"""
        severity_map = {
            "low": "low",
            "medium": "medium", 
            "high": "high",
            "critical": "high"
        }
        simple_severity = severity_map.get(state.incident_severity.value, "high")
        return f"{simple_severity}_{state.attack_type.value}"
    
    def _get_q_values(self, state: State) -> Dict[str, float]:
        """Get Q-values with VERY optimistic initialization"""
        state_key = self._state_to_key(state)
        
        if state_key not in self.q_table:
            # Initialize ALL actions optimistically
            self.q_table[state_key] = {
                action: self.q_init for action in self.actions
            }
            self.state_visit_counts[state_key] = 0
            logger.info(f"New state: {state_key} (Q_init={self.q_init})")
        
        self.state_visit_counts[state_key] += 1
        return self.q_table[state_key]
    
    def select_action(self, state: State) -> RLDecision:
        """
        UCB-style selection for better exploration
        """
        q_values = self._get_q_values(state)
        state_key = self._state_to_key(state)
        
        # Use epsilon-greedy with UCB bonus
        if random.random() < self.epsilon:
            # EXPLORE: Random action
            selected_action = random.choice(self.actions)
            is_exploration = True
        else:
            # EXPLOIT: Best action with exploration bonus
            total_visits = self.state_visit_counts[state_key]
            
            # Add exploration bonus for rarely-tried actions
            ucb_values = {}
            for action in self.actions:
                q_val = q_values[action]
                action_visits = self.action_counts.get(action, 0)
                
                # UCB bonus: sqrt(log(total) / (visits + 1))
                if total_visits > 0:
                    bonus = 0.3 * np.sqrt(np.log(total_visits + 1) / (action_visits + 1))
                else:
                    bonus = 0.3
                
                ucb_values[action] = q_val + bonus
            
            selected_action = max(ucb_values, key=ucb_values.get)
            is_exploration = False
        
        self.action_counts[selected_action] += 1
        
        decision = RLDecision(
            state=state,
            selected_action=RemediationAction(selected_action),
            q_values=q_values.copy(),
            epsilon=self.epsilon,
            is_exploration=is_exploration
        )
        
        logger.info(
            f"State: {state_key} | Action: {selected_action} | "
            f"Q: {q_values[selected_action]:.3f} | "
            f"Mode: {'🎲explore' if is_exploration else '🎯exploit'}"
        )
        
        return decision
    
    def update(self, state: State, action: RemediationAction, 
               reward: float, next_state=None) -> float:
        """Update with HIGH learning rate"""
        state_key = self._state_to_key(state)
        action_str = action.value
        
        current_q = self.q_table[state_key][action_str]
        
        # Simple update (no next state)
        target = reward
        td_error = target - current_q
        
        # AGGRESSIVE update
        new_q = current_q + self.learning_rate * td_error
        self.q_table[state_key][action_str] = new_q
        
        self.update_count += 1
        
        logger.info(
            f"Q-UPDATE: {state_key} + {action_str} | "
            f"{current_q:.3f} → {new_q:.3f} | "
            f"R={reward:.3f} | ΔQ={td_error:.3f}"
        )
        
        return td_error
    
    def decay_epsilon(self) -> None:
        """SLOW epsilon decay"""
        old_epsilon = self.epsilon
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
        self.episode_count += 1
        
        if self.episode_count % 5 == 0:
            logger.info(f"Episode {self.episode_count}: ε = {self.epsilon:.4f}")
    
    def get_statistics(self) -> Dict:
        """Get statistics"""
        return {
            "episode_count": self.episode_count,
            "update_count": self.update_count,
            "epsilon": self.epsilon,
            "num_states": len(self.q_table),
            "action_distribution": self.action_counts.copy(),
            "avg_q_value": np.mean([
                np.mean(list(q_vals.values()))
                for q_vals in self.q_table.values()
            ]) if self.q_table else 0.0,
            "max_q_value": np.max([
                max(q_vals.values())
                for q_vals in self.q_table.values()
            ]) if self.q_table else 0.0,
        }
    
    def print_q_table(self):
        """Print Q-table"""
        print("\n" + "="*80)
        print("Q-TABLE SUMMARY")
        print("="*80)
        
        for state_key in sorted(self.q_table.keys()):
            visits = self.state_visit_counts.get(state_key, 0)
            print(f"\nState: {state_key} (visited {visits} times)")
            q_values = self.q_table[state_key]
            
            sorted_actions = sorted(q_values.items(), key=lambda x: x[1], reverse=True)
            
            for i, (action, q_value) in enumerate(sorted_actions[:5]):
                marker = "⭐" if i == 0 else "  "
                tried = self.action_counts.get(action, 0)
                print(f"  {marker} {action:20s} Q={q_value:6.3f} (tried {tried}x)")
    
    def save(self, filepath: Path) -> None:
        """Save agent to disk"""
        state = {
            "q_table": self.q_table,
            "epsilon": self.epsilon,
            "episode_count": self.episode_count,
            "update_count": self.update_count,
            "action_counts": self.action_counts,
            "config": {
                "learning_rate": self.learning_rate,
                "initial_epsilon": self.initial_epsilon,
                "epsilon_decay": self.epsilon_decay,
                "min_epsilon": self.min_epsilon,
                "q_init": self.q_init,
                "discount_factor": self.discount_factor
            }
        }
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(state, f)
        
        logger.info(f"Saved agent to {filepath}")
    
    @classmethod
    def load(cls, filepath: Path, actions: List[RemediationAction]) -> 'ContextualBandit':
        """Load agent from disk"""
        with open(filepath, 'rb') as f:
            state = pickle.load(f)
        
        config = state['config']
        agent = cls(
            actions=actions,
            learning_rate=config['learning_rate'],
            epsilon=state['epsilon'],
            epsilon_decay=config['epsilon_decay'],
            min_epsilon=config['min_epsilon'],
            q_init=config['q_init']
        )
        
        # Set discount_factor if present in config, otherwise use default
        agent.discount_factor = config.get('discount_factor', 0.95)
        
        agent.q_table = state['q_table']
        agent.episode_count = state['episode_count']
        agent.update_count = state['update_count']
        agent.action_counts = state['action_counts']
        
        logger.info(f"Loaded agent from {filepath}")
        
        return agent


class RewardCalculator:
    """SIMPLE reward calculator"""
    
    def __init__(self):
        self.reward_success = 1.0
        self.reward_failure = -1.0
        self.time_penalty_factor = 0.01
    
    def calculate_reward(self, outcome: Outcome) -> RewardFeedback:
        """Simple, clear rewards"""
        components = {}
        
        if outcome.success:
            base_reward = self.reward_success
            components['success'] = base_reward
            
            # Big bonus for fast response
            if outcome.time_to_remediate < 10:
                speed_bonus = 0.5
                components['speed_bonus'] = speed_bonus
                base_reward += speed_bonus
        else:
            base_reward = self.reward_failure
            components['failure'] = base_reward
        
        # Small time penalty
        time_penalty = -self.time_penalty_factor * outcome.time_to_remediate
        total_reward = base_reward + time_penalty
        components['time_penalty'] = time_penalty
        
        feedback = RewardFeedback(
            outcome=outcome,
            reward=total_reward,
            components=components
        )
        
        logger.info(f"REWARD: {total_reward:.3f} ({'✅' if outcome.success else '❌'})")
        
        return feedback