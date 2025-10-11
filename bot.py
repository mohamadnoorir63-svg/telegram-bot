import os
import requests

# توکن رو از متغیر محیطی بخون (همون HUGGINGFACE_TOKEN در Heroku)
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

# اگر خواستی دستی بزاری، خط زیر رو باز کن و توکن رو بین کوتیشن بنویس
# HF_TOKEN = "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# یه مدل ساده و سبک برای تست انتخاب می‌کنیم (gpt2 جواب متنی میده)
API_URL = "https://api-inference.huggingface.co/models/gpt2"

payload = {
    "inputs": "سلام خنگول! حالت چطوره؟",
    "parameters": {"max_new_tokens": 50}
}

print("🚀 در حال ارسال درخواست به Hugging Face...")

try:
    response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
    print("📩 پاسخ دریافت شد!")
    print("کد وضعیت:", response.status_code)
    print("خروجی خام:\n", response.text)

    if response.status_code == 200:
        print("\n✅ اتصال موفق است! مدل جواب داد.")
    elif "error" in response.text:
        print("\n⚠️ خطا از سمت Hugging Face:")
        print(response.text)
    else:
        print("\n❌ پاسخ غیرمنتظره دریافت شد.")

except Exception as e:
    print("💥 خطا در اتصال یا درخواست:", str(e))
