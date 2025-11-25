import os
import json
import re
import asyncio
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, MessageHandler, filters

# ================= ⚙️ تنظیمات اولیه =================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WARN_FILE = os.path.join(BASE_DIR, "warnings.json")
BAN_FILE = os.path.join(BASE_DIR, "ban_list.json")
MUTE_FILE = os.path.join(BASE_DIR, "mute_list.json")
ALIAS_FILE = os.path.join(BASE_DIR, "alias_cmds.json")

SUDO_IDS = [8588347189]  # آیدی سودوها

# ایجاد فایل‌ها در صورت نبود
for file in [WARN_FILE, BAN_FILE, MUTE_FILE, ALIAS_FILE]:
    if not os.path.exists(file):
        with open(file, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

# ---------- یوزربات ----------
try:
    from userbot_module.userbot import client as userbot_client
    from userbot_module.userbot import punish_via_userbot
except ImportError:
    userbot_client = None
    async def punish_via_userbot(*args, **kwargs):
        pass

# ================= 📁 توابع کمکی =================

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

async def _resolve_target(msg, context, chat_id, explicit_arg: str = None):
    # اگر reply زده شده باشد
    if msg.reply_to_message and getattr(msg.reply_to_message, "from_user", None):
        return msg.reply_to_message.from_user

    text = (msg.text or "").strip()
    user_id = explicit_arg if explicit_arg and explicit_arg.isdigit() else None

    if not user_id:
        m_id = re.search(r"\b(\d{6,15})\b", text)
        if m_id:
            user_id = m_id.group(1)

    if user_id:
        try:
            cm = await context.bot.get_chat_member(chat_id, int(user_id))
            return cm.user
        except Exception as e:
            print(f"⚠️ خطا در گرفتن آیدی عددی: {e}")

    m_username = re.search(r"@([A-Za-z0-9_]{3,32})", text)
    if m_username:
        username = m_username.group(1)
        try:
            user_obj = await context.bot.get_chat(f"@{username}")
            if user_obj:
                return user_obj
        except Exception as e:
            print(f"⚠️ ربات نتونست @{username} رو resolve کنه: {e}")

        if userbot_client:
            try:
                user_entity = await userbot_client.get_entity(f"@{username}")
                class DummyUser:
                    def __init__(self, id, first_name, username=None):
                        self.id = id
                        self.first_name = first_name
                        self.username = username
                return DummyUser(user_entity.id, getattr(user_entity, "first_name", username), username)
            except Exception as e2:
                print(f"⚠️ یوزربات هم نتونست @{username} رو resolve کنه: {e2}")

    return None

def add_to_list(file, chat_id, user):
    data = _load_json(file)
    chat_key = str(chat_id)
    if chat_key not in data:
        data[chat_key] = {}
    data[chat_key][str(user.id)] = user.username or ""
    _save_json(file, data)

def remove_from_list(file, chat_id, user):
    data = _load_json(file)
    chat_key = str(chat_id)
    if chat_key in data and str(user.id) in data[chat_key]:
        del data[chat_key][str(user.id)]
        _save_json(file, data)

def list_from_file(file, chat_id):
    data = _load_json(file)
    chat_key = str(chat_id)
    if chat_key in data:
        return [f"{uid} ({uname})" if uname else str(uid) for uid, uname in data[chat_key].items()]
    return []

# ================= 🔐 هندلر تنبیه و alias =================

async def handle_punishments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not msg or chat.type not in ("group", "supergroup"):
        return

    text = (msg.text or "").strip()

    # ---------- ساخت alias داخل گروه ----------
    match_alias = re.match(r"افزودن دستور (.+?)\s+(.+)", text)
    if match_alias:
        if not await _has_access(context, chat.id, user.id):
            return
        alias_name = match_alias.group(1).strip()
        original_cmd = match_alias.group(2).strip()
        data = _load_json(ALIAS_FILE)
        chat_key = str(chat.id)
        if chat_key not in data:
            data[chat_key] = {}
        data[chat_key][alias_name] = original_cmd
        _save_json(ALIAS_FILE, data)
        reply = await msg.reply_text(f"✅ دستور alias ساخته شد:\n`{alias_name}`→`{original_cmd}`", parse_mode="Markdown")
        await asyncio.sleep(10)
        await reply.delete()
        return

    # ---------- لیست‌ها فقط برای مدیران و سودوها ----------
    if text in ["لیست بن", "لیست سکوت"]:
        if not await _has_access(context, chat.id, user.id):
            return
        file = BAN_FILE if text == "لیست بن" else MUTE_FILE
        items = list_from_file(file, chat.id)
        title = "لیست بن شده‌ها" if file == BAN_FILE else "لیست سکوت شده‌ها"
        reply = await msg.reply_text(f"{'🚫' if file==BAN_FILE else '🤐'} {title}:\n" + ("\n".join(items) if items else "هیچ کس"))
        await asyncio.sleep(10)
        await reply.delete()
        return

    # ---------- regex دستورات ----------
    PATTERNS = {
        "ban": re.compile(r"^بن(?:\s+(@?[A-Za-z0-9_]{3,32}|\d{6,15}))?$"),
        "unban": re.compile(r"^حذف\s+بن(?:\s+(@?[A-Za-z0-9_]{3,32}|\d{6,15}))?$"),
        "mute": re.compile(r"^سکوت(?:\s+(@?[A-Za-z0-9_]{3,32}|\d{6,15}))?$"),  # سکوت دائمی
        "unmute": re.compile(r"^حذف\s+سکوت(?:\s+(@?[A-Za-z0-9_]{3,32}|\d{6,15}))?$"),
        "warn": re.compile(r"^اخطار(?:\s+(@?[A-Za-z0-9_]{3,32}|\d{6,15}))?$"),
        "delwarn": re.compile(r"^حذف\s+اخطار(?:\s+(@?[A-Za-z0-9_]{3,32}|\d{6,15}))?$"),
    }

    matched = None
    cmd_type = None

    # ابتدا دستور اصلی را چک کن
    for k, pat in PATTERNS.items():
        m = pat.fullmatch(text)
        if m:
            cmd_type = k
            matched = m
            break

    # اگر دستور اصلی match نشد، alias را بررسی کن
    if not cmd_type:
        aliases_all = _load_json(ALIAS_FILE)
        chat_aliases = aliases_all.get(str(chat.id), {})
        for alias_text, alias_cmd in chat_aliases.items():
            if text.startswith(alias_text):
                text = alias_cmd
                for k, pat in PATTERNS.items():
                    m = pat.fullmatch(text)
                    if m:
                        cmd_type = k
                        matched = m
                        break
                break  # فقط اولین alias match شود

    if not cmd_type:
        return

    if not await _has_access(context, chat.id, user.id):
        return

    explicit_arg = matched.group(1) if matched else None

    # ---------- تعیین هدف ----------
    target_user = None
    if msg.reply_to_message and getattr(msg.reply_to_message, "from_user", None):
        target_user = msg.reply_to_message.from_user
    else:
        target_user = await _resolve_target(msg, context, chat.id, explicit_arg)

    if not target_user:
        reply = await msg.reply_text(
            "⚠️ هدف مشخص نیست.\n• ریپلای روی پیام کاربر\n• یا آیدی عددی/یوزرنیم"
        )
        await asyncio.sleep(10)
        await reply.delete()
        return

    # ---------- مرجع کاربر و ربات ----------
    bot_user = await context.bot.get_me()
    target_ref = f"@{target_user.username}" if getattr(target_user, "username", None) else str(target_user.id)

    # ---------- محدودیت‌ها ----------
    if target_user.id == bot_user.id:
        reply = await msg.reply_text("🚫 نمی‌توان روی ربات اقدام کرد.")
        await asyncio.sleep(10)
        await reply.delete()
        return

    if target_user.id in SUDO_IDS:
        reply = await msg.reply_text("🚫 نمی‌توان روی سودوها یا سودو ربات اقدام کرد.")
        await asyncio.sleep(10)
        await reply.delete()
        return

    try:
        tm = await context.bot.get_chat_member(chat.id, target_user.id)

        if tm.status == "creator":
            reply = await msg.reply_text("🛡 امکان اجرای دستور روی سازنده گروه وجود ندارد.")
            await asyncio.sleep(10)
            await reply.delete()
            return

        if tm.status == "administrator":
            # اگر هدف سودو ربات باشد، اجازه بده
            if target_user.id in SUDO_IDS:
                pass
            else:
                reply = await msg.reply_text("🛡 امکان اجرای دستور روی مدیر گروه وجود ندارد.")
                await asyncio.sleep(10)
                await reply.delete()
                return

    except Exception:
        pass

    # ---------- اجرای دستورات ----------
    try:
        if cmd_type == "ban":
            await context.bot.ban_chat_member(chat.id, target_user.id)
            add_to_list(BAN_FILE, chat.id, target_user)
            await punish_via_userbot(chat.id, target_ref, action="ban")
            reply = await msg.reply_text(f"🚫 {target_user.first_name} از گروه بن شد.")

        elif cmd_type == "unban":
            await context.bot.unban_chat_member(chat.id, target_user.id)
            remove_from_list(BAN_FILE, chat.id, target_user)
            await punish_via_userbot(chat.id, target_ref, action="unban")
            reply = await msg.reply_text(f"✅ {target_user.first_name} از بن خارج شد.")

        elif cmd_type == "mute":
            permissions = ChatPermissions(
                can_send_messages=False,
                can_send_polls=False,
                can_add_web_page_previews=False
            )
            await context.bot.restrict_chat_member(
                chat.id,
                target_user.id,
                permissions=permissions,
                until_date=None  # سکوت دائمی
            )
            add_to_list(MUTE_FILE, chat.id, target_user)
            await punish_via_userbot(chat.id, target_ref, action="mute")
            reply = await msg.reply_text(f"🤐 {target_user.first_name} برای همیشه سکوت شد.")

        elif cmd_type == "unmute":
            permissions = ChatPermissions(
                can_send_messages=True,
                can_send_polls=True,
                can_add_web_page_previews=True
            )
            await context.bot.restrict_chat_member(
                chat.id,
                target_user.id,
                permissions=permissions,
                until_date=None
            )
            remove_from_list(MUTE_FILE, chat.id, target_user)
            await punish_via_userbot(chat.id, target_ref, action="unmute")
            reply = await msg.reply_text(f"🔊 {target_user.first_name} از سکوت خارج شد.")

        elif cmd_type == "warn":
            warns = _load_json(WARN_FILE)
            key = f"{chat.id}:{target_user.id}"
            warns[key] = warns.get(key, 0) + 1
            _save_json(WARN_FILE, warns)
            if warns[key] >= 3:
                await context.bot.ban_chat_member(chat.id, target_user.id)
                add_to_list(BAN_FILE, chat.id, target_user)
                await punish_via_userbot(chat.id, target_ref, action="ban")
                warns[key] = 0
                _save_json(WARN_FILE, warns)
                reply = await msg.reply_text(f"🚫 {target_user.first_name} به‌دلیل ۳ اخطار بن شد.")
            else:
                reply = await msg.reply_text(f"⚠️ {target_user.first_name} اخطار {warns[key]}/3 گرفت.")

        elif cmd_type == "delwarn":
            warns = _load_json(WARN_FILE)
            key = f"{chat.id}:{target_user.id}"
            if key in warns:
                del warns[key]
                _save_json(WARN_FILE, warns)
                reply = await msg.reply_text(f"✅ اخطارهای {target_user.first_name} حذف شد.")
            else:
                reply = await msg.reply_text("ℹ️ این کاربر اخطاری نداشت.")

        await asyncio.sleep(10)
        await reply.delete()

    except Exception as e:
        print("handle_punishments execution exception:", e)
        reply = await msg.reply_text(f"⚠️ خطا در اجرای دستور: {e}")
        await asyncio.sleep(10)
        await reply.delete()

# ================= 🧩 ثبت هندلر =================

def register_punishment_handlers(application, group_number: int = 12):
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_punishments,
        ),
        group=group_number,
    )
