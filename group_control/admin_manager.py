import os
import json
import asyncio
import re

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADMINS_FILE = os.path.join(BASE_DIR, "group_admins.json")

SUDO_IDS = [8588347189]


# ================= فایل مدیران =================

if not os.path.exists(ADMINS_FILE):
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)


def _load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ================= دسترسی =================

async def _has_access(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    user_id: int
) -> bool:

    if user_id in SUDO_IDS:
        return True

    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except Exception:
        return False


# ================= حذف خودکار پیام =================

async def _auto_delete(bot, chat_id, message_id, delay=10):
    try:
        await asyncio.sleep(delay)
        await bot.delete_message(
            chat_id=chat_id,
            message_id=message_id
        )
    except Exception:
        pass


# ================= هندلر مدیریت مدیران =================

async def handle_admin_management(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
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
    data.setdefault(chat_key, [])

    # بررسی دسترسی ربات
    try:
        me = await context.bot.get_chat_member(
            chat.id,
            context.bot.id
        )

        bot_can_promote = (
            me.status == "creator"
            or (
                me.status == "administrator"
                and getattr(me, "can_promote_members", False)
            )
        )

    except Exception:
        bot_can_promote = False

    if not bot_can_promote:
        reply = await msg.reply_text(
            "🚫 من دسترسی لازم برای مدیریت مدیران را ندارم."
        )
        asyncio.create_task(
            _auto_delete(
                context.bot,
                chat.id,
                reply.message_id
            )
        )
        return

    COMMANDS = {
        "add_admin": re.compile(r"^افزودن\s+مدیر$"),
        "remove_admin": re.compile(r"^حذف\s+مدیر$"),
        "list_admins": re.compile(r"^لیست\s+مدیران$")
    }

    cmd_type = None

    for key, pattern in COMMANDS.items():
        if pattern.fullmatch(text):
            cmd_type = key
            break

    if not cmd_type:
        return

    if not await _has_access(context, chat.id, user.id):
        reply = await msg.reply_text(
            "🚫 فقط مدیران یا سودوها می‌توانند این دستور را اجرا کنند."
        )

        asyncio.create_task(
            _auto_delete(
                context.bot,
                chat.id,
                reply.message_id
            )
        )
        return

    # =====================================================
    # افزودن مدیر
    # =====================================================

    if cmd_type == "add_admin":

        if not msg.reply_to_message:
            reply = await msg.reply_text(
                "⚠️ لطفاً روی پیام کاربر ریپلای کنید."
            )

            asyncio.create_task(
                _auto_delete(
                    context.bot,
                    chat.id,
                    reply.message_id
                )
            )
            return

        target = msg.reply_to_message.from_user

        if target.id in SUDO_IDS or target.id == context.bot.id:
            reply = await msg.reply_text(
                "⚠️ نمی‌توان این کاربر را مدیر کرد."
            )

            asyncio.create_task(
                _auto_delete(
                    context.bot,
                    chat.id,
                    reply.message_id
                )
            )
            return

        if target.id in data[chat_key]:
            reply = await msg.reply_text(
                f"⚠️ {target.first_name} قبلاً توسط ربات اضافه شده است."
            )

            asyncio.create_task(
                _auto_delete(
                    context.bot,
                    chat.id,
                    reply.message_id
                )
            )
            return

        try:
            member = await context.bot.get_chat_member(
                chat.id,
                target.id
            )

            if member.status == "creator":
                reply = await msg.reply_text(
                    "⚠️ مالک گروه از قبل بالاترین دسترسی را دارد."
                )

                asyncio.create_task(
                    _auto_delete(
                        context.bot,
                        chat.id,
                        reply.message_id
                    )
                )
                return

            await context.bot.promote_chat_member(
                chat_id=chat.id,
                user_id=target.id,
                can_change_info=True,
                can_delete_messages=True,
                can_manage_video_chats=True,
                can_restrict_members=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_manage_topics=True,
                can_promote_members=False
            )

            data[chat_key].append(target.id)
            _save_json(ADMINS_FILE, data)

            reply = await msg.reply_text(
                f"✅ {target.first_name} به عنوان مدیر اضافه شد."
            )

        except Exception as e:
            reply = await msg.reply_text(
                f"⚠️ خطا در افزودن مدیر:\n{e}"
            )

        asyncio.create_task(
            _auto_delete(
                context.bot,
                chat.id,
                reply.message_id
            )
        )

    # =====================================================
    # حذف مدیر
    # =====================================================

    elif cmd_type == "remove_admin":

        if not msg.reply_to_message:
            reply = await msg.reply_text(
                "⚠️ لطفاً روی پیام مدیر ریپلای کنید."
            )

            asyncio.create_task(
                _auto_delete(
                    context.bot,
                    chat.id,
                    reply.message_id
                )
            )
            return

        target = msg.reply_to_message.from_user

        if target.id in SUDO_IDS or target.id == context.bot.id:
            reply = await msg.reply_text(
                "🚫 نمی‌توان این کاربر را حذف کرد."
            )

            asyncio.create_task(
                _auto_delete(
                    context.bot,
                    chat.id,
                    reply.message_id
                )
            )
            return

        if target.id not in data[chat_key]:
            reply = await msg.reply_text(
                "⚠️ این کاربر توسط ربات مدیر نشده است."
            )

            asyncio.create_task(
                _auto_delete(
                    context.bot,
                    chat.id,
                    reply.message_id
                )
            )
            return

        try:
            member = await context.bot.get_chat_member(
                chat.id,
                target.id
            )

            if member.status == "creator":
                reply = await msg.reply_text(
                    "🚫 مالک گروه قابل حذف از مدیریت نیست."
                )

                asyncio.create_task(
                    _auto_delete(
                        context.bot,
                        chat.id,
                        reply.message_id
                    )
                )
                return

            if member.status != "administrator":
                reply = await msg.reply_text(
                    "⚠️ این کاربر مدیر نیست."
                )

                asyncio.create_task(
                    _auto_delete(
                        context.bot,
                        chat.id,
                        reply.message_id
                    )
                )
                return

            await context.bot.promote_chat_member(
                chat_id=chat.id,
                user_id=target.id,
                is_anonymous=False,
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

            data[chat_key].remove(target.id)
            _save_json(ADMINS_FILE, data)

            reply = await msg.reply_text(
                f"⚙️ {target.first_name} از مدیریت برکنار شد."
            )

        except Exception as e:
            reply = await msg.reply_text(
                f"⚠️ خطا در حذف مدیر:\n{e}"
            )

        asyncio.create_task(
            _auto_delete(
                context.bot,
                chat.id,
                reply.message_id
            )
        )

    # =====================================================
    # لیست مدیران
    # =====================================================

    elif cmd_type == "list_admins":

        try:
            admins = await context.bot.get_chat_administrators(
                chat.id
            )

            lines = [
                f"• {admin.user.first_name}"
                for admin in admins
                if not admin.user.is_bot
            ]

            text = (
                "👑 <b>مدیران فعلی گروه:</b>\n"
                + "\n".join(lines)
                if lines
                else "ℹ️ مدیری یافت نشد."
            )

            reply = await msg.reply_text(
                text,
                parse_mode="HTML"
            )

            asyncio.create_task(
                _auto_delete(
                    context.bot,
                    chat.id,
                    reply.message_id,
                    20
                )
            )

        except Exception as e:
            reply = await msg.reply_text(
                f"⚠️ خطا در دریافت لیست مدیران:\n{e}"
            )

            asyncio.create_task(
                _auto_delete(
                    context.bot,
                    chat.id,
                    reply.message_id
                )
            )


# ================= ثبت هندلر =================

def register_admin_handlers(
    application,
    group_number: int = 15
):
    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND
            & filters.ChatType.GROUPS,
            handle_admin_management,
        ),
        group=group_number,
    )
