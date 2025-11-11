import os
import json
import re
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, MessageHandler, filters

# ================= ⚙️ تنظیمات اولیه =================
BASE_DIR = os.path.dirname(os.path.abspath(file))
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

# ================= 🎯 استخراج هدف با ریپلای یا آیدی عددی =================
async def _resolve_target(msg, context, chat_id):
    # 1) ریپلای
    if msg.reply_to_message and getattr(msg.reply_to_message, "from_user", None):
        return msg.reply_to_message.from_user

    # 2) آیدی عددی در متن
    text = (msg.text or "")
    m_id = re.search(r"\b(\d{6,15})\b", text)
    if m_id:
        try:
            target_id = int(m_id.group(1))
            cm = await context.bot.get_chat_member(chat_id, target_id)
            return cm.user
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

    # الگوهای دستور: فقط با ریپلای یا آیدی عددی
    PATTERNS = {
        "ban": r"^بن\s*$",
        "unban": r"^حذف\s*بن\s*$",
        "mute": r"^سکوت\s*(\d+)?\s*(ثانیه|دقیقه|ساعت)?\s*$",
        "unmute": r"^حذف\s*سکوت\s*$",
        "warn": r"^اخطار\s*$",
        "delwarn": r"^حذف\s*اخطار\s*$",
    }

    cmd_type = None
    extra_time = None  # برای سکوت
    for k, pat in PATTERNS.items():
        m = re.match(pat, text)
        if m:
            cmd_type = k
            if cmd_type == "mute" and m.group(1):
                num = int(m.group(1))
                unit = m.group(2)
                if unit == "ساعت":
                    extra_time = num * 3600
                elif unit == "دقیقه":
                    extra_time = num * 60
                else:
                    extra_time = num
            break

    if not cmd_type:
        return

    # مجوز اجرا
    if not await _has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    # استخراج کاربر هدف
    target_user = await _resolve_target(msg, context, chat.id)
    if not target_user:
        return await msg.reply_text(
            "⚠️ هدف مشخص نیست.\n• ریپلای روی پیام کاربر\n• یا آیدی عددی",
            parse_mode="Markdown"
        )

    # محافظت‌ها
    bot_user = await context.bot.get_me()
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
            seconds = extra_time or 3600
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
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_punishments,
        ),
        group=group_number,
    )
