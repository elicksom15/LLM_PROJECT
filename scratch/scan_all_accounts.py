import glob
import json
import os
import httpx

dirs = [
    r"E:\AI_MODELS\PROXY-REVERSA\accounts",
    r"C:\Users\elick\Downloads\doidera dms\accounts"
]

all_accs = []
for d in dirs:
    if os.path.exists(d):
        for f in glob.glob(os.path.join(d, "*.json")):
            all_accs.append(f)

print(f"Total account files found: {len(all_accs)}")

valid_tokens = []

for p in all_accs:
    try:
        with open(p, "r", encoding="utf-8") as fp:
            acc = json.load(fp)
    except Exception:
        continue
    
    ph = acc.get("xiaomichatbot_ph")
    st = acc.get("serviceToken")
    uid = acc.get("userId") or acc.get("userIdCookie")
    
    for c in acc.get("allCookies", []):
        name = c.get("name", "")
        if name in ("xiaomichatbot_ph", "api-platform_ph") and not ph:
            ph = c.get("value")
        if "serviceToken" in name and not st:
            st = c.get("value")
        if name == "userId" and not uid:
            uid = c.get("value")

    if ph and uid:
        valid_tokens.append({
            "file": p,
            "email": acc.get("email"),
            "userId": str(uid),
            "ph": str(ph).strip('"'),
            "st": str(st).strip('"') if st else ""
        })

print(f"Accounts with potential ph token: {len(valid_tokens)}")

# Test the first 5 potential tokens against Xiaomi API
for item in valid_tokens[:10]:
    url = f"https://aistudio.xiaomimimo.com/fastchat/open-apis/bot/chat?xiaomichatbot_ph={item['ph']}"
    headers = {
        "Cookie": f"userId={item['userId']}; xiaomichatbot_ph=\"{item['ph']}\"; xiaomichatbot_serviceToken=\"{item['st']}\"",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    payload = {
        "msgId": "test_ping",
        "conversationId": "test_conv",
        "query": "ola",
        "isEditedQuery": False,
        "modelConfig": {"enableThinking": False, "webSearchStatus": "disabled", "model": "mimo-v2.6-pro-ultraspeed-studio"},
        "multiMedias": []
    }
    try:
        with httpx.Client(timeout=6.0) as client:
            r = client.post(url, headers=headers, json=payload)
            print(f"[{item['email']}] Status: {r.status_code} | Text: {r.text[:100]}")
            if r.status_code == 200:
                print(f"*** FOUND WORKING TOKEN! {item['email']} ***")
                break
    except Exception as ex:
        print(f"[{item['email']}] Error: {ex}")
