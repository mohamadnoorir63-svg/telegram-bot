import json
import os
import random
from telegram import Update, InputFile

FILE = "jokes.json"
MEDIA_DIR = "jokes_media"

# 📁 ساخت پوشه ذخیره فایل‌ها در صورت نبود
if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)


# ========================= 💾 بارگذاری و ذخیره =========================
def load_jokes():
    if not os.path.exists(FILE):
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    with open(FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_jokes(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ========================= 😂 ذخیره جوک جدید =========================
async def save_joke(update: Update):
    data = load_jokes()
    reply = update.message.reply_to_message

    if not reply:
        return await update.message.reply_text("❗ لطفاً روی پیام جوک ریپلای کن!")

    entry = {"type": "text", "value": None}

    # ✅ ذخیره متن
    if reply.text:
        entry["type"] = "text"
        entry["value"] = reply.text.strip()

    # ✅ ذخیره عکس
    elif reply.photo:
        photo = reply.photo[-1]
        file = await photo.get_file()
        path = os.path.join(MEDIA_DIR, f"photo_{len(data)+1}.jpg")
        await file.download_to_drive(path)
        entry["type"] = "photo"
        entry["value"] = path

    # ✅ ذخیره استیکر
    elif reply.sticker:
        sticker = reply.sticker
        file = await sticker.get_file()
        path = os.path.join(MEDIA_DIR, f"sticker_{len(data)+1}.webp")
        await file.download_to_drive(path)
        entry["type"] = "sticker"
        entry["value"] = path

    # ✅ ذخیره ویدیو یا گیف
    elif reply.video or reply.animation:
        vid = reply.video or reply.animation
        file = await vid.get_file()
        path = os.path.join(MEDIA_DIR, f"video_{len(data)+1}.mp4")
        await file.download_to_drive(path)
        entry["type"] = "video"
        entry["value"] = path

    else:
        return await update.message.reply_text("❗ نوع پیام پشتیبانی نمی‌شود (فقط متن، عکس، استیکر یا ویدیو).")

    data[str(len(data) + 1)] = entry
    save_jokes(data)
    await update.message.reply_text("😂 جوک با موفقیت ذخیره شد!")


# ========================= 📜 نمایش همه جوک‌ها =========================
async def list_jokes(update: Update):
    data = load_jokes()
    if not data:
        return await update.message.reply_text("هنوز جوکی ذخیره نشده 😅")

    await update.message.reply_text(f"📚 تعداد کل جوک‌ها: {len(data)}")

    for k, v in list(data.items())[-10:]:  # فقط ۱۰ تای آخر
        t = v.get("type")
        val = v.get("value")

        try:
            if t == "text":
                await update.message.reply_text(f"😂 {val}")
            elif t == "photo":
                await update.message.reply_photo(photo=open(val, "rb"))
            elif t == "sticker":
                await update.message.reply_sticker(sticker=open(val, "rb"))
            elif t == "video":
                await update.message.reply_video(video=open(val, "rb"))
        except:
            await update.message.reply_text(f"⚠️ فایل شماره {k} پیدا نشد یا حذف شده.")
