import json
import os
import random
from telegram import Update

FILE = "fortunes.json"

def load_fortunes():
    if not os.path.exists(FILE):
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_fortunes(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def save_fortune(update: Update):
    """ذخیره فال از روی پیام ریپلای (متن، عکس، ویدیو یا استیکر)"""
    if not update.message.reply_to_message:
        return await update.message.reply_text("❗ باید روی پیام فال ریپلای بزنی.")

    msg = update.message.reply_to_message
    data = load_fortunes()
    fid = str(len(data) + 1)

    if msg.text:
        data[fid] = {"type": "text", "content": msg.text.strip()}
        await update.message.reply_text("🔮 فال متنی ذخیره شد!")
    elif msg.photo:
        file_id = msg.photo[-1].file_id
        data[fid] = {"type": "photo", "content": file_id}
        await update.message.reply_text("🖼 فال تصویری ذخیره شد!")
    elif msg.sticker:
        file_id = msg.sticker.file_id
        data[fid] = {"type": "sticker", "content": file_id}
        await update.message.reply_text("✨ فال استیکری ذخیره شد!")
    elif msg.video:
        file_id = msg.video.file_id
        data[fid] = {"type": "video", "content": file_id}
        await update.message.reply_text("🎥 فال ویدیویی ذخیره شد!")
    else:
        return await update.message.reply_text("❌ نوع این پیام پشتیبانی نمی‌شود (فقط متن، عکس، ویدیو یا استیکر).")

    save_fortunes(data)

async def list_fortunes(update: Update):
    """نمایش فهرست فال‌ها (فقط متنی)"""
    data = load_fortunes()
    if not data:
        return await update.message.reply_text("هنوز فالی ثبت نشده 😅")

    lines = []
    for k, v in data.items():
        if v["type"] == "text":
            lines.append(f"{k}. {v['content']}")
        else:
            lines.append(f"{k}. [{v['type']}]")

    text = "\n\n".join(lines)
    if len(text) > 4000:
        text = text[:3990] + "..."
    await update.message.reply_text(f"🔮 لیست فال‌ها:\n\n{text}")

async def send_random_fortune(update: Update):
    """ارسال فال تصادفی با تشخیص نوع"""
    data = load_fortunes()
    if not data:
        return await update.message.reply_text("هنوز فالی ذخیره نشده 😅")

    fortune = random.choice(list(data.values()))
    if fortune["type"] == "text":
        await update.message.reply_text(f"🔮 {fortune['content']}")
    elif fortune["type"] == "photo":
        await update.message.reply_photo(fortune["content"], caption="🔮 فال تصویری!")
    elif fortune["type"] == "sticker":
        await update.message.reply_sticker(fortune["content"])
    elif fortune["type"] == "video":
        await update.message.reply_video(fortune["content"], caption="🔮 فال ویدیویی!")
