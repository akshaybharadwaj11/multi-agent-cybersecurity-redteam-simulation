"""
Comprehensive Integration Tests for Cyber Defense Simulator
Tests end-to-end workflows and component integration
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.orchestrator import CyberDefenseOrchestrator
from core.data_models import (
    AttackType, SeverityLevel, RemediationAction, State
)
from cyber_defense_simulator.rag.vector_store import InMemoryVectorStore
from cyber_defense_simulator.rag.knowledge_base import KnowledgeBase
from cyber_defense_simulator.agents.red_team_agent import RedTeamAgent
from cyber_defense_simulator.agents.detection_agent import DetectionAgent
from cyber_defense_simulator.agents.rag_agent import RAGAgent
from cyber_defense_simulator.agents.remediation_agent import RemediationAgent
from cyber_defense_simulator.simulation.telemetry_generator import TelemetryGenerator
from cyber_defense_simulator.rl.contextual_bandit import ContextualBandit
from cyber_defense_simulator.rl.reward_calculator import RewardCalculator, simulate_outcome


class TestRedTeamAgent:
    """Test Red Team attack generation"""
    
    def test_attack_scenario_generation(self):
        """Test generating attack scenarios"""
        red_team = RedTeamAgent()
        
        scenario = red_team.generate_attack_scenario(
            scenario_id="test_001",
            attack_type=AttackType.PHISHING
        )
        
        assert scenario is not None
        assert scenario.scenario_id == "test_001"
        assert scenario.attack_type == AttackType.PHISHING
        assert len(scenario.steps) > 0
        assert all(step.technique_id.startswith("T") for step in scenario.steps)
    
    def test_multiple_attack_types(self):
        """Test generating different attack types"""
        red_team = RedTeamAgent()
        
        for attack_type in [AttackType.PHISHING, AttackType.LATERAL_MOVEMENT]:
            scenario = red_team.generate_attack_scenario(
                scenario_id=f"test_{attack_type.value}",
                attack_type=attack_type
            )
            
            assert scenario.attack_type == attack_type
            assert len(scenario.steps) >= 2


class TestTelemetryGenerator:
    """Test synthetic telemetry generation"""
    
    def test_telemetry_generation(self):
        """Test generating telemetry from attack"""
        red_team = RedTeamAgent()
        telemetry_gen = TelemetryGenerator(noise_level=0.2)
        
        scenario = red_team.generate_attack_scenario(
            scenario_id="test_telemetry",
            attack_type=AttackType.PHISHING
        )
        
        telemetry = telemetry_gen.generate_telemetry(scenario)
        
        assert telemetry is not None
        assert telemetry.scenario_id == scenario.scenario_id
        
        # Should have logs
        total_logs = (
            len(telemetry.system_logs) + len(telemetry.auth_logs) +
            len(telemetry.network_logs) + len(telemetry.process_logs)
        )
        assert total_logs > 0
    
    def test_noise_addition(self):
        """Test that benign noise is added"""
        red_team = RedTeamAgent()
        telemetry_gen = TelemetryGenerator(noise_level=0.5)
        
        scenario = red_team.generate_attack_scenario(
            scenario_id="test_noise",
            attack_type=AttackType.PHISHING
        )
        
        telemetry = telemetry_gen.generate_telemetry(scenario)
        
        # Check for benign logs
        benign_count = sum(
            1 for log in telemetry.system_logs
            if log.metadata.get('benign', False)
        )
        assert benign_count > 0


class TestDetectionAgent:
    """Test incident detection"""
    
    def test_incident_detection(self):
        """Test detecting incidents from telemetry"""
        red_team = RedTeamAgent()
        telemetry_gen = TelemetryGenerator()
        detection = DetectionAgent()
        
        # Generate attack and telemetry
        scenario = red_team.generate_attack_scenario(
            scenario_id="test_detection",
            attack_type=AttackType.CREDENTIAL_MISUSE
        )
        telemetry = telemetry_gen.generate_telemetry(scenario)
        
        # Detect incident
        incident = detection.detect_incident(telemetry, "incident_001")
        
        assert incident is not None
        assert incident.incident_id == "incident_001"
        assert incident.severity in list(SeverityLevel)
        assert 0.0 <= incident.confidence <= 1.0


class TestRAGAgent:
    """Test RAG retrieval"""
    
    @pytest.fixture
    def setup_rag(self):
        """Setup RAG with knowledge base"""
        vector_store = InMemoryVectorStore()
        kb = KnowledgeBase(vector_store)
        kb.initialize()
        rag_agent = RAGAgent(vector_store)
        return rag_agent
    
    def test_context_retrieval(self, setup_rag):
        """Test retrieving context for incident"""
        rag_agent = setup_rag
        
        # Create mock incident
        from core.data_models import IncidentReport, Anomaly
        
        incident = IncidentReport(
            incident_id="test_001",
            scenario_id="scenario_001",
            severity=SeverityLevel.HIGH,
            confidence=0.85,
            summary="Phishing attack detected",
            mitre_techniques=["T1566"],
            affected_assets=["workstation-1"]
        )
        
        context = rag_agent.retrieve_context(incident)
        
        assert context is not None
        assert context.incident_id == "test_001"
        # Should retrieve some runbooks
        assert len(context.runbooks) > 0


class TestRemediationAgent:
    """Test remediation planning"""
    
    def test_remediation_plan_generation(self):
        """Test generating remediation plan"""
        from core.data_models import IncidentReport, RAGContext
        
        remediation = RemediationAgent()
        
        incident = IncidentReport(
            incident_id="test_001",
            scenario_id="scenario_001",
            severity=SeverityLevel.CRITICAL,
            confidence=0.9,
            summary="Critical malware detected",
            mitre_techniques=["T1059"],
            affected_assets=["server-1"]
        )
        
        rag_context = RAGContext(incident_id="test_001")
        
        plan = remediation.generate_remediation_plan(incident, rag_context)
        
        assert plan is not None
        assert len(plan.options) > 0
        assert plan.recommended_action in list(RemediationAction)


class TestContextualBandit:
    """Test RL agent"""
    
    def test_action_selection(self):
        """Test selecting actions"""
        actions = [RemediationAction.BLOCK_IP, RemediationAction.ISOLATE_HOST]
        agent = ContextualBandit(actions=actions, epsilon=0.5)
        
        state = State(
            incident_severity=SeverityLevel.HIGH,
            attack_type=AttackType.PHISHING,
            confidence_level=0.8,
            num_affected_assets=2,
            mitre_techniques=["T1566"]
        )
        
        decision = agent.select_action(state)
        
        assert decision is not None
        assert decision.selected_action in actions
        assert 0.0 <= decision.epsilon <= 1.0
    
    def test_q_learning_update(self):
        """Test Q-value updates"""
        actions = [RemediationAction.BLOCK_IP, RemediationAction.ISOLATE_HOST]
        agent = ContextualBandit(actions=actions, learning_rate=0.1)
        
        state = State(
            incident_severity=SeverityLevel.MEDIUM,
            attack_type=AttackType.PHISHING,
            confidence_level=0.7,
            num_affected_assets=1,
            mitre_techniques=["T1566"]
        )
        
        # Initial decision
        decision = agent.select_action(state)
        initial_q = agent._get_q_values(state)[decision.selected_action.value]
        
        # Update with positive reward
        agent.update(state, decision.selected_action, reward=1.0)
        
        # Q-value should increase
        updated_q = agent._get_q_values(state)[decision.selected_action.value]
        assert updated_q > initial_q
    
    def test_epsilon_decay(self):
        """Test exploration rate decay"""
        actions = [RemediationAction.BLOCK_IP]
        agent = ContextualBandit(
            actions=actions,
            epsilon=1.0,
            epsilon_decay=0.9,
            min_epsilon=0.01
        )
        
        initial_epsilon = agent.epsilon
        
        # Decay multiple times
        for _ in range(10):
            agent.decay_epsilon()
        
        assert agent.epsilon < initial_epsilon
        assert agent.epsilon >= agent.min_epsilon


class TestRewardCalculator:
    """Test reward calculation"""
    
    def test_successful_outcome(self):
        """Test reward for successful containment"""
        calculator = RewardCalculator()
        
        from core.data_models import Outcome
        
        outcome = Outcome(
            incident_id="test_001",
            action_taken=RemediationAction.BLOCK_IP,
            success=True,
            false_positive=False,
            collateral_damage=False,
            attack_contained=True,
            time_to_remediate=10.0
        )
        
        feedback = calculator.calculate_reward(outcome)
        
        assert feedback.reward > 0  # Should be positive
        assert 'success' in feedback.components
    
    def test_failed_outcome(self):
        """Test reward for failed containment"""
        calculator = RewardCalculator()
        
        from core.data_models import Outcome
        
        outcome = Outcome(
            incident_id="test_001",
            action_taken=RemediationAction.NOTIFY_TEAM,
            success=False,
            false_positive=False,
            collateral_damage=False,
            attack_contained=False,
            time_to_remediate=15.0
        )
        
        feedback = calculator.calculate_reward(outcome)
        
        assert feedback.reward < 0  # Should be negative
        assert 'failure' in feedback.components


class TestOrchestrator:
    """Test end-to-end orchestration"""
    
    def test_single_episode(self):
        """Test running a single episode"""
        orchestrator = CyberDefenseOrchestrator(
            vector_store=InMemoryVectorStore(),
            initialize_kb=True
        )
        
        episode = orchestrator.run_episode(
            episode_number=1,
            attack_type=AttackType.PHISHING
        )
        
        # Verify episode completion
        assert episode is not None
        assert episode.episode_number == 1
        assert episode.attack_scenario is not None
        assert episode.telemetry is not None
        assert episode.incident_report is not None
        assert episode.rl_decision is not None
        assert episode.outcome is not None
        assert episode.reward is not None
    
    def test_multiple_episodes(self):
        """Test running multiple episodes"""
        orchestrator = CyberDefenseOrchestrator(
            vector_store=InMemoryVectorStore(),
            initialize_kb=True
        )
        
        metrics = orchestrator.run_simulation(num_episodes=3)
        
        assert metrics.total_episodes == 3
        assert len(orchestrator.episodes) == 3
        assert metrics.average_reward != 0
    
    def test_learning_progression(self):
        """Test that RL agent learns over time"""
        orchestrator = CyberDefenseOrchestrator(
            vector_store=InMemoryVectorStore(),
            initialize_kb=True
        )
        
        # Run episodes
        orchestrator.run_simulation(num_episodes=10)
        
        # Check that epsilon decreased
        rl_stats = orchestrator.rl_agent.get_statistics()
        assert rl_stats['epsilon'] < 0.1  # Should have decayed significantly
        
        # Check that Q-values were updated
        assert rl_stats['update_count'] > 0
        assert rl_stats['num_states'] > 0


class TestDataModels:
    """Test data models and validation"""
    
    def test_state_feature_vector(self):
        """Test state to feature vector conversion"""
        state = State(
            incident_severity=SeverityLevel.HIGH,
            attack_type=AttackType.PHISHING,
            confidence_level=0.8,
            num_affected_assets=3,
            mitre_techniques=["T1566", "T1059"]
        )
        
        features = state.to_feature_vector()
        
        assert len(features) == 5
        assert all(0.0 <= f <= 1.0 for f in features)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
