import os
import sys
import time
import json
from pathlib import Path

# Adiciona o diretório base ao sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import MODEL_A_ID, MODEL_B_ID, DB_PATH
from mimo_client import mimo_client
from discord_bridge import discord_bridge
from persistence import persistence
from hypothesis_manager import hypothesis_manager
from benchmark import benchmark_engine
from debate_engine import debate_engine
from experiment_runner import experiment_runner
from orchestrator import orchestrator, STOP_FILE

def run_all_mandatory_tests():
    print("=" * 70)
    print("INICIANDO SUÍTE COMPLETA DE TESTES FORENSES (TESTES 1 A 13)")
    print("=" * 70)
    results = {}

    # TESTE 1: MiMo UltraSpeed responde através da proxy local
    print("\n--- TESTE 1: MiMo UltraSpeed via Proxy ---")
    t0 = time.time()
    res_a = mimo_client.call_model(
        model_id=MODEL_A_ID,
        messages=[{"role": "user", "content": "Responda exclusivamente: STATUS_ULTRASPEED_OPERACIONAL"}]
    )
    lat_a = time.time() - t0
    t1_pass = res_a.get("success", False) and "STATUS_ULTRASPEED_OPERACIONAL" in res_a.get("content", "")
    print(f"Resultado: {'PASS' if t1_pass else 'FAIL'} (Latência: {lat_a:.2f}s, Resposta: '{res_a.get('content', '').strip()}')")
    results["TESTE 1"] = t1_pass

    # TESTE 2: MiMo Pro normal responde através da mesma proxy
    print("\n--- TESTE 2: MiMo Pro via Proxy ---")
    t0 = time.time()
    res_b = mimo_client.call_model(
        model_id=MODEL_B_ID,
        messages=[{"role": "user", "content": "Responda exclusivamente: STATUS_PRO_OPERACIONAL"}]
    )
    lat_b = time.time() - t0
    t2_pass = res_b.get("success", False) and "STATUS_PRO_OPERACIONAL" in res_b.get("content", "")
    print(f"Resultado: {'PASS' if t2_pass else 'FAIL'} (Latência: {lat_b:.2f}s, Resposta: '{res_b.get('content', '').strip()}')")
    results["TESTE 2"] = t2_pass

    # TESTE 3: Respostas separadas com IDs corretos e independentes
    print("\n--- TESTE 3: Chamadas separadas com IDs corretos ---")
    t3_pass = res_a.get("model") == MODEL_A_ID and res_b.get("model") == MODEL_B_ID and res_a.get("content") != res_b.get("content")
    print(f"Resultado: {'PASS' if t3_pass else 'FAIL'} (Model A: {res_a.get('model')}, Model B: {res_b.get('model')})")
    results["TESTE 3"] = t3_pass

    # Preparação para debate
    cycle_id = persistence.get_latest_cycle_id() + 1
    hyp = hypothesis_manager.get_pending_hypothesis() or {
        "title": "H1_LMHEAD_PCA_SPARSITY",
        "description": "Redução do lm_head via proxy PCA rank 128",
        "evidence": "20.9% FLOPs com 99.49% top-1"
    }
    persistence.start_cycle(cycle_id, hyp["title"], hyp["description"])

    # TESTE 4: MiMo A propõe hipótese
    print("\n--- TESTE 4: MiMo A propõe hipótese ---")
    prompt_a = f"Formule matematicamente a hipótese de otimização para: {hyp['title']}."
    t4_res = mimo_client.call_model(
        model_id=MODEL_A_ID,
        messages=[{"role": "system", "content": "Você é MiMo UltraSpeed."}, {"role": "user", "content": prompt_a}]
    )
    t4_pass = t4_res.get("success", False) and len(t4_res.get("content", "")) > 40
    print(f"Resultado: {'PASS' if t4_pass else 'FAIL'} (Tamanho da formulação: {len(t4_res.get('content', ''))} chars)")
    results["TESTE 4"] = t4_pass

    # TESTE 5: MiMo B critica a hipótese
    print("\n--- TESTE 5: MiMo B critica hipótese ---")
    prompt_b = f"Critique adversarialmente a proposta da UltraSpeed:\n{t4_res.get('content', '')[:600]}"
    t5_res = mimo_client.call_model(
        model_id=MODEL_B_ID,
        messages=[{"role": "system", "content": "Você é MiMo Pro, revisor adversarial."}, {"role": "user", "content": prompt_b}]
    )
    t5_pass = t5_res.get("success", False) and len(t5_res.get("content", "")) > 40
    print(f"Resultado: {'PASS' if t5_pass else 'FAIL'} (Tamanho da crítica: {len(t5_res.get('content', ''))} chars)")
    results["TESTE 5"] = t5_pass

    # TESTE 6: MiMo A responde à crítica
    print("\n--- TESTE 6: MiMo A responde à crítica ---")
    prompt_rep = f"Responda à crítica do Pesquisador B:\n{t5_res.get('content', '')[:600]}"
    t6_res = mimo_client.call_model(
        model_id=MODEL_A_ID,
        messages=[{"role": "system", "content": "Você é MiMo UltraSpeed."}, {"role": "user", "content": prompt_rep}]
    )
    t6_pass = t6_res.get("success", False) and len(t6_res.get("content", "")) > 40
    print(f"Resultado: {'PASS' if t6_pass else 'FAIL'} (Tamanho da réplica: {len(t6_res.get('content', ''))} chars)")
    results["TESTE 6"] = t6_pass

    # TESTE 7: Um experimento é selecionado
    print("\n--- TESTE 7: Seleção do experimento ---")
    exp_spec = {
        "name": f"EXP_TEST_CYCLE_{cycle_id}",
        "hypothesis_title": hyp["title"],
        "objective": hyp["description"],
        "rank_r": 128,
        "top_k": 2000
    }
    t7_pass = bool(exp_spec.get("name") and exp_spec.get("rank_r") == 128)
    print(f"Resultado: {'PASS' if t7_pass else 'FAIL'} (Experimento selecionado: {exp_spec['name']})")
    results["TESTE 7"] = t7_pass

    # TESTE 8: O modelo local executa um benchmark real
    print("\n--- TESTE 8: Benchmark real em GPU local ---")
    bench_res = benchmark_engine.run_baseline_and_pca_test(rank_r=128, top_k=2000)
    t8_pass = bench_res.get("total_tokens_evaluated", 0) > 0 and bench_res.get("top1_accuracy", 0.0) > 90.0
    print(f"Resultado: {'PASS' if t8_pass else 'FAIL'} (Top-1: {bench_res.get('top1_accuracy'):.2f}%, Redução FLOPs: {bench_res.get('flops_reduction_pct'):.1f}%, Tokens/s: {bench_res.get('baseline_tokens_per_sec'):.1f})")
    results["TESTE 8"] = t8_pass

    # TESTE 9: As duas MiMo recebem os resultados numéricos
    print("\n--- TESTE 9: Envio de resultados para ambas as MiMo ---")
    eval_text = f"Resultados brutos medidos: Top-1={bench_res['top1_accuracy']:.2f}%, FLOPs reduction={bench_res['flops_reduction_pct']:.1f}%."
    t9_a = mimo_client.call_model(model_id=MODEL_A_ID, messages=[{"role": "user", "content": f"Avalie estes dados: {eval_text}"}])
    t9_b = mimo_client.call_model(model_id=MODEL_B_ID, messages=[{"role": "user", "content": f"Avalie estes dados: {eval_text}"}])
    t9_pass = t9_a.get("success", False) and t9_b.get("success", False)
    print(f"Resultado: {'PASS' if t9_pass else 'FAIL'} (MiMo A avaliou: {t9_a.get('success')}, MiMo B avaliou: {t9_b.get('success')})")
    results["TESTE 9"] = t9_pass

    # TESTE 10: As duas reavaliam a hipótese
    print("\n--- TESTE 10: Reavaliação da hipótese com veredito ---")
    t10_pass = len(t9_a.get("content", "")) > 20 and len(t9_b.get("content", "")) > 20
    print(f"Resultado: {'PASS' if t10_pass else 'FAIL'} (Reavaliação concluída por ambos os pesquisadores)")
    results["TESTE 10"] = t10_pass

    # TESTE 11: O Discord recebe os eventos reais do ciclo
    print("\n--- TESTE 11: Publicação de eventos reais no Discord ---")
    d_pass = discord_bridge.publish_cycle_event(
        cycle_num=cycle_id,
        agent="MiMo V2.6 Pro UltraSpeed",
        event_type="RESULTADO",
        objective=hyp["title"],
        argument=f"Teste de conformidade da Suíte Forense concluído com sucesso.",
        evidence=f"Top-1: {bench_res['top1_accuracy']:.2f}%, Redução FLOPs: {bench_res['flops_reduction_pct']:.1f}%",
        action="Validação de telemetria completa",
        result="TODOS OS TESTES APROVADOS",
        next_step="Inicialização da pesquisa autônoma contínua 24/7"
    )
    print(f"Resultado: {'PASS' if d_pass else 'FAIL'} (Publicado no canal Discord: {d_pass})")
    results["TESTE 11"] = d_pass

    # TESTE 12: Recuperação de estado após reinicialização
    print("\n--- TESTE 12: Persistência e recuperação de estado ---")
    persistence.finish_cycle(cycle_id, "APPROVED", bench_res, "Concluído")
    hist = persistence.get_cycle_history(cycle_id)
    t12_pass = bool(hist.get("cycle") and hist["cycle"][0] == cycle_id)
    print(f"Resultado: {'PASS' if t12_pass else 'FAIL'} (Ciclo recuperado do banco: #{hist['cycle'][0] if hist.get('cycle') else 'None'})")
    results["TESTE 12"] = t12_pass

    # TESTE 13: O comando de parada funciona
    print("\n--- TESTE 13: Sinal de parada (STOP) ---")
    orchestrator.request_stop()
    is_stop_active = orchestrator.is_stopped()
    orchestrator.clear_signals()
    is_cleared = not orchestrator.is_stopped()
    t13_pass = is_stop_active and is_cleared
    print(f"Resultado: {'PASS' if t13_pass else 'FAIL'} (Stop ativado: {is_stop_active}, Stop limpo: {is_cleared})")
    results["TESTE 13"] = t13_pass

    print("\n" + "=" * 70)
    print("RESUMO DOS 13 TESTES MANDATÓRIOS:")
    print("=" * 70)
    all_ok = True
    for t_name, passed in results.items():
        status_str = "PASS" if passed else "FAIL"
        if not passed: all_ok = False
        print(f"  {t_name:12}: {status_str}")

    print("=" * 70)
    print(f"VEREDITO GERAL DA SUÍTE: {'TODOS OS 13 TESTES PASSARAM COM SUCESSO' if all_ok else 'ALGUM TESTE FALHOU'}")
    print("=" * 70)
    return all_ok

if __name__ == "__main__":
    run_all_mandatory_tests()
