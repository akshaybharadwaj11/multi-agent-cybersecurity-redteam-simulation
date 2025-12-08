"""
CrewAI Agent Implementation for Red Team vs Blue Team
Integrates RL-trained agents with CrewAI orchestration
"""

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
import numpy as np
from typing import List, Dict
from ..rl.dqn import DQNAgent, get_action_name
from ..environments.cyber_env import CyberSecurityEnv


# ==================== CUSTOM TOOLS ====================

@tool("Attack Planner")
def plan_attack_sequence(current_state: str, target_info: str) -> str:
    """
    Plans optimal attack sequence based on current network state.
    Uses learned Q-values to recommend best actions.
    
    Args:
        current_state: Current network state description
        target_info: Information about target systems
    
    Returns:
        Recommended attack sequence
    """
    return f"Recommended: Reconnaissance → Exploit → Privilege Escalation → Persistence"


@tool("Vulnerability Database")
def query_vulnerability_db(service: str, version: str) -> str:
    """
    Queries vulnerability database for known exploits.
    
    Args:
        service: Service name (e.g., 'apache', 'ssh')
        version: Version number
    
    Returns:
        Known vulnerabilities and CVEs
    """
    # Simulate CVE lookup
    cves = {
        'apache': ['CVE-2021-44228', 'CVE-2021-41773'],
        'ssh': ['CVE-2020-15778', 'CVE-2021-28041']
    }
    return f"Found vulnerabilities: {cves.get(service, ['None known'])}"


@tool("Network Scanner")
def scan_network(target_range: str) -> str:
    """
    Performs network reconnaissance scan.
    
    Args:
        target_range: IP range to scan
    
    Returns:
        Discovered hosts and services
    """
    return f"Scan results: 15 hosts discovered, 42 open ports identified"


@tool("Threat Intelligence")
def query_threat_intel(indicator: str) -> str:
    """
    Queries threat intelligence feeds for IOCs.
    
    Args:
        indicator: IP, hash, or domain to investigate
    
    Returns:
        Threat intelligence report
    """
    return f"Threat score: 7/10. Known association with APT29. 3 recent campaigns."


@tool("SIEM Analyzer")
def analyze_siem_logs(time_range: str, filter_criteria: str) -> str:
    """
    Analyzes SIEM logs for security events.
    
    Args:
        time_range: Time window to analyze
        filter_criteria: Log filtering criteria
    
    Returns:
        Security events and anomalies
    """
    return f"Found 127 events: 5 high-severity alerts, 23 medium, 99 low"


@tool("Incident Response Playbook")
def execute_ir_playbook(incident_type: str, severity: str) -> str:
    """
    Executes incident response playbook.
    
    Args:
        incident_type: Type of security incident
        severity: Incident severity level
    
    Returns:
        Response actions taken
    """
    return f"Playbook executed: Isolated host, collected forensics, initiated containment"


# ==================== RED TEAM AGENTS ====================

class RLRedTeamAgent(Agent):
    """Red Team Agent with RL-based decision making"""
    
    def __init__(self, agent_role: str, dqn_agent: DQNAgent, *args, **kwargs):
        self.dqn_agent = dqn_agent
        self.agent_role = agent_role
        super().__init__(*args, **kwargs)
    
    def get_rl_action(self, state: np.ndarray) -> int:
        """Get action from trained RL agent"""
        return self.dqn_agent.select_action(state, evaluate=True)
    
    def get_action_explanation(self, state: np.ndarray, action: int) -> str:
        """Get human-readable explanation of RL decision"""
        q_values = self.dqn_agent.get_q_values(state)
        action_name = get_action_name(action, 'red')
        
        explanation = f"""
Action: {action_name}
Q-value: {q_values[action]:.3f}
Confidence: {(q_values[action] - q_values.min()) / (q_values.max() - q_values.min() + 1e-8):.2%}
Alternative actions considered:
"""
        # Show top 3 alternatives
        top_actions = np.argsort(q_values)[-3:][::-1]
        for alt_action in top_actions:
            if alt_action != action:
                explanation += f"  - {get_action_name(alt_action, 'red')}: {q_values[alt_action]:.3f}\n"
        
        return explanation


