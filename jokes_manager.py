# jokes_manager.py
import json
import os
import random
from datetime import datetime
from urllib.parse import urlparse
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

# ========================= مسیرها و آماده‌سازی =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JOKE_FILE = os.path.join(BASE_DIR, "jokes.json")
MEDIA_DIR = os.path.join(BASE_DIR, "jokes_media")
os.makedirs(MEDIA_DIR, exist_ok=True)

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

def load_jokes():
    return _load_json(JOKE_FILE, {})

def save_jokes(data):
    with open(JOKE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ========================= تزئین جوک با قاب =========================
def decorate_joke(text: str) -> str:
    max_len = 50
    lines = []
    for line in text.split("\n"):
        while len(line) > max_len:
            lines.append(line[:max_len])
            line = line[max_len:]
        lines.append(line)
    decorated_text = "\n".join(lines)
    return f"🖤🥀──────༺♡༻──────🥀🖤\n{decorated_text}\n🖤🥀──────༺♡༻──────🥀🖤"

# ========================= ثبت جوک (ریپلای) =========================
async def save_joke(update: Update):
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text(
            "❗ لطفاً روی پیام جوک (متن/عکس/ویدیو/استیکر) ریپلای کن."
        )

    data = load_jokes()
    entry = {"type": "text", "value": ""}

    try:
        if reply.text or reply.caption:
            entry["type"] = "text"
            entry["value"] = (reply.text or reply.caption).strip()
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
            return await update.message.reply_text(
                "⚠️ فقط متن، عکس، ویدیو یا استیکر پشتیبانی می‌شود."
            )

        # جلوگیری از تکرار
        for v in data.values():
            if v.get("type") == entry["type"] and v.get("value") == entry["value"]:
                return await update.message.reply_text("😅 این جوک قبلاً ذخیره شده بود!")

        data[str(len(data) + 1)] = entry
        save_jokes(data)
        await update.message.reply_text("✅ جوک با موفقیت ذخیره شد!")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ذخیره جوک: {e}")

# ========================= حذف جوک =========================
async def delete_joke(update: Update):
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text(
            "❗ لطفاً روی پیام جوک ریپلای کن تا حذف شود."
        )

    data = load_jokes()
    if not data:
        return await update.message.reply_text("📂 هیچ جوکی برای حذف وجود ندارد.")

    # حذف بر اساس شماره
    if (reply.text and "جوک شماره" in reply.text) or (reply.caption and "جوک شماره" in reply.caption):
        text = reply.text or reply.caption
        num = "".join(ch for ch in text if ch.isdigit())
        if num and num in data:
            deleted = data.pop(num)
            save_jokes(data)
            val = _abs_media_path(deleted.get("value", ""))
            if os.path.exists(val) and not _is_valid_url(val):
                try:
                    os.remove(val)
                except Exception as e:
                    print(f"[Delete Joke Warning] حذف فایل شکست خورد: {e}")
            return await update.message.reply_text(f"🗑️ جوک شماره {num} حذف شد ✅")

    # حذف بر اساس محتوا
    delete_type = None
    delete_value = None
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
        save_jokes(data)
        val = _abs_media_path(deleted.get("value", ""))
        if os.path.exists(val) and not _is_valid_url(val):
            try:
                os.remove(val)
            except Exception as e:
                print(f"[Delete Joke Warning] حذف فایل شکست خورد: {e}")
        await update.message.reply_text("🗑️ جوک با موفقیت حذف شد ✅")
    else:
        await update.message.reply_text("⚠️ جوک موردنظر در فایل پیدا نشد.")

# ========================= لیست جوک‌ها =========================
async def list_jokes(update: Update):
    data = load_jokes()
    if not data:
        return await update.message.reply_text("هیچ جوکی ثبت نشده 😅")

    await update.message.reply_text(
        f"📜 تعداد کل جوک‌ها: {len(data)}\n\nبرای حذف، روی هر جوک ریپلای بزن و بنویس: حذف جوک 🗑️"
    )

    shown = 0
    for k in sorted(data.keys(), key=lambda x: int(x))[-10:]:
        v = data[k]
        t = v.get("type", "text")
        val = _abs_media_path(v.get("value", ""))
        try:
            if t == "text":
                decorated = decorate_joke(v.get("value"))
                decorated_html = (
                    decorated.replace("&", "&amp;")
                             .replace("<", "&lt;")
                             .replace(">", "&gt;")
                )
                await update.message.reply_text(
                    f"😂 جوک شماره {k}\n{decorated_html}",
                    parse_mode=ParseMode.HTML
                )
            elif t == "photo":
                await update.message.reply_photo(photo=val, caption=f"😂 جوک شماره {k}")
            elif t == "video":
                await update.message.reply_video(video=val, caption=f"🎥 جوک شماره {k}")
            elif t == "sticker":
                await update.message.reply_sticker(sticker=val)
            shown += 1
        except Exception as e:
            print(f"[List Joke Error] id={k} err={e}")
            continue

    if shown == 0:
        await update.message.reply_text("⚠️ هیچ جوک سالمی برای نمایش پیدا نشد.")

# ========================= ارسال جوک تصادفی =========================
async def send_random_joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_jokes()
    if not data:
        return await update.message.reply_text("📭 هنوز جوکی ذخیره نشده 😅")

    sent_state_file = os.path.join(BASE_DIR, "sent_jokes.json")
    if os.path.exists(sent_state_file):
        try:
            with open(sent_state_file, "r", encoding="utf-8") as f:
                sent_keys = json.load(f)
        except Exception:
            sent_keys = []
    else:
        sent_keys = []

    all_keys = list(data.keys())
    if len(sent_keys) >= len(all_keys):
        sent_keys = []
        print("♻️ لیست ارسال جوک‌ها ریست شد.")

    remaining_keys = [k for k in all_keys if k not in sent_keys]
    if not remaining_keys:
        remaining_keys = all_keys.copy()

    random.shuffle(remaining_keys)
    k = remaining_keys.pop()
    sent_keys.append(k)

    with open(sent_state_file, "w", encoding="utf-8") as f:
        json.dump(sent_keys, f, ensure_ascii=False, indent=2)

    v = data.get(k, {})
    t = v.get("type", "text")
    val = _abs_media_path(v.get("value", ""))

    try:
        if t == "text":
            decorated = decorate_joke(v.get("value"))
            decorated_html = (
                decorated.replace("&", "&amp;")
                         .replace("<", "&lt;")
                         .replace(">", "&gt;")
            )
            await update.message.reply_text(
                f"😂 {decorated_html}",
                parse_mode=ParseMode.HTML
            )
        elif t == "photo":
            await update.message.reply_photo(photo=val, caption=f"😂 جوک شماره {k}")
        elif t == "video":
            await update.message.reply_video(video=val, caption=f"🎥 جوک شماره {k}")
        elif t == "sticker":
            await update.message.reply_sticker(sticker=val)
        else:
            await update.message.reply_text("⚠️ نوع جوک پشتیبانی نمی‌شود.")
    except Exception as e:
        print(f"[Send Random Joke Error] id={k} err={e}")
        await update.message.reply_text("⚠️ خطا در ارسال جوک.")
