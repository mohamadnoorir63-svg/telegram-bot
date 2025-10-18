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
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # خراب بود → بازنویسی امن
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
    """با ریپلای روی پیام: متن/عکس/ویدیو/استیکر را به‌صورت امن ذخیره می‌کند."""
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("❗ لطفاً روی پیام فال (متن/عکس/ویدیو/استیکر) ریپلای کن.")

    data = load_fortunes()
    entry = {"type": "text", "value": ""}

    try:
        # متن یا کپشن
        if reply.text or reply.caption:
            val = (reply.text or reply.caption).strip()
            if not val:
                return await update.message.reply_text("⚠️ متن خالی است.")
            entry["type"] = "text"
            entry["value"] = val

        # عکس
        elif reply.photo:
            file = await reply.photo[-1].get_file()
            filename = f"photo_{int(datetime.now().timestamp())}.jpg"
            path = os.path.join(MEDIA_DIR, filename)
            await file.download_to_drive(path)
            entry["type"] = "photo"
            entry["value"] = os.path.relpath(path, BASE_DIR)

        # ویدیو
        elif reply.video:
            file = await reply.video.get_file()
            filename = f"video_{int(datetime.now().timestamp())}.mp4"
            path = os.path.join(MEDIA_DIR, filename)
            await file.download_to_drive(path)
            entry["type"] = "video"
            entry["value"] = os.path.relpath(path, BASE_DIR)

        # استیکر
        elif reply.sticker:
            file = await reply.sticker.get_file()
            filename = f"sticker_{int(datetime.now().timestamp())}.webp"
            path = os.path.join(MEDIA_DIR, filename)
            await file.download_to_drive(path)
            entry["type"] = "sticker"
            entry["value"] = os.path.relpath(path, BASE_DIR)

        else:
            return await update.message.reply_text("⚠️ فقط متن، عکس، ویدیو یا استیکر پشتیبانی می‌شود.")

        # جلوگیری از تکراری
        for v in data.values():
            if v.get("type") == entry["type"] and v.get("value") == entry["value"]:
                return await update.message.reply_text("😅 این فال قبلاً ذخیره شده بود!")

        data[str(len(data) + 1)] = entry
        save_fortunes(data)
        await update.message.reply_text("✅ فال با موفقیت ذخیره شد!")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ذخیره فال: {e}")

# ========================= ارسال فال تصادفی =========================
                
async def send_random_fortune(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """یکی از فال‌های ذخیره‌شده را به‌صورت رندومی ارسال می‌کند (با بررسی مسیرهای امن)."""
    data = load_fortunes()
    if not data:
        return await update.message.reply_text("📭 هنوز فالی ذخیره نشده 😔")

    keys = list(data.keys())
    random.shuffle(keys)

    for k in keys:
        v = data[k]
        t = v.get("type", "text").strip()
        raw = (v.get("value") or "").strip()

        # ⛔ اگر مقدار خالی یا نامعتبر بود، برو سراغ بعدی
        if not raw:
            continue

        val = _abs_media_path(raw)

        try:
            # 🔹 فال متنی
            if t == "text":
                return await update.message.reply_text(f"🔮 {raw}")

            # 🔹 عکس
            elif t == "photo":
                if _is_valid_url(val):
                    return await update.message.reply_photo(photo=val, caption=f"🔮 فال {k}")
                elif os.path.exists(val):
                    return await update.message.reply_photo(photo=open(val, "rb"), caption=f"🔮 فال {k}")
                else:
                    continue

            # 🔹 ویدیو
            elif t == "video":
                if _is_valid_url(val):
                    return await update.message.reply_video(video=val, caption=f"🎥 فال {k}")
                elif os.path.exists(val):
                    return await update.message.reply_video(video=open(val, "rb"), caption=f"🎥 فال {k}")
                else:
                    continue

            # 🔹 استیکر
            elif t == "sticker":
                if _is_valid_url(val):
                    return await update.message.reply_sticker(sticker=val)
                elif os.path.exists(val):
                    return await update.message.reply_sticker(sticker=open(val, "rb"))
                else:
                    continue

        except Exception as e:
            print(f"[Fortune Error] ❌ id={k}, type={t}, err={e}")
            continue

    await update.message.reply_text("⚠️ هیچ فالی قابل ارسال نبود — شاید مسیر فایل‌ها تغییر کرده باشه.")

# ========================= لیست فال‌ها (آخرین ۱۰ تا) =========================
async def list_fortunes(update: Update):
    data = load_fortunes()
    if not data: 
        return await update.message.reply_text("هنوز هیچ فالی ثبت نشده 😔")

    await update.message.reply_text(f"📜 تعداد کل فال‌ها: {len(data)}")

    # نمایش مختصر ایتم‌ها بدون ایجاد خطا
    shown = 0
    for k in sorted(data.keys(), key=lambda x: int(x))[-10:]:
        v = data[k]
        t = v.get("type", "text")
        raw = v.get("value", "")

        try:
            if t == "text":
                await update.message.reply_text(f"🔮 {raw}")
            elif t == "photo":
                val = _abs_media_path(raw)
                if _is_valid_url(val):
                    await update.message.reply_photo(photo=val, caption=f"🔮 فال {k}")
                elif os.path.exists(val):
                    await update.message.reply_photo(photo=InputFile(val), caption=f"🔮 فال {k}")
            elif t == "video":
                val = _abs_media_path(raw)
                if _is_valid_url(val):
                    await update.message.reply_video(video=val, caption=f"🎥 فال {k}")
                elif os.path.exists(val):
                    await update.message.reply_video(video=InputFile(val), caption=f"🎥 فال {k}")
            elif t == "sticker":
                val = _abs_media_path(raw)
                if _is_valid_url(val):
                    await update.message.reply_sticker(sticker=val)
                elif os.path.exists(val):
                    await update.message.reply_sticker(sticker=InputFile(val))
            shown += 1
        except Exception as e:
            print(f"[Fortune List Error] id={k} err={e}")

    if shown == 0:
        await update.message.reply_text("⚠️ چیزی برای نمایش پیدا نشد (ممکنه فایل‌ها جابه‌جا شده باشن).")
