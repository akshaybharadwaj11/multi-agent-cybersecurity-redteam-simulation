# 🛡️ Adaptive Red Team vs Blue Team Security Simulator

**Multi-Agent Cybersecurity Simulation with Reinforcement Learning**

An advanced cybersecurity simulation platform that uses CrewAI agents, RAG (Retrieval-Augmented Generation), and Reinforcement Learning to model realistic cyberattack scenarios and adaptive defense strategies.

## 🌟 Features

### Core Capabilities

- **🔴 Red Team Agent**: Generates realistic multi-stage cyberattack scenarios using MITRE ATT&CK framework
- **🔵 Blue Team Detection**: LLM-powered incident detection and analysis from synthetic telemetry
- **📚 RAG System**: Retrieves relevant security runbooks, threat intelligence, and past incidents
- **💡 Remediation Engine**: AI-driven action recommendations grounded in security best practices
- **🤖 RL Optimization**: Contextual bandit learns optimal defense strategies through experience
- **📊 Comprehensive Dashboard**: Real-time visualization of simulation results and learning progress

### Technical Highlights

- **Multi-Agent Orchestration**: Seamless coordination between Red Team, Detection, RAG, and Remediation agents
- **MITRE ATT&CK Integration**: Authentic technique mapping and realistic attack chains
- **Synthetic Telemetry**: Generates system, authentication, network, and process logs
- **Explainable AI**: Full audit trail of decisions, evidence, and justifications
- **Production-Ready**: Type-safe (Pydantic), well-tested, and modular architecture

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Cyber Defense Orchestrator                  │
└─────────────────────────────────────────────────────────────────┘
           │                                              │
           ▼                                              ▼
┌──────────────────────┐                      ┌──────────────────────┐
│   Red Team Agent     │                      │  Detection Agent     │
│  (Attack Generation) │──► Telemetry ───────►│ (Incident Analysis)  │
└──────────────────────┘    Generator         └──────────────────────┘
                                                         │
                                                         ▼
                                              ┌──────────────────────┐
                                              │     RAG Agent        │
                                              │ (Context Retrieval)  │
                                              └──────────────────────┘
                                                         │
                                                         ▼
                                              ┌──────────────────────┐
                                              │ Remediation Agent    │
                                              │ (Action Planning)    │
                                              └──────────────────────┘
                                                         │
                                                         ▼
                                              ┌──────────────────────┐
                                              │   RL Policy Agent    │
                                              │ (Action Selection)   │
                                              └──────────────────────┘
                                                         │
                                                         ▼
                                              ┌──────────────────────┐
                                              │  Reward Calculator   │
                                              │  (Feedback Loop)     │
                                              └──────────────────────┘
```

## 📋 Prerequisites

- Python 3.9+
- OpenAI API key
- 4GB RAM minimum
- pip or conda for package management

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd cyber_defense_simulator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Initialize Project Structure

```bash
# Run structure setup
python project_structure.py
```

### 3. Run Quick Demo

```bash
# Run 5-episode demo
python main.py --quick-test
```

### 4. Run Full Simulation

```bash
# Run 50 episodes with all attack types
python main.py --episodes 50

# Run specific attack types
python main.py --episodes 30 --attack-types phishing lateral_movement

# Enable verbose logging
python main.py --episodes 20 --verbose
```

### 5. Launch Dashboard

```bash
# Start interactive dashboard
streamlit run dashboard/app.py
```

## 📊 Understanding the Results

### Metrics Tracked

- **Success Rate**: Percentage of successfully contained attacks
- **Detection Rate**: Percentage of incidents detected with high confidence
- **Average Reward**: Mean reward across all episodes (higher = better)
- **Action Distribution**: Which remediation actions the RL agent prefers
- **Learning Progress**: Reward improvement over time

### Interpretation

**Good Performance Indicators:**
- Success rate > 70%
- Average reward increasing over time
- Diverse action distribution (not stuck on one action)
- Detection rate > 80%

**Signs of Learning:**
- Reward moving average trending upward
- Epsilon decreasing (less exploration)
- Q-values stabilizing
- Action selection becoming more deterministic

## 🔧 Configuration

Edit `.env` or `core/config.py`:

```python
# LLM Configuration
LLM_MODEL=gpt-4-turbo-preview  # or gpt-3.5-turbo for faster/cheaper
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# RL Configuration
RL_LEARNING_RATE=0.1
RL_EPSILON=0.1                 # Initial exploration rate
RL_EPSILON_DECAY=0.995
RL_DISCOUNT_FACTOR=0.95

