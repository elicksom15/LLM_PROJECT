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

sp = SmailproClient()
eo = sp.create_email(domain="outlook.com")
addr = eo.address
pwd = "T3st@api9x66"

x = XiaomiAPI()
j = x.register_full(addr, pwd, lambda em: sp.wait_for_code(eo, timeout=120))
print("Registered:", j.get("result"))

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

    if "verifyEmail" in driver.current_url:
        for b in driver.find_elements(By.TAG_NAME, "button"):
            if "enviar" in b.text.lower() or "send" in b.text.lower():
                driver.execute_script("arguments[0].click();", b)
                break

        code = sp.wait_for_code(eo, timeout=120)
        print("Code:", code)

        inp = driver.find_element(By.CSS_SELECTOR, "input[name='ticket']")
        # React input event dispatch so React state updates with the value!
        driver.execute_script("""
            const el = arguments[0];
            const val = arguments[1];
            const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            setter.call(el, val);
            el.dispatchEvent(new Event('input', {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
        """, inp, code)
        time.sleep(1)

        for b in driver.find_elements(By.TAG_NAME, "button"):
            if b.text.strip().lower() in ("submit", "confirmar", "avancar", "next"):
                print("Clicking submit button:", b.text)
                driver.execute_script("arguments[0].click();", b)
                break

        time.sleep(5)
        print("URL 5s after submit:", driver.current_url)
        driver.save_screenshot(r"E:\AI_MODELS\research_duel\scratch\after_code_submit.png")
        print("Page text snippet:")
        print(driver.find_element(By.TAG_NAME, "body").text[:400])

        # Wait up to 15s more
        for i in range(15):
            time.sleep(1)
            if "aistudio" in driver.current_url:
                print("Redirected to aistudio! URL:", driver.current_url)
                break
        print("Final URL:", driver.current_url)
finally:
    driver.quit()
