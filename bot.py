import os
import requests

# 🔑 خواندن توکن از Config Vars در Heroku
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

# ✅ مدل جدید و فعال (پشتیبانی از فارسی)
API_URL = "https://api-inference.huggingface.co/models/google/gemma-2b-it"

headers = {
    "Authorization": f"Bearer {HUGGINGFACE_TOKEN}",
    "Content-Type": "application/json"
}

# 📤 تابع برای ارسال درخواست به Hugging Face
def ask_huggingface(prompt):
    print("🚀 در حال ارسال درخواست به Hugging Face...")
    data = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 150}
    }
    response = requests.post(API_URL, headers=headers, json=data)
    print("📩 پاسخ دریافت شد!")
    print("کد وضعیت:", response.status_code)

    if response.status_code == 200:
        result = response.json()
        if isinstance(result, list) and "generated_text" in result[0]:
            print("✅ پاسخ مدل:")
            print(result[0]["generated_text"])
        else:
            print("⚠️ ساختار خروجی غیرمنتظره:", result)
    else:
        print("❌ پاسخ غیرمنتظره دریافت شد.")
        print("خروجی خام:")
        print(response.text)

# 🧠 تست اتصال
if __name__ == "__main__":
    ask_huggingface("سلام، حالت چطوره؟")
