import os
import json
import re
import asyncio
from telegram import Update
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
        warn = await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.", quote=True)
        await asyncio.sleep(5)
        await update.message.delete()
        await warn.delete()
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
        warn = await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.", quote=True)
        await asyncio.sleep(5)
        await update.message.delete()
        await warn.delete()
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

async def _del_msg(update: Update, warn_text: str = None):
    """حذف پیام و ارسال هشدار موقت"""
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

# ─────────────────────────────── بررسی پیام‌ها و اعمال قفل ───────────────────────────────
# دیکشنری برای ذخیره آخرین پیام هر کاربر
LAST_MESSAGES = {}

async def check_message_locks(update, context):
    """بررسی پیام و حذف در صورت نقض قفل‌ها"""
    if not update.message:
        return

    msg = update.message
    text = (msg.text or msg.caption or "").strip()
    text_lower = text.lower()
    chat = msg.chat
    user = msg.from_user

    locks = _get_locks(chat.id)
    if not any(locks.values()):
        return

    # مدیر + سودو + VIP معاف از حذف پیام
    if await _has_full_access(context, chat.id, user.id):
        return

    has_photo = bool(msg.photo)
    has_video = bool(msg.video)
    has_doc = bool(msg.document)
    has_voice = bool(msg.voice)
    has_anim = bool(msg.animation)
    has_stick = bool(msg.sticker)
    has_fwd = bool(msg.forward_date)

    # 🚫 پیام تکراری
    if locks.get("spam_repeats") and text:
        last_msg = LAST_MESSAGES.get(user.id)
        if last_msg and last_msg == text:
            return await _del_msg(update, "🚫 ارسال پیام تکراری ممنوع است.")
        LAST_MESSAGES[user.id] = text

    # ادامه بررسی سایر قفل‌ها ...
    # 🚫 همه لینک‌ ها
    if locks.get("all_links") and any(x in text for x in ["http://", "https://", "t.me", "telegram.me"]):
        return await _del_msg(update, "🚫 ارسال هرگونه لینک ممنوع است.")

    # 🚫 لینک ویدیو
    if locks.get("urls_videos") and any(x in text for x in ["youtube.com", "youtu.be", "tiktok.com"]):
        return await _del_msg(update, "🚫 ارسال لینک ویدیو ممنوع است.")

    # 🚫 لینک کوتاه
    if locks.get("short_links") and any(x in text for x in ["bit.ly", "tinyurl.com", "t2m.io"]):
        return await _del_msg(update, "🚫 ارسال لینک کوتاه ممنوع است.")

    # 🚫 ربات تبچی (Inline Bots)
    if locks.get("inline_bots") and getattr(msg, "via_bot", None):
        return await _del_msg(update, "🚫 استفاده از ربات اینلاین ممنوع است.")
        
   # 🚫 پیام طولانی
    if locks.get("long_text") and len(text) > 200:   # اینجا 200 یعنی حد مجاز
        return await _del_msg(update, "🚫 ارسال پیام طولانی ممنوع است.")

    # 🚫 حروف بزرگ
    if locks.get("capslock") and text.isupper():
        return await _del_msg(update, "🚫 پیام با حروف بزرگ ممنوع است.")

    # 🚫 لینک
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

    # 🚫 تگ
    if locks.get("tag") and "@" in text:
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

# ─────────────────────────────── فعال‌سازی / غیرفعال‌سازی قفل ───────────────────────────────

async def handle_lock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    """فعال‌سازی قفل"""
    chat = update.effective_chat
    user = update.effective_user

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

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
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    if key not in LOCK_TYPES:
        return

    if not _is_locked(chat.id, key):
        return await update.message.reply_text(f"🔓 قفل {LOCK_TYPES[key]} از قبل باز است.")

    _set_lock(chat.id, key, False)
    global LOCKS
    LOCKS = _load_json(LOCK_FILE, {})  # ← بروزرسانی حافظه بعد از تغییر

    await update.message.reply_text(f"🔓 قفل {LOCK_TYPES[key]} باز شد.")
    
    # ─────────────────────────────── قفل و قفل خودکار گروه ───────────────────────────────
import os
import json
from datetime import datetime, time
from telegram import ChatPermissions

