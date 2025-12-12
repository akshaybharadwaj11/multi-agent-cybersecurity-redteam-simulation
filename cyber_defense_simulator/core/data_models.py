"""
Data Models for Cyber Defense Simulator
Pydantic models for type safety and validation
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime
from enum import Enum
from typing import Any, Dict
from pydantic import BaseModel, Field
from typing import Literal

# ============================================================================
# Enums
# ============================================================================

class AttackType(str, Enum):
    PHISHING = "phishing"
    CREDENTIAL_MISUSE = "credential_misuse"
    LATERAL_MOVEMENT = "lateral_movement"
    DATA_EXFILTRATION = "data_exfiltration"
    MALWARE_EXECUTION = "malware_execution"
    PRIVILEGE_ESCALATION = "privilege_escalation"

class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RemediationAction(str, Enum):
    BLOCK_IP = "block_ip"
    LOCK_ACCOUNT = "lock_account"
    KILL_PROCESS = "kill_process"
    ISOLATE_HOST = "isolate_host"
    NOTIFY_TEAM = "notify_team"
    SCAN_SYSTEM = "scan_system"
    RESET_CREDENTIALS = "reset_credentials"
    QUARANTINE_FILE = "quarantine_file"

# ============================================================================
# Attack Models
# ============================================================================

class AttackStep(BaseModel):
    """Individual step in an attack chain"""
    step_number: int = Field(..., description="Sequential step number")
    technique_id: str = Field(..., description="MITRE ATT&CK technique ID")
    technique_name: str = Field(..., description="Human-readable technique name")
    description: str = Field(..., description="What the attacker does")
    timestamp: datetime = Field(default_factory=datetime.now)
    indicators: List[str] = Field(default_factory=list, description="Observable indicators")
    
class AttackScenario(BaseModel):
    """Complete attack scenario with multiple steps"""
    scenario_id: str = Field(..., description="Unique scenario identifier")
    attack_type: AttackType
    attacker_profile: str = Field(..., description="Attacker sophistication level")
    target_asset: str = Field(..., description="Primary target asset")
    steps: List[AttackStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    success_probability: float = Field(default=0.5, ge=0.0, le=1.0)

# ============================================================================
# Telemetry Models
# ============================================================================

class LogEntry(BaseModel):
    """Individual log entry"""
    timestamp: datetime
    source: str = Field(..., description="Log source (system, auth, network, etc.)")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TelemetryData(BaseModel):
    """Collection of telemetry from various sources"""
    scenario_id: str
    system_logs: List[LogEntry] = Field(default_factory=list)
    auth_logs: List[LogEntry] = Field(default_factory=list)
    network_logs: List[LogEntry] = Field(default_factory=list)
    process_logs: List[LogEntry] = Field(default_factory=list)
    collection_start: datetime = Field(default_factory=datetime.now)
    collection_end: Optional[datetime] = None

# ============================================================================
# Detection Models
# ============================================================================

class Anomaly(BaseModel):
    """Detected anomaly"""
    anomaly_type: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    description: str
    affected_entities: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)

class IncidentReport(BaseModel):
    """Structured incident report from detection agent"""
    incident_id: str
    scenario_id: str
    detected_at: datetime = Field(default_factory=datetime.now)
    severity: SeverityLevel
    confidence: float = Field(..., ge=0.0, le=1.0)
    summary: str = Field(..., description="Human-readable incident summary")
    anomalies: List[Anomaly] = Field(default_factory=list)
    mitre_techniques: List[str] = Field(default_factory=list)
    affected_assets: List[str] = Field(default_factory=list)
    timeline: List[Dict[str, Any]] = Field(default_factory=list)

# ============================================================================
# RAG Models
# ============================================================================

class ThreatIntelligence(BaseModel):
    """Retrieved threat intelligence"""
    source: str = Field(..., description="Source of intelligence")
    content: str = Field(..., description="Intelligence content")
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Runbook(BaseModel):
    """Security runbook"""
    runbook_id: str
    title: str
    description: str
    applicable_techniques: List[str] = Field(default_factory=list)
    procedures: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    expected_outcomes: List[str] = Field(default_factory=list)

class RAGContext(BaseModel):
    """Context retrieved from RAG system"""
    incident_id: str
    runbooks: List[Runbook] = Field(default_factory=list)
    threat_intel: List[ThreatIntelligence] = Field(default_factory=list)
    similar_incidents: List[Dict[str, Any]] = Field(default_factory=list)
    retrieved_at: datetime = Field(default_factory=datetime.now)

# ============================================================================
# Remediation Models
# ============================================================================

class RemediationOption(BaseModel):
    """Single remediation action option"""
    action: RemediationAction
    description: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    estimated_impact: str = Field(..., description="Expected impact on operations")
    risks: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    execution_steps: List[str] = Field(default_factory=list)

class RemediationPlan(BaseModel):
    """Complete remediation plan with multiple options"""
    incident_id: str
    options: List[RemediationOption] = Field(default_factory=list)
    recommended_action: Optional[RemediationAction] = None
    justification: str = Field(default="", description="Why this action is recommended")
    created_at: datetime = Field(default_factory=datetime.now)

# ============================================================================
# RL Models
# ============================================================================

class State(BaseModel):
    """RL state representation"""
    incident_severity: SeverityLevel
    attack_type: AttackType
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    num_affected_assets: int
    mitre_techniques: List[str] = Field(default_factory=list)
    
    def to_feature_vector(self) -> List[float]:
        """Convert state to feature vector for RL agent"""
        severity_map = {"low": 0.25, "medium": 0.5, "high": 0.75, "critical": 1.0}
        attack_type_map = {
            "phishing": 0, "credential_misuse": 1, "lateral_movement": 2,
            "data_exfiltration": 3, "malware_execution": 4, "privilege_escalation": 5
        }
        
        return [
            severity_map[self.incident_severity.value],
            attack_type_map[self.attack_type.value] / 5.0,
            self.confidence_level,
            min(self.num_affected_assets / 10.0, 1.0),
            len(self.mitre_techniques) / 5.0
        ]

class RLDecision(BaseModel):
    """RL agent's decision"""
    state: State
    selected_action: RemediationAction
    q_values: Dict[str, float] = Field(default_factory=dict)
    epsilon: float = Field(..., description="Exploration rate used")
    is_exploration: bool = Field(default=False)

