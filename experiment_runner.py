import time
import json
import logging
from typing import Dict, Any
from benchmark import benchmark_engine
from persistence import persistence
from discord_bridge import discord_bridge

logger = logging.getLogger("research_duel.experiment_runner")

class ExperimentRunner:
    def run_experiment(self, cycle_id: int, exp_spec: Dict[str, Any]) -> Dict[str, Any]:
        exp_name = exp_spec.get("name", f"EXP_CYCLE_{cycle_id}")
        mode = exp_spec.get("mode", "pca_static")
        rank_r = exp_spec.get("rank_r", 128)
        top_k = exp_spec.get("top_k", 2000)
        margin_tau = exp_spec.get("margin_tau", 1.2)
        k_small = exp_spec.get("k_small", 250)
        k_large = exp_spec.get("k_large", 2000)
        cos_cache_thresh = exp_spec.get("cos_cache_thresh", 0.95)

        sparsity_ratio = float(exp_spec.get("sparsity_ratio", 0.12))
        logger.info(f"Disparando benchmark em GPU: modo={mode}, sparsity_ratio={sparsity_ratio}")
        t0 = time.time()
        try:
            results = benchmark_engine.run_benchmark(
                mode=mode,
                sparsity_ratio=sparsity_ratio,
                rank_r=rank_r,
                top_k=top_k,
                margin_tau=margin_tau,
                k_small=k_small,
                k_large=k_large,
                cos_cache_thresh=cos_cache_thresh
            )
            duration = time.time() - t0

            # Registrar no SQLite
            metrics_summary = {
                "code_hash": results["code_hash"],
                "baseline_metric": results["baseline_tokens_per_sec"],
                "optimized_metric": results["optimized_tokens_per_sec"],
                "flops_reduction_pct": results["flops_reduction_pct"],
                "top1_accuracy": results["top1_accuracy"],
                "latency_ms": results["latency_ms"],
                "vram_mb": results["vram_mb"],
                "tokens_per_sec": results["optimized_tokens_per_sec"]
            }
            persistence.record_experiment(
                cycle_id=cycle_id,
                experiment_name=exp_name,
                metrics=metrics_summary,
                raw_results=results
            )

            # Telemetria periódica
            stats = persistence.get_summary_stats()
            telemetry_data = {
                "cycle_id": cycle_id,
                "active_hypothesis": exp_spec.get("hypothesis_title", "N/A"),
                "current_experiment": exp_name,
                "tokens_per_sec": results["optimized_tokens_per_sec"],
                "vram_used_mb": results["vram_mb"],
                "latency_ms": results["latency_ms"],
                "flops_reduction_pct": results["flops_reduction_pct"],
                "top1_accuracy_pct": results["top1_accuracy"],
                "approved_count": stats.get("approved_count", 0),
                "rejected_count": stats.get("rejected_count", 0),
                "next_action": "Debate Pós-Experimento & Veredito Final"
            }
            discord_bridge.publish_telemetry(telemetry_data)

            return {"success": True, "results": results}
        except Exception as e:
            logger.error(f"Erro executando experimento: {e}")
            return {"success": False, "error": str(e), "results": {"pass_criteria": False}}

experiment_runner = ExperimentRunner()
