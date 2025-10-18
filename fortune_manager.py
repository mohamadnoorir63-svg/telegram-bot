import json
import os
from datetime import datetime
from telegram import Update, InputFile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FORTUNE_FILE = os.path.join(BASE_DIR, "fortunes.json")
MEDIA_DIR = os.path.join(BASE_DIR, "fortunes_media")

os.makedirs(MEDIA_DIR, exist_ok=True)

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
        # 📜 متن
        if reply.text or reply.caption:
            new_value = (reply.text or reply.caption).strip()
            entry["type"] = "text"
            entry["value"] = new_value

        # 🖼️ عکس
        elif reply.photo:
            file = await reply.photo[-1].get_file()
            # لینک دائمی تلگرام (بهتر از مسیر محلی)
            entry["type"] = "photo"
            entry["value"] = file.file_path

        # 🎥 ویدیو
        elif reply.video:
            file = await reply.video.get_file()
            entry["type"] = "video"
            entry["value"] = file.file_path

        # 😄 استیکر
        elif reply.sticker:
            file = await reply.sticker.get_file()
            entry["type"] = "sticker"
            entry["value"] = file.file_path

        else:
            return await update.message.reply_text("⚠️ فقط متن، عکس، ویدیو یا استیکر پشتیبانی می‌شود.")

        # جلوگیری از تکرار
        for v in data.values():
            if v.get("value") == entry["value"]:
                return await update.message.reply_text("😅 این فال قبلاً ذخیره شده بود!")

        data[str(len(data) + 1)] = entry
        save_fortunes(data)
        await update.message.reply_text("✅ فال با موفقیت ذخیره شد!")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ذخیره فال: {e}")


# 📋 نمایش فال‌ها
async def list_fortunes(update: Update):
    data = load_fortunes()
    if not data:
        return await update.message.reply_text("هنوز هیچ فالی ثبت نشده 😔")

    await update.message.reply_text(f"📜 تعداد کل فال‌ها: {len(data)}")

    for k, v in list(data.items())[-10:]:
        t, val = v.get("type"), v.get("value")

        try:
            if t == "text":
                await update.message.reply_text(f"🔮 {val}")

            elif t == "photo":
                if val.startswith("http"):
                    await update.message.reply_photo(photo=val, caption=f"🔮 فال {k}")
                elif os.path.exists(val):
                    await update.message.reply_photo(photo=InputFile(val), caption=f"🔮 فال {k}")
                else:
                    await update.message.reply_text(f"🔮 فال {k}\n(📷 تصویر در دسترس نیست)\n{val}")

            elif t == "video":
                if val.startswith("http"):
                    await update.message.reply_video(video=val, caption=f"🎥 فال {k}")
                elif os.path.exists(val):
                    await update.message.reply_video(video=InputFile(val), caption=f"🎥 فال {k}")
                else:
                    await update.message.reply_text(f"🎥 فال {k} (ویدیو یافت نشد)")

            elif t == "sticker":
                if val.startswith("http"):
                    await update.message.reply_sticker(sticker=val)
                elif os.path.exists(val):
                    await update.message.reply_sticker(sticker=InputFile(val))
                else:
                    await update.message.reply_text(f"🌀 فال {k} (استیکر در دسترس نیست)")

            else:
                await update.message.reply_text(f"⚠️ فال {k} شناسایی نشد.")

        except Exception as e:
            await update.message.reply_text(f"⚠️ خطا در ارسال فال {k}: {e}")
