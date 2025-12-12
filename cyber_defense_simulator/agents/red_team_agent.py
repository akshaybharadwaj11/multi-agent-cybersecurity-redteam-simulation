"""
Red Team Agent - Attack Scenario Generation
Generates realistic multi-stage cyberattack scenarios
"""

from crewai import Agent, Task
from typing import Dict, List
import json
import logging
from datetime import datetime, timedelta
import random

from core.data_models import AttackScenario, AttackStep, AttackType, TelemetryData, LogEntry
from core.config import Config

logger = logging.getLogger(__name__)


class RedTeamAgent:
    """Generates realistic cyberattack scenarios and telemetry"""
    
    def __init__(self):
        """Initialize Red Team agent"""
        self.agent = Agent(
            role="Red Team Operator",
            goal="Generate realistic cyberattack scenarios with multi-stage attack chains",
            backstory="""You are an experienced penetration tester and red team operator 
            with deep knowledge of MITRE ATT&CK framework. You specialize in crafting 
            realistic attack scenarios that mirror real-world adversary tactics, techniques, 
            and procedures (TTPs). Your scenarios help blue teams train and improve their 
            detection and response capabilities.""",
            verbose=Config.CREW_VERBOSE,
            allow_delegation=False,
            llm=Config.LLM_MODEL
        )
        
        logger.info("Initialized Red Team Agent")
    
    def create_attack_generation_task(self, attack_type: AttackType) -> Task:
        """
        Create task for generating attack scenario
        
        Args:
            attack_type: Type of attack to generate
            
        Returns:
            CrewAI Task
        """
        task = Task(
            description=f"""
            Generate a realistic {attack_type.value} attack scenario with the following:
            
            1. Attacker Profile: Define sophistication level (novice, intermediate, advanced, nation-state)
            2. Target Asset: Identify primary target (workstation, server, database, network device)
            3. Attack Chain: Create 3-5 sequential steps following MITRE ATT&CK framework
            
            For each attack step, provide:
            - MITRE ATT&CK technique ID and name
            - Detailed description of what attacker does
            - Observable indicators (IPs, processes, files, network traffic)
            - Timestamp relative to attack start
            
            Format response as JSON with structure:
            {{
                "attacker_profile": "sophistication level",
                "target_asset": "asset description",
                "steps": [
                    {{
                        "step_number": 1,
                        "technique_id": "T1566.001",
                        "technique_name": "Phishing: Spearphishing Attachment",
                        "description": "detailed description",
                        "indicators": ["observable1", "observable2"],
                        "timestamp_offset_minutes": 0
                    }}
                ]
            }}
            
            Make it realistic, detailed, and technically accurate.
            """,
            agent=self.agent,
            expected_output="JSON attack scenario"
        )
        
        return task
    
    def generate_attack_scenario(
        self,
        scenario_id: str,
        attack_type: AttackType = None
    ) -> AttackScenario:
        """
        Generate complete attack scenario
        
        Args:
            scenario_id: Unique identifier
            attack_type: Type of attack (random if None)
            
        Returns:
            AttackScenario object
        """
        if attack_type is None:
            attack_type = random.choice(list(AttackType))
        
        logger.info(f"Generating {attack_type.value} attack scenario: {scenario_id}")
        
        # Create and execute task
        task = self.create_attack_generation_task(attack_type)
        
        try:
            # Execute task
            result = task.execute()
            
            # Parse result
            if isinstance(result, str):
                # Extract JSON from markdown code blocks if present
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    result = result.split("```")[1].split("```")[0].strip()
                
                attack_data = json.loads(result)
            else:
                attack_data = result
            
            # Create attack steps
            steps = []
            base_time = datetime.now()
            
            for step_data in attack_data.get('steps', []):
                step = AttackStep(
                    step_number=step_data['step_number'],
                    technique_id=step_data['technique_id'],
                    technique_name=step_data['technique_name'],
                    description=step_data['description'],
                    timestamp=base_time + timedelta(minutes=step_data.get('timestamp_offset_minutes', 0)),
                    indicators=step_data.get('indicators', [])
                )
                steps.append(step)
            
            # Create scenario
            scenario = AttackScenario(
                scenario_id=scenario_id,
                attack_type=attack_type,
                attacker_profile=attack_data.get('attacker_profile', 'intermediate'),
                target_asset=attack_data.get('target_asset', 'corporate workstation'),
                steps=steps,
                success_probability=random.uniform(0.6, 0.9)
            )
            
            logger.info(f"Generated scenario with {len(steps)} steps")
            return scenario
            
        except Exception as e:
            logger.error(f"Error generating attack scenario: {e}")
            # Fallback to template-based generation
            return self._generate_template_scenario(scenario_id, attack_type)
    
    def _generate_template_scenario(
        self,
        scenario_id: str,
        attack_type: AttackType
    ) -> AttackScenario:
        """
        Generate scenario using templates (fallback)
        
        Args:
            scenario_id: Scenario ID
            attack_type: Attack type
            
        Returns:
            AttackScenario
        """
        logger.info(f"Using template for {attack_type.value}")
        
        templates = {
            AttackType.PHISHING: self._phishing_template,
            AttackType.CREDENTIAL_MISUSE: self._credential_misuse_template,
            AttackType.LATERAL_MOVEMENT: self._lateral_movement_template,
            AttackType.DATA_EXFILTRATION: self._data_exfiltration_template,
        }
        
        template_func = templates.get(attack_type, self._phishing_template)
        return template_func(scenario_id)
    
    def _phishing_template(self, scenario_id: str) -> AttackScenario:
        """Phishing attack template"""
        base_time = datetime.now()
        
        steps = [
            AttackStep(
                step_number=1,
                technique_id="T1566.001",
                technique_name="Phishing: Spearphishing Attachment",
                description="Attacker sends email with malicious Excel document to finance team",
                timestamp=base_time,
                indicators=[
                    "Email from external domain mimicking vendor",
                    "Attachment: Invoice_Q4.xlsm",
                    "Sender: accounts@vendor-services.xyz"
                ]
            ),
            AttackStep(
                step_number=2,
                technique_id="T1204.002",
                technique_name="User Execution: Malicious File",
                description="User opens attachment and enables macros",
                timestamp=base_time + timedelta(minutes=30),
                indicators=[
                    "Excel.exe spawns PowerShell.exe",
                    "Process: powershell.exe -Enc <base64>",
                    "Unusual macro execution"
                ]
            ),
            AttackStep(
                step_number=3,
                technique_id="T1059.001",
                technique_name="Command and Scripting Interpreter: PowerShell",
                description="PowerShell downloads and executes second-stage payload",
                timestamp=base_time + timedelta(minutes=35),
                indicators=[
                    "Outbound connection to 198.51.100.42:443",
                    "File created: C:\\Users\\victim\\AppData\\Roaming\\update.exe",
                    "PowerShell downloading from external URL"
                ]
            ),
            AttackStep(
                step_number=4,
                technique_id="T1078.003",
                technique_name="Valid Accounts: Local Accounts",
                description="Credential harvesting using keylogger",
                timestamp=base_time + timedelta(hours=2),
                indicators=[
                    "Keystroke logging process active",
                    "Suspicious clipboard access",
                    "Credentials sent to C2 server"
                ]
            )
        ]
        
        return AttackScenario(
            scenario_id=scenario_id,
            attack_type=AttackType.PHISHING,
            attacker_profile="intermediate",
            target_asset="finance team workstations",
            steps=steps,
            success_probability=0.75
        )
    
    def _credential_misuse_template(self, scenario_id: str) -> AttackScenario:
        """Credential misuse template"""
        base_time = datetime.now()
        
        steps = [
            AttackStep(
                step_number=1,
                technique_id="T1110.003",
                technique_name="Brute Force: Password Spraying",
                description="Attacker performs password spraying against VPN endpoint",
                timestamp=base_time,
                indicators=[
                    "Multiple failed logins from 203.0.113.15",
                    "Common passwords attempted (Welcome2024, Spring2024)",
                    "Multiple usernames tested with same password"
                ]
            ),
            AttackStep(
                step_number=2,
                technique_id="T1078.004",
                technique_name="Valid Accounts: Cloud Accounts",
                description="Successful login with compromised credentials",
                timestamp=base_time + timedelta(hours=1),
                indicators=[
                    "Login from unusual location (Eastern Europe)",
                    "Impossible travel detected",
                    "User agent: Python-requests/2.28.0"
                ]
            ),
            AttackStep(
                step_number=3,
                technique_id="T1087.004",
                technique_name="Account Discovery: Cloud Account",
                description="Enumeration of cloud resources and permissions",
                timestamp=base_time + timedelta(hours=1, minutes=15),
                indicators=[
                    "Rapid API calls to enumerate users",
                    "List all SharePoint sites",
                    "Query directory for sensitive groups"
                ]
            )
        ]
        
        return AttackScenario(
            scenario_id=scenario_id,
            attack_type=AttackType.CREDENTIAL_MISUSE,
            attacker_profile="intermediate",
            target_asset="cloud environment",
            steps=steps,
            success_probability=0.70
        )
    
    def _lateral_movement_template(self, scenario_id: str) -> AttackScenario:
        """Lateral movement template"""
        base_time = datetime.now()
        
        steps = [
            AttackStep(
                step_number=1,
                technique_id="T1021.001",
                technique_name="Remote Services: Remote Desktop Protocol",
                description="RDP connection to file server using compromised admin account",
                timestamp=base_time,
                indicators=[
                    "RDP connection from workstation to file server",
                    "Admin account login outside business hours",
                    "Source: 10.0.5.45, Dest: 10.0.10.20"
                ]
            ),
            AttackStep(
                step_number=2,
                technique_id="T1003.001",
                technique_name="OS Credential Dumping: LSASS Memory",
                description="Dump LSASS to extract credentials",
                timestamp=base_time + timedelta(minutes=10),
                indicators=[
                    "procdump64.exe accessing LSASS",
                    "Suspicious memory dump: lsass.dmp",
                    "High-value target access"
                ]
            ),
            AttackStep(
                step_number=3,
                technique_id="T1021.002",
                technique_name="Remote Services: SMB/Windows Admin Shares",
                description="Use extracted credentials to access domain controller",
                timestamp=base_time + timedelta(minutes=30),
                indicators=[
                    "SMB connection to DC01.corp.local",
                    "Access to ADMIN$ share",
                    "Credential from previous dump used"
                ]
            )
        ]
        
        return AttackScenario(
            scenario_id=scenario_id,
            attack_type=AttackType.LATERAL_MOVEMENT,
            attacker_profile="advanced",
            target_asset="domain controller",
            steps=steps,
            success_probability=0.65
        )
    
    def _data_exfiltration_template(self, scenario_id: str) -> AttackScenario:
        """Data exfiltration template"""
        base_time = datetime.now()
        
        steps = [
            AttackStep(
                step_number=1,
                technique_id="T1005",
                technique_name="Data from Local System",
                description="Search for and collect sensitive documents",
                timestamp=base_time,
                indicators=[
                    "Recursive directory listing: \\\\fileserver\\sensitive",
                    "File searches: *.xlsx, *.pdf, *confidential*",
                    "Unusual file access patterns"
                ]
            ),
            AttackStep(
                step_number=2,
                technique_id="T1560.001",
                technique_name="Archive Collected Data: Archive via Utility",
                description="Compress data for exfiltration",
                timestamp=base_time + timedelta(minutes=45),
                indicators=[
                    "7z.exe creating archive: data.7z",
                    "Large archive: 2.3 GB",
                    "Password-protected archive"
                ]
            ),
            AttackStep(
                step_number=3,
                technique_id="T1048.003",
                technique_name="Exfiltration Over Alternative Protocol: DNS",
                description="Exfiltrate data using DNS tunneling",
                timestamp=base_time + timedelta(hours=2),
                indicators=[
                    "Abnormal DNS query volume",
                    "Long subdomain names (base64 encoded)",
                    "Queries to attacker-controlled domain"
                ]
            )
        ]
        
        return AttackScenario(
            scenario_id=scenario_id,
            attack_type=AttackType.DATA_EXFILTRATION,
            attacker_profile="advanced",
            target_asset="file server",
            steps=steps,
            success_probability=0.80
        )
