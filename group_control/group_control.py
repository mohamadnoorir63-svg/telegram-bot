import os
import json
import re
import asyncio
from datetime import datetime, time
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes

# ─────────────────────────────── تنظیمات دسترسی ───────────────────────────────

SUDO_IDS = [8588347189]  # آیدی سودو

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────────── فایل‌ها ───────────────────────────────
LOCK_FILE = os.path.join(BASE_DIR, "group_locks.json")
VIPS_FILE = os.path.join(BASE_DIR, "vip_users.json")
AUTO_LOCK_FILE = os.path.join(BASE_DIR, "auto_lock.json")

for f in [LOCK_FILE, VIPS_FILE, AUTO_LOCK_FILE]:
    if not os.path.exists(f):
        with open(f, "w", encoding="utf-8") as fw:
            json.dump({}, fw, ensure_ascii=False, indent=2)

# ─────────────────────────────── لود و ذخیره JSON ───────────────────────────────
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
VIPS = _load_json(VIPS_FILE, {})
AUTO_LOCKS = _load_json(AUTO_LOCK_FILE, {})

# ─────────────────────────────── دسترسی کاربران ───────────────────────────────
async def _is_admin_or_sudo(context, chat_id: int, user_id: int) -> bool:
    """بررسی اینکه کاربر مدیر گروه یا سودو هست یا نه"""
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
    """سودو + مدیر + VIP = دسترسی کامل"""
    if user_id in SUDO_IDS:
        return True
    if await _is_admin_or_sudo(context, chat_id, user_id):
        return True
    if _is_vip(chat_id, user_id):
        return True
    return False

# ─────────────────────────────── مدیریت VIP ───────────────────────────────
def add_vip(chat_id: int, user_id: int):
    cid = str(chat_id)
    if cid not in VIPS:
        VIPS[cid] = []
    if user_id not in VIPS[cid]:
        VIPS[cid].append(user_id)
        _save_json(VIPS_FILE, VIPS)

def remove_vip(chat_id: int, user_id: int):
    cid = str(chat_id)
    if cid in VIPS and user_id in VIPS[cid]:
        VIPS[cid].remove(user_id)
        _save_json(VIPS_FILE, VIPS)

# ─────────────────────────────── لیست قفل‌ها ───────────────────────────────
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

# ─────────────────────────────── مدیریت قفل‌ها ───────────────────────────────
def _get_locks(chat_id: int):
    return LOCKS.get(str(chat_id), {})

def _set_lock(chat_id: int, key: str, status: bool):
    cid = str(chat_id)
    if cid not in LOCKS:
        LOCKS[cid] = {}
    LOCKS[cid][key] = bool(status)
    _save_json(LOCK_FILE, LOCKS)

def _is_locked(chat_id: int, key: str) -> bool:
    return LOCKS.get(str(chat_id), {}).get(key, False)

# ─────────────────────────────── حذف پیام ───────────────────────────────
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
        # ─────────────────────────────── بررسی پیام‌ها ───────────────────────────────
async def check_message_locks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    msg = update.message
    text = (msg.text or msg.caption or "").lower()
    chat = msg.chat
    user = msg.from_user
    locks = _get_locks(chat.id)
    if not any(locks.values()):
        return

    # مدیران، سودوها و VIPها معاف هستند
    if await _has_full_access(context, chat.id, user.id):
        return

    has_photo = bool(msg.photo)
    has_video = bool(msg.video)
    has_doc = bool(msg.document)
    has_voice = bool(msg.voice)
    has_anim = bool(msg.animation)
    has_stick = bool(msg.sticker)
    has_fwd = bool(msg.forward_date)

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
    if (locks.get("usernames") or locks.get("mention")) and "@" in text:
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

# ─────────────────────────────── دستورات VIP ───────────────────────────────
async def handle_vip_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip().lower()
    chat = update.effective_chat

    if text.startswith("افزودن ویژه"):
        try:
            user_id = int(text.split()[1])
            add_vip(chat.id, user_id)
            await update.message.reply_text(f"✅ کاربر {user_id} ویژه شد.")
        except:
            await update.message.reply_text("⚠️ لطفاً آیدی کاربر را صحیح وارد کنید.")
    elif text.startswith("حذف ویژه"):
        try:
            user_id = int(text.split()[1])
            remove_vip(chat.id, user_id)
            await update.message.reply_text(f"❌ کاربر {user_id} از ویژه خارج شد.")
        except:
            await update.message.reply_text("⚠️ لطفاً آیدی کاربر را صحیح وارد کنید.")

