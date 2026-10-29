path = r"E:\AI_MODELS\PROXY-REVERSA\mimo_client.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

old_block = """                            if response.status_code == 429:
                                backoff = min(1.5 * attempt, 5.0)
                                logger.warning(f"⚠️ [429] Rate limit — rotando conta ({backoff:.1f}s), fastchat fixo")
                                # se pool pequeno, tenta garantir mais contas em background
                                if self.session_manager.healthy_count() <= 1:
                                    self.session_manager._kick_refill("rate_limit")
                                if attempt < config.MAX_RETRIES:
                                    await asyncio.sleep(backoff)
                                    # rotaciona se houver outra conta livre
                                    if len(self.session_manager.sessions) > 1:
                                        current_sess, _ = await self.session_manager.acquire_session()
                                        token = self.session_manager.get_token(current_sess)
                                        headers = self._build_headers(current_sess)
                                    continue"""

new_block = """                            if response.status_code == 429:
                                err_bytes = await response.aread()
                                err_str = err_bytes.decode('utf-8', errors='ignore')
                                is_daily_quota = ("4005" in err_str or "上限" in err_str or "次日" in err_str)
                                
                                if is_daily_quota:
                                    logger.error("🛑 [HTTP 429 - COTA DIÁRIA 4005 ESGOTADA] Conta atingiu limite de requisições diárias.")
                                    # Marca cooldown de 24h para esta conta
                                    self.session_manager.mark_session_cooldown(current_sess, duration_seconds=86400.0)
                                else:
                                    backoff = min(1.5 * attempt, 5.0)
                                    logger.warning(f"⚠️ [429] Rate limit temporário — rotando conta ({backoff:.1f}s), fastchat fixo")
                                    await asyncio.sleep(backoff)

                                if len(self.session_manager.sessions) > 1:
                                    logger.info("Rotacionando para próxima conta ativa do pool...")
                                    current_sess, _ = await self.session_manager.acquire_session()
                                    token = self.session_manager.get_token(current_sess)
                                    headers = self._build_headers(current_sess)
                                    url = f"{config.MIMO_BASE_URL}{endpoint}?xiaomichatbot_ph={urllib.parse.quote(token)}"
                                    if attempt < config.MAX_RETRIES:
                                        continue

                                # Se o pool ficou sem contas válidas, aciona ensure_session síncrono
                                from auto_refill import auto_refill
                                logger.warning("Pool sem alternativas viáveis — executando ensure_session síncrono...")
                                ok = await auto_refill.ensure_session("quota_429")
                                if ok:
                                    await self.session_manager.renew_session()
                                    current_sess, _ = await self.session_manager.acquire_session()
                                    token = self.session_manager.get_token(current_sess)
                                    if token and attempt < config.MAX_RETRIES:
                                        url = f"{config.MIMO_BASE_URL}{endpoint}?xiaomichatbot_ph={urllib.parse.quote(token)}"
                                        headers = self._build_headers(current_sess)
                                        continue
                                raise RuntimeError(f"Cota diária MiMo esgotada (HTTP 429). Auto-refill não conseguiu nova conta ativa.")"""

if old_block.replace("\r\n", "\n") in code.replace("\r\n", "\n"):
    code = code.replace("\r\n", "\n").replace(old_block.replace("\r\n", "\n"), new_block.replace("\r\n", "\n"))
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    print("mimo_client.py patched successfully!")
else:
    print("Could not find exact block in mimo_client.py")