class Outcome(BaseModel):
    """Result of taking an action"""
    incident_id: str
    action_taken: RemediationAction
    success: bool = Field(..., description="Was the attack stopped?")
    false_positive: bool = Field(default=False)
    collateral_damage: bool = Field(default=False)
    attack_contained: bool = Field(default=False)
    time_to_remediate: float = Field(..., description="Time taken in minutes")
    
class RewardFeedback(BaseModel):
    """Reward signal for RL agent"""
    outcome: Outcome
    reward: float = Field(..., description="Numerical reward")
    components: Dict[str, float] = Field(default_factory=dict, description="Reward breakdown")

# ============================================================================
# Orchestration Models
# ============================================================================

class Episode(BaseModel):
    """Single simulation episode"""
    episode_id: str
    episode_number: int
    attack_scenario: AttackScenario
    telemetry: TelemetryData
    incident_report: Optional[IncidentReport] = None
    rag_context: Optional[RAGContext] = None
    remediation_plan: Optional[RemediationPlan] = None
    rl_decision: Optional[RLDecision] = None
    outcome: Optional[Outcome] = None
    reward: Optional[RewardFeedback] = None
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_duration: Optional[float] = None

class SimulationMetrics(BaseModel):
    """Aggregate metrics across episodes"""
    total_episodes: int
    successful_defenses: int
    failed_defenses: int
    false_positives: int
    average_reward: float
    average_time_to_remediate: float
    detection_rate: float
    action_distribution: Dict[str, int] = Field(default_factory=dict)
    reward_history: List[float] = Field(default_factory=list)