# مسیر فایل قفل خودکار
AUTO_LOCK_FILE = os.path.join(BASE_DIR, "auto_lock.json")
if not os.path.exists(AUTO_LOCK_FILE):
    with open(AUTO_LOCK_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

def _load_auto_lock():
    try:
        with open(AUTO_LOCK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def _save_auto_lock(data):
    with open(AUTO_LOCK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

AUTO_LOCKS = _load_auto_lock()

# ──────────────── قفل و باز کردن گروه ────────────────
async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قفل کردن کل گروه (غیرفعال کردن ارسال پیام‌ها)"""
    chat = update.effective_chat
    user = update.effective_user

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    await context.bot.set_chat_permissions(chat.id, ChatPermissions(can_send_messages=False))
    await update.message.reply_text(
        f"🔒 گروه توسط <b>{user.first_name}</b> قفل شد تا اطلاع ثانوی.",
        parse_mode="HTML"
    )

async def unlock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """باز کردن کل گروه"""
    chat = update.effective_chat
    user = update.effective_user

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    await context.bot.set_chat_permissions(chat.id, ChatPermissions(can_send_messages=True))
    await update.message.reply_text(
        f"🔓 گروه توسط <b>{user.first_name}</b> باز شد.",
        parse_mode="HTML"
    )

# ──────────────── قفل خودکار ────────────────
async def auto_lock_check(context: ContextTypes.DEFAULT_TYPE):
    """چک کردن خودکار زمان قفل گروه‌ها (هر دقیقه توسط JobQueue)"""
    now = datetime.now().time()
    for chat_id, conf in AUTO_LOCKS.items():
        try:
            if not conf.get("enabled", False):
                continue  # اگر خاموش است، رد شو

            start = time.fromisoformat(conf["start"])
            end = time.fromisoformat(conf["end"])

            # اگر در بازهٔ زمانی قفل است
            if start <= now <= end:
                await context.bot.set_chat_permissions(
                    int(chat_id), ChatPermissions(can_send_messages=False)
                )
            else:
                await context.bot.set_chat_permissions(
                    int(chat_id), ChatPermissions(can_send_messages=True)
                )
        except Exception as e:
            print(f"[AutoLock Error] {e}")

# ──────────────── تنظیم، روشن و خاموش کردن ────────────────
async def enable_auto_lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """روشن کردن قفل خودکار"""
    chat = update.effective_chat
    user = update.effective_user

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    if str(chat.id) not in AUTO_LOCKS:
        return await update.message.reply_text("⚙️ ابتدا ساعت قفل خودکار را با دستور زیر مشخص کنید:\n📘 تنظیم قفل خودکار 23:00 07:00")

    AUTO_LOCKS[str(chat.id)]["enabled"] = True
    _save_auto_lock(AUTO_LOCKS)
    info = AUTO_LOCKS[str(chat.id)]
    await update.message.reply_text(
        f"✅ قفل خودکار فعال شد.\n🕓 از ساعت <b>{info['start']}</b> تا <b>{info['end']}</b>",
        parse_mode="HTML"
    )

async def disable_auto_lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """خاموش کردن قفل خودکار"""
    chat = update.effective_chat
    user = update.effective_user

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    if str(chat.id) not in AUTO_LOCKS:
        return await update.message.reply_text("⚙️ قفل خودکار هنوز تنظیم نشده است.")

    AUTO_LOCKS[str(chat.id)]["enabled"] = False
    _save_auto_lock(AUTO_LOCKS)
    await update.message.reply_text("❎ قفل خودکار گروه خاموش شد.")

async def set_auto_lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تنظیم ساعت قفل خودکار - مثال: تنظیم قفل خودکار 23:00 07:00"""
    chat = update.effective_chat
    user = update.effective_user

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    args = (update.message.text or "").split()
    if len(args) != 3:
        return await update.message.reply_text("📘 مثال صحیح:\n<code>تنظیم قفل خودکار 23:00 07:00</code>", parse_mode="HTML")

    start, end = args[1], args[2]
    try:
        time.fromisoformat(start)
        time.fromisoformat(end)
    except:
        return await update.message.reply_text("⚠️ فرمت ساعت نادرست است. (مثلاً 22:30)")

    AUTO_LOCKS[str(chat.id)] = {"start": start, "end": end, "enabled": True}
    _save_auto_lock(AUTO_LOCKS)
    await update.message.reply_text(
        f"✅ قفل خودکار از ساعت <b>{start}</b> تا <b>{end}</b> تنظیم و فعال شد.",
        parse_mode="HTML"
    )

# ──────────────── تشخیص دستورات قفل گروه ────────────────
async def handle_group_lock_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشخیص و اجرای دستور قفل گروه / قفل خودکار"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip().lower()

    if text == "قفل گروه":
        return await lock_group(update, context)
    if text in ["باز کردن گروه", "بازکردن گروه"]:
        return await unlock_group(update, context)
    if text == "قفل خودکار روشن":
        return await enable_auto_lock(update, context)
    if text == "قفل خودکار خاموش":
        return await disable_auto_lock(update, context)
    if text.startswith("تنظیم قفل خودکار"):
        return await set_auto_lock(update, context)
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

# ─────────────────────────────── هندلر مرکزی گروه ───────────────────────────────
async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر اصلی پیام‌های گروه"""

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

    # ───────────── بررسی دستورات قفل / باز کردن ─────────────
    if text.startswith("قفل ") or text.startswith("باز کردن ") or text.startswith("بازکردن "):
        return await handle_lock_commands(update, context)

    # ───────────── بررسی دستورات قفل گروه و قفل خودکار ─────────────
    result = await handle_group_lock_commands(update, context)
    if result:
        return

    # ───────────── در نهایت بررسی پیام‌ها مطابق قفل‌ها ─────────────
    await check_message_locks(update, context)
