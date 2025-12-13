"""
Knowledge Base Initialization
Loads runbooks, MITRE ATT&CK data, and threat intelligence
"""

import json
from typing import List, Dict
from pathlib import Path
import logging

from cyber_defense_simulator.rag.vector_store import VectorStore
from cyber_defense_simulator.core.config import Config

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """Manages cyber defense knowledge base"""
    
    def __init__(self, vector_store: VectorStore):
        """
        Initialize knowledge base
        
        Args:
            vector_store: Vector store instance
        """
        self.vector_store = vector_store
        self.runbooks = []
        self.mitre_techniques = []
        self.cve_data = []
    
    def initialize(self) -> None:
        """Initialize knowledge base with default data"""
        logger.info("Initializing knowledge base...")
        
        # Load runbooks
        self._load_default_runbooks()
        
        # Load MITRE ATT&CK techniques
        self._load_mitre_techniques()
        
        # Load CVE data
        self._load_cve_data()
        
        # Add past incidents (synthetic for now)
        self._load_synthetic_incidents()
        
        logger.info(f"Knowledge base initialized with {self.vector_store.get_document_count()} documents")
    
    def _load_default_runbooks(self) -> None:
        """Load default security runbooks"""
        runbooks = [
            {
                "id": "RB-001",
                "title": "Phishing Email Response",
                "techniques": ["T1566.001", "T1566.002"],
                "content": """
                Runbook: Phishing Email Response
                
                Objective: Detect and remediate phishing attacks
                
                Detection Indicators:
                - Suspicious sender addresses
                - Unusual attachment types (.exe, .scr, .zip)
                - Urgent language requesting credentials
                - Links to unexpected domains
                - Grammatical errors or formatting issues
                
                Immediate Actions:
                1. Quarantine suspicious email from all mailboxes
                2. Block sender domain at email gateway
                3. Scan endpoints for downloaded attachments
                4. Reset credentials for affected users
                5. Alert security team
                
                Investigation Steps:
                1. Analyze email headers and routing
                2. Check URL reputation and sandbox analysis
                3. Review authentication logs for compromised accounts
                4. Identify all recipients who clicked links
                5. Check for lateral movement attempts
                
                Remediation:
                1. Remove malicious emails organization-wide
                2. Block malicious domains and IPs
                3. Force password resets for affected accounts
                4. Deploy endpoint detection rules
                5. Conduct user awareness training
                
                Success Metrics:
                - No successful credential compromise
                - All malicious emails quarantined within 1 hour
                - Zero lateral movement detected
                """,
                "type": "runbook"
            },
            {
                "id": "RB-002",
                "title": "Credential Compromise Response",
                "techniques": ["T1078", "T1110", "T1555"],
                "content": """
                Runbook: Credential Compromise Response
                
                Objective: Respond to stolen or compromised credentials
                
                Detection Indicators:
                - Failed login attempts from unusual locations
                - Successful login from impossible travel scenarios
                - Access to sensitive resources outside normal hours
                - Multiple concurrent sessions from different IPs
                - Unusual authentication patterns
                
                Immediate Actions:
                1. Lock compromised accounts immediately
                2. Terminate active sessions
                3. Block source IP addresses
                4. Enable enhanced monitoring on related accounts
                5. Alert affected users
                
                Investigation Steps:
                1. Review authentication logs for timeline
                2. Identify accessed resources and data
                3. Check for privilege escalation attempts
                4. Analyze network traffic from compromised sessions
                5. Search for persistence mechanisms
                
                Remediation:
                1. Force password reset with MFA enrollment
                2. Review and revoke OAuth tokens/API keys
                3. Audit all access permissions
                4. Remove any backdoor accounts
                5. Deploy enhanced detection rules
                
                Success Metrics:
                - Account secured within 30 minutes
                - No unauthorized data access
                - All persistence mechanisms removed
                """,
                "type": "runbook"
            },
            {
                "id": "RB-003",
                "title": "Lateral Movement Detection",
                "techniques": ["T1021", "T1210", "T1570"],
                "content": """
                Runbook: Lateral Movement Detection and Response
                
                Objective: Detect and stop lateral movement within network
                
                Detection Indicators:
                - Unusual remote desktop connections
                - SMB/WMI activity to multiple hosts
                - Pass-the-hash attempts
                - Privilege escalation on multiple systems
                - Abnormal network scanning
                
                Immediate Actions:
                1. Isolate affected hosts from network
                2. Block compromised accounts
                3. Kill suspicious remote sessions
                4. Enable enhanced network monitoring
                5. Alert incident response team
                
                Investigation Steps:
                1. Map attack path through network logs
                2. Identify all compromised hosts
                3. Analyze tools and techniques used
                4. Check for data staging areas
                5. Review privilege usage
                
                Remediation:
                1. Reimage compromised systems
                2. Rotate service account credentials
                3. Patch exploited vulnerabilities
                4. Implement network segmentation
                5. Deploy EDR on all endpoints
                
                Success Metrics:
                - Lateral movement stopped within 2 hours
                - All compromised systems identified
                - No data exfiltration occurred
                """,
                "type": "runbook"
            },
            {
                "id": "RB-004",
                "title": "Data Exfiltration Response",
                "techniques": ["T1048", "T1041", "T1567"],
                "content": """
                Runbook: Data Exfiltration Response
                
                Objective: Detect and prevent data theft
                
                Detection Indicators:
                - Large outbound data transfers
                - Access to file servers outside business hours
                - Use of unauthorized cloud storage
                - Encrypted traffic to unknown destinations
                - Database queries for large datasets
                
                Immediate Actions:
                1. Block egress traffic to suspicious destinations
                2. Throttle or block affected user accounts
                3. Capture network traffic for analysis
                4. Freeze backup systems
                5. Alert legal and compliance teams
                
                Investigation Steps:
                1. Identify what data was accessed
                2. Determine exfiltration method and destination
                3. Review data classification and sensitivity
                4. Analyze timeline of access
                5. Identify attack vector for initial access
                
                Remediation:
                1. Implement DLP rules for sensitive data
                2. Block unauthorized cloud services
                3. Encrypt sensitive data at rest
                4. Implement data access monitoring
                5. Conduct forensic analysis
                
                Success Metrics:
                - Data exfiltration stopped
                - Full scope of data loss determined
                - Source of compromise identified
                """,
                "type": "runbook"
            },
            {
                "id": "RB-005",
                "title": "Malware Containment",
                "techniques": ["T1204", "T1059", "T1547"],
                "content": """
                Runbook: Malware Infection Response
                
                Objective: Contain and remove malware infections
                
                Detection Indicators:
                - Unusual process execution
                - Suspicious network connections
                - File system modifications
                - Registry changes for persistence
                - Anti-virus alerts
                
                Immediate Actions:
                1. Isolate infected systems
                2. Kill malicious processes
                3. Block C2 domains and IPs
                4. Quarantine malicious files
                5. Deploy endpoint protection
                
                Investigation Steps:
                1. Analyze malware sample in sandbox
                2. Identify infection vector
                3. Map malware capabilities
                4. Search for additional infected systems
                5. Check for data theft or destruction
                
                Remediation:
                1. Remove malware and persistence mechanisms
                2. Patch exploited vulnerabilities
                3. Restore from clean backups if needed
                4. Update detection signatures
                5. Block malware infrastructure
                
                Success Metrics:
                - All infections removed
                - No reinfection after 48 hours
                - IOCs added to detection systems
                """,
                "type": "runbook"
            }
        ]
        
        # Add to vector store
        documents = [rb["content"] for rb in runbooks]
        metadatas = [
            {
                "type": "runbook",
                "id": rb["id"],
                "title": rb["title"],
                "techniques": ",".join(rb["techniques"])
            }
            for rb in runbooks
        ]
        ids = [rb["id"] for rb in runbooks]
        
        self.vector_store.add_documents(documents, metadatas, ids)
        self.runbooks = runbooks
        
        logger.info(f"Loaded {len(runbooks)} runbooks")
    
    def _load_mitre_techniques(self) -> None:
        """Load MITRE ATT&CK technique descriptions"""
        techniques = [
            {
                "id": "T1566",
                "name": "Phishing",
                "content": "Adversaries send phishing messages to gain access to victim systems. Includes spearphishing attachments, links, and via service."
            },
            {
                "id": "T1078",
                "name": "Valid Accounts",
                "content": "Adversaries obtain and abuse credentials of existing accounts for persistence and privilege escalation."
            },
            {
                "id": "T1110",
                "name": "Brute Force",
                "content": "Adversaries use brute force techniques to gain access through credential guessing, spraying, or stuffing."
            },
            {
                "id": "T1021",
                "name": "Remote Services",
                "content": "Adversaries use valid accounts to log into remote services like RDP, SSH, VNC to achieve lateral movement."
            },
            {
                "id": "T1048",
                "name": "Exfiltration Over Alternative Protocol",
                "content": "Adversaries steal data using protocols other than the main C2 channel, often using DNS, ICMP, etc."
            },
            {
                "id": "T1059",
                "name": "Command and Scripting Interpreter",
                "content": "Adversaries abuse command and script interpreters to execute commands and malicious scripts."
            }
        ]
        
        documents = [t["content"] for t in techniques]
        metadatas = [
            {
                "type": "mitre_technique",
                "technique_id": t["id"],
                "name": t["name"]
            }
            for t in techniques
        ]
        ids = [f"MITRE-{t['id']}" for t in techniques]
        
        self.vector_store.add_documents(documents, metadatas, ids)
        self.mitre_techniques = techniques
        
        logger.info(f"Loaded {len(techniques)} MITRE techniques")
    
    def _load_cve_data(self) -> None:
        """Load CVE vulnerability data"""
        cves = [
            {
                "id": "CVE-2024-9999",
                "content": "Critical vulnerability in authentication mechanism allowing bypass via crafted requests."
            }
        ]
        
        if cves:
            documents = [c["content"] for c in cves]
            metadatas = [{"type": "cve", "cve_id": c["id"]} for c in cves]
            ids = [c["id"] for c in cves]
            
            self.vector_store.add_documents(documents, metadatas, ids)
            self.cve_data = cves
            
            logger.info(f"Loaded {len(cves)} CVE entries")
    
    def _load_synthetic_incidents(self) -> None:
        """Load synthetic past incidents for similarity search"""
        incidents = [
            {
                "id": "INC-001",
                "content": """
                Past Incident: Phishing campaign leading to credential compromise
                
                Summary: Organization-wide phishing campaign targeting finance team.
                Attack successfully compromised 3 accounts before detection.
                
                Timeline:
                - Day 1: Phishing emails sent to 50 users
                - Day 1 (+2h): First credential entered on fake site
                - Day 1 (+4h): Attacker accessed email accounts
                - Day 1 (+6h): Detection by anomalous login alerts
                - Day 1 (+7h): Accounts locked and passwords reset
                
                Lessons Learned:
                - Need faster email quarantine
                - MFA would have prevented account access
                - User training required
                """
            },
            {
                "id": "INC-002",
                "content": """
                Past Incident: Lateral movement after initial compromise
                
                Summary: Attacker gained access via vulnerable web server,
                moved laterally to domain controller within 48 hours.
                
                Timeline:
                - Day 1: Web server compromised via SQL injection
                - Day 2: Privilege escalation to local admin
                - Day 2: Network reconnaissance performed
                - Day 3: Lateral movement to file server
                - Day 3: Detection via EDR behavioral analysis
                - Day 3: Network isolation and remediation
                
                Lessons Learned:
                - Patch management critical
                - Network segmentation needed
                - EDR deployment was key to detection
                """
            }
        ]
        
        documents = [inc["content"] for inc in incidents]
        metadatas = [{"type": "incident", "incident_id": inc["id"]} for inc in incidents]
        ids = [inc["id"] for inc in incidents]
        
        self.vector_store.add_documents(documents, metadatas, ids)
        
        logger.info(f"Loaded {len(incidents)} past incidents")


def initialize_knowledge_base(vector_store: VectorStore) -> KnowledgeBase:
    """
    Initialize and populate knowledge base
    
    Args:
        vector_store: Vector store instance
        
    Returns:
        Initialized KnowledgeBase
    """
    kb = KnowledgeBase(vector_store)
    kb.initialize()
    return kb
