import sys
import sqlite3

sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect(r"E:\AI_MODELS\research_duel\research_state.db")
c = conn.cursor()

c.execute("SELECT cycle_id, round_num, agent_id, content FROM debate_messages WHERE round_num IN (1, 2, 4) ORDER BY id DESC LIMIT 6")
rows = c.fetchall()
for r in reversed(rows):
    print(f"=== CICLO #{r[0]} | ROUND {r[1]} | AGENTE: {r[2]} ===")
    print(r[3][:600])
    print("-" * 50)
