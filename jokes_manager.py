import json
import os
from telegram import Update

FILE = "jokes.json"

def load_jokes():
    if not os.path.exists(FILE):
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # 🧹 اگر فایل خراب بود، دوباره بسازش
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        return {}

def save_jokes(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def save_joke(update: Update):
    try:
        if not update.message.reply_to_message:
            return await update.message.reply_text("❗ باید روی پیام جوک ریپلای بزنی.")
        msg = update.message.reply_to_message.text
        if not msg:
            return await update.message.reply_text("❌ پیام ریپلای باید متنی باشه!")

        data = load_jokes()
        data[str(len(data) + 1)] = msg.strip()
        save_jokes(data)
        await update.message.reply_text("😂 جوک ذخیره شد!")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ذخیره جوک: {e}")

async def list_jokes(update: Update):
    data = load_jokes()
    if not data:
        return await update.message.reply_text("هنوز جوکی ثبت نشده 😅")
    text = "\n\n".join([f"{k}. {v}" for k, v in data.items()])
    if len(text) > 4000:
        text = text[:3990] + "..."
    await update.message.reply_text(f"😂 لیست جوک‌ها:\n\n{text}")
