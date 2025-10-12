import json
import os
from datetime import datetime
from telegram import Update

FORTUNE_FILE = "fortunes.json"

# ======================= 📦 آماده‌سازی فایل فال‌ها =======================

def init_fortunes():
    """ایجاد فایل در صورت نبود"""
    if not os.path.exists(FORTUNE_FILE):
        with open(FORTUNE_FILE, "w", encoding="utf-8") as f:
            json.dump({"fortunes": []}, f, ensure_ascii=False, indent=2)

def load_fortunes():
    if not os.path.exists(FORTUNE_FILE):
        init_fortunes()
    with open(FORTUNE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_fortunes(data):
    with open(FORTUNE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================= 💫 ثبت فال =======================

async def save_fortune(update: Update):
    """ذخیره فال جدید با متن یا عکس (ریپلای لازم دارد)"""
    reply = update.message.reply_to_message
    if not reply:
        await update.message.reply_text("❗ برای ثبت فال باید روی یک پیام ریپلای بزنی.")
        return

    data = load_fortunes()
    fortune_entry = {
        "user": update.effective_user.first_name,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "text": reply.text or "",
        "photo_id": reply.photo[-1].file_id if reply.photo else None,
    }

    data["fortunes"].append(fortune_entry)
    save_fortunes(data)

    await update.message.reply_text("🔮 فال جدید با موفقیت ذخیره شد!")

# ======================= 📋 لیست فال‌ها =======================

async def list_fortunes(update: Update):
    """نمایش لیست فال‌های ذخیره‌شده"""
    data = load_fortunes()
    fortunes = data.get("fortunes", [])
    if not fortunes:
        await update.message.reply_text("هیچ فالی ثبت نشده هنوز 😅")
        return

    text = "📜 لیست فال‌های ثبت‌شده:\n\n"
    for f in fortunes[-10:][::-1]:
        text += f"🧙‍♀️ {f['user']} — {f['date']}\n"
        if f["text"]:
            text += f"💬 {f['text']}\n"
        if f["photo_id"]:
            text += f"🖼 [عکس فال ثبت شده]\n"
        text += "\n"

    await update.message.reply_text(text[:4000])