# ─────────────────────────────── ادامه: قفل گروه و قفل خودکار ───────────────────────────────
# (این بخش شامل lock_group, unlock_group, auto_lock_check, set_auto_lock و handle_lock_commands است که با VIP یکپارچه شده‌اند)
# ─────────────────────────────── فعال / غیرفعال کردن قفل‌ها ───────────────────────────────
async def handle_lock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
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
    LOCKS = _load_json(LOCK_FILE, {})
    await update.message.reply_text(f"✅ قفل {LOCK_TYPES[key]} فعال شد.")

async def handle_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
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
    LOCKS = _load_json(LOCK_FILE, {})
    await update.message.reply_text(f"🔓 قفل {LOCK_TYPES[key]} باز شد.")

# ─────────────────────────────── هندلر دستورات قفل محتوایی ───────────────────────────────
async def handle_lock_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip().lower()
    for key, fa in LOCK_TYPES.items():
        if text == f"قفل {fa}":
            return await handle_lock(update, context, key)
        if text in (f"باز کردن {fa}", f"بازکردن {fa}"):
            return await handle_unlock(update, context, key)

# ─────────────────────────────── قفل / باز کردن کل گروه ───────────────────────────────
async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
    await context.bot.set_chat_permissions(chat.id, ChatPermissions(can_send_messages=False))
    await update.message.reply_text(
        f"🔒 گروه توسط <b>{user.first_name}</b> قفل شد.",
        parse_mode="HTML"
    )

async def unlock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
    await context.bot.set_chat_permissions(chat.id, ChatPermissions(can_send_messages=True))
    await update.message.reply_text(
        f"🔓 گروه توسط <b>{user.first_name}</b> باز شد.",
        parse_mode="HTML"
    )

# ─────────────────────────────── قفل خودکار ───────────────────────────────
async def auto_lock_check(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now().time()
    for chat_id, conf in AUTO_LOCKS.items():
        try:
            if not conf.get("enabled", False):
                continue
            start = time.fromisoformat(conf["start"])
            end = time.fromisoformat(conf["end"])
            perms = ChatPermissions(can_send_messages=False if start <= now <= end else True)
            await context.bot.set_chat_permissions(int(chat_id), perms)
        except Exception as e:
            print(f"[AutoLock Error] {e}")

async def set_auto_lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
    args = (update.message.text or "").split()
    if len(args) != 3:
        return await update.message.reply_text("📘 مثال: <code>تنظیم قفل خودکار 23:00 07:00</code>", parse_mode="HTML")
    start, end = args[1], args[2]
    try:
        time.fromisoformat(start)
        time.fromisoformat(end)
    except:
        return await update.message.reply_text("⚠️ فرمت ساعت نادرست است.")
    AUTO_LOCKS[str(chat.id)] = {"start": start, "end": end, "enabled": True}
    _save_json(AUTO_LOCK_FILE, AUTO_LOCKS)
    await update.message.reply_text(f"✅ قفل خودکار از {start} تا {end} تنظیم شد.", parse_mode="HTML")

async def enable_auto_lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if str(chat.id) not in AUTO_LOCKS:
        return await update.message.reply_text("⚙️ ابتدا ساعت قفل خودکار را تنظیم کنید.")
    AUTO_LOCKS[str(chat.id)]["enabled"] = True
    _save_json(AUTO_LOCK_FILE, AUTO_LOCKS)
    info = AUTO_LOCKS[str(chat.id)]
    await update.message.reply_text(f"✅ قفل خودکار فعال شد از {info['start']} تا {info['end']}", parse_mode="HTML")

async def disable_auto_lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if str(chat.id) not in AUTO_LOCKS:
        return await update.message.reply_text("⚙️ قفل خودکار هنوز تنظیم نشده است.")
    AUTO_LOCKS[str(chat.id)]["enabled"] = False
    _save_json(AUTO_LOCK_FILE, AUTO_LOCKS)
    await update.message.reply_text("❎ قفل خودکار گروه خاموش شد.")

# ─────────────────────────────── هندلر مرکزی پیام‌ها ───────────────────────────────
async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_message_locks(update, context)
    await handle_vip_commands(update, context)
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip().lower()
    # دستورات قفل محتوایی
    if text.startswith("قفل ") or text.startswith("باز کردن ") or text.startswith("بازکردن "):
        await handle_lock_commands(update, context)
    # دستورات قفل گروه و خودکار
    if text == "قفل گروه":
        await lock_group(update, context)
    elif text in ["باز کردن گروه", "بازکردن گروه"]:
        await unlock_group(update, context)
    elif text == "قفل خودکار روشن":
        await enable_auto_lock(update, context)
    elif text == "قفل خودکار خاموش":
        await disable_auto_lock(update, context)
    elif text.startswith("تنظیم قفل خودکار"):
        await set_auto_lock(update, context)