def create_red_team_agents(dqn_agents: List[DQNAgent]) -> List[Agent]:
    """Create specialized Red Team agents with RL capabilities"""
    
    agents = []
    
    # Attack Strategy Agent
    attack_strategist = RLRedTeamAgent(
        agent_role="Attack Strategist",
        dqn_agent=dqn_agents[0],
        role="Attack Strategy Coordinator",
        goal="Plan and coordinate sophisticated attack campaigns",
        backstory="""You are an elite penetration tester with 15 years of experience.
        You excel at identifying attack vectors and orchestrating multi-stage attacks.
        Your decisions are informed by deep reinforcement learning, having analyzed
        thousands of successful penetration tests.""",
        tools=[plan_attack_sequence, query_vulnerability_db],
        verbose=True,
        allow_delegation=True
    )
    agents.append(attack_strategist)
    
    # Reconnaissance Agent
    recon_agent = RLRedTeamAgent(
        agent_role="Reconnaissance Specialist",
        dqn_agent=dqn_agents[1],
        role="Reconnaissance and Intelligence Gathering",
        goal="Discover and map target infrastructure",
        backstory="""You specialize in OSINT and network reconnaissance.
        Through machine learning, you've learned to identify the most valuable
        targets and optimal scanning strategies.""",
        tools=[scan_network, query_vulnerability_db],
        verbose=True
    )
    agents.append(recon_agent)
    
    # Exploit Development Agent
    exploit_dev = RLRedTeamAgent(
        agent_role="Exploit Developer",
        dqn_agent=dqn_agents[2],
        role="Exploit Development and Execution",
        goal="Develop and execute exploits against identified vulnerabilities",
        backstory="""You are a master exploit developer who has reverse-engineered
        hundreds of vulnerabilities. Your RL training helps you select the most
        effective exploitation techniques.""",
        tools=[query_vulnerability_db],
        verbose=True
    )
    agents.append(exploit_dev)
    
    # Persistence Agent
    persistence_agent = RLRedTeamAgent(
        agent_role="Persistence Specialist",
        dqn_agent=dqn_agents[3],
        role="Persistence and Lateral Movement",
        goal="Maintain access and expand foothold in target network",
        backstory="""You specialize in maintaining persistent access and moving
        laterally through networks. Your RL training optimizes stealth and efficiency.""",
        tools=[],
        verbose=True
    )
    agents.append(persistence_agent)
    
    return agents


# ==================== BLUE TEAM AGENTS ====================

class RLBlueTeamAgent(Agent):
    """Blue Team Agent with RL-based decision making"""
    
    def __init__(self, agent_role: str, dqn_agent: DQNAgent, *args, **kwargs):
        self.dqn_agent = dqn_agent
        self.agent_role = agent_role
        super().__init__(*args, **kwargs)
    
    def get_rl_action(self, state: np.ndarray) -> int:
        """Get action from trained RL agent"""
        return self.dqn_agent.select_action(state, evaluate=True)
    
    def get_action_explanation(self, state: np.ndarray, action: int) -> str:
        """Get human-readable explanation of RL decision"""
        q_values = self.dqn_agent.get_q_values(state)
        action_name = get_action_name(action, 'blue')
        
        explanation = f"""
Action: {action_name}
Q-value: {q_values[action]:.3f}
Confidence: {(q_values[action] - q_values.min()) / (q_values.max() - q_values.min() + 1e-8):.2%}
Risk Level: {'HIGH' if q_values[action] > 0.5 else 'MEDIUM' if q_values[action] > 0 else 'LOW'}
"""
        return explanation


