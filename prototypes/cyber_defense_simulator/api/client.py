"""
API Client for Cyber Defense Simulator
Used by dashboard to communicate with backend API
"""

import httpx
import logging
from typing import Optional, Dict, Any, List
import time

logger = logging.getLogger(__name__)


class SimulatorAPIClient:
    """Client for interacting with the simulator API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize API client
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url.rstrip('/')
        self.client = httpx.Client(timeout=300.0)  # 5 minute timeout for long simulations
    
    def health_check(self) -> bool:
        """Check if API is healthy"""
        try:
            response = self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def run_simulation(
        self,
        num_episodes: int = 20,
        attack_types: Optional[List[str]] = None,
        simulation_mode: str = "Red Team vs Blue Team"
    ) -> Dict[str, Any]:
        """
        Start a new simulation
        
        Args:
            num_episodes: Number of episodes
            attack_types: Optional list of attack types
            simulation_mode: Simulation mode
            
        Returns:
            Simulation response
        """
        try:
            response = self.client.post(
                f"{self.base_url}/api/simulations/run",
                json={
                    "num_episodes": num_episodes,
                    "attack_types": attack_types,
                    "simulation_mode": simulation_mode
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"API error: {e.response.text}")
            raise Exception(f"API error: {e.response.text}")
        except Exception as e:
            logger.error(f"Error running simulation: {e}")
            raise
    
    def get_simulation_status(self, simulation_id: str) -> Dict[str, Any]:
        """
        Get status of a simulation
        
        Args:
            simulation_id: Simulation ID
            
        Returns:
            Status information
        """
        try:
            response = self.client.get(
                f"{self.base_url}/api/simulations/{simulation_id}/status"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            raise
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get status of current simulation"""
        try:
            response = self.client.get(f"{self.base_url}/api/simulations/current/status")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting current status: {e}")
            raise
    
    def get_simulation_results(self, simulation_id: str) -> Dict[str, Any]:
        """
        Get results of a completed simulation
        
        Args:
            simulation_id: Simulation ID
            
        Returns:
            Simulation results with output_dir and episodes
        """
        try:
            response = self.client.get(
                f"{self.base_url}/api/simulations/{simulation_id}/results"
            )
            response.raise_for_status()
            results = response.json()
            
            # Also get full results from current status to get output_dir
            current_status = self.get_current_status()
            if current_status.get("has_results"):
                # Get full results including output_dir
                # We'll need to add an endpoint for this or include it in results
                pass
            
            return results
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                # Simulation still running
                return {"status": "running"}
            raise
        except Exception as e:
            logger.error(f"Error getting results: {e}")
            raise
    
    def wait_for_completion(
        self,
        simulation_id: str,
        poll_interval: float = 2.0,
        max_wait: float = 600.0
    ) -> Dict[str, Any]:
        """
        Wait for simulation to complete
        
        Args:
            simulation_id: Simulation ID
            poll_interval: Seconds between status checks
            max_wait: Maximum seconds to wait
            
        Returns:
            Final results
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status = self.get_simulation_status(simulation_id)
            
            if status["status"] == "completed":
                return self.get_simulation_results(simulation_id)
            elif status["status"] == "failed":
                raise Exception(f"Simulation failed: {status.get('message', 'Unknown error')}")
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Simulation did not complete within {max_wait} seconds")
    
    def load_results(self, results_dir: str) -> Dict[str, Any]:
        """
        Load results from a directory
        
        Args:
            results_dir: Path to results directory
            
        Returns:
            Loaded results
        """
        try:
            response = self.client.post(
                f"{self.base_url}/api/results/load",
                json={"results_dir": results_dir}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error loading results: {e}")
            raise
    
    def close(self):
        """Close the HTTP client"""
        self.client.close()

