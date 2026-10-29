import json
import httpx

with open(r"E:\AI_MODELS\PROXY-REVERSA\accounts\emily_garza876_cvyvk_outlook_com.json", "r", encoding="utf-8") as f:
    acc = json.load(f)

# Use cookies from allCookies
cookies = {}
for c in acc.get("allCookies", []):
    cookies[c["name"]] = c["value"].strip('"')

cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items() if k in ("userId", "cUserId", "passToken", "deviceId", "pass_ua")])

client = httpx.Client(follow_redirects=False, timeout=15.0)

login_url = "https://account.xiaomi.com/pass/serviceLogin?sid=xiaomichatbot&callback=https%3A%2F%2Faistudio.xiaomimimo.com%2Fsts"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Cookie": cookie_header
}

curr_url = login_url
curr_headers = dict(headers)

for step in range(5):
    print(f"\n--- STEP {step+1}: GET {curr_url[:80]} ---")
    resp = client.get(curr_url, headers=curr_headers)
    print(f"Status: {resp.status_code}")
    for h, v in resp.headers.items():
        if h.lower() == "set-cookie":
            print(f"  Set-Cookie: {v[:120]}")
    loc = resp.headers.get("Location")
    if not loc:
        print("Final response body:", resp.text[:200])
        break
    print(f"Redirects to: {loc[:80]}")
    curr_url = loc
    # Forward new cookies if set
    new_cookies = []
    for h, v in resp.headers.multi_items():
        if h.lower() == "set-cookie":
            parts = v.split(";")[0]
            new_cookies.append(parts)
    if new_cookies:
        curr_headers["Cookie"] = curr_headers.get("Cookie", "") + "; " + "; ".join(new_cookies)
