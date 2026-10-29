from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import sys
sys.path.append(r"E:\AI_MODELS\PROXY-REVERSA")
from smailpro_client import SmailproClient, TempEmail

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--disable-gpu")
driver = webdriver.Chrome(options=opts)

try:
    url = "https://account.xiaomi.com/pass/serviceLogin?sid=xiaomichatbot&callback=https%3A%2F%2Faistudio.xiaomimimo.com%2Fsts"
    driver.get(url)
    time.sleep(3)

    driver.find_element(By.CSS_SELECTOR, "input[name='account']").send_keys("lcwzh5356009+ekyxf@outlook.com")
    driver.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys("T3st@api9x52")
    for cb in driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"):
        driver.execute_script("arguments[0].click();", cb)
    time.sleep(1)
    btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    driver.execute_script("arguments[0].click();", btn)
    time.sleep(5)

    print("Current URL:", driver.current_url)

    # Clica Enviar
    for b in driver.find_elements(By.TAG_NAME, "button"):
        if "enviar" in b.text.lower() or "send" in b.text.lower():
            driver.execute_script("arguments[0].click();", b)
            print("Clicked Enviar code!")
            break

    # Look for code in smailpro for lcwzh5356009+ekyxf@outlook.com
    # Note: smailpro needs email_obj. But let's see what the page looks like right after clicking Enviar!
    time.sleep(3)
    driver.save_screenshot(r"E:\AI_MODELS\research_duel\scratch\verify_code_input.png")
    
    print("Inputs on verify page:")
    for inp in driver.find_elements(By.TAG_NAME, "input"):
        print("  input:", inp.get_attribute("name"), inp.get_attribute("type"), inp.get_attribute("placeholder"), "displayed:", inp.is_displayed())
    print("Buttons on verify page:")
    for b in driver.find_elements(By.TAG_NAME, "button"):
        print("  btn:", b.text.strip(), "displayed:", b.is_displayed())
finally:
    driver.quit()
