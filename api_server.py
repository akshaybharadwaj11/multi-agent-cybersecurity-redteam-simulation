"""
FastAPI Backend Server for Cyber Defense Simulator UI
Connects the React UI to the actual simulation engine
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys
import logging
from collections import deque
import contextvars
import threading

# Add cyber_defense_simulator to path
sys.path.insert(0, str(Path(__file__).parent / "cyber_defense_simulator"))

from cyber_defense_simulator.core.orchestrator import CyberDefenseOrchestrator
from cyber_defense_simulator.core.data_models import AttackType, SimulationMetrics
from cyber_defense_simulator.core.config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Cyber Defense Simulator API")


class SimulationConfig(BaseModel):
    num_episodes: int = 10
    attack_types: Optional[List[str]] = None
    quick_test: bool = False


# CORS middleware - must be added before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Global state
orchestrator: Optional[CyberDefenseOrchestrator] = None
active_simulations: Dict[str, Dict] = {}
simulation_results: List[Dict] = []
simulation_control: Dict[str, Dict] = {}  # Control flags for pause/stop

# Agent logs storage - store last 1000 log entries per agent
agent_logs: Dict[str, deque] = {
    "red_team": deque(maxlen=1000),
    "detection": deque(maxlen=1000),
    "rag": deque(maxlen=1000),
    "remediation": deque(maxlen=1000),
    "rl_agent": deque(maxlen=1000),
    "orchestrator": deque(maxlen=1000),
}

# Context variable for current simulation_id (works across async boundaries)
_simulation_context_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('simulation_id', default=None)

# Thread-local storage for executor threads (when run_in_executor is used)
_simulation_thread_local = threading.local()


def get_current_simulation_id():
    """Get the current simulation_id from context variable or thread-local storage"""
    # First check thread-local (for executor threads)
    if hasattr(_simulation_thread_local, 'simulation_id'):
        return _simulation_thread_local.simulation_id
    # Then check contextvar (for async tasks)
    try:
        return _simulation_context_var.get()
    except LookupError:
        return None

def set_current_simulation_id(sim_id: Optional[str]):
    """Set the current simulation_id in both context variable and thread-local storage"""
    # Set in contextvar (for async)
    _simulation_context_var.set(sim_id)
    # Set in thread-local (for executor threads)
    _simulation_thread_local.simulation_id = sim_id

def create_log_entry(agent: str, level: str, message: str, **kwargs):
    """Helper function to create log entries with unique IDs"""
    import uuid
    # Get simulation_id from kwargs or thread-local context
    simulation_id = kwargs.get("simulation_id") or get_current_simulation_id()
    return {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message,
        "agent": agent,
        "raw_message": message,
        "module": kwargs.get("module"),
        "funcName": kwargs.get("funcName"),
        "lineno": kwargs.get("lineno"),
        "simulation_id": simulation_id,
    }


class LogHandler(logging.Handler):
    """Custom log handler to capture agent logs"""
    def __init__(self, agent_name: str):
        super().__init__()
        self.agent_name = agent_name
    
    def emit(self, record):
        # Try to get simulation_id from record's extra data, otherwise use context
        simulation_id = getattr(record, 'simulation_id', None) or get_current_simulation_id()
        log_entry = create_log_entry(
            agent=self.agent_name,
            level=record.levelname,
            message=record.getMessage(),
            module=record.module if hasattr(record, 'module') else None,
            funcName=record.funcName if hasattr(record, 'funcName') else None,
            lineno=record.lineno if hasattr(record, 'lineno') else None,
            simulation_id=simulation_id,
        )
        if self.agent_name in agent_logs:
            agent_logs[self.agent_name].append(log_entry)


# Setup custom log handlers for each agent
for agent_name in agent_logs.keys():
    handler = LogHandler(agent_name)
    handler.setLevel(logging.INFO)
    # Get or create logger for each agent
    agent_logger = logging.getLogger(f"agents.{agent_name}")
    agent_logger.addHandler(handler)
    agent_logger.setLevel(logging.INFO)

# Also capture orchestrator logs
orchestrator_handler = LogHandler("orchestrator")
orchestrator_handler.setLevel(logging.INFO)
orchestrator_logger = logging.getLogger("core.orchestrator")
orchestrator_logger.addHandler(orchestrator_handler)
orchestrator_logger.setLevel(logging.INFO)

# Capture agent-specific loggers
red_team_logger = logging.getLogger("agents.red_team_agent")
red_team_handler = LogHandler("red_team")
red_team_handler.setLevel(logging.INFO)
red_team_logger.addHandler(red_team_handler)
red_team_logger.setLevel(logging.INFO)

detection_logger = logging.getLogger("agents.detection_agent")
detection_handler = LogHandler("detection")
detection_handler.setLevel(logging.INFO)
detection_logger.addHandler(detection_handler)
detection_logger.setLevel(logging.INFO)

# RAG agent logger
rag_logger = logging.getLogger("agents.rag_agent")
rag_handler = LogHandler("rag")
rag_handler.setLevel(logging.INFO)
rag_logger.addHandler(rag_handler)
rag_logger.setLevel(logging.INFO)

# RAG vector store logger (for ChromaDB queries) - also goes to "rag" logs
rag_vector_logger = logging.getLogger("rag.vector_store")
rag_vector_handler = LogHandler("rag")
rag_vector_handler.setLevel(logging.INFO)
rag_vector_logger.addHandler(rag_vector_handler)
rag_vector_logger.setLevel(logging.INFO)

remediation_logger = logging.getLogger("agents.remediation_agent")
remediation_handler = LogHandler("remediation")
remediation_handler.setLevel(logging.INFO)
remediation_logger.addHandler(remediation_handler)
remediation_logger.setLevel(logging.INFO)


@app.on_event("startup")
async def startup_event():
    """Initialize orchestrator on startup"""
    global orchestrator
    try:
        logger.info("Initializing Cyber Defense Orchestrator...")
        
        # Try to load the latest trained RL agent
        training_results_dir = Path(__file__).parent / "training_results"
        rl_agent_path = None
        
        if training_results_dir.exists():
            # Find the most recent training result
            result_dirs = sorted(training_results_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
            for result_dir in result_dirs:
                potential_agent = result_dir / "rl_agent.pkl"
                if potential_agent.exists():
                    rl_agent_path = potential_agent
                    logger.info(f"Found trained RL agent: {rl_agent_path}")
                    break
        
        # Try to initialize orchestrator, with fallback if database has issues
        try:
            orchestrator = CyberDefenseOrchestrator(
                initialize_kb=True,
                rl_agent_path=rl_agent_path
            )
            logger.info("Orchestrator initialized successfully")
        except Exception as db_error:
            error_msg = str(db_error)
            if "no such column" in error_msg.lower() or "collections.topic" in error_msg.lower():
                logger.warning(f"Database schema issue detected: {error_msg}")
                logger.info("Attempting to initialize without knowledge base (database will be recreated on next run)...")
                # Try initializing without KB first, then we can recreate it
                try:
                    orchestrator = CyberDefenseOrchestrator(
                        initialize_kb=False,
                        rl_agent_path=rl_agent_path
                    )
                    logger.info("Orchestrator initialized without knowledge base")
                except Exception as e2:
                    logger.error(f"Failed to initialize orchestrator even without KB: {e2}")
                    raise
            else:
                raise
        
        # Log RL agent status
        if rl_agent_path:
            rl_stats = orchestrator.rl_agent.get_statistics()
            log_entry = create_log_entry(
                agent="orchestrator",
                level="INFO",
                message=f"Loaded trained RL agent: {rl_stats['episode_count']} episodes, "
                       f"{rl_stats['num_states']} states, epsilon={rl_stats['epsilon']:.4f}, "
                       f"avg_q={rl_stats['avg_q_value']:.4f}"
            )
            agent_logs["orchestrator"].append(log_entry)
        else:
            log_entry = create_log_entry(
                agent="orchestrator",
                level="INFO",
                message="Using new (untrained) RL agent"
            )
            agent_logs["orchestrator"].append(log_entry)
        
        # Log knowledge base status (if KB was initialized)
        try:
            doc_count = orchestrator.vector_store.get_document_count()
            log_entry = create_log_entry(
                agent="orchestrator",
                level="INFO",
                message=f"Knowledge base initialized with {doc_count} documents"
            )
            agent_logs["orchestrator"].append(log_entry)
        except Exception as kb_error:
            log_entry = create_log_entry(
                agent="orchestrator",
                level="WARNING",
                message=f"Knowledge base not available: {kb_error}"
            )
            agent_logs["orchestrator"].append(log_entry)
        
        # Add orchestrator logs
        log_entry = create_log_entry(
            agent="orchestrator",
            level="INFO",
            message="Orchestrator initialized successfully"
        )
        agent_logs["orchestrator"].append(log_entry)
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        log_entry = create_log_entry(
            agent="orchestrator",
            level="ERROR",
            message=f"Failed to initialize orchestrator: {e}"
        )
        agent_logs["orchestrator"].append(log_entry)


@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Handle OPTIONS requests for CORS preflight"""
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "3600",
        }
    )

