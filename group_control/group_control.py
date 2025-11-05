import os
import json
import re
import asyncio
from datetime import datetime
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from collections import deque

# لاگ پیام‌ها: برای هر چت یک صف محدود
MESSAGE_LOG: dict[str, deque] = {}
MAX_LOG_PER_CHAT = 2000  # حداکثر پیام‌هایی که برای هر چت نگه می‌داریم

# تاخیرهای حذف
MAX_DELETE = 1000
DELETE_DELAY = 0.05
# ─────────────────────────────── بررسی سودو، مدیر و دسترسی کامل ───────────────────────────────

# آیدی سودوی اصلی خودت
SUDO_IDS = [8588347189]  # آیدی خودت رو اینجا بذار

async def _is_admin_or_sudo(context, chat_id: int, user_id: int) -> bool:
    """بررسی اینکه کاربر مدیر گروه یا سودو هست یا نه"""
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except:
        return False


# اگر بعداً تابع full access داری، همین‌جا بذارش:
def _is_vip(chat_id: int, user_id: int) -> bool:
    """بررسی کاربر ویژه (در صورت موجود بودن فایل VIP)"""
    try:
        return user_id in VIPS.get(str(chat_id), [])
    except:
        return False


async def _has_full_access(context, chat_id: int, user_id: int) -> bool:
    """سودو + مدیر + ویژه = دسترسی کامل"""
    if user_id in SUDO_IDS:
        return True
    if await _is_admin_or_sudo(context, chat_id, user_id):
        return True
    if _is_vip(chat_id, user_id):
        return True
    return False
# ─────────────────────────────── مسیر فایل ───────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def path(filename: str) -> str:
    """برمی‌گردونه مسیر کامل فایل داخل فولدر group_control"""
    return os.path.join(BASE_DIR, filename)

