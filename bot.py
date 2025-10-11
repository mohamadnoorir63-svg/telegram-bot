import os
import requests

HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

# 🟢 مدل عمومی و فعال
API_URL = "https://api-inference.huggingface.co/models/NousResearch/hermes-2-pro-mistral"

headers = {
    "Authorization": f"Bearer {HUGGINGFACE_TOKEN}",
    "Content-Type": "application/json"
}

def ask_huggingface(prompt):
    print("🚀 در حال ارسال درخواست به Hugging Face...")
    data = {"inputs": prompt, "parameters": {"max_new_tokens": 150}}
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

if __name__ == "__main__":
    ask_huggingface("سلام، حالت چطوره؟")
