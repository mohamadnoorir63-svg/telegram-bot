import os
import json
import re
import asyncio
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADMINS_FILE = os.path.join(BASE_DIR, "group_admins.json")
CUSTOM_CMD_FILE = os.path.join(BASE_DIR, "benutzerdefiniert.json")  # کلید امن آلمانی

SUDO_IDS = [8588347189]

for f in (ADMINS_FILE, CUSTOM_CMD_FILE):
    if not os.path.exists(f):
        with open(f, "w", encoding="utf-8") as x:
            json.dump({}, x, ensure_ascii=False, indent=2)

def _load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def _has_access(context, chat_id, user_id):
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False

async def _bot_can_promote(context, chat_id):
    try:
        me = await context.bot.get_chat_member(chat_id, context.bot.id)
        return me.status == "creator" or getattr(me, "can_promote_members", False)
    except:
        return False

async def _get_target_user(update: Update, context, text: str):
    msg = update.effective_message
    chat_id = update.effective_chat.id

    # ریپلای
    if msg.reply_to_message:
        return msg.reply_to_message.from_user, None

    parts = text.split()
    if len(parts) >= 2:
        identifier = parts[1]
        if identifier.startswith("@"):
            try:
                user = await context.bot.get_chat_member(chat_id, identifier)
                return user.user, None
            except:
                return None, identifier  # mention اشتباه
        else:
            try:
                user_id = int(identifier)
                user = await context.bot.get_chat_member(chat_id, user_id)
                return user.user, None
            except:
                return None, None
    return None, None

# ================= 📦 پیام‌های موقت =================
async def _send_temp_message(msg, text, context, delete_after=10):
    sent = await msg.reply_text(text)
    asyncio.create_task(_delete_after(sent, delete_after, context))

async def _delete_after(message, delay, context):
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

