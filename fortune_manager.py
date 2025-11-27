# fortune_manager.py

import json
import os
import random
import uuid
from datetime import datetime
from urllib.parse import urlparse
import aiohttp
from telegram import Update, InputFile
from telegram.ext import ContextTypes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FORTUNE_FILE = os.path.join(BASE_DIR, "fortunes.json")
MEDIA_DIR = os.path.join(BASE_DIR, "fortunes_media")
os.makedirs(MEDIA_DIR, exist_ok=True)

MAX_FORTUNES = 100  # حداکثر تعداد فال‌ها

# ========================= ابزارهای کمکی =========================

def _is_valid_url(val: str) -> bool:
    if not isinstance(val, str) or not val.strip():
        return False
    if not (val.startswith("http://") or val.startswith("https://")):
        return False
    u = urlparse(val)
    return bool(u.scheme and u.netloc)

def _abs_media_path(val: str) -> str:
    """بازگرداندن مسیر کامل لوکال یا URL"""
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

# ========================= دانلود فایل از URL =========================

async def download_file(url, media_type):
    ext = "jpg" if media_type == "photo" else "mp4" if media_type == "video" else "webp"
    local_path = os.path.join(MEDIA_DIR, f"{uuid.uuid4()}.{ext}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                with open(local_path, "wb") as f:
                    f.write(await resp.read())
            else:
                raise Exception(f"دانلود فایل موفق نبود: {resp.status}")
    return local_path

# ========================= ارسال مدیا =========================

async def send_media(update: Update, media_type: str, val: str, k: str):
    real_path = _abs_media_path(val)

    if _is_valid_url(real_path):
        # دانلود URL به فایل لوکال
        try:
            real_path = await download_file(real_path, media_type)
        except Exception as e:
            return await update.message.reply_text(f"⚠️ خطا در پردازش فایل: {e}")

    if not os.path.exists(real_path):
        return await update.message.reply_text(f"⚠️ فایل پیدا نشد: {real_path}")

    file = InputFile(real_path)
    if media_type == "photo":
        await update.message.reply_photo(photo=file, caption=f"🔮 فال شماره {k}")
    elif media_type == "video":
        await update.message.reply_video(video=file, caption=f"🎥 فال شماره {k}")
    elif media_type == "sticker":
        await update.message.reply_sticker(sticker=file)

# ========================= ثبت فال =========================

async def save_fortune(update: Update):
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("❗ لطفاً روی پیام فال ریپلای کن.")

    data = load_fortunes()
    entry = {"type": "text", "value": ""}

    try:
        # ---- متن ----
        if reply.text or reply.caption:
            val = (reply.text or reply.caption).strip()
            entry["type"] = "text"
            entry["value"] = val

        # ---- عکس ----
        elif reply.photo:
            file = await reply.photo[-1].get_file()
            filename = f"photo_{uuid.uuid4()}.jpg"
            path = os.path.join(MEDIA_DIR, filename)
            await file.download_to_drive(path)
            entry["type"] = "photo"
            entry["value"] = os.path.relpath(path, BASE_DIR)

        # ---- ویدیو ----
        elif reply.video:
            file = await reply.video.get_file()
            filename = f"video_{uuid.uuid4()}.mp4"
            path = os.path.join(MEDIA_DIR, filename)
            await file.download_to_drive(path)
            entry["type"] = "video"
            entry["value"] = os.path.relpath(path, BASE_DIR)

        # ---- استیکر ----
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
            if v.get("type") == entry["type"] and v.get("value") == entry["value"]:
                return await update.message.reply_text("😅 این فال قبلاً ذخیره شده بود!")

        # پاک‌سازی قدیمی‌ترین
        if len(data) >= MAX_FORTUNES:
            oldest = sorted(data.keys())[0]
            old_val = _abs_media_path(data[oldest]["value"])
            if os.path.exists(old_val) and not _is_valid_url(old_val):
                os.remove(old_val)
            data.pop(oldest)

        # کلید یکتا
        key = str(uuid.uuid4())
        data[key] = entry
        save_fortunes(data)

        # ارسال فال ذخیره‌شده همان لحظه
        await send_media(update, entry["type"], entry["value"], key)
        await update.message.reply_text("✅ فال ذخیره و ارسال شد!")

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

    delete_type = None
    delete_val = None

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

    # پاک کردن فایل لوکال
    real_path = _abs_media_path(data[target_key]["value"])
    if os.path.exists(real_path) and not _is_valid_url(real_path):
        os.remove(real_path)

    data.pop(target_key)
    save_fortunes(data)
    await update.message.reply_text("🗑️ فال حذف شد.")

# ========================= ارسال فال تصادفی =========================

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

    v = data[k]
    await send_media(update, v["type"], v["value"], k)

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
        v = data[k]
        try:
            await send_media(update, v["type"], v["value"], k)
            shown += 1
        except Exception as e:
            print(f"[List Fortune Error] {k}: {e}")

    if shown > 0:
        await update.message.reply_text(f"✅ آخرین {shown} فال ارسال شد.")
