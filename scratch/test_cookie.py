import httpx
import urllib.parse
import json

ph = "YUGAogzWNn13ve3hXLKosw=="
uid = "6897627323"
tok = "/vjQa88K2JeX+vuUvl6J6EnFeuU7ajighpMZoYVgRPeOwf911UQ+BZbX4mBROr7xqOeGE3p06i13HBng/JO0/bbtmQaZySzKmrGLnAofO3ie+SKax1EDJBIX/a16pHZRS7CIziHGLSEKxalVHTg6PI6es72kcMTDxBHBUJjs2cQrFCt/U60B5axSZeeczECgPR/ZzB0GVieCaVY2EcOGZl7eoRz/1K95COdqP3vwAGNHzx534CcHLqbNt45lbuWYYVon5cl4y7pxOu3eKK60lt18vs+LFm74rv4ix5ilQS/dyRGleyywOCqeK/c4HbOXc42WWD75th83eAPtCsJdukS9DsbNxK3VBkHzM24lVeI="

url = f"https://aistudio.xiaomimimo.com/fastchat/open-apis/bot/chat?xiaomichatbot_ph={urllib.parse.quote(ph)}"
headers = {
    "Cookie": f'userId={uid}; xiaomichatbot_ph="{ph}"; xiaomichatbot_serviceToken="{tok}"',
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}
payload = {
    "msgId": "test_msg_check",
    "conversationId": "test_conv_check",
    "query": "ping",
    "isEditedQuery": False,
    "modelConfig": {
        "enableThinking": False,
        "webSearchStatus": "disabled",
        "model": "mimo-v2.6-pro-ultraspeed-studio"
    },
    "multiMedias": []
}

try:
    r = httpx.post(url, headers=headers, json=payload, timeout=12.0)
    print("FastChat Status:", r.status_code)
    print("FastChat Body:", r.text[:250])
except Exception as e:
    print("FastChat Error:", e)

# Test standard chat
url_std = f"https://aistudio.xiaomimimo.com/open-apis/bot/chat?xiaomichatbot_ph={urllib.parse.quote(ph)}"
try:
    r2 = httpx.post(url_std, headers=headers, json=payload, timeout=12.0)
    print("Standard Status:", r2.status_code)
    print("Standard Body:", r2.text[:250])
except Exception as e:
    print("Standard Error:", e)
