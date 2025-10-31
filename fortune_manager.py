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

# ========================= ابزارهای کمکی =========================
def _is_valid_url(val: str) -> bool:
    """URL معتبر با دامنه (برای جلوگیری از خطای 'url host is empty')."""
    if not isinstance(val, str) or not val.strip():
        return False
    if not (val.startswith("http://") or val.startswith("https://")):
        return False
    u = urlparse(val)
    return bool(u.scheme and u.netloc)

def _abs_media_path(val: str) -> str:
    """اگر مسیر نسبی بود، به مسیر مطلق تبدیل شود (برای فایل‌های لوکال)."""
    if not val:
        return val
    if _is_valid_url(val):
        return val
    return val if os.path.isabs(val) else os.path.join(BASE_DIR, val)

def _load_json(path: str, default):
    """لود ایمن فایل JSON"""
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

# ========================= ثبت فال (ریپلای) =========================
async def save_fortune(update: Update):
    """با ریپلای روی پیام: متن/عکس/ویدیو/استیکر را ذخیره می‌کند."""
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

# ========================= حذف فال (ریپلای) =========================
async def delete_fortune(update: Update):
    """با ریپلای روی فال، آن را از فایل حذف می‌کند (پشتیبانی از متن و مدیا)."""
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("❗ لطفاً روی پیام فال ریپلای کن.")

    data = load_fortunes()
    if not data:
        return await update.message.reply_text("📂 هیچ فالی برای حذف وجود ندارد.")

    delete_type = None
    delete_value = None

    # تشخیص نوع و مقدار
    if reply.text or reply.caption:
        delete_type = "text"
        delete_value = (reply.text or reply.caption).strip()
    elif reply.photo:
        delete_type = "photo"
        file = await reply.photo[-1].get_file()
        delete_value = os.path.basename(file.file_path)
    elif reply.video:
        delete_type = "video"
        file = await reply.video.get_file()
        delete_value = os.path.basename(file.file_path)
    elif reply.sticker:
        delete_type = "sticker"
        file = await reply.sticker.get_file()
        delete_value = os.path.basename(file.file_path)

    if not delete_type or not delete_value:
        return await update.message.reply_text("⚠️ نوع فال قابل شناسایی نیست.")

    key_to_delete = None
    for k, v in data.items():
        if v.get("type") == delete_type:
            val_path = _abs_media_path(v.get("value", ""))
            if delete_type == "text" and v.get("value") == delete_value:
                key_to_delete = k
                break
            elif delete_type != "text" and os.path.basename(val_path) == delete_value:
                key_to_delete = k
                break

    if key_to_delete:
        deleted = data.pop(key_to_delete)
        save_fortunes(data)
        val = _abs_media_path(deleted.get("value", ""))
        if os.path.exists(val) and not _is_valid_url(val):
            try:
                os.remove(val)
            except Exception as e:
                print(f"[Delete Fortune Warning] حذف فایل شکست خورد: {e}")

        await update.message.reply_text("🗑️ فال با موفقیت حذف شد ✅")
    else:
        await update.message.reply_text("⚠️ فال موردنظر در فایل پیدا نشد.")

# ========================= ارسال فال تصادفی =========================
async def send_random_fortune(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال فال تصادفی با بررسی مسیرهای واقعی و حذف موارد خراب."""
    data = load_fortunes()
    if not data:
        return await update.message.reply_text("📭 هنوز فالی ذخیره نشده 😔")

    keys = list(data.keys())
    random.shuffle(keys)
    cleaned_data = {}

    for k in keys:
        v = data.get(k, {})
        t = v.get("type", "text").strip()
        raw = (v.get("value") or "").strip()

        if not raw:
            continue

        val = _abs_media_path(raw)
        if not _is_valid_url(val) and not os.path.exists(val) and t != "text":
            continue

        cleaned_data[k] = v

        try:
            if t == "text":
                await update.message.reply_text(f"🔮 {raw}")
                break
            elif t == "photo":
                await update.message.reply_photo(photo=val, caption="🔮 فال تصویری!")
                break
            elif t == "video":
                await update.message.reply_video(video=val, caption="🎥 فال ویدیویی!")
                break
            elif t == "sticker":
                await update.message.reply_sticker(sticker=val)
                break
        except Exception as e:
            print(f"[Fortune Error] id={k} type={t} err={e}")
            continue

    if len(cleaned_data) != len(data):
        save_fortunes(cleaned_data)
        print(f"🧹 فال‌های خراب حذف شدند ({len(data) - len(cleaned_data)} مورد).")

    if not cleaned_data:
        await update.message.reply_text("⚠️ هیچ فالی سالم برای ارسال پیدا نشد 😔")

# ========================= لیست فال‌ها (آخرین ۱۰ مورد) =========================
async def list_fortunes(update: Update):
    """نمایش ۱۰ فال آخر با نوع و محتوا"""
    data = load_fortunes()
    if not data:
        return await update.message.reply_text("هنوز هیچ فالی ثبت نشده 😔")

    await update.message.reply_text(f"📜 تعداد کل فال‌ها: {len(data)}")

    shown = 0
    for k in sorted(data.keys(), key=lambda x: int(x))[-10:]:
        v = data[k]
        t = v.get("type", "text")
        val = _abs_media_path(v.get("value", ""))

        try:
            if t == "text":
                await update.message.reply_text(f"🔮 {v.get('value')}")
            elif t == "photo":
                await update.message.reply_photo(photo=val, caption=f"🔮 فال {k}")
            elif t == "video":
                await update.message.reply_video(video=val, caption=f"🎥 فال {k}")
            elif t == "sticker":
                await update.message.reply_sticker(sticker=val)
            shown += 1
        except Exception as e:
            print(f"[Fortune List Error] id={k} err={e}")
            continue

    if shown == 0:
        await update.message.reply_text("⚠️ هیچ فالی برای نمایش پیدا نشد (ممکنه فایل‌ها حذف یا جابه‌جا شده باشن).")
