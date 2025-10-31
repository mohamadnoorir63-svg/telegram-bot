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



# ========================= حذف فال (هماهنگ با لیست و پیام‌های ربات) =========================
async def delete_fortune(update: Update):
    """با ریپلای روی فال موردنظر، آن را از فایل حذف می‌کند (پشتیبانی از متن، عکس، ویدیو، استیکر و پیام‌های ربات)."""
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("❗ لطفاً روی پیام فال ریپلای کن تا حذف شود.")

    data = load_fortunes()
    if not data:
        return await update.message.reply_text("📂 هیچ فالی برای حذف وجود ندارد.")

    delete_type = None
    delete_match_values = []

    # 🧩 حالت ۱: فال شماره X (در پیام‌های ربات)
    if reply.caption and "فال شماره" in reply.caption:
        try:
            num = "".join(ch for ch in reply.caption if ch.isdigit())
            if num and num in data:
                deleted = data.pop(num)
                save_fortunes(data)

                # حذف فایل لوکال در صورت وجود
                val = _abs_media_path(deleted.get("value", ""))
                if os.path.exists(val) and not _is_valid_url(val):
                    try:
                        os.remove(val)
                    except Exception as e:
                        print(f"[Delete Fortune Warning] حذف فایل شکست خورد: {e}")

                return await update.message.reply_text(f"🗑️ فال شماره {num} با موفقیت حذف شد ✅")
        except Exception as e:
            print(f"[Delete Fortune Error] تشخیص شماره در کپشن شکست خورد: {e}")

    # 🧩 حالت ۲: فال شماره X (در پیام متنی)
    if reply.text and "فال شماره" in reply.text:
        try:
            num = "".join(ch for ch in reply.text if ch.isdigit())
            if num and num in data:
                deleted = data.pop(num)
                save_fortunes(data)

                val = _abs_media_path(deleted.get("value", ""))
                if os.path.exists(val) and not _is_valid_url(val):
                    try:
                        os.remove(val)
                    except Exception as e:
                        print(f"[Delete Fortune Warning] حذف فایل شکست خورد: {e}")

                return await update.message.reply_text(f"🗑️ فال شماره {num} با موفقیت حذف شد ✅")
        except Exception as e:
            print(f"[Delete Fortune Error] تشخیص شماره در متن شکست خورد: {e}")

    # 🧩 حالت ۳: حذف مستقیم بر اساس محتوای پیام (برای پیام‌های کاربر)
    if reply.text or reply.caption:
        delete_type = "text"
        delete_match_values.append((reply.text or reply.caption).strip())

    elif reply.photo:
        delete_type = "photo"
        file = await reply.photo[-1].get_file()
        delete_match_values.append(os.path.basename(file.file_path))
        delete_match_values.append("photo")

    elif reply.video:
        delete_type = "video"
        file = await reply.video.get_file()
        delete_match_values.append(os.path.basename(file.file_path))
        delete_match_values.append("video")

    elif reply.sticker:
        delete_type = "sticker"
        file = await reply.sticker.get_file()
        delete_match_values.append(os.path.basename(file.file_path))
        delete_match_values.append("sticker")

    else:
        return await update.message.reply_text("⚠️ نوع فال قابل شناسایی نیست.")

    key_to_delete = None
    for k, v in data.items():
        if v.get("type") == delete_type:
            val_path = _abs_media_path(v.get("value", ""))
            base_name = os.path.basename(val_path)

            # تطبیق بر اساس مقدار یا نام فایل
            if any(match in base_name or match == v.get("value") for match in delete_match_values):
                key_to_delete = k
                break

    # ⚙️ حذف نهایی
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