def create_blue_team_agents(dqn_agents: List[DQNAgent]) -> List[Agent]:
    """Create specialized Blue Team agents with RL capabilities"""
    
    agents = []
    
    # Threat Detection Agent
    threat_detector = RLBlueTeamAgent(
        agent_role="Threat Detector",
        dqn_agent=dqn_agents[0],
        role="Threat Detection and Analysis",
        goal="Detect and classify security threats in real-time",
        backstory="""You are a cybersecurity analyst with expertise in threat detection.
        Your RL training has exposed you to thousands of attack patterns, making you
        highly effective at identifying both known and novel threats.""",
        tools=[analyze_siem_logs, query_threat_intel],
        verbose=True,
        allow_delegation=True
    )
    agents.append(threat_detector)
    
    # Incident Response Agent
    incident_responder = RLBlueTeamAgent(
        agent_role="Incident Responder",
        dqn_agent=dqn_agents[1],
        role="Incident Response Coordinator",
        goal="Respond to and contain security incidents",
        backstory="""You are a seasoned incident responder who has handled hundreds
        of breaches. Your RL training optimizes response speed and effectiveness.""",
        tools=[execute_ir_playbook, analyze_siem_logs],
        verbose=True
    )
    agents.append(incident_responder)
    
    # Network Monitor Agent
    network_monitor = RLBlueTeamAgent(
        agent_role="Network Monitor",
        dqn_agent=dqn_agents[2],
        role="Network Traffic Analysis",
        goal="Monitor and analyze network traffic for anomalies",
        backstory="""You specialize in network security monitoring and traffic analysis.
        Through reinforcement learning, you've learned to distinguish between normal
        and malicious traffic patterns with high accuracy.""",
        tools=[analyze_siem_logs],
        verbose=True
    )
    agents.append(network_monitor)
    
    # Vulnerability Assessment Agent
    vuln_assessor = RLBlueTeamAgent(
        agent_role="Vulnerability Assessor",
        dqn_agent=dqn_agents[3],
        role="Vulnerability Assessment and Remediation",
        goal="Identify and prioritize vulnerabilities for patching",
        backstory="""You are a vulnerability management expert who understands
        how attackers think. Your RL training helps prioritize vulnerabilities
        based on real-world exploitation likelihood.""",
        tools=[query_vulnerability_db],
        verbose=True
    )
    agents.append(vuln_assessor)
    
    return agents


# ==================== ORCHESTRATOR ====================

