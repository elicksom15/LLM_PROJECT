import time
import json
import logging
from typing import Dict, Any, Tuple
from mimo_client import mimo_client
from config import MODEL_A_ID, MODEL_B_ID
from persistence import persistence
from discord_bridge import discord_bridge

logger = logging.getLogger("research_duel.debate_engine")

SYSTEM_PROMPT_ULTRASPEED = """Você é o Pesquisador A (MiMo-V2.6-Pro-UltraSpeed) — Cientista Chefe de Inovação Algorítmica e Descoberta Matemática.
SUA MISSÃO CENTRAL:
DESCOBRIR UMA TÉCNICA MATEMÁTICA INÉDITA, NÃO PAUTADA HOJE NA LITERATURA CONVENCIONAL, CAPAZ DE COLAPSAR O PODER DE COMPUTAÇÃO E OS FLOPS DO MODELO GPT LOCAL (~3B) NA RTX 3060 12GB,
MAXIMIZANDO A TAXA REAL DE TOKENS POR SEGUNDO (TKS/S) SEM PERDER A FIDELIDADE DA SAÍDA.

REGRA DE OURO: CÁLCULO PRIMEIRO, GPU DEPOIS!
- Toda hipótese deve conter DEDUÇÃO MATEMÁTICA E CÁLCULO ANALÍTICO EXPLÍCITO de FLOPs e complexidade assintótica.
- A formulação matemática precisa provar NO PAPEL uma redução teórica mínima de 75% a 85% de FLOPs antes de ir para a GPU.
- Se o cálculo analítico for fraco ou falhar, a hipótese é descartada na Fase 0 para NUNCA perder tempo de GPU à toa!

DIRETRIZ DE INOVAÇÃO PURA (PROIBIDO REPETIR O QUE JÁ EXISTE):
- É EXPRESSAMENTE PROIBIDO propor soluções gastas: NÃO proponha quantização 4-bit uniforme (GGUF, AWQ, GPTQ), nem poda ingênua que degrada a inteligência.
- Busque cálculos genuinamente inéditos:
  1. Variedades Simpléticas Invariantes: Redução hamiltoniana de dimensionalidade no espaço latente.
  2. Operadores Analíticos de Salto (Neural ODE / Expansão de Taylor): Substituição de blocos de camadas por salto analítico fechado O(d).
  3. Contração Espectral Tensorial de Kronecker: Fatoração adaptativa sem quantização escalar.
  4. Geometria Hiperbólica Poincaré: Busca de tokens argmax com complexidade O(d log K)."""

SYSTEM_PROMPT_PRO = """Você é o Pesquisador B (MiMo-V2.6-Pro) — Revisor Adversarial Sênior e Auditor de Validade Física e Matemática.
SUA MISSÃO:
AUDITAR COM MÁXIMO RIGOR AS PROPOSTAS INÉDITAS DO PESQUISADOR A PARA GARANTIR QUE NÃO SEJAM TEORIAS VAZIAS OU RECICLAGEM DISFARÇADA DE IDEIAS ANTIGAS.

Critérios Adversariais Inegociáveis (CÁLCULO PRIMEIRO, GPU DEPOIS):
1. Auditoria Matemática Rigorosa: Deduza os FLOPs teóricos da proposta. Se o corte de FLOPs for inferior a 75.0%, rejeite sumariamente no papel.
2. Originalidade vs Reciclagem: Se for apenas uma variação cosmética de técnicas convencionais conhecidas, rejeite e exija formulação matemática genuinamente nova.
3. Viabilidade Física Real: O cálculo proposto é computacionalmente mais leve em hardware real (GPU/CUDA) ou o overhead analítico consome mais tempo do que a matmul BLAS?
4. Fixe critérios estritos de falsificação matemática e física."""

def build_gpt3b_ledger_context() -> str:
    summary_data = persistence.get_summary_stats()
    latest_cycle = persistence.get_latest_cycle_id()
    
    ledger = (
        "=== BANCADA CIENTÍFICA: MODELO GPT LOCAL (~3B) NA RTX 3060 12GB ===\n"
        "1. AMBIENTE EXPERIMENTAL:\n"
        "   - GPU: NVIDIA GeForce RTX 3060 12GB GDDR6 (360 GB/s, 13.2 TFLOPs FP32)\n"
        "   - Modelo Testado: GPT Local (~3B architecture / GPT-2 testbed em branchman/models/gpt2)\n"
        "   - Diretriz Central: Reduzir poder de computação e FLOPs, elevar tokens/s SEM QUANTIZAÇÃO CONVENCIONAL.\n\n"
        "2. DESCOBERTAS EMPÍRICAS COMPROVADAS NO WORKSPACE:\n"
        "   - Projeção de Vocabulário PCA: Rank r=128 com Top-K=2000 alcançou 99.01% Top-1 com 79.1% de corte de FLOPs.\n"
        "   - Throughput Real: Subiu de 303.1 tok/s para 445.9 tok/s na RTX 3060 (+47.1% de ganho).\n"
        "   - Inércia Residual: Fase 8C provou forte persistência direcional (r=-0.914) entre tokens vizinhos.\n\n"
        f"3. HISTÓRICO DE CICLOS CONCLUÍDOS: {summary_data.get('total_cycles', 0)} ciclos no banco SQLite.\n"
        "===================================================================\n"
    )
    return ledger

