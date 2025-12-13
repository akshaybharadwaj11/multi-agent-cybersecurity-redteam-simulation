"""
Multi-Agent Orchestrator
Coordinates all agents, RL policy, and simulation flow
"""

import logging
from typing import Optional, List
from pathlib import Path
import json
from datetime import datetime
import uuid

from crewai import Crew

from cyber_defense_simulator.core.data_models import (
    Episode, AttackScenario, AttackType, State, SimulationMetrics,
    RemediationAction, Outcome
)
from cyber_defense_simulator.core.config import Config

# Import agents
from cyber_defense_simulator.agents.red_team_agent import RedTeamAgent
from cyber_defense_simulator.agents.detection_agent import DetectionAgent
from cyber_defense_simulator.agents.rag_agent import RAGAgent
from cyber_defense_simulator.agents.remediation_agent import RemediationAgent

# Import RL components
from cyber_defense_simulator.rl.contextual_bandit import ContextualBandit
from cyber_defense_simulator.rl.reward_calculator import RewardCalculator, simulate_outcome

# Import RAG
from cyber_defense_simulator.rag.vector_store import VectorStore
from cyber_defense_simulator.rag.knowledge_base import initialize_knowledge_base

# Import telemetry
from cyber_defense_simulator.simulation.telemetry_generator import TelemetryGenerator

logger = logging.getLogger(__name__)


