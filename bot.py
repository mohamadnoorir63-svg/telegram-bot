import os
import requests

HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# مدل تستی که حتماً فعال است
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"

payload = {
    "inputs": "سلام! حالت چطوره؟",
    "parameters": {"max_new_tokens": 50}
}

print("🚀 در حال ارسال درخواست به Hugging Face...")

try:
    response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    print("📩 پاسخ دریافت شد!")
    print("کد وضعیت:", response.status_code)
    print("خروجی خام:\n", response.text)

    if response.status_code == 200:
        print("\n✅ اتصال و مدل هر دو درست کار می‌کنند!")
    elif "error" in response.text:
        print("\n⚠️ خطا از سمت Hugging Face:")
        print(response.text)
    else:
        print("\n❌ پاسخ غیرمنتظره دریافت شد.")

except Exception as e:
    print("💥 خطا در اتصال یا درخواست:", str(e))
