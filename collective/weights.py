import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set

logger = logging.getLogger("research_duel.collective.weights")

@dataclass
class RelationshipWeights:
    """
    Três dimensões de pesos estritamente independentes para cada relação no Grafo de Conhecimento.
    NÃO misture os três pesos em um único atributo permanente.
    """
    weight_semantic: float = 0.50     # [0, 1] Similaridade conceitual / intensidade associativa
    weight_epistemic: float = 0.50    # [0, 1] Força do suporte evidencial, independência e ausência de contradições
    weight_operational: float = 0.50  # [0, 1] Utilidade histórica em gerar resultados verificados
    
    # Histórico de auditoria e incerteza
    uncertainty: float = 0.50
    update_count: int = 0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    update_history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "weight_semantic": round(self.weight_semantic, 4),
            "weight_epistemic": round(self.weight_epistemic, 4),
            "weight_operational": round(self.weight_operational, 4),
            "uncertainty": round(self.uncertainty, 4),
            "update_count": self.update_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "update_history": self.update_history
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RelationshipWeights":
        return cls(
            weight_semantic=float(data.get("weight_semantic", 0.5)),
            weight_epistemic=float(data.get("weight_epistemic", 0.5)),
            weight_operational=float(data.get("weight_operational", 0.5)),
            uncertainty=float(data.get("uncertainty", 0.5)),
            update_count=int(data.get("update_count", 0)),
            created_at=float(data.get("created_at", time.time())),
            updated_at=float(data.get("updated_at", time.time())),
            update_history=list(data.get("update_history", []))
        )

    def calculate_decision_score(
        self,
        alpha_op: float = 0.50,
        beta_ep: float = 0.35,
        gamma_sem: float = 0.15,
        exploration_bonus: float = 0.0
    ) -> float:
        """
        Calcula pontuação composta EFÊMERA para uma decisão específica de roteamento.
        Nunca sobrescreve os atributos permanentes originais.
        """
        score = (
            alpha_op * self.weight_operational +
            beta_ep * self.weight_epistemic +
            gamma_sem * self.weight_semantic +
            exploration_bonus * self.uncertainty
        )
        return max(0.0, min(1.0, score))


class OperationalWeightEngine:
    """
    Motor de Aprendizado e Governança Operacional.
    Garante idempotência, controle de incerteza, penalização de becos sem saída
    e aplicação estrita da fórmula de atualização operacional.
    """
    def __init__(
        self,
        learning_rate: float = 0.15,
        min_weight: float = 0.05,
        max_weight: float = 0.95,
        unproductive_penalty: float = 0.08,
        uncertainty_decay: float = 0.85
    ):
        self.learning_rate = learning_rate
        self.min_weight = min_weight
        self.max_weight = max_weight
        self.unproductive_penalty = unproductive_penalty
        self.uncertainty_decay = uncertainty_decay
        self.processed_feedback_events: Set[str] = set()

    def update_operational_weight(
        self,
        weights: RelationshipWeights,
        event_id: str,
        verified_reward: float,
        generation_id: str,
        method: str = "independent_verification"
    ) -> bool:
        """
        Aplica a fórmula:
        w_next = clip((1 - alpha) * w_current + alpha * verified_reward, min_weight, max_weight)
        com proteção de idempotência por event_id.
        """
        if event_id in self.processed_feedback_events:
            logger.warning(f"[Weights] Feedback duplicado ignorado (idempotência): event_id={event_id}")
            return False

        self.processed_feedback_events.add(event_id)

        w_current = weights.weight_operational
        w_next = (1.0 - self.learning_rate) * w_current + (self.learning_rate * verified_reward)
        w_next = max(self.min_weight, min(self.max_weight, w_next))

        weights.uncertainty = max(0.02, weights.uncertainty * self.uncertainty_decay)
        weights.update_count += 1
        weights.updated_at = time.time()
        weights.weight_operational = round(w_next, 4)

        audit_entry = {
            "event_id": event_id,
            "generation_id": generation_id,
            "timestamp": weights.updated_at,
            "w_prev": round(w_current, 4),
            "reward": round(verified_reward, 4),
            "w_next": weights.weight_operational,
            "method": method
        }
        weights.update_history.append(audit_entry)
        if len(weights.update_history) > 50:
            weights.update_history = weights.update_history[-50:]

        logger.info(
            f"[Weights] Atualização operacional {w_current:.3f} -> {weights.weight_operational:.3f} "
            f"(reward={verified_reward:.2f}, gen={generation_id})"
        )
        return True

    def penalize_unproductive_path(
        self,
        weights: RelationshipWeights,
        event_id: str,
        generation_id: str,
        reason: str = "unproductive_or_falsified"
    ) -> bool:
        """Penaliza caminhos comprovadamente improdutivos ou falsificados."""
        if event_id in self.processed_feedback_events:
            return False

        self.processed_feedback_events.add(event_id)
        w_current = weights.weight_operational
        w_next = max(self.min_weight, w_current - self.unproductive_penalty)

        weights.update_count += 1
        weights.updated_at = time.time()
        weights.weight_operational = round(w_next, 4)
        weights.update_history.append({
            "event_id": event_id,
            "generation_id": generation_id,
            "timestamp": weights.updated_at,
            "w_prev": round(w_current, 4),
            "penalty": self.unproductive_penalty,
            "w_next": weights.weight_operational,
            "reason": reason
        })
        return True

    def update_epistemic_weight(
        self,
        weights: RelationshipWeights,
        source_count_independent: int,
        reproducibility_rate: float,
        contradiction_count: int
    ) -> float:
        """
        Atualiza o peso epistêmico com base no suporte evidencial real.
        Garante que múltiplos agentes repetindo a mesma fonte NÃO contem como fontes independentes.
        """
        # Suporte positivo proporcional a fontes independentes verificadas (saturando em 4 fontes)
        source_factor = min(1.0, source_count_independent / 4.0)
        repro_factor = max(0.0, min(1.0, reproducibility_rate))
        
        # Penalidade severa por contradições abertas
        contradiction_penalty = min(0.60, contradiction_count * 0.20)

        epistemic = (0.5 * source_factor + 0.5 * repro_factor) - contradiction_penalty
        epistemic = max(0.05, min(0.95, epistemic))

        weights.weight_epistemic = round(epistemic, 4)
        weights.updated_at = time.time()
        return weights.weight_epistemic

operational_engine = OperationalWeightEngine()