LOCK_TYPES = {
    "group": "گروه",
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


# ─────────────────────────────── فایل ذخیره قفل‌ها ───────────────────────────────

LOCK_FILE = path("group_locks.json")

if not os.path.exists(LOCK_FILE):
    with open(LOCK_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

# ─────────────────────────────── توابع کمکی فایل ───────────────────────────────

def _load_json(path, default=None):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ خطا در لود {path}: {e}")
    return default or {}

def _save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ خطا در ذخیره {path}: {e}")

# ─────────────────────────────── مدیریت قفل‌ها ───────────────────────────────

LOCKS = _load_json(LOCK_FILE, {})

def _get_locks(chat_id: int):
    return LOCKS.get(str(chat_id), {})

def _set_lock(chat_id: int, key: str, status: bool):
    """ذخیره و آپدیت قفل در حافظه و فایل"""
    global LOCKS
    cid = str(chat_id)
    locks = LOCKS.get(cid, {})
    locks[key] = bool(status)
    LOCKS[cid] = locks
    _save_json(LOCK_FILE, LOCKS)
    LOCKS = _load_json(LOCK_FILE)

# ─────────────────────────────── بررسی مدیر یا سودو ───────────────────────────────
# ─────────────────────────────── بررسی دسترسی کامل ───────────────────────────────

async def _has_full_access(context, chat_id: int, user_id: int) -> bool:
    """
    بررسی اینکه آیا کاربر دسترسی کامل دارد یا نه:
    ✅ شامل سودوها، مدیران، و کاربران ویژه
    """
    if _is_sudo(user_id):
        return True
    if await _is_admin_or_sudo(context, chat_id, user_id):
        return True
    if _is_vip(chat_id, user_id):
        return True
    return False


# ─────────────────────────────── حذف پیام ممنوع ───────────────────────────────

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

# ─────────────────────────────── قفل‌ها ───────────────────────────────

async def handle_lock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    chat = update.effective_chat
    user = update.effective_user

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    if key not in LOCK_TYPES:
        return await update.message.reply_text("⚠️ نام قفل معتبر نیست.")

    _set_lock(chat.id, key, True)
    await update.message.reply_text(f"🔒 قفل <b>{LOCK_TYPES[key]}</b> فعال شد.", parse_mode="HTML")

async def handle_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    chat = update.effective_chat
    user = update.effective_user

    if not await _is_admin_or_sudo(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    if key not in LOCK_TYPES:
        return await update.message.reply_text("⚠️ نام قفل معتبر نیست.")

    _set_lock(chat.id, key, False)
    await update.message.reply_text(f"🔓 قفل <b>{LOCK_TYPES[key]}</b> باز شد.", parse_mode="HTML")

# ─────────────────────────────── کنترل پیام‌های ورودی ───────────────────────────────

async def check_message_locks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بررسی پیام و اعمال قفل‌ها"""
    if not update.message:
        return

    msg = update.message
    text = (msg.text or msg.caption or "").lower()
    chat = msg.chat
    user = msg.from_user

    locks = _get_locks(chat.id)
    if not any(locks.values()):
        return  # هیچ قفلی فعال نیست

    # مدیران و سودوها از قفل‌ها مستثنی‌اند
    if await _is_admin_or_sudo(context, chat.id, user.id):
        return

    # خصوصیات پیام
    has_photo = bool(msg.photo)
    has_video = bool(msg.video)
    has_doc = bool(msg.document)
    has_voice = bool(msg.voice)
    has_anim = bool(msg.animation)
    has_stick = bool(msg.sticker)
    has_fwd = bool(msg.forward_date)

    # 🚫 قفل لینک‌ها
    if locks.get("links") and any(x in text for x in ["http://", "https://", "t.me", "telegram.me"]):
        return await _del_msg(update, "🚫 ارسال لینک ممنوع است.")

    # 🚫 تبلیغ
    if locks.get("ads") and any(x in text for x in ["joinchat", "promo", "invite", "bot?start=", "channel"]):
        return await _del_msg(update, "🚫 تبلیغات در گروه ممنوع است.")

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

    # 🚫 منشن و یوزرنیم
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

# ─────────────────────────────── دستورات قفل و بازکردن ───────────────────────────────

async def handle_lock_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اجرای دستورات قفل / بازکردن بر اساس متن"""
    text = (update.message.text or "").strip().lower()

    for key, fa in LOCK_TYPES.items():
        if text == f"قفل {fa}":
            return await handle_lock(update, context, key)
        if text == f"بازکردن {fa}" or text == f"باز کردن {fa}":
            return await handle_unlock(update, context, key)

    # 🆕 اگر هیچ قفلی match نشد:
    await update.message.reply_text("⚠️ دستور قفل یا بازکردن نامعتبر است.")
# ==========================================================

AUTOLOCK_FILE = path("autolock.json")

if not os.path.exists(AUTOLOCK_FILE):
    with open(AUTOLOCK_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

AUTOLOCKS = _load_json(AUTOLOCK_FILE, {})

def _save_autolocks():
    _save_json(AUTOLOCK_FILE, AUTOLOCKS)

# ─────────────────────────────── قفل گروه دستی ───────────────────────────────

async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قفل کردن کل گروه (ممنوعیت ارسال پیام برای اعضا)"""
    chat = update.effective_chat
    user = update.effective_user

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌تونن گروه رو قفل کنن.")

    try:
        await context.bot.set_chat_permissions(
            chat.id,
            ChatPermissions(can_send_messages=False)
        )
        await update.message.reply_text(
            f"🔒 گروه توسط <b>{user.first_name}</b> قفل شد.\n📴 ارسال پیام برای اعضا غیرفعال شد.",
            parse_mode="HTML"
        )
        _set_lock(chat.id, "group", True)
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در قفل گروه:\n<code>{e}</code>", parse_mode="HTML")

# ─────────────────────────────── بازکردن گروه دستی ───────────────────────────────

async def unlock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """باز کردن کل گروه (فعال کردن ارسال پیام)"""
    chat = update.effective_chat
    user = update.effective_user

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌تونن گروه رو باز کنن.")

    try:
        await context.bot.set_chat_permissions(
            chat.id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_invite_users=True,
            )
        )
        await update.message.reply_text(
            f"✅ گروه توسط <b>{user.first_name}</b> باز شد.\n💬 کاربران می‌تونن پیام بفرستن.",
            parse_mode="HTML"
        )
        _set_lock(chat.id, "group", False)
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در باز کردن گروه:\n<code>{e}</code>", parse_mode="HTML")

# ─────────────────────────────── تنظیم قفل خودکار ───────────────────────────────

async def set_auto_lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    تنظیم زمان قفل خودکار گروه
    مثال: تنظیم قفل خودکار 23:00 06:00
    """
    chat = update.effective_chat
    user = update.effective_user

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌تونن تنظیم کنن.")

    parts = update.message.text.split()
    if len(parts) != 4:
        return await update.message.reply_text(
            "📘 مثال:\n<code>تنظیم قفل خودکار 23:00 06:00</code>", parse_mode="HTML"
        )

    start_time, end_time = parts[2], parts[3]
    try:
        datetime.strptime(start_time, "%H:%M")
        datetime.strptime(end_time, "%H:%M")
    except:
        return await update.message.reply_text("⚠️ ساعت باید به‌صورت HH:MM باشه مثل 23:00")

    AUTOLOCKS[str(chat.id)] = {"start": start_time, "end": end_time, "enabled": True}
    _save_autolocks()

    await update.message.reply_text(
        f"⏰ قفل خودکار فعال شد!\n🔒 قفل در: <b>{start_time}</b>\n🔓 باز شدن در: <b>{end_time}</b>",
        parse_mode="HTML"
    )

# ─────────────────────────────── خاموش کردن قفل خودکار ───────────────────────────────

async def disable_auto_lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """خاموش کردن قفل خودکار گروه"""
    chat = update.effective_chat
    user = update.effective_user

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    if str(chat.id) in AUTOLOCKS:
        AUTOLOCKS[str(chat.id)]["enabled"] = False
        _save_autolocks()
        await update.message.reply_text("🕓 قفل خودکار غیرفعال شد.")
    else:
        await update.message.reply_text("ℹ️ قفل خودکار از قبل تنظیم نشده بود.")

# ─────────────────────────────── بررسی خودکار زمان‌بندی ───────────────────────────────

async def check_auto_lock(context: ContextTypes.DEFAULT_TYPE):
    """اجرای خودکار قفل و باز کردن گروه طبق زمان‌بندی"""
    now = datetime.now().strftime("%H:%M")

    for chat_id, cfg in AUTOLOCKS.items():
        if not cfg.get("enabled", False):
            continue

        start = cfg.get("start")
        end = cfg.get("end")
        if not start or not end:
            continue

        # بازه زمانی بین start تا end
        if start <= now or now < end:
            # قفل کردن گروه
            try:
                await context.bot.set_chat_permissions(
                    int(chat_id),
                    ChatPermissions(can_send_messages=False)
                )
                _set_lock(int(chat_id), "group", True)
                print(f"[AUTOLOCK] Group {chat_id} closed at {now}")
            except Exception as e:
                print(f"[AUTOLOCK ERROR] {e}")
        else:
            # باز کردن گروه
            try:
                await context.bot.set_chat_permissions(
                    int(chat_id),
                    ChatPermissions(
                        can_send_messages=True,
                        can_send_media_messages=True,
                        can_send_polls=True,
                        can_send_other_messages=True,
                        can_add_web_page_previews=True,
                        can_invite_users=True,
                    )
                )
                _set_lock(int(chat_id), "group", False)
                print(f"[AUTOLOCK] Group {chat_id} opened at {now}")
            except Exception as e:
                print(f"[AUTOLOCK ERROR] {e}")

# ─────────────────────────────── دستورات کاربر ───────────────────────────────

async def handle_group_lock_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اجرای دستورات قفل گروه"""
    text = (update.message.text or "").strip().lower()

    if text in ["قفل گروه", "بستن گروه"]:
        return await lock_group(update, context)
    if text in ["باز کردن گروه", "بازکردن گروه", "باز کردن"]:
        return await unlock_group(update, context)
    if text.startswith("تنظیم قفل خودکار"):
        return await set_auto_lock(update, context)
    if text in ["قفل خودکار خاموش", "خاموش کردن قفل خودکار"]:
        return await disable_auto_lock(update, context)
        # ==========================================================
# 🧱 بخش ۳ — فیلتر کلمات (Filter System)
# ==========================================================

FILTER_FILE = path("filters.json")

if not os.path.exists(FILTER_FILE):
    with open(FILTER_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

FILTERS = _load_json(FILTER_FILE, {})

def _save_filters():
    _save_json(FILTER_FILE, FILTERS)

# ─────────────────────────────── افزودن فیلتر ───────────────────────────────

async def add_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """افزودن یک کلمه به لیست فیلتر"""
    chat = update.effective_chat
    user = update.effective_user
    text = (update.message.text or "").strip()

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران و سودوها مجازند.")

    parts = text.split("فیلتر", 1)
    if len(parts) < 2 or not parts[1].strip():
        return await update.message.reply_text("📘 مثال: <code>فیلتر سگ</code>", parse_mode="HTML")

    word = parts[1].strip().lower()
    chat_id = str(chat.id)

    FILTERS.setdefault(chat_id, [])
    if word in FILTERS[chat_id]:
        return await update.message.reply_text("ℹ️ این کلمه از قبل فیلتر شده است.")

    FILTERS[chat_id].append(word)
    _save_filters()

    await update.message.reply_text(f"🚫 کلمه <b>{word}</b> به لیست فیلترها اضافه شد.", parse_mode="HTML")

# ─────────────────────────────── حذف فیلتر ───────────────────────────────

async def remove_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف یک کلمه از فیلتر"""
    chat = update.effective_chat
    user = update.effective_user
    text = (update.message.text or "").strip()

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران و سودوها مجازند.")

    parts = text.split("حذف فیلتر", 1)
    if len(parts) < 2 or not parts[1].strip():
        return await update.message.reply_text("📘 مثال: <code>حذف فیلتر سگ</code>", parse_mode="HTML")

    word = parts[1].strip().lower()
    chat_id = str(chat.id)

    if chat_id not in FILTERS or word not in FILTERS[chat_id]:
        return await update.message.reply_text("ℹ️ این کلمه در لیست فیلتر نیست.")

    FILTERS[chat_id].remove(word)
    _save_filters()

    await update.message.reply_text(f"✅ کلمه <b>{word}</b> از فیلترها حذف شد.", parse_mode="HTML")

# ─────────────────────────────── لیست فیلترها ───────────────────────────────

async def list_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست کلمات فیلترشده"""
    chat_id = str(update.effective_chat.id)
    chat_filters = FILTERS.get(chat_id, [])

    if not chat_filters:
        return await update.message.reply_text("✅ هیچ کلمه‌ای فیلتر نشده است.")

    text = "<b>🚫 لیست کلمات فیلتر شده:</b>\n\n"
    for i, word in enumerate(chat_filters, 1):
        text += f"{i}. {word}\n"

    await update.message.reply_text(text, parse_mode="HTML")

# ─────────────────────────────── بررسی پیام‌ها ───────────────────────────────

async def check_filtered_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بررسی پیام‌ها برای کلمات فیلترشده"""
    if not update.message or not update.message.text:
        return

    msg = update.message
    chat = msg.chat
    user = msg.from_user
    text = msg.text.lower()
    chat_id = str(chat.id)

    # مدیرها و سودوها معافند
    if await _is_admin_or_sudo(context, chat.id, user.id):
        return

    chat_filters = FILTERS.get(chat_id, [])
    if not chat_filters:
        return

    for word in chat_filters:
        # بررسی کلمه به صورت جداگانه
        if re.search(rf"\b{re.escape(word)}\b", text):
            try:
                await msg.delete()
                warn = await msg.chat.send_message(
                    f"🚫 پیام شما به دلیل استفاده از کلمه <b>{word}</b> حذف شد.",
                    parse_mode="HTML"
                )
                await asyncio.sleep(4)
                await warn.delete()
            except Exception as e:
                print(f"[Filter Error] {e}")
            break  # فقط اولین تطبیق کافی‌ست

# ─────────────────────────────── دستورات فیلتر ───────────────────────────────

async def handle_filter_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستورات فیلتر / حذف فیلتر / لیست فیلتر"""
    text = (update.message.text or "").strip().lower()

    if text.startswith("فیلتر "):
        return await add_filter(update, context)
    if text.startswith("حذف فیلتر "):
        return await remove_filter(update, context)
    if text in ["لیست فیلتر", "لیست فیلترها"]:
        return await list_filters(update, context)
        # ==========================================================
# 🧱 بخش ۴ — بن، سکوت، اخطار و حذف آن‌ها
# ==========================================================

PUNISH_FILE = path("punishments.json")

if not os.path.exists(PUNISH_FILE):
    with open(PUNISH_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

PUNISH_DATA = _load_json(PUNISH_FILE, {})

def _save_punish():
    _save_json(PUNISH_FILE, PUNISH_DATA)

# ─────────────────────────────── بررسی نقش هدف ───────────────────────────────

async def _check_target(update: Update, context: ContextTypes.DEFAULT_TYPE, target):
    """بررسی هدف برای جلوگیری از بن یا اخطار اشتباهی"""
    me = await context.bot.get_me()

    if target.id == me.id:
        await update.message.reply_text("😅 منو می‌خوای بن کنی؟! من فقط رباتم!")
        return False

    if target.id in SUDO_IDS:
        await update.message.reply_text("👑 این کاربر سودو رباته — نمی‌تونی کاریش کنی!")
        return False

    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, target.id)
        if member.status in ("administrator", "creator"):
            await update.message.reply_text("🛡️ این کاربر مدیر گروهه — نمی‌تونی بن یا سکوتش کنی!")
            return False
    except:
        pass

    return True

# ─────────────────────────────── بن ───────────────────────────────

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بن کردن کاربر"""
    chat = update.effective_chat
    user = update.effective_user
    reply = update.message.reply_to_message

    if not reply:
        return await update.message.reply_text("📎 روی پیام کسی ریپلای کن و بن بنویس.")

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌تونن بن کنن.")

    target = reply.from_user
    if not await _check_target(update, context, target):
        return

    try:
        await context.bot.ban_chat_member(chat.id, target.id)
        PUNISH_DATA.setdefault(str(chat.id), {}).setdefault("banned", [])
        if target.id not in PUNISH_DATA[str(chat.id)]["banned"]:
            PUNISH_DATA[str(chat.id)]["banned"].append(target.id)
        _save_punish()
        await update.message.reply_text(f"🚫 <b>{target.first_name}</b> بن شد.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بن:\n<code>{e}</code>", parse_mode="HTML")

# ─────────────────────────────── حذف بن ───────────────────────────────

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رفع بن کاربر"""
    chat = update.effective_chat
    user = update.effective_user
    reply = update.message.reply_to_message

    if not reply:
        return await update.message.reply_text("📎 روی پیام کاربر بن‌شده ریپلای کن و بن حذف کن.")

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    target = reply.from_user
    try:
        await context.bot.unban_chat_member(chat.id, target.id)
        if str(chat.id) in PUNISH_DATA:
            PUNISH_DATA[str(chat.id)].get("banned", []).remove(target.id)
            _save_punish()
        await update.message.reply_text(f"✅ <b>{target.first_name}</b> از بن خارج شد.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در حذف بن:\n<code>{e}</code>", parse_mode="HTML")

# ─────────────────────────────── سکوت ───────────────────────────────

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ساکت کردن کاربر"""
    chat = update.effective_chat
    user = update.effective_user
    reply = update.message.reply_to_message

    if not reply:
        return await update.message.reply_text("📎 روی پیام کسی ریپلای کن و سکوت بنویس.")

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    target = reply.from_user
    if not await _check_target(update, context, target):
        return

    try:
        await context.bot.restrict_chat_member(
            chat.id, target.id, permissions=ChatPermissions(can_send_messages=False)
        )
        PUNISH_DATA.setdefault(str(chat.id), {}).setdefault("muted", [])
        if target.id not in PUNISH_DATA[str(chat.id)]["muted"]:
            PUNISH_DATA[str(chat.id)]["muted"].append(target.id)
        _save_punish()
        await update.message.reply_text(f"🤐 <b>{target.first_name}</b> در سکوت قرار گرفت.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در سکوت:\n<code>{e}</code>", parse_mode="HTML")

# ─────────────────────────────── حذف سکوت ───────────────────────────────

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف سکوت کاربر"""
    chat = update.effective_chat
    user = update.effective_user
    reply = update.message.reply_to_message

    if not reply:
        return await update.message.reply_text("📎 روی پیام کاربر سکوت‌شده ریپلای کن و حذف سکوت بنویس.")

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    target = reply.from_user
    try:
        await context.bot.restrict_chat_member(chat.id, target.id, permissions=ChatPermissions(can_send_messages=True))
        if str(chat.id) in PUNISH_DATA:
            PUNISH_DATA[str(chat.id)].get("muted", []).remove(target.id)
            _save_punish()
        await update.message.reply_text(f"✅ <b>{target.first_name}</b> از سکوت خارج شد.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در حذف سکوت:\n<code>{e}</code>", parse_mode="HTML")

# ─────────────────────────────── اخطار ───────────────────────────────

async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دادن اخطار به کاربر"""
    chat = update.effective_chat
    user = update.effective_user
    reply = update.message.reply_to_message

    if not reply:
        return await update.message.reply_text("📎 روی پیام کسی ریپلای کن و اخطار بنویس.")

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    target = reply.from_user
    if not await _check_target(update, context, target):
        return

    chat_id = str(chat.id)
    PUNISH_DATA.setdefault(chat_id, {}).setdefault("warns", {})
    warns = PUNISH_DATA[chat_id]["warns"]
    warns[str(target.id)] = warns.get(str(target.id), 0) + 1
    _save_punish()

    if warns[str(target.id)] >= 3:
        await ban_user(update, context)
        del warns[str(target.id)]
        _save_punish()
        await update.message.reply_text(f"🚨 {target.first_name} با ۳ اخطار بن شد!", parse_mode="HTML")
    else:
        await update.message.reply_text(f"⚠️ به {target.first_name} اخطار داده شد ({warns[str(target.id)]}/3)", parse_mode="HTML")

# ─────────────────────────────── حذف اخطار ───────────────────────────────

async def remove_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف یک اخطار از کاربر"""
    chat = update.effective_chat
    user = update.effective_user
    reply = update.message.reply_to_message

    if not reply:
        return await update.message.reply_text("📎 روی پیام کسی ریپلای کن و حذف اخطار بنویس.")
    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    target = reply.from_user
    chat_id = str(chat.id)
    warns = PUNISH_DATA.get(chat_id, {}).get("warns", {})

    if str(target.id) not in warns:
        return await update.message.reply_text("ℹ️ این کاربر اخطاری ندارد.")

    warns[str(target.id)] -= 1
    if warns[str(target.id)] <= 0:
        del warns[str(target.id)]
    _save_punish()

    await update.message.reply_text(f"✅ یک اخطار از {target.first_name} حذف شد.", parse_mode="HTML")

# ─────────────────────────────── لیست سکوت و اخطار ───────────────────────────────

async def list_mutes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    muted = PUNISH_DATA.get(chat_id, {}).get("muted", [])
    if not muted:
        return await update.message.reply_text("✅ هیچ‌کس در سکوت نیست.")
    text = "<b>🤐 لیست افراد در سکوت:</b>\n\n"
    for i, uid in enumerate(muted, 1):
        text += f"{i}. <a href='tg://user?id={uid}'>کاربر {uid}</a>\n"
    await update.message.reply_text(text, parse_mode="HTML")

async def list_warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    warns = PUNISH_DATA.get(chat_id, {}).get("warns", {})
    if not warns:
        return await update.message.reply_text("✅ هیچ اخطاری وجود ندارد.")
    text = "<b>⚠️ لیست اخطارها:</b>\n\n"
    for uid, count in warns.items():
        text += f"• <a href='tg://user?id={uid}'>کاربر {uid}</a> — {count}/3\n"
    await update.message.reply_text(text, parse_mode="HTML")

# ─────────────────────────────── دستورات مدیریت ───────────────────────────────

async def handle_punish_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشخیص دستورات مدیریتی"""
    text = (update.message.text or "").strip().lower()

    if text == "بن":
        return await ban_user(update, context)
    if text == "حذف بن":
        return await unban_user(update, context)
    if text == "سکوت":
        return await mute_user(update, context)
    if text == "حذف سکوت":
        return await unmute_user(update, context)
    if text == "اخطار":
        return await warn_user(update, context)
    if text == "حذف اخطار":
        return await remove_warn(update, context)
    if text in ["لیست سکوت", "لیست ساکت‌ها"]:
        return await list_mutes(update, context)
    if text in ["لیست اخطار", "لیست اخطارها"]:
        return await list_warns(update, context)
        # ==========================================================
# 🧱 بخش ۵ — سیستم ثبت اصل کاربران
# ==========================================================

ORIGIN_FILE = path("origins.json")

if not os.path.exists(ORIGIN_FILE):
    with open(ORIGIN_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

ORIGINS = _load_json(ORIGIN_FILE, {})

def _save_origins():
    _save_json(ORIGIN_FILE, ORIGINS)

# ─────────────────────────────── ثبت اصل ───────────────────────────────

async def set_origin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ثبت اصل برای یک کاربر (فقط مدیر یا سودو)"""
    chat = update.effective_chat
    user = update.effective_user
    msg = update.message

    # فقط مدیر یا سودو
    if not await _has_full_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها می‌تونن اصل ثبت کنن.")

    if not msg.reply_to_message:
        return await msg.reply_text("📎 روی پیام فرد مورد نظر ریپلای کن و بنویس: ثبت اصل <اصل کاربر>")

    parts = msg.text.strip().split("ثبت اصل", 1)
    if len(parts) < 2 or not parts[1].strip():
        return await msg.reply_text("📘 مثال:\n<code>ثبت اصل شمالی</code>", parse_mode="HTML")

    target = msg.reply_to_message.from_user
    origin_value = parts[1].strip()
    chat_id = str(chat.id)

    ORIGINS.setdefault(chat_id, {})
    ORIGINS[chat_id][str(target.id)] = origin_value
    _save_origins()

    await msg.reply_text(
        f"🪪 برای <b>{target.first_name}</b>\nاصل ثبت شد: <b>{origin_value}</b>",
        parse_mode="HTML"
    )

# ─────────────────────────────── نمایش اصل ───────────────────────────────

async def show_origin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش اصل فرد"""
    msg = update.message
    chat_id = str(msg.chat.id)
    user = msg.from_user
    text = (msg.text or "").strip().lower()

    # اگر روی پیام کسی گفت "اصل"
    if msg.reply_to_message:
        target = msg.reply_to_message.from_user
        target_id = str(target.id)
        if chat_id in ORIGINS and target_id in ORIGINS[chat_id]:
            origin = ORIGINS[chat_id][target_id]
            return await msg.reply_text(f"🪪 اصل <b>{target.first_name}</b>: <b>{origin}</b>", parse_mode="HTML")
        return  # هیچ پاسخی نده

    # اگر خودش گفت "اصل من"
    if text == "اصل من":
        target_id = str(user.id)
        if chat_id in ORIGINS and target_id in ORIGINS[chat_id]:
            origin = ORIGINS[chat_id][target_id]
            return await msg.reply_text(f"🪪 اصل شما: <b>{origin}</b>", parse_mode="HTML")
        return  # هیچی نگو

    # اگر گفت "اصل" بدون ریپلای
    if text == "اصل":
        return  # بدون ریپلای هیچی نگو

# ─────────────────────────────── لیست همه اصل‌ها ───────────────────────────────

async def list_origins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست تمام اصل‌های ثبت‌شده"""
    chat_id = str(update.effective_chat.id)
    origins = ORIGINS.get(chat_id, {})

    if not origins:
        return await update.message.reply_text("ℹ️ هنوز هیچ اصلی ثبت نشده است.")

    text = "<b>🪪 لیست اصل‌های ثبت‌شده:</b>\n\n"
    for uid, origin in origins.items():
        text += f"• <a href='tg://user?id={uid}'>کاربر {uid}</a> — {origin}\n"

    await update.message.reply_text(text, parse_mode="HTML")

# ─────────────────────────────── دستورات مرتبط ───────────────────────────────

async def handle_origin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشخیص دستورات مرتبط با اصل"""
    text = (update.message.text or "").strip().lower()

    if text.startswith("ثبت اصل"):
        return await set_origin(update, context)
    if text in ["اصل", "اصل من"]:
        return await show_origin(update, context)
    if text in ["لیست اصل", "لیست اصل‌ها", "همه اصل"]:
        return await list_origins(update, context)
        # ==========================================================
# 🧱 بخش ۶ — سیستم ثبت لقب کاربران
# ==========================================================

# لقب‌ها در همان فایل origins.json ذخیره می‌شوند
# ساختار: ORIGINS[chat_id][user_id] = {"origin": "...", "nickname": "..."}

# ─────────────────────────────── ثبت لقب ───────────────────────────────

async def set_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ثبت لقب برای یک کاربر (فقط مدیر یا سودو)"""
    chat = update.effective_chat
    user = update.effective_user
    msg = update.message

    if not await _has_full_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها می‌تونن لقب ثبت کنن.")

    if not msg.reply_to_message:
        return await msg.reply_text("📎 روی پیام فرد مورد نظر ریپلای کن و بنویس: ثبت لقب <لقب>")

    parts = msg.text.strip().split("ثبت لقب", 1)
    if len(parts) < 2 or not parts[1].strip():
        return await msg.reply_text("📘 مثال:\n<code>ثبت لقب شجاع‌دل</code>", parse_mode="HTML")

    target = msg.reply_to_message.from_user
    nickname = parts[1].strip()
    chat_id = str(chat.id)

    ORIGINS.setdefault(chat_id, {})
    ORIGINS[chat_id].setdefault(str(target.id), {})
    ORIGINS[chat_id][str(target.id)]["nickname"] = nickname
    _save_origins()

    await msg.reply_text(
        f"🏷️ برای <b>{target.first_name}</b>\nلقب ثبت شد: <b>{nickname}</b>",
        parse_mode="HTML"
    )

# ─────────────────────────────── نمایش لقب ───────────────────────────────

async def show_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لقب فرد"""
    msg = update.message
    chat_id = str(msg.chat.id)
    user = msg.from_user
    text = (msg.text or "").strip().lower()

    # اگر روی پیام کسی گفت "لقب"
    if msg.reply_to_message:
        target = msg.reply_to_message.from_user
        data = ORIGINS.get(chat_id, {}).get(str(target.id), {})
        nickname = data.get("nickname")
        if nickname:
            return await msg.reply_text(f"🏷️ لقب <b>{target.first_name}</b>: <b>{nickname}</b>", parse_mode="HTML")
        return  # هیچ پاسخی نده

    # اگر خودش گفت "لقب من"
    if text == "لقب من":
        data = ORIGINS.get(chat_id, {}).get(str(user.id), {})
        nickname = data.get("nickname")
        if nickname:
            return await msg.reply_text(f"🏷️ لقب شما: <b>{nickname}</b>", parse_mode="HTML")
        return  # ساکت باش

    # اگر گفت "لقب" بدون ریپلای
    if text == "لقب":
        return  # ساکت

# ─────────────────────────────── لیست همه لقب‌ها ───────────────────────────────

async def list_nicknames(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست تمام لقب‌های ثبت‌شده"""
    chat_id = str(update.effective_chat.id)
    origins = ORIGINS.get(chat_id, {})

    # استخراج فقط کاربرانی که لقب دارند
    nicknamed = {uid: data.get("nickname") for uid, data in origins.items() if data.get("nickname")}
    if not nicknamed:
        return await update.message.reply_text("ℹ️ هنوز هیچ لقبی ثبت نشده است.")

    text = "<b>🏷️ لیست لقب‌های ثبت‌شده:</b>\n\n"
    for uid, nickname in nicknamed.items():
        text += f"• <a href='tg://user?id={uid}'>کاربر {uid}</a> — {nickname}\n"

    await update.message.reply_text(text, parse_mode="HTML")

# ─────────────────────────────── دستورات مرتبط ───────────────────────────────

async def handle_nickname_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشخیص دستورات مرتبط با لقب"""
    text = (update.message.text or "").strip().lower()

    if text.startswith("ثبت لقب"):
        return await set_nickname(update, context)
    if text in ["لقب", "لقب من"]:
        return await show_nickname(update, context)
    if text in ["لیست لقب", "لیست لقب‌ها", "همه لقب"]:
        return await list_nicknames(update, context)
        # ==========================================================
# 🧱 بخش ۷ — تگ گروهی کاربران
# ==========================================================

TAG_BATCH_SIZE = 5  # تعداد کاربران در هر پیام تگ
TAG_DELAY = 2       # فاصله بین پیام‌ها (ثانیه)

# ─────────────────────────────── تگ همه ───────────────────────────────

async def tag_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تگ کردن همه کاربران گروه"""
    chat = update.effective_chat
    user = update.effective_user

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران و سودوها می‌تونن از این دستور استفاده کنن.")

    await update.message.reply_text("📢 در حال تگ کردن همه کاربران... لطفاً صبر کنید.")

    try:
        members = await context.bot.get_chat_administrators(chat.id)
        me = await context.bot.get_me()

        # فهرست اعضا از داده‌های XP (در بخش XP اضافه می‌شه)
        chat_id = str(chat.id)
        all_users = XP_DATA.get(chat_id, {})

        if not all_users:
            return await update.message.reply_text("ℹ️ هنوز اطلاعاتی از کاربران وجود ندارد.")

        users_to_tag = [int(uid) for uid in all_users.keys() if int(uid) != me.id]

        # تگ در گروه
        for i in range(0, len(users_to_tag), TAG_BATCH_SIZE):
            batch = users_to_tag[i:i + TAG_BATCH_SIZE]
            mentions = " ".join([f"<a href='tg://user?id={uid}'>👤</a>" for uid in batch])
            await context.bot.send_message(chat.id, mentions, parse_mode="HTML")
            await asyncio.sleep(TAG_DELAY)

        await update.message.reply_text("✅ تگ همه کاربران انجام شد.", parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در تگ همه:\n<code>{e}</code>", parse_mode="HTML")

# ─────────────────────────────── تگ مدیران ───────────────────────────────

async def tag_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تگ کردن فقط مدیران گروه"""
    chat = update.effective_chat
    user = update.effective_user

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران و سودوها مجازند.")

    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        me = await context.bot.get_me()

        admin_ids = [m.user.id for m in admins if m.user.id != me.id]

        if not admin_ids:
            return await update.message.reply_text("ℹ️ مدیری یافت نشد.")

        for i in range(0, len(admin_ids), TAG_BATCH_SIZE):
            batch = admin_ids[i:i + TAG_BATCH_SIZE]
            mentions = " ".join([f"<a href='tg://user?id={uid}'>👮</a>" for uid in batch])
            await context.bot.send_message(chat.id, mentions, parse_mode="HTML")
            await asyncio.sleep(TAG_DELAY)

        await update.message.reply_text("✅ تگ مدیران انجام شد.", parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در تگ مدیران:\n<code>{e}</code>", parse_mode="HTML")

# ─────────────────────────────── تگ فعال‌ها ───────────────────────────────

async def tag_active(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تگ کاربران فعال (آخرین ۱۰ کاربر فعال)"""
    chat = update.effective_chat
    user = update.effective_user
    chat_id = str(chat.id)

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران و سودوها مجازند.")

    if chat_id not in XP_DATA or not XP_DATA[chat_id]:
        return await update.message.reply_text("ℹ️ هنوز هیچ کاربری فعالیتی نداشته است.")

    sorted_users = sorted(
        XP_DATA[chat_id].items(),
        key=lambda x: x[1].get("last", 0),
        reverse=True
    )

    users_to_tag = [int(uid) for uid, _ in sorted_users[:10]]

    for i in range(0, len(users_to_tag), TAG_BATCH_SIZE):
        batch = users_to_tag[i:i + TAG_BATCH_SIZE]
        mentions = " ".join([f"<a href='tg://user?id={uid}'>🔥</a>" for uid in batch])
        await context.bot.send_message(chat.id, mentions, parse_mode="HTML")
        await asyncio.sleep(TAG_DELAY)

    await update.message.reply_text("✅ تگ کاربران فعال انجام شد.", parse_mode="HTML")

# ─────────────────────────────── تگ غیرفعال‌ها ───────────────────────────────

async def tag_inactive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تگ کاربران غیرفعال (آخرین ۱۰ کاربر کم‌فعال)"""
    chat = update.effective_chat
    user = update.effective_user
    chat_id = str(chat.id)

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران و سودوها مجازند.")

    if chat_id not in XP_DATA or not XP_DATA[chat_id]:
        return await update.message.reply_text("ℹ️ هنوز هیچ کاربری فعالیتی نداشته است.")

    sorted_users = sorted(
        XP_DATA[chat_id].items(),
        key=lambda x: x[1].get("last", 0)
    )

    users_to_tag = [int(uid) for uid, _ in sorted_users[:10]]

    for i in range(0, len(users_to_tag), TAG_BATCH_SIZE):
        batch = users_to_tag[i:i + TAG_BATCH_SIZE]
        mentions = " ".join([f"<a href='tg://user?id={uid}'>💤</a>" for uid in batch])
        await context.bot.send_message(chat.id, mentions, parse_mode="HTML")
        await asyncio.sleep(TAG_DELAY)

    await update.message.reply_text("✅ تگ کاربران غیرفعال انجام شد.", parse_mode="HTML")

# ─────────────────────────────── کنترل دستورات ───────────────────────────────

async def handle_tag_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشخیص دستورات تگ"""
    text = (update.message.text or "").strip().lower()

    if text in ["تگ همه", "تگ کل"]:
        return await tag_all(update, context)
    if text in ["تگ مدیران", "تگ ادمین‌ها"]:
        return await tag_admins(update, context)
    if text in ["تگ فعال", "تگ کاربران فعال"]:
        return await tag_active(update, context)
    if text in ["تگ غیرفعال", "تگ غیر فعال"]:
        return await tag_inactive(update, context)
        
# ─────────────────────────────── ثبت پیام‌ها ───────────────────────────────
def _log_message(update: Update):
    """ثبت پیام‌ها برای قابلیت پاکسازی (در حافظه)"""
    if not update.message:
        return
    chat_id = str(update.effective_chat.id)
    msg = update.message
    entry = {
        "message_id": msg.message_id,
        "user_id": msg.from_user.id if msg.from_user else None,
    }
    if chat_id not in MESSAGE_LOG:
        MESSAGE_LOG[chat_id] = deque(maxlen=MAX_LOG_PER_CHAT)
    MESSAGE_LOG[chat_id].append(entry)

# در ابتدای handle_group_message این را اضافه کن:
# _log_message(update)

# ─────────────────────────────── حذف پیام‌های آخر ───────────────────────────────
async def delete_last_messages(update: Update, context: ContextTypes.DEFAULT_TYPE, count: int):
    """حذف n پیام آخر (بر اساس لاگ محلی)"""
    chat = update.effective_chat
    user = update.effective_user
    chat_id = str(chat.id)

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌تونن پاکسازی کنن.")

    if count <= 0:
        return await update.message.reply_text("⚠️ عدد باید مثبت باشد.")

    entries = list(MESSAGE_LOG.get(chat_id, []))
    if not entries:
        return await update.message.reply_text("ℹ️ هیچ پیامی در لاگ موجود نیست.")

    to_delete = [e["message_id"] for e in reversed(entries)][:count]

    deleted = 0
    for mid in to_delete:
        try:
            await context.bot.delete_message(chat.id, mid)
            deleted += 1
            await asyncio.sleep(DELETE_DELAY)
        except Exception:
            continue

    if deleted:
        kept = [e for e in MESSAGE_LOG[chat_id] if e["message_id"] not in set(to_delete)]
        MESSAGE_LOG[chat_id] = deque(kept, maxlen=MAX_LOG_PER_CHAT)

    await update.message.reply_text(f"🧹 {deleted} پیام حذف شد.", parse_mode="HTML")

# ─────────────────────────────── پاکسازی کل چت ───────────────────────────────
async def clear_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاکسازی کل چت تا سقف پیام‌های ذخیره‌شده"""
    chat = update.effective_chat
    user = update.effective_user
    chat_id = str(chat.id)

    if not await _has_full_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌تونن پاکسازی کنن.")

    await update.message.reply_text("🧹 در حال پاکسازی کل چت...")

    entries = list(MESSAGE_LOG.get(chat_id, []))
    if not entries:
        return await update.message.reply_text("ℹ️ چیزی برای حذف در لاگ وجود ندارد.")

    to_delete = [e["message_id"] for e in reversed(entries)][:MAX_DELETE]

    deleted = 0
    for mid in to_delete:
        try:
            await context.bot.delete_message(chat.id, mid)
            deleted += 1
            await asyncio.sleep(DELETE_DELAY)
        except Exception:
            continue

    if deleted:
        kept = [e for e in MESSAGE_LOG[chat_id] if e["message_id"] not in set(to_delete)]
        MESSAGE_LOG[chat_id] = deque(kept, maxlen=MAX_LOG_PER_CHAT)

    await update.message.reply_text(f"✅ پاکسازی انجام شد ({deleted} پیام حذف شد).", parse_mode="HTML")

# ─────────────────────────────── حذف پیام‌های کاربر خاص ───────────────────────────────
async def delete_user_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف پیام‌های اخیر یک کاربر خاص (با ریپلای)"""
    chat = update.effective_chat
    user = update.effective_user
    msg = update.message
    chat_id = str(chat.id)

    if not msg.reply_to_message:
        return await msg.reply_text("📎 روی پیام کاربر مورد نظر ریپلای کن و بنویس: حذف")

    if not await _has_full_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها می‌تونن پیام‌های دیگران رو حذف کنن.")

    target = msg.reply_to_message.from_user
    target_id = target.id

    entries = list(MESSAGE_LOG.get(chat_id, []))
    if not entries:
        return await msg.reply_text("ℹ️ هیچ پیام ثبت‌شده‌ای از این کاربر پیدا نشد.")

    user_msgs = [e["message_id"] for e in reversed(entries) if e["user_id"] == target_id][:MAX_DELETE]
    if not user_msgs:
        return await msg.reply_text("ℹ️ پیام اخیر قابل حذفی از این کاربر در لاگ پیدا نشد.")

    await msg.reply_text(f"🧹 در حال حذف پیام‌های اخیر <b>{target.first_name}</b>...", parse_mode="HTML")

    deleted = 0
    for mid in user_msgs:
        try:
            await context.bot.delete_message(chat.id, mid)
            deleted += 1
            await asyncio.sleep(DELETE_DELAY)
        except Exception:
            continue

    if deleted:
        kept = [e for e in MESSAGE_LOG[chat_id] if e["message_id"] not in set(user_msgs)]
        MESSAGE_LOG[chat_id] = deque(kept, maxlen=MAX_LOG_PER_CHAT)

    await context.bot.send_message(
        chat.id,
        f"✅ پیام‌های <b>{target.first_name}</b> حذف شد ({deleted} پیام).",
        parse_mode="HTML"
    )

# ─────────────────────────────── کنترل دستورات ───────────────────────────────
async def handle_clean_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشخیص دستورات پاکسازی"""
    text = (update.message.text or "").strip().lower()

    # پاکسازی کامل
    if text == "پاکسازی":
        return await clear_chat(update, context)

    # حذف عددی
    if text.startswith("حذف "):
        try:
            count = int(text.split()[1])
            if count <= 0:
                return await update.message.reply_text("⚠️ عدد باید مثبت باشد.")
            if count > MAX_DELETE:
                count = MAX_DELETE
            return await delete_last_messages(update, context, count)
        except (IndexError, ValueError):
            return await update.message.reply_text("📘 مثال: <code>حذف 50</code>", parse_mode="HTML")

    # حذف پیام‌های یک کاربر خاص (با ریپلای)
    if text == "حذف" and update.message.reply_to_message:
        return await delete_user_messages(update, context)

        # ==========================================================
# 🧱 بخش ۹ — سیستم کاربران ویژه (VIP System)
# ==========================================================

VIP_FILE = path("vips.json")

if not os.path.exists(VIP_FILE):
    with open(VIP_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

VIPS = _load_json(VIP_FILE, {})

def _save_vips():
    _save_json(VIP_FILE, VIPS)

# ─────────────────────────────── بررسی کاربر ویژه ───────────────────────────────

def _is_vip(chat_id: int, user_id: int) -> bool:
    """بررسی اینکه آیا کاربر ویژه است یا خیر"""
    chat_id = str(chat_id)
    return user_id in VIPS.get(chat_id, [])

# ─────────────────────────────── افزودن ویژه ───────────────────────────────

async def add_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """افزودن کاربر به لیست ویژه"""
    chat = update.effective_chat
    user = update.effective_user
    msg = update.message

    if not await _has_full_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها می‌تونن کاربر ویژه اضافه کنن.")

    if not msg.reply_to_message:
        return await msg.reply_text("📎 روی پیام فرد مورد نظر ریپلای کن و بنویس: افزودن ویژه")

    target = msg.reply_to_message.from_user
    chat_id = str(chat.id)

    VIPS.setdefault(chat_id, [])
    if target.id in VIPS[chat_id]:
        return await msg.reply_text(f"ℹ️ {target.first_name} از قبل ویژه است.")

    VIPS[chat_id].append(target.id)
    _save_vips()

    await msg.reply_text(f"🌟 <b>{target.first_name}</b> به لیست کاربران ویژه اضافه شد!", parse_mode="HTML")

# ─────────────────────────────── حذف ویژه ───────────────────────────────

async def remove_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف کاربر از لیست ویژه"""
    chat = update.effective_chat
    user = update.effective_user
    msg = update.message

    if not await _has_full_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    if not msg.reply_to_message:
        return await msg.reply_text("📎 روی پیام کاربر ویژه ریپلای کن و بنویس: حذف ویژه")

    target = msg.reply_to_message.from_user
    chat_id = str(chat.id)

    if chat_id not in VIPS or target.id not in VIPS[chat_id]:
        return await msg.reply_text(f"ℹ️ {target.first_name} در لیست ویژه نیست.")

    VIPS[chat_id].remove(target.id)
    _save_vips()

    await msg.reply_text(f"❌ <b>{target.first_name}</b> از لیست ویژه حذف شد.", parse_mode="HTML")

# ─────────────────────────────── لیست ویژه ───────────────────────────────

async def list_vips(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست کاربران ویژه"""
    chat_id = str(update.effective_chat.id)
    vip_list = VIPS.get(chat_id, [])

    if not vip_list:
        return await update.message.reply_text("ℹ️ هیچ کاربر ویژه‌ای ثبت نشده است.")

    text = "<b>🌟 لیست کاربران ویژه:</b>\n\n"
    for i, uid in enumerate(vip_list, 1):
        text += f"{i}. <a href='tg://user?id={uid}'>کاربر {uid}</a>\n"

    await update.message.reply_text(text, parse_mode="HTML")

# ─────────────────────────────── کنترل دستورات ───────────────────────────────

async def handle_vip_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشخیص دستورات ویژه"""
    text = (update.message.text or "").strip().lower()

    if text in ["افزودن ویژه", "ویژه کردن"]:
        return await add_vip(update, context)
    if text in ["حذف ویژه", "ویژه حذف"]:
        return await remove_vip(update, context)
    if text in ["لیست ویژه", "کاربران ویژه"]:
        return await list_vips(update, context)
        # ==========================================================
# 🧱 بخش ۱۰ — مدیریت مدیران گروه (Admin Control System)
# ==========================================================

ADMINS_FILE = path("group_admins.json")

if not os.path.exists(ADMINS_FILE):
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

ADMINS = _load_json(ADMINS_FILE, {})

def _save_admins():
    _save_json(ADMINS_FILE, ADMINS)

def _is_local_admin(chat_id: int, user_id: int) -> bool:
    """بررسی مدیر بودن محلی"""
    chat_id = str(chat_id)
    return str(user_id) in ADMINS.get(chat_id, [])

# ─────────────────────────────── افزودن مدیر ───────────────────────────────

async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """افزودن مدیر جدید (درصورت داشتن مجوز، واقعی؛ در غیراینصورت محلی)"""
    chat = update.effective_chat
    user = update.effective_user
    msg = update.message

    if not await _has_full_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها می‌تونن مدیر اضافه کنن.")

    if not msg.reply_to_message:
        return await msg.reply_text("📎 روی پیام فرد مورد نظر ریپلای کن و بنویس: افزودن مدیر")

    target = msg.reply_to_message.from_user
    chat_id = str(chat.id)

    # تلاش برای ارتقای واقعی در تلگرام
    try:
        await context.bot.promote_chat_member(
            chat_id=chat.id,
            user_id=target.id,
            can_manage_chat=True,
            can_delete_messages=True,
            can_restrict_members=True,
            can_invite_users=True,
            can_pin_messages=True,
            can_manage_video_chats=True,
            can_promote_members=False
        )
        await msg.reply_text(f"👮 <b>{target.first_name}</b> به عنوان مدیر گروه ارتقا یافت.", parse_mode="HTML")
    except Exception as e:
        print(f"[Admin Promote Error] {e}")
        # اگر دسترسی نداشت، به‌صورت محلی ثبت می‌کنیم
        ADMINS.setdefault(chat_id, [])
        if str(target.id) not in ADMINS[chat_id]:
            ADMINS[chat_id].append(str(target.id))
            _save_admins()
        await msg.reply_text(f"✅ <b>{target.first_name}</b> به عنوان مدیر محلی ثبت شد.", parse_mode="HTML")

# ─────────────────────────────── حذف مدیر ───────────────────────────────

async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف مدیر از گروه یا فایل محلی"""
    chat = update.effective_chat
    user = update.effective_user
    msg = update.message
    if not await _has_full_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها مجاز به حذف مدیر هستند.")

    if not msg.reply_to_message:
        return await msg.reply_text("📎 روی پیام مدیر مورد نظر ریپلای کن و بنویس: حذف مدیر")

    target = msg.reply_to_message.from_user
    chat_id = str(chat.id)

    # تلاش برای حذف واقعی از مدیران تلگرام
    try:
        await context.bot.promote_chat_member(
            chat_id=chat.id,
            user_id=target.id,
            can_manage_chat=False,
            can_delete_messages=False,
            can_restrict_members=False,
            can_invite_users=False,
            can_pin_messages=False,
            can_manage_video_chats=False,
            can_promote_members=False
        )
        await msg.reply_text(f"🧹 <b>{target.first_name}</b> از مدیران گروه حذف شد.", parse_mode="HTML")
    except Exception as e:
        print(f"[Admin Demote Error] {e}")
        # اگر دسترسی نداشت، فقط از فایل محلی حذف می‌کنیم
        if chat_id in ADMINS and str(target.id) in ADMINS[chat_id]:
            ADMINS[chat_id].remove(str(target.id))
            _save_admins()
            await msg.reply_text(f"🧹 <b>{target.first_name}</b> از مدیران محلی حذف شد.", parse_mode="HTML")
        else:
            await msg.reply_text(f"ℹ️ {target.first_name} در لیست مدیران محلی نیست.", parse_mode="HTML")

# ─────────────────────────────── لیست مدیران ───────────────────────────────

async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش مدیران واقعی و محلی گروه"""
    chat = update.effective_chat
    chat_id = str(chat.id)

    text = "👮 <b>مدیران گروه:</b>\n\n"

    try:
        real_admins = await context.bot.get_chat_administrators(chat.id)
        for admin in real_admins:
            text += f"• {admin.user.first_name} — <i>مدیر واقعی</i>\n"
    except Exception as e:
        text += f"⚠️ خطا در دریافت مدیران واقعی: {e}\n"

    local_admins = ADMINS.get(chat_id, [])
    if local_admins:
        text += "\n📂 <b>مدیران محلی:</b>\n"
        for uid in local_admins:
            text += f"• <a href='tg://user?id={uid}'>کاربر {uid}</a>\n"

    await update.message.reply_text(text, parse_mode="HTML")

# ─────────────────────────────── کنترل دستورات ───────────────────────────────

async def handle_admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشخیص دستورات مدیریتی"""
    text = (update.message.text or "").strip().lower()

    if text in ["افزودن مدیر", "مدیر کردن"]:
        return await add_admin(update, context)
    if text in ["حذف مدیر", "مدیر حذف"]:
        return await remove_admin(update, context)
    if text in ["لیست مدیران", "مدیران"]:
        return await list_admins(update, context)
        # ==========================================================
# 🧱 بخش ۱۱ — مدیریت سودوهای جهانی (Global Sudo System)
# ==========================================================

SUDO_FILE = path("sudos.json")

if not os.path.exists(SUDO_FILE):
    with open(SUDO_FILE, "w", encoding="utf-8") as f:
        json.dump({"sudo_ids": []}, f, ensure_ascii=False, indent=2)

SUDO_DATA = _load_json(SUDO_FILE, {})
SUDO_IDS = set(SUDO_DATA.get("sudo_ids", []))

def _save_sudos():
    SUDO_DATA["sudo_ids"] = list(SUDO_IDS)
    _save_json(SUDO_FILE, SUDO_DATA)

# ─────────────────────────────── بررسی سودو ───────────────────────────────

def _is_sudo(user_id: int) -> bool:
    """بررسی اینکه آیا کاربر سودو هست یا خیر"""
    return user_id in SUDO_IDS

# ─────────────────────────────── افزودن سودو ───────────────────────────────

async def add_sudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """افزودن کاربر جدید به سودوهای جهانی"""
    user = update.effective_user
    msg = update.message

    # فقط سودوی اصلی می‌تونه سودو اضافه کنه
    if user.id not in SUDO_IDS:
        return await msg.reply_text("🚫 فقط سودوی اصلی ربات می‌تونه سودو جدید اضافه کنه.")

    if not msg.reply_to_message:
        return await msg.reply_text("📎 روی پیام فرد مورد نظر ریپلای کن و بنویس: افزودن سودو")

    target = msg.reply_to_message.from_user

    if target.id in SUDO_IDS:
        return await msg.reply_text(f"ℹ️ <b>{target.first_name}</b> از قبل سودو است.", parse_mode="HTML")

    SUDO_IDS.add(target.id)
    _save_sudos()
    await msg.reply_text(f"👑 <b>{target.first_name}</b> به سودوهای جهانی اضافه شد!", parse_mode="HTML")

# ─────────────────────────────── حذف سودو ───────────────────────────────

async def remove_sudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف سودو از لیست جهانی"""
    user = update.effective_user
    msg = update.message

    if user.id not in SUDO_IDS:
        return await msg.reply_text("🚫 فقط سودوی اصلی می‌تونه سودو حذف کنه.")

    if not msg.reply_to_message:
        return await msg.reply_text("📎 روی پیام سودو مورد نظر ریپلای کن و بنویس: حذف سودو")

    target = msg.reply_to_message.from_user

    if target.id not in SUDO_IDS:
        return await msg.reply_text(f"ℹ️ {target.first_name} در لیست سودوها نیست.", parse_mode="HTML")

    SUDO_IDS.remove(target.id)
    _save_sudos()
    await msg.reply_text(f"🧹 <b>{target.first_name}</b> از سودوها حذف شد.", parse_mode="HTML")

# ─────────────────────────────── لیست سودوها ───────────────────────────────

async def list_sudos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست تمام سودوهای جهانی"""
    if not SUDO_IDS:
        return await update.message.reply_text("ℹ️ هنوز هیچ سودویی ثبت نشده است.")

    text = "👑 <b>لیست سودوهای جهانی ربات:</b>\n\n"
    for i, uid in enumerate(SUDO_IDS, start=1):
        text += f"{i}. <a href='tg://user?id={uid}'>کاربر {uid}</a>\n"

    await update.message.reply_text(text, parse_mode="HTML")

# ─────────────────────────────── کنترل دستورات ───────────────────────────────

async def handle_sudo_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشخیص دستورات سودو"""
    text = (update.message.text or "").strip().lower()

    if text in ["افزودن سودو", "sudo add"]:
        return await add_sudo(update, context)
    if text in ["حذف سودو", "sudo del"]:
        return await remove_sudo(update, context)
    if text in ["لیست سودو", "لیست سودوها", "sudo list"]:
        return await list_sudos(update, context)
        
# ==========================================================
# 🧱 بخش ۱۲ — مرکز کنترل پیام‌ها و دستورات اصلی
# ==========================================================

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر مرکزی برای بررسی و اجرای تمام سیستم‌ها"""
    if not update.message:
        return
        async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ثبت تمام پیام‌ها برای قابلیت حذف و پاکسازی
    _log_message(update)

    # ادامه‌ی کد اصلی...

    msg = update.message
    text = (msg.text or msg.caption or "").strip().lower()

    # ✅ مرحله ۱: بررسی قفل‌های پیام (اول حذف، بعد سایر سیستم‌ها)
    await check_message_locks(update, context)

    # ✅ مرحله ۲: بررسی فیلتر کلمات
    await check_filtered_words(update, context)

    # ✅ مرحله ۳: بررسی سیستم‌های خاص (اصل، لقب، تگ و ...)
    if text:
        await handle_origin_commands(update, context)
        await handle_nickname_commands(update, context)
        await handle_tag_commands(update, context)

    # ✅ مرحله ۴: بررسی دستورهای قفل / بازکردن
    if text.startswith("قفل ") or text.startswith("بازکردن ") or text.startswith("باز کردن "):
        return await handle_lock_commands(update, context)

    # ✅ مرحله ۵: قفل گروه و قفل خودکار
    if text in ["قفل گروه", "باز کردن گروه", "بازکردن گروه", "باز کردن"]:
        return await handle_group_lock_commands(update, context)
    if text.startswith("تنظیم قفل خودکار") or text in ["قفل خودکار خاموش", "خاموش کردن قفل خودکار"]:
        return await handle_group_lock_commands(update, context)

    # ✅ مرحله ۶: فیلتر کلمات
    if text.startswith("فیلتر") or text.startswith("حذف فیلتر") or text in ["لیست فیلتر", "لیست فیلترها"]:
        return await handle_filter_commands(update, context)

    # ✅ مرحله ۷: مجازات‌ها (بن، سکوت، اخطار)
    if text in ["بن", "حذف بن", "سکوت", "حذف سکوت", "اخطار", "حذف اخطار", "لیست سکوت", "لیست اخطار", "لیست اخطارها"]:
        return await handle_punish_commands(update, context)

    # ✅ مرحله ۸: پاکسازی
    if text.startswith("حذف") or text == "پاکسازی":
        return await handle_clean_commands(update, context)

    # ✅ مرحله ۹: ویژه‌ها
    if text in ["افزودن ویژه", "ویژه کردن", "حذف ویژه", "ویژه حذف", "لیست ویژه", "کاربران ویژه"]:
        return await handle_vip_commands(update, context)

    # ✅ مرحله ۱۰: مدیران
    if text in ["افزودن مدیر", "مدیر کردن", "حذف مدیر", "مدیر حذف", "لیست مدیران", "مدیران"]:
        return await handle_admin_commands(update, context)

    # ✅ مرحله ۱۱: سودوها
    if text in ["افزودن سودو", "sudo add", "حذف سودو", "sudo del", "لیست سودو", "لیست سودوها", "sudo list"]:
        return await handle_sudo_commands(update, context)

    # ✅ مرحله ۱۲: تگ‌ها
    if text in ["تگ همه", "تگ مدیران", "تگ فعال", "تگ غیرفعال", "تگ غیر فعال"]:
        return await handle_tag_commands(update, context)

    # ✅ مرحله ۱۳: اصل / لقب (به صورت عمومی)
    if text.startswith("ثبت اصل") or text.startswith("ثبت لقب") or text in ["اصل", "اصل من", "لقب", "لقب من", "لیست اصل", "لیست لقب"]:
        return  # چون در مرحله ۳ انجام شد

    # ✅ مرحله ۱۴: بررسی خودکار قفل زمان‌بندی‌شده
    # (می‌تونی هر چند دقیقه با job_queue اجراش کنی)
    # await check_auto_lock(context)

    # ✅ مرحله آخر: واکنش ساده در گروه (اختیاری)
    # اگر خواستی ربات در برابر بعضی کلمات خاص واکنش نشون بده، اینجا اضافه کن
