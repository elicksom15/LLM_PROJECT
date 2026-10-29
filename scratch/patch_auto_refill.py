import re

path = r"E:\AI_MODELS\PROXY-REVERSA\auto_refill.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace definition of login_aistudio_http
old_func_pattern = re.compile(
    r"def login_aistudio_http\(email: str, password: str, timeout: float = LOGIN_TIMEOUT\).*?driver\.get\(\"https://aistudio\.xiaomimimo\.com/\"\)\s+time\.sleep\(4\)",
    re.DOTALL
)

new_func = """def login_aistudio_http(email: str, password: str, timeout: float = LOGIN_TIMEOUT, sp=None, email_obj=None) -> Optional[Dict]:
    \"\"\"
    Login via browser headless em aistudio.xiaomimimo.com (sid=xiaomichatbot).
    Retorna dict {userId, xiaomichatbot_ph, xiaomichatbot_serviceToken, email} ou None.
    \"\"\"
    try:
        from seleniumbase import Driver
    except ImportError:
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            opts = Options()
            opts.add_argument("--headless=new")
            opts.add_argument("--disable-gpu")
            opts.add_argument(f"--user-agent={UA}")
            driver = webdriver.Chrome(options=opts)
        except Exception as e:
            _log("browser unavailable", e)
            return None
    else:
        driver = Driver(browser="chrome", headless=True)
        driver.set_page_load_timeout(30)

    try:
        _log("aistudio login", email)
        driver.get("https://account.xiaomi.com/pass/serviceLogin?sid=xiaomichatbot")
        time.sleep(3)

        # Tratar banner de cookies
        try:
            for b in driver.find_elements(By.CSS_SELECTOR, "button[class*='cookie'], div[class*='cookie'] button"):
                driver.execute_script("arguments[0].click();", b)
        except Exception:
            pass

        # preenche email
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        acc = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[name='account'], input[name='user'], input[type='email']")
            )
        )
        acc.clear()
        acc.send_keys(email)
        time.sleep(0.5)

        # senha
        try:
            pw = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
            )
            pw.clear()
            pw.send_keys(password)
        except Exception:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                driver.execute_script("arguments[0].click();", btn)
            except Exception:
                acc.send_keys("\\n")
            time.sleep(2)
            pw = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
            )
            pw.clear()
            pw.send_keys(password)

        # Checkbox termos
        try:
            for cb in driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"):
                if not cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
        except Exception:
            pass

        # submit via JavaScript
        try:
            btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            driver.execute_script("arguments[0].click();", btn)
        except Exception:
            pw.send_keys("\\n")

        time.sleep(3)

        # Trata verificação de email (verifyEmail) se solicitada
        curr_url = driver.current_url or ""
        if "verifyEmail" in curr_url or "identity" in curr_url:
            if not sp or not email_obj:
                _log("verifyEmail exigido sem caixa postal ativa — pulando conta rapidamente")
                return None
            _log("verifyEmail detectado! Clicando Enviar código...")
            try:
                for b in driver.find_elements(By.TAG_NAME, "button"):
                    txt = b.text.lower()
                    if "enviar" in txt or "send" in txt:
                        driver.execute_script("arguments[0].click();", b)
                        _log("Clicou Enviar código!")
                        break
            except Exception as ex:
                _log("Erro ao clicar Enviar:", ex)

            _log("Aguardando código smailpro...")
            code = sp.wait_for_code(email_obj, timeout=120)
            if not code:
                _log("Código não recebido no smailpro.")
                return None
            _log("Código recebido:", code)

            # Preenche o código
            for inp in driver.find_elements(By.TAG_NAME, "input"):
                if inp.is_displayed():
                    inp.clear()
                    inp.send_keys(code)
                    _log("Código inserido no input:", inp.get_attribute("name"))
                    break
            time.sleep(1)

            # Clica confirmar
            for sub in driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], button[class*='primary']"):
                if sub.is_displayed():
                    driver.execute_script("arguments[0].click();", sub)
                    _log("Confirmou código!")
                    break
            time.sleep(5)

        # agree modal
        try:
            agree = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Agree')]"))
            )
            driver.execute_script("arguments[0].click();", agree)
            time.sleep(1.5)
        except Exception:
            pass

        # espera login
        deadline = time.time() + timeout
        logged = False
        while time.time() < deadline:
            time.sleep(1)
            try:
                host = driver.execute_script("return location.hostname") or ""
            except Exception:
                host = ""
            names = {c["name"] for c in driver.get_cookies()}
            if "passToken" in names or "cUserId" in names:
                logged = True
                break
            if host in ("aistudio.xiaomimimo.com", "platform.xiaomimimo.com"):
                logged = True
                break

        if not logged:
            _log("login nao completou", driver.execute_script("return location.hostname"))
            return None

        # força harvest no aistudio
        driver.get("https://aistudio.xiaomimimo.com/")
        time.sleep(5)
        for _ in range(3):
            try:
                host = driver.execute_script("return location.hostname") or ""
            except Exception:
                host = ""
            if "account.xiaomi" in host or "serviceLogin" in (driver.current_url or ""):
                time.sleep(4)
                continue
            break
        driver.get("https://aistudio.xiaomimimo.com/")
        time.sleep(4)"""

if old_func_pattern.search(content):
    content = old_func_pattern.sub(new_func, content, count=1)
    print("login_aistudio_http patched!")
else:
    print("Could not find login_aistudio_http pattern!")

# Update register_new_account to pass sp and email_obj
old_call = 'sess = login_aistudio_http(addr, password)'
new_call = 'sess = login_aistudio_http(addr, password, sp=sp, email_obj=email_obj)'
if old_call in content:
    content = content.replace(old_call, new_call, 1)
    print("register_new_account call patched!")
else:
    print("Could not find register_new_account call!")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Finished patching auto_refill.py")
