import json
import os
from telegram import Update

FORTUNE_FILE = "fortunes.json"
MEDIA_DIR = "fortunes_media"

# 📁 ساخت پوشه
if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)


# 💾 فایل فال‌ها
def load_fortunes():
    if not os.path.exists(FORTUNE_FILE):
        with open(FORTUNE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    with open(FORTUNE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_fortunes(data):
    with open(FORTUNE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 🔮 ذخیره فال جدید
async def save_fortune(update: Update):
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("❗ لطفاً روی پیام فال ریپلای کن (متن یا مدیا).")

    data = load_fortunes()
    entry = {"type": "text", "value": ""}
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
            entry["type"] = "photo"
            entry["value"] = path
        elif reply.video:
            file = await reply.video.get_file()
            path = os.path.join(MEDIA_DIR, f"video_{len(data)+1}.mp4")
            await file.download_to_drive(path)
            entry["type"] = "video"
            entry["value"] = path
        elif reply.sticker:
            file = await reply.sticker.get_file()
            path = os.path.join(MEDIA_DIR, f"sticker_{len(data)+1}.webp")
            await file.download_to_drive(path)
            entry["type"] = "sticker"
            entry["value"] = path
        else:
            return await update.message.reply_text("⚠️ فقط متن، عکس، ویدیو یا استیکر پشتیبانی می‌شود.")

        # ضدتکرار
        for v in data.values():
            if v.get("value") == entry["value"]:
                return await update.message.reply_text("🔁 این فال قبلاً ثبت شده بود!")

        data[str(len(data) + 1)] = entry
        save_fortunes(data)
        await update.message.reply_text("✅ فال با موفقیت ذخیره شد!")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ذخیره فال: {e}")


# 📋 نمایش لیست فال‌ها
async def list_fortunes(update: Update):
    data = load_fortunes()
    if not data:
        return await update.message.reply_text("هیچ فالی ثبت نشده 😔")

    await update.message.reply_text(f"📜 تعداد کل فال‌ها: {len(data)}")

    for k, v in list(data.items())[-10:]:
        t, val = v.get("type"), v.get("value")
        try:
            if t == "text":
                await update.message.reply_text("🔮 " + val)
            elif t == "photo" and os.path.exists(val):
                await update.message.reply_photo(photo=open(val, "rb"))
            elif t == "sticker" and os.path.exists(val):
                await update.message.reply_sticker(sticker=open(val, "rb"))
            elif t == "video" and os.path.exists(val):
                await update.message.reply_video(video=open(val, "rb"))
            else:
                await update.message.reply_text(f"⚠️ فایل شماره {k} پیدا نشد.")
        except Exception as e:
            await update.message.reply_text(f"⚠️ خطا در ارسال فال {k}: {e}")