class CyberDefenseOrchestrator:
    """
    Orchestrates the entire cyber defense simulation
    
    Workflow:
    1. Red Team generates attack
    2. Telemetry generator creates logs
    3. Detection agent analyzes telemetry
    4. RAG agent retrieves context
    5. Remediation agent recommends actions
    6. RL agent selects action
    7. Simulate outcome and calculate reward
    8. Update RL policy
    """
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        initialize_kb: bool = True
    ):
        """
        Initialize orchestrator
        
        Args:
            vector_store: Optional vector store (creates new if None)
            initialize_kb: Whether to initialize knowledge base
        """
        logger.info("Initializing Cyber Defense Orchestrator...")
        
        # Validate API key
        if not Config.OPENAI_API_KEY or Config.OPENAI_API_KEY == "your_openai_api_key_here":
            raise ValueError(
                "OPENAI_API_KEY is required. Please set it in .env file.\n"
                "Create a .env file with: OPENAI_API_KEY=sk-your-key-here"
            )
        
        # Initialize vector store and knowledge base
        if vector_store is None:
            self.vector_store = VectorStore()
        else:
            self.vector_store = vector_store
        
        if initialize_kb:
            logger.info("Initializing knowledge base...")
            try:
                self.knowledge_base = initialize_knowledge_base(self.vector_store)
            except Exception as e:
                logger.warning(f"Knowledge base initialization failed: {e}. Continuing without KB.")
                self.knowledge_base = None
        
        # Initialize agents
        self.red_team = RedTeamAgent()
        self.detection = DetectionAgent()
        self.rag = RAGAgent(self.vector_store)
        self.remediation = RemediationAgent()
        
        # Initialize RL agent
        all_actions = list(RemediationAction)
        self.rl_agent = ContextualBandit(actions=all_actions)
        
        # Initialize reward calculator
        self.reward_calculator = RewardCalculator()
        
        # Initialize telemetry generator
        self.telemetry_generator = TelemetryGenerator(noise_level=0.3)
        
        # Metrics tracking
        self.episodes: List[Episode] = []
        self.metrics = SimulationMetrics(
            total_episodes=0,
            successful_defenses=0,
            failed_defenses=0,
            false_positives=0,
            average_reward=0.0,
            average_time_to_remediate=0.0,
            detection_rate=0.0
        )
        
        logger.info("Orchestrator initialized successfully")
    
    def run_episode(
        self,
        episode_number: int,
        attack_type: Optional[AttackType] = None
    ) -> Episode:
        """
        Run a single simulation episode
        
        Args:
            episode_number: Episode number
            attack_type: Optional attack type (random if None)
            
        Returns:
            Completed Episode
        """
        episode_id = f"episode_{episode_number}_{uuid.uuid4().hex[:8]}"
        logger.info(f"\n{'='*80}")
        logger.info(f"Starting Episode {episode_number}: {episode_id}")
        logger.info(f"{'='*80}")
        
        episode = Episode(
            episode_id=episode_id,
            episode_number=episode_number,
            attack_scenario=None,
            telemetry=None
        )
        
        try:
            # Step 1: Red Team - Generate attack
            logger.info("\n[1/7] Red Team: Generating attack scenario...")
            scenario_id = f"scenario_{episode_number}"
            attack_scenario = self.red_team.generate_attack_scenario(
                scenario_id=scenario_id,
                attack_type=attack_type
            )
            episode.attack_scenario = attack_scenario
            logger.info(f"✓ Generated {attack_scenario.attack_type.value} attack with {len(attack_scenario.steps)} steps")
            
            # Step 2: Generate telemetry
            logger.info("\n[2/7] Telemetry: Generating synthetic logs...")
            telemetry = self.telemetry_generator.generate_telemetry(attack_scenario)
            episode.telemetry = telemetry
            total_logs = (
                len(telemetry.system_logs) + len(telemetry.auth_logs) +
                len(telemetry.network_logs) + len(telemetry.process_logs)
            )
            logger.info(f"✓ Generated {total_logs} log entries")
            
            # Step 3: Detection - Analyze telemetry
            logger.info("\n[3/7] Detection: Analyzing telemetry for incidents...")
            incident_id = f"incident_{episode_number}"
            incident_report = self.detection.detect_incident(telemetry, incident_id)
            episode.incident_report = incident_report
            logger.info(
                f"✓ Incident detected: {incident_report.severity.value} severity, "
                f"{incident_report.confidence:.2f} confidence"
            )
            
            # Step 4: RAG - Retrieve context
            logger.info("\n[4/7] RAG: Retrieving threat intelligence and runbooks...")
            try:
                rag_context = self.rag.retrieve_context(incident_report)
                episode.rag_context = rag_context
                logger.info(
                    f"✓ Retrieved {len(rag_context.runbooks)} runbooks, "
                    f"{len(rag_context.threat_intel)} threat intel items, "
                    f"{len(rag_context.similar_incidents)} similar incidents"
                )
            except Exception as e:
                logger.warning(f"RAG retrieval encountered issues: {e}. Using fallback context.")
                # Create minimal RAG context - RAG agent should handle this, but double-check
                from cyber_defense_simulator.core.data_models import RAGContext
                rag_context = RAGContext(incident_id=incident_report.incident_id)
                
                # Ensure we have at least some context
                if not rag_context.runbooks and incident_report.mitre_techniques:
                    from cyber_defense_simulator.core.data_models import Runbook, ThreatIntelligence
                    # Add fallback runbook for each technique
                    for technique in incident_report.mitre_techniques:
                        rag_context.runbooks.append(Runbook(
                            runbook_id=f"fallback_{technique}",
                            title=f"Security Response for {technique}",
                            description=f"Standard security response procedures for MITRE technique {technique}",
                            applicable_techniques=[technique],
                            procedures=[
                                "1. Isolate affected systems",
                                "2. Block malicious IP addresses",
                                "3. Lock compromised accounts",
                                "4. Scan for additional threats",
                                "5. Notify security team"
                            ],
                            prerequisites=[],
                            expected_outcomes=["Threat contained", "Systems secured"]
                        ))
                    
                    # Add fallback threat intel
                    rag_context.threat_intel.append(ThreatIntelligence(
                        source="MITRE ATT&CK Framework",
                        content=f"Threat intelligence for techniques: {', '.join(incident_report.mitre_techniques)}",
                        relevance_score=0.7,
                        metadata={"type": "fallback"}
                    ))
                
                episode.rag_context = rag_context
                logger.info(f"✓ Created fallback RAG context with {len(rag_context.runbooks)} runbooks")
            
            # Step 5: Remediation - Generate action options
            logger.info("\n[5/7] Remediation: Generating action recommendations...")
            remediation_plan = self.remediation.generate_remediation_plan(
                incident_report,
                rag_context
            )
            episode.remediation_plan = remediation_plan
            logger.info(
                f"✓ Generated {len(remediation_plan.options)} remediation options"
            )
            
            # Step 6: RL - Select action
            logger.info("\n[6/7] RL Agent: Selecting optimal action...")
            state = self._create_state(incident_report, attack_scenario)
            rl_decision = self.rl_agent.select_action(state)
            episode.rl_decision = rl_decision
            logger.info(
                f"✓ Selected action: {rl_decision.selected_action.value} "
                f"({'exploration' if rl_decision.is_exploration else 'exploitation'})"
            )
            
            # Step 7: Simulate outcome and calculate reward
            logger.info("\n[7/7] Simulation: Executing action and computing reward...")
            outcome = simulate_outcome(
                action_taken=rl_decision.selected_action.value,
                incident_severity=incident_report.severity.value,
                attack_type=attack_scenario.attack_type.value,
                confidence=incident_report.confidence
            )
            outcome.incident_id = incident_id
            episode.outcome = outcome
            
            reward_feedback = self.reward_calculator.calculate_reward(outcome)
            episode.reward = reward_feedback
            
            logger.info(
                f"✓ Outcome: {'Success' if outcome.success else 'Failure'}, "
                f"Reward: {reward_feedback.reward:.3f}"
            )
            
            # Step 8: Update RL agent
            self.rl_agent.update(
                state=state,
                action=rl_decision.selected_action,
                reward=reward_feedback.reward
            )
            
            # Update metrics
            self._update_metrics(episode)
            
            # Mark episode complete
            episode.end_time = datetime.now()
            episode.total_duration = (
                episode.end_time - episode.start_time
            ).total_seconds()
            
            self.episodes.append(episode)
            
            logger.info(f"\n{'='*80}")
            logger.info(f"Episode {episode_number} completed in {episode.total_duration:.2f}s")
            logger.info(f"{'='*80}\n")
            
            return episode
            
        except Exception as e:
            logger.error(f"Error in episode {episode_number}: {e}", exc_info=True)
            # Don't let one episode failure stop the entire simulation
            # Create minimal episode record to continue
            # Ensure episode has minimum required data
            if episode:
                # If episode is missing critical data, try to create minimal valid episode
                if episode.attack_scenario is None:
                    logger.warning("Episode missing attack scenario, creating minimal scenario")
                    from cyber_defense_simulator.core.data_models import AttackScenario, AttackStep
                    episode.attack_scenario = AttackScenario(
                        scenario_id=f"error_scenario_{episode_number}",
                        attack_type=AttackType.PHISHING,
                        attacker_profile="unknown",
                        target_asset="unknown",
                        steps=[AttackStep(
                            step_number=1,
                            technique_id="T1059",
                            technique_name="Command Execution",
                            description="Error occurred during attack generation",
                            indicators=[]
                        )]
                    )
                
                if episode.telemetry is None:
                    logger.warning("Episode missing telemetry, creating minimal telemetry")
                    from cyber_defense_simulator.core.data_models import TelemetryData
                    episode.telemetry = TelemetryData(
                        scenario_id=episode.attack_scenario.scenario_id if episode.attack_scenario else f"scenario_{episode_number}"
                    )
                
                episode.end_time = datetime.now()
                if episode.start_time:
                    episode.total_duration = (episode.end_time - episode.start_time).total_seconds()
                
                # Try to create minimal incident report if missing
                if episode.incident_report is None:
                    logger.warning("Creating minimal incident report for failed episode")
                    from cyber_defense_simulator.core.data_models import IncidentReport, SeverityLevel
                    episode.incident_report = IncidentReport(
                        incident_id=f"incident_{episode_number}",
                        scenario_id=episode.attack_scenario.scenario_id if episode.attack_scenario else f"scenario_{episode_number}",
                        severity=SeverityLevel.LOW,
                        confidence=0.3,
                        summary="Episode encountered errors during execution"
                    )
                
                # Ensure we have at least minimal RAG context
                if episode.rag_context is None and episode.incident_report:
                    from cyber_defense_simulator.core.data_models import RAGContext, Runbook
                    episode.rag_context = RAGContext(incident_id=episode.incident_report.incident_id)
                    episode.rag_context.runbooks.append(Runbook(
                        runbook_id="fallback",
                        title="General Security Response",
                        description="Standard security response procedures",
                        applicable_techniques=["T1059"],
                        procedures=["Isolate systems", "Block IPs", "Lock accounts"],
                        prerequisites=[],
                        expected_outcomes=[]
                    ))
                
                # Add to episodes list even if incomplete
                self.episodes.append(episode)
            
            return episode
    
    def train_rl_agent(
        self,
        num_training_episodes: int = 20,
        attack_types: Optional[List[AttackType]] = None
    ) -> None:
        """
        Train the RL agent on initial episodes
        
        Args:
            num_training_episodes: Number of training episodes
            attack_types: Optional list of attack types for training
        """
        logger.info(f"\n{'#'*80}")
        logger.info(f"🤖 Training RL Agent: {num_training_episodes} episodes")
        logger.info(f"{'#'*80}\n")
        
        # Reset metrics for training
        training_episodes = []
        
        for i in range(num_training_episodes):
            # Select attack type
            attack_type = None
            if attack_types:
                attack_type = attack_types[i % len(attack_types)]
            
            # Run training episode
            episode = self.run_episode(i + 1, attack_type)
            training_episodes.append(episode)
            
            # Decay epsilon for exploration
            self.rl_agent.decay_epsilon()
            
            # Log progress every 5 episodes
            if (i + 1) % 5 == 0:
                rl_stats = self.rl_agent.get_statistics()
                logger.info(f"Training Progress: Episode {i+1}/{num_training_episodes}")
                logger.info(f"  Epsilon: {rl_stats['epsilon']:.4f}, States: {rl_stats['num_states']}")
        
        logger.info(f"\n✅ Training complete! RL agent trained on {num_training_episodes} episodes")
        rl_stats = self.rl_agent.get_statistics()
        logger.info(f"   Final epsilon: {rl_stats['epsilon']:.4f}")
        logger.info(f"   States explored: {rl_stats['num_states']}")
        logger.info(f"   Q-value updates: {rl_stats['update_count']}")
    
    def run_simulation(
        self,
        num_episodes: int = None,
        attack_types: Optional[List[AttackType]] = None
    ) -> SimulationMetrics:
        """
        Run full simulation for multiple episodes
        Training happens automatically in the backend based on episode count
        
        Args:
            num_episodes: Total number of episodes (includes training)
            attack_types: Optional list of attack types to cycle through
            
        Returns:
            Final simulation metrics
        """
        if num_episodes is None:
            num_episodes = Config.NUM_EPISODES
        
        # Automatic training phase (backend only)
        # Use 20% of episodes for training, minimum 3, maximum 20
        training_episodes = max(3, min(20, int(num_episodes * 0.2)))
        simulation_episodes = num_episodes - training_episodes
        
        if training_episodes > 0 and simulation_episodes > 0:
            logger.info(f"\n🤖 Automatic Training Phase: {training_episodes} episodes (backend)")
            self.train_rl_agent(
                num_training_episodes=training_episodes,
                attack_types=attack_types
            )
            logger.info("\n" + "="*80)
            logger.info(f"Training complete. Starting main simulation: {simulation_episodes} episodes...")
            logger.info("="*80 + "\n")
            
            # Reset metrics for main simulation (keep RL agent state)
            self.metrics = SimulationMetrics(
                total_episodes=0,
                successful_defenses=0,
                failed_defenses=0,
                false_positives=0,
                average_reward=0.0,
                average_time_to_remediate=0.0,
                detection_rate=0.0
            )
            self.episodes = []  # Clear training episodes
            
            # Use remaining episodes for simulation
            num_episodes = simulation_episodes
        
        logger.info(f"\n{'#'*80}")
        logger.info(f"Starting Simulation: {num_episodes} episodes")
        logger.info(f"{'#'*80}\n")
        
        successful_episodes = 0
        failed_episodes = 0
        
        for i in range(num_episodes):
            # Select attack type
            attack_type = None
            if attack_types:
                attack_type = attack_types[i % len(attack_types)]
            
            # Run episode
            try:
                episode = self.run_episode(i + 1, attack_type)
                
                # Check if episode completed successfully
                if episode and episode.attack_scenario and episode.telemetry and episode.incident_report and episode.outcome:
                    successful_episodes += 1
                    # Only update RL if we have a valid outcome
                    if episode.reward:
                        # RL update already happened in run_episode, just verify
                        pass
                else:
                    failed_episodes += 1
                    logger.warning(f"Episode {i+1} completed with missing data - continuing simulation")
            except Exception as e:
                failed_episodes += 1
                logger.error(f"Episode {i+1} failed: {e}. Continuing with next episode...")
                # Continue simulation even if episode fails
            
            # Decay epsilon for RL exploration (always, even on failure)
            self.rl_agent.decay_epsilon()
            
            # Log progress every 5 episodes (more frequent for visibility)
            if (i + 1) % 5 == 0:
                self._log_progress()
                logger.info(f"Progress: {successful_episodes} successful, {failed_episodes} failed out of {i+1} total")
        
        logger.info(f"\n{'#'*80}")
        logger.info("Simulation Complete!")
        logger.info(f"{'#'*80}\n")
        
        self._log_final_metrics()
        
        return self.metrics
    
    def _create_state(
        self,
        incident_report,
        attack_scenario
    ) -> State:
        """Create RL state from incident and scenario"""
        return State(
            incident_severity=incident_report.severity,
            attack_type=attack_scenario.attack_type,
            confidence_level=incident_report.confidence,
            num_affected_assets=len(incident_report.affected_assets) or 1,
            mitre_techniques=incident_report.mitre_techniques
        )
    
    def _update_metrics(self, episode: Episode) -> None:
        """Update simulation metrics"""
        self.metrics.total_episodes += 1
        
        if episode.outcome:
            if episode.outcome.success:
                self.metrics.successful_defenses += 1
            else:
                self.metrics.failed_defenses += 1
            
            if episode.outcome.false_positive:
                self.metrics.false_positives += 1
        
        if episode.reward:
            self.metrics.reward_history.append(episode.reward.reward)
            self.metrics.average_reward = sum(self.metrics.reward_history) / len(self.metrics.reward_history)
        
        if episode.rl_decision:
            action = episode.rl_decision.selected_action.value
            self.metrics.action_distribution[action] = self.metrics.action_distribution.get(action, 0) + 1
        
        # Detection rate
        if episode.incident_report and episode.incident_report.confidence > 0.5:
            detected = sum(1 for e in self.episodes if e.incident_report and e.incident_report.confidence > 0.5)
            self.metrics.detection_rate = detected / self.metrics.total_episodes
    
    def _log_progress(self) -> None:
        """Log current progress"""
        logger.info("\n" + "="*80)
        logger.info("Progress Update")
        logger.info("="*80)
        logger.info(f"Episodes: {self.metrics.total_episodes}")
        if self.metrics.total_episodes > 0:
            logger.info(f"Success Rate: {self.metrics.successful_defenses / self.metrics.total_episodes:.2%}")
            logger.info(f"Detection Rate: {self.metrics.detection_rate:.2%}")
        logger.info(f"Average Reward: {self.metrics.average_reward:.3f}")
        logger.info(f"Epsilon: {self.rl_agent.epsilon:.4f}")
        logger.info("="*80 + "\n")
    
    def _log_final_metrics(self) -> None:
        """Log final simulation metrics"""
        logger.info("\nFinal Metrics:")
        logger.info(f"Total Episodes: {self.metrics.total_episodes}")
        logger.info(f"Successful Defenses: {self.metrics.successful_defenses}")
        logger.info(f"Failed Defenses: {self.metrics.failed_defenses}")
        logger.info(f"False Positives: {self.metrics.false_positives}")
        
        if self.metrics.total_episodes > 0:
            logger.info(f"Success Rate: {self.metrics.successful_defenses / self.metrics.total_episodes:.2%}")
            logger.info(f"Detection Rate: {self.metrics.detection_rate:.2%}")
        else:
            logger.warning("No episodes completed successfully")
        
        logger.info(f"Average Reward: {self.metrics.average_reward:.3f}")
        logger.info(f"\nAction Distribution:")
        for action, count in sorted(self.metrics.action_distribution.items()):
            pct = count / self.metrics.total_episodes
            logger.info(f"  {action}: {count} ({pct:.1%})")
        
        # RL statistics
        rl_stats = self.rl_agent.get_statistics()
        logger.info(f"\nRL Agent Statistics:")
        logger.info(f"  States Explored: {rl_stats['num_states']}")
        logger.info(f"  Updates: {rl_stats['update_count']}")
        logger.info(f"  Final Epsilon: {rl_stats['epsilon']:.4f}")
        logger.info(f"  Average Q-value: {rl_stats['avg_q_value']:.3f}")
    
    def save_results(self, output_dir: Path) -> None:
        """
        Save simulation results
        
        Args:
            output_dir: Directory to save results
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save metrics
        metrics_file = output_dir / "metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(self.metrics.dict(), f, indent=2, default=str)
        
        # Save RL agent
        agent_file = output_dir / "rl_agent.pkl"
        self.rl_agent.save(agent_file)
        
        # Save episode summaries
        episodes_file = output_dir / "episodes.json"
        episodes_data = [
            {
                "episode_id": e.episode_id,
                "attack_type": e.attack_scenario.attack_type.value if e.attack_scenario else None,
                "severity": e.incident_report.severity.value if e.incident_report else None,
                "action_taken": e.rl_decision.selected_action.value if e.rl_decision else None,
                "success": e.outcome.success if e.outcome else None,
                "reward": e.reward.reward if e.reward else None
            }
            for e in self.episodes
        ]
        with open(episodes_file, 'w') as f:
            json.dump(episodes_data, f, indent=2)
        
        logger.info(f"Results saved to {output_dir}")
