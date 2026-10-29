import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = BASE_DIR.parent
PROXY_DIR = WORKSPACE_ROOT / "PROXY-REVERSA"

# Proxy Reversa Xiaomi
MIMO_API_BASE = os.getenv("MIMO_API_BASE", "http://127.0.0.1:8088/v1")
MODEL_A_ID = "mimo-v2.6-pro-ultraspeed"
MODEL_B_ID = "mimo-v2.6-pro"

# Credenciais Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID", "1561523208509853756")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID", "1559222768778874932")

discord_bot_path = PROXY_DIR / "discord_bot.py"
if discord_bot_path.exists():
    try:
        content = discord_bot_path.read_text(encoding="utf-8")
        if not DISCORD_TOKEN:
            m_tok = re.search(r'DISCORD_TOKEN\s*=\s*os\.getenv\(\s*["\']DISCORD_TOKEN["\'],\s*["\']([^"\']+)["\']', content)
            if m_tok:
                DISCORD_TOKEN = m_tok.group(1)
        if not DISCORD_CHANNEL_ID:
            m_chan = re.search(r'CHANNEL_ID\s*=\s*(\d+)', content)
            if m_chan:
                DISCORD_CHANNEL_ID = m_chan.group(1)
        if not DISCORD_GUILD_ID:
            m_guild = re.search(r'GUILD_ID\s*=\s*(\d+)', content)
            if m_guild:
                DISCORD_GUILD_ID = m_guild.group(1)
    except Exception:
        pass

# Diretórios
EXPERIMENTS_DIR = BASE_DIR / "experiments"
RESULTS_DIR = BASE_DIR / "results"
LOGS_DIR = BASE_DIR / "logs"
DB_PATH = BASE_DIR / "research_state.db"

# FOCO DE PESQUISA: MODELO GPT LOCAL (~3B) NA RTX 3060 12GB
# OBJETIVO: REDUZIR PODER DE COMPUTAÇÃO, CORTAR FLOPS, MAXIMIZAR TOKENS/S SEM QUANTIZAÇÃO CONVENCIONAL
RESEARCH_MISSION = "GPT_3B_COMPUTATION_FLOPS_REDUCTION_NO_QUANT"
TARGET_MODEL_NAME = "GPT Local (~3B Testbed)"
LOCAL_BENCH_GPT = WORKSPACE_ROOT / "branchman" / "models" / "gpt2"

EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
