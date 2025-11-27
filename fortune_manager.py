# fortune_manager.py

import os
import json
import uuid
import aiohttp
from datetime import datetime
from urllib.parse import urlparse
from telegram import Update, InputFile
from telegram.ext import ContextTypes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FORTUNE_FILE = os.path.join(BASE_DIR, "fortunes.json")
MEDIA_DIR = os.path.join(BASE_DIR, "fortunes_media")
os.makedirs(MEDIA_DIR, exist_ok=True)

MAX_FORTUNES = 100

# ========================= ابزارهای کمکی =========================

def _is_valid_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    if not url.lower().startswith(("http://", "https://")):
        return False
    p = urlparse(url)
    return bool(p.scheme and p.netloc)

def _abs_path(val: str) -> str:
    if not val:
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

# ========================= دانلود URL =========================

async def download_url(url: str, filename: str) -> str:
    path = os.path.join(MEDIA_DIR, filename)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise ValueError(f"⚠️ دانلود فایل از URL ناموفق بود: {url}")
            with open(path, "wb") as f:
                f.write(await resp.read())
    return path

# ========================= ارسال مدیا =========================

async def send_media(update: Update, media_type: str, val: str, k: str):
    try:
        # اگر URL است، ابتدا دانلود کن
        if _is_valid_url(val):
            ext = os.path.splitext(val)[1] or ""
            filename = f"{media_type}_{uuid.uuid4()}{ext}"
            val = await download_url(val, filename)

        val = _abs_path(val)
        if not os.path.exists(val):
            return await update.message.reply_text(f"⚠️ فایل پیدا نشد: {val}")

        file = InputFile(val)
        if media_type == "photo":
            await update.message.reply_photo(photo=file, caption=f"🔮 فال شماره {k}")
        elif media_type == "video":
            await update.message.reply_video(video=file, caption=f"🎥 فال شماره {k}")
        elif media_type == "sticker":
            await update.message.reply_sticker(sticker=file)
        else:  # متن
            await update.message.reply_text(val)
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در پردازش فایل: {e}")

# ========================= ثبت فال =========================

async def save_fortune(update: Update):
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("❗ لطفاً روی پیام فال ریپلای کن.")

    data = load_fortunes()
    entry = {"type": "text", "value": ""}

    try:
        if reply.text or reply.caption:
            entry["type"] = "text"
            entry["value"] = (reply.text or reply.caption).strip()
        elif reply.photo:
            file = await reply.photo[-1].get_file()
            filename = f"photo_{uuid.uuid4()}.jpg"
            path = os.path.join(MEDIA_DIR, filename)
            await file.download_to_drive(path)
            entry["type"] = "photo"
            entry["value"] = os.path.relpath(path, BASE_DIR)
        elif reply.video:
            file = await reply.video.get_file()
            filename = f"video_{uuid.uuid4()}.mp4"
            path = os.path.join(MEDIA_DIR, filename)
            await file.download_to_drive(path)
            entry["type"] = "video"
            entry["value"] = os.path.relpath(path, BASE_DIR)
        elif reply.sticker:
            file = await reply.sticker.get_file()
            filename = f"sticker_{uuid.uuid4()}.webp"
            path = os.path.join(MEDIA_DIR, filename)
            await file.download_to_drive(path)
            entry["type"] = "sticker"
            entry["value"] = os.path.relpath(path, BASE_DIR)
        else:
            return await update.message.reply_text("⚠️ فقط متن، عکس، ویدیو یا استیکر پشتیبانی می‌شود.")

        # جلوگیری از تکراری بودن
        for v in data.values():
            if v["type"] == entry["type"] and v["value"] == entry["value"]:
                return await update.message.reply_text("😅 این فال قبلاً ذخیره شده بود!")

        if len(data) >= MAX_FORTUNES:
            oldest = sorted(data.keys())[0]
            old_val = _abs_path(data[oldest]["value"])
            if os.path.exists(old_val) and not _is_valid_url(old_val):
                os.remove(old_val)
            data.pop(oldest)

        key = str(uuid.uuid4())
        data[key] = entry
        save_fortunes(data)

        # ارسال همزمان بعد از ذخیره
        await send_media(update, entry["type"], entry["value"], key)

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ذخیره فال: {e}")

# ========================= حذف فال =========================

async def delete_fortune(update: Update):
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("❗ لطفاً روی پیام فال ریپلای کن.")

    data = load_fortunes()
    if not data:
        return await update.message.reply_text("📂 هیچ فالی ذخیره نشده.")

    delete_type, delete_val = None, None
    if reply.text or reply.caption:
        delete_type = "text"
        delete_val = (reply.text or reply.caption).strip()
    elif reply.photo:
        delete_type = "photo"
    elif reply.video:
        delete_type = "video"
    elif reply.sticker:
        delete_type = "sticker"
    else:
        return await update.message.reply_text("⚠️ نوع پیام قابل شناسایی نیست.")

    target_key = None
    for k, v in data.items():
        if v["type"] == delete_type:
            if delete_type == "text":
                if v["value"] == delete_val:
                    target_key = k
                    break
            else:
                target_key = k
                break

    if not target_key:
        return await update.message.reply_text("⚠️ فال موردنظر پیدا نشد.")

    real_path = _abs_path(data[target_key]["value"])
    if os.path.exists(real_path) and not _is_valid_url(real_path):
        os.remove(real_path)

    data.pop(target_key)
    save_fortunes(data)
    await update.message.reply_text("🗑️ فال حذف شد.")

# ========================= ارسال تصادفی =========================

async def send_random_fortune(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_fortunes()
    if not data:
        return await update.message.reply_text("📭 هنوز فالی ذخیره نشده.")

    sent_file = os.path.join(BASE_DIR, "sent_fortunes.json")
    sent = _load_json(sent_file, [])
    keys = list(data.keys())
    remaining = [k for k in keys if k not in sent]

    if not remaining:
        sent = []
        remaining = keys.copy()

    last = sent[-1] if sent else None
    options = [k for k in remaining if k != last] or remaining
    k = random.choice(options)
    sent.append(k)

    with open(sent_file, "w", encoding="utf-8") as f:
        json.dump(sent, f, ensure_ascii=False, indent=2)

    await send_media(update, data[k]["type"], data[k]["value"], k)

# ========================= لیست فال‌ها =========================

async def list_fortunes(update: Update):
    data = load_fortunes()
    if not data:
        return await update.message.reply_text("😔 هنوز فالی ثبت نشده.")

    await update.message.reply_text(
        f"📜 تعداد کل فال‌ها: {len(data)}\n\n"
        "برای حذف هر فال روی پیام ریپلای کرده بنویسید: حذف فال 🗑️"
    )

    shown = 0
    for k in sorted(data.keys())[-10:]:
        try:
            await send_media(update, data[k]["type"], data[k]["value"], k)
            shown += 1
        except Exception as e:
            print(f"[List Fortune Error] {k}: {e}")

    if shown:
        await update.message.reply_text(f"✅ آخرین {shown} فال ارسال شد.")
