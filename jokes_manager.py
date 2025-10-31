import json
import os
from telegram import Update

# 📁 تنظیم مسیرهای مطلق
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JOKES_FILE = os.path.join(BASE_DIR, "jokes.json")
MEDIA_DIR = os.path.join(BASE_DIR, "jokes_media")

# 📁 ساخت پوشه برای ذخیره فایل‌ها
if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)


# 💾 مدیریت فایل جوک‌ها
def load_jokes():
    """بارگذاری جوک‌ها از فایل"""
    if not os.path.exists(JOKES_FILE):
        with open(JOKES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    with open(JOKES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_jokes(data):
    """ذخیره جوک‌ها در فایل"""
    with open(JOKES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 😂 ثبت جوک جدید
async def save_joke(update: Update):
    """ذخیره جوک (متن، عکس، ویدیو یا استیکر) با ریپلای"""
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("❗ لطفاً روی پیام جوک ریپلای کن (متن یا مدیا).")

    data = load_jokes()
    entry = {"type": "text", "value": ""}
    new_value = None

    try:
        # نوع پیام را تشخیص بده
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

        # جلوگیری از تکرار
        for v in data.values():
            if v.get("value") == entry["value"]:
                return await update.message.reply_text("😅 این جوک قبلاً ذخیره شده بود!")

        data[str(len(data) + 1)] = entry
        save_jokes(data)
        await update.message.reply_text("✅ جوک با موفقیت ذخیره شد!")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ذخیره جوک: {e}")


# 📋 نمایش لیست جوک‌ ها
async def list_jokes(update: Update):
    """نمایش آخرین 10 جوک ذخیره‌شده"""
    data = load_jokes()
    if not data:
        return await update.message.reply_text("هیچ جوکی ثبت نشده 😅")

    await update.message.reply_text(f"📜 تعداد کل جوک‌ها: {len(data)}")

    for k, v in list(data.items())[-10:]:  # آخرین 10 تا
        t, val = v.get("type"), v.get("value")

        # اطمینان از مسیر مطلق
        if not os.path.isabs(val):
            val = os.path.join(BASE_DIR, val)

        try:
            if t == "text":
                await update.message.reply_text("😂 " + val)

            elif t == "photo" and os.path.exists(val):
                await update.message.reply_photo(photo=open(val, "rb"))

            elif t == "sticker" and os.path.exists(val):
                await update.message.reply_sticker(sticker=open(val, "rb"))

            elif t == "video" and os.path.exists(val):
                await update.message.reply_video(video=open(val, "rb"))

            else:
                await update.message.reply_text(f"⚠️ فایل شماره {k} پیدا نشد یا حذف شده است.")

        except Exception as e:
            await update.message.reply_text(f"⚠️ خطا در ارسال جوک {k}: {e}")
