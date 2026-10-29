import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from collective.graph_engine import knowledge_graph, KnowledgeNode, KnowledgeEdge
from collective.agent_pool import agent_pool, LogicalAgent
from collective.gds_engine import gds_engine

logger = logging.getLogger("research_duel.collective.orchestrator")

@dataclass
class ExecutionTask:
    id: str
    task_type: str  # INVESTIGATION, ADVERSARIAL_CRITIQUE, VERIFICATION, SYNTHESIS, CONTRADICTION_RESOLUTION
    target_node_id: str
    assigned_agent_id: str
    dependencies: List[str] = field(default_factory=list)
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED
    result: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)

@dataclass
class DynamicExecutionGraph:
    """
    Grafo de Execução Dinâmico (B).
    Mapeia tarefas, agentes ativos e dependências causais para a geração atual.
    """
    generation_id: str
    tasks: Dict[str, ExecutionTask] = field(default_factory=dict)
    routing_audit_log: List[Dict[str, Any]] = field(default_factory=list)

    def add_task(self, task: ExecutionTask):
        self.tasks[task.id] = task

    def get_ready_tasks(self) -> List[ExecutionTask]:
        ready = []
        for t in self.tasks.values():
            if t.status == "PENDING":
                deps_met = all(
                    self.tasks[dep_id].status == "COMPLETED"
                    for dep_id in t.dependencies
                    if dep_id in self.tasks
                )
                if deps_met:
                    ready.append(t)
        return ready


class DynamicGraphOrchestrator:
    """
    Orquestrador Baseado em Grafo Dinâmico.
    Analisa a topologia do Grafo de Conhecimento (A) e constrói o Grafo de Execução (B).
    """
    def build_execution_graph_for_generation(
        self,
        generation_id: str,
        generation_num: int
    ) -> DynamicExecutionGraph:
        exec_graph = DynamicExecutionGraph(generation_id=generation_id)

        # 1. Análise estrutural de lacunas via GDS
        gds_res = gds_engine.run_full_analysis()
        pagerank = gds_engine.cached_pagerank
        betweenness = gds_engine.cached_betweenness

        # 2. Diagnóstico do Grafo de Conhecimento
        open_contradictions = knowledge_graph.find_nodes(label="Contradiction", validation_status="OPEN")
        proposed_hyps = knowledge_graph.find_nodes(label="Hypothesis", validation_status="PROPOSED")
        contradictory_hyps = knowledge_graph.find_nodes(label="Hypothesis", validation_status="CONTRADICTORY")

        logger.info(
            f"[Orchestrator] Geração {generation_num}: {len(proposed_hyps)} propostas abertas, "
            f"{len(open_contradictions)} contradições abertas, {len(contradictory_hyps)} em conflito."
        )

        task_counter = 1

        # CASO 1: Prioridade Máxima para Resolução de Contradições
        if open_contradictions or contradictory_hyps:
            logger.info("[Orchestrator] Conflitos detectados! Priorizando agentes Críticos e Verificadores Independentes.")
            critics = agent_pool.select_active_agents(required_roles=["critic", "independent_verifier"], max_active=3)
            
            for c_node in open_contradictions[:2]:
                t_id = f"task_{generation_id}_{task_counter:03d}"
                assigned_agent = critics[task_counter % len(critics)].id
                exec_graph.add_task(ExecutionTask(
                    id=t_id,
                    task_type="CONTRADICTION_RESOLUTION",
                    target_node_id=c_node.id,
                    assigned_agent_id=assigned_agent
                ))
                exec_graph.routing_audit_log.append({
                    "task_id": t_id,
                    "reason": "OPEN_CONTRADICTION",
                    "target_node": c_node.id,
                    "agent": assigned_agent,
                    "justification": f"Contradição {c_node.id} exige auditoria crítica imediata."
                })
                task_counter += 1

        # CASO 2: Hipóteses Promissoras com Suporte Insuficiente -> Ativar Investigadores & Analistas
        if proposed_hyps:
            # Ordena por relevância estrutural (PageRank + Betweenness)
            ranked_hyps = sorted(
                proposed_hyps,
                key=lambda h: pagerank.get(h.id, 0.0) + betweenness.get(h.id, 0.0),
                reverse=True
            )
            top_hyps = ranked_hyps[:3]
            investigators = agent_pool.select_active_agents(
                required_roles=["investigator", "evidence_analyst", "planner"],
                max_active=4
            )

            for h in top_hyps:
                t1_id = f"task_{generation_id}_{task_counter:03d}"
                inv_agent = investigators[task_counter % len(investigators)].id
                exec_graph.add_task(ExecutionTask(
                    id=t1_id,
                    task_type="INVESTIGATION",
                    target_node_id=h.id,
                    assigned_agent_id=inv_agent
                ))
                task_counter += 1

                # Tarefa dependente: Verificação Independente
                t2_id = f"task_{generation_id}_{task_counter:03d}"
                verif_agents = agent_pool.select_active_agents(required_roles=["independent_verifier"], max_active=1)
                verif_agent = verif_agents[0].id if verif_agents else "agent_verifier_independent"
                exec_graph.add_task(ExecutionTask(
                    id=t2_id,
                    task_type="VERIFICATION",
                    target_node_id=h.id,
                    assigned_agent_id=verif_agent,
                    dependencies=[t1_id]
                ))
                task_counter += 1

                exec_graph.routing_audit_log.append({
                    "investigation_task_id": t1_id,
                    "verification_task_id": t2_id,
                    "target_hypothesis": h.id,
                    "justification": f"Hipótese {h.id} selecionada por centralidade estrutural ({pagerank.get(h.id, 0.0):.3f})"
                })

        # CASO 3: Se não houver hipóteses pendentes, formular nova fronteira via Estratégias Não-Exploradas
        if task_counter == 1:
            logger.info("[Orchestrator] Grafo estável. Disparando geração de nova fronteira de pesquisa.")
            researchers = agent_pool.select_active_agents(
                required_roles=["planner", "investigator", "researcher"],
                max_active=3
            )
            t_front_id = f"task_{generation_id}_001"
            exec_graph.add_task(ExecutionTask(
                id=t_front_id,
                task_type="INVESTIGATION",
                target_node_id="root_frontier",
                assigned_agent_id=researchers[0].id
            ))
            exec_graph.routing_audit_log.append({
                "task_id": t_front_id,
                "reason": "FRONTIER_EXPANSION",
                "justification": "Exploração de novos caminhos operacionais baseados em gaps do GDS."
            })

        logger.info(f"[Orchestrator] Grafo de Execução gerado com {len(exec_graph.tasks)} tarefas planejadas.")
        return exec_graph

graph_orchestrator = DynamicGraphOrchestrator()
