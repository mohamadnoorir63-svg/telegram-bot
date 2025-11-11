import os
import json
import re
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, MessageHandler, filters

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WARN_FILE = os.path.join(BASE_DIR, "warnings.json")
MSG_FILE = os.path.join(BASE_DIR, "group_messages.json")
ALIAS_FILE = os.path.join(BASE_DIR, "command_aliases.json")

SUDO_IDS = [8588347189]

for file in [WARN_FILE, MSG_FILE, ALIAS_FILE]:
    if not os.path.exists(file):
        with open(file, "w", encoding="utf-8") as f:
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

async def _has_access(context, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except Exception:
        return False

async def _resolve_target(msg, context, chat_id):
    # 1. ریپلای
    if msg.reply_to_message and getattr(msg.reply_to_message, "from_user", None):
        return msg.reply_to_message.from_user
    # 2. آیدی عددی در متن
    text = (msg.text or "")
    m = re.search(r"\b(\d{6,15})\b", text)
    if m:
        try:
            target_id = int(m.group(1))
            cm = await context.bot.get_chat_member(chat_id, target_id)
            return cm.user
        except Exception:
            return None
    return None

def get_group_message(chat_id, cmd_type):
    messages = _load_json(MSG_FILE)
    chat_msgs = messages.get(str(chat_id), {})
    defaults = {
        "ban": "🚫 {name} از گروه بن شد",
        "unban": "✅ {name} از بن خارج شد",
        "mute": "🤐 {name} برای {seconds} ثانیه سکوت شد",
        "unmute": "🔊 {name} از سکوت خارج شد",
        "warn": "⚠️ {name} اخطار گرفت",
        "delwarn": "✅ اخطارهای {name} حذف شد",
    }
    return chat_msgs.get(cmd_type, defaults.get(cmd_type, ""))

async def set_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not msg or chat.type not in ("group", "supergroup"):
        return

    text = (msg.text or "").strip()
    m = re.match(r"تنظیم پیام\s+(\S+)\s+(.+)", text)
    if not m:
        return
    if not await _has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    cmd_type = m.group(1)
    message_text = m.group(2)
    messages = _load_json(MSG_FILE)
    chat_msgs = messages.get(str(chat.id), {})
    chat_msgs[cmd_type] = message_text
    messages[str(chat.id)] = chat_msgs
    _save_json(MSG_FILE, messages)
    await msg.reply_text(f"✅ پیام دستور `{cmd_type}` ثبت شد.")

async def set_command_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not msg or chat.type not in ("group", "supergroup"):
        return

    text = (msg.text or "").strip()
    m = re.match(r"ثبت دستور\s+(\S+)\s+(\S+)", text)
    if not m:
        return
    if not await _has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    alias_name = m.group(1)
    main_cmd = m.group(2)
    aliases = _load_json(ALIAS_FILE)
    chat_aliases = aliases.get(str(chat.id), {})
    chat_aliases[alias_name] = main_cmd
    aliases[str(chat.id)] = chat_aliases
    _save_json(ALIAS_FILE, aliases)
    await msg.reply_text(f"✅ دستور `{alias_name}` به عنوان جایگزین `{main_cmd}` ثبت شد.")

async def handle_punishments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not msg or chat.type not in ("group", "supergroup"):
        return
    text = (msg.text or "").strip()
    if not text:
        return

    # بررسی alias
    aliases = _load_json(ALIAS_FILE).get(str(chat.id), {})
    cmd_type = aliases.get(text, None)
    if not cmd_type:
        cmd_type = text  # دستور اصلی

    # دستورهای اصلی
    MAIN_CMDS = ["ban","unban","mute","unmute","warn","delwarn"]
    if cmd_type not in MAIN_CMDS:
        return

    if not await _has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    target_user = await _resolve_target(msg, context, chat.id)
    if not target_user:
        return await msg.reply_text("⚠️ هدف مشخص نیست (ریپلای یا آیدی).")

    bot_user = await context.bot.get_me()
    if target_user.id == bot_user.id or target_user.id in SUDO_IDS:
        return await msg.reply_text("🚫 نمی‌توان روی این کاربر دستور اجرا کرد.")

    try:
        tm = await context.bot.get_chat_member(chat.id, target_user.id)
        if tm.status in ("creator","administrator"):
            return await msg.reply_text("🛡 امکان اجرای دستور روی این کاربر وجود ندارد.")
    except Exception:
        pass

    try:
        msg_text = get_group_message(chat.id, cmd_type)
        seconds = 3600

        if cmd_type == "ban":
            await context.bot.ban_chat_member(chat.id, target_user.id)
        elif cmd_type == "unban":
            await context.bot.unban_chat_member(chat.id, target_user.id)
        elif cmd_type == "mute":
            until = datetime.utcnow() + timedelta(seconds=seconds)
            await context.bot.restrict_chat_member(chat.id, target_user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until)
            msg_text = msg_text.replace("{seconds}", str(seconds))
        elif cmd_type == "unmute":
            await context.bot.restrict_chat_member(chat.id, target_user.id,
                permissions=ChatPermissions(can_send_messages=True))
        elif cmd_type == "warn":
            warns = _load_json(WARN_FILE)
            key = f"{chat.id}:{target_user.id}"
            warns[key] = warns.get(key,0)+1
            _save_json(WARN_FILE, warns)
            if warns[key]>=3:
                await context.bot.ban_chat_member(chat.id, target_user.id)
                warns[key]=0
                _save_json(WARN_FILE,warns)
                msg_text = get_group_message(chat.id,"ban")
        elif cmd_type == "delwarn":
            warns = _load_json(WARN_FILE)
            key = f"{chat.id}:{target_user.id}"
            if key in warns:
                del warns[key]
                _save_json(WARN_FILE,warns)

        await msg.reply_text(msg_text.format(name=target_user.first_name))

    except Exception as e:
        print("Error:", e)
        await msg.reply_text(f"⚠️ خطا در اجرای دستور: {e}")

def register_punishment_handlers(application, group_number: int = 12):
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
        handle_punishments
    ), group=group_number)

    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
        set_group_message
    ), group=group_number + 1)

    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
        set_command_alias
    ), group=group_number + 2)
