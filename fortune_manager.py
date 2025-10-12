import json
import os
import random
from telegram import Update

FILE = "fortunes.json"

# ======================= 📂 بارگذاری و ذخیره =======================

def load_fortunes():
    if not os.path.exists(FILE):
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    with open(FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_fortunes(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================= 🔮 ثبت فال =======================

async def save_fortune(update: Update):
    """ذخیره فال جدید با ریپلای"""
    if not update.message.reply_to_message or not update.message.reply_to_message.text:
        return await update.message.reply_text("❗ فقط متن فال رو ریپلای کن (نه عکس یا استیکر).")

    data = load_fortunes()
    msg = update.message.reply_to_message.text.strip()
    if not msg:
        return await update.message.reply_text("❗ فال خالیه 😅")

    new_id = str(len(data) + 1)
    data[new_id] = msg
    save_fortunes(data)
    await update.message.reply_text("🔮 فال ذخیره شد!")

# ======================= 📜 لیست فال‌ها =======================

async def list_fortunes(update: Update):
    data = load_fortunes()
    if not data:
        return await update.message.reply_text("هنوز فالی ثبت نشده 😅")

    text = "\n\n".join([f"{k}. {v}" for k, v in data.items()])
    await update.message.reply_text(f"🔮 *لیست فال‌ها:*\n\n{text}", parse_mode="Markdown")

# ======================= 🎲 فال تصادفی =======================

def get_random_fortune():
    data = load_fortunes()
    if not data:
        return None
    return random.choice(list(data.values()))
