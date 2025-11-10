import os
import json
import re
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions, MessageEntity
from telegram.ext import ContextTypes, MessageHandler, filters

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


# ================= 🎯 استخراج هدف امن =================
async def _resolve_target(msg, context, chat_id):
    # ✅ حالت ۱: ریپلای
    if msg.reply_to_message:
        return msg.reply_to_message.from_user

    text = msg.text or ""
    entities = msg.entities or []

    # ✅ حالت ۲: mention یا text_mention
    for ent in entities:
        try:
            if ent.type == MessageEntity.TEXT_MENTION:
                return ent.user

            if ent.type == MessageEntity.MENTION:
                start = ent.offset
                length = ent.length
                username = text[start:start + length].lstrip("@")

                try:
                    user_obj = await context.bot.get_chat(username)
                    return user_obj
                except:
                    continue
        except:
            continue

    # ✅ حالت ۳: آیدی عددی در متن
    m = re.search(r"\b(\d{6,15})\b", text)
    if m:
        try:
            target_id = int(m.group(1))
            cm = await context.bot.get_chat_member(chat_id, target_id)
            return cm.user
        except:
            return None

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

    # ✅ regex فقط ابتدای جمله، تا توی وسط چت اشتباهی فعال نشه
    COMMAND_PATTERNS = {
        "ban": r"^بن(?:\s|$)",
        "unban": r"^حذف\s*بن(?:\s|$)",
        "mute": r"^سکوت(?:\s|$)",
        "unmute": r"^حذف\s*سکوت(?:\s|$)",
        "warn": r"^اخطار(?:\s|$)",
        "delwarn": r"^حذف\s*اخطار(?:\s|$)",
    }

    cmd_type = None
    for cmd, pattern in COMMAND_PATTERNS.items():
        if re.match(pattern, text):
            cmd_type = cmd
            break

    if not cmd_type:
        return  # متن دستور واقعی نیست

    # ✅ بررسی دسترسی اجراکننده
    if not await _has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    # ✅ استخراج هدف امن
    target = await _resolve_target(msg, context, chat.id)
    if not target:
        return await msg.reply_text(
            "⚠️ هدف مشخص نیست.\n"
            "• ریپلای روی پیام کاربر\n"
            "• @username (عضو گروه)\n"
            "• آیدی عددی"
        )

    # ✅ محافظت در برابر بن ادمین‌ها یا خود ربات
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

    # ✅ اجرای دستورات
    try:
        # 🚫 بن
        if cmd_type == "ban":
            await context.bot.ban_chat_member(chat.id, target.id)
            return await msg.reply_text(f"🚫 {target.first_name} از گروه بن شد.")

        # 🔓 حذف بن
        if cmd_type == "unban":
            await context.bot.unban_chat_member(chat.id, target.id)
            return await msg.reply_text(f"✅ {target.first_name} از بن خارج شد.")

        # 🤐 سکوت
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
                seconds = 3600  # پیش‌فرض: ۱ ساعت

            until_date = datetime.utcnow() + timedelta(seconds=seconds)
            await context.bot.restrict_chat_member(
                chat.id,
                target.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until_date
            )
            return await msg.reply_text(f"🤐 {target.first_name} برای {seconds} ثانیه سکوت شد.")

        # 🔊 حذف سکوت
        if cmd_type == "unmute":
            await context.bot.restrict_chat_member(
                chat.id,
                target.id,
                permissions=ChatPermissions(can_send_messages=True)
            )
            return await msg.reply_text(f"🔊 {target.first_name} از سکوت خارج شد.")

        # ⚠️ اخطار
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

        # ✅ حذف اخطار
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


# ================= 🧩 ثبت هندلر =================
def register_punishment_handlers(application, group_number: int = 12):
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_punishments,
        ),
        group=group_number,
    )
