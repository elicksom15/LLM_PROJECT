import sys
import sqlite3

sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect(r"E:\AI_MODELS\research_duel\research_state.db")
c = conn.cursor()

c.execute("SELECT round_num, agent_id, content FROM debate_messages WHERE cycle_id = 68")
rows = c.fetchall()
for r in rows:
    print(f"=== ROUND {r[0]} | AGENTE: {r[1]} ===")
    print(r[2][:700])
    print("-" * 50)
