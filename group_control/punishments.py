import os
import json
import re
from telegram import Update, ChatPermissions, MessageEntity
from telegram.ext import ContextTypes, MessageHandler, filters
from datetime import timedelta, datetime

# ================= ⚙️ تنظیمات اولیه =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WARN_FILE = os.path.join(BASE_DIR, "warnings.json")

SUDO_IDS = [8588347189]  # آیدی سودوها

if not os.path.exists(WARN_FILE):
    with open(WARN_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)


def _load_json(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
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
    except:
        return False


# ================= 🔧 استخراج هدف امن =================
async def _resolve_target(msg, context, chat_id):
    """
    بازمی‌گرداند: (target_user_or_None, mention_present_but_not_found_or_None)
    - اگر ریپلای باشد -> target و None
    - اگر text_mention باشد -> target و None
    - اگر mention (entity) باشد و عضو گروه باشد -> target و None
    - اگر mention (متن) باشد و عضو گروه نباشد -> (None, username)  # تا پیام راهنما داده شود
    - اگر آیدی عددی بعد از دستور باشد و عضو گروه باشد -> target و None
    - در غیر این صورت -> (None, None)
    """
    # 1) ریپلای
    if msg.reply_to_message:
        return msg.reply_to_message.from_user, None

    text = msg.text or ""
    entities = msg.entities or []

    # 2) entities: text_mention یا mention
    for ent in entities:
        try:
            if ent.type == MessageEntity.TEXT_MENTION:
                return ent.user, None
            if ent.type == MessageEntity.MENTION:
                start = ent.offset
                length = ent.length
                mention_text = text[start:start + length]  # شامل '@'
                username = mention_text.lstrip("@")
                # فقط اگر username عضو گروه باشد قبول می‌کنیم
                try:
                    cm = await context.bot.get_chat_member(chat_id, username)
                    return cm.user, None
                except:
                    # mention وجود داره ولی کاربر عضو گروه نیست یا پیدا نشد
                    return None, username
        except Exception:
            continue

    # 3) بررسی وجود @username به صورت متن (بدون entity) — مثال: "بن @username" ولی entity توسط تلگرام ساخته نشده
    # regex برای گرفتن اولین @username در متن
    plain_mention = re.search(r"@([A-Za-z0-9_]{5,32})", text)
    if plain_mention:
        username = plain_mention.group(1)
        try:
            cm = await context.bot.get_chat_member(chat_id, username)
            return cm.user, None
        except:
            return None, username

    # 4) آیدی عددی دقیقاً بعد از دستور
    m = re.search(r"^(بن|حذف\s*بن|سکوت|حذف\s*سکوت|اخطار|حذف\s*اخطار)\s+(\d{6,15})\b", text)
    if m:
        try:
            target_id = int(m.group(2))
            cm = await context.bot.get_chat_member(chat_id, target_id)
            return cm.user, None
        except:
            return None, None

    return None, None


# ================= 🔧 هندلر دستورات =================
async def handle_punishments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not msg or chat.type not in ("group", "supergroup"):
        return

    text = (msg.text or "").strip()
    if not text:
        return

    # الگوهای دستورات (ابتدای پیام)
    COMMAND_PATTERNS = {
        "ban": r"^بن(?:\s+|$)",
        "unban": r"^حذف\s*بن(?:\s+|$)",
        "mute": r"^سکوت(?:\s+|$)",
        "unmute": r"^حذف\s*سکوت(?:\s+|$)",
        "warn": r"^اخطار(?:\s+|$)",
        "delwarn": r"^حذف\s*اخطار(?:\s+|$)",
    }

    # تعیین نوع دستور (فقط بر اساس ابتدای پیام)
    cmd_type = None
    for cmd, pattern in COMMAND_PATTERNS.items():
        if re.match(pattern, text):
            cmd_type = cmd
            break

    if not cmd_type:
        return  # پیام دستور نیست

    # بررسی دسترسی اجراکننده
    if not await _has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    # استخراج هدف — همراه با پرچم mention_failed
    target, mention_failed = await _resolve_target(msg, context, chat.id)

    # اگر mention وجود داشته و اما پیدا نشده -> راهنمایی کنیم و دستور اجرا نشه
    if mention_failed:
        return await msg.reply_text(
            f"⚠️ کاربری با یوزرنیم @{mention_failed} در گروه یافت نشد.\n"
            "برای اجرای دستور یکی از روش‌ها را انجام دهید:\n"
            "• روی پیامِ کاربر ریپلای کنید و دستور را بفرستید.\n"
            "• آیدی عددی کاربر را بعد از دستور وارد کنید (مثال: بن 123456789)."
        )

    # اگر هدف مشخص نیست -> پیام عمومی راهنما
    if not target:
        return await msg.reply_text(
            "⚠️ هدف مشخص نیست — دستور اجرا نشد.\n"
            "برای مشخص کردن هدف یکی از روش‌ها را انجام دهید:\n"
            "• ریپلای روی پیام کاربر و نوشتن دستور (مثلاً: بن)\n"
            "• نوشتن @username (کاربر باید قبلاً در گروه فعال بوده باشد)\n"
            "• یا نوشتن آیدی عددی بعد از دستور (مثلاً: بن 123456789)"
        )

    # محافظت‌ها
    if target.id == context.bot.id:
        return await msg.reply_text("😅 نمی‌تونم خودم رو تنبیه کنم.")
    if target.id in SUDO_IDS:
        return await msg.reply_text("🚫 امکان اجرای دستور روی این کاربر وجود ندارد.")
    try:
        t_member = await context.bot.get_chat_member(chat.id, target.id)
        if t_member.status in ("creator", "administrator"):
            return await msg.reply_text("🛡 امکان اجرای دستور روی این کاربر وجود ندارد.")
    except:
        pass

    # ---- اجرای دستورها ----
    try:
        if cmd_type == "ban":
            await context.bot.ban_chat_member(chat.id, target.id)
            return await msg.reply_text(f"🚫 {target.first_name} از گروه بن شد.")

        if cmd_type == "unban":
            await context.bot.unban_chat_member(chat.id, target.id)
            return await msg.reply_text(f"✅ {target.first_name} از بن خارج شد.")

        if cmd_type == "mute":
            m = re.search(r"سکوت\s*(\d+)?\s*(ثانیه|دقیقه|ساعت)?", text)
            if m and m.group(1):
                num = int(m.group(1))
                unit = m.group(2)
                if unit == "ساعت":
                    seconds = num * 3600
                elif unit == "دقیقه":
                    seconds = num * 60
                elif unit == "ثانیه":
                    seconds = num
                else:
                    seconds = num * 60
            else:
                seconds = 3600
            until_date = datetime.utcnow() + timedelta(seconds=seconds)
            await context.bot.restrict_chat_member(
                chat.id, target.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until_date
            )
            return await msg.reply_text(f"🤐 {target.first_name} برای {seconds} ثانیه سکوت شد.")

        if cmd_type == "unmute":
            await context.bot.restrict_chat_member(
                chat.id, target.id,
                permissions=ChatPermissions(can_send_messages=True)
            )
            return await msg.reply_text(f"🔊 {target.first_name} از سکوت خارج شد.")

        if cmd_type == "warn":
            warns = _load_json(WARN_FILE)
            key = f"{chat.id}:{target.id}"
            warns[key] = warns.get(key, 0) + 1
            _save_json(WARN_FILE, warns)
            if warns[key] >= 3:
                await context.bot.ban_chat_member(chat.id, target.id)
                warns[key] = 0
                _save_json(WARN_FILE, warns)
                return await msg.reply_text(f"🚫 {target.first_name} به‌دلیل ۳ اخطار بن شد.")
            else:
                return await msg.reply_text(f"⚠️ {target.first_name} اخطار {warns[key]}/3 گرفت.")

        if cmd_type == "delwarn":
            warns = _load_json(WARN_FILE)
            key = f"{chat.id}:{target.id}"
            if key in warns:
                del warns[key]
                _save_json(WARN_FILE, warns)
                return await msg.reply_text(f"✅ اخطارهای {target.first_name} حذف شد.")
            return await msg.reply_text("ℹ️ این کاربر اخطاری نداشت.")

    except Exception as e:
        return await msg.reply_text(f"⚠️ خطا در اجرای دستور: {e}")


# ================= 🔧 ثبت هندلر =================
def register_punishment_handlers(application, group_number: int = 12):
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_punishments,
        ),
        group=group_number,
    )
