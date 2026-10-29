import json
import httpx

with open(r"E:\AI_MODELS\PROXY-REVERSA\accounts\emily_garza876_cvyvk_outlook_com.json", "r", encoding="utf-8") as f:
    acc = json.load(f)

cookies = {}
for c in acc.get("allCookies", []):
    cookies[c["name"]] = c["value"].strip('"')

print("Loaded cookies:", list(cookies.keys()))

client = httpx.Client(follow_redirects=True, timeout=15.0)
for k, v in cookies.items():
    client.cookies.set(k, v, domain=".xiaomi.com")
    client.cookies.set(k, v, domain=".account.xiaomi.com")

login_url = "https://account.xiaomi.com/pass/serviceLogin?sid=xiaomichatbot&callback=https%3A%2F%2Faistudio.xiaomimimo.com%2Fsts"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

resp = client.get(login_url, headers=headers)
print("Final URL:", resp.url)
print("Status code:", resp.status_code)

final_cookies = dict(client.cookies)
print("All final cookies:")
for k, v in final_cookies.items():
    print(f"  {k}: {v[:30]}...")

if "xiaomichatbot_ph" in final_cookies:
    print("\n*** SUCESSO ABSOLUTO! OBTIDO xiaomichatbot_ph! ***")
    ph = final_cookies["xiaomichatbot_ph"]
    st = final_cookies.get("xiaomichatbot_serviceToken") or final_cookies.get("serviceToken")
    uid = final_cookies.get("userId") or acc.get("userId")
    print(f"userId: {uid}")
    print(f"ph: {ph}")
    print(f"st: {st[:30]}...")
else:
    print("\nNao veio no redirect direto. Vamos tentar aistudio:")
    resp2 = client.get("https://aistudio.xiaomimimo.com/", headers=headers)
    print("AIStudio URL:", resp2.url)
    print("AIStudio Cookies:", list(client.cookies.keys()))
