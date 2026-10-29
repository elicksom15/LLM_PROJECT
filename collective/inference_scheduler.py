import time
import hashlib
import logging
import threading
from typing import Dict, Any, List, Optional
from mimo_client import mimo_client
from config import MODEL_A_ID, MODEL_B_ID
from collective.config import collective_config

logger = logging.getLogger("research_duel.collective.scheduler")

class InferenceScheduler:
    """
    Scheduler Centralizado de Inferência com Controle Estrito de Concorrência.
    Permite que centenas de agentes lógicos acessem o pool compartilhado de modelos
    respeitando os limites físicos de taxa, timeouts e orçamento de tokens.
    """
    def __init__(self, max_concurrency: Optional[int] = None):
        self.max_concurrency = max_concurrency or collective_config.agents.inference_concurrency
        self.semaphore = threading.Semaphore(self.max_concurrency)
        self.lock = threading.Lock()
        self.total_tokens_used = 0
        self.total_calls_made = 0
        self.total_failures = 0
        self.response_cache: Dict[str, Dict[str, Any]] = {}

    def _cache_key(self, model_id: str, messages: List[Dict[str, str]], temperature: float) -> str:
        serialized = f"{model_id}|{temperature}|" + "|".join(f"{m.get('role')}:{m.get('content')}" for m in messages)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def dispatch(
        self,
        agent_id: str,
        role: str,
        messages: List[Dict[str, str]],
        preferred_model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        allow_cache: bool = True,
        timeout: float = 120.0
    ) -> Dict[str, Any]:
        """
        Despacha uma requisição de inferência regulada por semáforo de concorrência.
        """
        temp = temperature if temperature is not None else collective_config.agents.default_temperature
        tokens_limit = max_tokens or collective_config.agents.max_tokens_per_call

        # Mapeamento inteligente de modelo por papel do agente
        if not preferred_model:
            if role in ("investigator", "researcher", "relation_builder"):
                preferred_model = MODEL_A_ID  # UltraSpeed (Inovador)
            else:
                preferred_model = MODEL_B_ID  # Pro (Auditor/Crítico)

        cache_k = self._cache_key(preferred_model, messages, temp)
        if allow_cache and cache_k in self.response_cache:
            cached = self.response_cache[cache_k]
            logger.info(f"[Scheduler] Cache hit para {agent_id} ({role})")
            return {
                "success": True,
                "content": cached["content"],
                "model": preferred_model,
                "cached": True,
                "tokens_estimated": cached.get("tokens_estimated", 0),
                "latency_sec": 0.01
            }

        acquired = self.semaphore.acquire(timeout=timeout)
        if not acquired:
            logger.error(f"[Scheduler] Timeout aguardando semáforo de inferência para {agent_id}")
            return {
                "success": False,
                "error": "INFERENCE_SEMAPHORE_TIMEOUT",
                "content": ""
            }

        t0 = time.time()
        try:
            logger.info(f"[Scheduler] Executando inferência para {agent_id} ({role}) via {preferred_model}...")
            res = mimo_client.call_model(
                model_id=preferred_model,
                messages=messages,
                temperature=temp,
                max_tokens=tokens_limit,
                timeout=timeout
            )

            # Fallback seguro para o outro modelo se falhar temporariamente
            if not res.get("success") and res.get("error") != "XIAOMI_DAILY_QUOTA_EXCEEDED":
                fallback_model = MODEL_B_ID if preferred_model == MODEL_A_ID else MODEL_A_ID
                logger.warning(f"[Scheduler] Falha primária em {preferred_model}. Tentando failover em {fallback_model}...")
                res = mimo_client.call_model(
                    model_id=fallback_model,
                    messages=messages,
                    temperature=temp,
                    max_tokens=tokens_limit,
                    timeout=timeout
                )

            latency = time.time() - t0
            content = res.get("content", "").strip()
            est_tokens = int(len(content.split()) * 1.3) + int(sum(len(m.get("content", "").split()) * 1.3 for m in messages))

            with self.lock:
                self.total_calls_made += 1
                if res.get("success"):
                    self.total_tokens_used += est_tokens
                    if allow_cache and content:
                        self.response_cache[cache_k] = {
                            "content": content,
                            "tokens_estimated": est_tokens
                        }
                else:
                    self.total_failures += 1

            return {
                "success": res.get("success", False),
                "content": content,
                "error": res.get("error"),
                "model": res.get("model", preferred_model),
                "cached": False,
                "tokens_estimated": est_tokens,
                "latency_sec": latency
            }
        except Exception as e:
            logger.error(f"[Scheduler] Exceção na inferência de {agent_id}: {e}")
            with self.lock:
                self.total_failures += 1
            return {
                "success": False,
                "error": str(e),
                "content": ""
            }
        finally:
            self.semaphore.release()

    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "max_concurrency": self.max_concurrency,
                "total_calls_made": self.total_calls_made,
                "total_tokens_used": self.total_tokens_used,
                "total_failures": self.total_failures,
                "cached_items_count": len(self.response_cache)
            }

inference_scheduler = InferenceScheduler()
