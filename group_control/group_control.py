import os
import json
import re
import asyncio
from datetime import datetime
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes

# ─────────────────────────────── تنظیمات اولیه و دسترسی ───────────────────────────────

SUDO_IDS = [8588347189]  # آیدی سودوی اصلی

async def _is_admin_or_sudo(context, chat_id: int, user_id: int) -> bool:
    """بررسی مدیر یا سودو"""
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except:
        return False

def _is_vip(chat_id: int, user_id: int) -> bool:
    try:
        return user_id in VIPS.get(str(chat_id), [])
    except:
        return False

async def _has_full_access(context, chat_id: int, user_id: int) -> bool:
    """بررسی دسترسی کامل"""
    if user_id in SUDO_IDS:
        return True
    if await _is_admin_or_sudo(context, chat_id, user_id):
        return True
    if _is_vip(chat_id, user_id):
        return True
    return False

# ─────────────────────────────── مسیر فایل‌ها ───────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCK_FILE = os.path.join(BASE_DIR, "group_locks.json")

if not os.path.exists(LOCK_FILE):
    with open(LOCK_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

def _load_json(path, default=None):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[⚠️] خطا در خواندن {path}: {e}")
    return default or {}

def _save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[⚠️] خطا در ذخیره {path}: {e}")

# ─────────────────────────────── انواع قفل‌ها ───────────────────────────────

LOCK_TYPES = {
    "links": "لینک",
    "photos": "عکس",
    "videos": "ویدیو",
    "files": "فایل",
    "voices": "ویس",
    "stickers": "استیکر",
    "gifs": "گیف",
    "media": "رسانه",
    "forward": "فوروارد",
    "ads": "تبلیغ",
    "usernames": "یوزرنیم",
    "mention": "منشن",
    "arabic": "عربی",
    "english": "انگلیسی",
    "text": "متن",
    "audio": "موزیک",
    "emoji": "ایموجی",
    "caption": "کپشن",
    "reply": "ریپلای",
    "voicechat": "ویس چت",
    "location": "مکان",
    "contact": "مخاطب",
    "poll": "نظرسنجی",
    "bots": "ربات",
    "join": "ورود"
}

# ─────────────────────────────── عملیات روی قفل‌ها ───────────────────────────────

LOCKS = _load_json(LOCK_FILE, {})

def _get_locks(chat_id: int):
    return LOCKS.get(str(chat_id), {})

def _set_lock(chat_id: int, key: str, status: bool):
    """ذخیره قفل در حافظه و فایل"""
    cid = str(chat_id)
    if cid not in LOCKS:
        LOCKS[cid] = {}
    LOCKS[cid][key] = bool(status)
    _save_json(LOCK_FILE, LOCKS)

def _is_locked(chat_id: int, key: str) -> bool:
    """بررسی فعال بودن قفل"""
    return LOCKS.get(str(chat_id), {}).get(key, False)

# ─────────────────────────────── حذف پیام ممنوع ───────────────────────────────

async def _del_msg(update: Update, warn_text: str = None):
    try:
        msg = update.message
        user = update.effective_user
        await msg.delete()
        if warn_text:
            warn = await msg.chat.send_message(
                f"{warn_text}\n👤 {user.first_name}",
                parse_mode="HTML"
            )
            await asyncio.sleep(4)
            await warn.delete()
    except Exception as e:
        print(f"[Delete Error] {e}")

# ─────────────────────────────── اعمال قفل‌ها روی پیام ───────────────────────────────

async def check_message_locks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بررسی پیام و اعمال قفل‌های فعال"""
    if not update.message:
        return

    msg = update.message
    text = (msg.text or msg.caption or "").lower()
    chat = msg.chat
    user = msg.from_user

    locks = _get_locks(chat.id)
    if not any(locks.values()):
        return

    # مدیرها و سودوها مستثنی هستند
    if await _is_admin_or_sudo(context, chat.id, user.id):
        return

    # ویژگی‌های پیام
    has_photo = bool(msg.photo)
    has_video = bool(msg.video)
    has_doc = bool(msg.document)
    has_voice = bool(msg.voice)
    has_anim = bool(msg.animation)
    has_stick = bool(msg.sticker)
    has_fwd = bool(msg.forward_date)

    # 🚫 قفل لینک
    if locks.get("links") and any(x in text for x in ["http://", "https://", "t.me", "telegram.me"]):
        return await _del_msg(update, "🚫 ارسال لینک ممنوع است.")

    # 🚫 تبلیغ
    if locks.get("ads") and any(x in text for x in ["joinchat", "promo", "invite", "bot?start=", "channel"]):
        return await _del_msg(update, "🚫 تبلیغات ممنوع است.")

    # 🚫 رسانه‌ها
    if locks.get("photos") and has_photo:
        return await _del_msg(update, "🚫 ارسال عکس ممنوع است.")
    if locks.get("videos") and has_video:
        return await _del_msg(update, "🚫 ارسال ویدیو ممنوع است.")
    if locks.get("files") and has_doc:
        return await _del_msg(update, "🚫 ارسال فایل ممنوع است.")
    if locks.get("voices") and has_voice:
        return await _del_msg(update, "🚫 ارسال ویس ممنوع است.")
    if locks.get("stickers") and has_stick:
        return await _del_msg(update, "🚫 ارسال استیکر ممنوع است.")
    if locks.get("gifs") and has_anim:
        return await _del_msg(update, "🚫 ارسال گیف ممنوع است.")
    if locks.get("forward") and has_fwd:
        return await _del_msg(update, "🚫 فوروارد پیام ممنوع است.")

    # 🚫 منشن / یوزرنیم
    if (locks.get("usernames") or locks.get("mention")) and "@" in text:
        return await _del_msg(update, "🚫 استفاده از @ یا منشن ممنوع است.")

    # 🚫 حروف عربی / انگلیسی
    if locks.get("arabic") and any("\u0600" <= c <= "\u06FF" for c in text):
        return await _del_msg(update, "🚫 استفاده از حروف عربی ممنوع است.")
    if locks.get("english") and any("a" <= c <= "z" or "A" <= c <= "Z" for c in text):
        return await _del_msg(update, "🚫 استفاده از حروف انگلیسی ممنوع است.")

    # 🚫 کپشن / ریپلای
    if locks.get("caption") and msg.caption:
        return await _del_msg(update, "🚫 کپشن‌گذاری ممنوع است.")
    if locks.get("reply") and msg.reply_to_message:
        return await _del_msg(update, "🚫 پاسخ دادن ممنوع است.")

    # 🚫 فقط ایموجی
    if locks.get("emoji"):
        emoji_pattern = re.compile(r"[\U00010000-\U0010ffff]", flags=re.UNICODE)
        if text and all(emoji_pattern.match(c) for c in text if not c.isspace()):
            return await _del_msg(update, "🚫 ارسال فقط ایموجی مجاز نیست.")

    # 🚫 پیام متنی
    if locks.get("text") and text and not (has_photo or has_video or has_doc):
        return await _del_msg(update, "🚫 ارسال پیام متنی ممنوع است.")

# ─────────────────────────────── فعال و غیرفعال کردن قفل ───────────────────────────────

async def handle_lock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    chat = update.effective_chat
    user = update.effective_user

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    if key not in LOCK_TYPES:
        return await update.message.reply_text("⚠️ نوع قفل معتبر نیست.")

    if _is_locked(chat.id, key):
        return await update.message.reply_text(f"🔒 قفل {LOCK_TYPES[key]} از قبل فعال است.")
    _set_lock(chat.id, key, True)
    await update.message.reply_text(f"✅ قفل {LOCK_TYPES[key]} فعال شد.")

async def handle_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    chat = update.effective_chat
    user = update.effective_user

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    if key not in LOCK_TYPES:
        return await update.message.reply_text("⚠️ نوع قفل معتبر نیست.")

    if not _is_locked(chat.id, key):
        return await update.message.reply_text(f"🔓 قفل {LOCK_TYPES[key]} از قبل باز است.")
    _set_lock(chat.id, key, False)
    await update.message.reply_text(f"🔓 قفل {LOCK_TYPES[key]} باز شد.")

# ─────────────────────────────── دستورات متنی ───────────────────────────────

async def handle_lock_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشخیص دستور قفل / بازکردن"""
    text = (update.message.text or "").strip().lower()

    for key, fa in LOCK_TYPES.items():
        if text == f"قفل {fa}":
            return await handle_lock(update, context, key)
        if text in [f"باز کردن {fa}", f"بازکردن {fa}"]:
            return await handle_unlock(update, context, key)

    await update.message.reply_text("⚠️ دستور قفل یا بازکردن معتبر نیست.")
