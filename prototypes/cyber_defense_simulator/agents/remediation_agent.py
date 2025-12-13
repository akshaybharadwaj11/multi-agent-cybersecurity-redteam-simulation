"""
Remediation Agent - Action Recommendation
Generates remediation action recommendations based on incidents and context
"""

from crewai import Agent, Task
from typing import List
import json
import logging

from cyber_defense_simulator.core.data_models import (
    IncidentReport, RAGContext, RemediationPlan, RemediationOption, RemediationAction
)
from cyber_defense_simulator.core.config import Config

logger = logging.getLogger(__name__)


class RemediationAgent:
    """Generates remediation action recommendations"""
    
    def __init__(self):
        """Initialize Remediation agent"""
        self.agent = Agent(
            role="Incident Response Lead",
            goal="Recommend effective remediation actions that contain security incidents while minimizing disruption",
            backstory="""You are a senior incident responder with expertise in containment strategies, 
            remediation procedures, and security operations. You excel at making critical decisions under 
            pressure, balancing the need for swift action with operational considerations. You understand 
            the trade-offs between different response options and can clearly explain your recommendations. 
            Your decisions are grounded in established security runbooks and best practices.""",
            verbose=Config.CREW_VERBOSE,
            allow_delegation=False,
            llm=Config.get_llm()
        )
        
        logger.info("Initialized Remediation Agent")
    
    def create_remediation_task(
        self,
        incident_report: IncidentReport,
        rag_context: RAGContext
    ) -> Task:
        """
        Create task for remediation planning
        
        Args:
            incident_report: Incident report
            rag_context: Retrieved context
            
        Returns:
            CrewAI Task
        """
        # Prepare context summary
        runbook_summary = "\n".join([
            f"- {rb.title}: {rb.description[:100]}..."
            for rb in rag_context.runbooks[:3]
        ])
        
        task = Task(
            description=f"""
            Recommend remediation actions for this security incident:
            
            INCIDENT:
            - Severity: {incident_report.severity.value}
            - Confidence: {incident_report.confidence:.2f}
            - Summary: {incident_report.summary}
            - MITRE Techniques: {', '.join(incident_report.mitre_techniques)}
            - Affected Assets: {', '.join(incident_report.affected_assets)}
            
            AVAILABLE RUNBOOKS:
            {runbook_summary}
            
            REMEDIATION ACTIONS TO CONSIDER:
            - BLOCK_IP: Block source IP addresses at firewall
            - LOCK_ACCOUNT: Lock compromised user accounts
            - KILL_PROCESS: Terminate malicious processes
            - ISOLATE_HOST: Isolate affected hosts from network
            - NOTIFY_TEAM: Alert security team for manual review
            - SCAN_SYSTEM: Run antivirus/EDR scan on systems
            - RESET_CREDENTIALS: Force password reset for accounts
            - QUARANTINE_FILE: Quarantine malicious files
            
            REQUIREMENTS:
            1. Recommend 2-3 remediation options ranked by effectiveness
            2. For each option provide:
               - Action type (from list above)
               - Clear description of what will be done
               - Confidence score (0.0-1.0)
               - Expected impact on business operations
               - Potential risks or side effects
               - Prerequisites needed
               - Step-by-step execution plan
            
            3. Select ONE recommended action and explain why it's best
            
            OUTPUT FORMAT (JSON):
            {{
                "recommended_action": "BLOCK_IP",
                "justification": "Why this action is recommended",
                "options": [
                    {{
                        "action": "BLOCK_IP",
                        "description": "What will be done",
                        "confidence": 0.9,
                        "estimated_impact": "minimal|moderate|significant",
                        "risks": ["risk1", "risk2"],
                        "prerequisites": ["prereq1"],
                        "execution_steps": ["step1", "step2"]
                    }}
                ]
            }}
            
            Consider severity, confidence, and operational impact. Prefer actions that:
            - Match the incident severity
            - Have clear success criteria
            - Minimize business disruption
            - Follow established runbooks
            """,
            agent=self.agent,
            expected_output="JSON remediation plan"
        )
        
        return task
    
    def generate_remediation_plan(
        self,
        incident_report: IncidentReport,
        rag_context: RAGContext
    ) -> RemediationPlan:
        """
        Generate remediation plan
        
        Args:
            incident_report: Incident report
            rag_context: Retrieved context
            
        Returns:
            RemediationPlan with recommended actions
        """
        logger.info(f"Generating remediation plan for incident {incident_report.incident_id}")
        
        try:
            # Create and execute task
            task = self.create_remediation_task(incident_report, rag_context)
            from crewai import Crew
            crew = Crew(
                agents=[self.agent],
                tasks=[task],
                verbose=Config.CREW_VERBOSE
            )
            result = crew.kickoff()
            
            # Extract result
            if hasattr(result, 'raw'):
                result = result.raw
            elif hasattr(result, 'tasks_output'):
                result = result.tasks_output[0].raw if result.tasks_output else str(result)
            else:
                result = str(result)
            
            # Parse result
            if isinstance(result, str):
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    result = result.split("```")[1].split("```")[0].strip()
                
                plan_data = json.loads(result)
            else:
                plan_data = result
            
            # Create remediation plan
            plan = self._create_plan_from_data(incident_report, plan_data)
            
            logger.info(
                f"Generated plan with {len(plan.options)} options, "
                f"recommended: {plan.recommended_action.value if plan.recommended_action else 'None'}"
            )
            
            return plan
            
        except Exception as e:
            logger.error(f"Error generating remediation plan: {e}")
            # Fallback to rule-based recommendations
            return self._fallback_remediation(incident_report, rag_context)
    
    def _create_plan_from_data(
        self,
        incident_report: IncidentReport,
        data: dict
    ) -> RemediationPlan:
        """Create RemediationPlan from parsed data"""
        options = []
        
        def normalize_action(action_str: str) -> RemediationAction:
            """Normalize action string to enum value"""
            # Convert to lowercase and replace underscores
            action_lower = action_str.lower().strip()
            
            # Map common variations to enum values
            action_map = {
                'isolate_host': 'isolate_host',
                'isolation_host': 'isolate_host',
                'isolate': 'isolate_host',
                'block_ip': 'block_ip',
                'blockip': 'block_ip',
                'lock_account': 'lock_account',
                'lockaccount': 'lock_account',
                'kill_process': 'kill_process',
                'killprocess': 'kill_process',
                'notify_team': 'notify_team',
                'notifyteam': 'notify_team',
                'scan_system': 'scan_system',
                'scansystem': 'scan_system',
                'reset_credentials': 'reset_credentials',
                'resetcredentials': 'reset_credentials',
                'quarantine_file': 'quarantine_file',
                'quarantinefile': 'quarantine_file',
            }
            
            # Try direct match first
            if action_lower in action_map:
                action_lower = action_map[action_lower]
            
            # Try to find matching enum value
            for action_enum in RemediationAction:
                if action_enum.value == action_lower or action_enum.name.lower() == action_lower:
                    return action_enum
            
            # Default fallback
            logger.warning(f"Unknown action '{action_str}', defaulting to BLOCK_IP")
            return RemediationAction.BLOCK_IP
        
        for opt_data in data.get('options', []):
            try:
                action = normalize_action(opt_data['action'])
            except (KeyError, ValueError) as e:
                logger.warning(f"Error parsing action '{opt_data.get('action', 'unknown')}': {e}. Using BLOCK_IP")
                action = RemediationAction.BLOCK_IP
            
            option = RemediationOption(
                action=action,
                description=opt_data.get('description', ''),
                confidence=opt_data.get('confidence', 0.7),
                estimated_impact=opt_data.get('estimated_impact', 'moderate'),
                risks=opt_data.get('risks', []),
                prerequisites=opt_data.get('prerequisites', []),
                execution_steps=opt_data.get('execution_steps', [])
            )
            options.append(option)
        
        # Get recommended action (use normalize_action function defined above)
        recommended_str = data.get('recommended_action', '')
        if recommended_str:
            try:
                recommended = normalize_action(recommended_str)
            except Exception as e:
                logger.warning(f"Error parsing recommended action '{recommended_str}': {e}. Using first option.")
                recommended = options[0].action if options else None
        else:
            # Use first option if no recommendation
            recommended = options[0].action if options else None
        
        plan = RemediationPlan(
            incident_id=incident_report.incident_id,
            options=options,
            recommended_action=recommended,
            justification=data.get('justification', '')
        )
        
        return plan
    
    def _fallback_remediation(
        self,
        incident_report: IncidentReport,
        rag_context: RAGContext
    ) -> RemediationPlan:
        """
        Fallback rule-based remediation recommendation
        
        Args:
            incident_report: Incident report
            rag_context: RAG context
            
        Returns:
            RemediationPlan
        """
        logger.info("Using fallback remediation rules")
        
        # Map severity to actions
        severity_actions = {
            "critical": [
                RemediationAction.ISOLATE_HOST,
                RemediationAction.KILL_PROCESS,
                RemediationAction.LOCK_ACCOUNT
            ],
            "high": [
                RemediationAction.BLOCK_IP,
                RemediationAction.LOCK_ACCOUNT,
                RemediationAction.SCAN_SYSTEM
            ],
            "medium": [
                RemediationAction.NOTIFY_TEAM,
                RemediationAction.SCAN_SYSTEM,
                RemediationAction.BLOCK_IP
            ],
            "low": [
                RemediationAction.NOTIFY_TEAM,
                RemediationAction.SCAN_SYSTEM
            ]
        }
        
        recommended_actions = severity_actions.get(
            incident_report.severity.value,
            [RemediationAction.NOTIFY_TEAM]
        )
        
        options = []
        for i, action in enumerate(recommended_actions[:3]):
            confidence = 0.8 - (i * 0.1)
            
            option = RemediationOption(
                action=action,
                description=f"Execute {action.value} to contain the incident",
                confidence=confidence,
                estimated_impact="moderate" if i == 0 else "minimal",
                risks=["May impact legitimate users" if action in [
                    RemediationAction.ISOLATE_HOST,
                    RemediationAction.LOCK_ACCOUNT
                ] else "Minimal risk"],
                prerequisites=["Verify incident is not false positive"],
                execution_steps=[
                    f"1. Verify {action.value} is appropriate",
                    f"2. Execute {action.value} action",
                    "3. Monitor for effectiveness",
                    "4. Document actions taken"
                ]
            )
            options.append(option)
        
        plan = RemediationPlan(
            incident_id=incident_report.incident_id,
            options=options,
            recommended_action=recommended_actions[0] if recommended_actions else None,
            justification=f"Recommended based on {incident_report.severity.value} severity incident"
        )
        
        return plan
