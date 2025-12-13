"""
Reward Function for RL Agent
Calculates rewards based on remediation outcomes
"""

import logging
from typing import Dict

from cyber_defense_simulator.core.data_models import Outcome, RewardFeedback
from cyber_defense_simulator.core.config import Config

logger = logging.getLogger(__name__)


class RewardCalculator:
    """
    Calculates rewards for RL agent based on remediation outcomes
    
    Reward components:
    - Success bonus: +1.0 if attack contained
    - Failure penalty: -1.0 if attack succeeded
    - False positive penalty: -0.5 if no real threat
    - Collateral damage penalty: -0.3 if legitimate services affected
    - Time penalty: Small penalty for slow response
    """
    
    def __init__(
        self,
        reward_success: float = None,
        reward_failure: float = None,
        reward_false_positive: float = None,
        reward_collateral_damage: float = None,
        reward_uncertainty: float = None,
        time_penalty_factor: float = 0.01
    ):
        """
        Initialize reward calculator
        
        Args:
            reward_success: Reward for successful containment
            reward_failure: Penalty for failed containment
            reward_false_positive: Penalty for false positive
            reward_collateral_damage: Penalty for collateral damage
            reward_uncertainty: Reward for uncertain outcomes
            time_penalty_factor: Penalty per minute of response time
        """
        config = Config.get_reward_config()
        
        self.reward_success = reward_success or config['success']
        self.reward_failure = reward_failure or config['failure']
        self.reward_false_positive = reward_false_positive or config['false_positive']
        self.reward_collateral_damage = reward_collateral_damage or config['collateral_damage']
        self.reward_uncertainty = reward_uncertainty or config['uncertainty']
        self.time_penalty_factor = time_penalty_factor
        
        logger.info("Initialized RewardCalculator")
        logger.info(f"Success: {self.reward_success}, Failure: {self.reward_failure}")
    
    def calculate_reward(self, outcome: Outcome) -> RewardFeedback:
        """
        Calculate reward based on outcome
        
        Improved reward shaping:
        - Higher rewards for successful containment
        - Reduced penalties for failures (to encourage exploration)
        - Bonus for fast response times
        - Penalty scaling based on severity
        
        Args:
            outcome: Outcome of remediation action
            
        Returns:
            RewardFeedback with total reward and components
        """
        components = {}
        
        # Base reward based on primary outcome
        if outcome.false_positive:
            # False alarm - penalize but not as much as failure
            base_reward = self.reward_false_positive
            components['false_positive'] = base_reward
            
        elif outcome.success and outcome.attack_contained:
            # Successful containment - maximum reward (increased for better learning)
            base_reward = self.reward_success
            components['success'] = base_reward
            
            # Bonus for fast response (encourage quick action)
            if outcome.time_to_remediate < 10.0:
                speed_bonus = self.reward_success * 0.2 * (1.0 - outcome.time_to_remediate / 10.0)
                base_reward += speed_bonus
                components['speed_bonus'] = speed_bonus
            
        elif not outcome.success:
            # Failed to stop attack - penalty (reduced for better exploration)
            base_reward = self.reward_failure
            components['failure'] = base_reward
            
        else:
            # Uncertain outcome
            base_reward = self.reward_uncertainty
            components['uncertainty'] = base_reward
        
        # Additional penalties
        total_reward = base_reward
        
        # Collateral damage penalty (reduced)
        if outcome.collateral_damage:
            damage_penalty = self.reward_collateral_damage
            total_reward += damage_penalty
            components['collateral_damage'] = damage_penalty
        
        # Time penalty (encourage faster response, but minimal)
        time_penalty = -self.time_penalty_factor * outcome.time_to_remediate
        total_reward += time_penalty
        components['time_penalty'] = time_penalty
        
        # Create feedback
        feedback = RewardFeedback(
            outcome=outcome,
            reward=total_reward,
            components=components
        )
        
        logger.debug(
            f"Reward: {total_reward:.3f} | "
            f"Success: {outcome.success} | "
            f"FP: {outcome.false_positive} | "
            f"Collateral: {outcome.collateral_damage}"
        )
        
        return feedback
    
    def get_reward_breakdown(self, feedback: RewardFeedback) -> str:
        """
        Get human-readable reward breakdown
        
        Args:
            feedback: RewardFeedback object
            
        Returns:
            Formatted string explaining reward
        """
        lines = [f"Total Reward: {feedback.reward:.3f}"]
        lines.append("\nComponents:")
        
        for component, value in feedback.components.items():
            lines.append(f"  {component}: {value:.3f}")
        
        return "\n".join(lines)
    
    def compute_expected_reward(
        self,
        success_prob: float,
        false_positive_prob: float = 0.0,
        collateral_damage_prob: float = 0.0,
        avg_time: float = 10.0
    ) -> float:
        """
        Compute expected reward for decision analysis
        
        Args:
            success_prob: Probability of success
            false_positive_prob: Probability of false positive
            collateral_damage_prob: Probability of collateral damage
            avg_time: Average time to remediate
            
        Returns:
            Expected reward value
        """
        expected = 0.0
        
        # Success case
        expected += success_prob * self.reward_success
        
        # Failure case
        expected += (1 - success_prob - false_positive_prob) * self.reward_failure
        
        # False positive case
        expected += false_positive_prob * self.reward_false_positive
        
        # Collateral damage
        expected += collateral_damage_prob * self.reward_collateral_damage
        
        # Time penalty
        expected += -self.time_penalty_factor * avg_time
        
        return expected


