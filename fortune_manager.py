import json
import os
import random
from telegram import Update

FORTUNE_FILE = "fortunes.json"
MEDIA_DIR = "fortunes_media"

if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

def load_fortunes():
    if not os.path.exists(FORTUNE_FILE):
        with open(FORTUNE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    with open(FORTUNE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_fortunes(data):
    with open(FORTUNE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 🔮 ذخیره فال با دسته‌بندی
async def save_fortune(update: Update):
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("❗ لطفاً روی پیام فال ریپلای کن (متن یا مدیا).")

    args = update.message.text.split(" ", 1)
    tag = args[1].strip() if len(args) > 1 else "عمومی"

    data = load_fortunes()
    entry = {"type": "text", "value": "", "tag": tag}
    new_value = None

    try:
        if reply.text:
            new_value = reply.text.strip()
            entry["type"] = "text"
            entry["value"] = new_value
        elif reply.caption:
            new_value = reply.caption.strip()
            entry["type"] = "text"
            entry["value"] = new_value
        elif reply.photo:
            file = await reply.photo[-1].get_file()
            path = os.path.join(MEDIA_DIR, f"photo_{len(data)+1}.jpg")
            await file.download_to_drive(path)
            new_value = path
            entry["type"] = "photo"
            entry["value"] = path
        elif reply.video:
            file = await reply.video.get_file()
            path = os.path.join(MEDIA_DIR, f"video_{len(data)+1}.mp4")
            await file.download_to_drive(path)
            new_value = path
            entry["type"] = "video"
            entry["value"] = path
        elif reply.sticker:
            file = await reply.sticker.get_file()
            path = os.path.join(MEDIA_DIR, f"sticker_{len(data)+1}.webp")
            await file.download_to_drive(path)
            new_value = path
            entry["type"] = "sticker"
            entry["value"] = path
        else:
            return await update.message.reply_text("⚠️ فقط متن، عکس، ویدیو یا استیکر پشتیبانی می‌شود.")

        for v in data.values():
            if v.get("value") == new_value:
                return await update.message.reply_text("🔁 این فال قبلاً ذخیره شده بود!")

        data[str(len(data) + 1)] = entry
        save_fortunes(data)
        await update.message.reply_text(f"✅ فال جدید در دسته '{tag}' ذخیره شد!")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ذخیره فال: {e}")

# 📜 فال تصادفی از دسته خاص
async def random_fortune(update: Update, tag=None):
    data = load_fortunes()
    if not data:
        return await update.message.reply_text("هیچ فالی هنوز ثبت نشده 😔")

    fortunes = list(data.values())
    if tag:
        fortunes = [f for f in fortunes if f.get("tag") == tag]
        if not fortunes:
            return await update.message.reply_text(f"🔍 فالی در دسته '{tag}' پیدا نشد!")

    fortune = random.choice(fortunes)
    t, val = fortune.get("type"), fortune.get("value")

    try:
        if t == "text":
            await update.message.reply_text(f"🔮 ({fortune.get('tag')})\n{val}")
        elif t == "photo" and os.path.exists(val):
            with open(val, "rb") as f:
                await update.message.reply_photo(photo=f, caption=f"🔮 ({fortune.get('tag')})")
        elif t == "video" and os.path.exists(val):
            with open(val, "rb") as f:
                await update.message.reply_video(video=f, caption=f"🔮 ({fortune.get('tag')})")
        elif t == "sticker" and os.path.exists(val):
            with open(val, "rb") as f:
                await update.message.reply_sticker(sticker=f)
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ارسال فال: {e}")
