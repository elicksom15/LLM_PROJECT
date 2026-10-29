import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = BASE_DIR / "config_collective.yaml"

@dataclass
class AgentPoolConfig:
    logical_pool: int = 100
    max_logical_pool: int = 500
    active_limit: int = 12
    inference_concurrency: int = 4
    dynamic_activation: bool = True
    specialized_roles: bool = True
    default_temperature: float = 0.35
    max_tokens_per_call: int = 2048

@dataclass
class KnowledgeGraphConfig:
    provider: str = "neo4j"
    uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user: str = os.getenv("NEO4J_USER", "neo4j")
    password: str = os.getenv("NEO4J_PASSWORD", "password123")
    database: str = os.getenv("NEO4J_DATABASE", "neo4j")
    persistence: bool = True
    adaptive_weights: bool = True
    provenance_required: bool = True
    fallback_to_embedded: bool = True
    state_file: str = str(BASE_DIR / "collective_graph_state.json")

@dataclass
class WeightsConfig:
    learning_rate: float = 0.15
    min_weight: float = 0.05
    max_weight: float = 0.95
    unproductive_penalty: float = 0.08
    exploration_rate: float = 0.10
    uncertainty_discount: float = 0.90

@dataclass
class ExecutionConfig:
    continuous: bool = True
    generation_budget_enabled: bool = True
    max_generation_time_sec: int = 180
    max_tokens_per_generation: int = 64000
    max_tasks_per_generation: int = 24
    checkpoint_enabled: bool = True
    graceful_shutdown: bool = True
    circuit_breaker_error_limit: int = 5
    stagnation_generation_limit: int = 4

@dataclass
class VerificationConfig:
    require_independent_verifier: bool = True
    min_math_reduction_threshold: float = 0.75
    reproducibility_runs: int = 2
    reward_scale: float = 1.0

@dataclass
class CollectiveConfig:
    agents: AgentPoolConfig = field(default_factory=AgentPoolConfig)
    knowledge_graph: KnowledgeGraphConfig = field(default_factory=KnowledgeGraphConfig)
    weights: WeightsConfig = field(default_factory=WeightsConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    verification: VerificationConfig = field(default_factory=VerificationConfig)

    @classmethod
    def load(cls, config_path: Path = DEFAULT_CONFIG_PATH) -> "CollectiveConfig":
        if not config_path.exists():
            return cls()
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            
            c = cls()
            if "agents" in data:
                c.agents = AgentPoolConfig(**data["agents"])
            if "knowledge_graph" in data:
                c.knowledge_graph = KnowledgeGraphConfig(**data["knowledge_graph"])
            if "weights" in data:
                c.weights = WeightsConfig(**data["weights"])
            if "execution" in data:
                c.execution = ExecutionConfig(**data["execution"])
            if "verification" in data:
                c.verification = VerificationConfig(**data["verification"])
            return c
        except Exception as e:
            print(f"[CollectiveConfig] Aviso ao carregar {config_path}: {e}. Usando defaults.")
            return cls()

collective_config = CollectiveConfig.load()