def simulate_outcome(
    action_taken: str,
    incident_severity: str,
    attack_type: str,
    confidence: float
) -> Outcome:
    """
    Simulate outcome based on action and context
    
    IMPROVED: More realistic and action-appropriate outcome simulation
    - Better action-appropriateness matching
    - Higher success rates for appropriate actions
    - More deterministic outcomes for better learning
    
    Args:
        action_taken: Remediation action
        incident_severity: Severity level
        attack_type: Type of attack
        confidence: Detection confidence
        
    Returns:
        Simulated outcome
    """
    import random
    from cyber_defense_simulator.core.data_models import RemediationAction, AttackType
    
    # Action-appropriateness matrix (higher = better match)
    action_effectiveness = {
        # For network-based attacks (PHISHING, DATA_EXFILTRATION)
        AttackType.PHISHING.value: {
            RemediationAction.BLOCK_IP.value: 0.85,
            RemediationAction.ISOLATE_HOST.value: 0.75,
            RemediationAction.LOCK_ACCOUNT.value: 0.80,
            RemediationAction.NOTIFY_TEAM.value: 0.60,
            RemediationAction.SCAN_SYSTEM.value: 0.50,
            RemediationAction.QUARANTINE_FILE.value: 0.55,
            RemediationAction.KILL_PROCESS.value: 0.45,
            RemediationAction.RESET_CREDENTIALS.value: 0.70,
        },
        AttackType.DATA_EXFILTRATION.value: {
            RemediationAction.BLOCK_IP.value: 0.90,
            RemediationAction.ISOLATE_HOST.value: 0.85,
            RemediationAction.LOCK_ACCOUNT.value: 0.70,
            RemediationAction.NOTIFY_TEAM.value: 0.65,
            RemediationAction.SCAN_SYSTEM.value: 0.55,
            RemediationAction.QUARANTINE_FILE.value: 0.60,
            RemediationAction.KILL_PROCESS.value: 0.50,
            RemediationAction.RESET_CREDENTIALS.value: 0.65,
        },
        # For credential-based attacks
        AttackType.CREDENTIAL_MISUSE.value: {
            RemediationAction.LOCK_ACCOUNT.value: 0.90,
            RemediationAction.RESET_CREDENTIALS.value: 0.85,
            RemediationAction.BLOCK_IP.value: 0.70,
            RemediationAction.ISOLATE_HOST.value: 0.75,
            RemediationAction.NOTIFY_TEAM.value: 0.65,
            RemediationAction.SCAN_SYSTEM.value: 0.50,
            RemediationAction.QUARANTINE_FILE.value: 0.45,
            RemediationAction.KILL_PROCESS.value: 0.40,
        },
        # For malware/execution attacks
        AttackType.MALWARE_EXECUTION.value: {
            RemediationAction.QUARANTINE_FILE.value: 0.90,
            RemediationAction.KILL_PROCESS.value: 0.85,
            RemediationAction.ISOLATE_HOST.value: 0.80,
            RemediationAction.SCAN_SYSTEM.value: 0.75,
            RemediationAction.BLOCK_IP.value: 0.70,
            RemediationAction.NOTIFY_TEAM.value: 0.60,
            RemediationAction.LOCK_ACCOUNT.value: 0.50,
            RemediationAction.RESET_CREDENTIALS.value: 0.45,
        },
        # For lateral movement
        AttackType.LATERAL_MOVEMENT.value: {
            RemediationAction.ISOLATE_HOST.value: 0.90,
            RemediationAction.BLOCK_IP.value: 0.85,
            RemediationAction.LOCK_ACCOUNT.value: 0.80,
            RemediationAction.SCAN_SYSTEM.value: 0.70,
            RemediationAction.NOTIFY_TEAM.value: 0.65,
            RemediationAction.QUARANTINE_FILE.value: 0.55,
            RemediationAction.KILL_PROCESS.value: 0.60,
            RemediationAction.RESET_CREDENTIALS.value: 0.50,
        },
        # For privilege escalation
        AttackType.PRIVILEGE_ESCALATION.value: {
            RemediationAction.LOCK_ACCOUNT.value: 0.90,
            RemediationAction.ISOLATE_HOST.value: 0.85,
            RemediationAction.RESET_CREDENTIALS.value: 0.80,
            RemediationAction.KILL_PROCESS.value: 0.75,
            RemediationAction.BLOCK_IP.value: 0.70,
            RemediationAction.SCAN_SYSTEM.value: 0.65,
            RemediationAction.NOTIFY_TEAM.value: 0.60,
            RemediationAction.QUARANTINE_FILE.value: 0.50,
        },
    }
    
    # Get base success probability from action-appropriateness
    base_success = action_effectiveness.get(
        attack_type,
        {action: 0.60 for action in [a.value for a in RemediationAction]}
    ).get(action_taken, 0.60)
    
    # Adjust based on severity (higher severity = harder to contain)
    severity_multiplier = {
        "low": 1.0,
        "medium": 0.95,
        "high": 0.85,
        "critical": 0.75
    }
    success_prob = base_success * severity_multiplier.get(incident_severity, 0.85)
    
    # Adjust based on confidence (higher confidence = better outcomes)
    # Confidence acts as a multiplier (0.5 confidence = 0.5x, 1.0 confidence = 1.0x)
    confidence_adjusted = 0.5 + (confidence * 0.5)  # Map [0,1] to [0.5, 1.0]
    success_prob *= confidence_adjusted
    
    # Cap success probability between 0.3 and 0.95 (always some uncertainty)
    success_prob = max(0.30, min(0.95, success_prob))
    
    # Determine outcome with some noise
    noise = random.gauss(0, 0.05)  # Small Gaussian noise
    success_prob_noisy = max(0.0, min(1.0, success_prob + noise))
    success = random.random() < success_prob_noisy
    
    # False positive: only if low confidence AND not successful
    false_positive = not success and confidence < 0.5 and random.random() < (0.5 - confidence)
    
    # Collateral damage: more likely with aggressive actions, less likely with appropriate ones
    aggressive_actions = [
        RemediationAction.ISOLATE_HOST.value,
        RemediationAction.KILL_PROCESS.value,
        RemediationAction.BLOCK_IP.value
    ]
    collateral_prob = 0.15 if action_taken in aggressive_actions else 0.05
    collateral_damage = success and random.random() < collateral_prob
    
    # Attack contained if successful
    attack_contained = success
    
    # Response time: faster for appropriate actions, slower for inappropriate ones
    base_time = 10.0 if action_taken in aggressive_actions else 15.0
    time_multiplier = 1.0 if base_success > 0.75 else 1.5  # Slower for inappropriate actions
    time_to_remediate = random.uniform(
        base_time * time_multiplier * 0.7,
        base_time * time_multiplier * 1.5
    )
    
    outcome = Outcome(
        incident_id="simulated",
        action_taken=RemediationAction(action_taken),
        success=success,
        false_positive=false_positive,
        collateral_damage=collateral_damage,
        attack_contained=attack_contained,
        time_to_remediate=time_to_remediate
    )
    
    return outcome
