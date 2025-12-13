"""
Telemetry Generator - Synthetic Log Creation
Generates realistic system, auth, network, and process logs from attack scenarios
"""

import random
from datetime import datetime, timedelta
from typing import List
import logging

from cyber_defense_simulator.core.data_models import AttackScenario, TelemetryData, LogEntry

logger = logging.getLogger(__name__)


class TelemetryGenerator:
    """Generates synthetic telemetry from attack scenarios"""
    
    def __init__(self, noise_level: float = 0.3):
        """
        Initialize telemetry generator
        
        Args:
            noise_level: Proportion of benign noise logs (0.0-1.0)
        """
        self.noise_level = noise_level
        logger.info(f"Initialized TelemetryGenerator (noise={noise_level})")
    
    def generate_telemetry(self, scenario: AttackScenario) -> TelemetryData:
        """
        Generate complete telemetry data from attack scenario
        
        Args:
            scenario: Attack scenario
            
        Returns:
            TelemetryData with synthetic logs
        """
        logger.info(f"Generating telemetry for scenario {scenario.scenario_id}")
        
        telemetry = TelemetryData(
            scenario_id=scenario.scenario_id,
            collection_start=scenario.created_at
        )
        
        # Generate logs for each attack step
        for step in scenario.steps:
            # System logs
            system_logs = self._generate_system_logs(step, scenario)
            telemetry.system_logs.extend(system_logs)
            
            # Auth logs
            auth_logs = self._generate_auth_logs(step, scenario)
            telemetry.auth_logs.extend(auth_logs)
            
            # Network logs
            network_logs = self._generate_network_logs(step, scenario)
            telemetry.network_logs.extend(network_logs)
            
            # Process logs
            process_logs = self._generate_process_logs(step, scenario)
            telemetry.process_logs.extend(process_logs)
        
        # Add benign noise
        self._add_noise_logs(telemetry, scenario)
        
        # Sort all logs by timestamp
        telemetry.system_logs.sort(key=lambda x: x.timestamp)
        telemetry.auth_logs.sort(key=lambda x: x.timestamp)
        telemetry.network_logs.sort(key=lambda x: x.timestamp)
        telemetry.process_logs.sort(key=lambda x: x.timestamp)
        
        telemetry.collection_end = datetime.now()
        
        total_logs = (
            len(telemetry.system_logs) + len(telemetry.auth_logs) +
            len(telemetry.network_logs) + len(telemetry.process_logs)
        )
        logger.info(f"Generated {total_logs} total log entries")
        
        return telemetry
    
    def _generate_system_logs(self, step, scenario) -> List[LogEntry]:
        """Generate system logs for an attack step"""
        logs = []
        
        # Map technique to system events
        if "T1566" in step.technique_id:  # Phishing
            logs.append(LogEntry(
                timestamp=step.timestamp,
                source="system",
                log_level="WARNING",
                message=f"File downloaded: {random.choice(['Invoice.xlsm', 'Document.docx', 'Update.zip'])}",
                metadata={"user": "jsmith", "path": "C:\\Users\\jsmith\\Downloads"}
            ))
        
        elif "T1059" in step.technique_id:  # Command execution
            logs.append(LogEntry(
                timestamp=step.timestamp,
                source="system",
                log_level="INFO",
                message=f"Process created: powershell.exe with args: -Enc {random.choice(['VGVzdA==', 'QXR0YWNr'])}",
                metadata={"parent": "excel.exe", "user": "jsmith"}
            ))
        
        elif "T1003" in step.technique_id:  # Credential dumping
            logs.append(LogEntry(
                timestamp=step.timestamp,
                source="system",
                log_level="CRITICAL",
                message="Sensitive process access detected: LSASS.exe",
                metadata={"accessor": "procdump64.exe", "access_type": "PROCESS_VM_READ"}
            ))
        
        return logs
    
    def _generate_auth_logs(self, step, scenario) -> List[LogEntry]:
        """Generate authentication logs"""
        logs = []
        
        if "T1110" in step.technique_id:  # Brute force
            # Multiple failed attempts
            for i in range(random.randint(5, 15)):
                logs.append(LogEntry(
                    timestamp=step.timestamp + timedelta(seconds=i*5),
                    source="auth",
                    log_level="WARNING",
                    message=f"Failed login attempt for user: {random.choice(['admin', 'user', 'jdoe'])}",
                    metadata={"source_ip": "203.0.113.15", "method": "password"}
                ))
        
        elif "T1078" in step.technique_id:  # Valid accounts
            logs.append(LogEntry(
                timestamp=step.timestamp,
                source="auth",
                log_level="INFO",
                message="Successful login from unusual location",
                metadata={
                    "user": "admin",
                    "source_ip": "198.51.100.42",
                    "location": "Romania",
                    "user_agent": "Python-requests/2.28.0"
                }
            ))
        
        elif "T1021" in step.technique_id:  # Remote services
            logs.append(LogEntry(
                timestamp=step.timestamp,
                source="auth",
                log_level="INFO",
                message="RDP session established",
                metadata={
                    "user": "admin",
                    "source": "10.0.5.45",
                    "destination": "10.0.10.20",
                    "protocol": "RDP"
                }
            ))
        
        return logs
    
    def _generate_network_logs(self, step, scenario) -> List[LogEntry]:
        """Generate network logs"""
        logs = []
        
        if "T1071" in step.technique_id or "T1048" in step.technique_id:  # C2 or exfiltration
            logs.append(LogEntry(
                timestamp=step.timestamp,
                source="network",
                log_level="WARNING",
                message="Outbound connection to suspicious IP",
                metadata={
                    "source": "10.0.5.45",
                    "destination": "198.51.100.42:443",
                    "protocol": "HTTPS",
                    "bytes_sent": random.randint(1000000, 10000000)
                }
            ))
        
        if "T1048.003" in step.technique_id:  # DNS exfiltration
            for i in range(random.randint(10, 30)):
                logs.append(LogEntry(
                    timestamp=step.timestamp + timedelta(seconds=i*2),
                    source="network",
                    log_level="INFO",
                    message=f"DNS query: {random.choice(['data', 'exfil', 'chunk'])}{i}.attacker.com",
                    metadata={"query_type": "A", "response": "NXDOMAIN"}
                ))
        
        return logs
    
    def _generate_process_logs(self, step, scenario) -> List[LogEntry]:
        """Generate process execution logs"""
        logs = []
        
        if "T1059" in step.technique_id:  # Script execution
            logs.append(LogEntry(
                timestamp=step.timestamp,
                source="process",
                log_level="INFO",
                message="Process spawned by Office application",
                metadata={
                    "parent": "EXCEL.EXE",
                    "child": "powershell.exe",
                    "cmdline": "-Enc VGhpcyBpcyBhIHRlc3Q="
                }
            ))
        
        if "T1003" in step.technique_id:  # Credential dumping
            logs.append(LogEntry(
                timestamp=step.timestamp,
                source="process",
                log_level="CRITICAL",
                message="Suspicious tool execution detected",
                metadata={
                    "process": "procdump64.exe",
                    "args": "-ma lsass.exe lsass.dmp",
                    "user": "admin"
                }
            ))
        
        return logs
    
    def _add_noise_logs(self, telemetry: TelemetryData, scenario: AttackScenario) -> None:
        """Add benign noise logs to make detection more realistic"""
        num_malicious = (
            len(telemetry.system_logs) + len(telemetry.auth_logs) +
            len(telemetry.network_logs) + len(telemetry.process_logs)
        )
        
        num_noise = int(num_malicious * self.noise_level / (1 - self.noise_level))
        
        start_time = scenario.created_at
        end_time = scenario.created_at + timedelta(hours=4)
        
        benign_templates = {
            "system": [
                "System update installed successfully",
                "Windows Defender scan completed",
                "Application started: Microsoft Teams",
                "File saved: Document.docx",
            ],
            "auth": [
                "User logged in successfully from workstation",
                "Password changed by user",
                "Session timeout for inactive user",
            ],
            "network": [
                "Connection to office365.com established",
                "DNS query: www.google.com",
                "HTTP GET: internal-portal.company.com",
            ],
            "process": [
                "Process started: chrome.exe",
                "Service started: Windows Update",
                "Application closed normally: outlook.exe",
            ]
        }
        
        for _ in range(num_noise):
            log_type = random.choice(list(benign_templates.keys()))
            message = random.choice(benign_templates[log_type])
            timestamp = start_time + (end_time - start_time) * random.random()
            
            log = LogEntry(
                timestamp=timestamp,
                source=log_type,
                log_level="INFO",
                message=message,
                metadata={"benign": True}
            )
            
            if log_type == "system":
                telemetry.system_logs.append(log)
            elif log_type == "auth":
                telemetry.auth_logs.append(log)
            elif log_type == "network":
                telemetry.network_logs.append(log)
            elif log_type == "process":
                telemetry.process_logs.append(log)
