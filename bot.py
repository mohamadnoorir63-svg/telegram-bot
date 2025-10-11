import os
import requests

# دریافت توکن از تنظیمات Heroku
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

# اگر متغیر محیطی خالی بود، اخطار بده
if not HF_TOKEN:
    print("❌ خطا: متغیر HUGGINGFACE_TOKEN تنظیم نشده است.")
    exit()

# آدرس مدل امن و فعال
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

# ورودی تستی برای مدل
payload = {
    "inputs": "سلام! حالت چطوره؟",
    "parameters": {"max_new_tokens": 100}
}

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
    print("⚠️ خطای کلی هنگام اتصال:", e)
