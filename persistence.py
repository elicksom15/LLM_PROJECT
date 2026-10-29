import sqlite3
import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from config import DB_PATH

class ResearchPersistence:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = str(db_path)
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("""
            CREATE TABLE IF NOT EXISTS research_cycles (
                cycle_id INTEGER PRIMARY KEY,
                created_at REAL,
                status TEXT,
                hypothesis_title TEXT,
                objective TEXT,
                experiment_name TEXT,
                verdict TEXT,
                metrics_json TEXT,
                next_step TEXT
            )
            """)
            c.execute("""
            CREATE TABLE IF NOT EXISTS debate_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_id INTEGER,
                round_num INTEGER,
                agent_id TEXT,
                model_name TEXT,
                message_type TEXT,
                content TEXT,
                latency_sec REAL,
                timestamp REAL
            )
            """)
            c.execute("""
            CREATE TABLE IF NOT EXISTS hypotheses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE,
                description TEXT,
                status TEXT,  -- PENDING, APPROVED, REJECTED, FALSIFIED
                proposed_by TEXT,
                cycle_id INTEGER,
                evidence TEXT,
                created_at REAL,
                updated_at REAL
            )
            """)
            c.execute("""
            CREATE TABLE IF NOT EXISTS experiment_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_id INTEGER,
                experiment_name TEXT,
                code_hash TEXT,
                baseline_metric REAL,
                optimized_metric REAL,
                flops_reduction_pct REAL,
                top1_accuracy REAL,
                latency_ms REAL,
                vram_mb INTEGER,
                tokens_per_sec REAL,
                raw_results_json TEXT,
                timestamp REAL
            )
            """)
            conn.commit()

    def get_latest_cycle_id(self) -> int:
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT MAX(cycle_id) FROM research_cycles")
            row = c.fetchone()
            return row[0] if row and row[0] is not None else 0

    def start_cycle(self, cycle_id: int, hypothesis_title: str, objective: str):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("""
            INSERT OR REPLACE INTO research_cycles 
            (cycle_id, created_at, status, hypothesis_title, objective, verdict, metrics_json, next_step)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (cycle_id, time.time(), "IN_PROGRESS", hypothesis_title, objective, "PENDING", "{}", "Iniciando debate"))
            conn.commit()

    def record_debate_message(
        self,
        cycle_id: int,
        round_num: int,
        agent_id: str,
        model_name: str,
        message_type: str,
        content: str,
        latency_sec: float
    ):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("""
            INSERT INTO debate_messages 
            (cycle_id, round_num, agent_id, model_name, message_type, content, latency_sec, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (cycle_id, round_num, agent_id, model_name, message_type, content, latency_sec, time.time()))
            conn.commit()

    def record_experiment(
        self,
        cycle_id: int,
        experiment_name: str,
        metrics: Dict[str, Any],
        raw_results: Dict[str, Any]
    ):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("""
            INSERT INTO experiment_records 
            (cycle_id, experiment_name, code_hash, baseline_metric, optimized_metric, 
             flops_reduction_pct, top1_accuracy, latency_ms, vram_mb, tokens_per_sec, raw_results_json, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cycle_id,
                experiment_name,
                metrics.get("code_hash", ""),
                metrics.get("baseline_metric", 0.0),
                metrics.get("optimized_metric", 0.0),
                metrics.get("flops_reduction_pct", 0.0),
                metrics.get("top1_accuracy", 0.0),
                metrics.get("latency_ms", 0.0),
                metrics.get("vram_mb", 0),
                metrics.get("tokens_per_sec", 0.0),
                json.dumps(raw_results),
                time.time()
            ))
            conn.commit()

    def finish_cycle(self, cycle_id: int, verdict: str, metrics: Dict[str, Any], next_step: str):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("""
            UPDATE research_cycles 
            SET status = ?, verdict = ?, metrics_json = ?, next_step = ?
            WHERE cycle_id = ?
            """, ("COMPLETED", verdict, json.dumps(metrics), next_step, cycle_id))
            conn.commit()

    def get_cycle(self, cycle_id: int):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT cycle_id, created_at, status, hypothesis_title, objective, verdict, metrics_json, next_step "
                "FROM research_cycles WHERE cycle_id = ?",
                (cycle_id,)
            )
            row = c.fetchone()
            if not row:
                return None
            return {
                "cycle_id": row[0],
                "created_at": row[1],
                "status": row[2],
                "hypothesis_title": row[3],
                "objective": row[4],
                "verdict": row[5],
                "metrics_json": row[6],
                "next_step": row[7]
            }

    def get_cycle_history(self, cycle_id: int) -> Dict[str, Any]:
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM research_cycles WHERE cycle_id = ?", (cycle_id,))
            cycle_row = c.fetchone()
            c.execute("SELECT round_num, agent_id, model_name, message_type, content, latency_sec FROM debate_messages WHERE cycle_id = ? ORDER BY id ASC", (cycle_id,))
            messages = c.fetchall()
            c.execute("SELECT * FROM experiment_records WHERE cycle_id = ?", (cycle_id,))
            exp_row = c.fetchone()
            return {
                "cycle": cycle_row,
                "messages": messages,
                "experiment": exp_row
            }

    def get_summary_stats(self) -> Dict[str, Any]:
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM research_cycles WHERE verdict = 'APPROVED'")
            app = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM research_cycles WHERE verdict IN ('REJECTED', 'FALSIFIED')")
            rej = c.fetchone()[0]
            c.execute("SELECT MAX(cycle_id) FROM research_cycles")
            max_c = c.fetchone()[0] or 0
            return {
                "approved_count": app,
                "rejected_count": rej,
                "total_cycles": max_c
            }

persistence = ResearchPersistence()
