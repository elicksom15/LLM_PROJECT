import time
import json
import logging
from typing import Optional, Dict, Any, List
import httpx
from config import DISCORD_TOKEN, DISCORD_CHANNEL_ID

logger = logging.getLogger("research_duel.discord")

def make_bar(pct: float, length: int = 10) -> str:
    """Gera barra de progresso ASCII estilizada: [`████████░░`] 80.0%"""
    pct = max(0.0, min(100.0, float(pct)))
    filled = int(round(length * (pct / 100.0)))
    filled = max(0, min(length, filled))
    empty = length - filled
    return f"[`{'█' * filled}{'░' * empty}`] **{pct:.1f}%**"

class DiscordBridge:
    def __init__(self, token: Optional[str] = None, channel_id: Optional[str] = None):
        self.token = token or DISCORD_TOKEN
        self.channel_id = str(channel_id or DISCORD_CHANNEL_ID)
        self.base_url = "https://discord.com/api/v10"
        self.enabled = bool(self.token and self.channel_id)
        if not self.enabled:
            logger.warning("DiscordBridge desativado: token ou channel_id não configurados.")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "DualMiMoResearchEngine/2.0"
        }

    def send_embed(self, embed: Dict[str, Any], content: Optional[str] = None) -> bool:
        """Envia um Discord Rich Embed formatado diretamente via REST API acompanhado de texto."""
        if not self.enabled:
            print(f"[DISCORD OFFLINE EMBED] {embed.get('title')}")
            return False

        payload: Dict[str, Any] = {"embeds": [embed]}
        if content:
            payload["content"] = content

        for attempt in range(3):
            try:
                with httpx.Client(timeout=12.0) as client:
                    r = client.post(
                        f"{self.base_url}/channels/{self.channel_id}/messages",
                        headers=self._headers(),
                        json=payload
                    )
                    if r.status_code in (200, 201):
                        return True
                    elif r.status_code == 429:
                        retry_after = r.json().get("retry_after", 2.0)
                        logger.warning(f"Discord 429 Rate-limit: aguardando {retry_after}s")
                        time.sleep(retry_after)
                    else:
                        logger.error(f"Erro Discord Embed ({r.status_code}): {r.text[:200]}")
                        time.sleep(1.0)
            except Exception as ex:
                logger.error(f"Exceção enviando Discord Embed: {ex}")
                time.sleep(1.5)
        return False

    def send_raw_message(self, content: str) -> bool:
        if not self.enabled:
            print(f"[DISCORD OFFLINE] {content[:100]}...")
            return False

        chunks = []
        while len(content) > 1950:
            split_idx = content.rfind("\n", 0, 1950)
            if split_idx == -1:
                split_idx = 1950
            chunks.append(content[:split_idx])
            content = content[split_idx:].lstrip()
        if content:
            chunks.append(content)

        success = True
        for chunk in chunks:
            payload = {"content": chunk}
            for attempt in range(3):
                try:
                    with httpx.Client(timeout=10.0) as client:
                        r = client.post(
                            f"{self.base_url}/channels/{self.channel_id}/messages",
                            headers=self._headers(),
                            json=payload
                        )
                        if r.status_code in (200, 201):
                            break
                        elif r.status_code == 429:
                            retry_after = r.json().get("retry_after", 2.0)
                            time.sleep(retry_after)
                        else:
                            logger.error(f"Erro Discord ({r.status_code}): {r.text[:200]}")
                            time.sleep(1.0)
                except Exception as ex:
                    logger.error(f"Exceção enviando mensagem Discord: {ex}")
                    time.sleep(1.5)
            else:
                success = False
        return success

    # =========================================================================
    # CARDS VISUAIS DE TELEMETRIA CIENTÍFICA
    # =========================================================================

    def publish_investigation_card(
        self,
        cycle_id: int,
        hypothesis: Dict[str, Any],
        arg_a: str,
        arg_b: str
    ) -> bool:
        """Rodada 1: Formulações Independentes de Redução de Computação."""
        embed = {
            "title": f"🔬 RESEARCH CYCLE #{cycle_id} — INVESTIGAÇÃO INDEPENDENTE",
            "description": (
                f"**Bancada:** Modelo GPT (~3B) • **Alvo:** Reduzir FLOPs e elevar Tokens/s sem quantização\n"
                f"**Hipótese:** `{hypothesis.get('title', 'N/A')}`\n{hypothesis.get('description', '')}"
            ),
            "color": 0x3498DB,  # Azul científico
            "fields": [
                {
                    "name": "⚡ MiMo-V2.6-Pro-UltraSpeed (Pesquisador A)",
                    "value": (arg_a[:950] + "...") if len(arg_a) > 950 else arg_a,
                    "inline": False
                },
                {
                    "name": "🛡️ MiMo-V2.6-Pro (Pesquisador B)",
                    "value": (arg_b[:950] + "...") if len(arg_b) > 950 else arg_b,
                    "inline": False
                }
            ],
            "footer": {
                "text": f"Dual MiMo Research Engine • RTX 3060 12GB • Ciclo #{cycle_id}"
            }
        }
        content_msg = f"⚡ **[PESQUISA GPT ~3B]** 🔬 Ciclo #{cycle_id} — Rodada 1: Investigação Independente iniciada"
        return self.send_embed(embed, content=content_msg)

    def publish_confrontation_card(
        self,
        cycle_id: int,
        hypothesis: Dict[str, Any],
        crit_a: str,
        crit_b: str
    ) -> bool:
        """Rodada 2: Confronto Adversarial & Críticas."""
        embed = {
            "title": f"⚔️ RESEARCH CYCLE #{cycle_id} — DEBATE & CONFRONTO ADVERSARIAL",
            "description": f"Auditoria de redução de complexidade de FLOPs e limites físicos de hardware.",
            "color": 0x9B59B6,  # Roxo adversarial
            "fields": [
                {
                    "name": "🔍 MiMo Pro ➔ UltraSpeed (Auditoria de Overheads)",
                    "value": (crit_b[:950] + "...") if len(crit_b) > 950 else crit_b,
                    "inline": False
                },
                {
                    "name": "💡 UltraSpeed ➔ Pro (Réplica & Compensação)",
                    "value": (crit_a[:950] + "...") if len(crit_a) > 950 else crit_a,
                    "inline": False
                }
            ],
            "footer": {
                "text": f"Dual MiMo Debate Rigoroso • SQLite Persistent • Ciclo #{cycle_id}"
            }
        }
        content_msg = f"⚡ **[PESQUISA GPT ~3B]** ⚔️ Ciclo #{cycle_id} — Rodada 2: Confronto Adversarial & Críticas"
        return self.send_embed(embed, content=content_msg)

    def publish_specification_card(
        self,
        cycle_id: int,
        hypothesis: Dict[str, Any],
        spec: Dict[str, Any]
    ) -> bool:
        """Rodada 3: Especificação Experimental Formalizada."""
        embed = {
            "title": f"📋 RESEARCH CYCLE #{cycle_id} — ESPECIFICAÇÃO DO EXPERIMENTO",
            "description": f"Consenso científico formalizado para execução na bancada GPT (~3B).",
            "color": 0xE67E22,  # Âmbar / Laranja
            "fields": [
                {
                    "name": "🎯 Ensaio",
                    "value": f"`{spec.get('name', 'EXP')}`",
                    "inline": True
                },
                {
                    "name": "⚙️ Parâmetros Algorítmicos",
                    "value": (
                        f"• **Rank PCA (r):** `{spec.get('rank_r', 128)}`\n"
                        f"• **Top-K:** `{spec.get('top_k', 2000)}`\n"
                        f"• **Limiar Margem:** `{spec.get('margin_tau', 1.2)}`"
                    ),
                    "inline": True
                },
                {
                    "name": "📊 Metas de Validação",
                    "value": (
                        f"• **Aprovação:** `{spec.get('pass_criteria', 'top1 >= 98.0%')}`\n"
                        f"• **Falsificação:** `{spec.get('falsification_criteria', 'top1 < 98.0% ou sem ganho')}`"
                    ),
                    "inline": False
                }
            ],
            "footer": {
                "text": f"Bancada: GPT Local (~3B) • RTX 3060 12GB • Ciclo #{cycle_id}"
            }
        }
        content_msg = f"⚡ **[PESQUISA GPT ~3B]** 📋 Ciclo #{cycle_id} — Rodada 3: Especificação Experimental Definida"
        return self.send_embed(embed, content=content_msg)

    def publish_experiment_card(
        self,
        cycle_id: int,
        hypothesis: Dict[str, Any],
        spec: Dict[str, Any],
        results: Dict[str, Any],
        verdict: str,
        eval_summary: str
    ) -> bool:
        """Rodada 4: Resultados Reais Medidos na GPU e Veredito."""
        is_approved = (verdict == "APPROVED")
        color = 0x2ECC71 if is_approved else 0xE74C3C
        verdict_badge = "✅ HIPÓTESE APROVADA" if is_approved else "❌ HIPÓTESE FALSIFICADA / REJEITADA"

        top1 = results.get("top1_accuracy", 0.0)
        flops_red = results.get("flops_reduction_pct", 0.0)
        base_tok = results.get("baseline_tokens_per_sec", 0.0)
        opt_tok = results.get("optimized_tokens_per_sec", 0.0)
        speedup = results.get("speedup_pct", 0.0)
        vram_mb = results.get("vram_mb", 0)
        vram_pct = (vram_mb / 12288.0) * 100.0

        embed = {
            "title": f"🚀 RESEARCH CYCLE #{cycle_id} — BANCADA GPT (~3B) EM GPU",
            "description": (
                f"**Alvo:** Reduzir Poder de Computação & FLOPs sem Quantização Convencional\n"
                f"**Status:** {verdict_badge}\n"
                f"**Hipótese:** `{hypothesis.get('title', 'N/A')}`"
            ),
            "color": color,
            "fields": [
                {
                    "name": "📉 Redução de FLOPs e Computação",
                    "value": f"{make_bar(flops_red, length=12)}\n*Economia computacional direta*",
                    "inline": True
                },
                {
                    "name": "🎯 Acurácia Top-1 Argmax",
                    "value": f"{make_bar(top1, length=12)}\n*Preservação da saída do modelo*",
                    "inline": True
                },
                {
                    "name": "⚡ Throughput de Inferência (Tokens/s)",
                    "value": f"```yaml\nBaseline:  {base_tok:.1f} tok/s\nOtimizado: {opt_tok:.1f} tok/s ({speedup:+.1f}%)\nLatência:  {results.get('latency_ms', 0.0):.2f} ms/token\n```",
                    "inline": False
                },
                {
                    "name": "💾 VRAM & Fidelidade Probabilística",
                    "value": (
                        f"• **Divergência KL:** `{results.get('kl_divergence', 0.0):.6f}`\n"
                        f"• **Similaridade Cosseno:** `{results.get('cosine_similarity', 0.0):.6f}`\n"
                        f"• **VRAM Pico:** {make_bar(vram_pct, length=8)} `{vram_mb} MB / 12,288 MB`\n"
                        f"• **Pesos:** Precisão Completa *(Sem Quantização Convencional)*"
                    ),
                    "inline": False
                },
                {
                    "name": "⚖️ Síntese dos Agentes Pesquisadores",
                    "value": (eval_summary[:950] + "...") if len(eval_summary) > 950 else eval_summary,
                    "inline": False
                }
            ],
            "footer": {
                "text": f"Bancada GPT (~3B) • RTX 3060 12GB • Hash: {results.get('code_hash', 'N/A')}"
            }
        }
        content_msg = f"⚡ **[PESQUISA GPT ~3B]** 🚀 Ciclo #{cycle_id} — Resultados na RTX 3060 ({verdict_badge})"
        return self.send_embed(embed, content=content_msg)

    def publish_cycle_event(
        self,
        cycle_num: int,
        agent: str,
        event_type: str,
        objective: str,
        argument: str,
        evidence: str,
        counterpoint: str = "N/A",
        action: str = "N/A",
        result: str = "N/A",
        next_step: str = "N/A"
    ) -> bool:
        color_map = {
            "HIPÓTESE": 0x3498DB,
            "CRÍTICA": 0x9B59B6,
            "EXPERIMENTO": 0xE67E22,
            "RESULTADO": 0x2ECC71,
            "FALHA": 0xE74C3C
        }
        color = color_map.get(event_type.upper(), 0x7289DA)

        fields = [
            {"name": "🎯 Objetivo", "value": objective[:1000], "inline": False},
            {"name": "🧠 Argumento / Ação", "value": argument[:1000], "inline": False}
        ]
        if counterpoint != "N/A":
            fields.append({"name": "🛡️ Contraponto Adversarial", "value": counterpoint[:1000], "inline": False})
        if result != "N/A":
            fields.append({"name": "📊 Resultado", "value": result[:1000], "inline": True})
        if next_step != "N/A":
            fields.append({"name": "⏩ Próximo Passo", "value": next_step[:1000], "inline": True})

        embed = {
            "title": f"📡 [CYCLE #{cycle_num}] {event_type.upper()} — {agent}",
            "color": color,
            "fields": fields,
            "footer": {"text": "Dual MiMo Autonomous Research Engine • RTX 3060 12GB"}
        }
        return self.send_embed(embed)

    def publish_telemetry(self, stats: Dict[str, Any]) -> bool:
        cycle_id = stats.get('cycle_id', 1)
        top1 = stats.get('top1_accuracy_pct', 0.0)
        flops = stats.get('flops_reduction_pct', 0.0)
        vram_mb = stats.get('vram_used_mb', 0)
        vram_pct = (vram_mb / 12288.0) * 100.0

        embed = {
            "title": "📊 TELEMETRIA CIENTÍFICA EM TEMPO REAL",
            "description": (
                f"**Ciclo Atual:** `#{cycle_id}` | "
                f"**Hipótese Ativa:** `{stats.get('active_hypothesis', 'N/A')}`\n"
                f"**Bancada:** Modelo GPT Local (~3B) • **Objetivo:** Reduzir FLOPs sem quantizar"
            ),
            "color": 0x1ABC9C,
            "fields": [
                {
                    "name": "🎯 Qualidade Top-1 Argmax",
                    "value": make_bar(top1, length=10),
                    "inline": True
                },
                {
                    "name": "📉 Redução de FLOPs",
                    "value": make_bar(flops, length=10),
                    "inline": True
                },
                {
                    "name": "💾 VRAM Utilizada",
                    "value": f"{make_bar(vram_pct, length=8)} `{vram_mb} MB / 12,288 MB`",
                    "inline": False
                },
                {
                    "name": "⚡ Throughput & Latência",
                    "value": f"`{stats.get('tokens_per_sec', 0.0):.1f} tok/s` | `{stats.get('latency_ms', 0.0):.2f} ms/tok`",
                    "inline": True
                },
                {
                    "name": "🏆 Placar de Hipóteses",
                    "value": f"Aprovadas: **{stats.get('approved_count', 0)}** | Rejeitadas: **{stats.get('rejected_count', 0)}**",
                    "inline": True
                },
                {
                    "name": "⏩ Próxima Ação",
                    "value": f"{stats.get('next_action', 'Aguardando próximo debate')}",
                    "inline": False
                }
            ],
            "footer": {
                "text": "Bancada GPT (~3B) • RTX 3060 12GB • Sem Quantização Convencional"
            }
        }
        content_msg = f"📊 **[TELEMETRIA TEMPO REAL]** Ciclo #{cycle_id} — Bancada GPT (~3B)"
        return self.send_embed(embed, content=content_msg)

    def publish_analytical_gate_card(
        self,
        cycle_id: int,
        hypothesis: Dict[str, Any],
        audit: Dict[str, Any]
    ) -> bool:
        """Publica o Card da Fase 0: Auditoria Matemática Prévia (Cálculo Primeiro, GPU Depois)."""
        passed = audit.get("passed_math_gate", False)
        status_color = 0x2ECC71 if passed else 0xE74C3C  # Verde se passou, Vermelho se rejeitado no papel
        verdict_icon = "🟢" if passed else "🔴"
        verdict_str = "**APROVADO NO CÁLCULO — LIBERADO PARA GPU**" if passed else "**REJEITADO NO CÁLCULO — DESCARTADO SEM GASTO DE GPU**"

        flops_pct = audit.get("flops_reduction_pct", 0.0)
        speedup = audit.get("theoretical_speedup", 1.0)

        embed = {
            "title": f"🧮 RESEARCH CYCLE #{cycle_id} — FASE 0: AUDITORIA MATEMÁTICA",
            "description": (
                f"**Hipótese:** `{hypothesis.get('title', 'N/A')}`\n"
                f"**Alvo Analítico:** `{audit.get('target_scope', 'N/A')}`\n"
                f"**Diretriz:** Calcular viabilidade matemática antes de acionar a RTX 3060."
            ),
            "color": status_color,
            "fields": [
                {
                    "name": "📐 Formulação Matemática do Operador",
                    "value": f"`{audit.get('math_formula', 'N/A')}`",
                    "inline": False
                },
                {
                    "name": "📉 Redução Teórica de FLOPs",
                    "value": f"{make_bar(flops_pct, length=10)}\nTeórico: `{audit.get('flops_proposed', 0):,} FLOPs` (vs `{audit.get('flops_baseline', 0):,} FLOPs`)",
                    "inline": True
                },
                {
                    "name": "⚡ Aceleração Teórica Projetada",
                    "value": f"`{speedup:.2f}x` teóricos\nMeta Mínima: `4.00x` (75% corte)",
                    "inline": True
                },
                {
                    "name": "📊 Complexidade Assintótica",
                    "value": f"• Baseline: `{audit.get('complexity_baseline', 'N/A')}`\n• Proposta: `{audit.get('complexity_proposed', 'N/A')}`",
                    "inline": False
                },
                {
                    "name": f"{verdict_icon} Veredito Matemático (Fase 0)",
                    "value": (
                        f"{verdict_str}\n"
                        f"{audit.get('rejection_reason', 'Hipótese comprovou corte matemático >= 75% no papel e prossegue para teste físico.')}"
                    ),
                    "inline": False
                }
            ],
            "footer": {
                "text": "Dual MiMo Research Engine • Fase 0: Cálculo Primeiro, GPU Depois • RTX 3060 12GB"
            }
        }
        content_msg = f"🧮 **[FASE 0 — CÁLCULO PRIMEIRO]** Ciclo #{cycle_id}: {verdict_str}"
        return self.send_embed(embed, content=content_msg)


    def publish_git_sync_card(
        self,
        cycle_id: int,
        commit_info: Dict[str, Any]
    ) -> bool:
        """Publica Card Executivo anunciando commit e sincronização contínua com o GitHub."""
        short_hash = commit_info.get("short_hash", "HEAD")
        commit_hash = commit_info.get("commit_hash", "")
        commit_msg = commit_info.get("commit_msg", "Research Sync")
        repo_url = commit_info.get("repo_url", "https://github.com/elicksom15/LLM_PROJECT.git").rstrip(".git")
        branch = commit_info.get("branch", "main")
        total_cycles = commit_info.get("total_cycles", cycle_id)
        approved_count = commit_info.get("approved_count", 0)

        commit_link = f"[{short_hash}]({repo_url}/commit/{commit_hash})" if commit_hash else f"`{short_hash}`"
        state_link = f"[STATE.md (Ledger Completo)]({repo_url}/blob/{branch}/STATE.md)"
        ledger_link = f"[ledger.json (Dados Brutos)]({repo_url}/blob/{branch}/ledger.json)"
        readme_link = f"[README Executivo]({repo_url}/blob/{branch}/README.md)"

        embed = {
            "title": f"📦 GITHUB SINCRONIZADO — COMMIT [{short_hash}]",
            "url": f"{repo_url}/commit/{commit_hash}" if commit_hash else repo_url,
            "description": (
                f"**Repositório Oficial:** [`elicksom15/LLM_PROJECT`]({repo_url})\n"
                f"**Branch Ativa:** `{branch}` • **Sincronização:** Automática e Contínua (24/7)\n"
                f"Todo o estado dos ensaios, hipóteses e ledger foram enviados para a nuvem."
            ),
            "color": 0x24292E,  # GitHub Dark / Octocat
            "fields": [
                {
                    "name": "📌 Commit & Identificação",
                    "value": f"• **Hash:** {commit_link}\n• **Mensagem:** `{commit_msg}`",
                    "inline": False
                },
                {
                    "name": "📊 Painel de Ciclos Sincronizados",
                    "value": (
                        f"• **Ciclo Concluído:** `#{cycle_id}`\n"
                        f"• **Total de Ciclos no Ledger:** `{total_cycles}`\n"
                        f"• **Hipóteses Aprovadas:** `🏆 {approved_count}`"
                    ),
                    "inline": True
                },
                {
                    "name": "🌐 Navegação e Documentação",
                    "value": (
                        f"• 📜 {state_link}\n"
                        f"• 🗄️ {ledger_link}\n"
                        f"• 📘 {readme_link}"
                    ),
                    "inline": True
                }
            ],
            "footer": {
                "text": "Dual MiMo Research Engine • GitHub Continuous Delivery • RTX 3060 12GB"
            }
        }
        content_msg = f"🚀 **[GITHUB SYNC]** Novo commit enviado com sucesso: {commit_link} (`{commit_msg}`)"
        return self.send_embed(embed, content=content_msg)


    def publish_collective_swarm_card(
        self,
        cycle_id: int,
        generation_num: int,
        hypothesis_title: str,
        verdict: str,
        active_agents: list,
        graph_stats: dict,
        audit_res: dict = None,
        bench_res: dict = None,
        commit_info: dict = None
    ) -> bool:
        """Publica Card Executivo Completo da Rede Multiagente Hierárquica Orientada por Grafos."""
        is_approved = (verdict == "APPROVED")
        status_color = 0x2ECC71 if is_approved else (0xF39C12 if "ANALYTICAL" in verdict else 0xE74C3C)
        status_icon = "🟢" if is_approved else ("🛑" if "ANALYTICAL" in verdict else "🔴")

        agent_lines = []
        role_icons = {
            "orchestrator": "👑", "planner": "📋", "investigator": "📐", "researcher": "🔬",
            "evidence_analyst": "📊", "relation_builder": "🔗", "critic": "🛡️",
            "contradiction_detector": "⚡", "independent_verifier": "⚖️", "synthesizer": "🧪",
            "memory_retriever": "🗄️", "strategy_evaluator": "📈"
        }
        for ag in active_agents[:6]:
            role = ag.get("role", "agent")
            icon = role_icons.get(role, "🤖")
            role_name = role.replace("_", " ").title()
            agent_lines.append(f"{icon} `{ag.get('id', 'N/A')}` — **{role_name}** ({ag.get('status', 'DONE')})")
        if len(active_agents) > 6:
            agent_lines.append(f"*(+ {len(active_agents) - 6} agentes adicionais operando no pool)*")
        agent_block = "\n".join(agent_lines) if agent_lines else "• *Pool de 100 agentes sob orquestração adaptativa*"

        ws = graph_stats.get("avg_ws", 0.85)
        we = graph_stats.get("avg_we", 0.70)
        wo = graph_stats.get("avg_wo", 0.65)
        total_nodes = graph_stats.get("total_nodes", 0)
        total_edges = graph_stats.get("total_edges", 0)
        comms = graph_stats.get("communities_count", 0)
        contras = graph_stats.get("contradictions_open", 0)

        graph_block = (
            f"• **Nós no Grafo:** `{total_nodes}` | **Arestas Ponderadas:** `{total_edges}`\n"
            f"• **Comunidades Leiden:** `{comms}` | **Contradições:** `{contras}`\n"
            f"• **Pesos:** Semântico `$W_s={ws:.2f}$` • Epistêmico `$W_e={we:.2f}$` • Operacional `$W_o={wo:.2f}$`"
        )

        fields = [
            {
                "name": "👥 Equipe Ativa do Pool (100 Agentes Lógicos)",
                "value": agent_block,
                "inline": False
            },
            {
                "name": "🌐 Memória Coletiva (Neo4j / GDS Engine)",
                "value": graph_block,
                "inline": False
            }
        ]

        if audit_res:
            flops_pct = audit_res.get("flops_reduction_pct", 0.0)
            formula = audit_res.get("math_formula", "N/A")
            v_gate = audit_res.get("status", "N/A")
            gate_badge = "🟢 APROVADA NO CÁLCULO" if v_gate == "APPROVED_FOR_GPU" else "🛑 DESCARTADA NA FASE 0"
            fields.append({
                "name": f"🧮 Fase 0: Auditoria Matemática — {gate_badge}",
                "value": (
                    f"• **Fórmula:** `{formula}`\n"
                    f"• **Redução Teórica:** {make_bar(flops_pct, length=8)}\n"
                    f"• **Complexidade:** `{audit_res.get('complexity_proposed', 'N/A')}`\n"
                    f"• **Parecer:** {audit_res.get('rejection_reason') or 'Cálculo matemático auditado e verificado com corte comprovado no papel.'}"
                ),
                "inline": False
            })

        if bench_res:
            top1 = bench_res.get("top1_accuracy", 0.0)
            speedup = bench_res.get("speedup_pct", 0.0)
            tps = bench_res.get("optimized_tokens_per_sec") or bench_res.get("optimized_tps") or bench_res.get("tokens_per_sec", 0.0)
            base_tps = bench_res.get("baseline_tokens_per_sec", 0.0)
            fields.append({
                "name": "💻 Validação Física em Bancada (RTX 3060 12GB)",
                "value": (
                    f"• **Throughput Real:** `{tps:.1f} tokens/s` (Base: `{base_tps:.1f}` | Aceleração: `+{speedup:.1f}%`)\n"
                    f"• **Acurácia Top-1:** `{top1:.2f}%` (Meta: `>= 98.0%`)\n"
                    f"• **Memória VRAM:** `{bench_res.get('vram_mb', 0)} MB` | **Status:** `{verdict}`"
                ),
                "inline": False
            })

        if commit_info:
            short_h = commit_info.get("short_hash", "HEAD")
            repo = commit_info.get("repo_url", "https://github.com/elicksom15/LLM_PROJECT.git").rstrip(".git")
            c_hash = commit_info.get("commit_hash", "")
            c_link = f"[{short_h}]({repo}/commit/{c_hash})" if c_hash else f"`{short_h}`"
            fields.append({
                "name": "📦 Sincronização GitHub",
                "value": f"• **Commit:** {c_link} • **Branch:** `main` • **Ledger:** Sincronizado",
                "inline": False
            })

        embed = {
            "title": f"🧠 [INTELIGÊNCIA COLETIVA] Ciclo #{cycle_id} (Geração #{generation_num}) — {status_icon} {verdict}",
            "description": (
                f"**Bancada & Alvo:** Modelo GPT (~3B) na RTX 3060 12GB sem quantização\n"
                f"*(Alvo Qwen 32B em espera até solução 100% e autorização)*\n"
                f"**Hipótese Central:** `{hypothesis_title}`"
            ),
            "color": status_color,
            "fields": fields,
            "footer": {
                "text": f"Sistema Cognitivo Multiagente • 100 Agentes Lógicos • Bancada GPT-3B • RTX 3060 • Ciclo #{cycle_id}"
            }
        }
        content_msg = f"🧠 **[INTELIGÊNCIA COLETIVA]** Ciclo #{cycle_id} finalizado: {status_icon} `{verdict}` — `{hypothesis_title}`"
        return self.send_embed(embed, content=content_msg)

discord_bridge = DiscordBridge()
