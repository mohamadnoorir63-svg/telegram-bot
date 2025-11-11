# punishments.py
import os
import json
from datetime import datetime, timedelta
from telethon import events
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights

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

async def _has_access(client, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_IDS:
        return True
    try:
        perm = await client.get_permissions(chat_id, user_id)
        return perm.is_admin
    except:
        return False

async def _resolve_target(event, text_arg=None):
    reply = await event.get_reply_message()
    if reply:
        return reply.sender_id

    if text_arg:
        if text_arg.startswith("@"):
            try:
                entity = await event.client.get_entity(text_arg)
                return entity.id
            except:
                return None
        elif text_arg.isdigit():
            return int(text_arg)
    return None

async def handle_punishments(event):
    cmd = event.pattern_match.group(1)
    arg = event.pattern_match.group(2)
    me = await event.client.get_me()
    chat_id = event.chat_id
    sender_id = event.sender_id

    # بررسی دسترسی
    if not await _has_access(event.client, chat_id, sender_id):
        return await event.reply("🚫 فقط مدیران یا سودوها مجاز هستند.")

    # تعیین هدف
    target_id = await _resolve_target(event, arg)
    if not target_id:
        return await event.reply(
            "⚠️ هدف مشخص نیست.\n• ریپلای روی پیام کاربر\n• @username\n• آیدی عددی"
        )

    # محافظت از خود ربات و سودو
    if target_id == me.id or target_id in SUDO_IDS:
        return await event.reply("🚫 امکان اجرای دستور روی این کاربر وجود ندارد.")

    # بررسی ادمین بودن هدف
    try:
        member = await event.client.get_permissions(chat_id, target_id)
        if member.is_admin:
            return await event.reply("🛡 امکان اجرای دستور روی ادمین وجود ندارد.")
    except:
        pass

    # --- اجرای دستورات ---
    try:
        if cmd == "بن":
            rights = ChatBannedRights(until_date=None, view_messages=True, send_messages=True)
            await event.client(EditBannedRequest(chat_id, target_id, rights))
            await event.reply("🚫 کاربر با موفقیت بن شد.")

        elif cmd == "حذف بن":
            rights = ChatBannedRights(until_date=None, view_messages=False, send_messages=False)
            await event.client(EditBannedRequest(chat_id, target_id, rights))
            await event.reply("✅ بن کاربر حذف شد.")

        elif cmd == "سکوت":
            seconds = 3600
            if arg and arg.isdigit():
                seconds = int(arg)
            until = datetime.utcnow() + timedelta(seconds=seconds)
            rights = ChatBannedRights(until_date=until, send_messages=True)
            await event.client(EditBannedRequest(chat_id, target_id, rights))
            await event.reply(f"🤐 کاربر برای {seconds} ثانیه سکوت شد.")

        elif cmd == "حذف سکوت":
            rights = ChatBannedRights(until_date=None, send_messages=False)
            await event.client(EditBannedRequest(chat_id, target_id, rights))
            await event.reply("🔊 سکوت کاربر حذف شد.")

        elif cmd == "اخطار":
            warns = _load_json(WARN_FILE)
            key = f"{chat_id}:{target_id}"
            warns[key] = warns.get(key, 0) + 1
            _save_json(WARN_FILE, warns)
            if warns[key] >= 3:
                rights = ChatBannedRights(until_date=None, view_messages=True, send_messages=True)
                await event.client(EditBannedRequest(chat_id, target_id, rights))
                warns[key] = 0
                _save_json(WARN_FILE, warns)
                await event.reply("🚫 کاربر به دلیل ۳ اخطار بن شد.")
            else:
                await event.reply(f"⚠️ اخطار {warns[key]}/3 داده شد.")

        elif cmd == "حذف اخطار":
            warns = _load_json(WARN_FILE)
            key = f"{chat_id}:{target_id}"
            if key in warns:
                del warns[key]
                _save_json(WARN_FILE, warns)
                await event.reply("✅ اخطارهای کاربر حذف شد.")
            else:
                await event.reply("ℹ️ این کاربر اخطاری ندارد.")
    except Exception as e:
        await event.reply(f"⚠️ خطا در اجرای دستور: {e}")

def register_punishment_handlers(client):
    """ثبت هندلر روی کلاینت Telethon"""
    client.add_event_handler(
        handle_punishments,
        events.NewMessage(pattern=r"^(بن|حذف بن|سکوت|حذف سکوت|اخطار|حذف اخطار)(?:\s+(.+))?$")
    )
