import json
import os
from telegram import Update

JOKES_FILE = "jokes.json"
MEDIA_DIR = "jokes_media"

# 📁 ساخت پوشه‌ها در صورت نیاز
if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

# 💾 مدیریت فایل جوک‌ها
def load_jokes():
    if not os.path.exists(JOKES_FILE):
        with open(JOKES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    with open(JOKES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_jokes(data):
    with open(JOKES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 😂 ثبت جوک با تگ و ضدتکرار
async def save_joke(update: Update):
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("❗ لطفاً روی پیام جوک ریپلای کن (متن یا مدیا).")

    args = update.message.text.split(" ", 1)
    tag = args[1].strip() if len(args) > 1 else "عمومی"

    data = load_jokes()
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

        # جلوگیری از تکرار
        for v in data.values():
            if v.get("value") == new_value:
                return await update.message.reply_text("😅 این جوک قبلاً ذخیره شده بود!")

        data[str(len(data) + 1)] = entry
        save_jokes(data)
        await update.message.reply_text(f"✅ جوک جدید در دسته '{tag}' ذخیره شد!")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ذخیره جوک: {e}")


# 📋 لیست جوک‌ها (عمومی یا بر اساس تگ)
async def list_jokes(update: Update):
    text = update.message.text.strip()
    args = text.split(" ", 1)
    tag_filter = args[1].strip() if len(args) > 1 else None

    data = load_jokes()
    if not data:
        return await update.message.reply_text("هیچ جوکی هنوز ثبت نشده 😅")

    jokes = list(data.items())
    if tag_filter:
        jokes = [j for j in jokes if j[1].get("tag") == tag_filter]
        if not jokes:
            return await update.message.reply_text(f"⚠️ جوکی در دسته '{tag_filter}' پیدا نشد!")

    await update.message.reply_text(f"📜 تعداد جوک‌های{' '+tag_filter if tag_filter else ''}: {len(jokes)}")

    for k, v in jokes[-10:]:
        t, val = v.get("type"), v.get("value")
        try:
            if t == "text":
                await update.message.reply_text(f"😂 ({v.get('tag')})\n{val}")
            elif t == "photo" and os.path.exists(val):
                with open(val, "rb") as f:
                    await update.message.reply_photo(photo=f, caption=f"😂 ({v.get('tag')})")
            elif t == "video" and os.path.exists(val):
                with open(val, "rb") as f:
                    await update.message.reply_video(video=f, caption=f"😂 ({v.get('tag')})")
            elif t == "sticker" and os.path.exists(val):
                with open(val, "rb") as f:
                    await update.message.reply_sticker(sticker=f)
        except Exception as e:
            await update.message.reply_text(f"⚠️ خطا در نمایش جوک {k}: {e}")
