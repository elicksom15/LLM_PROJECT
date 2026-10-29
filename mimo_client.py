import time
import json
import logging
from typing import Dict, Any, List, Optional
import httpx
from config import MIMO_API_BASE, MODEL_A_ID, MODEL_B_ID

logger = logging.getLogger("research_duel.mimo_client")

class DualMiMoClient:
    def __init__(self, base_url: str = MIMO_API_BASE):
        self.base_url = base_url.rstrip("/")
        self.chat_url = f"{self.base_url}/chat/completions"
        self.models_url = f"{self.base_url}/models"
        self.health_url = f"{self.base_url.replace('/v1', '')}/health"

    def check_health(self) -> Dict[str, Any]:
        try:
            with httpx.Client(timeout=5.0) as client:
                r = client.get(self.health_url)
                return {"status_code": r.status_code, "data": r.json() if r.status_code == 200 else r.text}
        except Exception as e:
            return {"status_code": 0, "error": str(e)}

    def check_models(self) -> List[str]:
        try:
            with httpx.Client(timeout=5.0) as client:
                r = client.get(self.models_url)
                if r.status_code == 200:
                    data = r.json().get("data", [])
                    return [m.get("id") for m in data]
        except Exception as e:
            logger.error(f"Erro consultando /models: {e}")
        return []

    def call_model(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.4,
        max_tokens: int = 2048,
        timeout: float = 120.0
    ) -> Dict[str, Any]:
        """
        Executa requisição estrita ao modelo especificado via streaming acumulado
        para máxima estabilidade e imunidade a travamento de buffers.
        """
        if model_id not in (MODEL_A_ID, MODEL_B_ID):
            raise ValueError(f"Modelo não autorizado: {model_id}. Utilize apenas {MODEL_A_ID} ou {MODEL_B_ID}.")

        # Micro-pausa preventiva para não estourar rate limit da mesma sessão Xiaomi
        time.sleep(2.5)

        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }

        t0 = time.time()
        for attempt in range(4):
            try:
                with httpx.Client(timeout=timeout) as client:
                    with client.stream("POST", self.chat_url, json=payload) as response:
                        if response.status_code == 200:
                            accumulated = []
                            for line in response.iter_lines():
                                if not line:
                                    continue
                                if line.startswith("data: "):
                                    data_str = line[6:].strip()
                                    if data_str == "[DONE]":
                                        break
                                    try:
                                        chunk = json.loads(data_str)
                                        delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                        if delta:
                                            accumulated.append(delta)
                                    except Exception:
                                        pass
                            content = "".join(accumulated).strip()
                            if content:
                                # Detectar erros de cota e rate limit mascarados pelo proxy
                                if "Aviso do MiMo Proxy" in content or "今日请求次数已达上限" in content or "code':4005" in content or "HTTP 429" in content:
                                    logger.error(f"Cota diária da API Xiaomi esgotada (4005/429): {content[:150]}")
                                    return {
                                        "success": False,
                                        "model": model_id,
                                        "error": "XIAOMI_DAILY_QUOTA_EXCEEDED",
                                        "raw_message": content
                                    }

                                return {
                                    "success": True,
                                    "model": model_id,
                                    "content": content,
                                    "latency_sec": time.time() - t0
                                }
                        logger.warning(f"Tentativa {attempt+1} retornou status {response.status_code}. Aguardando retry...")
                        time.sleep(3.0)
            except Exception as ex:
                logger.error(f"Tentativa {attempt+1} falhou com erro: {ex}")
                time.sleep(4.0)

        return {
            "success": False,
            "model": model_id,
            "error": "Falha de streaming após 4 tentativas.",
            "latency_sec": time.time() - t0
        }

mimo_client = DualMiMoClient()
