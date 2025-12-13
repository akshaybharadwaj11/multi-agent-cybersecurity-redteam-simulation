"""
RAG Agent - Threat Intelligence and Runbook Retrieval
Retrieves relevant context from knowledge base to support decision-making
"""

from crewai import Agent, Task
from typing import List
import logging

from cyber_defense_simulator.core.data_models import IncidentReport, RAGContext, ThreatIntelligence, Runbook
from cyber_defense_simulator.rag.vector_store import VectorStore
from cyber_defense_simulator.core.config import Config

logger = logging.getLogger(__name__)


class RAGAgent:
    """Retrieves threat intelligence and runbooks using RAG"""
    
    def __init__(self, vector_store: VectorStore):
        """
        Initialize RAG agent
        
        Args:
            vector_store: Vector store with knowledge base
        """
        self.vector_store = vector_store
        
        self.agent = Agent(
            role="Threat Intelligence Analyst",
            goal="Retrieve relevant threat intelligence, runbooks, and past incident data to support security operations",
            backstory="""You are a threat intelligence analyst specializing in cyber threat research 
            and knowledge management. You maintain comprehensive databases of security runbooks, 
            MITRE ATT&CK techniques, vulnerability data, and historical incident reports. You excel 
            at quickly finding relevant information to support incident response and providing context 
            that helps responders make informed decisions.""",
            verbose=Config.CREW_VERBOSE,
            allow_delegation=False,
            llm=Config.get_llm()
        )
        
        logger.info("Initialized RAG Agent")
    
    def create_retrieval_task(self, incident_report: IncidentReport) -> Task:
        """
        Create task for context retrieval
        
        Args:
            incident_report: Incident report to find context for
            
        Returns:
            CrewAI Task
        """
        task = Task(
            description=f"""
            Retrieve relevant threat intelligence and response guidance for this incident:
            
            INCIDENT SUMMARY:
            - Severity: {incident_report.severity.value}
            - Techniques: {', '.join(incident_report.mitre_techniques)}
            - Summary: {incident_report.summary}
            
            RETRIEVAL TASKS:
            1. Find security runbooks matching the detected MITRE techniques
            2. Retrieve threat intelligence about similar attack patterns
            3. Search for past incidents with similar characteristics
            4. Identify applicable response procedures
            
            Prioritize:
            - Direct matches to MITRE techniques
            - High-confidence, actionable guidance
            - Recent and relevant threat intelligence
            
            Provide brief summaries of retrieved information with relevance scores.
            """,
            agent=self.agent,
            expected_output="Summary of retrieved context"
        )
        
        return task
    
    def retrieve_context(self, incident_report: IncidentReport) -> RAGContext:
        """
        Retrieve relevant context for incident
        
        Args:
            incident_report: Incident report
            
        Returns:
            RAGContext with retrieved information
        """
        logger.info(f"Retrieving context for incident {incident_report.incident_id}")
        
        context = RAGContext(incident_id=incident_report.incident_id)
        
        try:
            # Retrieve runbooks for each MITRE technique
            if incident_report.mitre_techniques:
                for technique in incident_report.mitre_techniques:
                    try:
                        runbooks = self._retrieve_runbooks(technique)
                        if runbooks:
                            context.runbooks.extend(runbooks)
                        else:
                            # No results - add fallback
                            context.runbooks.append(self._create_fallback_runbook(technique))
                    except Exception as e:
                        logger.warning(f"Failed to retrieve runbooks for {technique}: {e}")
                        # Add fallback runbook
                        context.runbooks.append(self._create_fallback_runbook(technique))
            else:
                # No techniques - add generic fallback
                context.runbooks.append(self._create_fallback_runbook("T1059"))
            
            # Retrieve threat intelligence
            try:
                threat_intel = self._retrieve_threat_intelligence(incident_report)
                if threat_intel:
                    context.threat_intel.extend(threat_intel)
                else:
                    # No results - add fallback
                    context.threat_intel.append(self._create_fallback_threat_intel(incident_report))
            except Exception as e:
                logger.warning(f"Failed to retrieve threat intelligence: {e}")
                # Add fallback threat intel
                context.threat_intel.append(self._create_fallback_threat_intel(incident_report))
            
            # Find similar past incidents
            try:
                similar_incidents = self._retrieve_similar_incidents(incident_report)
                if similar_incidents:
                    context.similar_incidents.extend(similar_incidents)
            except Exception as e:
                logger.warning(f"Failed to retrieve similar incidents: {e}")
                # Continue without similar incidents - not critical
        
        except Exception as e:
            logger.error(f"Error in RAG retrieval: {e}. Using fallback context.")
            # Ensure we have at least some context
            if not context.runbooks:
                if incident_report.mitre_techniques:
                    for technique in incident_report.mitre_techniques:
                        context.runbooks.append(self._create_fallback_runbook(technique))
                else:
                    context.runbooks.append(self._create_fallback_runbook("T1059"))
            
            if not context.threat_intel:
                context.threat_intel.append(self._create_fallback_threat_intel(incident_report))
        
        logger.info(
            f"Retrieved {len(context.runbooks)} runbooks, "
            f"{len(context.threat_intel)} threat intel items, "
            f"{len(context.similar_incidents)} similar incidents"
        )
        
        return context
    
    def _retrieve_runbooks(self, technique_id: str) -> List[Runbook]:
        """
        Retrieve runbooks for a MITRE technique
        
        Args:
            technique_id: MITRE ATT&CK technique ID
            
        Returns:
            List of relevant runbooks
        """
        # Search vector store
        results = self.vector_store.search_by_mitre_technique(
            technique_id=technique_id,
            top_k=2
        )
        
        runbooks = []
        for doc, metadata, score in results:
            if metadata.get('type') == 'runbook':
                # Parse runbook from document
                runbook = Runbook(
                    runbook_id=metadata.get('id', 'unknown'),
                    title=metadata.get('title', 'Security Runbook'),
                    description=doc[:200] + "..." if len(doc) > 200 else doc,
                    applicable_techniques=[technique_id],
                    procedures=self._extract_procedures(doc),
                    prerequisites=[],
                    expected_outcomes=[]
                )
                runbooks.append(runbook)
        
        return runbooks
    
    def _retrieve_threat_intelligence(
        self,
        incident_report: IncidentReport
    ) -> List[ThreatIntelligence]:
        """
        Retrieve threat intelligence relevant to incident
        
        Args:
            incident_report: Incident report
            
        Returns:
            List of threat intelligence
        """
        # Build search query from incident
        query = f"{incident_report.summary} {' '.join(incident_report.mitre_techniques)}"
        
        results = self.vector_store.search(
            query=query,
            top_k=3,
            filters={"type": "mitre_technique"}
        )
        
        threat_intel = []
        for doc, metadata, score in results:
            intel = ThreatIntelligence(
                source=f"MITRE {metadata.get('technique_id', 'unknown')}",
                content=doc,
                relevance_score=score,
                metadata=metadata
            )
            threat_intel.append(intel)
        
        return threat_intel
    
    def _retrieve_similar_incidents(
        self,
        incident_report: IncidentReport
    ) -> List[dict]:
        """
        Find similar past incidents
        
        Args:
            incident_report: Current incident
            
        Returns:
            List of similar incidents
        """
        results = self.vector_store.search_similar_incidents(
            incident_description=incident_report.summary,
            top_k=2
        )
        
        incidents = []
        for doc, metadata, score in results:
            if metadata.get('type') == 'incident':
                incidents.append({
                    "incident_id": metadata.get('incident_id', 'unknown'),
                    "description": doc[:300] + "..." if len(doc) > 300 else doc,
                    "similarity_score": score
                })
        
        return incidents
    
    def _extract_procedures(self, runbook_text: str) -> List[str]:
        """Extract key procedures from runbook text"""
        procedures = []
        
        # Simple extraction - look for numbered items or action verbs
        lines = runbook_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and (
                line[0].isdigit() or
                any(line.lower().startswith(verb) for verb in [
                    'block', 'quarantine', 'isolate', 'terminate',
                    'lock', 'reset', 'disable', 'enable', 'scan'
                ])
            ):
                procedures.append(line)
        
        return procedures[:5]  # Top 5 procedures
    
    def _create_fallback_runbook(self, technique_id: str) -> Runbook:
        """Create fallback runbook when retrieval fails"""
        return Runbook(
            runbook_id=f"fallback_{technique_id}",
            title=f"Security Response for {technique_id}",
            description=f"General security response procedures for MITRE ATT&CK technique {technique_id}",
            applicable_techniques=[technique_id],
            procedures=[
                "1. Isolate affected systems from network",
                "2. Block malicious IP addresses",
                "3. Lock compromised accounts",
                "4. Scan systems for additional threats",
                "5. Notify security team"
            ],
            prerequisites=["Network access", "Administrative privileges"],
            expected_outcomes=["Threat contained", "Systems secured"]
        )
    
    def _create_fallback_threat_intel(self, incident_report: IncidentReport) -> ThreatIntelligence:
        """Create fallback threat intelligence when retrieval fails"""
        return ThreatIntelligence(
            source="MITRE ATT&CK Framework",
            content=f"Threat intelligence for {', '.join(incident_report.mitre_techniques)}. "
                   f"Incident severity: {incident_report.severity.value}. "
                   f"Recommended immediate containment actions.",
            relevance_score=0.7,
            metadata={"type": "fallback", "techniques": incident_report.mitre_techniques}
        )
