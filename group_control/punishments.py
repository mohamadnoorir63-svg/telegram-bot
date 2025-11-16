import os
import json
import re
import asyncio
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, MessageHandler, filters

# ================= ⚙️ تنظیمات اولیه =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ADMINS_FILE = os.path.join(BASE_DIR, "group_admins.json")
WARN_FILE = os.path.join(BASE_DIR, "warnings.json")
BAN_FILE = os.path.join(BASE_DIR, "ban_list.json")
MUTE_FILE = os.path.join(BASE_DIR, "mute_list.json")
ALIAS_FILE = os.path.join(BASE_DIR, "custom_aliases.json")

SUDO_IDS = [8588347189]  # آیدی سودوها

for f in [ADMINS_FILE, WARN_FILE, BAN_FILE, MUTE_FILE, ALIAS_FILE]:
    if not os.path.exists(f):
        with open(f, "w", encoding="utf-8") as x:
            json.dump({}, x, ensure_ascii=False, indent=2)

# ---------- یوزربات (اختیاری) ----------
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
    except:
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
    except:
        return False

async def _auto_delete(bot, chat_id: int, message_id: int, delay: int = 10):
    try:
        await asyncio.sleep(delay)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except:
        pass

# ================= 🧰 مدیریت مدیران =================
def _load_admins(chat_id):
    data = _load_json(ADMINS_FILE)
    return data.get(str(chat_id), [])

def _save_admin(chat_id, user_id):
    data = _load_json(ADMINS_FILE)
    key = str(chat_id)
    if key not in data:
        data[key] = []
    if user_id not in data[key]:
        data[key].append(user_id)
    _save_json(ADMINS_FILE, data)

def _remove_admin(chat_id, user_id):
    data = _load_json(ADMINS_FILE)
    key = str(chat_id)
    if key in data and user_id in data[key]:
        data[key].remove(user_id)
        _save_json(ADMINS_FILE, data)

async def handle_admin_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not msg or not msg.text or chat.type != "supergroup":
        return
    text = msg.text.strip()

    if not await _has_access(context, chat.id, user.id):
        reply = await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
        asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
        return

    # ===== افزودن مدیر =====
    if text.startswith("افزودن مدیر") and msg.reply_to_message:
        target = msg.reply_to_message.from_user
        if target.id in SUDO_IDS or target.id == context.bot.id:
            reply = await msg.reply_text("⚠️ نمی‌توان این کاربر را مدیر کرد.")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
            return
        try:
            await context.bot.promote_chat_member(
                chat.id, target.id,
                can_change_info=True, can_delete_messages=True, can_manage_video_chats=True,
                can_restrict_members=True, can_invite_users=True, can_pin_messages=True,
                can_promote_members=True, can_manage_topics=True
            )
            _save_admin(chat.id, target.id)
            reply = await msg.reply_text(f"✅ {target.first_name} مدیر شد.")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
        except Exception as e:
            reply = await msg.reply_text(f"⚠️ خطا در افزودن مدیر: {e}")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))

    # ===== حذف مدیر =====
    elif text.startswith("حذف مدیر") and msg.reply_to_message:
        target = msg.reply_to_message.from_user
        if target.id in SUDO_IDS or target.id == context.bot.id:
            reply = await msg.reply_text("🚫 نمی‌توان این کاربر را حذف کرد!")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
            return
        try:
            await context.bot.promote_chat_member(
                chat.id, target.id,
                can_change_info=False, can_delete_messages=False, can_manage_video_chats=False,
                can_restrict_members=False, can_invite_users=False, can_pin_messages=False,
                can_promote_members=False, can_manage_topics=False
            )
            _remove_admin(chat.id, target.id)
            reply = await msg.reply_text(f"⚙️ {target.first_name} از مدیران حذف شد.")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
        except Exception as e:
            reply = await msg.reply_text(f"⚠️ خطا در حذف مدیر: {e}")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))

    # ===== لیست مدیران =====
    elif text == "لیست مدیران":
        try:
            current_admins = await context.bot.get_chat_administrators(chat.id)
            lines = [f"• {a.user.first_name}" for a in current_admins if not a.user.is_bot]
            reply = await msg.reply_text("👑 مدیران:\n" + ("\n".join(lines) if lines else "هیچ کس"))
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 20))
        except Exception as e:
            reply = await msg.reply_text(f"⚠️ خطا در دریافت لیست مدیران: {e}")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))

