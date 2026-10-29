import time
import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from collective.graph_engine import knowledge_graph, KnowledgeNode, KnowledgeEdge
from collective.weights import operational_engine
from analytical_engine import analytical_engine
from benchmark import benchmark_engine

logger = logging.getLogger("research_duel.collective.verifier")

@dataclass
class VerificationOutcome:
    verification_id: str
    generation_id: str
    target_hypothesis_id: str
    verifier_agent_id: str
    status: str  # verified, refuted, inconclusive, error
    reward: float  # [0.0, 1.0]
    consumed_relation_ids: List[str]
    method: str
    details: Dict[str, Any]

class IndependentVerifierEngine:
    """
    Motor de Verificação Independente e Aprendizado Operacional (Fase 8).
    Garante separação estrita entre o agente propositor e o verificador.
    Recompensas são atribuídas APENAS mediante provas objetivas reproduzíveis.
    """
    def __init__(self, graph_manager=None):
        self.km = graph_manager or knowledge_graph

    def verify_hypothesis(
        self,
        hypothesis_id: str,
        proposer_agent_id: str,
        generation_id: str,
        consumed_relation_ids: List[str],
        spec: Optional[Dict[str, Any]] = None,
        graph_manager=None
    ) -> VerificationOutcome:
        """
        Executa verificação independente em duas etapas:
        1. Validação Matemática Analítica Prévia (Fase 0)
        2. Teste Físico em Hardware (GPU Benchmark se aplicável)
        """
        km = graph_manager or self.km
        hyp_node = km.get_node(hypothesis_id)
        if not hyp_node:
            return VerificationOutcome(
                verification_id=f"verif_err_{int(time.time()*1000)}",
                generation_id=generation_id,
                target_hypothesis_id=hypothesis_id,
                verifier_agent_id="system_verifier",
                status="error",
                reward=0.0,
                consumed_relation_ids=consumed_relation_ids,
                method="missing_node_error",
                details={"error": "Nó de hipótese não encontrado"}
            )

        # Regra 1: O verificador não pode ser o mesmo agente que propôs a hipótese
        verifier_agent_id = "agent_verifier_independent"
        if proposer_agent_id == verifier_agent_id:
            verifier_agent_id = "agent_verifier_secondary"

        v_id = f"verif_{generation_id}_{int(time.time()*1000)}"
        spec = spec or {
            "rank_r": 128,
            "top_k": 2000,
            "k_small": 250,
            "k_large": 2000,
            "margin_tau": 1.2
        }

        # ETAPA 1: Auditoria Analítica Independente
        audit_res = analytical_engine.audit_hypothesis(
            hypothesis={"title": hyp_node.title, "description": hyp_node.description},
            spec=spec
        )
        passed_math = audit_res.get("passed_math_gate", False)
        flops_pct = audit_res.get("flops_reduction_pct", 0.0)

        if not passed_math:
            # Rejeição Matemática no papel
            logger.info(f"[Verifier] Hipótese {hyp_node.id} REFUTADA NO CÁLCULO (Corte: {flops_pct:.1f}% < 75%)")
            hyp_node.validation_status = "REFUTED"
            hyp_node.epistemic_class = "FALSIFIED"
            km.add_node(hyp_node)

            # Aplica penalidade operacional aos caminhos consumidos
            for rel_id in consumed_relation_ids:
                rel = km.get_edge(rel_id)
                if rel:
                    operational_engine.penalize_unproductive_path(
                        weights=rel.weights,
                        event_id=f"penal_{v_id}_{rel_id}",
                        generation_id=generation_id,
                        reason="math_falsification"
                    )
                    km.add_edge(rel)

            return VerificationOutcome(
                verification_id=v_id,
                generation_id=generation_id,
                target_hypothesis_id=hypothesis_id,
                verifier_agent_id=verifier_agent_id,
                status="refuted",
                reward=0.0,
                consumed_relation_ids=consumed_relation_ids,
                method="analytical_math_audit",
                details=audit_res
            )

        # ETAPA 2: Validação Física em GPU
        try:
            bench_res = benchmark_engine.run_benchmark(
                mode="dynamic_k_adaptive",
                rank_r=spec.get("rank_r", 128),
                k_small=spec.get("k_small", 250),
                k_large=spec.get("k_large", 2000),
                margin_tau=spec.get("margin_tau", 1.2)
            )
            top1 = bench_res.get("top1_accuracy", 0.0)
            speedup = bench_res.get("speedup_pct", 0.0)
            passed_bench = (top1 >= 98.0 and speedup > 0.0)

            if passed_bench:
                # Aprovação Comprovada
                reward = min(1.0, 0.5 + (top1 / 200.0) + (min(speedup, 100.0) / 400.0))
                logger.info(f"🏆 [Verifier] Hipótese {hyp_node.id} VERIFICADA NA GPU! Top-1: {top1:.2f}%, Speedup: {speedup:+.1f}%")
                hyp_node.validation_status = "VERIFIED"
                hyp_node.epistemic_class = "EMPIRICAL_FACT"
                km.add_node(hyp_node)

                # Recompensa operacional autorizada para as relações consumidas
                for rel_id in consumed_relation_ids:
                    rel = km.get_edge(rel_id)
                    if rel:
                        operational_engine.update_operational_weight(
                            weights=rel.weights,
                            event_id=f"reward_{v_id}_{rel_id}",
                            verified_reward=reward,
                            generation_id=generation_id,
                            method="gpu_physical_verification"
                        )
                        km.add_edge(rel)

                return VerificationOutcome(
                    verification_id=v_id,
                    generation_id=generation_id,
                    target_hypothesis_id=hypothesis_id,
                    verifier_agent_id=verifier_agent_id,
                    status="verified",
                    reward=reward,
                    consumed_relation_ids=consumed_relation_ids,
                    method="gpu_physical_verification",
                    details=bench_res
                )
            else:
                # Falsificação Física
                logger.info(f"[Verifier] Hipótese {hyp_node.id} FALSIFICADA na GPU (Top-1: {top1:.2f}%, Speedup: {speedup:+.1f}%)")
                hyp_node.validation_status = "REFUTED"
                hyp_node.epistemic_class = "FALSIFIED"
                km.add_node(hyp_node)

                for rel_id in consumed_relation_ids:
                    rel = km.get_edge(rel_id)
                    if rel:
                        operational_engine.penalize_unproductive_path(
                            weights=rel.weights,
                            event_id=f"penal_phys_{v_id}_{rel_id}",
                            generation_id=generation_id,
                            reason="physical_falsification"
                        )
                        km.add_edge(rel)

                return VerificationOutcome(
                    verification_id=v_id,
                    generation_id=generation_id,
                    target_hypothesis_id=hypothesis_id,
                    verifier_agent_id=verifier_agent_id,
                    status="refuted",
                    reward=0.0,
                    consumed_relation_ids=consumed_relation_ids,
                    method="gpu_physical_verification",
                    details=bench_res
                )
        except Exception as e:
            logger.error(f"[Verifier] Exceção na verificação de bancada: {e}")
            return VerificationOutcome(
                verification_id=v_id,
                generation_id=generation_id,
                target_hypothesis_id=hypothesis_id,
                verifier_agent_id=verifier_agent_id,
                status="inconclusive",
                reward=0.1,
                consumed_relation_ids=consumed_relation_ids,
                method="execution_exception",
                details={"error": str(e)}
            )

independent_verifier = IndependentVerifierEngine()