# ========================= ارسال فال تصادفی (بدون تکرار تا اتمام کل مجموعه) =========================
async def send_random_fortune(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال فال تصادفی، بدون تکرار تا اتمام مجموعه (سپس بازتنظیم)"""
    data = load_fortunes()
    if not data:
        return await update.message.reply_text("📭 هنوز فالی ذخیره نشده 😔")

    # مسیر حافظهٔ موقتی برای ذخیره کلیدهای ارسال‌شده
    sent_state_file = os.path.join(BASE_DIR, "sent_fortunes.json")

    # بارگذاری وضعیت ارسال‌شده‌ها
    if os.path.exists(sent_state_file):
        try:
            with open(sent_state_file, "r", encoding="utf-8") as f:
                sent_keys = json.load(f)
        except Exception:
            sent_keys = []
    else:
        sent_keys = []

    # بررسی اینکه همه فال‌ها فرستاده شدن یا نه
    all_keys = list(data.keys())

    if len(sent_keys) >= len(all_keys):
        sent_keys = []  # همه ارسال شدن → ریست برای دور بعد
        print("♻️ لیست ارسال فال‌ها ریست شد (همه ارسال شده بودند).")

    # پیدا کردن کلیدهای باقیمانده
    remaining_keys = [k for k in all_keys if k not in sent_keys]
    if not remaining_keys:
        remaining_keys = all_keys.copy()

    # انتخاب تصادفی از باقی‌مانده‌ها
    random.shuffle(remaining_keys)
    k = remaining_keys.pop()
    sent_keys.append(k)

    # ذخیره وضعیت جدید
    with open(sent_state_file, "w", encoding="utf-8") as f:
        json.dump(sent_keys, f, ensure_ascii=False, indent=2)

    v = data.get(k, {})
    t = v.get("type", "text").strip()
    raw = (v.get("value") or "").strip()

    if not raw:
        return await update.message.reply_text("⚠️ فال نامعتبر یا خالی بود، مورد بعدی...")

    val = _abs_media_path(raw)

    try:
        if t == "text":
            await update.message.reply_text(f"🔮 {raw}")

        elif t == "photo":
            await update.message.reply_photo(photo=val, caption=f"🔮 فال شماره {k}")

        elif t == "video":
            await update.message.reply_video(video=val, caption=f"🎥 فال شماره {k}")

        elif t == "sticker":
            await update.message.reply_sticker(sticker=val)

        else:
            await update.message.reply_text("⚠️ نوع فایل پشتیبانی نمی‌شود.")

    except Exception as e:
        print(f"[Fortune Error] id={k} type={t} err={e}")
        await update.message.reply_text("⚠️ خطا در ارسال فال. مورد بعدی امتحان می‌شود.")

# ========================= لیست فال‌ها (شماره‌دار و قابل حذف با ریپلای) =========================
async def list_fortunes(update: Update):
    """نمایش ۱۰ فال آخر با شماره و امکان حذف با ریپلای"""
    data = load_fortunes()
    if not data:
        return await update.message.reply_text("هنوز هیچ فالی ثبت نشده 😔")

    await update.message.reply_text(
        f"📜 تعداد کل فال‌ها: {len(data)}\n\n"
        "برای حذف هر فال، روی پیام فال ریپلای بزن و بنویس: «حذف فال» 🗑️"
    )

    shown = 0
    # آخرین ۱۰ فال
    for k in sorted(data.keys(), key=lambda x: int(x))[-10:]:
        v = data[k]
        t = v.get("type", "text")
        val = _abs_media_path(v.get("value", ""))

        try:
            if t == "text":
                # فال متنی با شماره
                await update.message.reply_text(f"🔮 فال شماره {k}\n{v.get('value')}")
            elif t == "photo":
                # فال تصویری با کپشن شماره‌دار
                await update.message.reply_photo(photo=val, caption=f"🔮 فال شماره {k}")
            elif t == "video":
                # فال ویدیویی با کپشن شماره‌دار
                await update.message.reply_video(video=val, caption=f"🎥 فال شماره {k}")
            elif t == "sticker":
                # فال استیکری با شماره
                await update.message.reply_text(f"🔮 فال شماره {k} (استیکر)")
                await update.message.reply_sticker(sticker=val)
            shown += 1

        except Exception as e:
            print(f"[Fortune List Error] id={k} err={e}")
            continue

    if shown == 0:
        await update.message.reply_text("⚠️ هیچ فالی برای نمایش پیدا نشد (ممکنه فایل‌ها حذف شده باشن).")
    else:
        await update.message.reply_text(f"✅ {shown} فال آخر نمایش داده شد.\n\n"
                                        "برای حذف، روی فال دلخواه ریپلای بزن و بنویس: حذف فال 🗑️")
