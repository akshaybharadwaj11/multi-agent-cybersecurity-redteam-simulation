"""
FastAPI Server for Cyber Defense Simulator
Provides REST API endpoints for the dashboard
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import logging
from pathlib import Path
import sys
import json
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Setup logging for API server
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('simulation.log', mode='a')  # Append mode
    ],
    force=True  # Override any existing configuration
)

from cyber_defense_simulator.core.orchestrator import CyberDefenseOrchestrator
from cyber_defense_simulator.core.data_models import AttackType, SimulationMetrics

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Cyber Defense Simulator API",
    description="REST API for multi-agent cybersecurity simulation",
    version="1.0.0"
)

# CORS middleware for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for running simulations
simulation_state: Dict[str, Any] = {
    "running": False,
    "current_simulation": None,
    "results": None,
    "status": "idle"
}


# Request/Response Models
class SimulationRequest(BaseModel):
    num_episodes: int = 20
    attack_types: Optional[List[str]] = None
    simulation_mode: str = "Red Team vs Blue Team"


class SimulationResponse(BaseModel):
    simulation_id: str
    status: str
    message: str


class SimulationStatus(BaseModel):
    simulation_id: str
    status: str
    progress: Optional[float] = None
    current_episode: Optional[int] = None
    total_episodes: Optional[int] = None
    message: Optional[str] = None


class MetricsResponse(BaseModel):
    total_episodes: int
    successful_defenses: int
    failed_defenses: int
    false_positives: int
    average_reward: float
    average_time_to_remediate: float
    detection_rate: float
    reward_history: List[float]
    action_distribution: Dict[str, int]
    attack_distribution: Optional[Dict[str, int]] = None
    defense_strategies: Optional[List[Dict[str, Any]]] = None
    episode_details: Optional[List[Dict[str, Any]]] = None
    output_dir: Optional[str] = None
    simulation_mode: Optional[str] = None


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Cyber Defense Simulator API",
        "timestamp": datetime.now().isoformat()
    }


# Run simulation
@app.post("/api/simulations/run", response_model=SimulationResponse)
async def run_simulation(
    request: SimulationRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a new simulation
    
    Args:
        request: Simulation configuration
        background_tasks: FastAPI background tasks
        
    Returns:
        Simulation response with ID and status
    """
    if simulation_state["running"]:
        raise HTTPException(
            status_code=409,
            detail="Simulation already running. Please wait for it to complete."
        )
    
    # Generate simulation ID
    simulation_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Update state
    simulation_state["running"] = True
    simulation_state["status"] = "starting"
    simulation_state["current_simulation"] = simulation_id
    
    # Start simulation in background
    background_tasks.add_task(
        execute_simulation,
        simulation_id,
        request.num_episodes,
        request.attack_types,
        request.simulation_mode
    )
    
    return SimulationResponse(
        simulation_id=simulation_id,
        status="started",
        message=f"Simulation {simulation_id} started with {request.num_episodes} episodes"
    )


def execute_simulation(
    simulation_id: str,
    num_episodes: int,
    attack_types: Optional[List[str]],
    simulation_mode: str
):
    """
    Execute simulation in background
    
    Args:
        simulation_id: Unique simulation ID
        num_episodes: Number of episodes
        attack_types: Optional list of attack types
        simulation_mode: Simulation mode
    """
    try:
        logger.info(f"Starting simulation {simulation_id}")
        simulation_state["status"] = "running"
        
        # Initialize orchestrator
        orchestrator = CyberDefenseOrchestrator()
        
        # Convert attack types
        attack_type_list = None
        if attack_types:
            attack_type_list = [AttackType(at) for at in attack_types]
        
        # Run simulation
        metrics = orchestrator.run_simulation(
            num_episodes=num_episodes,
            attack_types=attack_type_list
        )
        
        # Save results
        output_dir = Path("./results") / simulation_id
        output_dir.mkdir(parents=True, exist_ok=True)
        orchestrator.save_results(output_dir)
        
        # Prepare response data
        reward_history = []
        action_distribution = {}
        attack_distribution = {}
        defense_strategies = []
        episode_details = []
        
        if orchestrator.episodes:
            for episode in orchestrator.episodes:
                # Reward history
                if episode.reward:
                    reward_history.append(episode.reward.reward)
                
                # Action distribution
                if episode.rl_decision:
                    action = episode.rl_decision.selected_action.value
                    action_distribution[action] = action_distribution.get(action, 0) + 1
                
                # Attack distribution
                if episode.attack_scenario:
                    attack_type = episode.attack_scenario.attack_type.value
                    attack_distribution[attack_type] = attack_distribution.get(attack_type, 0) + 1
                
                # Defense strategies (successful ones)
                if episode.outcome and episode.outcome.success and episode.rl_decision:
                    defense_strategies.append({
                        "episode": episode.episode_number,
                        "attack_type": episode.attack_scenario.attack_type.value if episode.attack_scenario else "unknown",
                        "action": episode.rl_decision.selected_action.value,
                        "severity": episode.incident_report.severity.value if episode.incident_report else "unknown",
                        "reward": episode.reward.reward if episode.reward else 0.0,
                        "time_to_remediate": episode.outcome.time_to_remediate if episode.outcome else 0.0
                    })
                
                # Episode details
                episode_details.append({
                    "episode_number": episode.episode_number,
                    "attack_type": episode.attack_scenario.attack_type.value if episode.attack_scenario else "unknown",
                    "severity": episode.incident_report.severity.value if episode.incident_report else "unknown",
                    "action_taken": episode.rl_decision.selected_action.value if episode.rl_decision else "unknown",
                    "success": episode.outcome.success if episode.outcome else False,
                    "reward": episode.reward.reward if episode.reward else 0.0
                })
        
        # Store results with full metrics
        simulation_state["results"] = {
            "simulation_id": simulation_id,
            "metrics": {
                "total_episodes": metrics.total_episodes,
                "successful_defenses": metrics.successful_defenses,
                "failed_defenses": metrics.failed_defenses,
                "false_positives": metrics.false_positives,
                "average_reward": metrics.average_reward,
                "average_time_to_remediate": metrics.average_time_to_remediate,
                "detection_rate": metrics.detection_rate,
                "reward_history": reward_history,
                "action_distribution": action_distribution,
                "attack_distribution": attack_distribution,
                "defense_strategies": defense_strategies,
                "episode_details": episode_details
            },
            "output_dir": str(output_dir),
            "simulation_mode": simulation_mode,
            "episodes": [
                {
                    "episode_id": ep.episode_id,
                    "episode_number": ep.episode_number,
                    "attack_type": ep.attack_scenario.attack_type.value if ep.attack_scenario else "unknown",
                    "reward": ep.reward.reward if ep.reward else 0.0,
                    "outcome": {
                        "success": ep.outcome.success if ep.outcome else False,
                        "severity": ep.incident_report.severity.value if ep.incident_report else "unknown",
                        "action_taken": ep.rl_decision.selected_action.value if ep.rl_decision else "unknown"
                    } if ep.outcome else None
                }
                for ep in orchestrator.episodes
            ]
        }
        
        simulation_state["status"] = "completed"
        logger.info(f"Simulation {simulation_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Simulation {simulation_id} failed: {e}", exc_info=True)
        simulation_state["status"] = "failed"
        simulation_state["results"] = {
            "simulation_id": simulation_id,
            "error": str(e)
        }
    finally:
        simulation_state["running"] = False


