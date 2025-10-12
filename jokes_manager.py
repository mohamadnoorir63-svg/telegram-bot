import json
import os
from datetime import datetime
from telegram import Update

JOKES_FILE = "jokes.json"

# ======================= 📦 آماده‌سازی فایل جوک‌ها =======================

def init_jokes():
    """ایجاد فایل در صورت نبود"""
    if not os.path.exists(JOKES_FILE):
        with open(JOKES_FILE, "w", encoding="utf-8") as f:
            json.dump({"jokes": []}, f, ensure_ascii=False, indent=2)

def load_jokes():
    if not os.path.exists(JOKES_FILE):
        init_jokes()
    with open(JOKES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_jokes(data):
    with open(JOKES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================= 😂 ثبت جوک =======================

async def save_joke(update: Update):
    """ذخیره جوک جدید از پیام ریپلای‌شده"""
    reply = update.message.reply_to_message
    if not reply:
        await update.message.reply_text("❗ برای ثبت جوک باید روی یه پیام ریپلای بزنی.")
        return

    data = load_jokes()
    joke_entry = {
        "user": update.effective_user.first_name,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "text": reply.text or "",
        "photo_id": reply.photo[-1].file_id if reply.photo else None,
    }

    data["jokes"].append(joke_entry)
    save_jokes(data)

    await update.message.reply_text("😂 جوک با موفقیت ذخیره شد!")

# ======================= 📋 لیست جوک‌ها =======================

async def list_jokes(update: Update):
    """نمایش لیست جوک‌های ذخیره‌شده"""
    data = load_jokes()
    jokes = data.get("jokes", [])
    if not jokes:
        await update.message.reply_text("فعلاً هیچ جوکی ذخیره نشده 😅")
        return

    text = "🤣 لیست آخرین جوک‌ها:\n\n"
    for j in jokes[-10:][::-1]:
        text += f"👤 {j['user']} — {j['date']}\n"
        if j["text"]:
            text += f"💬 {j['text']}\n"
        if j["photo_id"]:
            text += f"🖼 [جوک تصویری ثبت شده]\n"
        text += "\n"

    await update.message.reply_text(text[:4000])
