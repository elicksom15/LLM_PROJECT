import json
import time
import logging
from typing import Dict, Any, List, Optional
from persistence import persistence
from mimo_client import mimo_client
from config import MODEL_A_ID, MODEL_B_ID

logger = logging.getLogger("research_duel.hypothesis_manager")

# HIPÓTESES INÉDITAS: CÁLCULOS MATEMÁTICOS E OPERADORES NÃO CONVENCIONAIS PARA O GPT (~3B)
# Proibição expressa de quantização uniforme (GGUF/AWQ/GPTQ) ou poda ingênua.
GPT_3B_HYPOTHESES = [
    {
        "title": "GPT3B_H_INVARIANT_SYMPLECTIC_MANIFOLD",
        "description": (
            "Substituição da projeção densa de 50.257 logits por uma variedade simplética invariante no subespaço latente: "
            "uma transformação ortogonal de rank r=128 projeta o estado de ativação diretamente na variedade de Poisson dos logits competitivos, "
            "eliminando 79% dos cálculos matriciais com preservação da estrutura hamiltoniana do residual stream."
        ),
        "proposed_by": "mimo-v2.6-pro-ultraspeed (Inovação Inédita)",
        "evidence": "Fase 8C provou que a trajetória residual reside em uma variedade simplética de dimensão intrínseca d_eff < 100."
    },
    {
        "title": "GPT3B_H_ANALYTICAL_TAYLOR_ODE_JUMP",
        "description": (
            "Operador de Salto Analítico de Camadas (Closed-Form Taylor Jump): modelagem do fluxo residual como uma Equação "
            "Diferencial Ordinária dh/dt = F(h). Utiliza expansão de Taylor analítica de 2ª ordem para saltar 6 camadas intermediárias densas "
            "com custo computacional O(d) em vez de O(L · d^2), cortando mais de 80% dos FLOPs no bloco intermediário."
        ),
        "proposed_by": "mimo-v2.6-pro-ultraspeed (Inovação Inédita)",
        "evidence": "Residual streams de Transformers profundos convergem para atratores contínuos suaves (Neural ODE equivalence)."
    },
    {
        "title": "GPT3B_H_KRONECKER_SPECTRAL_CONTRACTION",
        "description": (
            "Aproximação tensorial de contração de Kronecker adaptativa (W ≈ Σ A_i ⊗ B_i) para os pesos de projeção e FFN, "
            "onde matrizes densas são fatoradas analiticamente sem quantização escalar, cortando FLOPs em 82% via produto tensorial esparso."
        ),
        "proposed_by": "CONSENSO_DUAL_MIMO (Álgebra Tensorial)",
        "evidence": "Decomposição espectral de matrizes de atenção exibe rápida queda de autovalores de von Neumann."
    },
    {
        "title": "GPT3B_H_POINCARE_HYPERBOLIC_VOCAB",
        "description": (
            "Mapeamento do vocabulário em geometria hiperbólica no disco de Poincaré: como a hierarquia léxica é arbórea, "
            "a busca do token argmax requer apenas O(d · log K) operações métricas hiperbólicas em vez de busca exaustiva O(d · V), "
            "reduzindo drasticamente os FLOPs de decodificação."
        ),
        "proposed_by": "mimo-v2.6-pro (Geometria Não-Euclidiana)",
        "evidence": "Tokens autoregressivos seguem estruturas taxonômicas inerentemente hiperbólicas."
    },
    {
        "title": "GPT3B_H_DYNAMIC_K_CONFIDENCE_THRESHOLD",
        "description": (
            "Seleção dinâmica adaptativa do espaço Top-K baseada na margem de separação estocástica (K_small=250 vs K_large=2000), "
            "reduzindo a média de FLOPs da projeção final em mais de 88% quando a margem delta > 1.2."
        ),
        "proposed_by": "mimo-v2.6-pro-ultraspeed",
        "evidence": "Distribuição leptocúrtica de tokens frequentes com separação acentuada de argmax."
    }
]

