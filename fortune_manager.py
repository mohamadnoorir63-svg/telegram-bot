import json
import os
from datetime import datetime
from telegram import Update

# 📁 مسیرها
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FORTUNE_FILE = os.path.join(BASE_DIR, "fortunes.json")
MEDIA_DIR = os.path.join(BASE_DIR, "fortunes_media")

# 📁 اطمینان از وجود پوشه مدیا
os.makedirs(MEDIA_DIR, exist_ok=True)


# 💾 مدیریت فایل فال‌ها
def load_fortunes():
    """بارگذاری فال‌ها از فایل JSON"""
    if not os.path.exists(FORTUNE_FILE):
        with open(FORTUNE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    with open(FORTUNE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_fortunes(data):
    """ذخیره فال‌ها در فایل JSON"""
    with open(FORTUNE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 🔮 ثبت فال جدید
async def save_fortune(update: Update):
    """ذخیره فال (متن، عکس، ویدیو یا استیکر) با ریپلای"""
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("❗ لطفاً روی پیام فال ریپلای کن (متن یا مدیا).")

    data = load_fortunes()
    entry = {"type": "text", "value": ""}
    new_value = None

    try:
        # 📜 فال متنی
        if reply.text or reply.caption:
            new_value = (reply.text or reply.caption).strip()
            entry["type"] = "text"
            entry["value"] = new_value

        # 🖼️ فال تصویری
        elif reply.photo:
            file = await reply.photo[-1].get_file()
            filename = f"photo_{int(datetime.now().timestamp())}.jpg"
            path = os.path.join(MEDIA_DIR, filename)
            await file.download_to_drive(path)
            entry["type"] = "photo"
            entry["value"] = path

        # 🎥 فال ویدیویی
        elif reply.video:
            file = await reply.video.get_file()
            filename = f"video_{int(datetime.now().timestamp())}.mp4"
            path = os.path.join(MEDIA_DIR, filename)
            await file.download_to_drive(path)
            entry["type"] = "video"
            entry["value"] = path

        # 😄 استیکر
        elif reply.sticker:
            file = await reply.sticker.get_file()
            filename = f"sticker_{int(datetime.now().timestamp())}.webp"
            path = os.path.join(MEDIA_DIR, filename)
            await file.download_to_drive(path)
            entry["type"] = "sticker"
            entry["value"] = path

        else:
            return await update.message.reply_text("⚠️ فقط متن، عکس، ویدیو یا استیکر پشتیبانی می‌شود.")

        # جلوگیری از ذخیره تکراری
        for v in data.values():
            if v.get("value") == entry["value"]:
                return await update.message.reply_text("😅 این فال قبلاً ذخیره شده بود!")

        # ثبت نهایی
        data[str(len(data) + 1)] = entry
        save_fortunes(data)
        await update.message.reply_text("✅ فال با موفقیت ذخیره شد!")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ذخیره فال: {e}")


# 📋 لیست فال‌ها
async def list_fortunes(update: Update):
    """نمایش آخرین 10 فال ذخیره‌شده"""
    data = load_fortunes()
    if not data:
        return await update.message.reply_text("هنوز هیچ فالی ثبت نشده 😔")

    await update.message.reply_text(f"📜 تعداد کل فال‌ها: {len(data)}")

    for k, v in list(data.items())[-10:]:  # آخرین ۱۰ فال
        t, val = v.get("type"), v.get("value")

        # اگر مسیر نسبی بود، به مطلق تبدیل کن
        if not os.path.isabs(val):
            val = os.path.join(BASE_DIR, val)

        try:
            if t == "text":
                await update.message.reply_text("🔮 " + val)

            elif t == "photo" and os.path.exists(val):
                await update.message.reply_photo(photo=open(val, "rb"), caption=f"🔮 فال {k}")

            elif t == "video" and os.path.exists(val):
                await update.message.reply_video(video=open(val, "rb"), caption=f"🔮 فال {k}")

            elif t == "sticker" and os.path.exists(val):
                await update.message.reply_sticker(sticker=open(val, "rb"))

            else:
                await update.message.reply_text(f"⚠️ فایل شماره {k} پیدا نشد یا حذف شده است.")

        except Exception as e:
            await update.message.reply_text(f"⚠️ خطا در ارسال فال {k}: {e}")
