from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import sys
from pathlib import Path

BASE_DIR = Path(r"E:\AI_MODELS\PROXY-REVERSA")
sys.path.insert(0, str(BASE_DIR))
from smailpro_client import SmailproClient
from xiaomi_api import XiaomiAPI

def log(*args):
    print(time.strftime("%H:%M:%S"), *args, flush=True)

# Register brand new account
sp = SmailproClient()
eo = sp.create_email(domain="outlook.com")
addr = eo.address
pwd = "T3st@api9x77"
log("Created email:", addr)

x = XiaomiAPI()
j = x.register_full(addr, pwd, lambda em: sp.wait_for_code(eo, timeout=120))
log("Registered:", j.get("result"))

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--disable-gpu")
driver = webdriver.Chrome(options=opts)

try:
    url = "https://account.xiaomi.com/pass/serviceLogin?sid=xiaomichatbot&callback=https%3A%2F%2Faistudio.xiaomimimo.com%2Fsts"
    driver.get(url)
    time.sleep(3)

    driver.find_element(By.CSS_SELECTOR, "input[name='account']").send_keys(addr)
    driver.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys(pwd)
    for cb in driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"):
        driver.execute_script("arguments[0].click();", cb)
    time.sleep(1)

    driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "button[type='submit']"))
    time.sleep(5)

    log("Current URL:", driver.current_url)

    if "verifyEmail" in driver.current_url:
        for b in driver.find_elements(By.TAG_NAME, "button"):
            if "enviar" in b.text.lower() or "send" in b.text.lower():
                driver.execute_script("arguments[0].click();", b)
                log("Clicked Enviar")
                break

        code = sp.wait_for_code(eo, timeout=120)
        log("Code:", code)

        inp = driver.find_element(By.CSS_SELECTOR, "input[name='ticket']")
        inp.clear()
        inp.send_keys(code)
        time.sleep(1)

        for b in driver.find_elements(By.TAG_NAME, "button"):
            if b.text.strip().lower() in ("submit", "confirmar", "avancar", "next"):
                driver.execute_script("arguments[0].click();", b)
                log("Clicked Submit!")
                break

        # DO NOT CALL driver.get()! Let the browser follow the natural redirect!
        log("Waiting for natural redirect (up to 30s)...")
        for i in range(30):
            time.sleep(1)
            curr = driver.current_url
            if i % 3 == 0:
                log(f"Step {i} URL: {curr[:80]}")
            if "aistudio" in curr:
                log("REACHED AISTUDIO NATURALLY!")
                break

    time.sleep(3)
    cdp = driver.execute_cdp_cmd("Network.getAllCookies", {}) or {}
    raw = cdp.get("cookies") or []
    jar = {c.get("name"): c.get("value", "") for c in raw if c.get("name")}
    log("Cookies in jar:", sorted(jar.keys()))

    if "xiaomichatbot_ph" in jar:
        log("FOUND xiaomichatbot_ph! Token:", jar["xiaomichatbot_ph"])
        import json
        sess = {
            "userId": jar.get("userId") or jar.get("cUserId", ""),
            "xiaomichatbot_ph": jar["xiaomichatbot_ph"],
            "xiaomichatbot_serviceToken": jar.get("xiaomichatbot_serviceToken") or jar.get("serviceToken", ""),
            "email": addr,
            "password": pwd
        }
        Path(r"E:\AI_MODELS\PROXY-REVERSA\cookies.json").write_text(json.dumps([sess], indent=2), encoding="utf-8")
        log("WROTE COOKIE TO cookies.json!")
    else:
        log("xiaomichatbot_ph NOT in jar.")
finally:
    driver.quit()
