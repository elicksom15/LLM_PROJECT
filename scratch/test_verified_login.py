from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--disable-gpu")
driver = webdriver.Chrome(options=opts)

try:
    url = "https://account.xiaomi.com/pass/serviceLogin?sid=xiaomichatbot&callback=https%3A%2F%2Faistudio.xiaomimimo.com%2Fsts"
    driver.get(url)
    time.sleep(3)

    # Login
    driver.find_element(By.CSS_SELECTOR, "input[name='account']").send_keys("lcwzh5356009+ekyxf@outlook.com")
    driver.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys("T3st@api9x52")
    for cb in driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"):
        driver.execute_script("arguments[0].click();", cb)
    time.sleep(1)
    btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    driver.execute_script("arguments[0].click();", btn)
    print("Submitted form. Waiting 10s...")
    time.sleep(10)

    print("Current URL:", driver.current_url)
    print("Page Title:", driver.title)
    driver.save_screenshot(r"E:\AI_MODELS\research_duel\scratch\after_verify_login.png")

    # Navigate to aistudio
    driver.get("https://aistudio.xiaomimimo.com/")
    time.sleep(5)
    print("AIStudio URL:", driver.current_url)

    cdp = driver.execute_cdp_cmd("Network.getAllCookies", {}) or {}
    raw = cdp.get("cookies") or []
    jar = {c.get("name"): c.get("value", "") for c in raw if c.get("name")}
    print("Cookies from CDP:")
    for k in sorted(jar.keys()):
        print(f"  {k}: {jar[k][:30]}...")

    if "xiaomichatbot_ph" in jar:
        print("\n*** OBTIDO COM SUCESSO xiaomichatbot_ph! ***")
        ph = jar["xiaomichatbot_ph"]
        st = jar.get("xiaomichatbot_serviceToken") or jar.get("serviceToken")
        uid = jar.get("userId") or jar.get("cUserId")
        print(f"userId: {uid}")
        print(f"ph: {ph}")
        print(f"st: {st}")
finally:
    driver.quit()
