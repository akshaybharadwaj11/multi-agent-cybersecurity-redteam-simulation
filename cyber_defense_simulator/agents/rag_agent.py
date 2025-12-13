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
            llm=Config.get_llm(),
            memory=False  # Disable memory to prevent response caching
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
        
        # Retrieve runbooks for each MITRE technique
        for technique in incident_report.mitre_techniques:
            runbooks = self._retrieve_runbooks(technique)
            context.runbooks.extend(runbooks)
        
        # Retrieve threat intelligence
        threat_intel = self._retrieve_threat_intelligence(incident_report)
        context.threat_intel.extend(threat_intel)
        
        # Find similar past incidents
        similar_incidents = self._retrieve_similar_incidents(incident_report)
        context.similar_incidents.extend(similar_incidents)
        
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
        logger.info(f"🔍 Searching ChromaDB for runbooks matching MITRE technique: {technique_id}")
        
        # Search vector store
        results = self.vector_store.search_by_mitre_technique(
            technique_id=technique_id,
            top_k=2
        )
        
        logger.info(f"📚 ChromaDB returned {len(results)} results for technique {technique_id}")
        
        runbooks = []
        for idx, (doc, metadata, score) in enumerate(results, 1):
            if metadata.get('type') == 'runbook':
                runbook_id = metadata.get('id', 'unknown')
                title = metadata.get('title', 'Security Runbook')
                techniques = metadata.get('techniques', 'N/A')
                
                # Log detailed retrieval information
                logger.info(
                    f"📖 Retrieved Runbook #{idx}:\n"
                    f"   ID: {runbook_id}\n"
                    f"   Title: {title}\n"
                    f"   Techniques: {techniques}\n"
                    f"   Similarity Score: {score:.4f}\n"
                    f"   Content Preview: {doc[:150]}..."
                )
                
                # Parse runbook from document
                runbook = Runbook(
                    runbook_id=runbook_id,
                    title=title,
                    description=doc[:200] + "..." if len(doc) > 200 else doc,
                    applicable_techniques=[technique_id],
                    procedures=self._extract_procedures(doc),
                    prerequisites=[],
                    expected_outcomes=[]
                )
                runbooks.append(runbook)
        
        if not runbooks:
            logger.warning(f"⚠️  No runbooks found for technique {technique_id}")
        
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
        
        logger.info(f"🔍 Searching ChromaDB for threat intelligence with query: {query[:100]}...")
        
        results = self.vector_store.search(
            query=query,
            top_k=3,
            filters={"type": "mitre_technique"}
        )
        
        logger.info(f"📊 ChromaDB returned {len(results)} threat intelligence results")
        
        threat_intel = []
        for idx, (doc, metadata, score) in enumerate(results, 1):
            technique_id = metadata.get('technique_id', 'unknown')
            source = f"MITRE {technique_id}"
            
            # Log detailed retrieval information
            logger.info(
                f"🎯 Retrieved Threat Intelligence #{idx}:\n"
                f"   Source: {source}\n"
                f"   Technique ID: {technique_id}\n"
                f"   Similarity Score: {score:.4f}\n"
                f"   Content Preview: {doc[:150]}..."
            )
            
            intel = ThreatIntelligence(
                source=source,
                content=doc,
                relevance_score=score,
                metadata=metadata
            )
            threat_intel.append(intel)
        
        if not threat_intel:
            logger.warning(f"⚠️  No threat intelligence found for query")
        
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
        logger.info(f"🔍 Searching ChromaDB for similar incidents: {incident_report.summary[:100]}...")
        
        results = self.vector_store.search_similar_incidents(
            incident_description=incident_report.summary,
            top_k=2
        )
        
        logger.info(f"📋 ChromaDB returned {len(results)} similar incident results")
        
        incidents = []
        for idx, (doc, metadata, score) in enumerate(results, 1):
            if metadata.get('type') == 'incident':
                incident_id = metadata.get('incident_id', 'unknown')
                
                # Log detailed retrieval information
                logger.info(
                    f"📝 Retrieved Similar Incident #{idx}:\n"
                    f"   Incident ID: {incident_id}\n"
                    f"   Similarity Score: {score:.4f}\n"
                    f"   Description Preview: {doc[:150]}..."
                )
                
                incidents.append({
                    "incident_id": incident_id,
                    "description": doc[:300] + "..." if len(doc) > 300 else doc,
                    "similarity_score": score
                })
        
        if not incidents:
            logger.warning(f"⚠️  No similar incidents found")
        
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