class CyberSecurityOrchestrator:
    """
    Main orchestrator coordinating Red Team vs Blue Team
    Integrates RL agents with CrewAI framework
    """
    
    def __init__(
        self,
        red_agents: List[RLRedTeamAgent],
        blue_agents: List[RLBlueTeamAgent],
        environment: CyberSecurityEnv
    ):
        self.red_agents = red_agents
        self.blue_agents = blue_agents
        self.environment = environment
        self.simulation_history = []
        
    def create_red_team_tasks(self, state: np.ndarray) -> List[Task]:
        """Create tasks for red team based on current state"""
        tasks = []
        
        # Task 1: Reconnaissance
        recon_task = Task(
            description="""Perform comprehensive reconnaissance on the target network.
            Identify key assets, vulnerabilities, and potential entry points.
            Use your RL-trained decision making to prioritize targets.""",
            agent=self.red_agents[1],
            expected_output="Detailed reconnaissance report with prioritized targets"
        )
        tasks.append(recon_task)
        
        # Task 2: Attack Planning
        planning_task = Task(
            description="""Based on reconnaissance, plan a sophisticated attack campaign.
            Leverage your RL training to optimize attack sequences.
            Consider stealth, effectiveness, and probability of success.""",
            agent=self.red_agents[0],
            expected_output="Comprehensive attack plan with action sequences",
            context=[recon_task]
        )
        tasks.append(planning_task)
        
        # Task 3: Exploitation
        exploit_task = Task(
            description="""Execute the planned attacks. Use your RL-trained exploit
            selection to maximize success rate. Adapt strategy based on defenses.""",
            agent=self.red_agents[2],
            expected_output="Exploitation report with successful compromises",
            context=[planning_task]
        )
        tasks.append(exploit_task)
        
        # Task 4: Persistence
        persistence_task = Task(
            description="""Establish persistence and expand foothold.
            Use RL-optimized techniques for stealth and longevity.""",
            agent=self.red_agents[3],
            expected_output="Persistence mechanisms established",
            context=[exploit_task]
        )
        tasks.append(persistence_task)
        
        return tasks
    
    def create_blue_team_tasks(self, state: np.ndarray) -> List[Task]:
        """Create tasks for blue team based on current state"""
        tasks = []
        
        # Task 1: Threat Detection
        detection_task = Task(
            description="""Monitor network for suspicious activity.
            Use your RL-trained anomaly detection to identify threats.
            Analyze SIEM logs and threat intelligence.""",
            agent=self.blue_agents[0],
            expected_output="Threat assessment report with detected incidents"
        )
        tasks.append(detection_task)
        
        # Task 2: Incident Response
        response_task = Task(
            description="""Respond to detected threats.
            Use RL-optimized response strategies for containment.
            Prioritize critical assets and minimize damage.""",
            agent=self.blue_agents[1],
            expected_output="Incident response actions and containment status",
            context=[detection_task]
        )
        tasks.append(response_task)
        
        # Task 3: Network Hardening
        hardening_task = Task(
            description="""Analyze vulnerabilities and harden defenses.
            Use RL training to prioritize patching and security controls.""",
            agent=self.blue_agents[3],
            expected_output="Network hardening recommendations and actions",
            context=[detection_task, response_task]
        )
        tasks.append(hardening_task)
        
        return tasks
    
    def run_simulation(self, n_episodes: int = 1) -> Dict:
        """Run competitive simulation between teams"""
        results = {
            'red_team_success': [],
            'blue_team_success': [],
            'actions_taken': [],
            'final_states': []
        }
        
        for episode in range(n_episodes):
            print(f"\n{'='*60}")
            print(f"Episode {episode + 1}/{n_episodes}")
            print(f"{'='*60}\n")
            
            state, _ = self.environment.reset()
            
            # Create and execute red team crew
            print("🔴 RED TEAM OPERATIONS")
            red_tasks = self.create_red_team_tasks(state)
            red_crew = Crew(
                agents=self.red_agents,
                tasks=red_tasks,
                process=Process.sequential,
                verbose=True
            )
            red_result = red_crew.kickoff()
            
            # Get RL actions from red team
            red_actions = [agent.get_rl_action(state) for agent in self.red_agents]
            
            # Execute red actions in environment
            for action in red_actions:
                state, reward, done, _, info = self.environment.step_red(action)
            
            red_success = info['attack_success_rate']
            
            # Create and execute blue team crew
            print("\n🔵 BLUE TEAM OPERATIONS")
            blue_tasks = self.create_blue_team_tasks(state)
            blue_crew = Crew(
                agents=self.blue_agents,
                tasks=blue_tasks,
                process=Process.sequential,
                verbose=True
            )
            blue_result = blue_crew.kickoff()
            
            # Get RL actions from blue team
            blue_actions = [agent.get_rl_action(state) for agent in self.blue_agents]
            
            # Execute blue actions in environment
            for action in blue_actions:
                state, reward, done, _, info = self.environment.step_blue(action)
            
            blue_success = info['defense_success_rate']
            
            # Store results
            results['red_team_success'].append(red_success)
            results['blue_team_success'].append(blue_success)
            results['actions_taken'].append({
                'red': red_actions,
                'blue': blue_actions
            })
            results['final_states'].append(state)
            
            print(f"\nEpisode Results:")
            print(f"  Red Team Success: {red_success:.2%}")
            print(f"  Blue Team Success: {blue_success:.2%}")
            print(f"  Winner: {'Red Team' if red_success > blue_success else 'Blue Team' if blue_success > red_success else 'Draw'}")
        
        return results