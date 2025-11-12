import os
import json
import re
import asyncio
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADMINS_FILE = os.path.join(BASE_DIR, "group_admins.json")
CUSTOM_CMD_FILE = os.path.join(BASE_DIR, "custom_commands.json")

# 🔱 ایدی‌های سودو
SUDO_IDS = [8588347189]

# 📁 ساخت فایل‌ها در صورت نبود
for f in (ADMINS_FILE, CUSTOM_CMD_FILE):
    if not os.path.exists(f):
        with open(f, "w", encoding="utf-8") as x:
            json.dump({}, x, ensure_ascii=False, indent=2)


# ===== ابزارهای کمکی =====
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
    """بررسی اینکه کاربر سودو یا مدیر گروه است"""
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False


async def _bot_can_promote(context, chat_id):
    """بررسی اینکه ربات اجازه‌ی ترفیع دارد"""
    try:
        me = await context.bot.get_chat_member(chat_id, context.bot.id)
        return me.status == "creator" or getattr(me, "can_promote_members", False)
    except:
        return False


async def _get_target_user(update: Update, context, text: str):
    """دریافت هدف از ریپلای یا @username یا آیدی"""
    msg = update.effective_message
    chat_id = update.effective_chat.id

    if msg.reply_to_message:
        return msg.reply_to_message.from_user, None

    parts = text.split()
    if len(parts) >= 2:
        identifier = parts[1]
        try:
            if identifier.startswith("@"):
                member = await context.bot.get_chat_member(chat_id, identifier)
                return member.user, None
            else:
                uid = int(identifier)
                member = await context.bot.get_chat_member(chat_id, uid)
                return member.user, None
        except:
            return None, identifier
    return None, None


async def _send_temp_message(msg, text, context, delete_after=10):
    sent = await msg.reply_text(text, parse_mode="HTML")
    asyncio.create_task(_delete_after(sent, delete_after, context))


async def _delete_after(message, delay, context):
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(message.chat.id, message.message_id)
    except:
        pass


