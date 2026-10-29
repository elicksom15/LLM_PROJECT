import time
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path

from collective.config import collective_config
from collective.graph_engine import knowledge_graph, KnowledgeNode, KnowledgeEdge
from collective.weights import RelationshipWeights, operational_engine
from collective.agent_pool import agent_pool, LogicalAgent
from collective.inference_scheduler import inference_scheduler
from collective.subgraph_extractor import subgraph_extractor
from collective.graph_orchestrator import graph_orchestrator, DynamicExecutionGraph
from collective.verifier import independent_verifier, VerificationOutcome
from collective.gds_engine import gds_engine
from persistence import persistence
from discord_bridge import discord_bridge

logger = logging.getLogger("research_duel.collective.generation")

@dataclass
class GenerationRecord:
    generation_id: str
    generation_num: int
    started_at: float
    ended_at: float = 0.0
    status: str = "IN_PROGRESS"  # IN_PROGRESS, COMPLETED, FAILED, STAGNATED, BUDGET_EXCEEDED
    tasks_executed: int = 0
    tokens_consumed: int = 0
    new_hypotheses_count: int = 0
    verifications_count: int = 0
    verified_success_count: int = 0
    refutations_count: int = 0
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)

class GenerationCycleEngine:
    """
    Motor de Gerações Contínuas de Inteligência (Fase 6).
    Coordena as 13 etapas de cada geração com limites explícitos de recursos,
    preservação acumulada de conhecimento e resiliência a falhas.
    """
    def __init__(self):
        self.config = collective_config.execution
        self.generation_counter = self._get_latest_generation_num()
        self.consecutive_stagnations = 0

    def _get_latest_generation_num(self) -> int:
        gen_nodes = knowledge_graph.find_nodes(label="Generation")
        if not gen_nodes:
            return 0
        nums = []
        for g in gen_nodes:
            try:
                nums.append(int(g.properties.get("generation_num", 0)))
            except Exception:
                pass
        return max(nums) if nums else 0

    def run_generation(self, task_focus: str = "REDUCAO_EXTREMA_FLOPS_GPT3B") -> Dict[str, Any]:
        """
        Executa uma geração completa (13 passos).
        """
        self.generation_counter += 1
        gen_num = self.generation_counter
        gen_id = f"gen_{gen_num:04d}_{int(time.time())}"
        start_time = time.time()

        record = GenerationRecord(
            generation_id=gen_id,
            generation_num=gen_num,
            started_at=start_time
        )

        logger.info(f"\n{'='*70}\n>>> INICIANDO GERAÇÃO #{gen_num} DE INTELIGÊNCIA COLETIVA ({gen_id}) <<<\n{'='*70}")

        # ETAPA 1 & 2: Consultar conhecimento acumulado & Identificar fronteira
        logger.info("[ETAPA 1 & 2] Consultando memória acumulada e identificando fronteira...")
        stats = knowledge_graph.count_stats()
        open_problems = knowledge_graph.find_nodes(label="Problem", validation_status="PROPOSED")
        if not open_problems:
            # Semeia problema raiz se o grafo estiver iniciando
            prob_root = KnowledgeNode(
                id="prob_qwen32b_rtx3060",
                label="Problem",
                title="Execução do Qwen 32B na RTX 3060 12GB sem Quantização Convencional",
                description="Reduzir o poder computacional e tráfego de ativações em >75% via operadores matemáticos exatos.",
                provenance="system",
                validation_status="OPEN",
                epistemic_class="PROBLEM"
            )
            knowledge_graph.add_node(prob_root)

        # ETAPA 3 & 4: Subgrafo relevante & Plano de investigação
        logger.info("[ETAPA 3 & 4] Extraindo subgrafo contextual e construindo Grafo de Execução...")
        subgraph_ctx = subgraph_extractor.extract_context_for_task(task_topic=task_focus, max_nodes=12)
        exec_graph = graph_orchestrator.build_execution_graph_for_generation(gen_id, gen_num)

        # ETAPA 5: Seleção de agentes especializados
        logger.info("[ETAPA 5] Alocando agentes lógicos para tarefas do grafo...")
        tasks = exec_graph.get_ready_tasks()
        tokens_generation = 0

        # ETAPA 6 & 7: Execução paralela/orquestrada de investigações & Síntese
        logger.info(f"[ETAPA 6 & 7] Executando {len(tasks)} investigações via InferenceScheduler...")
        for task in tasks:
            if time.time() - start_time > self.config.max_generation_time_sec:
                logger.warning("[Orçamento] Tempo limite da geração atingido. Interrompendo novas tarefas.")
                record.status = "BUDGET_EXCEEDED"
                break
            if tokens_generation > self.config.max_tokens_per_generation:
                logger.warning("[Orçamento] Limite de tokens da geração atingido.")
                record.status = "BUDGET_EXCEEDED"
                break

            agent = agent_pool.agents.get(task.assigned_agent_id)
            if not agent:
                continue

            prompt_msgs = [
                {"role": "system", "content": agent.system_prompt},
                {"role": "user", "content": (
                    f"{subgraph_ctx['formatted_prompt']}\n\n"
                    f"OBJETIVO DA GERAÇÃO #{gen_num}:\n"
                    f"Tarefa: {task.task_type} sobre o nó `{task.target_node_id}`.\n"
                    f"Apresente formulação inédita (com dedução analítica de FLOPs) para a bancada local."
                )}
            ]

            inf_res = inference_scheduler.dispatch(
                agent_id=agent.id,
                role=agent.role,
                messages=prompt_msgs,
                allow_cache=False
            )
            tokens_used = inf_res.get("tokens_estimated", 0)
            tokens_generation += tokens_used
            agent_pool.release_agent(agent.id, tokens_used)

            task.status = "COMPLETED" if inf_res.get("success") else "FAILED"
            task.result = inf_res
            record.tasks_executed += 1

            # ETAPA 8: Relacionar novos conhecimentos no grafo
            if inf_res.get("success"):
                content = inf_res.get("content", "")
                h_id = f"hyp_gen{gen_num}_{abs(hash(content)) % 100000}"
                title_line = content.split("\n")[0][:80].strip("# ").strip() or f"Hipótese Inédita Geração #{gen_num}"
                
                new_hyp = KnowledgeNode(
                    id=h_id,
                    label="Hypothesis",
                    title=title_line,
                    description=content[:500],
                    provenance=agent.id,
                    validation_status="PROPOSED",
                    epistemic_class="HYPOTHESIS",
                    properties={"gen_id": gen_id, "full_text": content}
                )
                knowledge_graph.add_node(new_hyp)
                record.new_hypotheses_count += 1

                # Conecta ao nó alvo da tarefa
                edge_id = f"e_{h_id}_addresses_{task.target_node_id}"
                e_new = KnowledgeEdge(
                    id=edge_id,
                    source_id=h_id,
                    target_id=task.target_node_id if task.target_node_id in knowledge_graph.embedded.nodes else "prob_qwen32b_rtx3060",
                    relation_type="ADDRESSES",
                    weights=RelationshipWeights(weight_semantic=0.85, weight_epistemic=0.5, weight_operational=0.5),
                    provenance=agent.id
                )
                knowledge_graph.add_edge(e_new)

                # ETAPA 9: Verificação Independente Objetiva
                logger.info(f"[ETAPA 9] Disparando Verificador Independente para {h_id}...")
                v_outcome = independent_verifier.verify_hypothesis(
                    hypothesis_id=h_id,
                    proposer_agent_id=agent.id,
                    generation_id=gen_id,
                    consumed_relation_ids=subgraph_ctx["consumed_relation_ids"] + [edge_id]
                )
                record.verifications_count += 1

                # ETAPA 10 & 11: Revisar conclusões & Atualizar pesos operacionais
                if v_outcome.status == "verified":
                    record.verified_success_count += 1
                    logger.info(f"✅ Hipótese {h_id} confirmada com recompensa {v_outcome.reward:.2f}!")
                else:
                    record.refutations_count += 1
                    logger.info(f"🛑 Hipótese {h_id} refutada objetivamente ({v_outcome.method}).")

        # ETAPA 12: Registrar métricas e Checkpoint da Geração
        logger.info("[ETAPA 12] Gravando nó de geração e checkpoint no grafo...")
        record.ended_at = time.time()
        record.tokens_consumed = tokens_generation
        if record.status == "IN_PROGRESS":
            record.status = "COMPLETED"

        # Salva o nó Generation no Grafo de Conhecimento
        gen_node = KnowledgeNode(
            id=gen_id,
            label="Generation",
            title=f"Geração de Inteligência Coletiva #{gen_num}",
            description=f"Executou {record.tasks_executed} tarefas, {record.verifications_count} verificações.",
            provenance="orchestrator",
            validation_status=record.status,
            epistemic_class="EMPIRICAL_FACT",
            properties={
                "generation_num": gen_num,
                "duration_sec": round(record.ended_at - record.started_at, 2),
                "tokens_consumed": tokens_generation,
                "new_hypotheses": record.new_hypotheses_count,
                "verified": record.verified_success_count,
                "refuted": record.refutations_count
            }
        )
        knowledge_graph.add_node(gen_node)

        # ETAPA 13: Preparação da geração seguinte e telemetria
        logger.info(f"[ETAPA 13] Geração #{gen_num} finalizada em {record.ended_at - record.started_at:.1f}s. Preparando próxima geração.")

        # Notificação ao Discord
        discord_bridge.send_raw_message(
            f"🧠 **[INTELIGÊNCIA COLETIVA — GERAÇÃO #{gen_num}]**\n"
            f"• **Status:** `{record.status}` | **Duração:** `{record.ended_at - record.started_at:.1f}s`\n"
            f"• **Tarefas Executadas:** `{record.tasks_executed}` | **Tokens:** `{tokens_generation}`\n"
            f"• **Novas Hipóteses:** `{record.new_hypotheses_count}` | **Verificadas:** `🏆 {record.verified_success_count}` | **Refutadas:** `❌ {record.refutations_count}`\n"
            f"• **Grafo Total:** `{len(knowledge_graph.embedded.nodes)} nós` e `{len(knowledge_graph.embedded.edges)} arestas ponderadas`."
        )

        return {
            "generation_id": gen_id,
            "generation_num": gen_num,
            "status": record.status,
            "duration_sec": record.ended_at - record.started_at,
            "tasks_executed": record.tasks_executed,
            "tokens_consumed": tokens_generation,
            "new_hypotheses": record.new_hypotheses_count,
            "verified": record.verified_success_count,
            "refuted": record.refutations_count
        }

generation_engine = GenerationCycleEngine()
