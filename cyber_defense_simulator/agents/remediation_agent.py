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
            llm=Config.get_llm(),
            memory=False  # Disable memory to prevent response caching
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
            result = task.execute()
            
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
        
        for opt_data in data.get('options', []):
            # Normalize action string to lowercase to match enum values
            action_str = opt_data['action'].lower().replace(' ', '_')
            try:
                action = RemediationAction(action_str)
            except ValueError:
                # Try to find matching enum by name (case-insensitive)
                action_name = opt_data['action'].upper().replace(' ', '_')
                try:
                    action = RemediationAction[action_name]
                except KeyError:
                    logger.warning(f"Invalid action '{opt_data['action']}', using NOTIFY_TEAM as fallback")
                    action = RemediationAction.NOTIFY_TEAM
            
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
        
        recommended_str = data.get('recommended_action')
        if recommended_str:
            # Normalize recommended action
            rec_action_str = recommended_str.lower().replace(' ', '_')
            try:
                recommended = RemediationAction(rec_action_str)
            except ValueError:
                rec_action_name = recommended_str.upper().replace(' ', '_')
                try:
                    recommended = RemediationAction[rec_action_name]
                except KeyError:
                    logger.warning(f"Invalid recommended action '{recommended_str}', using None")
                    recommended = None
        else:
            recommended = None
        
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
