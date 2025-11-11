import os
import json
import re
import unicodedata
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions, MessageEntity
from telegram.ext import ContextTypes, MessageHandler, filters

# ================= ⚙️ تنظیمات اولیه =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WARN_FILE = os.path.join(BASE_DIR, "warnings.json")

SUDO_IDS = [8588347189]  # آیدی سودوها — این را به لیست خودت اضافه/ویرایش کن

if not os.path.exists(WARN_FILE):
    with open(WARN_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)


def _load_json(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ================= 🔐 بررسی ادمین / سودو =================
async def _has_access(context, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except Exception:
        return False


# ================== کمکی: پاک‌سازی username ==================
def _clean_username(u: str) -> str:
    if not u:
        return u
    if u.startswith("@"):
        u = u[1:]
    u = unicodedata.normalize("NFKC", u)
    u = re.sub(r"[\u200B\u200C\u200D\uFEFF]", "", u)
    return u.strip()


# ================= 🎯 استخراج هدف مقاوم =================
async def _resolve_target(msg, context, chat_id, explicit_arg: str = None, debug_reply: bool = True):
    """
    برگشت: telegram.User یا None
    روش‌ها (اولویت):
      1) ریپلای روی پیام
      2) MessageEntity.TEXT_MENTION
      3) MessageEntity.MENTION -> تلاش get_chat_member(chat_id, username)
      4) explicit_arg (از regex) -> تلاش با get_chat_member سپس get_chat
      5) جستجوی @username در متن (fallback)
      6) آیدی عددی در متن
      7) بررسی admins (آخرین تلاش)
    اگر debug_reply=True و هدف پیدا نشد، یک پیام (کوتاه) برای اجراکننده می‌فرستد با اطلاعات مفید برای دیباگ.
    """
    # 1) reply
    if msg.reply_to_message and getattr(msg.reply_to_message, "from_user", None):
        return msg.reply_to_message.from_user

    text = (msg.text or "") or ""
    entities = msg.entities or []

    # 2) text_mention
    for ent in entities:
        try:
            if ent.type == MessageEntity.TEXT_MENTION and getattr(ent, "user", None):
                return ent.user
        except Exception:
            pass

    # 3) mention entity (@username)
    for ent in entities:
        try:
            if ent.type == MessageEntity.MENTION:
                start = ent.offset
                length = ent.length
                raw = text[start:start+length]  # مثل "@user"
                username = _clean_username(raw)
                if username.startswith("@"):
                    username = username[1:]
                if not username:
                    continue
                # اول تلاش کن با get_chat_member در همین گروه (مطمئن‌ترین)
                try:
                    cm = await context.bot.get_chat_member(chat_id, username)
                    return cm.user
                except Exception:
                    # اگر get_chat_member با username کار نکرد، تلاش کن با get_chat عمومی
                    try:
                        uobj = await context.bot.get_chat(username)
                        # اگر برگردد و یک user باشد، آن را برگردان
                        if getattr(uobj, "type", None) in (None, "private"):
                            return uobj
                    except Exception:
                        continue
        except Exception:
            continue

    # 4) explicit_arg (از regex)
    if explicit_arg:
        arg = explicit_arg.strip()
        cleaned = _clean_username(arg)
        # اگر arg با @ است
        if cleaned.startswith("@"):
            cleaned = cleaned[1:]
        # تلاش اول: get_chat_member در گروه (username یا id)
        try:
            # اگر عدد است
            if re.fullmatch(r"\d{6,15}", cleaned):
                cm = await context.bot.get_chat_member(chat_id, int(cleaned))
                return cm.user
            else:
                cm = await context.bot.get_chat_member(chat_id, cleaned)
                return cm.user
        except Exception:
            # تلاش دوم: get_chat عمومی
            try:
                if re.fullmatch(r"\d{6,15}", cleaned):
                    # اگر فقط عدد بود و get_chat_member نخوند، به None
                    pass
                else:
                    uobj = await context.bot.get_chat(cleaned)
                    return uobj
            except Exception:
                pass

    # 5) fallback: پیدا کردن @username داخل متن
    m_user = re.search(r"@([A-Za-z0-9_]{3,32})", text)
    if m_user:
        username = _clean_username(m_user.group(1))
        try:
            cm = await context.bot.get_chat_member(chat_id, username)
            return cm.user
        except Exception:
            try:
                uobj = await context.bot.get_chat(username)
                return uobj
            except Exception:
                pass

    # 6) آیدی عددی در متن
    m_id = re.search(r"\b(\d{6,15})\b", text)
    if m_id:
        try:
            cm = await context.bot.get_chat_member(chat_id, int(m_id.group(1)))
            return cm.user
        except Exception:
            pass

    # 7) آخرین راه: بررسی admins برای پیدا کردن با تطبیق username/displayname
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        # بررسی بر اساس username یا نام
        for a in admins:
            uname = getattr(a.user, "username", "") or ""
            if uname and uname.lower() in text.lower():
                return a.user
            # بررسی نام کامل
            full = (getattr(a.user, "first_name", "") or "") + " " + (getattr(a.user, "last_name", "") or "")
            if full.strip() and full.strip().lower() in text.lower():
                return a.user
    except Exception:
        pass

    # دیباگ: ارسال مختصر برای اجراکننده (فقط اگر بخوای)
    if debug_reply:
        try:
            debug_lines = []
            debug_lines.append("🔍 دیباگ شناسایی هدف:")
            debug_lines.append(f"متن: {repr(text)[:200]}")
            ent_info = []
            for e in entities:
                ent_info.append(f"{getattr(e,'type',None)}@{getattr(e,'offset',None')}/{getattr(e,'length',None)}")
            debug_lines.append("entities: " + ", ".join(ent_info))
            debug_lines.append("لطفاً مطمئن شوید username دقیق و بدون علامت اضافی است و ربات دسترسی لازم دارد.")
            await msg.reply("\n".join(debug_lines))
        except Exception:
            pass

    return None
# ================= ⚙️ هندلر دستورات تنبیهی =================
async def handle_punishments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not msg or chat.type not in ("group", "supergroup"):
        return

    text = (msg.text or "").strip()
    if not text:
        return

    # الگوهای دقیق — فقط قالب‌های مجاز را قبول کن
    # برای بن/حذف بن/اخطار/حذف اخطار: فقط "کلمه" یا "کلمه @username" یا "کلمه <id>" یا ریپلای
    PATTERNS = {
        "ban": re.compile(r"^بن(?:\s+(@[A-Za-z0-9_]{3,}|[0-9]{6,15}))?\s*$"),
        "unban": re.compile(r"^حذف\s*بن(?:\s+(@[A-Za-z0-9_]{3,}|[0-9]{6,15}))?\s*$"),
        # سکوت: optionally allow time after username/id or after command when reply used
        "mute": re.compile(r"^سکوت(?:\s+(@[A-Za-z0-9_]{3,}|[0-9]{6,15}))?(?:\s+(\d+)\s*(ثانیه|دقیقه|ساعت)?)?\s*$"),
        "unmute": re.compile(r"^حذف\s*سکوت(?:\s+(@[A-Za-z0-9_]{3,}|[0-9]{6,15}))?\s*$"),
        "warn": re.compile(r"^اخطار(?:\s+(@[A-Za-z0-9_]{3,}|[0-9]{6,15}))?\s*$"),
        "delwarn": re.compile(r"^حذف\s*اخطار(?:\s+(@[A-Za-z0-9_]{3,}|[0-9]{6,15}))?\s*$"),
    }

    matched = None
    cmd_type = None
    for k, pat in PATTERNS.items():
        m = pat.match(text)
        if m:
            cmd_type = k
            matched = m
            break

    if not cmd_type:
        return  # دستور معتبر نبوده — هیچ کاری نکن

    # مجوز اجرا
    if not await _has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    # استخراج explicit_arg از capture group (اگر موجود)
    explicit_arg = None
    extra_time = None  # برای سکوت: (number, unit)
    if matched:
        # groups: group(1) ممکنه username یا id، برای mute گروه(2) و (3) ممکنه زمان باشند
        explicit_arg = matched.group(1) if matched.lastindex and matched.lastindex >= 1 else None
        if cmd_type == "mute":
            # در regex بالا گروه 2 = number, گروه 3 = unit
            if matched.lastindex and matched.lastindex >= 3:
                num = matched.group(2)
                unit = matched.group(3)
                if num:
                    extra_time = (int(num), unit)

    # حالا resolve target (ریپلای یا explicit_arg)
    target_user = await _resolve_target(msg, context, chat.id, explicit_arg)
    if not target_user:
        return await msg.reply_text(
            "⚠️ هدف مشخص نیست.\n"
            "• ریپلای روی پیام کاربر\n"
            "• یا `@username` (عضو گروه)\n"
            "• یا آیدی عددی\n",
            parse_mode="Markdown"
        )

    # محافظت‌ها: خودِ بات، سودوها، ادمین‌ها
    bot_user = (await context.bot.get_me())
    if target_user.id == bot_user.id:
        return await msg.reply_text("😅 نمی‌تونم خودم رو تنبیه کنم.")
    if target_user.id in SUDO_IDS:
        return await msg.reply_text("🚫 این کاربر در لیست سودو است و قابل تنبیه نیست.")
    try:
        tm = await context.bot.get_chat_member(chat.id, target_user.id)
        if tm.status in ("creator", "administrator"):
            return await msg.reply_text("🛡 امکان اجرای دستور روی این کاربر وجود ندارد (ادمین).")
    except Exception:
        pass

    # اجرای دستورات
    try:
        if cmd_type == "ban":
            await context.bot.ban_chat_member(chat.id, target_user.id)
            return await msg.reply_text(f"🚫 {target_user.first_name} از گروه بن شد.")

        if cmd_type == "unban":
            await context.bot.unban_chat_member(chat.id, target_user.id)
            return await msg.reply_text(f"✅ {target_user.first_name} از بن خارج شد.")

        if cmd_type == "mute":
            # محاسبه زمان سکوت
            seconds = 3600  # پیش‌فرض یک ساعت
            if extra_time:
                num, unit = extra_time
                if unit == "ساعت":
                    seconds = num * 3600
                elif unit == "دقیقه":
                    seconds = num * 60
                else:
                    seconds = num
            # اگر explicit_arg نبود (یعنی ریپلای) ولی کاربر خواست زمان بفرستد، هم پشتیبانی شد
            until = datetime.utcnow() + timedelta(seconds=seconds)
            await context.bot.restrict_chat_member(
                chat.id, target_user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until
            )
            return await msg.reply_text(f"🤐 {target_user.first_name} برای {seconds} ثانیه سکوت شد.")

        if cmd_type == "unmute":
            await context.bot.restrict_chat_member(
                chat.id, target_user.id,
                permissions=ChatPermissions(can_send_messages=True)
            )
            return await msg.reply_text(f"🔊 {target_user.first_name} از سکوت خارج شد.")

        if cmd_type == "warn":
            warns = _load_json(WARN_FILE)
            key = f"{chat.id}:{target_user.id}"
            warns[key] = warns.get(key, 0) + 1
            _save_json(WARN_FILE, warns)
            if warns[key] >= 3:
                await context.bot.ban_chat_member(chat.id, target_user.id)
                warns[key] = 0
                _save_json(WARN_FILE, warns)
                return await msg.reply_text(f"🚫 {target_user.first_name} به‌دلیل ۳ اخطار بن شد.")
            else:
                return await msg.reply_text(f"⚠️ {target_user.first_name} اخطار {warns[key]}/3 گرفت.")

        if cmd_type == "delwarn":
            warns = _load_json(WARN_FILE)
            key = f"{chat.id}:{target_user.id}"
            if key in warns:
                del warns[key]
                _save_json(WARN_FILE, warns)
                return await msg.reply_text(f"✅ اخطارهای {target_user.first_name} حذف شد.")
            return await msg.reply_text("ℹ️ این کاربر اخطاری نداشت.")

    except Exception as e:
        print("handle_punishments execution exception:", e)
        return await msg.reply_text(f"⚠️ خطا در اجرای دستور: {e}")


# ================= 🧩 ثبت هندلر =================
def register_punishment_handlers(application, group_number: int = 12):
    """
    ثبت هندلر برای python-telegram-bot.
    فراخوانی در bot.py:
        register_punishment_handlers(application, group_number=12)
    """
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_punishments,
        ),
        group=group_number,
    )
