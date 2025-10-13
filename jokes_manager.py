import json
import os
from telegram import Update

JOKES_FILE = "jokes.json"
MEDIA_DIR = "jokes_media"

# 📁 اطمینان از وجود پوشه
if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

# 💾 لود و ذخیره داده‌ها
def load_jokes():
    if not os.path.exists(JOKES_FILE):
        with open(JOKES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    with open(JOKES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_jokes(data):
    with open(JOKES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 😂 ذخیره جوک جدید
async def save_joke(update: Update):
    """ذخیره جوک با پشتیبانی از متن، عکس، ویدیو یا استیکر"""
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("❗ لطفاً روی پیام جوک ریپلای کن (متن یا مدیا).")

    data = load_jokes()
    entry = {"type": "text", "value": ""}

    try:
        if reply.text:
            entry["type"] = "text"
            entry["value"] = reply.text.strip()

        elif reply.caption:
            entry["type"] = "text"
            entry["value"] = reply.caption.strip()

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

        data[str(len(data) + 1)] = entry
        save_jokes(data)
        await update.message.reply_text("✅ جوک جدید با موفقیت ذخیره شد!")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ذخیره جوک: {e}")

# 📋 نمایش لیست جوک‌ها
async def list_jokes(update: Update):
    """نمایش آخرین جوک‌های ذخیره‌شده"""
    data = load_jokes()
    if not data:
        return await update.message.reply_text("هیچ جوکی هنوز ثبت نشده 😅")

    await update.message.reply_text(f"📜 تعداد کل جوک‌ها: {len(data)}")

    for k, v in list(data.items())[-10:]:
        t, val = v.get("type"), v.get("value")
        try:
            if t == "text":
                await update.message.reply_text("😂 " + val)
            elif t == "photo" and os.path.exists(val):
                with open(val, "rb") as f:
                    await update.message.reply_photo(photo=f)
            elif t == "video" and os.path.exists(val):
                with open(val, "rb") as f:
                    await update.message.reply_video(video=f)
            elif t == "sticker" and os.path.exists(val):
                with open(val, "rb") as f:
                    await update.message.reply_sticker(sticker=f)
            else:
                await update.message.reply_text(f"⚠️ فایل جوک شماره {k} پیدا نشد یا حذف شده.")
        except Exception as e:
            await update.message.reply_text(f"⚠️ خطا در ارسال جوک {k}: {e}")
