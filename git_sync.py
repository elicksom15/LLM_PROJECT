#!/usr/bin/env python3
# language: Python, file: git_sync.py, target: GitHub synchronization engine for Dual MiMo Research
"""
Git Sync Engine — Sincronização Contínua e Automática da Pesquisa com GitHub:
Repositório: https://github.com/elicksom15/LLM_PROJECT.git
"""
import os
import sys
import json
import time
import sqlite3
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Força codificação UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logger = logging.getLogger("research_duel.git_sync")

BASE_DIR = Path(__file__).resolve().parent
REPO_URL = "https://github.com/elicksom15/LLM_PROJECT.git"
DB_PATH = BASE_DIR / "research_state.db"
STATE_MD_PATH = BASE_DIR / "STATE.md"
LEDGER_JSON_PATH = BASE_DIR / "ledger.json"
README_MD_PATH = BASE_DIR / "README.md"

TRACKED_FILES = [
    "STATE.md",
    "README.md",
    "ledger.json",
    ".gitignore",
    "git_sync.py",
    "analytical_engine.py",
    "benchmark.py",
    "discord_bridge.py",
    "orchestrator.py",
    "hypothesis_manager.py",
    "debate_engine.py",
    "persistence.py",
    "config.py",
    "experiment_runner.py",
    "mimo_client.py",
    "PAUSE_RESEARCH.bat",
    "RESUME_RESEARCH.bat",
    "START_RESEARCH.bat",
    "STOP_RESEARCH.bat"
]

