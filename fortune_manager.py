# fortune_manager.py

import json
import os
import random
import uuid
from datetime import datetime
from urllib.parse import urlparse
from telegram import Update, InputFile
from telegram.ext import ContextTypes

# ========================= مسیرها و آماده‌سازی =========================
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
            await update.message.reply_photo(photo=val, caption=f"🔮 فال شماره {k}")
        elif media_type == "video":
            await update.message.reply_video(video=val, caption=f"🎥 فال شماره {k}")
        elif media_type == "sticker":
            await update.message.reply_sticker(sticker=val)
    else:
        if not os.path.exists(val):
            return await update.message.reply_text(f"⚠️ فایل لوکال پیدا نشد: {val}")
        file = InputFile(val)
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

        # جلوگیری از تکراری بودن شدید
        for v in data.values():
            if v.get("type") == entry["type"] and v.get("value") == entry["value"]:
                return await update.message.reply_text("😅 این فال قبلاً ذخیره شده بود!")

        # حذف قدیمی‌ترین فال اگر بیشتر از MAX_FORTUNES
        if len(data) >= MAX_FORTUNES:
            sorted_keys = sorted(data.keys(), key=lambda x: x)
            oldest_key = sorted_keys[0]
            old_val = _abs_media_path(data[oldest_key].get("value", ""))
            if os.path.exists(old_val) and not _is_valid_url(old_val):
                os.remove(old_val)
            data.pop(oldest_key)

        # کلید یکتا
        new_key = str(uuid.uuid4())
        data[new_key] = entry
        save_fortunes(data)
        await update.message.reply_text("✅ فال با موفقیت ذخیره شد!")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ذخیره فال: {e}")

# ========================= حذف فال =========================
async def delete_fortune(update: Update):
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("❗ لطفاً روی پیام فال ریپلای کن تا حذف شود.")

    data = load_fortunes()
    if not data:
        return await update.message.reply_text("📂 هیچ فالی برای حذف وجود ندارد.")

    delete_type = None
    delete_match_value = None

    if reply.text or reply.caption:
        delete_type = "text"
        delete_match_value = (reply.text or reply.caption).strip()
    elif reply.photo:
        delete_type = "photo"
    elif reply.video:
        delete_type = "video"
    elif reply.sticker:
        delete_type = "sticker"
    else:
        return await update.message.reply_text("⚠️ نوع فال قابل شناسایی نیست.")

    key_to_delete = None
    for k, v in data.items():
        if v.get("type") == delete_type:
            if delete_type == "text":
                if v.get("value") == delete_match_value:
                    key_to_delete = k
                    break
            else:
                key_to_delete = k
                break

    if key_to_delete:
        deleted = data.pop(key_to_delete)
        save_fortunes(data)
        val = _abs_media_path(deleted.get("value", ""))
        if os.path.exists(val) and not _is_valid_url(val):
            os.remove(val)
        await update.message.reply_text("🗑️ فال با موفقیت حذف شد ✅")
    else:
        await update.message.reply_text("⚠️ فال موردنظر در فایل پیدا نشد.")

# ========================= ارسال فال تصادفی بدون تکرار پشت سر هم =========================
async def send_random_fortune(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_fortunes()
    if not data:
        return await update.message.reply_text("📭 هنوز فالی ذخیره نشده 😔")

    sent_state_file = os.path.join(BASE_DIR, "sent_fortunes.json")
    sent_keys = _load_json(sent_state_file, [])

    all_keys = list(data.keys())
    remaining_keys = [k for k in all_keys if k not in sent_keys]

    if not remaining_keys:  # همه فال‌ها ارسال شدند → ریست
        sent_keys = []
        remaining_keys = all_keys.copy()

    # جلوگیری از تکرار پشت سر هم
    last_sent = sent_keys[-1] if sent_keys else None
    possible_keys = [k for k in remaining_keys if k != last_sent] or remaining_keys
    k = random.choice(possible_keys)
    sent_keys.append(k)

    # ذخیره وضعیت ارسال
    with open(sent_state_file, "w", encoding="utf-8") as f:
        json.dump(sent_keys, f, ensure_ascii=False, indent=2)

    v = data.get(k, {})
    t = v.get("type", "text").strip()
    raw = (v.get("value") or "").strip()
    if not raw:
        return await update.message.reply_text("⚠️ فال نامعتبر یا خالی بود.")

    await send_media(update, t, raw, k)

# ========================= لیست فال‌ها =========================
async def list_fortunes(update: Update):
    data = load_fortunes()
    if not data:
        return await update.message.reply_text("هنوز هیچ فالی ثبت نشده 😔")

    await update.message.reply_text(
        f"📜 تعداد کل فال‌ها: {len(data)}\n\n"
        "برای حذف هر فال، روی پیام فال ریپلای بزن و بنویس: «حذف فال» 🗑️"
    )

    shown = 0
    for k in sorted(data.keys(), key=lambda x: x)[-10:]:
        v = data[k]
        t = v.get("type", "text")
        val = _abs_media_path(v.get("value", ""))

        try:
            await send_media(update, t, val, k)
            shown += 1
        except Exception as e:
            print(f"[Fortune List Error] id={k} err={e}")
            continue

    if shown == 0:
        await update.message.reply_text("⚠️ هیچ فالی برای نمایش پیدا نشد (ممکنه فایل‌ها حذف شده باشن).")
    else:
        await update.message.reply_text(
            f"✅ {shown} فال آخر نمایش داده شد.\n\n"
            "برای حذف، روی فال دلخواه ریپلای بزن و بنویس: حذف فال 🗑️"
        )
