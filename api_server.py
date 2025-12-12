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

# Add cyber_defense_simulator to path
sys.path.insert(0, str(Path(__file__).parent / "cyber_defense_simulator"))

from core.orchestrator import CyberDefenseOrchestrator
from core.data_models import AttackType, SimulationMetrics
from core.config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Cyber Defense Simulator API")


class SimulationConfig(BaseModel):
    num_episodes: int = 10
    attack_types: Optional[List[str]] = None
    quick_test: bool = False


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
orchestrator: Optional[CyberDefenseOrchestrator] = None
active_simulations: Dict[str, Dict] = {}
simulation_results: List[Dict] = []

# Agent logs storage - store last 1000 log entries per agent
agent_logs: Dict[str, deque] = {
    "red_team": deque(maxlen=1000),
    "detection": deque(maxlen=1000),
    "rag": deque(maxlen=1000),
    "remediation": deque(maxlen=1000),
    "rl_agent": deque(maxlen=1000),
    "orchestrator": deque(maxlen=1000),
}


def create_log_entry(agent: str, level: str, message: str, **kwargs):
    """Helper function to create log entries with unique IDs"""
    import uuid
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
    }


class LogHandler(logging.Handler):
    """Custom log handler to capture agent logs"""
    def __init__(self, agent_name: str):
        super().__init__()
        self.agent_name = agent_name
    
    def emit(self, record):
        log_entry = create_log_entry(
            agent=self.agent_name,
            level=record.levelname,
            message=record.getMessage(),
            module=record.module if hasattr(record, 'module') else None,
            funcName=record.funcName if hasattr(record, 'funcName') else None,
            lineno=record.lineno if hasattr(record, 'lineno') else None,
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

detection_logger = logging.getLogger("agents.detection_agent")
detection_handler = LogHandler("detection")
detection_handler.setLevel(logging.INFO)
detection_logger.addHandler(detection_handler)

rag_logger = logging.getLogger("agents.rag_agent")
rag_handler = LogHandler("rag")
rag_handler.setLevel(logging.INFO)
rag_logger.addHandler(rag_handler)

remediation_logger = logging.getLogger("agents.remediation_agent")
remediation_handler = LogHandler("remediation")
remediation_handler.setLevel(logging.INFO)
remediation_logger.addHandler(remediation_handler)


@app.on_event("startup")
async def startup_event():
    """Initialize orchestrator on startup"""
    global orchestrator
    try:
        logger.info("Initializing Cyber Defense Orchestrator...")
        orchestrator = CyberDefenseOrchestrator(initialize_kb=True)
        logger.info("Orchestrator initialized successfully")
        
        # Log knowledge base status
        doc_count = orchestrator.vector_store.get_document_count()
        log_entry = create_log_entry(
            agent="orchestrator",
            level="INFO",
            message=f"Knowledge base initialized with {doc_count} documents"
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


@app.get("/")
async def root():
    return {"message": "Cyber Defense Simulator API", "status": "running"}


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


@app.post("/api/simulations/start")
async def start_simulation(config: SimulationConfig, background_tasks: BackgroundTasks):
    """Start a new simulation"""
    try:
        if orchestrator is None:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
        
        sim_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Parse attack types
        attack_types = None
        if config.attack_types:
            attack_types = [AttackType(at) for at in config.attack_types]
        
        # Store simulation info
        active_simulations[sim_id] = {
            "id": sim_id,
            "status": "running",
            "progress": 0,
            "current_episode": 0,
            "total_episodes": config.num_episodes,
            "start_time": datetime.now(),
            "attack_type": config.attack_types[0] if config.attack_types else "mixed",
            "success_rate": 0,
        }
        
        # Log simulation start
        log_entry = create_log_entry(
            agent="orchestrator",
            level="INFO",
            message=f"Starting simulation {sim_id} with {config.num_episodes} episodes"
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
    try:
        logger.info(f"Starting background simulation {sim_id}")
        print(f"[API] Starting background simulation {sim_id}")  # Debug output
        
        # Log start
        log_entry = create_log_entry(
            agent="orchestrator",
            level="INFO",
            message=f"Simulation {sim_id} started - {num_episodes} episodes"
        )
        agent_logs["orchestrator"].append(log_entry)
        
        # Update status
        if sim_id in active_simulations:
            active_simulations[sim_id]["status"] = "running"
            active_simulations[sim_id]["current_episode"] = 0
        
        # Track initial episode count
        initial_episode_count = len(orchestrator.episodes)
        
        # Run episodes one by one to track progress
        for episode_num in range(1, num_episodes + 1):
            try:
                # Select attack type for this episode
                attack_type = None
                if attack_types:
                    attack_type = attack_types[(episode_num - 1) % len(attack_types)]
                
                # Log episode start
                log_entry = create_log_entry(
                    agent="orchestrator",
                    level="INFO",
                    message=f"Starting episode {episode_num}/{num_episodes}"
                )
                agent_logs["orchestrator"].append(log_entry)
                
                # Run episode (run in executor to avoid blocking async event loop)
                loop = asyncio.get_event_loop()
                episode = await loop.run_in_executor(
                    None,
                    lambda: orchestrator.run_episode(
                        episode_number=initial_episode_count + episode_num,
                        attack_type=attack_type
                    )
                )
                
                # Log agent activities from episode
                if episode.attack_scenario:
                    log_entry = create_log_entry(
                        agent="red_team",
                        level="INFO",
                        message=f"Red Team generated {episode.attack_scenario.attack_type.value} attack with {len(episode.attack_scenario.steps)} steps"
                    )
                    agent_logs["red_team"].append(log_entry)
                
                if episode.incident_report:
                    log_entry = create_log_entry(
                        agent="detection",
                        level="INFO",
                        message=f"Detection agent identified {episode.incident_report.severity.value} severity incident (confidence: {episode.incident_report.confidence:.2f})"
                    )
                    agent_logs["detection"].append(log_entry)
                
                if episode.rag_context:
                    log_entry = create_log_entry(
                        agent="rag",
                        level="INFO",
                        message=f"RAG agent retrieved {len(episode.rag_context.runbooks)} runbooks and {len(episode.rag_context.threat_intel)} threat intel items"
                    )
                    agent_logs["rag"].append(log_entry)
                
                if episode.remediation_plan:
                    log_entry = create_log_entry(
                        agent="remediation",
                        level="INFO",
                        message=f"Remediation agent generated {len(episode.remediation_plan.options)} action options, recommended: {episode.remediation_plan.recommended_action.value if episode.remediation_plan.recommended_action else 'none'}"
                    )
                    agent_logs["remediation"].append(log_entry)
                
                if episode.rl_decision:
                    log_entry = create_log_entry(
                        agent="rl_agent",
                        level="INFO",
                        message=f"RL agent selected action: {episode.rl_decision.selected_action.value} ({'exploration' if episode.rl_decision.is_exploration else 'exploitation'})"
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
                logger.error(f"Error in episode {episode_num} of simulation {sim_id}: {e}")
                log_entry = create_log_entry(
                    agent="orchestrator",
                    level="ERROR",
                    message=f"Error in episode {episode_num}: {str(e)}"
                )
                agent_logs["orchestrator"].append(log_entry)
                continue
        
        # Calculate final metrics
        final_episodes = [
            ep for ep in orchestrator.episodes 
            if ep.episode_number > initial_episode_count
        ]
        
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
        
        log_entry = create_log_entry(
            agent="orchestrator",
            level="INFO",
            message=f"Simulation {sim_id} completed - {successful}/{len(final_episodes)} successful"
        )
        agent_logs["orchestrator"].append(log_entry)
        
        logger.info(f"Simulation {sim_id} completed")
    except Exception as e:
        logger.error(f"Error in background simulation {sim_id}: {e}")
        if sim_id in active_simulations:
            active_simulations[sim_id]["status"] = "failed"
        log_entry = create_log_entry(
            agent="orchestrator",
            level="ERROR",
            message=f"Simulation {sim_id} failed: {str(e)}"
        )
        agent_logs["orchestrator"].append(log_entry)


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
        },
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
async def get_rl_metrics():
    """Get RL agent metrics and statistics"""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        # Get fresh statistics from RL agent
        rl_stats = orchestrator.rl_agent.get_statistics()
        
        # Get Q-value trends from recent episodes
        q_value_history = []
        epsilon_history = []
        
        if orchestrator.episodes:
            for episode in orchestrator.episodes[-50:]:  # Last 50 episodes
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
        
        # Calculate exploration vs exploitation ratio
        recent_episodes = [ep for ep in orchestrator.episodes[-20:] if ep.rl_decision]
        exploration_count = sum(1 for ep in recent_episodes if ep.rl_decision.is_exploration)
        exploitation_count = len(recent_episodes) - exploration_count
        
        # Use episode_count from RL stats (should match number of episodes that completed)
        # But also ensure it's at least the number of episodes with RL decisions
        episode_count = max(rl_stats["episode_count"], len([ep for ep in orchestrator.episodes if ep.rl_decision]))
        
        return {
            "parameters": {
                "learning_rate": orchestrator.rl_agent.learning_rate,
                "epsilon": orchestrator.rl_agent.epsilon,
                "epsilon_decay": orchestrator.rl_agent.epsilon_decay,
                "min_epsilon": orchestrator.rl_agent.min_epsilon,
                "discount_factor": orchestrator.rl_agent.discount_factor,
                "q_init": orchestrator.rl_agent.q_init,
            },
            "statistics": {
                "episode_count": episode_count,
                "update_count": rl_stats["update_count"],
                "num_states": rl_stats["num_states"],
                "avg_q_value": float(rl_stats["avg_q_value"]),
                "current_epsilon": float(rl_stats["epsilon"]),
            },
            "action_distribution": {
                action.replace("_", " ").title(): count
                for action, count in rl_stats["action_distribution"].items()
            },
            "exploration_ratio": {
                "exploration": exploration_count,
                "exploitation": exploitation_count,
                "ratio": exploration_count / len(recent_episodes) if recent_episodes else 0.0,
            },
            "q_value_history": q_value_history[-30:],  # Last 30 episodes
            "epsilon_history": epsilon_history[-30:],  # Last 30 episodes
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
        }
    
    try:
        # Get REAL episodes from orchestrator
        episodes = orchestrator.episodes[-50:] if orchestrator.episodes else []
        
        if not episodes:
            return {
                "episodes": [],
                "rewards": [],
                "actions": [],
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
        
        return {
            "episodes": reward_data,
            "rewards": reward_data,
            "actions": [{"name": k, "value": v} for k, v in action_counts.items()],
            "attackTypes": attack_type_data,
        }
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return {
            "episodes": [],
            "rewards": [],
            "actions": [],
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