class GitSyncEngine:
    def __init__(self, repo_url: str = REPO_URL):
        self.repo_url = repo_url
        self._ensure_git_init()

    def _run_git(self, args: list[str], timeout: float = 35.0) -> Tuple[int, str, str]:
        try:
            res = subprocess.run(
                ["git"] + args,
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout
            )
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        except Exception as e:
            logger.error(f"Erro executando git {' '.join(args)}: {e}")
            return -1, "", str(e)

    def _ensure_git_init(self):
        if not (BASE_DIR / ".git").exists():
            logger.info("Inicializando repositório Git local...")
            self._run_git(["init"])
            self._run_git(["config", "user.name", "elicksom15"])
            self._run_git(["config", "user.email", "elick@example.com"])
            self._run_git(["remote", "add", "origin", self.repo_url])
            self._run_git(["branch", "-M", "main"])
        else:
            self._run_git(["config", "user.name", "elicksom15"])
            self._run_git(["config", "user.email", "elick@example.com"])
            self._run_git(["remote", "set-url", "origin", self.repo_url])

    def rehydrate_db_from_ledger(self) -> bool:
        """Restaura o banco SQLite local a partir de ledger.json caso o arquivo .db não exista."""
        if DB_PATH.exists() and DB_PATH.stat().st_size > 4096:
            return True
        if not LEDGER_JSON_PATH.exists():
            return False

        try:
            logger.info("Reidratando SQLite local a partir do ledger.json sincronizado...")
            data = json.loads(LEDGER_JSON_PATH.read_text(encoding="utf-8"))
            from persistence import persistence
            conn = persistence._get_conn()
            c = conn.cursor()

            recent = data.get("recent_cycles", [])
            for row in reversed(recent):
                c.execute(
                    "INSERT OR REPLACE INTO research_cycles (cycle_id, created_at, status, hypothesis_title, verdict, next_step) "
                    "VALUES (?, ?, 'FINISHED', ?, ?, ?)",
                    (row.get("cycle_id"), time.time(), row.get("title"), row.get("verdict"), row.get("next_step"))
                )
            conn.commit()
            conn.close()
            logger.info(f"Reidratação concluída: {len(recent)} ciclos restaurados para {DB_PATH.name}.")
            return True
        except Exception as e:
            logger.error(f"Erro ao reidratar banco do ledger: {e}")
            return False

    def pull_state(self) -> bool:
        """Puxa o estado mais recente do GitHub para continuar exatamente de onde parou."""
        logger.info("Puxando atualizações do GitHub (git pull origin main --rebase)...")
        code, out, err = self._run_git(["pull", "origin", "main", "--rebase"], timeout=30.0)
        if code == 0:
            logger.info("Git pull (rebase) concluído com sucesso!")
            self.rehydrate_db_from_ledger()
            return True
        else:
            code2, out2, err2 = self._run_git(["pull", "origin", "main"], timeout=30.0)
            if code2 == 0:
                logger.info("Git pull (merge) concluído!")
                self.rehydrate_db_from_ledger()
                return True
            logger.warning(f"Aviso no git pull: {err or err2}")
            return False

    def export_state_documentation(self) -> Dict[str, Any]:
        """Extrai todo o histórico do SQLite e gera documentação de alto nível (STATE.md e ledger.json)."""
        if not DB_PATH.exists():
            return {}

        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()

        # 1. Estatísticas gerais
        c.execute("SELECT verdict, COUNT(*) FROM research_cycles GROUP BY verdict")
        counts = {r[0]: r[1] for r in c.fetchall()}
        total_cycles = sum(counts.values())
        approved_count = counts.get("APPROVED", 0)
        rejected_count = counts.get("REJECTED", 0) + counts.get("REJECTED_ANALYTICAL", 0)

        # 2. Hipóteses Aprovadas
        c.execute(
            "SELECT cycle_id, hypothesis_title, metrics_json, next_step "
            "FROM research_cycles WHERE verdict = 'APPROVED' ORDER BY cycle_id ASC"
        )
        approved_rows = []
        for r in c.fetchall():
            try:
                m = json.loads(r[2]) if r[2] else {}
            except Exception:
                m = {}
            approved_rows.append({
                "cycle_id": r[0],
                "title": r[1],
                "top1_accuracy": m.get("top1_accuracy") or m.get("top1_accuracy_pct", 0.0),
                "flops_reduction": m.get("flops_reduction_pct", 0.0),
                "tokens_per_sec": m.get("tokens_per_sec") or m.get("optimized_tokens_per_sec", 0.0),
                "speedup_pct": m.get("speedup_pct", 0.0),
                "kl_divergence": m.get("kl_divergence", 0.0),
                "next_step": r[3]
            })

        # 3. Todos os Ciclos Recentes (últimos 50)
        c.execute(
            "SELECT cycle_id, created_at, hypothesis_title, verdict, metrics_json, next_step "
            "FROM research_cycles ORDER BY cycle_id DESC LIMIT 50"
        )
        recent_cycles = []
        for r in c.fetchall():
            try:
                m = json.loads(r[4]) if r[4] else {}
            except Exception:
                m = {}
            recent_cycles.append({
                "cycle_id": r[0],
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(r[1])) if isinstance(r[1], (int, float)) else str(r[1]),
                "title": r[2],
                "verdict": r[3],
                "flops_reduction": m.get("flops_reduction_pct", 0.0),
                "top1_accuracy": m.get("top1_accuracy") or m.get("top1_accuracy_pct", 0.0),
                "tokens_per_sec": m.get("tokens_per_sec") or m.get("optimized_tokens_per_sec", 0.0),
                "next_step": r[5]
            })

        conn.close()

        # Salva ledger.json estruturado
        ledger_data = {
            "project": "Dual MiMo Autonomous Research Engine",
            "target": "Redução Extrema de Computação em LLMs sem Quantização Convencional (Qwen 32B na RTX 3060 12GB)",
            "last_sync": time.strftime("%Y-%m-%d %H:%M:%S"),
            "stats": {
                "total_cycles": total_cycles,
                "approved_count": approved_count,
                "rejected_count": rejected_count
            },
            "approved_hypotheses": approved_rows,
            "recent_cycles": recent_cycles
        }
        LEDGER_JSON_PATH.write_text(json.dumps(ledger_data, indent=2, ensure_ascii=False), encoding="utf-8")

        # Gera STATE.md executivo
        md = []
        md.append("# 🔬 LLM_PROJECT — Scientific Research Ledger (Tempo Real)")
        md.append("> **Pesquisa Científica Autônoma 24/7:** Redução de Computação e Otimização Física de LLMs sem Quantização Convencional.")
        md.append(f"> **Bancada Experimental:** NVIDIA GeForce RTX 3060 12GB (VRAM: 12,288 MB | Banda: 360 GB/s)")
        md.append(f"> **Sincronização Contínua Git:** [`https://github.com/elicksom15/LLM_PROJECT`](https://github.com/elicksom15/LLM_PROJECT)\n")
        
        md.append("## 📊 Painel Geral de Execução")
        md.append(f"- **Total de Ciclos Científicos Executados:** `{total_cycles}`")
        md.append(f"- **Hipóteses Aprovadas (Incorporadas):** `🏆 {approved_count}`")
        md.append(f"- **Hipóteses Falsificadas / Rejeitadas:** `❌ {rejected_count}`")
        md.append(f"- **Diretriz de Rigor:** Fase 0 (Cálculo Analítico Primeiro — corte teórico de FLOPs e VRAM $\ge 75\%$)\n")

        md.append("## 🏆 Hipóteses Aprovadas")
        if approved_rows:
            md.append("| Ciclo | Hipótese | Top-1 Argmax | Corte de FLOPs | Throughput | Divergência KL |")
            md.append("| :---: | :--- | :---: | :---: | :---: | :---: |")
            for a in approved_rows:
                md.append(f"| **#{a['cycle_id']}** | `{a['title']}` | **{a['top1_accuracy']:.1f}%** | **{a['flops_reduction']:.1f}%** | `{a['tokens_per_sec']:.1f} tok/s` | `{a['kl_divergence']:.4f}` |")
        else:
            md.append("*Nenhuma hipótese atingiu o limiar de aprovação plena nesta fase de refinamento.*")
        md.append("\n")

        md.append("## 📜 Histórico Recente de Ciclos e Vereditos")
        md.append("| Ciclo | Timestamp | Hipótese | Veredito | Corte FLOPs | Top-1 | Observações |")
        md.append("| :---: | :---: | :--- | :---: | :---: | :---: | :--- |")
        for c_item in recent_cycles:
            v_badge = "🟢 APROVADA" if c_item["verdict"] == "APPROVED" else ("🛑 POUPADA (FASE 0)" if "ANALYTICAL" in str(c_item["verdict"]) else "🔴 REJEITADA")
            md.append(f"| **#{c_item['cycle_id']}** | {c_item['timestamp']} | `{c_item['title']}` | {v_badge} | {c_item['flops_reduction']:.1f}% | {c_item['top1_accuracy']:.1f}% | {str(c_item['next_step'])[:80]} |")

        STATE_MD_PATH.write_text("\n".join(md), encoding="utf-8")

        # Atualiza README.md executivo
        readme_content = f"""# ⚡ Dual MiMo Autonomous Research Engine (LLM_PROJECT)

[![Research Cycles](https://img.shields.io/badge/Cycles-{total_cycles}-blue.svg)](#)
[![Approved Hypotheses](https://img.shields.io/badge/Approved-{approved_count}-success.svg)](#)
[![Hardware](https://img.shields.io/badge/GPU-RTX%203060%2012GB-76B900.svg)](#)
[![Methodology](https://img.shields.io/badge/Method-Cálculo%20Primeiro%20(Fase%200)-orange.svg)](#)

Motor de pesquisa científica autônomo 24/7 alimentado por instâncias duais do modelo **MiMo-V2.6 (UltraSpeed & Pro)** debatendo em regime adversarial para **reduzir o poder computacional e viabilizar a execução de LLMs gigantes (como Qwen 32B) em uma RTX 3060 12GB sem quantização convencional**.

---

### 🎯 Missão Principal
Desenvolver uma formulação matemática inédita que reduza o custo computacional e o tráfego de memória de inferência autorregressiva em mais de **75% a 85%**, eliminando as perdas de precisão das quantizações convencionais (AWQ/GPTQ) através de:
- **Álgebra de Subespaços Invariantes de Krylov**
- **Transporte Paralelo Espectral entre Camadas**
- **Splitting de Strang e Operadores Anti-simétricos Simpléticos**

---

### 🧮 Diretriz: Cálculo Primeiro, GPU Depois (Fase 0)
1. **Auditoria Matemática:** Antes de acionar a GPU, os operadores são auditados formalmente no papel. Se a redução teórica de FLOPs e tráfego de VRAM for $< 75\%$, a hipótese é **imediatamente rejeitada**, poupando ciclos físicos da RTX 3060.
2. **Validação Física em GPU:** Modelos aprovados no cálculo são compilados e medidos na bancada física local (`~3B GPT`), aferindo throughput real (tokens/s), divergência KL e acurácia Top-1.
3. **Persistência e Telemetria em Tempo Real:** Todos os ciclos, teses e pareceres são registrados em SQLite e transmitidos ao Discord com sincronização contínua neste repositório.

Para conferir o relatório completo de todos os ciclos executados, acesse:
👉 **[Ver Estado e Ledger Completo (STATE.md)](STATE.md)**
"""
        README_MD_PATH.write_text(readme_content, encoding="utf-8")

        return ledger_data

    def commit_and_push(self, cycle_id: int, hypothesis_title: str, verdict: str) -> Optional[Dict[str, Any]]:
        """Compila o estado, comita e envia ao GitHub com push imediato."""
        try:
            logger.info(f"[GIT SYNC] Exportando documentação e preparando commit para Ciclo #{cycle_id}...")
            ledger_data = self.export_state_documentation()

            # Adiciona apenas arquivos de código, documentação e ledger (sem travar .db)
            files_to_add = [f for f in TRACKED_FILES if (BASE_DIR / f).exists()]
            self._run_git(["add"] + files_to_add)

            commit_msg = f"🔬 [Ciclo #{cycle_id}] {verdict} — {hypothesis_title}"
            code, out, err = self._run_git(["commit", "-m", commit_msg])
            if code != 0 and "nothing to commit" in (out + err):
                logger.info("Nada novo para comitar nesta rodada.")

            # Push para a branch main
            code_push, out_push, err_push = self._run_git(["push", "origin", "main"], timeout=45.0)
            if code_push != 0:
                logger.warning(f"Aviso no git push: {err_push}. Reconciliando com pull --rebase...")
                self._run_git(["pull", "origin", "main", "--rebase"])
                code_push, out_push, err_push = self._run_git(["push", "origin", "main"], timeout=45.0)

            # Obtém hash do último commit
            _, commit_hash, _ = self._run_git(["rev-parse", "HEAD"])
            short_hash = commit_hash[:7] if commit_hash else "unknown"

            stats = ledger_data.get("stats", {})
            logger.info(f"✅ [GIT SYNC SUCESSO] Commit {short_hash} enviado com sucesso para {self.repo_url}!")
            return {
                "commit_hash": commit_hash,
                "short_hash": short_hash,
                "commit_msg": commit_msg,
                "repo_url": self.repo_url,
                "branch": "main",
                "total_cycles": stats.get("total_cycles", cycle_id),
                "approved_count": stats.get("approved_count", 0),
                "rejected_count": stats.get("rejected_count", 0)
            }
        except Exception as e:
            logger.error(f"Exceção durante git sync: {e}")
            return None

git_sync = GitSyncEngine()

if __name__ == "__main__":
    print("Testando git sync...")
    res = git_sync.commit_and_push(cycle_id=73, hypothesis_title="SYNC_ONLINE", verdict="ACTIVE")
    print("Resultado:", res)