# ================= 🧰 سیستم alias =================
def _load_aliases(chat_id):
    data = _load_json(ALIAS_FILE)
    return data.get(str(chat_id), {})

def _save_alias(chat_id, alias, cmd_type, template="{Name}"):
    data = _load_json(ALIAS_FILE)
    key = str(chat_id)
    if key not in data:
        data[key] = {}
    data[key][alias] = {"type": cmd_type, "template": template}
    _save_json(ALIAS_FILE, data)

def _delete_alias(chat_id, alias):
    data = _load_json(ALIAS_FILE)
    key = str(chat_id)
    if key in data and alias in data[key]:
        del data[key][alias]
        _save_json(ALIAS_FILE, data)

async def handle_alias_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not msg or chat.type not in ("group", "supergroup"):
        return
    text = (msg.text or "").strip()

    if not await _has_access(context, chat.id, user.id):
        return

    # افزودن alias
    m_add = re.match(r"^افزودن دستور\s+(.+)\s+(بن|سکوت|اخطار)\s+\{Name\}", text)
    if m_add:
        alias_text = m_add.group(1).strip()
        cmd_type = m_add.group(2).strip()
        _save_alias(chat.id, alias_text, cmd_type)
        await msg.reply_text(f"✅ دستور alias '{alias_text}' برای {cmd_type} ساخته شد.")
        return

    # حذف alias
    m_del = re.match(r"^حذف دستور\s+(.+)$", text)
    if m_del:
        alias_text = m_del.group(1).strip()
        _delete_alias(chat.id, alias_text)
        await msg.reply_text(f"✅ دستور alias '{alias_text}' حذف شد.")
        return

# ================= 🧰 دستورات تنبیهی =================
def add_to_list(file, chat_id, user):
    data = _load_json(file)
    key = str(chat_id)
    if key not in data:
        data[key] = {}
    data[key][str(user.id)] = user.username or ""
    _save_json(file, data)

def remove_from_list(file, chat_id, user):
    data = _load_json(file)
    key = str(chat_id)
    if key in data and str(user.id) in data[key]:
        del data[key][str(user.id)]
        _save_json(file, data)

def list_from_file(file, chat_id):
    data = _load_json(file)
    key = str(chat_id)
    if key in data:
        return [f"{uid} ({uname})" if uname else str(uid) for uid, uname in data[key].items()]
    return []

async def _resolve_target(msg, context, chat_id, explicit_arg=None):
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
        except:
            pass
    m_username = re.search(r"@([A-Za-z0-9_]{3,32})", text)
    if m_username:
        username = m_username.group(1)
        try:
            user_obj = await context.bot.get_chat(f"@{username}")
            if user_obj: return user_obj
        except:
            pass
    return None

async def handle_punishments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # همان کد تنبیهی که پیش‌تر نوشتی، بدون تغییر
    ...

# ================= 🧰 اجرای alias روی punish =================
async def handle_punishments_with_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    if not msg or chat.type not in ("group", "supergroup"):
        return
    text = (msg.text or "").strip()

    aliases = _load_aliases(chat.id)
    for alias_text, info in aliases.items():
        if alias_text in text:
            if msg.reply_to_message and getattr(msg.reply_to_message, "from_user", None):
                target_user = msg.reply_to_message.from_user
                msg.text = f"{info['type']} {target_user.id}"
                await handle_punishments(update, context)
                return

# ================= 🧩 ثبت هندلرها =================
def register_all_handlers(application):
    # مدیران
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.SUPERGROUPS,
                       handle_admin_management), group=15)
    # alias مدیریت alias
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.SUPERGROUPS,
                       handle_alias_management), group=14)
    # دستورات تنبیهی با alias
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
                       handle_punishments_with_alias), group=12)
