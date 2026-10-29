import time
import logging
from typing import Dict, Any, List
from collective.graph_engine import knowledge_graph
from collective.agent_pool import agent_pool
from collective.inference_scheduler import inference_scheduler
from collective.gds_engine import gds_engine
from collective.generation_cycle import generation_engine
from discord_bridge import discord_bridge

logger = logging.getLogger("research_duel.collective.observability")

class CollectiveObservability:
    """
    Observabilidade e Telemetria da Inteligência Coletiva (Fase 13).
    Gera snapshots executivos, relatórios de estado e cards para o Discord.
    """
    def collect_metrics_snapshot(self) -> Dict[str, Any]:
        graph_stats = knowledge_graph.count_stats()
        agent_stats = agent_pool.get_stats()
        sched_stats = inference_scheduler.get_stats()
        gds_stats = gds_engine.run_full_analysis()

        return {
            "timestamp": time.time(),
            "generation_current": generation_engine.generation_counter,
            "graph": {
                "total_nodes": graph_stats.get("total_nodes", 0),
                "total_edges": graph_stats.get("total_edges", 0),
                "hypotheses_proposed": graph_stats.get("hypotheses_proposed", 0),
                "hypotheses_verified": graph_stats.get("hypotheses_verified", 0),
                "hypotheses_refuted": graph_stats.get("hypotheses_refuted", 0),
                "contradictions_open": graph_stats.get("contradictions_open", 0),
                "communities_detected": gds_stats.get("communities_count", 0)
            },
            "agents": {
                "logical_pool_total": agent_stats.get("total_logical_agents", 0),
                "max_logical_pool": agent_stats.get("max_logical_pool", 0),
                "active_limit": agent_stats.get("active_limit", 0),
                "status_breakdown": agent_stats.get("by_status", {})
            },
            "inference": {
                "total_calls": sched_stats.get("total_calls_made", 0),
                "total_tokens": sched_stats.get("total_tokens_used", 0),
                "total_failures": sched_stats.get("total_failures", 0),
                "cached_items": sched_stats.get("cached_items_count", 0)
            }
        }

    def publish_discord_observability_card(self) -> bool:
        snap = self.collect_metrics_snapshot()
        g = snap["graph"]
        a = snap["agents"]
        inf = snap["inference"]

        embed = {
            "title": "🧠 INTELIGÊNCIA COLETIVA ADAPTATIVA — TELEMETRIA",
            "description": (
                f"**Geração Ativa:** `#{snap['generation_current']}` • **Arquitetura:** Multiagente Hierárquica\n"
                f"Grafo de Conhecimento persistente com três dimensões de pesos ($W_s, W_e, W_o$)."
            ),
            "color": 0x7289DA, # Blurple
            "fields": [
                {
                    "name": "🌐 Grafo de Conhecimento (Neo4j / Embedded)",
                    "value": (
                        f"• **Nós Totais:** `{g['total_nodes']}`\n"
                        f"• **Arestas Ponderadas:** `{g['total_edges']}`\n"
                        f"• **Comunidades (Leiden):** `{g['communities_detected']}`\n"
                        f"• **Contradições Abertas:** `⚠️ {g['contradictions_open']}`"
                    ),
                    "inline": True
                },
                {
                    "name": "📊 Status Epistêmico de Hipóteses",
                    "value": (
                        f"• **Propostas:** `{g['hypotheses_proposed']}`\n"
                        f"• **Verificadas:** `🏆 {g['hypotheses_verified']}`\n"
                        f"• **Refutadas:** `❌ {g['hypotheses_refuted']}`"
                    ),
                    "inline": True
                },
                {
                    "name": "🤖 Pool de Agentes Lógicos & Concorrência",
                    "value": (
                        f"• **Pool Lógico:** `{a['logical_pool_total']} agentes` (Expansível até `{a['max_logical_pool']}`)\n"
                        f"• **Limite Ativo Simultâneo:** `{a['active_limit']}`\n"
                        f"• **Inferências Realizadas:** `{inf['total_calls']}` | **Tokens:** `{inf['total_tokens']:,}`\n"
                        f"• **Falhas / Retries:** `{inf['total_failures']}`"
                    ),
                    "inline": False
                }
            ],
            "footer": {
                "text": "LLM_PROJECT Collective Intelligence Engine • RTX 3060 12GB"
            }
        }
        return discord_bridge.send_embed(embed, content="📡 **[TELEMETRIA DO GRAFO COLETIVO]** Snapshot Atualizado")

observability = CollectiveObservability()
