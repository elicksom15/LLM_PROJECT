from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import json

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--disable-gpu")
driver = webdriver.Chrome(options=opts)

try:
    url = "https://account.xiaomi.com/fe/service/login/password?sid=xiaomichatbot&qs=%253Fsid%253Dxiaomichatbot&callback=https%3A%2F%2Faistudio.xiaomimimo.com%2Fsts"
    driver.get(url)
    time.sleep(3)
    
    # Preencher account
    acc = driver.find_element(By.CSS_SELECTOR, "input[name='account']")
    acc.clear()
    acc.send_keys("emily.garza876+cvyvk@outlook.com")
    
    # Preencher password
    pwd = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
    pwd.clear()
    pwd.send_keys("T3st@api9x35")
    
    # Marcar checkbox
    checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
    for cb in checkboxes:
        if not cb.is_selected():
            driver.execute_script("arguments[0].click();", cb)
    
    time.sleep(1)
    
    # Clicar botão de submit
    btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    driver.execute_script("arguments[0].click();", btn)
    
    print("Clicked submit. Waiting 8 seconds...")
    time.sleep(8)
    
    print("After submit URL:", driver.current_url)
    print("After submit Title:", driver.title)
    driver.save_screenshot(r"E:\AI_MODELS\research_duel\scratch\after_submit.png")
    
    cookies = driver.get_cookies()
    print("Cookies obtained:")
    for c in cookies:
        print(f"  {c['name']}: {c['value'][:25]} (domain={c['domain']})")
        
finally:
    driver.quit()
