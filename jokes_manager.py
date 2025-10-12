import json
import os
import random
from telegram import InputFile

# ======================= 📁 فایل داده =======================

JOKES_FILE = "jokes.json"

def _init_file():
    if not os.path.exists(JOKES_FILE):
        with open(JOKES_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

def _load():
    _init_file()
    with open(JOKES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save(data):
    with open(JOKES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================= 😂 ثبت جوک =======================

async def save_joke(update):
    """ذخیره جوک از ریپلی (متن یا عکس)"""
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("❗ باید روی پیامی ریپلای بزنی تا ذخیره کنم.")

    jokes = _load()
    joke_entry = {}

    if reply.text:
        joke_entry["type"] = "text"
        joke_entry["content"] = reply.text.strip()
    elif reply.photo:
        file_id = reply.photo[-1].file_id
        joke_entry["type"] = "photo"
        joke_entry["content"] = file_id
        if reply.caption:
            joke_entry["caption"] = reply.caption.strip()
    else:
        return await update.message.reply_text("❗ فقط عکس یا متن می‌تونم ذخیره کنم!")

    jokes.append(joke_entry)
    _save(jokes)
    await update.message.reply_text("😂 جوک جدید ذخیره شد!")

# ======================= 📋 لیست جوک‌ها =======================

async def list_jokes(update):
    jokes = _load()
    if not jokes:
        return await update.message.reply_text("هیچ جوکی هنوز ذخیره نکردم 😅")

    # یکی رو تصادفی بفرست
    joke = random.choice(jokes)
    if joke["type"] == "text":
        await update.message.reply_text(f"😂 {joke['content']}")
    elif joke["type"] == "photo":
        caption = joke.get("caption", "😂 جوک تصویری!")
        await update.message.reply_photo(photo=joke["content"], caption=caption)
