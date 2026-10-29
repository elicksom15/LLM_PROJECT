import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from collective.config import collective_config

logger = logging.getLogger("research_duel.collective.agents")

ROLE_PROMPTS = {
    "orchestrator": (
        "Você é o Orquestrador Hierárquico Chefe. Sua missão é coordenar as gerações de pesquisa, "
        "distribuir objetivos, priorizar investigações e assegurar a convergência científica sem redundâncias."
    ),
    "planner": (
        "Você é o Planejador Estratégico. Sua missão é desmembrar problemas abertos em planos experimentais "
        "rigorosos com critérios de validação e falsificação formalmente definidos."
    ),
    "investigator": (
        "Você é o Investigador Teórico. Sua missão é formular soluções matemáticas e algorítmicas inéditas "
        "para colapsar os FLOPs e a complexidade computacional sem utilizar quantização convencional."
    ),
    "researcher": (
        "Você é o Pesquisador de Fronteira. Sua missão é explorar álgebras tensoriais, subespaços invariantes de Krylov, "
        "splitting de Strang e variedades simpléticas para viabilizar inferência rápida em hardware de consumo."
    ),
    "evidence_analyst": (
        "Você é o Analista de Evidências. Sua missão é analisar dados empíricos, separar correlações espúrias "
        "de causas físicas e calcular a solidez epistêmica de cada observação."
    ),
    "relation_builder": (
        "Você é o Construtor de Relações do Grafo. Sua missão é identificar conexões semânticas, dependências "
        "causais e implicações teóricas entre hipóteses isoladas e nós existentes."
    ),
    "critic": (
        "Você é o Crítico Adversarial Sênior. Sua missão é auditar implacavelmente propostas, identificando "
        "gargalos de hardware, sobrecargas de memória, premissas infundadas e ideias recicladas."
    ),
    "contradiction_detector": (
        "Você é o Detector de Contradições. Sua missão é escanear hipóteses e conclusões ativas no grafo, "
        "apontando incompatibilidades lógicas, contradições numéricas e divergências matemáticas."
    ),
    "independent_verifier": (
        "Você é o Verificador Independente. Sua missão é testar objetivamente hipóteses geradas por outros agentes "
        "via execução de código, testes de reprodutibilidade e auditoria matemática sem viés de autoria."
    ),
    "synthesizer": (
        "Você é o Sintetizador Epistêmico. Sua missão é consolidar subgrafos verificados em conclusões formais, "
        "destilando princípios invariantes que servirão de base para as próximas gerações."
    ),
    "memory_retriever": (
        "Você é o Recuperador de Memória Operacional. Sua missão é extrair do grafo apenas os subgrafos "
        "relevantes para cada tarefa, impedindo alucinações e garantindo rastreabilidade de procedência."
    ),
    "strategy_evaluator": (
        "Você é o Avaliador de Estratégias e Utilidade. Sua missão é medir o retorno operacional de cada caminho "
        "investigativo e atribuir recompensas ou penalidades aos pesos das arestas consumidas."
    )
}

@dataclass
class LogicalAgent:
    id: str
    role: str
    specialization: str
    system_prompt: str
    temperature: float = 0.35
    max_tokens: int = 2048
    status: str = "IDLE"  # IDLE, ASSIGNED, EXECUTING, COMPLETED, PAUSED
    total_calls: int = 0
    total_tokens_consumed: int = 0
    tasks_completed: int = 0
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "specialization": self.specialization,
            "status": self.status,
            "total_calls": self.total_calls,
            "total_tokens_consumed": self.total_tokens_consumed,
            "tasks_completed": self.tasks_completed
        }


