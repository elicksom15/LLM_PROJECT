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
    print(time.strftime("%H:%M:%S"), "[TEST-REFILL]", *args, flush=True)

def test_full_pipeline():
    log("Iniciando teste de registro e colheita completa...")
    sp = SmailproClient()
    log("Criando email temporario...")
    email_obj = sp.create_email(domain="outlook.com")
    addr = email_obj.address
    password = "T3st@api9x99"
    log("Email criado:", addr)

    def get_code(em, _sp=sp, _eo=email_obj):
        try:
            return _sp.wait_for_code(_eo, timeout=120)
        except Exception as e:
            log("Erro inbox:", e)
            return None

    x = XiaomiAPI()
    log("Executando register_full...")
    j = x.register_full(addr, password, get_code)
    log("register_full result:", j.get("result"), j.get("description", ""))

    plat = x.platform_handshake()
    fp = x.save_account(addr, password, plat)
    log("Conta salva em:", fp)

    # Agora faz o login no aistudio com Selenium
    log("Iniciando Selenium para harvest do aistudio...")
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=opts)
    
    try:
        url = "https://account.xiaomi.com/pass/serviceLogin?sid=xiaomichatbot"
        driver.get(url)
        time.sleep(3)

        # Tratar banner de cookies se existir
        for b in driver.find_elements(By.CSS_SELECTOR, "button[class*='cookie'], div[class*='cookie'] button"):
            try:
                driver.execute_script("arguments[0].click();", b)
            except:
                pass

        # Preenche email
        acc_input = driver.find_element(By.CSS_SELECTOR, "input[name='account']")
        acc_input.clear()
        acc_input.send_keys(addr)

        # Preenche senha
        pwd_input = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
        pwd_input.clear()
        pwd_input.send_keys(password)

        # Checkbox
        for cb in driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"):
            driver.execute_script("arguments[0].click();", cb)

        time.sleep(1)
        btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        driver.execute_script("arguments[0].click();", btn)
        log("Form submetido. Aguardando...")
        time.sleep(5)

        curr_url = driver.current_url or ""
        log("URL apos submit:", curr_url)

        if "verifyEmail" in curr_url or "identity" in curr_url:
            log("verifyEmail detectado! Clicando no botao 'Enviar'...")
            for b in driver.find_elements(By.TAG_NAME, "button"):
                if "enviar" in b.text.lower() or "send" in b.text.lower():
                    driver.execute_script("arguments[0].click();", b)
                    log("Clicou no botao Enviar!")
                    break
            
            log("Aguardando codigo no smailpro inbox...")
            code = sp.wait_for_code(email_obj, timeout=120)
            log("Codigo recebido:", code)
            
            # Digita codigo no input
            for inp in driver.find_elements(By.TAG_NAME, "input"):
                if inp.is_displayed():
                    inp.clear()
                    inp.send_keys(code)
                    log("Digitou codigo no input:", inp.get_attribute("name"))
                    break
            
            time.sleep(1)
            for sub in driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], button[class*='primary']"):
                if sub.is_displayed():
                    driver.execute_script("arguments[0].click();", sub)
                    log("Clicou botao confirmar!")
                    break
            time.sleep(6)

        log("URL final:", driver.current_url)

        # Forcar navegacao para aistudio
        driver.get("https://aistudio.xiaomimimo.com/")
        time.sleep(5)

        cdp = driver.execute_cdp_cmd("Network.getAllCookies", {}) or {}
        raw = cdp.get("cookies") or []
        jar = {c.get("name"): c.get("value", "") for c in raw if c.get("name")}
        
        log("Cookies capturados:", sorted(jar.keys()))
        ph = jar.get("xiaomichatbot_ph")
        st = jar.get("xiaomichatbot_serviceToken") or jar.get("serviceToken")
        uid = jar.get("userId") or jar.get("cUserId")

        if ph:
            log(f"*** VITORIA! OBTIDO xiaomichatbot_ph: {ph[:12]}... ***")
            sess = {
                "userId": uid,
                "xiaomichatbot_ph": ph,
                "xiaomichatbot_serviceToken": st,
                "email": addr,
                "password": password
            }
            # Salvar no cookies.json
            cookies_file = BASE_DIR / "cookies.json"
            cookies_data = json.loads(cookies_file.read_text(encoding="utf-8")) if cookies_file.exists() else []
            cookies_data.append(sess)
            cookies_file.write_text(json.dumps(cookies_data, indent=2, ensure_ascii=False), encoding="utf-8")
            log("Sessao salva no cookies.json!")
            return sess
        else:
            log("xiaomichatbot_ph nao encontrado. Cookies:", jar)
            return None
    finally:
        driver.quit()

if __name__ == "__main__":
    test_full_pipeline()