# ================= 🔧 هندلر =================
async def handle_admin_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    text = (msg.text or "").strip()

    if chat.type not in ("group", "supergroup") or not text:
        return

    data = _load_json(ADMINS_FILE)
    chat_key = str(chat.id)
    if chat_key not in data:
        data[chat_key] = []

    custom_all = _load_json(CUSTOM_CMD_FILE)
    custom_cmds = custom_all.get(chat_key, {})

    # ====== ثبت دستور جدید ======
    if text.startswith("دستور جدید"):
        if not await _has_access(context, chat.id, user.id):
            return  # ساکت بماند
        match = re.match(r"^دستور جدید\s+(.+?)\s+(افزودن‌مدیر|حذف‌مدیر)\s+(.+)$", text)
        if not match:
            await _send_temp_message(
                msg,
                "📘 فرمت درست:\n<code>دستور جدید [نام دستور] [افزودن‌مدیر|حذف‌مدیر] [متن پاسخ]</code>",
                context
            )
            return
        name, cmd_type, response = match.groups()
        if name in custom_cmds:
            await _send_temp_message(msg, "⚠️ این نام قبلاً تعریف شده.", context)
            return
        custom_cmds[name] = {"type": cmd_type, "text": response}
        custom_all[chat_key] = custom_cmds
        _save_json(CUSTOM_CMD_FILE, custom_all)
        await _send_temp_message(msg, f"✅ دستور جدید <b>{name}</b> ثبت شد.", context)
        return

    # ====== اجرای دستورات سفارشی ======
    if text in custom_cmds:
        cmd_info = custom_cmds[text]
        target, mention_failed = await _get_target_user(update, context, text)

        # اگر mention اشتباه باشد یا هدف نبود → ساکت
        if mention_failed or not target:
            return

        # محافظت‌ها
        if target.id == context.bot.id:
            await _send_temp_message(msg, "😅 نمی‌توانم خودم را مدیر کنم!", context)
            return
        if target.id in SUDO_IDS:
            await _send_temp_message(msg, "👑 این کاربر جزو سودوهاست و تغییر نمی‌شود.", context)
            return
        if not await _bot_can_promote(context, chat.id):
            await _send_temp_message(msg, "🚫 من اجازه‌ی تغییر مدیران را ندارم. لطفاً ربات را ادمین کنید.", context)
            return

        try:
            if cmd_info["type"] == "افزودن‌مدیر":
                await context.bot.promote_chat_member(
                    chat_id=chat.id, user_id=target.id,
                    can_delete_messages=True, can_restrict_members=True,
                    can_invite_users=True, can_pin_messages=True,
                    can_manage_topics=True
                )
                if target.id not in data[chat_key]:
                    data[chat_key].append(target.id)
                    _save_json(ADMINS_FILE, data)
            elif cmd_info["type"] == "حذف‌مدیر":
                await context.bot.promote_chat_member(
                    chat_id=chat.id, user_id=target.id,
                    can_manage_chat=False, can_delete_messages=False,
                    can_manage_video_chats=False, can_restrict_members=False,
                    can_promote_members=False, can_change_info=False,
                    can_invite_users=False, can_pin_messages=False,
                    can_manage_topics=False
                )
                if target.id in data[chat_key]:
                    data[chat_key].remove(target.id)
                    _save_json(ADMINS_FILE, data)

            text_out = cmd_info.get("text", "").replace("{name}", target.first_name)
            await _send_temp_message(msg, text_out or "✅ عملیات انجام شد.", context)
        except:
            pass
        return

    # ====== دستورات اصلی ======
    target, mention_failed = await _get_target_user(update, context, text)
    if mention_failed or not target:
        return  # ساکت بماند

    if text.startswith("افزودن مدیر"):
        if not await _has_access(context, chat.id, user.id):
            return
        if target.id == context.bot.id:
            await _send_temp_message(msg, "😅 نمی‌توانم خودم را مدیر کنم!", context)
            return
        if target.id in SUDO_IDS:
            await _send_temp_message(msg, "👑 این کاربر جزو سودوهاست و تغییر نمی‌شود.", context)
            return
        if not await _bot_can_promote(context, chat.id):
            await _send_temp_message(msg, "🚫 من اجازه‌ی تغییر مدیران را ندارم.", context)
            return
        try:
            await context.bot.promote_chat_member(
                chat_id=chat.id, user_id=target.id,
                can_delete_messages=True, can_restrict_members=True,
                can_invite_users=True, can_pin_messages=True,
                can_manage_topics=True
            )
            if target.id not in data[chat_key]:
                data[chat_key].append(target.id)
                _save_json(ADMINS_FILE, data)
            await _send_temp_message(msg, f"👑 {target.first_name} به‌عنوان مدیر گروه منصوب شد.", context)
        except:
            pass
        return

    if text.startswith("حذف مدیر"):
        if not await _has_access(context, chat.id, user.id):
            return
        if target.id == context.bot.id:
            await _send_temp_message(msg, "😅 نمی‌توانم خودم را حذف کنم!", context)
            return
        if target.id in SUDO_IDS:
            await _send_temp_message(msg, "👑 این کاربر جزو سودوهاست و تغییر نمی‌شود.", context)
            return
        if not await _bot_can_promote(context, chat.id):
            await _send_temp_message(msg, "🚫 من اجازه‌ی تغییر مدیران را ندارم.", context)
            return
        try:
            await context.bot.promote_chat_member(
                chat_id=chat.id, user_id=target.id,
                can_manage_chat=False, can_delete_messages=False,
                can_manage_video_chats=False, can_restrict_members=False,
                can_promote_members=False, can_change_info=False,
                can_invite_users=False, can_pin_messages=False,
                can_manage_topics=False
            )
            if target.id in data[chat_key]:
                data[chat_key].remove(target.id)
                _save_json(ADMINS_FILE, data)
            await _send_temp_message(msg, f"⚙️ {target.first_name} از فهرست مدیران حذف شد.", context)
        except:
            pass
        return

    if text == "لیست مدیران":
        try:
            current_admins = await context.bot.get_chat_administrators(chat.id)
            lines = [f"• {a.user.first_name}" for a in current_admins if not a.user.is_bot]
            await _send_temp_message(msg, "👑 مدیران فعلی گروه:\n" + "\n".join(lines) if lines else "ℹ️ هیچ مدیری در گروه یافت نشد.", context)
        except:
            pass

def register_admin_handlers(application, group_number: int = 15):
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_admin_management,
        ),
        group=group_number,
    )
