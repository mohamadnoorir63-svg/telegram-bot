# fortune_manager.py
import json
import os
import random
from datetime import datetime
from urllib.parse import urlparse
from telegram import Update, InputFile
from telegram.ext import ContextTypes

# ========================= مسیرها و آماده‌سازی =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FORTUNE_FILE = os.path.join(BASE_DIR, "fortunes.json")
MEDIA_DIR = os.path.join(BASE_DIR, "fortunes_media")
os.makedirs(MEDIA_DIR, exist_ok=True)
SENT_MAPPING_FILE = os.path.join(BASE_DIR, "sent_fortunes.json")

# ========================= ابزارهای کمکی =========================
def _is_valid_url(val: str) -> bool:
    if not isinstance(val, str) or not val.strip():
        return False
    if not (val.startswith("http://") or val.startswith("https://")):
        return False
    u = urlparse(val)
    return bool(u.scheme and u.netloc)

def _abs_media_path(val: str) -> str:
    if not val:
        return val
    if _is_valid_url(val):
        return val
    return val if os.path.isabs(val) else os.path.join(BASE_DIR, val)

def _load_json(path: str, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default

def load_fortunes():
    return _load_json(FORTUNE_FILE, {})

def save_fortunes(data):
    with open(FORTUNE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ========================= ارسال مدیا ایمن =========================
async def send_media(update: Update, media_type: str, val: str, k: str):
    val = _abs_media_path(val)
    if _is_valid_url(val):
        if media_type == "photo":
            msg = await update.message.reply_photo(photo=val, caption=f"🔮 فال شماره {k}")
        elif media_type == "video":
            msg = await update.message.reply_video(video=val, caption=f"🎥 فال شماره {k}")
        elif media_type == "sticker":
            msg = await update.message.reply_sticker(sticker=val)
        else:
            msg = await update.message.reply_text(f"⚠️ نوع مدیا نامعتبر: {media_type}")
    else:
        if not os.path.exists(val):
            return await update.message.reply_text(f"⚠️ فایل لوکال پیدا نشد: {val}")
        file = InputFile(val)
        if media_type == "photo":
            msg = await update.message.reply_photo(photo=file, caption=f"🔮 فال شماره {k}")
        elif media_type == "video":
            msg = await update.message.reply_video(video=file, caption=f"🎥 فال شماره {k}")
        elif media_type == "sticker":
            msg = await update.message.reply_sticker(sticker=file)
        else:
            msg = await update.message.reply_text(f"⚠️ نوع مدیا نامعتبر: {media_type}")
    return msg

# ========================= ثبت فال (ریپلای) =========================
async def save_fortune(update: Update):
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("❗ لطفاً روی پیام فال ریپلای کن.")

    data = load_fortunes()
    entry = {"type": "text", "value": ""}

    try:
        if reply.text or reply.caption:
            val = (reply.text or reply.caption).strip()
            if not val:
                return await update.message.reply_text("⚠️ متن خالی است.")
            entry["type"] = "text"
            entry["value"] = val

        elif reply.photo:
            file = await reply.photo[-1].get_file()
            filename = f"photo_{int(datetime.now().timestamp())}.jpg"
            path = os.path.join(MEDIA_DIR, filename)
            await file.download_to_drive(path)
            entry["type"] = "photo"
            entry["value"] = os.path.relpath(path, BASE_DIR)

        elif reply.video:
            file = await reply.video.get_file()
            filename = f"video_{int(datetime.now().timestamp())}.mp4"
            path = os.path.join(MEDIA_DIR, filename)
            await file.download_to_drive(path)
            entry["type"] = "video"
            entry["value"] = os.path.relpath(path, BASE_DIR)

        elif reply.sticker:
            file = await reply.sticker.get_file()
            filename = f"sticker_{int(datetime.now().timestamp())}.webp"
            path = os.path.join(MEDIA_DIR, filename)
            await file.download_to_drive(path)
            entry["type"] = "sticker"
            entry["value"] = os.path.relpath(path, BASE_DIR)

        else:
            return await update.message.reply_text("⚠️ فقط متن، عکس، ویدیو یا استیکر پشتیبانی می‌شود.")

        for v in data.values():
            if v.get("type") == entry["type"] and v.get("value") == entry["value"]:
                return await update.message.reply_text("😅 این فال قبلاً ذخیره شده بود!")

        data[str(len(data) + 1)] = entry
        save_fortunes(data)
        await update.message.reply_text("✅ فال با موفقیت ذخیره شد!")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ذخیره فال: {e}")

# ========================= حذف پیشرفته فال با ریپلای =========================
async def delete_sent_fortune(update: Update):
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("❗ لطفاً روی پیام فال ریپلای کن.")

    sent_mapping = _load_json(SENT_MAPPING_FILE, {})

    msg_id = str(reply.message_id)
    if msg_id not in sent_mapping:
        return await update.message.reply_text("⚠️ این پیام مربوط به فال نیست یا قبلاً حذف شده.")

    k = sent_mapping.pop(msg_id)
    data = load_fortunes()
    deleted = data.pop(k, None)
    save_fortunes(data)

    # حذف رسانه
    if deleted:
        val = _abs_media_path(deleted.get("value", ""))
        if val and os.path.exists(val) and deleted.get("type") != "text":
            os.remove(val)

    # ذخیره mapping به‌روز
    save_fortunes(sent_mapping)  # برای اطمینان mapping هم ذخیره شود
    with open(SENT_MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(sent_mapping, f, ensure_ascii=False, indent=2)

    await update.message.reply_text("🗑️ فال با موفقیت حذف شد ✅")

# ========================= ارسال فال تصادفی =========================
async def send_random_fortune(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_fortunes()
    if not data:
        return await update.message.reply_text("📭 هنوز فالی ذخیره نشده 😔")

    # انتخاب فال تصادفی
    all_keys = list(data.keys())
    k = random.choice(all_keys)
    v = data[k]
    t = v.get("type", "text").strip()
    raw = (v.get("value") or "").strip()
    if not raw:
        return await update.message.reply_text("⚠️ فال نامعتبر یا خالی بود.")

    sent_message = await send_media(update, t, raw, k)

    # ذخیره mapping پیام => کلید فال
    sent_mapping = _load_json(SENT_MAPPING_FILE, {})
    sent_mapping[str(sent_message.message_id)] = k
    with open(SENT_MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(sent_mapping, f, ensure_ascii=False, indent=2)
