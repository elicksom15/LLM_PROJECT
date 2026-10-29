import sqlite3
import json

conn = sqlite3.connect(r"E:\AI_MODELS\research_duel\research_state.db")
c = conn.cursor()

c.execute("PRAGMA table_info(research_cycles)")
cols = [r[1] for r in c.fetchall()]
print("Columns in research_cycles:", cols)

print("\n=== TOTAL DE CICLOS REGISTRADOS ===")
c.execute("SELECT COUNT(*), verdict FROM research_cycles GROUP BY verdict")
for row in c.fetchall():
    print(f"Veredito: {row[1]} -> Total: {row[0]}")

print("\n=== HIPÓTESES APROVADAS ===")
c.execute("SELECT cycle_id, hypothesis_title, verdict, results_summary, status FROM research_cycles WHERE verdict = 'APPROVED' OR status = 'APPROVED'")
approved = c.fetchall()
for row in approved:
    print(f"\n--- Ciclo #{row[0]}: {row[1]} ---")
    print(f"  Veredito: {row[2]} | Status: {row[4]}")
    print(f"  Resultados: {str(row[3])[:300]}")

print("\n=== ÚLTIMOS 5 DEBATES CONCLUÍDOS ===")
c.execute("SELECT cycle_id, hypothesis_title, verdict, results_summary, next_steps FROM research_cycles ORDER BY cycle_id DESC LIMIT 5")
for row in c.fetchall():
    print(f"\nCiclo #{row[0]}: {row[1]} [{row[2]}]")
    print(f"  Resultados: {str(row[3])[:250]}")
    print(f"  Próximo passo: {str(row[4])[:250]}")
