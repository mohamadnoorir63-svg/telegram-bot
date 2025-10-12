import json
import os
from telegram import Update, InputFile
import random

FILE = "jokes.json"

def load_jokes():
    if not os.path.exists(FILE):
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_jokes(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def save_joke(update: Update):
    """ذخیره جوک از روی پیام ریپلای (متن، عکس، استیکر یا ویدیو)"""
    if not update.message.reply_to_message:
        return await update.message.reply_text("❗ باید روی پیام جوک ریپلای بزنی.")

    msg = update.message.reply_to_message
    data = load_jokes()
    joke_id = str(len(data) + 1)

    if msg.text:
        data[joke_id] = {"type": "text", "content": msg.text.strip()}
        await update.message.reply_text("😂 جوک متنی ذخیره شد!")
    elif msg.photo:
        file_id = msg.photo[-1].file_id
        data[joke_id] = {"type": "photo", "content": file_id}
        await update.message.reply_text("🖼 جوک تصویری ذخیره شد!")
    elif msg.sticker:
        file_id = msg.sticker.file_id
        data[joke_id] = {"type": "sticker", "content": file_id}
        await update.message.reply_text("😜 جوک استیکری ذخیره شد!")
    elif msg.video:
        file_id = msg.video.file_id
        data[joke_id] = {"type": "video", "content": file_id}
        await update.message.reply_text("🎥 جوک ویدیویی ذخیره شد!")
    else:
        return await update.message.reply_text("❌ نوع این پیام پشتیبانی نمی‌شود (فقط متن، عکس، ویدیو یا استیکر).")

    save_jokes(data)

async def list_jokes(update: Update):
    """نمایش فهرست جوک‌ها (فقط متنی)"""
    data = load_jokes()
    if not data:
        return await update.message.reply_text("هنوز جوکی ثبت نشده 😅")

    lines = []
    for k, v in data.items():
        if v["type"] == "text":
            lines.append(f"{k}. {v['content']}")
        else:
            lines.append(f"{k}. [{v['type']}]")

    text = "\n\n".join(lines)
    if len(text) > 4000:
        text = text[:3990] + "..."
    await update.message.reply_text(f"😂 لیست جوک‌ها:\n\n{text}")

async def send_random_joke(update: Update):
    """ارسال جوک تصادفی با تشخیص نوع"""
    data = load_jokes()
    if not data:
        return await update.message.reply_text("هنوز جوکی ذخیره نشده 😅")

    joke = random.choice(list(data.values()))
    if joke["type"] == "text":
        await update.message.reply_text(f"😂 {joke['content']}")
    elif joke["type"] == "photo":
        await update.message.reply_photo(joke["content"], caption="😂 جوک تصویری!")
    elif joke["type"] == "sticker":
        await update.message.reply_sticker(joke["content"])
    elif joke["type"] == "video":
        await update.message.reply_video(joke["content"], caption="😂 جوک ویدیویی!")
