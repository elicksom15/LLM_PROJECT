from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--disable-gpu")
driver = webdriver.Chrome(options=opts)

try:
    driver.get("https://account.xiaomi.com/pass/serviceLogin?sid=xiaomichatbot")
    time.sleep(4)
    print("Page Title:", driver.title)
    print("Current URL:", driver.current_url)
    inputs = driver.find_elements(By.TAG_NAME, "input")
    print("Found input elements:", len(inputs))
    for inp in inputs:
        print("  input:", inp.get_attribute("name"), inp.get_attribute("type"), inp.get_attribute("placeholder"))
    
    driver.save_screenshot(r"E:\AI_MODELS\research_duel\scratch\login_page.png")
    print("Saved screenshot to login_page.png")
finally:
    driver.quit()
