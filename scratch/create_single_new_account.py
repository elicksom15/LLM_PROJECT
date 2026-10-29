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

print("1. Creating fresh smailpro email...")
sp = SmailproClient()
eo = sp.create_email(domain="outlook.com")
addr = eo.address
pwd = "T3st@api9x11"
print("Email:", addr)

print("2. Registering via XiaomiAPI...")
x = XiaomiAPI()
j = x.register_full(addr, pwd, lambda em: sp.wait_for_code(eo, timeout=120))
print("Registration result:", j.get("result"))

print("3. Opening Chrome...")
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
    print("URL after login submit:", driver.current_url)

    if "verifyEmail" in driver.current_url:
        print("verifyEmail prompt. Clicking Enviar...")
        for b in driver.find_elements(By.TAG_NAME, "button"):
            if "enviar" in b.text.lower() or "send" in b.text.lower():
                driver.execute_script("arguments[0].click();", b)
                break
        
        print("Waiting for code in smailpro...")
        code = sp.wait_for_code(eo, timeout=120)
        print("Received code:", code)

        inp = driver.find_element(By.CSS_SELECTOR, "input[name='ticket']")
        inp.clear()
        inp.send_keys(code)
        # also fire input events
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles:true}));", inp)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change', {bubbles:true}));", inp)
        time.sleep(1)

        submit_btn = None
        for b in driver.find_elements(By.TAG_NAME, "button"):
            if b.text.strip().lower() in ("submit", "confirmar", "avancar", "next"):
                submit_btn = b
                break
        
        if submit_btn:
            print("Clicking submit button:", submit_btn.text)
            driver.execute_script("arguments[0].click();", submit_btn)
        
        print("Waiting 10s and tracking network / URLs...")
        for sec in range(12):
            time.sleep(1)
            print(f"  Sec {sec+1} URL: {driver.current_url[:90]}")
            if "aistudio" in driver.current_url:
                print("  ==> NAVIGATED TO AISTUDIO!")
                break
        
        # Check if error message is on page
        page_text = driver.find_element(By.TAG_NAME, "body").text
        lines = [l.strip() for l in page_text.splitlines() if l.strip()]
        print("Page text lines:", lines[:10])

    # Check cookies
    cdp = driver.execute_cdp_cmd("Network.getAllCookies", {}) or {}
    raw = cdp.get("cookies") or []
    jar = {c.get("name"): c.get("value", "") for c in raw if c.get("name")}
    print("CDP Cookies found:")
    for k in sorted(jar.keys()):
        print(f"  {k}: {jar[k][:25]}...")

    if "xiaomichatbot_ph" in jar:
        print(f"\n*** SUCCESS! xiaomichatbot_ph = {jar['xiaomichatbot_ph']} ***")
        sess = {
            "userId": jar.get("userId") or jar.get("cUserId", ""),
            "xiaomichatbot_ph": jar["xiaomichatbot_ph"],
            "xiaomichatbot_serviceToken": jar.get("xiaomichatbot_serviceToken") or jar.get("serviceToken", ""),
            "email": addr,
            "password": pwd
        }
        with open(r"E:\AI_MODELS\PROXY-REVERSA\cookies.json", "w", encoding="utf-8") as f:
            json.dump([sess], f, indent=2)
        print("Saved directly to E:\\AI_MODELS\\PROXY-REVERSA\\cookies.json!")
finally:
    driver.quit()
