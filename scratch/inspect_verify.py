from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--disable-gpu")
driver = webdriver.Chrome(options=opts)

try:
    url = "https://account.xiaomi.com/fe/service/login/password?sid=xiaomichatbot&qs=%253Fsid%253Dxiaomichatbot&callback=https%3A%2F%2Faistudio.xiaomimimo.com%2Fsts"
    driver.get(url)
    time.sleep(3)

    driver.find_element(By.CSS_SELECTOR, "input[name='account']").send_keys("emily.garza876+cvyvk@outlook.com")
    driver.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys("T3st@api9x35")
    for cb in driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"):
        driver.execute_script("arguments[0].click();", cb)
    time.sleep(1)
    btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    driver.execute_script("arguments[0].click();", btn)
    time.sleep(6)

    print("Current URL:", driver.current_url)
    print("Page Title:", driver.title)
    for b in driver.find_elements(By.TAG_NAME, "button"):
        print(f"Button: text='{b.text.strip()}' class='{b.get_attribute('class')}'")
    for i in driver.find_elements(By.TAG_NAME, "input"):
        print(f"Input: name='{i.get_attribute('name')}' type='{i.get_attribute('type')}' placeholder='{i.get_attribute('placeholder')}'")
finally:
    driver.quit()