class DebateEngine:
    def execute_round1_investigation(self, cycle_id: int, hypothesis: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        ledger = build_gpt3b_ledger_context()
        prompt = (
            f"{ledger}\n"
            f"PROBLEMA EM INVESTIGAÇÃO — CICLO #{cycle_id}:\n"
            f"Hipótese: {hypothesis['title']}\n"
            f"Descrição: {hypothesis['description']}\n"
            f"Evidência Prévia: {hypothesis.get('evidence', 'Fundamentação prévia')}\n\n"
            f"Apresente sua formulação independente para reduzir a computação e elevar os tokens/s na bancada GPT (~3B) sem quantizar."
        )

        res_a = mimo_client.call_model(
            model_id=MODEL_A_ID,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_ULTRASPEED},
                {"role": "user", "content": prompt}
            ]
        )
        content_a = res_a.get("content", "")
        persistence.record_debate_message(
            cycle_id=cycle_id,
            round_num=1,
            agent_id="Pesquisador A",
            model_name=MODEL_A_ID,
            message_type="HIPOTESE_GPT3B",
            content=content_a,
            latency_sec=res_a.get("latency_sec", 0.0)
        )

        time.sleep(2.0)

        res_b = mimo_client.call_model(
            model_id=MODEL_B_ID,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_PRO},
                {"role": "user", "content": prompt}
            ]
        )
        content_b = res_b.get("content", "")
        persistence.record_debate_message(
            cycle_id=cycle_id,
            round_num=1,
            agent_id="Pesquisador B",
            model_name=MODEL_B_ID,
            message_type="AUDITORIA_CRITICA_GPT3B",
            content=content_b,
            latency_sec=res_b.get("latency_sec", 0.0)
        )

        discord_bridge.publish_investigation_card(
            cycle_id=cycle_id,
            hypothesis=hypothesis,
            arg_a=content_a,
            arg_b=content_b
        )

        return res_a, res_b

    def execute_round2_confrontation(
        self,
        cycle_id: int,
        hypothesis: Dict[str, Any],
        res_a: Dict[str, Any],
        res_b: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        prompt_a = (
            f"O Pesquisador B (MiMo Pro) fez a seguinte crítica à sua proposta:\n\n"
            f"{res_b.get('content', '')}\n\n"
            f"Refute ou incorpore as restrições, aprimorando o algoritmo para garantir que o corte de FLOPs "
            f"realmente acelere a taxa de tokens/s na RTX 3060 sem perda de fidelidade."
        )
        crit_a = mimo_client.call_model(
            model_id=MODEL_A_ID,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_ULTRASPEED},
                {"role": "user", "content": prompt_a}
            ]
        )
        content_crit_a = crit_a.get("content", "")
        persistence.record_debate_message(
            cycle_id=cycle_id,
            round_num=2,
            agent_id="Pesquisador A",
            model_name=MODEL_A_ID,
            message_type="REPLICA_GPT3B",
            content=content_crit_a,
            latency_sec=crit_a.get("latency_sec", 0.0)
        )

        time.sleep(2.0)

        prompt_b = (
            f"O Pesquisador A (MiMo UltraSpeed) defendeu a seguinte formulação:\n\n"
            f"{res_a.get('content', '')}\n\n"
            f"Audite detalhadamente os cálculos de FLOPs e latência real em hardware. "
            f"Fixe os critérios irrefutáveis de falsificação experimental."
        )
        crit_b = mimo_client.call_model(
            model_id=MODEL_B_ID,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_PRO},
                {"role": "user", "content": prompt_b}
            ]
        )
        content_crit_b = crit_b.get("content", "")
        persistence.record_debate_message(
            cycle_id=cycle_id,
            round_num=2,
            agent_id="Pesquisador B",
            model_name=MODEL_B_ID,
            message_type="CRITICA_ADVERSARIAL_GPT3B",
            content=content_crit_b,
            latency_sec=crit_b.get("latency_sec", 0.0)
        )

        discord_bridge.publish_confrontation_card(
            cycle_id=cycle_id,
            hypothesis=hypothesis,
            crit_a=content_crit_a,
            crit_b=content_crit_b
        )

        return crit_a, crit_b

    def execute_round3_specification(
        self,
        cycle_id: int,
        hypothesis: Dict[str, Any],
        crit_a: Dict[str, Any],
        crit_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Define os parâmetros numéricos para o teste na bancada GPT."""
        prompt_spec = (
            f"Com base no debate entre MiMo UltraSpeed e MiMo Pro sobre '{hypothesis['title']}':\n"
            f"Defina os parâmetros do ensaio na bancada GPT (~3B) para reduzir FLOPs e maximizar tokens/s.\n"
            f"Retorne um JSON estrito no formato:\n"
            f"{{\n"
            f'  "rank_r": 128,\n'
            f'  "top_k": 2000,\n'
            f'  "margin_tau": 1.2,\n'
            f'  "k_small": 250,\n'
            f'  "k_large": 2000,\n'
            f'  "pass_criteria": "top1 >= 98.5% e flops_reduction >= 50.0%",\n'
            f'  "falsification_criteria": "top1 < 98.0% ou speedup <= 1.0x"\n'
            f"}}"
        )

        spec_res = mimo_client.call_model(
            model_id=MODEL_B_ID,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_PRO},
                {"role": "user", "content": prompt_spec}
            ]
        )

        raw_text = spec_res.get("content", "")
        rank_r = 128
        top_k = 2000
        margin_tau = 1.2
        k_small = 250
        k_large = 2000
        pass_crit = "top1 >= 98.0% e flops_reduction >= 50.0%"
        fals_crit = "top1 < 98.0% ou speedup <= 1.0x"

        try:
            import re
            m = re.search(r"\{[\s\S]*\}", raw_text)
            if m:
                data = json.loads(m.group(0))
                rank_r = int(data.get("rank_r", 128))
                top_k = int(data.get("top_k", 2000))
                margin_tau = float(data.get("margin_tau", 1.2))
                k_small = int(data.get("k_small", 250))
                k_large = int(data.get("k_large", 2000))
                pass_crit = data.get("pass_criteria", pass_crit)
                fals_crit = data.get("falsification_criteria", fals_crit)
        except Exception:
            pass

        spec = {
            "name": f"EXP_CYCLE_{cycle_id}_GPT3B_FLOPS_CUT",
            "hypothesis_title": hypothesis["title"],
            "objective": "Abaixar poder de computação e FLOPs, elevar tokens/s sem quantização",
            "rank_r": rank_r,
            "top_k": top_k,
            "margin_tau": margin_tau,
            "k_small": k_small,
            "k_large": k_large,
            "pass_criteria": pass_crit,
            "falsification_criteria": fals_crit
        }

        discord_bridge.publish_specification_card(
            cycle_id=cycle_id,
            hypothesis=hypothesis,
            spec=spec
        )

        return spec

    def execute_post_experiment_evaluation(
        self,
        cycle_id: int,
        hypothesis: Dict[str, Any],
        results: Dict[str, Any]
    ) -> Tuple[str, str]:
        """Avaliação dos números reais na RTX 3060 por ambas as MiMo."""
        eval_prompt = (
            f"RESULTADOS REAIS NA BANCADA GPT (~3B) NA RTX 3060:\n"
            f"- Acurácia Top-1 Argmax: {results.get('top1_accuracy', 0):.2f}%\n"
            f"- Redução de FLOPs: {results.get('flops_reduction_pct', 0):.1f}%\n"
            f"- Throughput Baseline: {results.get('baseline_tokens_per_sec', 0):.1f} tok/s\n"
            f"- Throughput Otimizado: {results.get('optimized_tokens_per_sec', 0):.1f} tok/s ({results.get('speedup_pct', 0):+.1f}%)\n"
            f"- Latência por Token: {results.get('latency_ms', 0):.2f} ms\n"
            f"- VRAM Alocada: {results.get('vram_mb', 0)} MB\n"
            f"- Divergência KL: {results.get('kl_divergence', 0):.6f}\n\n"
            f"Avalie se a hipótese foi APROVADA ou FALSIFICADA no objetivo de abaixar a computação sem quantização."
        )

        res_a = mimo_client.call_model(
            model_id=MODEL_A_ID,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_ULTRASPEED},
                {"role": "user", "content": eval_prompt}
            ]
        )
        time.sleep(2.0)
        res_b = mimo_client.call_model(
            model_id=MODEL_B_ID,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_PRO},
                {"role": "user", "content": eval_prompt}
            ]
        )

        persistence.record_debate_message(
            cycle_id=cycle_id,
            round_num=4,
            agent_id="Pesquisador A",
            model_name=MODEL_A_ID,
            message_type="VEREDITO_FINAL_GPT3B",
            content=res_a.get("content", ""),
            latency_sec=res_a.get("latency_sec", 0.0)
        )
        persistence.record_debate_message(
            cycle_id=cycle_id,
            round_num=4,
            agent_id="Pesquisador B",
            model_name=MODEL_B_ID,
            message_type="VEREDITO_FINAL_GPT3B",
            content=res_b.get("content", ""),
            latency_sec=res_b.get("latency_sec", 0.0)
        )

        is_approved = bool(results.get("pass_criteria", False))
        verdict = "APPROVED" if is_approved else "REJECTED"
        eval_summary = f"UltraSpeed: {res_a.get('content', '')[:300]}... | Pro: {res_b.get('content', '')[:300]}..."

        return verdict, eval_summary

debate_engine = DebateEngine()