# Reward Function
REWARD_SUCCESS=1.0
REWARD_FAILURE=-1.0
REWARD_FALSE_POSITIVE=-0.5
REWARD_COLLATERAL_DAMAGE=-0.3

# Simulation
NUM_EPISODES=100
MAX_STEPS_PER_EPISODE=20
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_integration.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run fast tests only (skip slow)
pytest tests/ -m "not slow"
```

## 📁 Project Structure

```
cyber_defense_simulator/
├── agents/                    # CrewAI agents
│   ├── red_team_agent.py     # Attack generation
│   ├── detection_agent.py    # Incident detection
│   ├── rag_agent.py          # Context retrieval
│   └── remediation_agent.py  # Action planning
├── core/                      # Core logic
│   ├── data_models.py        # Pydantic models
│   ├── config.py             # Configuration
│   └── orchestrator.py       # Multi-agent coordination
├── rag/                       # RAG system
│   ├── vector_store.py       # ChromaDB integration
│   ├── knowledge_base.py     # Security knowledge
│   └── embeddings.py         # Embedding generation
├── rl/                        # Reinforcement learning
│   ├── contextual_bandit.py  # RL policy
│   └── reward_calculator.py  # Reward function
├── simulation/                # Attack simulation
│   ├── telemetry_generator.py # Log generation
│   └── environment.py        # Simulated environment
├── dashboard/                 # Streamlit dashboard
│   └── app.py
├── tests/                     # Test suite
│   ├── test_agents.py
│   ├── test_rag.py
│   ├── test_rl.py
│   └── test_integration.py
└── main.py                    # Entry point
```

## 🎯 Attack Types Supported

1. **Phishing**: Spearphishing emails with malicious attachments
2. **Credential Misuse**: Brute force, password spraying, stolen credentials
3. **Lateral Movement**: RDP, SMB, credential dumping
4. **Data Exfiltration**: File collection, DNS tunneling, unauthorized uploads
5. **Malware Execution**: Script execution, persistence mechanisms

## 🛠️ Remediation Actions

- **BLOCK_IP**: Block source IP addresses at firewall
- **LOCK_ACCOUNT**: Lock compromised user accounts
- **KILL_PROCESS**: Terminate malicious processes
- **ISOLATE_HOST**: Isolate affected hosts from network
- **NOTIFY_TEAM**: Alert security team for manual review
- **SCAN_SYSTEM**: Run antivirus/EDR scan
- **RESET_CREDENTIALS**: Force password reset
- **QUARANTINE_FILE**: Quarantine malicious files

## 🤝 Contributing

Contributions welcome! Areas for enhancement:

- Additional attack types (ransomware, supply chain)
- More sophisticated RL algorithms (DQN, PPO)
- Real-world integration capabilities
- Advanced visualization features
- Performance optimizations

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- **MITRE ATT&CK**: Framework for adversary tactics and techniques
- **CrewAI**: Multi-agent orchestration framework
- **OpenAI**: LLM capabilities for reasoning
- **ChromaDB**: Vector database for RAG

## 📚 References

- [MITRE ATT&CK Framework](https://attack.mitre.org/)
- [CrewAI Documentation](https://docs.crewai.com/)
- [Reinforcement Learning: An Introduction](http://incompleteideas.net/book/the-book-2nd.html)
- [RAG Pattern Documentation](https://python.langchain.com/docs/use_cases/question_answering/)

## 💬 Support

For questions, issues, or feedback:
- Open an issue on GitHub
- Check existing issues for solutions
- Review documentation in `/docs`

## 🔮 Future Roadmap

- [ ] Advanced RL algorithms (Deep Q-Networks, Actor-Critic)
- [ ] Real-time data stream integration
- [ ] Adversarial agent improvements
- [ ] Multi-environment support
- [ ] Custom attack scenario builder
- [ ] Export to SIEM formats
- [ ] Collaborative defense scenarios
- [ ] Performance benchmarking suite

---