# ===== هندلر اصلی مدیریت =====
async def handle_admin_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    text = (msg.text or "").strip()

    if chat.type not in ("group", "supergroup") or not text:
        return

    # 📂 بارگذاری داده‌ها
    data = _load_json(ADMINS_FILE)
    chat_key = str(chat.id)
    if chat_key not in data:
        data[chat_key] = []

    custom_all = _load_json(CUSTOM_CMD_FILE)
    custom_cmds = custom_all.get(chat_key, {})

    # ===== دستور سفارشی =====
    if text.startswith("دستور جدید"):
        if not await _has_access(context, chat.id, user.id):
            return
        match = re.match(r"^دستور جدید\s+(.+?)\s+(افزودن‌مدیر|حذف‌مدیر)\s+(.+)$", text)
        if not match:
            await _send_temp_message(
                msg,
                "📘 فرمت درست:\n<code>دستور جدید [نام دستور] [افزودن‌مدیر|حذف‌مدیر] [متن پاسخ]</code>",
                context,
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

    # ===== اجرای دستورات سفارشی =====
    if text in custom_cmds:
        cmd = custom_cmds[text]
        target, mention_failed = await _get_target_user(update, context, text)
        if not target or mention_failed:
            return

        if target.id == context.bot.id or target.id in SUDO_IDS:
            await _send_temp_message(msg, "⚠️ این کاربر تغییر نمی‌کند.", context)
            return

        # ✅ تشخیص حالت UserBot یا BotFather
        is_userbot = getattr(context.bot, "is_user", False)
        if not is_userbot and not await _bot_can_promote(context, chat.id):
            await _send_temp_message(msg, "🚫 من اجازه‌ی تغییر مدیران را ندارم.", context)
            return

        try:
            if cmd["type"] == "افزودن‌مدیر":
                if is_userbot:
                    await context.bot.promote_chat_member(
                        chat_id=chat.id,
                        user_id=target.id,
                        can_delete_messages=True,
                        can_restrict_members=True,
                        can_invite_users=True,
                        can_pin_messages=True,
                        can_manage_topics=True,
                    )
                data[chat_key].append(target.id)
                _save_json(ADMINS_FILE, data)
                text_out = cmd["text"].replace("{name}", target.first_name)
                await _send_temp_message(msg, text_out or "✅ مدیر افزوده شد.", context)

            elif cmd["type"] == "حذف‌مدیر":
                if is_userbot:
                    await context.bot.promote_chat_member(
                        chat_id=chat.id,
                        user_id=target.id,
                        can_manage_chat=False,
                        can_delete_messages=False,
                        can_manage_video_chats=False,
                        can_restrict_members=False,
                        can_promote_members=False,
                        can_change_info=False,
                        can_invite_users=False,
                        can_pin_messages=False,
                        can_manage_topics=False,
                    )
                if target.id in data[chat_key]:
                    data[chat_key].remove(target.id)
                    _save_json(ADMINS_FILE, data)
                text_out = cmd["text"].replace("{name}", target.first_name)
                await _send_temp_message(msg, text_out or "⚙️ مدیر حذف شد.", context)
        except Exception as e:
            await _send_temp_message(msg, f"⚠️ خطا: {e}", context)
        return

    # ===== دستورات ثابت =====
    target, mention_failed = await _get_target_user(update, context, text)
    if mention_failed:
        return

    is_userbot = getattr(context.bot, "is_user", False)

    if text == "افزودن مدیر" and target:
        if not await _has_access(context, chat.id, user.id):
            await _send_temp_message(msg, "🚫 فقط مدیران یا سودوها مجازند.", context)
            return
        if target.id == context.bot.id or target.id in SUDO_IDS:
            await _send_temp_message(msg, "⚠️ این کاربر تغییر نمی‌کند.", context)
            return
        if target.id in data[chat_key]:
            await _send_temp_message(msg, f"ℹ️ {target.first_name} قبلاً مدیر است.", context)
            return
        if not is_userbot and not await _bot_can_promote(context, chat.id):
            await _send_temp_message(msg, "🚫 من اجازه‌ی تغییر مدیران را ندارم.", context)
            return

        try:
            if is_userbot:
                await context.bot.promote_chat_member(
                    chat_id=chat.id,
                    user_id=target.id,
                    can_delete_messages=True,
                    can_restrict_members=True,
                    can_invite_users=True,
                    can_pin_messages=True,
                    can_manage_topics=True,
                )
            data[chat_key].append(target.id)
            _save_json(ADMINS_FILE, data)
            await _send_temp_message(msg, f"👑 {target.first_name} به‌عنوان مدیر منصوب شد.", context)
        except Exception as e:
            await _send_temp_message(msg, f"⚠️ خطا در افزودن مدیر: {e}", context)
        return

    if text == "حذف مدیر" and target:
        if not await _has_access(context, chat.id, user.id):
            await _send_temp_message(msg, "🚫 فقط مدیران یا سودوها مجازند.", context)
            return
        if target.id == context.bot.id or target.id in SUDO_IDS:
            await _send_temp_message(msg, "⚠️ این کاربر تغییر نمی‌کند.", context)
            return
        if target.id not in data[chat_key]:
            await _send_temp_message(msg, f"ℹ️ {target.first_name} قبلاً مدیر نبوده است.", context)
            return
        if not is_userbot and not await _bot_can_promote(context, chat.id):
            await _send_temp_message(msg, "🚫 من اجازه‌ی تغییر مدیران را ندارم.", context)
            return

        try:
            if is_userbot:
                await context.bot.promote_chat_member(
                    chat_id=chat.id,
                    user_id=target.id,
                    can_manage_chat=False,
                    can_delete_messages=False,
                    can_manage_video_chats=False,
                    can_restrict_members=False,
                    can_promote_members=False,
                    can_change_info=False,
                    can_invite_users=False,
                    can_pin_messages=False,
                    can_manage_topics=False,
                )
            if target.id in data[chat_key]:
                data[chat_key].remove(target.id)
                _save_json(ADMINS_FILE, data)
            await _send_temp_message(msg, f"⚙️ {target.first_name} از مدیران حذف شد.", context)
        except Exception as e:
            await _send_temp_message(msg, f"⚠️ خطا در حذف مدیر: {e}", context)
        return

    if text == "لیست مدیران":
        try:
            current_admins = await context.bot.get_chat_administrators(chat.id)
            names = [f"• {a.user.first_name}" for a in current_admins if not a.user.is_bot]
            out = "👑 مدیران فعلی گروه:\n" + "\n".join(names) if names else "ℹ️ مدیری یافت نشد."
            await _send_temp_message(msg, out, context)
        except:
            pass


# ===== ثبت هندلر =====
def register_admin_handlers(application, group_number: int = 15):
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS, handle_admin_management),
        group=group_number,
    )