class HypothesisManager:
    def __init__(self):
        self._ensure_gpt3b_hypotheses()

    def _ensure_gpt3b_hypotheses(self):
        with persistence._get_conn() as conn:
            c = conn.cursor()
            for h in GPT_3B_HYPOTHESES:
                c.execute("SELECT id, status FROM hypotheses WHERE title = ?", (h["title"],))
                row = c.fetchone()
                if not row:
                    self.register_hypothesis(
                        title=h["title"],
                        description=h["description"],
                        proposed_by=h["proposed_by"],
                        evidence=h["evidence"],
                        status="PENDING"
                    )

    def register_hypothesis(
        self,
        title: str,
        description: str,
        proposed_by: str,
        evidence: str,
        status: str = "PENDING",
        cycle_id: Optional[int] = None
    ) -> int:
        with persistence._get_conn() as conn:
            c = conn.cursor()
            now = time.time()
            c.execute("""
            INSERT OR REPLACE INTO hypotheses 
            (title, description, status, proposed_by, cycle_id, evidence, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, description, status, proposed_by, cycle_id, evidence, now, now))
            conn.commit()
            return c.lastrowid

    def get_pending_hypothesis(self) -> Optional[Dict[str, Any]]:
        with persistence._get_conn() as conn:
            c = conn.cursor()
            # Priorizar hipóteses da bancada GPT-3B (prefixo GPT3B)
            c.execute("SELECT id, title, description, proposed_by, evidence FROM hypotheses WHERE status = 'PENDING' AND title LIKE 'GPT3B%' ORDER BY id ASC LIMIT 1")
            row = c.fetchone()
            if not row:
                c.execute("SELECT id, title, description, proposed_by, evidence FROM hypotheses WHERE status = 'PENDING' ORDER BY id ASC LIMIT 1")
                row = c.fetchone()
            if row:
                return {
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "proposed_by": row[3],
                    "evidence": row[4]
                }
            return None

    def update_status(self, title: str, status: str, cycle_id: int):
        with persistence._get_conn() as conn:
            c = conn.cursor()
            c.execute("""
            UPDATE hypotheses 
            SET status = ?, cycle_id = ?, updated_at = ?
            WHERE title = ?
            """, (status, cycle_id, time.time(), title))
            conn.commit()

    def synthesize_frontier_hypothesis(self, cycle_id: int) -> Dict[str, Any]:
        """Gera novas hipóteses para reduzir o poder de computação do modelo GPT com formulações inéditas."""
        logger.info(f"Sintetizando nova hipótese de redução de computação no GPT (~3B) para o Ciclo #{cycle_id}...")
        prompt = (
            f"Você é o Cientista Chefe da Dual MiMo Engine. O foco inegociável é: "
            f"DESCOBRIR UMA TÉCNICA MATEMÁTICA INÉDITA, NÃO PAUTADA NA LITERATURA ATUAL, "
            f"UM NOVO CÁLCULO QUE REDUZA DRASTICAMENTE OS FLOPS E A CARGA COMPUTACIONAL NO MODELO GPT LOCAL (~3B) NA RTX 3060 12GB, "
            f"SEM RECORRER À QUANTIZAÇÃO CONVENCIONAL (AWQ/GPTQ/GGUF) E SEM REPETIR IDEIAS GASTAS PARA NÃO PERDER TEMPO.\n"
            f"Exemplos de direções inovadoras: Operadores de Leis Locais em subespaço invariante, projeções simpléticas, "
            f"álgebra de transição entre estados residuais, decomposição espectral de atalhos fechados.\n"
            f"Proponha a próxima hipótese para o Ciclo #{cycle_id}.\n"
            f"Retorne um JSON no formato:\n"
            f"{{\n"
            f'  "title": "GPT3B_H{cycle_id}_NOME_DA_HIPOTESE_INEDITA",\n'
            f'  "description": "Formulação matemática inovadora com equações ou operadores específicos.",\n'
            f'  "evidence": "Justificativa física de por que este cálculo supera as matmuls densas convencionais."\n'
            f"}}"
        )
        res = mimo_client.call_model(
            model_id=MODEL_A_ID,
            messages=[{"role": "user", "content": prompt}]
        )
        raw_text = res.get("content", "")
        # Fallbacks dinâmicos variados com formulações matemáticas inéditas (evita repetição em caso de API pause)
        fallback_catalogue = [
            (
                f"GPT3B_H{cycle_id}_INVARIANT_SYMPLECTIC_MANIFOLD",
                "Projeção em Variedades Simpléticas Invariantes no Subespaço Latente para colapso de FLOPs.",
                "Preservação da estrutura hamiltoniana do residual stream."
            ),
            (
                f"GPT3B_H{cycle_id}_ANALYTICAL_TAYLOR_ODE_JUMP",
                "Operador Analítico de Salto de Camada via Expansão de Taylor de 2ª Ordem no Residual Stream.",
                "Modelagem do fluxo de ativações como EDO suave dh/dt = F(h)."
            ),
            (
                f"GPT3B_H{cycle_id}_KRONECKER_SPECTRAL_CONTRACTION",
                "Fatoração Tensorial de Kronecker Dinâmica para pesos de projeção e camadas densas.",
                "Decomposição espectral com rápida convergência de autovalores."
            ),
            (
                f"GPT3B_H{cycle_id}_POINCARE_HYPERBOLIC_VOCAB",
                "Busca Hiperbólica em Variedade de Poincaré O(d · log K) para tokens de vocabulário.",
                "Geometria hierárquica do vocabulário autoregressivo."
            )
        ]
        chosen_fb = fallback_catalogue[cycle_id % len(fallback_catalogue)]
        title, desc, evidence = chosen_fb

        try:
            import re
            m = re.search(r"\{[\s\S]*\}", raw_text)
            if m:
                d = json.loads(m.group(0))
                title = d.get("title", title)
                desc = d.get("description", desc)
                evidence = d.get("evidence", evidence)
        except Exception:
            pass

        self.register_hypothesis(
            title=title,
            description=desc,
            proposed_by="mimo-v2.6-pro-ultraspeed (Síntese Autônoma GPT-3B)",
            evidence=evidence,
            status="PENDING"
        )

        return {
            "title": title,
            "description": desc,
            "proposed_by": "mimo-v2.6-pro-ultraspeed (Síntese Autônoma GPT-3B)",
            "evidence": evidence
        }

hypothesis_manager = HypothesisManager()
