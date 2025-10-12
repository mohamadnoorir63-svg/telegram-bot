import json
import os
import random
from telegram import Update

FILE = "jokes.json"

# ======================= 📂 بارگذاری و ذخیره =======================

def load_jokes():
    if not os.path.exists(FILE):
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    with open(FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_jokes(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================= 😂 ثبت جوک =======================

async def save_joke(update: Update):
    """ذخیره جوک جدید با ریپلای"""
    if not update.message.reply_to_message or not update.message.reply_to_message.text:
        return await update.message.reply_text("❗ فقط متن جوک رو ریپلای کن (نه عکس یا استیکر).")

    data = load_jokes()
    msg = update.message.reply_to_message.text.strip()
    if not msg:
        return await update.message.reply_text("❗ جوک خالیه 😅")

    new_id = str(len(data) + 1)
    data[new_id] = msg
    save_jokes(data)
    await update.message.reply_text("😂 جوک ذخیره شد!")

# ======================= 📜 لیست جوک‌ها =======================

async def list_jokes(update: Update):
    data = load_jokes()
    if not data:
        return await update.message.reply_text("هنوز جوکی ثبت نشده 😅")

    jokes_text = "\n\n".join([f"{k}. {v}" for k, v in data.items()])
    await update.message.reply_text(f"😂 *لیست جوک‌ها:*\n\n{jokes_text}", parse_mode="Markdown")

# ======================= 🎲 جوک تصادفی =======================

def get_random_joke():
    data = load_jokes()
    if not data:
        return None
    return random.choice(list(data.values()))
