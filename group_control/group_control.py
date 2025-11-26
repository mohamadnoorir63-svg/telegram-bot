import os
import json
import re
import asyncio
from datetime import datetime, time
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
# ─────────────────────────────── تنظیمات دسترسی ───────────────────────────────
SUDO_IDS = [8588347189]  # آیدی سودو

# مسیر فایل VIP
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIP_FILE = os.path.join(BASE_DIR, "vips.json")

# بارگذاری VIPها
VIPS = {}
if os.path.exists(VIP_FILE):
    try:
        with open(VIP_FILE, "r", encoding="utf-8") as f:
            VIPS = json.load(f)
    except:
        VIPS = {}

def _save_vips():
    with open(VIP_FILE, "w", encoding="utf-8") as f:
        json.dump(VIPS, f, ensure_ascii=False, indent=2)

# ─────────────────────────────── دسترسی‌ها ───────────────────────────────
async def _is_admin_or_sudo(context, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except:
        return False

def _is_vip(chat_id: int, user_id: int) -> bool:
    return user_id in VIPS.get(str(chat_id), [])

async def _has_full_access(context, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_IDS:
        return True
    if await _is_admin_or_sudo(context, chat_id, user_id):
        return True
    if _is_vip(chat_id, user_id):
        return True
    return False

# ─────────────── اضافه کردن VIP ───────────────
async def set_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اضافه کردن کاربر به VIP"""
    chat = update.effective_chat
    user = update.effective_user

    if not await _has_full_access(context, chat.id, user.id):
        return

    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    else:
        args = (update.message.text or "").split()
        if len(args) != 2 or not args[1].isdigit():
            warn = await update.message.reply_text(
                "📘 مثال صحیح:\n<code>تنظیم ویژه 123456789</code>",
                parse_mode="HTML",
                quote=True
            )
            await asyncio.sleep(5)
            await update.message.delete()
            await warn.delete()
            return
        target_id = int(args[1])

    cid = str(chat.id)
    if cid not in VIPS:
        VIPS[cid] = []

    if target_id in VIPS[cid]:
        warn = await update.message.reply_text("✅ این کاربر از قبل ویژه است.", quote=True)
        await asyncio.sleep(5)
        await update.message.delete()
        await warn.delete()
        return

    VIPS[cid].append(target_id)
    _save_vips()
    reply = await update.message.reply_text(
        f"✅ کاربر <b>{target_id}</b> به ویژه‌ها اضافه شد.",
        parse_mode="HTML", quote=True
    )
    await asyncio.sleep(5)
    await update.message.delete()
    await reply.delete()

# ─────────────── حذف VIP ───────────────
async def remove_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف کاربر از VIP"""
    chat = update.effective_chat
    user = update.effective_user

    if not await _has_full_access(context, chat.id, user.id):
        return

    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    else:
        args = (update.message.text or "").split()
        if len(args) != 2 or not args[1].isdigit():
            warn = await update.message.reply_text(
                "📘 مثال صحیح:\n<code>حذف ویژه 123456789</code>",
                parse_mode="HTML", quote=True
            )
            await asyncio.sleep(5)
            await update.message.delete()
            await warn.delete()
            return
        target_id = int(args[1])

    cid = str(chat.id)
    if cid not in VIPS or target_id not in VIPS[cid]:
        warn = await update.message.reply_text("ℹ️ این کاربر در لیست ویژه نیست.", quote=True)
        await asyncio.sleep(5)
        await update.message.delete()
        await warn.delete()
        return

    VIPS[cid].remove(target_id)
    _save_vips()
    reply = await update.message.reply_text(
        f"❎ کاربر <b>{target_id}</b> از لیست ویژه حذف شد.",
        parse_mode="HTML", quote=True
    )
    await asyncio.sleep(5)
    await update.message.delete()
    await reply.delete()

# ─────────────── نمایش لیست VIP ───────────────
async def list_vips(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست کاربران VIP گروه"""
    chat = update.effective_chat
    cid = str(chat.id)
    vips = VIPS.get(cid, [])

    if not vips:
        await update.message.reply_text("ℹ️ هنوز کاربری در لیست ویژه وجود ندارد.")
        return

    text = "✅ لیست کاربران ویژه:\n"
    for i, uid in enumerate(vips, 1):
        text += f"{i}. <b>{uid}</b>\n"

    await update.message.reply_text(text, parse_mode="HTML")
# ─────────────────────────────── مسیر فایل و لود قفل‌ها ───────────────────────────────
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

LOCKS = _load_json(LOCK_FILE, {})

# ─────────────────────────────── لیست کامل قفل‌ها ───────────────────────────────
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
    "tag": "تگ",           # منشن / یوزرنیم یکجا شد
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
    "join": "ورود",
    # ───────────── قفل‌های پیشرفته ─────────────
    "all_links": "همه لینک‌ ها",
    "inline_bots": "ربات تبچی",
    "external_media": "رسانه خارجی",
    "invite_links": "لینک دعوت",
    "file_types": "فایل‌های خاص",
    "forward_from_bots": "فوروارد از ربات",
    "urls_videos": "لینک ویدیو",
    "short_links": "لینک کوتاه",
    "spam_repeats": "پیام تکراری",
    "capslock": "حروف بزرگ",
    "long_text": "پیام بلند"
}

# ─────────────────────────────── توابع مدیریت فایل قفل ───────────────────────────────

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
    return LOCKS.get(str(chat_id), {}).get(key, False)

# ─────────────────────────────── حذف پیام ممنوع ───────────────────────────────
# ─────────────────────────────── حذف پیام با نماد اختصاصی ───────────────────────────────
LOCK_REASONS = {
    "spam_repeats": "🚫 ارسال پیام تکراری ممنوع است.",
    "all_links": "🌐 ارسال هرگونه لینک ممنوع است.",
    "urls_videos": "🎥 ارسال لینک ویدیو ممنوع است.",
    "short_links": "🔗 ارسال لینک کوتاه ممنوع است.",
    "inline_bots": "🤖 استفاده از ربات اینلاین ممنوع است.",
    "long_text": "📝 ارسال پیام طولانی ممنوع است.",
    "capslock": "🔠 پیام با حروف بزرگ ممنوع است.",
    "ads": "📢 ارسال تبلیغ ممنوع است.",
    "photos": "📸 ارسال عکس ممنوع است.",
    "videos": "🎬 ارسال ویدیو ممنوع است.",
    "files": "📂 ارسال فایل ممنوع است.",
    "voices": "🎙️ ارسال ویس ممنوع است.",
    "stickers": "🖼️ ارسال استیکر ممنوع است.",
    "gifs": "🎞️ ارسال گیف ممنوع است.",
    "forward": "📤 فوروارد پیام ممنوع است.",
    "tag": "🏷️ استفاده از @ یا منشن ممنوع است.",
    "arabic": "🕌 استفاده از حروف عربی ممنوع است.",
    "english": "🇬🇧 استفاده از حروف انگلیسی ممنوع است.",
    "caption": "🏷️ کپشن‌گذاری ممنوع است.",
    "reply": "↩️ پاسخ دادن ممنوع است.",
    "emoji": "😎 ارسال فقط ایموجی مجاز نیست.",
    "text": "✉️ ارسال پیام متنی ممنوع است.",
    "voicechat": "🎤 ارسال ویس چت ممنوع است.",
    "location": "📍 ارسال مکان ممنوع است.",
    "contact": "📇 ارسال مخاطب ممنوع است.",
    "bots": "🤖 ارسال ربات ممنوع است.",
    "join": "🚪 ورود اعضا محدود است.",
    "media": "🖼️ ارسال رسانه ممنوع است.",
    "external_media": "🌐 ارسال رسانه خارجی ممنوع است.",
    "invite_links": "✉️ ارسال لینک دعوت ممنوع است.",
    "file_types": "📄 ارسال فایل‌های خاص ممنوع است.",
    "forward_from_bots": "📤 فوروارد از ربات ممنوع است.",
    "urls_videos": "🎬 ارسال لینک ویدیو ممنوع است.",
}

async def _del_msg(update: Update, reason: str):
    """حذف پیام و ارسال هشدار با نماد اختصاصی"""
    try:
        msg = update.message
        user = update.effective_user
        await msg.delete()

        now = datetime.now().strftime("%H:%M:%S")
        text = (
            f"⚠️ پیام شما حذف شد\n"
            f"📌 دلیل: {reason}\n"
            f"👤 کاربر: {user.first_name}\n"
            f"⏰ ساعت: {now}\n"
            f"❗ لطفاً از ارسال این نوع محتوا خودداری کنید."
        )
        warn_msg = await msg.chat.send_message(text, parse_mode="HTML")
        await asyncio.sleep(5)
        await warn_msg.delete()
    except Exception as e:
        print(f"[Delete Error] {e}")

# ─────────────────────────────── بررسی پیام‌ها با نماد اختصاصی ───────────────────────────────
LAST_MESSAGES = {}

async def check_message_locks(update: Update, context):
    """بررسی پیام و حذف در صورت نقض قفل‌ها"""
    if not update.message:
        return

    msg = update.message
    text = (msg.text or msg.caption or "").strip()
    chat = msg.chat
    user = msg.from_user

    locks = _get_locks(chat.id)
    if not any(locks.values()):
        return

    if await _has_full_access(context, chat.id, user.id):
        return

    has_photo = bool(msg.photo)
    has_video = bool(msg.video)
    has_doc = bool(msg.document)
    has_voice = bool(msg.voice)
    has_anim = bool(msg.animation)
    has_stick = bool(msg.sticker)
    has_fwd = bool(msg.forward_date)
    has_location = bool(msg.location)
    has_contact = bool(msg.contact)

    emoji_pattern = re.compile(r"[\U00010000-\U0010ffff]", flags=re.UNICODE)

    for lock_key, reason in LOCK_REASONS.items():
        if not locks.get(lock_key):
            continue

        if lock_key == "spam_repeats" and text:
            last_msg = LAST_MESSAGES.get(user.id)
            if last_msg and last_msg == text:
                return await _del_msg(update, reason)
            LAST_MESSAGES[user.id] = text

        elif lock_key == "all_links" and any(x in text for x in ["http://", "https://", "t.me", "telegram.me"]):
            return await _del_msg(update, reason)

        elif lock_key == "urls_videos" and any(x in text for x in ["youtube.com", "youtu.be", "tiktok.com"]):
            return await _del_msg(update, reason)

        elif lock_key == "short_links" and any(x in text for x in ["bit.ly", "tinyurl.com", "t2m.io"]):
            return await _del_msg(update, reason)

        elif lock_key == "inline_bots" and getattr(msg, "via_bot", None):
            return await _del_msg(update, reason)

        elif lock_key == "long_text" and len(text) > 200:
            return await _del_msg(update, reason)

        elif lock_key == "capslock" and text.isupper():
            return await _del_msg(update, reason)

        elif lock_key == "ads" and any(x in text for x in ["joinchat", "promo", "invite", "bot?start=", "channel"]):
            return await _del_msg(update, reason)

        elif lock_key == "photos" and has_photo:
            return await _del_msg(update, reason)
        elif lock_key == "videos" and has_video:
            return await _del_msg(update, reason)
        elif lock_key == "files" and has_doc:
            return await _del_msg(update, reason)
        elif lock_key == "voices" and has_voice:
            return await _del_msg(update, reason)
        elif lock_key == "stickers" and has_stick:
            return await _del_msg(update, reason)
        elif lock_key == "gifs" and has_anim:
            return await _del_msg(update, reason)
        elif lock_key == "forward" and has_fwd:
            return await _del_msg(update, reason)
        elif lock_key == "voicechat" and getattr(msg, "voice_chat_started", False):
            return await _del_msg(update, reason)
        elif lock_key == "location" and has_location:
            return await _del_msg(update, reason)
        elif lock_key == "contact" and has_contact:
            return await _del_msg(update, reason)

        elif lock_key == "tag" and "@" in text:
            return await _del_msg(update, reason)

        elif lock_key == "arabic" and any("\u0600" <= c <= "\u06FF" for c in text):
            return await _del_msg(update, reason)
        elif lock_key == "english" and any("a" <= c <= "z" or "A" <= c <= "Z" for c in text):
            return await _del_msg(update, reason)

        elif lock_key == "caption" and msg.caption:
            return await _del_msg(update, reason)
        elif lock_key == "reply" and msg.reply_to_message:
            return await _del_msg(update, reason)

        elif lock_key == "emoji" and text and all(emoji_pattern.match(c) for c in text if not c.isspace()):
            return await _del_msg(update, reason)

        elif lock_key == "text" and text and not (has_photo or has_video or has_doc):
            return await _del_msg(update, reason)

        elif lock_key == "bots" and getattr(msg, "via_bot", None):
            return await _del_msg(update, reason)

        elif lock_key == "join" and False:  # محدودیت ورود می‌تونه اینجا اضافه بشه
            return await _del_msg(update, reason)

        elif lock_key == "media" and (has_photo or has_video or has_doc or has_anim or has_stick or has_voice):
            return await _del_msg(update, reason)

        elif lock_key == "external_media" and False:  # بررسی رسانه خارجی در متن یا لینک‌ها
            return await _del_msg(update, reason)

        elif lock_key == "invite_links" and any(x in text for x in ["t.me/joinchat", "telegram.me/joinchat"]):
            return await _del_msg(update, reason)

        elif lock_key == "file_types" and has_doc:
            # می‌تونی نوع فایل خاص رو بررسی کنی
            return await _del_msg(update, reason)

        elif lock_key == "forward_from_bots" and getattr(msg, "forward_from", None) and getattr(msg.forward_from, "is_bot", False):
            return await _del_msg(update, reason)
    
# ─────────────────────────────── فعال‌سازی / غیرفعال‌سازی قفل ───────────────────────────────

async def handle_lock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    """فعال‌سازی قفل"""
    chat = update.effective_chat
    user = update.effective_user

    if not await _has_full_access(context, chat.id, user.id):
        return
    if key not in LOCK_TYPES:
        return

    if _is_locked(chat.id, key):
        return await update.message.reply_text(f"🔒 قفل {LOCK_TYPES[key]} از قبل فعال است.")

    _set_lock(chat.id, key, True)
    global LOCKS
    LOCKS = _load_json(LOCK_FILE, {})  # ← بروزرسانی حافظه بعد از تغییر

    await update.message.reply_text(f"✅ قفل {LOCK_TYPES[key]} فعال شد.")

async def handle_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    """غیرفعال‌سازی قفل"""
    chat = update.effective_chat
    user = update.effective_user

    if not await _has_full_access(context, chat.id, user.id):
        return
    if key not in LOCK_TYPES:
        return

    if not _is_locked(chat.id, key):
        return await update.message.reply_text(f"🔓 قفل {LOCK_TYPES[key]} از قبل باز است.")

    _set_lock(chat.id, key, False)
    global LOCKS
    LOCKS = _load_json(LOCK_FILE, {})  # ← بروزرسانی حافظه بعد از تغییر

    await update.message.reply_text(f"🔓 قفل {LOCK_TYPES[key]} باز شد.")
    

        # ─────────────────────────────── مدیریت دستورات قفل‌های محتوایی ───────────────────────────────
async def handle_lock_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشخیص و اجرای دستور قفل یا بازکردن (مثلاً: قفل عکس / باز کردن لینک و ...)"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip().lower()

    for key, fa in LOCK_TYPES.items():
        if text == f"قفل {fa}":
            return await handle_lock(update, context, key)
        if text in (f"باز کردن {fa}", f"بازکردن {fa}"):
            return await handle_unlock(update, context, key)

    # هیچ پیامی نده اگه دستور اشتباه بود
    return
    # ─────────────────────────────── نمایش وضعیت قفل‌ها ───────────────────────────────
async def show_lock_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش وضعیت همه قفل‌ها در گروه"""
    chat = update.effective_chat
    user = update.effective_user

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("❌ شما دسترسی لازم را ندارید.")

    locks = _get_locks(chat.id)
    if not locks:
        await update.message.reply_text("ℹ️ هیچ قفلی برای این گروه تعریف نشده است.")
        return

    text = "🔒 وضعیت قفل‌های گروه:\n\n"
    for key, fa in LOCK_TYPES.items():
        status = "✅ فعال" if locks.get(key) else "❌ باز"
        text += f"{fa}: {status}\n"

    await update.message.reply_text(text)
    

# ─────────────────────────────── هندلر مرکزی گروه ───────────────────────────────
async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = (update.message.text or update.message.caption or "").strip().lower()

    # ───────────── دستورات VIP ─────────────
    if text.startswith("تنظیم ویژه"):
        return await set_vip(update, context)

    if text.startswith("حذف ویژه"):
        return await remove_vip(update, context)

    if text == "لیست ویژه":
        return await list_vips(update, context)

    # ───────────── بررسی وضعیت قفل‌ها ─────────────
    if text == "وضعیت":
        return await show_lock_status(update, context)

    # ───────────── بررسی دستورات قفل / باز کردن محتوا ─────────────
    if text.startswith("قفل ") or text.startswith("باز کردن ") or text.startswith("بازکردن "):
        return await handle_lock_commands(update, context)

    # ───────────── در نهایت بررسی پیام‌ها مطابق قفل‌ها ─────────────
    await check_message_locks(update, context)