# Get simulation status
@app.get("/api/simulations/{simulation_id}/status", response_model=SimulationStatus)
async def get_simulation_status(simulation_id: str):
    """
    Get status of a running simulation
    
    Args:
        simulation_id: Simulation ID
        
    Returns:
        Simulation status
    """
    if not simulation_state["running"]:
        if simulation_state["results"]:
            return SimulationStatus(
                simulation_id=simulation_id,
                status="completed",
                progress=100.0,
                message="Simulation completed"
            )
        else:
            return SimulationStatus(
                simulation_id=simulation_id,
                status="not_found",
                message="Simulation not found"
            )
    
    if simulation_state["current_simulation"] != simulation_id:
        raise HTTPException(
            status_code=404,
            detail=f"Simulation {simulation_id} not found"
        )
    
    return SimulationStatus(
        simulation_id=simulation_id,
        status=simulation_state["status"],
        progress=50.0 if simulation_state["status"] == "running" else None,
        message=f"Simulation is {simulation_state['status']}"
    )


# Get simulation results
@app.get("/api/simulations/{simulation_id}/results", response_model=MetricsResponse)
async def get_simulation_results(simulation_id: str):
    """
    Get results of a completed simulation
    
    Args:
        simulation_id: Simulation ID
        
    Returns:
        Simulation metrics and results
    """
    if simulation_state["running"]:
        raise HTTPException(
            status_code=409,
            detail="Simulation is still running. Please wait for completion."
        )
    
    if not simulation_state["results"]:
        raise HTTPException(
            status_code=404,
            detail=f"Results for simulation {simulation_id} not found"
        )
    
    results = simulation_state["results"]
    if results["simulation_id"] != simulation_id:
        raise HTTPException(
            status_code=404,
            detail=f"Results for simulation {simulation_id} not found"
        )
    
    metrics = results["metrics"]
    
    return MetricsResponse(
        total_episodes=metrics["total_episodes"],
        successful_defenses=metrics["successful_defenses"],
        failed_defenses=metrics["failed_defenses"],
        false_positives=metrics["false_positives"],
        average_reward=metrics["average_reward"],
        average_time_to_remediate=metrics["average_time_to_remediate"],
        detection_rate=metrics["detection_rate"],
        reward_history=metrics["reward_history"],
        action_distribution=metrics["action_distribution"],
        attack_distribution=metrics.get("attack_distribution", {}),
        defense_strategies=metrics.get("defense_strategies", []),
        episode_details=metrics.get("episode_details", []),
        output_dir=results.get("output_dir"),
        simulation_mode=results.get("simulation_mode")
    )


# Get current simulation status
@app.get("/api/simulations/current/status")
async def get_current_simulation_status():
    """Get status of current simulation"""
    return {
        "running": simulation_state["running"],
        "status": simulation_state["status"],
        "simulation_id": simulation_state["current_simulation"],
        "has_results": simulation_state["results"] is not None
    }


# Load results from directory
@app.post("/api/results/load")
async def load_results(results_dir: str):
    """
    Load results from a directory
    
    Args:
        results_dir: Path to results directory
        
    Returns:
        Loaded metrics and episodes
    """
    try:
        results_path = Path(results_dir)
        
        if not results_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Results directory not found: {results_dir}"
            )
        
        # Load metrics
        metrics_file = results_path / "metrics.json"
        episodes_file = results_path / "episodes.json"
        
        if not metrics_file.exists() or not episodes_file.exists():
            raise HTTPException(
                status_code=404,
                detail="Results files not found in directory"
            )
        
        with open(metrics_file) as f:
            metrics = json.load(f)
        
        with open(episodes_file) as f:
            episodes = json.load(f)
        
        return {
            "status": "success",
            "metrics": metrics,
            "episodes": episodes,
            "results_dir": str(results_path)
        }
        
    except Exception as e:
        logger.error(f"Error loading results: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error loading results: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "cyber_defense_simulator.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

