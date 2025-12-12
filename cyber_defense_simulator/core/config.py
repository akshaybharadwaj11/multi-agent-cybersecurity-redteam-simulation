"""
Configuration Management for Cyber Defense Simulator
Centralized configuration using environment variables
"""

import os
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

class Config:
    """Global configuration class"""
    
    # ========================================================================
    # API Configuration
    # ========================================================================
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2000"))
    
    # ========================================================================
    # Vector Store Configuration
    # ========================================================================
    VECTOR_STORE_TYPE: str = os.getenv("VECTOR_STORE_TYPE", "chromadb")
    VECTOR_STORE_PATH: str = os.getenv("VECTOR_STORE_PATH", "./data/vector_store")
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "1536"))
    TOP_K_RETRIEVAL: int = int(os.getenv("TOP_K_RETRIEVAL", "5"))
    
    # ========================================================================
    # RL Configuration
    # ========================================================================
    RL_LEARNING_RATE: float = float(os.getenv("RL_LEARNING_RATE", "0.1"))
    RL_EPSILON: float = float(os.getenv("RL_EPSILON", "0.1"))
    RL_EPSILON_DECAY: float = float(os.getenv("RL_EPSILON_DECAY", "0.995"))
    RL_MIN_EPSILON: float = float(os.getenv("RL_MIN_EPSILON", "0.01"))
    RL_DISCOUNT_FACTOR: float = float(os.getenv("RL_DISCOUNT_FACTOR", "0.95"))
    RL_Q_INIT: float = float(os.getenv("RL_Q_INIT", "0.0"))
    
    # ========================================================================
    # Simulation Configuration
    # ========================================================================
    NUM_EPISODES: int = int(os.getenv("NUM_EPISODES", "100"))
    MAX_STEPS_PER_EPISODE: int = int(os.getenv("MAX_STEPS_PER_EPISODE", "20"))
    ATTACK_SUCCESS_THRESHOLD: float = float(os.getenv("ATTACK_SUCCESS_THRESHOLD", "0.7"))
    
    # ========================================================================
    # Reward Function Configuration
    # ========================================================================
    REWARD_SUCCESS: float = float(os.getenv("REWARD_SUCCESS", "1.0"))
    REWARD_FAILURE: float = float(os.getenv("REWARD_FAILURE", "-1.0"))
    REWARD_FALSE_POSITIVE: float = float(os.getenv("REWARD_FALSE_POSITIVE", "-0.5"))
    REWARD_COLLATERAL_DAMAGE: float = float(os.getenv("REWARD_COLLATERAL_DAMAGE", "-0.3"))
    REWARD_UNCERTAINTY: float = float(os.getenv("REWARD_UNCERTAINTY", "0.0"))
    
    # ========================================================================
    # Paths
    # ========================================================================
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    RUNBOOKS_DIR: Path = DATA_DIR / "runbooks"
    MITRE_DIR: Path = DATA_DIR / "mitre_attack"
    CVE_DIR: Path = DATA_DIR / "cve_data"
    LOGS_DIR: Path = DATA_DIR / "logs"
    
    # ========================================================================
    # CrewAI Configuration
    # ========================================================================
    CREW_VERBOSE: bool = os.getenv("CREW_VERBOSE", "true").lower() == "true"
    CREW_MAX_ITER: int = int(os.getenv("CREW_MAX_ITER", "3"))
    CREW_MEMORY: bool = os.getenv("CREW_MEMORY", "true").lower() == "true"
    
    # ========================================================================
    # Logging Configuration
    # ========================================================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "simulation.log")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required. Set it in .env file.")
        
        # Create necessary directories
        for directory in [cls.DATA_DIR, cls.RUNBOOKS_DIR, cls.MITRE_DIR, 
                         cls.CVE_DIR, cls.LOGS_DIR, Path(cls.VECTOR_STORE_PATH)]:
            directory.mkdir(parents=True, exist_ok=True)
        
        return True
    
    @classmethod
    def get_llm_config(cls) -> dict:
        """Get LLM configuration for CrewAI"""
        return {
            "model": cls.LLM_MODEL,
            "temperature": cls.LLM_TEMPERATURE,
            "max_tokens": cls.LLM_MAX_TOKENS,
            "api_key": cls.OPENAI_API_KEY
        }
    
    @classmethod
    def get_rl_config(cls) -> dict:
        """Get RL configuration"""
        return {
            "learning_rate": cls.RL_LEARNING_RATE,
            "epsilon": cls.RL_EPSILON,
            "epsilon_decay": cls.RL_EPSILON_DECAY,
            "min_epsilon": cls.RL_MIN_EPSILON,
            "discount_factor": cls.RL_DISCOUNT_FACTOR,
            "q_init": cls.RL_Q_INIT
        }
    
    @classmethod
    def get_reward_config(cls) -> dict:
        """Get reward function configuration"""
        return {
            "success": cls.REWARD_SUCCESS,
            "failure": cls.REWARD_FAILURE,
            "false_positive": cls.REWARD_FALSE_POSITIVE,
            "collateral_damage": cls.REWARD_COLLATERAL_DAMAGE,
            "uncertainty": cls.REWARD_UNCERTAINTY
        }


# Validate configuration on import
Config.validate()
