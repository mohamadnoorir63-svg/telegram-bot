import os
import requests

HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

if not HF_TOKEN:
    print("❌ خطا: متغیر HUGGINGFACE_TOKEN تنظیم نشده است.")
    exit()

API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"

headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
payload = {"inputs": "سلام! حالت چطوره؟", "parameters": {"max_new_tokens": 50}}

print("🚀 در حال ارسال درخواست به Hugging Face...")

try:
    response = requests.post(API_URL, headers=headers, json=payload)
    print("📩 پاسخ دریافت شد!")
    print("کد وضعیت:", response.status_code)

    if response.status_code == 200:
        result = response.json()
        print("✅ پاسخ مدل:")
        print(result[0]["generated_text"])
    else:
        print("❌ پاسخ غیرمنتظره دریافت شد.")
        print("خروجی خام:")
        print(response.text)

except Exception as e:
    print("⚠️ خطا در اتصال:", e)