class LogicalAgentPool:
    """
    Pool Hierárquico Dinâmico de 100 a 500 Agentes Lógicos.
    Desacopla perfis de execução de processos permanentes pesados.
    """
    def __init__(self, target_pool_size: Optional[int] = None, max_pool_size: Optional[int] = None):
        self.target_size = target_pool_size or collective_config.agents.logical_pool
        self.max_size = max_pool_size or collective_config.agents.max_logical_pool
        self.active_limit = collective_config.agents.active_limit
        self.agents: Dict[str, LogicalAgent] = {}
        self._initialize_pool(self.target_size)

    def _initialize_pool(self, count: int):
        roles = list(ROLE_PROMPTS.keys())
        specializations = [
            "Álgebra Espectral & Krylov", "Geometria Não-Euclidiana", "Salto Analítico ODE",
            "Hardware RTX 3060 Profiling", "Fatoração Tensorial Kronecker", "Top-K Adaptativo",
            "Variedades Simpléticas", "Quantização Não-Convencional", "Redução de Bytes de VRAM",
            "Análise de Erro & Confiabilidade", "Consistência de Saída Top-1", "Throughput Autorregressivo"
        ]

        for i in range(1, count + 1):
            role = roles[(i - 1) % len(roles)]
            spec = specializations[(i - 1) % len(specializations)]
            agent_id = f"agent_{i:03d}_{role}"
            
            self.agents[agent_id] = LogicalAgent(
                id=agent_id,
                role=role,
                specialization=f"{spec} (Nível {((i-1)//len(roles))+1})",
                system_prompt=f"{ROLE_PROMPTS[role]}\nEspecialidade Focada: {spec}.",
                temperature=collective_config.agents.default_temperature,
                max_tokens=collective_config.agents.max_tokens_per_call
            )

        logger.info(f"[AgentPool] Pool de agentes inicializado com {len(self.agents)} agentes lógicos (limite máx: {self.max_size}).")

    def expand_pool(self, new_total_size: int) -> int:
        """Expande dinamicamente o pool até o limite máximo configurado (ex: 500)."""
        new_total_size = min(self.max_size, max(len(self.agents), new_total_size))
        current_len = len(self.agents)
        if new_total_size > current_len:
            roles = list(ROLE_PROMPTS.keys())
            for i in range(current_len + 1, new_total_size + 1):
                role = roles[(i - 1) % len(roles)]
                agent_id = f"agent_{i:03d}_{role}"
                self.agents[agent_id] = LogicalAgent(
                    id=agent_id,
                    role=role,
                    specialization=f"Expansão Dinâmica Geração (Nível {((i-1)//len(roles))+1})",
                    system_prompt=ROLE_PROMPTS[role],
                    temperature=collective_config.agents.default_temperature,
                    max_tokens=collective_config.agents.max_tokens_per_call
                )
            logger.info(f"[AgentPool] Pool expandido: {current_len} -> {len(self.agents)} agentes lógicos.")
        return len(self.agents)

    def select_active_agents(
        self,
        required_roles: List[str],
        max_active: Optional[int] = None
    ) -> List[LogicalAgent]:
        """
        Ativa dinamicamente um subconjunto enxuto de agentes necessários para a geração/tarefa,
        respeitando o limite de concorrência ativa.
        """
        limit = max_active or self.active_limit
        selected: List[LogicalAgent] = []
        selected_ids: Set[str] = set()

        # 1. Prioriza agentes com os papéis estritamente solicitados
        for role in required_roles:
            candidates = [a for a in self.agents.values() if a.role == role and a.id not in selected_ids]
            # Seleciona o com menor contagem de tarefas para balanceamento de carga
            if candidates:
                candidates.sort(key=lambda x: x.tasks_completed)
                chosen = candidates[0]
                chosen.status = "ASSIGNED"
                selected.append(chosen)
                selected_ids.add(chosen.id)
                if len(selected) >= limit:
                    break

        # 2. Se houver vagas no orçamento de ativação, preenche com investigadores e analistas
        if len(selected) < limit:
            remaining = [a for a in self.agents.values() if a.id not in selected_ids]
            remaining.sort(key=lambda x: (0 if x.role in ("investigator", "critic", "independent_verifier") else 1, x.tasks_completed))
            for a in remaining:
                a.status = "ASSIGNED"
                selected.append(a)
                selected_ids.add(a.id)
                if len(selected) >= limit:
                    break

        logger.info(f"[AgentPool] Ativados {len(selected)}/{len(self.agents)} agentes lógicos para a tarefa.")
        return selected

    def release_agent(self, agent_id: str, tokens_used: int = 0):
        if agent_id in self.agents:
            ag = self.agents[agent_id]
            ag.status = "IDLE"
            ag.total_calls += 1
            ag.tasks_completed += 1
            ag.total_tokens_consumed += tokens_used

    def get_stats(self) -> Dict[str, Any]:
        by_role: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        for a in self.agents.values():
            by_role[a.role] = by_role.get(a.role, 0) + 1
            by_status[a.status] = by_status.get(a.status, 0) + 1
        return {
            "total_logical_agents": len(self.agents),
            "max_logical_pool": self.max_size,
            "active_limit": self.active_limit,
            "by_role": by_role,
            "by_status": by_status
        }

agent_pool = LogicalAgentPool()
