# DiagramGPT Architecture Diagram Prompt

Generate a comprehensive architecture diagram for an **Adaptive Red Team vs Blue Team Security Simulator** - a multi-agent cybersecurity simulation system with Reinforcement Learning.

## System Overview
This is a multi-agent cybersecurity simulation platform that models realistic cyberattack scenarios and adaptive defense strategies. The system uses CrewAI agents, RAG (Retrieval-Augmented Generation), and Reinforcement Learning to simulate and learn from cyber defense scenarios.

## Architecture Components

### 1. **Frontend Layer (React Dashboard)**
- React-based web UI with real-time dashboards
- Components: Dashboard, Simulations, Analytics, RL Metrics, Agent Orchestration views
- Connects to FastAPI backend via REST API

### 2. **Backend API Layer (FastAPI Server)**
- FastAPI REST API server (`api_server.py`)
- Endpoints for: simulations, episodes, agent logs, RL metrics, dashboard stats
- Handles background simulation execution
- CORS-enabled for frontend access

### 3. **Core Orchestration Layer**
- **CyberDefenseOrchestrator** (main coordinator)
  - Coordinates all agents and components
  - Manages simulation episodes
  - Tracks metrics and results

### 4. **Multi-Agent System (CrewAI Framework)**

#### **Red Team Agent**
- Role: Attack scenario generation
- Generates realistic multi-stage cyberattacks
- Uses MITRE ATT&CK framework
- Creates attack scenarios with steps, techniques, and indicators
- Output: AttackScenario (with AttackStep sequences)

#### **Telemetry Generator**
- Converts attack scenarios into synthetic logs
- Generates: system logs, auth logs, network logs, process logs
- Adds realistic noise to simulate normal operations
- Output: TelemetryData

#### **Detection Agent**
- Analyzes telemetry for security incidents
- Uses LLM to identify anomalies and threats
- Classifies severity (low, medium, high, critical)
- Output: IncidentReport with confidence scores

#### **RAG Agent (Retrieval-Augmented Generation)**
- Retrieves relevant security knowledge
- Queries vector store (ChromaDB) for:
  - Security runbooks
  - Threat intelligence
  - Similar past incidents
- Uses semantic search via embeddings
- Output: RAGContext (runbooks, threat intel, similar incidents)

#### **Remediation Agent**
- Generates remediation action recommendations
- Considers incident details and RAG context
- Evaluates multiple action options
- Output: RemediationPlan (with multiple RemediationOption)

#### **RL Agent (Contextual Bandit)**
- Reinforcement Learning agent for action selection
- Uses epsilon-greedy policy with Q-learning
- Learns optimal actions based on state and rewards
- State features: severity, attack type, confidence, affected assets
- Actions: BLOCK_IP, LOCK_ACCOUNT, KILL_PROCESS, ISOLATE_HOST, NOTIFY_TEAM, SCAN_SYSTEM, RESET_CREDENTIALS, QUARANTINE_FILE
- Output: RLDecision (selected action, Q-values, exploration/exploitation flag)

#### **Reward Calculator**
- Simulates outcome of taken action
- Calculates reward signal for RL agent
- Considers: success/failure, false positives, collateral damage
- Updates RL agent Q-values

### 5. **RAG System (Knowledge Base)**

#### **Vector Store (ChromaDB)**
- Persistent vector database
- Stores embeddings of security documents
- Supports similarity search

#### **Embedding Generator**
- Converts text to vector embeddings
- Uses OpenAI embeddings API

#### **Knowledge Base**
- Contains: security runbooks, MITRE ATT&CK techniques, CVE data, threat intelligence
- Initialized from data files (runbooks, MITRE attack data)

### 6. **Data Models (Pydantic)**
- Type-safe data structures:
  - AttackScenario, AttackStep, AttackType
  - TelemetryData, LogEntry
  - IncidentReport, Anomaly
  - RAGContext, Runbook, ThreatIntelligence
  - RemediationPlan, RemediationOption
  - State, RLDecision, Outcome, RewardFeedback
  - Episode, SimulationMetrics

### 7. **External Services**
- **OpenAI API**: LLM capabilities (GPT models) for agents
- **ChromaDB**: Vector database for RAG

## Data Flow (Episode Execution)

1. **Episode Start** → Orchestrator initiates
2. **Red Team** → Generates AttackScenario (multi-step attack)
3. **Telemetry Generator** → Converts attack to synthetic logs (TelemetryData)
4. **Detection Agent** → Analyzes telemetry → Creates IncidentReport
5. **RAG Agent** → Queries vector store → Retrieves RAGContext (runbooks, threat intel)
6. **Remediation Agent** → Generates RemediationPlan (action options)
7. **RL Agent** → Selects action from state (State → RLDecision)
8. **Reward Calculator** → Simulates outcome → Calculates reward
9. **RL Update** → Updates Q-values based on reward
10. **Episode End** → Results saved, metrics updated

## Key Relationships

- **Orchestrator** → Coordinates all agents sequentially
- **Agents** → Use CrewAI framework with OpenAI LLM
- **RAG Agent** → Queries VectorStore (ChromaDB)
- **RL Agent** → Receives State, selects Action, receives Reward
- **VectorStore** → Stores embeddings, retrieves via similarity search
- **FastAPI** → Exposes REST endpoints to React frontend
- **Frontend** → Displays real-time simulation data and metrics

## Technology Stack

- **Multi-Agent**: CrewAI
- **LLM**: OpenAI GPT (configurable model)
- **Vector DB**: ChromaDB (persistent)
- **RL**: Contextual Bandit (epsilon-greedy Q-learning)
- **Backend**: FastAPI (Python)
- **Frontend**: React + Vite
- **Data Validation**: Pydantic
- **Embeddings**: OpenAI Embeddings API

## Visual Layout Suggestions

- Show Frontend (React) at the top
- Show Backend API (FastAPI) below frontend
- Show Orchestrator in center as main coordinator
- Show agent flow horizontally: Red Team → Telemetry → Detection → RAG → Remediation → RL
- Show RAG System (VectorStore + Knowledge Base) connected to RAG Agent
- Show Reward Calculator connected to RL Agent (feedback loop)
- Show External Services (OpenAI, ChromaDB) on sides
- Use different colors/shapes for:
  - Agents (rectangles)
  - Data stores (cylinders)
  - External services (clouds)
  - Data flow (arrows)

## Special Features to Highlight

- **Feedback Loop**: RL agent learns from outcomes (reward → Q-value updates)
- **Multi-stage Attacks**: Red Team generates sequential attack steps
- **Context-Aware Decisions**: RAG provides relevant knowledge for remediation
- **Real-time Dashboard**: Frontend updates as simulations run
- **Learning System**: RL agent improves over episodes (epsilon decay, Q-value learning)

Please create a comprehensive architecture diagram showing all these components, their relationships, and data flow with clear labels and logical grouping.

