import sys
import sqlite3
import json

sys.stdout.reconfigure(encoding="utf-8")

conn = sqlite3.connect(r"E:\AI_MODELS\research_duel\research_state.db")
c = conn.cursor()

print("=== AS 7 HIPÓTESES APROVADAS PELO DUAL MIMO ENGINE ===")
c.execute("SELECT cycle_id, hypothesis_title, verdict, metrics_json, next_step FROM research_cycles WHERE verdict = 'APPROVED' OR status = 'APPROVED'")
approved = c.fetchall()
for row in approved:
    cid, title, verd, metrics_raw, next_s = row
    print(f"\n[APROVADO] CICLO #{cid}: {title}")
    try:
        m = json.loads(metrics_raw) if metrics_raw else {}
        print(f"   Top-1 Accuracy: {m.get('top1_accuracy', m.get('top1_accuracy_pct'))}%")
        print(f"   FLOPs Reduction: {m.get('flops_reduction_pct')}%")
        print(f"   Throughput (tok/s): {m.get('tokens_per_sec', m.get('optimized_tokens_per_sec'))} (Baseline: {m.get('baseline_tokens_per_sec')})")
        print(f"   Speedup medido: {m.get('speedup_pct')}%")
        print(f"   VRAM Peak: {m.get('vram_mb')} MB")
        print(f"   KL Divergence: {m.get('kl_divergence')}")
    except Exception as ex:
        print(f"   Metrics raw: {metrics_raw[:150]}")
    print(f"   Conclusão / Next Step: {next_s}")

print("\n=== DEBATE RECENTE E INSIGHTS CHAVE (ÚLTIMAS MENSAGENS DE DEBATE) ===")
c.execute("SELECT cycle_id, agent_name, round_type, content FROM debate_messages WHERE round_type IN ('round4_eval', 'round2_critique') ORDER BY id DESC LIMIT 4")
for row in c.fetchall():
    print(f"\n[Ciclo #{row[0]} | {row[1]} | {row[2]}]")
    print(f"{row[3][:500]}...\n")
