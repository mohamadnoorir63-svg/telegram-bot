import os
import json
import asyncio
import re
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADMINS_FILE = os.path.join(BASE_DIR, "group_admins.json")
SUDO_IDS = [8588347189]  # سودوهای ربات

# ایجاد فایل در صورت عدم وجود
if not os.path.exists(ADMINS_FILE):
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

def _load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def _has_access(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
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

# ================= هندلر دقیق مدیریت مدیران =================
async def handle_admin_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.text:
        return

    chat = update.effective_chat
    user = update.effective_user
    text = msg.text.strip()

    if not chat or chat.type != "supergroup":
        return

    data = _load_json(ADMINS_FILE)
    chat_key = str(chat.id)
    if chat_key not in data:
        data[chat_key] = []

    # بررسی دسترسی ربات
    try:
        me = await context.bot.get_chat_member(chat.id, context.bot.id)
        bot_can_promote = me.status == "creator" or (me.status == "administrator" and getattr(me, "can_promote_members", False))
    except:
        bot_can_promote = False

    if not bot_can_promote:
        reply = await msg.reply_text("🚫 من دسترسی لازم برای مدیریت مدیران را ندارم.")
        asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
        return

    # ================= regex دقیق دستورات =================
    COMMANDS = {
        "add_admin": re.compile(r"^افزودن\s+مدیر$"),
        "remove_admin": re.compile(r"^حذف\s+مدیر$"),
        "list_admins": re.compile(r"^لیست\s+مدیران$")
    }

    cmd_type = None
    for k, pat in COMMANDS.items():
        if pat.fullmatch(text):
            cmd_type = k
            break

    if not cmd_type:
        return  # دستور نامعتبر

    # بررسی دسترسی کاربر
    if not await _has_access(context, chat.id, user.id):
        reply = await msg.reply_text("🚫 فقط مدیران یا سودوها می‌توانند این دستور را اجرا کنند.")
        asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
        return

    # ================= افزودن مدیر =================
    if cmd_type == "add_admin":
        if not msg.reply_to_message:
            reply = await msg.reply_text("⚠️ لطفاً روی پیام کاربر ریپلای کنید.")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
            return
        target = msg.reply_to_message.from_user
        if target.id in SUDO_IDS or target.id == context.bot.id:
            reply = await msg.reply_text("⚠️ نمی‌توان این کاربر را مدیر کرد.")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
            return
        if target.id in data.get(chat_key, []):
            reply = await msg.reply_text(f"⚠️ {target.first_name} قبلاً توسط ربات اضافه شده است.")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
            return
        try:
            await context.bot.promote_chat_member(
                chat.id, target.id,
                can_change_info=True, can_delete_messages=True, can_manage_video_chats=True,
                can_restrict_members=True, can_invite_users=True, can_pin_messages=True,
                can_promote_members=True, can_manage_topics=True
            )
            data[chat_key].append(target.id)
            _save_json(ADMINS_FILE, data)
            reply = await msg.reply_text(f"✅ {target.first_name} به‌عنوان مدیر اضافه شد.")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
        except Exception as e:
            reply = await msg.reply_text(f"⚠️ خطا در افزودن مدیر: {e}")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))

    # ================= حذف مدیر =================
    elif cmd_type == "remove_admin":
        if not msg.reply_to_message:
            reply = await msg.reply_text("⚠️ لطفاً روی پیام مدیر ریپلای کنید.")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
            return
        target = msg.reply_to_message.from_user
        if target.id in SUDO_IDS or target.id == context.bot.id:
            reply = await msg.reply_text("🚫 نمی‌توان این کاربر را حذف کرد!")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
            return
        if target.id not in data.get(chat_key, []):
            reply = await msg.reply_text("⚠️ این کاربر قبلاً توسط ربات اضافه نشده است.")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
            return
        try:
            await context.bot.promote_chat_member(
                chat.id, target.id,
                can_change_info=False, can_delete_messages=False, can_manage_video_chats=False,
                can_restrict_members=False, can_invite_users=False, can_pin_messages=False,
                can_promote_members=False, can_manage_topics=False
            )
            data[chat_key].remove(target.id)
            _save_json(ADMINS_FILE, data)
            reply = await msg.reply_text(f"⚙️ {target.first_name} از مدیران حذف شد.")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
        except Exception as e:
            reply = await msg.reply_text(f"⚠️ خطا در حذف مدیر: {e}")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))

    # ================= لیست مدیران =================
    elif cmd_type == "list_admins":
        try:
            current_admins = await context.bot.get_chat_administrators(chat.id)
            lines = [f"• {a.user.first_name}" for a in current_admins if not a.user.is_bot]
            text = "👑 <b>مدیران فعلی گروه:</b>\n" + "\n".join(lines) if lines else "ℹ️ هیچ مدیری یافت نشد."
            reply = await msg.reply_text(text, parse_mode="HTML")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 20))
        except Exception as e:
            reply = await msg.reply_text(f"⚠️ خطا در دریافت لیست مدیران: {e}")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))

# ================= ثبت هندلر =================
def register_admin_handlers(application, group_number: int = 15):
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_admin_management,
        ),
        group=group_number,
    )
