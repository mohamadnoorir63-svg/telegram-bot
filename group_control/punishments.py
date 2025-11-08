import os
import json
import re
import asyncio
from telegram import Update, ChatPermissions, MessageEntity
from telegram.ext import ContextTypes, MessageHandler, filters
from datetime import timedelta, datetime

# ================= ⚙️ تنظیمات اولیه =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WARN_FILE = os.path.join(BASE_DIR, "warnings.json")
CUSTOM_CMD_FILE = os.path.join(BASE_DIR, "custom_commands.json")
SUDO_IDS = [8588347189]  # آیدی سودوها

# ایجاد فایل‌ها در صورت عدم وجود
for f in (WARN_FILE, CUSTOM_CMD_FILE):
    if not os.path.exists(f):
        with open(f, "w", encoding="utf-8") as x:
            json.dump({}, x, ensure_ascii=False, indent=2)


# ================= 🔧 JSON helpers =================
def _load_json(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def _save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ================= 🔐 بررسی دسترسی =================
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
    if msg.reply_to_message:
        return msg.reply_to_message.from_user, None

    text = msg.text or ""
    entities = msg.entities or []

    for ent in entities:
        try:
            if ent.type == MessageEntity.TEXT_MENTION:
                return ent.user, None
            if ent.type == MessageEntity.MENTION:
                start, length = ent.offset, ent.length
                username = text[start:start + length].lstrip("@")
                try:
                    cm = await context.bot.get_chat_member(chat_id, username)
                    return cm.user, None
                except:
                    return None, username
        except:
            continue

    plain_mention = re.search(r"@([A-Za-z0-9_]{5,32})", text)
    if plain_mention:
        username = plain_mention.group(1)
        try:
            cm = await context.bot.get_chat_member(chat_id, username)
            return cm.user, None
        except:
            return None, username

    m = re.search(r"\b(\d{6,15})\b", text)
    if m:
        try:
            target_id = int(m.group(1))
            cm = await context.bot.get_chat_member(chat_id, target_id)
            return cm.user, None
        except:
            return None, None

    return None, None


# ================= 📦 پیام‌های موقت =================
async def _send_temp(msg, text, context, delete_after=10):
    sent = await msg.reply_text(text)
    asyncio.create_task(_delete_after(sent, delete_after, context))


async def _delete_after(message, delay, context):
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(message.chat.id, message.message_id)
    except:
        pass


# ================= 🔧 هندلر اصلی =================
async def handle_punishments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not msg or chat.type not in ("group", "supergroup"):
        return

    text = (msg.text or "").strip()
    if not text:
        return

    # ---------------- افزودن دستور جدید ----------------
    if text.startswith("دستور جدید") or text.startswith("افزودن دستور"):
        if not await _has_access(context, chat.id, user.id):
            return  # ساکت
        match = re.match(
            r"^(?:دستور جدید|افزودن دستور)\s+(.+?)\s+(افزودن‌مدیر|حذف‌مدیر)\s+(.+)$", text
        )
        if not match:
            await _send_temp(
                msg,
                "📘 فرمت درست:\n<code>افزودن دستور [نام دستور] [افزودن‌مدیر|حذف‌مدیر] [متن پاسخ]</code>",
                context,
            )
            return
        name, cmd_type, response = match.groups()
        custom_all = _load_json(CUSTOM_CMD_FILE)
        chat_key = str(chat.id)
        custom_cmds = custom_all.get(chat_key, {})
        if name in custom_cmds:
            await _send_temp(msg, "⚠️ این نام قبلاً تعریف شده.", context)
            return
        custom_cmds[name] = {"type": cmd_type, "text": response}
        custom_all[chat_key] = custom_cmds
        _save_json(CUSTOM_CMD_FILE, custom_all)
        await _send_temp(msg, f"✅ دستور جدید <b>{name}</b> ثبت شد.", context)
        return

    # ---------------- اجرای دستور سفارشی ----------------
    custom_all = _load_json(CUSTOM_CMD_FILE)
    chat_key = str(chat.id)
    custom_cmds = custom_all.get(chat_key, {})
    if text in custom_cmds:
        cmd_info = custom_cmds[text]
        target, mention_failed = await _resolve_target(msg, context, chat.id)
        if mention_failed or not target:
            return
        if target.id == context.bot.id:
            await _send_temp(msg, "😅 من ربات هستم!", context)
            return
        if target.id in SUDO_IDS:
            await _send_temp(msg, "👑 این کاربر سودو است.", context)
            return
        t_member = await context.bot.get_chat_member(chat.id, target.id)
        if t_member.status in ("creator", "administrator"):
            await _send_temp(msg, "🛡 امکان اجرای دستور روی این کاربر وجود ندارد.", context)
            return
        try:
            if cmd_info["type"] == "افزودن‌مدیر":
                await context.bot.promote_chat_member(
                    chat.id, target.id,
                    can_delete_messages=True,
                    can_restrict_members=True,
                    can_invite_users=True,
                    can_pin_messages=True,
                    can_manage_topics=True
                )
            elif cmd_info["type"] == "حذف‌مدیر":
                await context.bot.promote_chat_member(
                    chat.id, target.id,
                    can_manage_chat=False,
                    can_delete_messages=False,
                    can_manage_video_chats=False,
                    can_restrict_members=False,
                    can_promote_members=False,
                    can_change_info=False,
                    can_invite_users=False,
                    can_pin_messages=False,
                    can_manage_topics=False
                )
            text_out = cmd_info.get("text", "").replace("{name}", target.first_name)
            await _send_temp(msg, text_out or "✅ عملیات انجام شد.", context)
        except:
            return
        return

    # ---------------- دستورات بن/سکوت/اخطار با alias ----------------
    COMMAND_PATTERNS = {
        "ban": [r"^بن(?:\s+|$)", r"^اخراج(?:\s+|$)", r"^kick(?:\s+|$)"],
        "unban": [r"^حذف\s*بن(?:\s+|$)", r"^unban(?:\s+|$)"],
        "mute": [r"^سکوت(?:\s+|$)", r"^بی‌صدا(?:\s+|$)", r"^mute(?:\s+|$)"],
        "unmute": [r"^حذف\s*سکوت(?:\s+|$)", r"^unmute(?:\s+|$)"],
        "warn": [r"^اخطار(?:\s+|$)", r"^هشدار(?:\s+|$)", r"^warn(?:\s+|$)"],
        "delwarn": [r"^حذف\s*اخطار(?:\s+|$)", r"^delwarn(?:\s+|$)"]
    }

    cmd_type = None
    for cmd, patterns in COMMAND_PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, text):
                cmd_type = cmd
                break
        if cmd_type:
            break

    if not cmd_type:
        return

    if not await _has_access(context, chat.id, user.id):
        return

    target, mention_failed = await _resolve_target(msg, context, chat.id)
    if mention_failed or not target:
        return

    if target.id == context.bot.id:
        await _send_temp(msg, "😅 من ربات هستم — نمی‌توانم تنبیه شوم.", context)
        return
    if target.id in SUDO_IDS:
        await _send_temp(msg, "🚫 امکان اجرای دستور روی این کاربر وجود ندارد.", context)
        return
    try:
        t_member = await context.bot.get_chat_member(chat.id, target.id)
        if t_member.status in ("creator", "administrator"):
            await _send_temp(msg, "🛡 امکان اجرای دستور روی این کاربر وجود ندارد.", context)
            return
    except:
        pass

    # اجرای دستور اصلی
    try:
        if cmd_type == "ban":
            await context.bot.ban_chat_member(chat.id, target.id)
            await msg.reply_text(f"🚫 {target.first_name} از گروه بن شد.")
        elif cmd_type == "unban":
            await context.bot.unban_chat_member(chat.id, target.id)
            await msg.reply_text(f"✅ {target.first_name} از بن خارج شد.")
        elif cmd_type == "mute":
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
            await msg.reply_text(f"🤐 {target.first_name} برای {seconds} ثانیه سکوت شد.")
        elif cmd_type == "unmute":
            await context.bot.restrict_chat_member(
                chat.id, target.id,
                permissions=ChatPermissions(can_send_messages=True)
            )
            await msg.reply_text(f"🔊 {target.first_name} از سکوت خارج شد.")
        elif cmd_type == "warn":
            warns = _load_json(WARN_FILE)
            key = f"{chat.id}:{target.id}"
            warns[key] = warns.get(key, 0) + 1
            _save_json(WARN_FILE, warns)
            if warns[key] >= 3:
                await context.bot.ban_chat_member(chat.id, target.id)
                warns[key] = 0
                _save_json(WARN_FILE, warns)
                await msg.reply_text(f"🚫 {target.first_name} به‌دلیل ۳ اخطار بن شد.")
            else:
                await msg.reply_text(f"⚠️ {target.first_name} اخطار {warns[key]}/3 گرفت.")
        elif cmd_type == "delwarn":
            warns = _load_json(WARN_FILE)
            key = f"{chat.id}:{target.id}"
            if key in warns:
                del warns[key]
                _save_json(WARN_FILE, warns)
                await msg.reply_text(f"✅ اخطارهای {target.first_name} حذف شد.")
    except:
        return


# ================= 🔧 ثبت هندلر =================
def register_punishment_handlers(application, group_number: int = 12):
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_punishments,
        ),
        group=group_number,
    )
