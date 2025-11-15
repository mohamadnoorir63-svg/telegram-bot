import os
import json
import re
import asyncio
from datetime import datetime, time
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes

# ────────────── تنظیمات دسترسی ──────────────
SUDO_IDS = [8588347189]  # آیدی سودو

# ────────────── مسیر فایل‌ها ──────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VIP_FILE = os.path.join(BASE_DIR, "vips.json")
LOCK_FILE = os.path.join(BASE_DIR, "group_locks.json")
AUTO_LOCK_FILE = os.path.join(BASE_DIR, "auto_lock.json")

# ────────────── بارگذاری داده‌ها ──────────────
if not os.path.exists(VIP_FILE):
    with open(VIP_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

if not os.path.exists(LOCK_FILE):
    with open(LOCK_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

if not os.path.exists(AUTO_LOCK_FILE):
    with open(AUTO_LOCK_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

# VIP
try:
    with open(VIP_FILE, "r", encoding="utf-8") as f:
        VIPS = json.load(f)
except:
    VIPS = {}

# LOCKS
try:
    with open(LOCK_FILE, "r", encoding="utf-8") as f:
        LOCKS = json.load(f)
except:
    LOCKS = {}

# AUTO LOCKS
try:
    with open(AUTO_LOCK_FILE, "r", encoding="utf-8") as f:
        AUTO_LOCKS = json.load(f)
except:
    AUTO_LOCKS = {}

# ────────────── لیست قفل‌ها ──────────────
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
    "tag": "تگ",
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
    "all_links": "همه لینک‌ها",
    "inline_bots": "ربات تبچی",
    "external_media": "رسانه خارجی",
    "invite_links": "لینک دعوت",
    "file_types": "فایل‌های خاص",
    "forward_from_bots": "فوروارد از ربات",
    "urls_videos": "لینک ویدیو",
    "short_links": "لینک کوتاه",
    "spam_repeats": "پیام تکراری",
    "capslock": "حروف بزرگ",
    "long_text": "پیام بلند",
}

# ────────────── توابع ذخیره/بارگذاری ──────────────
def _save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[⚠️] خطا در ذخیره {path}: {e}")


def _save_vips():
    global VIPS
    _save_json(VIP_FILE, VIPS)


def _save_locks():
    global LOCKS
    _save_json(LOCK_FILE, LOCKS)


def _save_auto_locks():
    global AUTO_LOCKS
    _save_json(AUTO_LOCK_FILE, AUTO_LOCKS)


def _get_locks(chat_id: int):
    return LOCKS.get(str(chat_id), {})


def _is_locked(chat_id: int, key: str) -> bool:
    return LOCKS.get(str(chat_id), {}).get(key, False)


def _set_lock(chat_id: int, key: str, status: bool):
    global LOCKS
    LOCKS.setdefault(str(chat_id), {})[key] = bool(status)
    _save_locks()


# ────────────── دسترسی‌ها ──────────────
async def _is_admin_or_sudo(context, chat_id: int, user_id: int) -> bool:
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
    if user_id in SUDO_IDS:
        return True
    if await _is_admin_or_sudo(context, chat_id, user_id):
        return True
    if _is_vip(chat_id, user_id):
        return True
    return False


# ────────────── حذف پیام و هشدار ──────────────
async def _del_msg(update: Update, warn_text: str = None):
    try:
        msg = update.message
        user = update.effective_user
        await msg.delete()
        if warn_text:
            warn = await msg.chat.send_message(
                f"{warn_text}\n👤 {user.first_name}", parse_mode="HTML"
            )
            await asyncio.sleep(4)
            await warn.delete()
    except Exception as e:
        print(f"[Delete Error] {e}")


# ────────────── VIP ──────────────
async def set_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    global VIPS
    if not await _has_full_access(context, chat.id, user.id):
        await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
        return
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    else:
        args = (update.message.text or "").split()
        if len(args) != 2 or not args[1].isdigit():
            await update.message.reply_text("📘 مثال صحیح:\nتنظیم ویژه 123456789")
            return
        target_id = int(args[1])
    cid = str(chat.id)
    VIPS.setdefault(cid, [])
    if target_id in VIPS[cid]:
        await update.message.reply_text("✅ این کاربر از قبل ویژه است.")
        return
    VIPS[cid].append(target_id)
    _save_vips()
    await update.message.reply_text(f"✅ کاربر <b>{target_id}</b> به ویژه‌ها اضافه شد.", parse_mode="HTML")


async def remove_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    global VIPS
    if not await _has_full_access(context, chat.id, user.id):
        await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
        return
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    else:
        args = (update.message.text or "").split()
        if len(args) != 2 or not args[1].isdigit():
            await update.message.reply_text("📘 مثال صحیح:\nحذف ویژه 123456789")
            return
        target_id = int(args[1])
    cid = str(chat.id)
    if cid not in VIPS or target_id not in VIPS[cid]:
        await update.message.reply_text("ℹ️ این کاربر در لیست ویژه نیست.")
        return
    VIPS[cid].remove(target_id)
    _save_vips()
    await update.message.reply_text(f"❎ کاربر <b>{target_id}</b> از لیست ویژه حذف شد.", parse_mode="HTML")


async def list_vips(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


# ────────────── قفل محتوا ──────────────
LAST_MESSAGES = {}


async def check_message_locks(update, context):
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

    # پیام تکراری
    if locks.get("spam_repeats") and text:
        last_msg = LAST_MESSAGES.get(user.id)
        if last_msg and last_msg == text:
            return await _del_msg(update, "🚫 ارسال پیام تکراری ممنوع است.")
        LAST_MESSAGES[user.id] = text

    # قفل‌های محتوایی
    if locks.get("all_links") and any(x in text for x in ["http://", "https://", "t.me", "telegram.me"]):
        return await _del_msg(update, "🚫 ارسال هرگونه لینک ممنوع است.")
    if locks.get("urls_videos") and any(x in text for x in ["youtube.com", "youtu.be", "tiktok.com"]):
        return await _del_msg(update, "🚫 ارسال لینک ویدیو ممنوع است.")
    if locks.get("short_links") and any(x in text for x in ["bit.ly", "tinyurl.com", "t2m.io"]):
        return await _del_msg(update, "🚫 ارسال لینک کوتاه ممنوع است.")
    if locks.get("inline_bots") and getattr(msg, "via_bot", None):
        return await _del_msg(update, "🚫 استفاده از ربات اینلاین ممنوع است.")
    if locks.get("long_text") and len(text) > 200:
        return await _del_msg(update, "🚫 ارسال پیام طولانی ممنوع است.")
    if locks.get("capslock") and text.isupper():
        return await _del_msg(update, "🚫 پیام با حروف بزرگ ممنوع است.")
    if locks.get("links") and any(x in text for x in ["http://", "https://", "t.me", "telegram.me"]):
        return await _del_msg(update, "🚫 ارسال لینک ممنوع است.")
    if locks.get("ads") and any(x in text for x in ["joinchat", "promo", "invite", "bot?start=", "channel"]):
        return await _del_msg(update, "🚫 تبلیغات ممنوع است.")
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
    if locks.get("tag") and "@" in text:
        return await _del_msg(update, "🚫 استفاده از @ یا منشن ممنوع است.")
    if locks.get("arabic") and any("\u0600" <= c <= "\u06FF" for c in text):
        return await _del_msg(update, "🚫 استفاده از حروف عربی ممنوع است.")
    if locks.get("english") and any("a" <= c <= "z" or "A" <= c <= "Z" for c in text):
        return await _del_msg(update, "🚫 استفاده از حروف انگلیسی ممنوع است.")
    if locks.get("caption") and msg.caption:
        return await _del_msg(update, "🚫 کپشن‌گذاری ممنوع است.")
    if locks.get("reply") and msg.reply_to_message:
        return await _del_msg(update, "🚫 پاسخ دادن ممنوع است.")
    if locks.get("emoji"):
        emoji_pattern = re.compile(r"[\U00010000-\U0010ffff]", flags=re.UNICODE)
        if text and all(emoji_pattern.match(c) for c in text if not c.isspace()):
            return await _del_msg(update, "🚫 ارسال فقط ایموجی مجاز نیست.")
    if locks.get("text") and text and not (has_photo or has_video or has_doc):
        return await _del_msg(update, "🚫 ارسال پیام متنی ممنوع است.")


# ────────────── فعال/غیرفعال کردن قفل محتوا ──────────────
async def handle_lock(update, context, key: str):
    chat = update.effective_chat
    user = update.effective_user
    if not await _has_full_access(context, chat.id, user.id):
        await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
        return
    if key not in LOCK_TYPES:
        return
    if _is_locked(chat.id, key):
        await update.message.reply_text(f"🔒 قفل {LOCK_TYPES.get(key, key)} از قبل فعال است.")
        return
    _set_lock(chat.id, key, True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await update.message.reply_text(f"✅ قفل {LOCK_TYPES.get(key, key)} توسط <b>{user.first_name}</b> فعال شد.\n🕓 زمان: {now}", parse_mode="HTML")


async def handle_unlock(update, context, key: str):
    chat = update.effective_chat
    user = update.effective_user
    if not await _has_full_access(context, chat.id, user.id):
        await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
        return
    if key not in LOCK_TYPES:
        return
    if not _is_locked(chat.id, key):
        await update.message.reply_text(f"🔓 قفل {LOCK_TYPES.get(key, key)} از قبل باز است.")
        return
    _set_lock(chat.id, key, False)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await update.message.reply_text(f"🔓 قفل {LOCK_TYPES.get(key, key)} توسط <b>{user.first_name}</b> باز شد.\n🕓 زمان: {now}", parse_mode="HTML")


async def handle_lock_commands(update, context):
    text = (update.message.text or "").strip().lower()
    for key, fa in LOCK_TYPES.items():
        if text == f"قفل {fa}":
            return await handle_lock(update, context, key)
        if text in (f"باز کردن {fa}", f"بازکردن {fa}"):
            return await handle_unlock(update, context, key)
    return False


# ────────────── قفل گروه و قفل خودکار ──────────────
async def lock_group(update, context):
    chat = update.effective_chat
    user = update.effective_user
    if not await _has_full_access(context, chat.id, user.id):
        await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
        return
    await context.bot.set_chat_permissions(chat.id, ChatPermissions(can_send_messages=False))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await update.message.reply_text(f"🔒 گروه توسط <b>{user.first_name}</b> قفل شد.\n🕓 زمان: {now}", parse_mode="HTML")


async def unlock_group(update, context):
    chat = update.effective_chat
    user = update.effective_user
    if not await _has_full_access(context, chat.id, user.id):
        await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
        return
    await context.bot.set_chat_permissions(chat.id, ChatPermissions(can_send_messages=True))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await update.message.reply_text(f"🔓 گروه توسط <b>{user.first_name}</b> باز شد.\n🕓 زمان: {now}", parse_mode="HTML")


async def set_auto_lock(update, context):
    chat = update.effective_chat
    user = update.effective_user
    args = (update.message.text or "").split()
    # ────────────── تنظیم قفل خودکار ──────────────
async def set_auto_lock(update, context):
    chat = update.effective_chat
    user = update.effective_user
    args = (update.message.text or "").split()
    if not await _has_full_access(context, chat.id, user.id):
        await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
        return
    if len(args) != 3 or not (args[1].isdigit() and args[2].isdigit()):
        await update.message.reply_text("📘 مثال صحیح:\nزمان قفل 22 6\n(قفل از ساعت 22 تا 6)")
        return
    start_hour, end_hour = int(args[1]), int(args[2])
    AUTO_LOCKS[str(chat.id)] = {"start": start_hour, "end": end_hour}
    _save_auto_locks()
    await update.message.reply_text(f"🕒 قفل خودکار گروه از ساعت {start_hour}:00 تا {end_hour}:00 تنظیم شد.")


async def auto_lock_job(context: ContextTypes.DEFAULT_TYPE):
    for cid, times in AUTO_LOCKS.items():
        chat_id = int(cid)
        start, end = times["start"], times["end"]
        now_hour = datetime.now().hour
        try:
            if start <= now_hour or now_hour < end:
                # گروه را قفل کن
                await context.bot.set_chat_permissions(chat_id, ChatPermissions(can_send_messages=False))
            else:
                # گروه را باز کن
                await context.bot.set_chat_permissions(chat_id, ChatPermissions(can_send_messages=True))
        except Exception as e:
            print(f"[AutoLock Error] {chat_id}: {e}")


# ────────────── هندلر اصلی پیام گروه ──────────────
from telegram.ext import MessageHandler, filters

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # بررسی VIP و مدیران
    if await _has_full_access(context, update.effective_chat.id, update.effective_user.id):
        return  # دسترسی کامل، هیچ کاری انجام نمی‌دهیم
    # بررسی قفل‌های محتوا
    await check_message_locks(update, context)
    # بررسی دستورات قفل/باز کردن
    await handle_lock_commands(update, context)