@app.get("/")
async def root():
    return {"message": "Cyber Defense Simulator API", "status": "running"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "orchestrator_initialized": orchestrator is not None,
        "episodes_count": len(orchestrator.episodes) if orchestrator else 0,
        "active_simulations": len([s for s in active_simulations.values() if s['status'] == 'running']),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics - REAL DATA ONLY"""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        # Calculate REAL stats from orchestrator
        total_episodes = len(orchestrator.episodes)
        
        if total_episodes == 0:
            # Return zeros if no episodes yet
            return {
                "totalEpisodes": 0,
                "successRate": 0.0,
                "avgReward": 0.0,
                "activeSimulations": len([s for s in active_simulations.values() if s['status'] == 'running']),
                "totalDetections": 0,
                "avgResponseTime": 0.0,
            }
        
        successful = sum(1 for ep in orchestrator.episodes if ep.outcome and ep.outcome.success)
        success_rate = successful / total_episodes
        
        total_reward = sum(ep.reward.reward for ep in orchestrator.episodes if ep.reward)
        avg_reward = total_reward / total_episodes
        
        active_count = len([s for s in active_simulations.values() if s['status'] == 'running'])
        
        total_detections = sum(1 for ep in orchestrator.episodes if ep.incident_report)
        
        # Calculate REAL avg response time from episode durations
        durations = [ep.total_duration for ep in orchestrator.episodes if ep.total_duration and ep.total_duration > 0]
        avg_response_time = sum(durations) / len(durations) if durations else 0.0
        
        return {
            "totalEpisodes": total_episodes,
            "successRate": success_rate,
            "avgReward": avg_reward,
            "activeSimulations": active_count,
            "totalDetections": total_detections,
            "avgResponseTime": avg_response_time,
        }
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating stats: {str(e)}")


@app.get("/api/simulations")
async def get_all_simulations():
    """Get all simulations - both active and completed"""
    if orchestrator is None:
        return []
    
    try:
        simulations = []
        seen_ids = set()
        
        # Get all active simulations (running, completed, failed)
        for sim_id, sim_data in active_simulations.items():
            seen_ids.add(sim_id)
            simulations.append({
                "id": sim_id,
                "name": f"Simulation {sim_id}",
                "attackType": sim_data.get("attack_type", "mixed").replace("_", " ").title(),
                "episodes": sim_data.get("total_episodes", 0),
                "successRate": sim_data.get("success_rate", 0),
                "status": sim_data.get("status", "completed"),
                "progress": sim_data.get("progress", 0),
                "currentEpisode": sim_data.get("current_episode", 0),
                "timestamp": sim_data.get("start_time", datetime.now()),
                "initial_episode_count": sim_data.get("initial_episode_count"),
                "final_episode_count": sim_data.get("final_episode_count"),
            })
        
        # Get completed simulations from simulation_results
        for sim_data in simulation_results:
            sim_id = sim_data.get("id")
            if sim_id and sim_id not in seen_ids:
                seen_ids.add(sim_id)
                simulations.append({
                    "id": sim_id,
                    "name": f"Simulation {sim_id}",
                    "attackType": sim_data.get("attack_type", "mixed").replace("_", " ").title(),
                    "episodes": sim_data.get("total_episodes", 0),
                    "successRate": sim_data.get("success_rate", 0),
                    "status": sim_data.get("status", "completed"),
                    "progress": sim_data.get("progress", 100),
                    "currentEpisode": sim_data.get("current_episode", 0),
                    "timestamp": sim_data.get("start_time", datetime.now()),
                    "initial_episode_count": sim_data.get("initial_episode_count"),
                    "final_episode_count": sim_data.get("final_episode_count"),
                })
        
        # Sort by timestamp (most recent first)
        simulations.sort(key=lambda x: x["timestamp"] if isinstance(x["timestamp"], datetime) else datetime.fromisoformat(str(x["timestamp"])), reverse=True)
        return simulations
    except Exception as e:
        logger.error(f"Error getting simulations: {e}")
        return []


@app.get("/api/simulations/recent")
async def get_recent_simulations(limit: int = 5):
    """Get recent simulations - REAL DATA ONLY"""
    all_sims = await get_all_simulations()
    return all_sims[:limit]


@app.post("/api/simulations/{simulation_id}/pause")
async def pause_simulation(simulation_id: str):
    """Pause a running simulation"""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    if simulation_id not in active_simulations:
        raise HTTPException(status_code=404, detail=f"Simulation {simulation_id} not found")
    
    sim_data = active_simulations[simulation_id]
    if sim_data.get("status") != "running":
        raise HTTPException(status_code=400, detail=f"Simulation {simulation_id} is not running (status: {sim_data.get('status')})")
    
    # Set pause flag
    if simulation_id not in simulation_control:
        simulation_control[simulation_id] = {}
    simulation_control[simulation_id]["paused"] = True
    
    # Update status
    active_simulations[simulation_id]["status"] = "paused"
    
    logger.info(f"Simulation {simulation_id} paused")
    return {"message": f"Simulation {simulation_id} paused", "status": "paused"}


@app.post("/api/simulations/{simulation_id}/resume")
async def resume_simulation(simulation_id: str):
    """Resume a paused simulation"""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    if simulation_id not in active_simulations:
        raise HTTPException(status_code=404, detail=f"Simulation {simulation_id} not found")
    
    sim_data = active_simulations[simulation_id]
    if sim_data.get("status") != "paused":
        raise HTTPException(status_code=400, detail=f"Simulation {simulation_id} is not paused (status: {sim_data.get('status')})")
    
    # Clear pause flag
    if simulation_id in simulation_control:
        simulation_control[simulation_id]["paused"] = False
    
    # Update status
    active_simulations[simulation_id]["status"] = "running"
    
    logger.info(f"Simulation {simulation_id} resumed")
    return {"message": f"Simulation {simulation_id} resumed", "status": "running"}


@app.post("/api/simulations/{simulation_id}/stop")
async def stop_simulation(simulation_id: str):
    """Stop a running or paused simulation"""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    if simulation_id not in active_simulations:
        raise HTTPException(status_code=404, detail=f"Simulation {simulation_id} not found")
    
    sim_data = active_simulations[simulation_id]
    status = sim_data.get("status")
    if status not in ["running", "paused"]:
        raise HTTPException(status_code=400, detail=f"Simulation {simulation_id} cannot be stopped (status: {status})")
    
    # Set stop flag
    if simulation_id not in simulation_control:
        simulation_control[simulation_id] = {}
    simulation_control[simulation_id]["stopped"] = True
    simulation_control[simulation_id]["paused"] = False  # Clear pause if paused
    
    # Update status immediately
    active_simulations[simulation_id]["status"] = "stopped"
    
    logger.info(f"Simulation {simulation_id} stopped by user")
    return {"message": f"Simulation {simulation_id} stopped", "status": "stopped"}


@app.post("/api/simulations/start")
async def start_simulation(config: SimulationConfig, background_tasks: BackgroundTasks):
    """Start a new simulation"""
    try:
        if orchestrator is None:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
        
        # Generate unique simulation ID - each simulation gets its own ID
        # All logs from this simulation will be grouped together in one log stream
        sim_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Parse attack types
        attack_types = None
        if config.attack_types:
            attack_types = [AttackType(at) for at in config.attack_types]
        
        # Store simulation info with initial episode count
        initial_ep_count = len(orchestrator.episodes)
        active_simulations[sim_id] = {
            "id": sim_id,
            "status": "running",
            "progress": 0,
            "current_episode": 0,
            "total_episodes": config.num_episodes,
            "start_time": datetime.now(),
            "attack_type": config.attack_types[0] if config.attack_types else "mixed",
            "success_rate": 0,
            "initial_episode_count": initial_ep_count,
            "final_episode_count": initial_ep_count + config.num_episodes,  # Will be updated when complete
        }
        
        # Log simulation start
        log_entry = create_log_entry(
            agent="orchestrator",
            level="INFO",
            message=f"Starting simulation {sim_id} with {config.num_episodes} episodes",
            simulation_id=sim_id
        )
        agent_logs["orchestrator"].append(log_entry)
        
        # Run simulation in background
        background_tasks.add_task(
            run_simulation_background,
            sim_id,
            config.num_episodes,
            attack_types
        )
        
        return {
            "id": sim_id,
            "status": "running",
            "message": "Simulation started"
        }
    except Exception as e:
        logger.error(f"Error starting simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_simulation_background(sim_id: str, num_episodes: int, attack_types: Optional[List[AttackType]]):
    """Run simulation in background with progress tracking"""
    # Set simulation context for this thread
    set_current_simulation_id(sim_id)
    try:
        logger.info(f"Starting background simulation {sim_id}")
        print(f"[API] Starting background simulation {sim_id}")  # Debug output
        
        # Log start
        log_entry = create_log_entry(
            agent="orchestrator",
            level="INFO",
            message=f"Simulation {sim_id} started - {num_episodes} episodes",
            simulation_id=sim_id
        )
        agent_logs["orchestrator"].append(log_entry)
        
        # Update status
        if sim_id in active_simulations:
            active_simulations[sim_id]["status"] = "running"
            active_simulations[sim_id]["current_episode"] = 0
        
        # Track initial episode count
        initial_episode_count = len(orchestrator.episodes)
        
        # Store episode range in simulation data for filtering
        if sim_id in active_simulations:
            active_simulations[sim_id]["initial_episode_count"] = initial_episode_count
            active_simulations[sim_id]["final_episode_count"] = initial_episode_count + num_episodes
        
        # Initialize control flags
        simulation_control[sim_id] = {"paused": False, "stopped": False}
        
        # Run episodes one by one to track progress
        for episode_num in range(1, num_episodes + 1):
            # Check if simulation was stopped
            if sim_id in simulation_control and simulation_control[sim_id].get("stopped", False):
                logger.info(f"Simulation {sim_id} stopped by user at episode {episode_num}")
                if sim_id in active_simulations:
                    active_simulations[sim_id].update({
                        "status": "stopped",
                        "progress": int((episode_num - 1) / num_episodes * 100),
                        "current_episode": episode_num - 1,
                    })
                break
            
            # Check if simulation is paused - wait until resumed
            while sim_id in simulation_control and simulation_control[sim_id].get("paused", False):
                if simulation_control[sim_id].get("stopped", False):
                    break
                await asyncio.sleep(0.5)  # Check every 500ms
            
            # Check again after pause loop in case it was stopped during pause
            if sim_id in simulation_control and simulation_control[sim_id].get("stopped", False):
                logger.info(f"Simulation {sim_id} stopped by user at episode {episode_num}")
                if sim_id in active_simulations:
                    active_simulations[sim_id].update({
                        "status": "stopped",
                        "progress": int((episode_num - 1) / num_episodes * 100),
                        "current_episode": episode_num - 1,
                    })
                break
            
            try:
                # Select attack type for this episode
                attack_type = None
                if attack_types:
                    attack_type = attack_types[(episode_num - 1) % len(attack_types)]
                
                # Log episode start
                log_entry = create_log_entry(
                    agent="orchestrator",
                    level="INFO",
                    message=f"Starting episode {episode_num}/{num_episodes}",
                    simulation_id=sim_id
                )
                agent_logs["orchestrator"].append(log_entry)
                
                # Run episode (run in executor to avoid blocking async event loop)
                # We need to set simulation_id in the executor thread so agent logs get tagged
                def run_episode_with_simulation_context():
                    # Set simulation context in this thread (keep it for entire simulation)
                    set_current_simulation_id(sim_id)
                    try:
                        print(f"[API] Running episode {episode_num}/{num_episodes} for simulation {sim_id}")
                        episode = orchestrator.run_episode(
                            episode_number=initial_episode_count + episode_num,
                            attack_type=attack_type
                        )
                        print(f"[API] Episode {episode_num} completed successfully")
                        return episode
                    except Exception as e:
                        import traceback
                        print(f"[API] Episode {episode_num} failed with error: {e}")
                        print(f"[API] Traceback: {traceback.format_exc()}")
                        raise
                
                loop = asyncio.get_event_loop()
                episode = await loop.run_in_executor(None, run_episode_with_simulation_context)
                
                # Log agent activities from episode
                if episode.attack_scenario:
                    log_entry = create_log_entry(
                        agent="red_team",
                        level="INFO",
                        message=f"Red Team generated {episode.attack_scenario.attack_type.value} attack with {len(episode.attack_scenario.steps)} steps",
                        simulation_id=sim_id
                    )
                    agent_logs["red_team"].append(log_entry)
                
                if episode.incident_report:
                    log_entry = create_log_entry(
                        agent="detection",
                        level="INFO",
                        message=f"Detection agent identified {episode.incident_report.severity.value} severity incident (confidence: {episode.incident_report.confidence:.2f})",
                        simulation_id=sim_id
                    )
                    agent_logs["detection"].append(log_entry)
                
                if episode.rag_context:
                    # Create detailed retrieval message
                    retrieval_parts = []
                    retrieval_parts.append(f"RAG agent retrieved {len(episode.rag_context.runbooks)} runbooks and {len(episode.rag_context.threat_intel)} threat intel items")
                    
                    if episode.rag_context.runbooks:
                        retrieval_parts.append("\n📚 RUNBOOKS:")
                        for idx, runbook in enumerate(episode.rag_context.runbooks, 1):
                            retrieval_parts.append(f"  [{idx}] {runbook.title} (ID: {runbook.runbook_id})")
                            retrieval_parts.append(f"      Techniques: {', '.join(runbook.applicable_techniques) if runbook.applicable_techniques else 'N/A'}")
                            retrieval_parts.append(f"      Description: {runbook.description[:300]}..." if len(runbook.description) > 300 else f"      Description: {runbook.description}")
                            if runbook.procedures:
                                retrieval_parts.append(f"      Procedures ({len(runbook.procedures)} steps): {', '.join(runbook.procedures[:3])}" + ("..." if len(runbook.procedures) > 3 else ""))
                    
                    if episode.rag_context.threat_intel:
                        retrieval_parts.append("\n🎯 THREAT INTELLIGENCE:")
                        for idx, intel in enumerate(episode.rag_context.threat_intel, 1):
                            retrieval_parts.append(f"  [{idx}] {intel.source} (Relevance: {intel.relevance_score:.4f})")
                            content_preview = intel.content[:300] + "..." if len(intel.content) > 300 else intel.content
                            retrieval_parts.append(f"      Content: {content_preview}")
                            if intel.metadata.get('technique_id'):
                                retrieval_parts.append(f"      MITRE: {intel.metadata.get('technique_id')}")
                    
                    if episode.rag_context.similar_incidents:
                        retrieval_parts.append(f"\n📋 SIMILAR INCIDENTS: {len(episode.rag_context.similar_incidents)} found")
                        for idx, incident in enumerate(episode.rag_context.similar_incidents[:2], 1):
                            retrieval_parts.append(f"  [{idx}] {incident.get('incident_id', 'N/A')} (Similarity: {incident.get('similarity_score', 0):.4f})")
                    
                    detailed_message = "\n".join(retrieval_parts)
                    
                    log_entry = create_log_entry(
                        agent="rag",
                        level="INFO",
                        message=detailed_message,
                        simulation_id=sim_id
                    )
                    agent_logs["rag"].append(log_entry)
                
                if episode.remediation_plan:
                    log_entry = create_log_entry(
                        agent="remediation",
                        level="INFO",
                        message=f"Remediation agent generated {len(episode.remediation_plan.options)} action options, recommended: {episode.remediation_plan.recommended_action.value if episode.remediation_plan.recommended_action else 'none'}",
                        simulation_id=sim_id
                    )
                    agent_logs["remediation"].append(log_entry)
                
                if episode.rl_decision:
                    log_entry = create_log_entry(
                        agent="rl_agent",
                        level="INFO",
                        message=f"RL agent selected action: {episode.rl_decision.selected_action.value} ({'exploration' if episode.rl_decision.is_exploration else 'exploitation'})",
                        simulation_id=sim_id
                    )
                    agent_logs["rl_agent"].append(log_entry)
                
                # Update progress
                if sim_id in active_simulations:
                    progress = (episode_num / num_episodes) * 100
                    active_simulations[sim_id].update({
                        "current_episode": episode_num,
                        "progress": progress,
                    })
                    
                    # Calculate current success rate
                    completed_episodes = [
                        ep for ep in orchestrator.episodes 
                        if ep.episode_number > initial_episode_count
                    ]
                    if completed_episodes:
                        successful = sum(1 for ep in completed_episodes if ep.outcome and ep.outcome.success)
                        active_simulations[sim_id]["success_rate"] = successful / len(completed_episodes)
                
                logger.info(f"Episode {episode_num}/{num_episodes} completed for simulation {sim_id}")
                
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                logger.error(f"Error in episode {episode_num} of simulation {sim_id}: {e}")
                logger.error(f"Traceback: {error_trace}")
                print(f"[API ERROR] Episode {episode_num} failed: {e}")
                print(f"[API ERROR] Traceback: {error_trace}")
                
                log_entry = create_log_entry(
                    agent="orchestrator",
                    level="ERROR",
                    message=f"Error in episode {episode_num}: {str(e)}\n\nTraceback:\n{error_trace[:500]}",
                    simulation_id=sim_id
                )
                agent_logs["orchestrator"].append(log_entry)
                
                # Don't continue if too many errors
                if episode_num > 1:
                    failed_count = sum(1 for ep in orchestrator.episodes 
                                     if ep.episode_number > initial_episode_count and not ep.outcome)
                    if failed_count > num_episodes * 0.5:  # More than 50% failed
                        logger.error(f"Too many failed episodes ({failed_count}), stopping simulation")
                        break
                continue
        
        # Calculate final metrics
        final_episodes = [
            ep for ep in orchestrator.episodes 
            if ep.episode_number > initial_episode_count
        ]
        
        # Update final episode count
        final_episode_count = len(orchestrator.episodes)
        
        if final_episodes:
            successful = sum(1 for ep in final_episodes if ep.outcome and ep.outcome.success)
            total_reward = sum(ep.reward.reward for ep in final_episodes if ep.reward)
            
            # Update final status
            if sim_id in active_simulations:
                active_simulations[sim_id].update({
                    "status": "completed",
                    "progress": 100,
                    "current_episode": num_episodes,
                    "success_rate": successful / len(final_episodes) if len(final_episodes) > 0 else 0,
                    "end_time": datetime.now(),
                    "initial_episode_count": initial_episode_count,
                    "final_episode_count": final_episode_count,
                    "metrics": {
                        "total_episodes": len(final_episodes),
                        "successful_defenses": successful,
                        "failed_defenses": len(final_episodes) - successful,
                        "average_reward": total_reward / len(final_episodes) if final_episodes else 0,
                    }
                })
                
                # Store in simulation_results for persistence (keep last 100)
                sim_copy = active_simulations[sim_id].copy()
                simulation_results.append(sim_copy)
                if len(simulation_results) > 100:
                    simulation_results.pop(0)  # Remove oldest
                
                # Remove from active_simulations since it's completed
                # Keep it in active_simulations for a short time for status queries, but mark as completed
                # The simulation will be available via get_all_simulations() from simulation_results
                
                # Clean up control flags
                if sim_id in simulation_control:
                    del simulation_control[sim_id]
        
        log_entry = create_log_entry(
            agent="orchestrator",
            level="INFO",
            message=f"Simulation {sim_id} completed - {successful}/{len(final_episodes)} successful",
            simulation_id=sim_id
        )
        agent_logs["orchestrator"].append(log_entry)
        
        logger.info(f"Simulation {sim_id} completed")
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error in background simulation {sim_id}: {e}")
        logger.error(f"Traceback: {error_trace}")
        print(f"[API ERROR] Simulation {sim_id} failed: {e}")
        print(f"[API ERROR] Traceback: {error_trace}")
        
        if sim_id in active_simulations:
            active_simulations[sim_id]["status"] = "failed"
        log_entry = create_log_entry(
            agent="orchestrator",
            level="ERROR",
            message=f"Simulation {sim_id} failed: {str(e)}\n\nTraceback:\n{error_trace[:1000]}",
            simulation_id=sim_id
        )
        agent_logs["orchestrator"].append(log_entry)
    finally:
        # Clear simulation context
        set_current_simulation_id(None)


@app.get("/api/simulations/{simulation_id}/status")
async def get_simulation_status(simulation_id: str):
    """Get simulation status with real-time progress"""
    if simulation_id not in active_simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    sim_data = active_simulations[simulation_id].copy()
    
    # Update progress in real-time if running
    if sim_data["status"] == "running" and orchestrator:
        # Get current episode count (this is updated by background task)
        current = sim_data.get("current_episode", 0)
        total = sim_data["total_episodes"]
        progress = min((current / total) * 100, 99) if total > 0 else 0
        sim_data["progress"] = progress
    
    return sim_data


@app.get("/api/simulations/{simulation_id}/episodes")
async def get_simulation_episodes(simulation_id: str):
    """Get episodes for a simulation"""
    if simulation_id not in active_simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    sim_data = active_simulations[simulation_id]
    start_time = sim_data.get("start_time")
    
    # Get episodes that started after this simulation
    if orchestrator and start_time:
        episodes = [
            {
                "episode_number": ep.episode_number,
                "attack_type": ep.attack_scenario.attack_type.value if ep.attack_scenario else "unknown",
                "severity": ep.incident_report.severity.value if ep.incident_report else "unknown",
                "confidence": ep.incident_report.confidence if ep.incident_report else 0,
                "action": ep.rl_decision.selected_action.value if ep.rl_decision else "none",
                "success": ep.outcome.success if ep.outcome else False,
                "reward": ep.reward.reward if ep.reward else 0,
                "duration": ep.total_duration if ep.total_duration else 0,
                "timestamp": ep.start_time.isoformat() if ep.start_time else None,
            }
            for ep in orchestrator.episodes
            if ep.start_time >= start_time
        ]
        return episodes
    
    return []


@app.get("/api/episodes/{episode_number}")
async def get_episode_details(episode_number: int):
    """Get detailed episode information"""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    if episode_number < 1 or episode_number > len(orchestrator.episodes):
        raise HTTPException(status_code=404, detail="Episode not found")
    
    episode = orchestrator.episodes[episode_number - 1]
    
    return {
        "episode_number": episode.episode_number,
        "episode_id": episode.episode_id,
        "attack_scenario": {
            "type": episode.attack_scenario.attack_type.value if episode.attack_scenario else None,
            "target": episode.attack_scenario.target_asset if episode.attack_scenario else None,
            "steps": [
                {
                    "step_number": step.step_number,
                    "technique_id": step.technique_id,
                    "technique_name": step.technique_name,
                    "description": step.description,
                }
                for step in (episode.attack_scenario.steps if episode.attack_scenario else [])
            ]
        },
        "incident_report": {
            "severity": episode.incident_report.severity.value if episode.incident_report else None,
            "confidence": episode.incident_report.confidence if episode.incident_report else None,
            "summary": episode.incident_report.summary if episode.incident_report else None,
            "mitre_techniques": episode.incident_report.mitre_techniques if episode.incident_report else [],
        },
        "remediation": {
            "recommended_action": episode.remediation_plan.recommended_action.value if episode.remediation_plan and episode.remediation_plan.recommended_action else None,
            "options": [
                {
                    "action": opt.action.value,
                    "confidence": opt.confidence,
                    "description": opt.description,
                }
                for opt in (episode.remediation_plan.options if episode.remediation_plan else [])
            ]
        },
        "rl_decision": {
            "selected_action": episode.rl_decision.selected_action.value if episode.rl_decision else None,
            "is_exploration": episode.rl_decision.is_exploration if episode.rl_decision else False,
            "epsilon": episode.rl_decision.epsilon if episode.rl_decision else 0,
            "q_values": episode.rl_decision.q_values if episode.rl_decision else {},
            "state": {
                "incident_severity": episode.rl_decision.state.incident_severity.value if episode.rl_decision and episode.rl_decision.state else None,
                "attack_type": episode.rl_decision.state.attack_type.value if episode.rl_decision and episode.rl_decision.state else None,
                "confidence_level": episode.rl_decision.state.confidence_level if episode.rl_decision and episode.rl_decision.state else None,
            } if episode.rl_decision else None,
        },
        "rag_context": {
            "runbooks": [
                {
                    "runbook_id": rb.runbook_id,
                    "title": rb.title,
                    "description": rb.description,
                    "applicable_techniques": rb.applicable_techniques,
                    "procedures": rb.procedures,
                }
                for rb in (episode.rag_context.runbooks if episode.rag_context else [])
            ],
            "threat_intel": [
                {
                    "source": ti.source,
                    "content": ti.content,
                    "relevance_score": ti.relevance_score,
                    "metadata": ti.metadata,
                }
                for ti in (episode.rag_context.threat_intel if episode.rag_context else [])
            ],
            "similar_incidents": episode.rag_context.similar_incidents if episode.rag_context else [],
        } if episode.rag_context else None,
        "outcome": {
            "success": episode.outcome.success if episode.outcome else False,
            "false_positive": episode.outcome.false_positive if episode.outcome else False,
            "collateral_damage": episode.outcome.collateral_damage if episode.outcome else False,
        },
        "reward": episode.reward.reward if episode.reward else 0,
        "duration": episode.total_duration if episode.total_duration else 0,
        "timestamp": episode.start_time.isoformat() if episode.start_time else None,
    }


@app.get("/api/agents/status")
async def get_agent_status():
    """Get agent status - REAL DATA"""
    try:
        if orchestrator is None:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
        
        # Get last episode to determine agent activity
        last_episode = orchestrator.episodes[-1] if orchestrator.episodes else None
        
        # Determine if agents are active based on recent episodes
        is_active = len(orchestrator.episodes) > 0
        last_activity = last_episode.start_time if last_episode and last_episode.start_time else datetime.now()
        
        return {
            "redTeam": {
                "status": "active" if is_active else "idle",
                "lastActivity": last_activity.isoformat(),
                "tasksCompleted": len(orchestrator.episodes),
            },
            "detection": {
                "status": "active" if is_active and last_episode and last_episode.incident_report else "idle",
                "lastActivity": last_activity.isoformat(),
                "tasksCompleted": sum(1 for ep in orchestrator.episodes if ep.incident_report),
            },
            "rag": {
                "status": "active" if is_active and last_episode and last_episode.rag_context else "idle",
                "lastActivity": last_activity.isoformat(),
                "tasksCompleted": sum(1 for ep in orchestrator.episodes if ep.rag_context),
            },
            "remediation": {
                "status": "active" if is_active and last_episode and last_episode.remediation_plan else "idle",
                "lastActivity": last_activity.isoformat(),
                "tasksCompleted": sum(1 for ep in orchestrator.episodes if ep.remediation_plan),
            },
        }
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/logs")
async def get_agent_logs(agent: Optional[str] = None, limit: int = 100):
    """Get agent logs - REAL LOGS"""
    try:
        if agent:
            # Get logs for specific agent
            if agent not in agent_logs:
                raise HTTPException(status_code=404, detail=f"Agent '{agent}' not found")
            logs = list(agent_logs[agent])[-limit:]
        else:
            # Get logs from all agents, merged and sorted
            all_logs = []
            for agent_name, log_deque in agent_logs.items():
                for log_entry in log_deque:
                    all_logs.append(log_entry)
            # Sort by timestamp
            all_logs.sort(key=lambda x: x["timestamp"])
            logs = all_logs[-limit:]
        
        return {
            "logs": logs,
            "total": len(logs),
            "agent": agent or "all",
        }
    except Exception as e:
        logger.error(f"Error getting agent logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/logs/{log_id}")
async def get_log_details(log_id: str):
    """Get detailed information for a specific log entry"""
    try:
        # Search all agents for the log with this ID
        for agent_name, log_deque in agent_logs.items():
            for log_entry in log_deque:
                if log_entry.get("id") == log_id:
                    return log_entry
        
        raise HTTPException(status_code=404, detail=f"Log entry '{log_id}' not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting log details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rl/metrics")
async def get_rl_metrics(simulation_id: Optional[str] = None):
    """Get RL agent metrics and statistics, optionally filtered by simulation_id"""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        # Filter episodes by simulation if simulation_id provided
        filtered_episodes = orchestrator.episodes
        if simulation_id:
            # Find simulation episode range
            initial_ep = None
            final_ep = None
            
            if simulation_id in active_simulations:
                sim_data = active_simulations[simulation_id]
                initial_ep = sim_data.get("initial_episode_count")
                final_ep = sim_data.get("final_episode_count")
            else:
                # Check simulation_results
                for sim_data in simulation_results:
                    if sim_data.get("id") == simulation_id:
                        initial_ep = sim_data.get("initial_episode_count")
                        final_ep = sim_data.get("final_episode_count")
                        break
            
            if initial_ep is not None:
                # Filter episodes by episode number range (more reliable than timestamps)
                if final_ep is not None:
                    # Use episode number range (episodes are 1-indexed, initial_ep is 0-indexed count)
                    # So if initial_ep=0, we want episodes 1, 2, 3... up to final_ep
                    filtered_episodes = [
                        ep for ep in orchestrator.episodes
                        if ep.episode_number > initial_ep and ep.episode_number <= final_ep
                    ]
                    logger.info(f"Filtering episodes for {simulation_id}: initial_ep={initial_ep}, final_ep={final_ep}, found {len(filtered_episodes)} episodes")
                else:
                    # Only initial_ep available, get all episodes after it
                    filtered_episodes = [
                        ep for ep in orchestrator.episodes
                        if ep.episode_number > initial_ep
                    ]
                    logger.info(f"Filtering episodes for {simulation_id}: initial_ep={initial_ep}, found {len(filtered_episodes)} episodes (no final_ep)")
            else:
                # Simulation not found, return empty data
                filtered_episodes = []
                logger.warning(f"Simulation {simulation_id} not found or missing episode range data")
        
        # Get fresh statistics from RL agent (global stats)
        rl_stats = orchestrator.rl_agent.get_statistics()
        
        # Get Q-value trends from filtered episodes
        q_value_history = []
        epsilon_history = []
        
        if filtered_episodes:
            # Use all filtered episodes (not just last 50)
            for episode in filtered_episodes:
                if episode.rl_decision:
                    # Get Q-value for selected action
                    q_vals = episode.rl_decision.q_values
                    if q_vals:
                        selected_q = q_vals.get(episode.rl_decision.selected_action.value, 0.0)
                        q_value_history.append({
                            "episode": episode.episode_number,
                            "q_value": selected_q,
                            "epsilon": episode.rl_decision.epsilon,
                            "is_exploration": episode.rl_decision.is_exploration,
                            "reward": episode.reward.reward if episode.reward else 0.0,
                        })
                        epsilon_history.append({
                            "episode": episode.episode_number,
                            "epsilon": episode.rl_decision.epsilon,
                        })
        
        # Calculate exploration vs exploitation ratio from filtered episodes
        recent_episodes = [ep for ep in filtered_episodes[-20:] if ep.rl_decision]
        exploration_count = sum(1 for ep in recent_episodes if ep.rl_decision.is_exploration)
        exploitation_count = len(recent_episodes) - exploration_count
        
        # Calculate episode count for filtered episodes
        filtered_episode_count = len([ep for ep in filtered_episodes if ep.rl_decision])
        
        # Calculate action distribution for filtered episodes
        filtered_action_counts = {}
        for episode in filtered_episodes:
            if episode.rl_decision:
                action = episode.rl_decision.selected_action.value
                filtered_action_counts[action] = filtered_action_counts.get(action, 0) + 1
        
        # Calculate success rate and reward metrics from filtered episodes
        successful_episodes = sum(1 for ep in filtered_episodes if ep.outcome and ep.outcome.success)
        total_with_outcome = sum(1 for ep in filtered_episodes if ep.outcome)
        success_rate = successful_episodes / total_with_outcome if total_with_outcome > 0 else 0.0
        
        # Calculate reward statistics
        rewards = [ep.reward.reward for ep in filtered_episodes if ep.reward]
        avg_reward = sum(rewards) / len(rewards) if rewards else 0.0
        max_reward = max(rewards) if rewards else 0.0
        min_reward = min(rewards) if rewards else 0.0
        
        # Calculate reward trend (last 10 vs first 10)
        if len(rewards) >= 20:
            recent_rewards = rewards[-10:]
            early_rewards = rewards[:10]
            recent_avg = sum(recent_rewards) / len(recent_rewards)
            early_avg = sum(early_rewards) / len(early_rewards)
            reward_trend = recent_avg - early_avg
        else:
            reward_trend = 0.0
        
        # Calculate success rate trend
        if len(filtered_episodes) >= 20:
            recent_episodes = filtered_episodes[-10:]
            early_episodes = filtered_episodes[:10]
            recent_success = sum(1 for ep in recent_episodes if ep.outcome and ep.outcome.success) / len([ep for ep in recent_episodes if ep.outcome]) if len([ep for ep in recent_episodes if ep.outcome]) > 0 else 0
            early_success = sum(1 for ep in early_episodes if ep.outcome and ep.outcome.success) / len([ep for ep in early_episodes if ep.outcome]) if len([ep for ep in early_episodes if ep.outcome]) > 0 else 0
            success_trend = recent_success - early_success
        else:
            success_trend = 0.0
        
        # Calculate false positive and collateral damage rates
        false_positives = sum(1 for ep in filtered_episodes if ep.outcome and ep.outcome.false_positive)
        collateral_damage = sum(1 for ep in filtered_episodes if ep.outcome and ep.outcome.collateral_damage)
        false_positive_rate = false_positives / total_with_outcome if total_with_outcome > 0 else 0.0
        collateral_damage_rate = collateral_damage / total_with_outcome if total_with_outcome > 0 else 0.0
        
        # Calculate average response time
        response_times = [ep.outcome.time_to_remediate for ep in filtered_episodes if ep.outcome and ep.outcome.time_to_remediate]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        
        # Prepare success rate history
        success_rate_history = []
        if filtered_episodes:
            window_size = max(10, len(filtered_episodes) // 20)  # Adaptive window size
            for i in range(0, len(filtered_episodes), window_size):
                window_episodes = filtered_episodes[i:i+window_size]
                window_successful = sum(1 for ep in window_episodes if ep.outcome and ep.outcome.success)
                window_total = sum(1 for ep in window_episodes if ep.outcome)
                if window_total > 0:
                    success_rate_history.append({
                        "episode": window_episodes[0].episode_number,
                        "success_rate": window_successful / window_total,
                        "window_size": window_total
                    })
        
        return {
            "simulation_id": simulation_id,  # Include simulation_id in response
            "parameters": {
                "learning_rate": orchestrator.rl_agent.learning_rate,
                "epsilon": orchestrator.rl_agent.epsilon,
                "epsilon_decay": orchestrator.rl_agent.epsilon_decay,
                "min_epsilon": orchestrator.rl_agent.min_epsilon,
                "discount_factor": orchestrator.rl_agent.discount_factor,
                "q_init": orchestrator.rl_agent.q_init,
            },
            "statistics": {
                "episode_count": filtered_episode_count,  # Use filtered count
                "update_count": rl_stats["update_count"],  # Global update count
                "num_states": rl_stats["num_states"],  # Global state count
                "avg_q_value": float(rl_stats["avg_q_value"]),
                "max_q_value": float(rl_stats.get("max_q_value", 0.0)),  # New metric from improved RL core
                "current_epsilon": float(rl_stats["epsilon"]),
                "is_learning": bool(rl_stats["update_count"] > 0),  # Explicitly convert to bool
            },
            "action_distribution": {
                action.replace("_", " ").title(): count
                for action, count in filtered_action_counts.items()
            } if filtered_action_counts else {
                action.replace("_", " ").title(): count
                for action, count in rl_stats["action_distribution"].items()
            },
            "exploration_ratio": {
                "exploration": exploration_count,
                "exploitation": exploitation_count,
                "ratio": exploration_count / len(recent_episodes) if recent_episodes else 0.0,
            },
            "performance_metrics": {
                "success_rate": float(success_rate),
                "success_trend": float(success_trend),
                "avg_reward": float(avg_reward),
                "max_reward": float(max_reward),
                "min_reward": float(min_reward),
                "reward_trend": float(reward_trend),
                "false_positive_rate": float(false_positive_rate),
                "collateral_damage_rate": float(collateral_damage_rate),
                "avg_response_time": float(avg_response_time),
            },
            "q_value_history": q_value_history,  # All filtered episodes
            "epsilon_history": epsilon_history,  # All filtered episodes
            "success_rate_history": success_rate_history,  # Success rate over time
        }
    except Exception as e:
        logger.error(f"Error getting RL metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics")
async def get_analytics(range: str = "24h"):
    """Get analytics data - REAL DATA ONLY"""
    if orchestrator is None:
        return {
            "episodes": [],
            "rewards": [],
            "actions": [],
            "performance_metrics": [],
        }
    
    try:
        # Get REAL episodes from orchestrator
        episodes = orchestrator.episodes[-50:] if orchestrator.episodes else []
        
        if not episodes:
            return {
                "episodes": [],
                "rewards": [],
                "actions": [],
                "performance_metrics": [],
            }
        
        # REAL reward data
        reward_data = [
            {
                "episode": i + 1,
                "reward": ep.reward.reward if ep.reward else 0.0,
            }
            for i, ep in enumerate(episodes)
        ]
        
        # REAL action distribution
        action_counts = {}
        for ep in episodes:
            if ep.rl_decision and ep.rl_decision.selected_action:
                action = ep.rl_decision.selected_action.value
                action_counts[action] = action_counts.get(action, 0) + 1
        
        # Calculate attack type statistics
        attack_type_stats = {}
        for ep in episodes:
            if ep.attack_scenario:
                attack_type = ep.attack_scenario.attack_type.value
                if attack_type not in attack_type_stats:
                    attack_type_stats[attack_type] = {"count": 0, "success": 0}
                attack_type_stats[attack_type]["count"] += 1
                if ep.outcome and ep.outcome.success:
                    attack_type_stats[attack_type]["success"] += 1
        
        attack_type_data = [
            {
                "type": k.replace("_", " ").title(),
                "count": v["count"],
                "success": v["success"]
            }
            for k, v in attack_type_stats.items()
        ]
        
        # Calculate time-series metrics for performance chart
        # Group episodes by time buckets (hourly)
        from collections import defaultdict
        from datetime import datetime, timedelta
        
        time_series_data = defaultdict(lambda: {"rewards": [], "successes": 0, "detections": 0, "total": 0})
        
        for ep in episodes:
            if ep.start_time:
                # Round to nearest hour
                hour_key = ep.start_time.replace(minute=0, second=0, microsecond=0)
                time_series_data[hour_key]["total"] += 1
                if ep.reward:
                    time_series_data[hour_key]["rewards"].append(ep.reward.reward)
                if ep.outcome and ep.outcome.success:
                    time_series_data[hour_key]["successes"] += 1
                if ep.incident_report and ep.incident_report.confidence > 0.5:
                    time_series_data[hour_key]["detections"] += 1
        
        # Convert to chart format
        performance_metrics = []
        sorted_times = sorted(time_series_data.keys())
        
        # Get last 6 hours or all available data
        now = datetime.now()
        cutoff_time = now - timedelta(hours=6)
        filtered_times = [t for t in sorted_times if t >= cutoff_time]
        
        for time_key in filtered_times[-7:]:  # Last 7 data points
            data = time_series_data[time_key]
            avg_reward = sum(data["rewards"]) / len(data["rewards"]) if data["rewards"] else 0.0
            success_rate = data["successes"] / data["total"] if data["total"] > 0 else 0.0
            detection_rate = data["detections"] / data["total"] if data["total"] > 0 else 0.0
            
            # Normalize reward to 0-1 range for chart (from -1,1 range)
            performance_metrics.append({
                "time": time_key.strftime("%H:%M"),
                "reward": max(0, min(1, (avg_reward + 1) / 2)),  # Normalize from -1,1 to 0,1
                "success": success_rate,
                "detection": detection_rate
            })
        
        return {
            "episodes": reward_data,
            "rewards": reward_data,
            "actions": [{"name": k, "value": v} for k, v in action_counts.items()],
            "attackTypes": attack_type_data,
            "performance_metrics": performance_metrics,  # Add time-series data
        }
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return {
            "episodes": [],
            "rewards": [],
            "actions": [],
            "performance_metrics": [],
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
