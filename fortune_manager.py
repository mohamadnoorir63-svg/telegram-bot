import json
import os
import random
from telegram import InputFile

# ======================= 📁 فایل داده =======================

FORTUNES_FILE = "fortunes.json"

def _init_file():
    if not os.path.exists(FORTUNES_FILE):
        with open(FORTUNES_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

def _load():
    _init_file()
    with open(FORTUNES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save(data):
    with open(FORTUNES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================= 🔮 ثبت فال =======================

async def save_fortune(update):
    """ذخیره فال از ریپلی (متن یا عکس)"""
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("❗ باید روی پیامی ریپلای بزنی تا فال رو ذخیره کنم.")

    fortunes = _load()
    fortune_entry = {}

    if reply.text:
        fortune_entry["type"] = "text"
        fortune_entry["content"] = reply.text.strip()
    elif reply.photo:
        file_id = reply.photo[-1].file_id
        fortune_entry["type"] = "photo"
        fortune_entry["content"] = file_id
        if reply.caption:
            fortune_entry["caption"] = reply.caption.strip()
    else:
        return await update.message.reply_text("❗ فقط عکس یا متن می‌تونم ذخیره کنم!")

    fortunes.append(fortune_entry)
    _save(fortunes)
    await update.message.reply_text("🔮 فال جدید ذخیره شد!")

# ======================= 📜 لیست فال‌ها =======================

async def list_fortunes(update):
    fortunes = _load()
    if not fortunes:
        return await update.message.reply_text("هنوز هیچ فالی ذخیره نکردم 😅")

    fortune = random.choice(fortunes)
    if fortune["type"] == "text":
        await update.message.reply_text(f"🔮 {fortune['content']}")
    elif fortune["type"] == "photo":
        caption = fortune.get("caption", "🔮 فال تصویری امروزت!")
        await update.message.reply_photo(photo=fortune["content"], caption=caption)
