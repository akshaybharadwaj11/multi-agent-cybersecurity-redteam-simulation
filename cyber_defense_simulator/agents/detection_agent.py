"""
Detection Agent - Incident Detection and Summarization
Analyzes telemetry to detect and summarize security incidents
"""

from crewai import Agent, Task
from typing import List, Dict
import json
import logging
from datetime import datetime
import re

from core.data_models import (
    TelemetryData, IncidentReport, Anomaly, SeverityLevel, AttackType
)
from core.config import Config

logger = logging.getLogger(__name__)


class DetectionAgent:
    """Detects and summarizes security incidents from telemetry"""
    
    def __init__(self):
        """Initialize Detection agent"""
        self.agent = Agent(
            role="Security Operations Center (SOC) Analyst",
            goal="Detect security incidents by analyzing system telemetry and create detailed incident reports",
            backstory="""You are an experienced SOC analyst with expertise in threat detection, 
            log analysis, and incident response. You excel at identifying malicious patterns in 
            large volumes of security telemetry, correlating events across different log sources, 
            and producing clear, actionable incident reports. You are familiar with MITRE ATT&CK 
            framework and can map observed activities to specific techniques.""",
            verbose=Config.CREW_VERBOSE,
            allow_delegation=False,
            llm=Config.get_llm()
        )
        
        # Detection rules for quick filtering
        self.suspicious_patterns = {
            "powershell_encoded": re.compile(r"powershell.*-Enc", re.IGNORECASE),
            "lsass_access": re.compile(r"lsass", re.IGNORECASE),
            "failed_auth": re.compile(r"failed login", re.IGNORECASE),
            "unusual_location": re.compile(r"unusual location", re.IGNORECASE),
            "suspicious_domain": re.compile(r"attacker|malicious|suspicious", re.IGNORECASE),
        }
        
        logger.info("Initialized Detection Agent")
    
    def create_detection_task(
        self,
        telemetry: TelemetryData,
        scenario_id: str
    ) -> Task:
        """
        Create task for incident detection
        
        Args:
            telemetry: Telemetry data to analyze
            scenario_id: Scenario identifier
            
        Returns:
            CrewAI Task
        """
        # Prepare log summary for LLM
        log_summary = self._prepare_log_summary(telemetry)
        
        task = Task(
            description=f"""
            Analyze the following security telemetry and produce a detailed incident report.
            
            TELEMETRY SUMMARY:
            {log_summary}
            
            ANALYSIS TASKS:
            1. Identify all suspicious activities and anomalies
            2. Correlate events across different log sources
            3. Map observed techniques to MITRE ATT&CK framework
            4. Determine incident severity (low, medium, high, critical)
            5. Assess confidence level in detection (0.0-1.0)
            6. Create timeline of attack progression
            7. Identify affected assets
            
            OUTPUT FORMAT (JSON):
            {{
                "severity": "critical|high|medium|low",
                "confidence": 0.85,
                "summary": "Brief incident description",
                "anomalies": [
                    {{
                        "type": "anomaly type",
                        "confidence": 0.9,
                        "description": "what was detected",
                        "affected_entities": ["entity1", "entity2"],
                        "evidence": ["log entry 1", "log entry 2"]
                    }}
                ],
                "mitre_techniques": ["T1566", "T1059"],
                "affected_assets": ["workstation-45", "file-server-01"],
                "timeline": [
                    {{
                        "time": "relative timestamp",
                        "event": "what happened",
                        "significance": "why it matters"
                    }}
                ]
            }}
            
            Focus on HIGH-CONFIDENCE detections. Be specific about evidence.
            """,
            agent=self.agent,
            expected_output="JSON incident report"
        )
        
        return task
    
    def detect_incident(
        self,
        telemetry: TelemetryData,
        incident_id: str
    ) -> IncidentReport:
        """
        Detect and create incident report from telemetry
        
        Args:
            telemetry: Telemetry data
            incident_id: Incident identifier
            
        Returns:
            IncidentReport
        """
        logger.info(f"Analyzing telemetry for incident {incident_id}")
        
        # Quick rule-based pre-filtering
        suspicious_logs = self._apply_detection_rules(telemetry)
        
        if not suspicious_logs:
            logger.info("No suspicious activity detected")
            return self._create_clean_report(incident_id, telemetry.scenario_id)
        
        # LLM-based deep analysis
        try:
            task = self.create_detection_task(telemetry, telemetry.scenario_id)
            result = task.execute()
            
            # Parse result
            if isinstance(result, str):
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    result = result.split("```")[1].split("```")[0].strip()
                
                incident_data = json.loads(result)
            else:
                incident_data = result
            
            # Create incident report
            report = self._create_incident_report(
                incident_id,
                telemetry.scenario_id,
                incident_data
            )
            
            logger.info(
                f"Incident detected: {report.severity.value} severity, "
                f"{report.confidence:.2f} confidence"
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Error in LLM detection: {e}")
            # Fallback to rule-based detection
            return self._fallback_detection(incident_id, telemetry, suspicious_logs)
    
    def _prepare_log_summary(self, telemetry: TelemetryData) -> str:
        """Prepare concise log summary for LLM analysis"""
        lines = []
        
        # Sample logs (send subset to LLM)
        if telemetry.system_logs:
            lines.append("SYSTEM LOGS:")
            for log in telemetry.system_logs[:10]:
                lines.append(f"  [{log.timestamp.strftime('%H:%M:%S')}] {log.message}")
        
        if telemetry.auth_logs:
            lines.append("\nAUTHENTICATION LOGS:")
            for log in telemetry.auth_logs[:10]:
                lines.append(f"  [{log.timestamp.strftime('%H:%M:%S')}] {log.message}")
        
        if telemetry.network_logs:
            lines.append("\nNETWORK LOGS:")
            for log in telemetry.network_logs[:10]:
                lines.append(f"  [{log.timestamp.strftime('%H:%M:%S')}] {log.message}")
        
        if telemetry.process_logs:
            lines.append("\nPROCESS LOGS:")
            for log in telemetry.process_logs[:10]:
                lines.append(f"  [{log.timestamp.strftime('%H:%M:%S')}] {log.message}")
        
        return "\n".join(lines)
    
    def _apply_detection_rules(self, telemetry: TelemetryData) -> List[Dict]:
        """Apply rule-based detection to filter suspicious logs"""
        suspicious = []
        
        all_logs = (
            telemetry.system_logs + telemetry.auth_logs +
            telemetry.network_logs + telemetry.process_logs
        )
        
        for log in all_logs:
            for pattern_name, pattern in self.suspicious_patterns.items():
                if pattern.search(log.message):
                    suspicious.append({
                        "log": log,
                        "pattern": pattern_name,
                        "source": log.source
                    })
        
        logger.debug(f"Rule-based detection found {len(suspicious)} suspicious logs")
        return suspicious
    
    def _create_incident_report(
        self,
        incident_id: str,
        scenario_id: str,
        data: Dict
    ) -> IncidentReport:
        """Create IncidentReport from parsed data"""
        # Parse anomalies
        anomalies = []
        for anom_data in data.get('anomalies', []):
            anomaly = Anomaly(
                anomaly_type=anom_data.get('type', 'unknown'),
                confidence=anom_data.get('confidence', 0.5),
                description=anom_data.get('description', ''),
                affected_entities=anom_data.get('affected_entities', []),
                evidence=anom_data.get('evidence', [])
            )
            anomalies.append(anomaly)
        
        # Parse severity
        severity_str = data.get('severity', 'medium').lower()
        severity = SeverityLevel(severity_str)
        
        report = IncidentReport(
            incident_id=incident_id,
            scenario_id=scenario_id,
            severity=severity,
            confidence=data.get('confidence', 0.7),
            summary=data.get('summary', 'Security incident detected'),
            anomalies=anomalies,
            mitre_techniques=data.get('mitre_techniques', []),
            affected_assets=data.get('affected_assets', []),
            timeline=data.get('timeline', [])
        )
        
        return report
    
    def _fallback_detection(
        self,
        incident_id: str,
        telemetry: TelemetryData,
        suspicious_logs: List[Dict]
    ) -> IncidentReport:
        """Fallback rule-based detection when LLM fails"""
        logger.info("Using fallback detection")
        
        # Count suspicious patterns
        pattern_counts = {}
        for item in suspicious_logs:
            pattern = item['pattern']
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        # Determine severity based on patterns
        if pattern_counts.get('lsass_access', 0) > 0:
            severity = SeverityLevel.CRITICAL
        elif pattern_counts.get('powershell_encoded', 0) > 0:
            severity = SeverityLevel.HIGH
        elif pattern_counts.get('failed_auth', 0) > 5:
            severity = SeverityLevel.MEDIUM
        else:
            severity = SeverityLevel.LOW
        
        # Create simple anomaly
        anomaly = Anomaly(
            anomaly_type="suspicious_activity",
            confidence=0.7,
            description=f"Detected suspicious patterns: {', '.join(pattern_counts.keys())}",
            affected_entities=["unknown"],
            evidence=[item['log'].message for item in suspicious_logs[:5]]
        )
        
        report = IncidentReport(
            incident_id=incident_id,
            scenario_id=telemetry.scenario_id,
            severity=severity,
            confidence=0.7,
            summary=f"Security incident detected with {len(suspicious_logs)} suspicious events",
            anomalies=[anomaly],
            mitre_techniques=["T1059"],  # Generic
            affected_assets=["workstation"],
            timeline=[]
        )
        
        return report
    
    def _create_clean_report(self, incident_id: str, scenario_id: str) -> IncidentReport:
        """Create report indicating no incident detected"""
        return IncidentReport(
            incident_id=incident_id,
            scenario_id=scenario_id,
            severity=SeverityLevel.LOW,
            confidence=0.3,
            summary="No significant security incident detected",
            anomalies=[],
            mitre_techniques=[],
            affected_assets=[],
            timeline=[]
        )
