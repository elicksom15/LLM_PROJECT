import sys
import time
import json
from pathlib import Path

BASE_DIR = Path(r"E:\AI_MODELS\PROXY-REVERSA")
sys.path.insert(0, str(BASE_DIR))

from smailpro_client import SmailproClient
from xiaomi_api import XiaomiAPI
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def log(*args):
    print(time.strftime("%H:%M:%S"), "[HARVEST]", *args, flush=True)

def run():
    sp = SmailproClient()
    log("Criando email temporario...")
    email_obj = sp.create_email(domain="outlook.com")
    addr = email_obj.address
    password = "T3st@api9x88"
    log("Email criado:", addr)

    def get_code(em, _sp=sp, _eo=email_obj):
        try:
            return _sp.wait_for_code(_eo, timeout=120)
        except Exception as e:
            log("Erro inbox:", e)
            return None

    x = XiaomiAPI()
    log("Registrando conta via XiaomiAPI...")
    j = x.register_full(addr, password, get_code)
    log("Register result:", j.get("result"))

    plat = x.platform_handshake()
    fp = x.save_account(addr, password, plat)
    log("Salvo em:", fp)

    log("Iniciando Chrome...")
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=opts)

    try:
        url = "https://account.xiaomi.com/pass/serviceLogin?sid=xiaomichatbot&callback=https%3A%2F%2Faistudio.xiaomimimo.com%2Fsts"
        driver.get(url)
        time.sleep(3)

        # Login
        acc = driver.find_element(By.CSS_SELECTOR, "input[name='account']")
        acc.clear()
        acc.send_keys(addr)

        pw = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
        pw.clear()
        pw.send_keys(password)

        for cb in driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"):
            driver.execute_script("arguments[0].click();", cb)
        time.sleep(1)

        btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        driver.execute_script("arguments[0].click();", btn)
        log("Form submetido. Aguardando...")
        time.sleep(5)

        curr_url = driver.current_url or ""
        log("URL atual:", curr_url)

        if "verifyEmail" in curr_url or "identity" in curr_url:
            log("verifyEmail ativo. Clicando Enviar...")
            for b in driver.find_elements(By.TAG_NAME, "button"):
                txt = b.text.lower()
                if "enviar" in txt or "send" in txt:
                    driver.execute_script("arguments[0].click();", b)
                    log("Clicou Enviar!")
                    break

            log("Aguardando codigo no smailpro...")
            code = sp.wait_for_code(email_obj, timeout=120)
            log("Codigo recebido:", code)

            inp = driver.find_element(By.CSS_SELECTOR, "input[name='ticket']")
            inp.clear()
            inp.send_keys(code)
            log("Digitou codigo no input ticket!")
            time.sleep(1)

            # Clica Submit
            for b in driver.find_elements(By.TAG_NAME, "button"):
                if b.text.strip().lower() in ("submit", "confirmar", "avancar", "next"):
                    driver.execute_script("arguments[0].click();", b)
                    log("Clicou Submit!")
                    break
            time.sleep(5)

        log("Navegando para aistudio.xiaomimimo.com...")
        driver.get("https://aistudio.xiaomimimo.com/")
        time.sleep(5)

        cdp = driver.execute_cdp_cmd("Network.getAllCookies", {}) or {}
        raw = cdp.get("cookies") or []
        jar = {c.get("name"): c.get("value", "") for c in raw if c.get("name")}

        log("Cookies encontrados no CDP:")
        for k in sorted(jar.keys()):
            log(f"  {k}: {jar[k][:25]}...")

        ph = jar.get("xiaomichatbot_ph")
        st = jar.get("xiaomichatbot_serviceToken") or jar.get("serviceToken")
        uid = jar.get("userId") or jar.get("cUserId")

        if ph:
            log(f"*** SUCESSO TOTAL! xiaomichatbot_ph = {ph} ***")
            sess = {
                "userId": str(uid),
                "xiaomichatbot_ph": ph,
                "xiaomichatbot_serviceToken": str(st),
                "email": addr,
                "password": password
            }
            # Grava no cookies.json
            cookies_file = BASE_DIR / "cookies.json"
            cookies_file.write_text(json.dumps([sess], indent=2, ensure_ascii=False), encoding="utf-8")
            log("cookies.json ATUALIZADO COM CONTA NOVA E FUNCIONAL!")
            return sess
        else:
            log("ERRO: xiaomichatbot_ph nao apareceu nos cookies CDP.")
            return None
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
