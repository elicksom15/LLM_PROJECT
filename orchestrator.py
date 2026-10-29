import time
import sys
import logging
from typing import Dict, Any, Optional
from config import BASE_DIR, LOGS_DIR
from mimo_client import mimo_client
from persistence import persistence
from hypothesis_manager import hypothesis_manager
from debate_engine import debate_engine
from experiment_runner import experiment_runner
from discord_bridge import discord_bridge
from analytical_engine import analytical_engine
from git_sync import git_sync

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "orchestrator.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("research_duel.orchestrator")

STOP_FILE = BASE_DIR / "STOP.signal"
PAUSE_FILE = BASE_DIR / "PAUSE.signal"

class ResearchOrchestrator:
    def __init__(self):
        self.running = False

    def is_stopped(self) -> bool:
        return STOP_FILE.exists()

    def is_paused(self) -> bool:
        return PAUSE_FILE.exists()

    def request_stop(self):
        STOP_FILE.touch()
        logger.info("Sinal de PARADA (STOP.signal) gravado.")

    def request_pause(self):
        PAUSE_FILE.touch()
        logger.info("Sinal de PAUSA (PAUSE.signal) gravado.")

    def clear_signals(self):
        if STOP_FILE.exists():
            STOP_FILE.unlink()
        if PAUSE_FILE.exists():
            PAUSE_FILE.unlink()

    def run_single_cycle(self) -> Dict[str, Any]:
        """
        Executa um ciclo completo de ponta a ponta com continuidade e contexto máximo:
        1. Recupera estado atual no SQLite (começa exatamente de onde parou)
        2. Seleciona próxima hipótese pendente (ou sintetiza nova fronteira)
        3. Rodada 1: Investigação independente (com Contexto Científico Máximo)
        4. Rodada 2: Confronto e críticas adversariais
        5. Rodada 3: Especificação experimental consensual
        6. Fase 0: Auditoria matemática prévia (corte >= 75%)
        7. Execução real do benchmark na RTX 3060 12GB (se aprovado no cálculo)
        8. Rodada 4: Avaliação crítica pós-experimento por ambas as MiMo
        9. Sincronização contínua com Git (commit + push imediato)
        10. Publicação de Rich Embed no Discord com link de commit e ledger
        """
        self.clear_signals()
        cycle_id = persistence.get_latest_cycle_id() + 1
        hypothesis = hypothesis_manager.get_pending_hypothesis()

        if not hypothesis:
            logger.info("Nenhuma hipótese pendente na fila. Sintetizando nova hipótese de fronteira com as MiMo...")
            hypothesis = hypothesis_manager.synthesize_frontier_hypothesis(cycle_id)

        logger.info(f"=== INICIANDO RESEARCH CYCLE #{cycle_id}: {hypothesis['title']} ===")
        persistence.start_cycle(cycle_id, hypothesis["title"], hypothesis["description"])

        # RODADA 1: Investigação Independente
        logger.info(f"[CICLO #{cycle_id}] Rodada 1: Investigação Independente com Contexto Máximo...")
        res_a, res_b = debate_engine.execute_round1_investigation(cycle_id, hypothesis)

        # Se alguma das MiMo falhou por cota diária ou erro de API, suspender o ciclo e aguardar
        if not res_a.get("success") or not res_b.get("success"):
            err_msg = res_a.get("error") or res_b.get("error") or "Falha de comunicação com as MiMo"
            logger.warning(f"[CICLO #{cycle_id}] Interrompido por erro de cota/API: {err_msg}. Pausando ciclo.")
            discord_bridge.send_raw_message(
                f"⏸️ **[PESQUISA EM PAUSA TEMPORÁRIA]**\n"
                f"A API da Xiaomi atingiu o limite de requisições diárias (`今日请求次数已达上限` / 4005).\n"
                f"O orquestrador aguardará renovação de sessão ou rotação de contas pelo auto-refill antes de prosseguir com o **Ciclo #{cycle_id}**."
            )
            time.sleep(60.0)
            return {
                "cycle_id": cycle_id,
                "hypothesis": hypothesis["title"],
                "verdict": "PAUSED_QUOTA",
                "metrics": {}
            }

        # Intervalo anti-rate-limit
        time.sleep(2.5)

        # RODADA 2: Confronto Adversarial
        logger.info(f"[CICLO #{cycle_id}] Rodada 2: Confronto e Críticas Adversariais...")
        crit_a, crit_b = debate_engine.execute_round2_confrontation(cycle_id, hypothesis, res_a, res_b)

        time.sleep(2.5)

        # RODADA 3: Especificação Experimental
        logger.info(f"[CICLO #{cycle_id}] Rodada 3: Consenso e Especificação Experimental...")
        exp_spec = debate_engine.execute_round3_specification(cycle_id, hypothesis, crit_a, crit_b)

        # FASE 0 OBRIGATÓRIA: AUDITORIA MATEMÁTICA E CÁLCULO ANALÍTICO (CÁLCULO PRIMEIRO, GPU DEPOIS)
        logger.info(f"[CICLO #{cycle_id}] Fase 0: Auditoria Matemática Prévia de FLOPs e Complexidade...")
        math_audit = analytical_engine.audit_hypothesis(hypothesis, exp_spec)
        discord_bridge.publish_analytical_gate_card(cycle_id, hypothesis, math_audit)

        if not math_audit.get("passed_math_gate", False):
            # REJEIÇÃO MATEMÁTICA IMEDIATA: Não gasta GPU à toa!
            rejection_reason = math_audit.get("rejection_reason", "Cálculo não provou corte >= 75% de FLOPs.")
            logger.warning(f"[CICLO #{cycle_id}] Hipótese REJEITADA NO CÁLCULO: {rejection_reason}. GPU preservada!")
            verdict = "REJECTED_ANALYTICAL"
            exp_results = {
                "top1_accuracy": 0.0,
                "top1_accuracy_pct": 0.0,
                "flops_reduction_pct": math_audit.get("flops_reduction_pct", 0.0),
                "speedup_factor": math_audit.get("theoretical_speedup", 1.0),
                "vram_allocated_mb": 0.0,
                "tokens_per_sec": 0.0,
                "latency_per_token_ms": 0.0,
                "analytical_rejection": True,
                "math_formula": math_audit.get("math_formula", "")
            }
            hypothesis_manager.update_status(hypothesis["title"], verdict, cycle_id)
            persistence.finish_cycle(cycle_id, verdict, exp_results, f"Rejeitada na Fase 0: {rejection_reason}")
            
            discord_bridge.send_raw_message(
                f"🛑 **[GPU POUPADA — CICLO #{cycle_id}]**\n"
                f"Hipótese `{hypothesis['title']}` foi **REJEITADA NA AUDITORIA MATEMÁTICA**.\n"
                f"Redução teórica de FLOPs ({math_audit.get('flops_reduction_pct', 0.0):.1f}%) não atingiu o limiar de 75.0%.\n"
                f"Nenhum ciclo da RTX 3060 foi desperdiçado. Avançando para a próxima formulação inédita."
            )

            # Sincronização contínua com GitHub
            commit_info = git_sync.commit_and_push(cycle_id, hypothesis["title"], verdict)
            if commit_info:
                discord_bridge.publish_git_sync_card(cycle_id, commit_info)

            time.sleep(3.0)
            return {
                "cycle_id": cycle_id,
                "hypothesis": hypothesis["title"],
                "verdict": verdict,
                "metrics": exp_results
            }

        # SE PASSOU NO CÁLCULO: EXECUÇÃO DO EXPERIMENTO NA GPU (RTX 3060 12GB)
        logger.info(f"[CICLO #{cycle_id}] Hipótese APROVADA NO CÁLCULO! Executando Experimento Físico na RTX 3060...")
        exp_run_res = experiment_runner.run_experiment(cycle_id, exp_spec)
        exp_results = exp_run_res.get("results", {})

        time.sleep(2.0)

        # RODADA 4: Avaliação Pós-Experimento
        logger.info(f"[CICLO #{cycle_id}] Rodada 4: Avaliação dos Resultados Reais pelas MiMo...")
        verdict, eval_summary = debate_engine.execute_post_experiment_evaluation(cycle_id, hypothesis, exp_results)

        # Publicar Card de Resultados de Alto Impacto no Discord
        discord_bridge.publish_experiment_card(
            cycle_id=cycle_id,
            hypothesis=hypothesis,
            spec=exp_spec,
            results=exp_results,
            verdict=verdict,
            eval_summary=eval_summary
        )

        # Atualização de status e persistência SQLite
        hypothesis_manager.update_status(hypothesis["title"], verdict, cycle_id)
        next_step = "Incorporado ao Ledger Científico. Avançando para próxima fronteira." if verdict == "APPROVED" else "Investigar causa de falsificação no próximo ciclo."
        persistence.finish_cycle(cycle_id, verdict, exp_results, next_step)

        # Sincronização contínua com GitHub
        commit_info = git_sync.commit_and_push(cycle_id, hypothesis["title"], verdict)
        if commit_info:
            discord_bridge.publish_git_sync_card(cycle_id, commit_info)

        logger.info(f"=== RESEARCH CYCLE #{cycle_id} CONCLUÍDO COM SUCESSO: VEREDITO = {verdict} ===")
        return {
            "cycle_id": cycle_id,
            "hypothesis": hypothesis["title"],
            "verdict": verdict,
            "metrics": exp_results
        }

    def start_loop(self, max_cycles: int = 100, interval_sec: float = 20.0):
        """
        Loop contínuo de pesquisa autônoma 24/7.
        Executa ciclo após ciclo, puxando e enviando atualizações ao GitHub e transmitindo ao Discord.
        """
        logger.info(">>> INICIANDO MOTOR DE PESQUISA AUTÔNOMA 24/7 (DUAL MIMO RESEARCH ENGINE) <<<")
        self.clear_signals()
        self.running = True

        # Sincronização inicial com o GitHub para garantir continuidade
        git_sync.pull_state()

        cycle_count = 0
        while self.running and cycle_count < max_cycles:
            if self.is_stopped():
                logger.info("Execução interrompida por STOP.signal.")
                break
            while self.is_paused():
                logger.info("Execução pausada (PAUSE.signal ativo). Aguardando 10s...")
                time.sleep(10)
                if self.is_stopped():
                    break

            try:
                cycle_res = self.run_single_cycle()
                if cycle_res.get("verdict") == "PAUSED_QUOTA":
                    logger.info("Ciclo pausado por limite de cota Xiaomi. Aguardando 60s antes de nova tentativa...")
                    time.sleep(60.0)
                    continue

                cycle_count += 1
                logger.info(f"[LOOP 24/7] Ciclo #{cycle_res.get('cycle_id')} finalizado com sucesso ({cycle_count}/{max_cycles}).")
            except Exception as e:
                logger.error(f"[LOOP 24/7] Erro inesperado no ciclo de pesquisa: {e}", exc_info=True)
                time.sleep(15)

            if cycle_count < max_cycles:
                logger.info(f"Intervalo de resfriamento entre ciclos ({interval_sec}s)...")
                time.sleep(interval_sec)

        logger.info("Dual MiMo Research Engine finalizou a sessão autônoma.")

orchestrator = ResearchOrchestrator()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "loop":
        max_c = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        orchestrator.start_loop(max_cycles=max_c, interval_sec=20.0)
    else:
        orchestrator.run_single_cycle()
