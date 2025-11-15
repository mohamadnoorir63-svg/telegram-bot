# group_control/group_lock.py
import asyncio
from telegram import ChatPermissions, Update
from telegram.ext import MessageHandler, filters, ContextTypes

# ────────────── وضعیت قفل گروه (در حافظه) ──────────────
GROUP_LOCKS = {}  # chat_id: True/False

def set_group_lock(chat_id: int, status: bool):
    GROUP_LOCKS[chat_id] = status

def is_group_locked(chat_id: int) -> bool:
    return GROUP_LOCKS.get(chat_id, False)

# ────────────── مدیریت دستورات قفل / باز کردن ──────────────
async def group_lock_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    user = update.effective_user
    text = update.message.text.strip()

    # فقط مدیر و سازنده می‌توانند قفل/باز کنند
    member = await context.bot.get_chat_member(chat_id, user.id)
    if member.status not in ("administrator", "creator"):
        return await update.message.reply_text("🚫 فقط مدیران می‌توانند این دستور را اجرا کنند.")

    if text == "قفل گروه":
        set_group_lock(chat_id, True)
        # فقط متن بسته، مدیا باز
        perms = ChatPermissions(
            can_send_messages=False,  # متن بسته
            can_send_media_messages=True,  # مدیا باز
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=False,
            can_invite_users=True,
            can_pin_messages=False
        )
        await context.bot.set_chat_permissions(chat_id, perms)
        msg = await update.message.reply_text("🔒 گروه قفل شد (فقط پیام متنی بسته شد).")
        await asyncio.sleep(3)
        await msg.delete()
        await update.message.delete()

    elif text in ("باز کردن گروه", "بازکردن گروه"):
        set_group_lock(chat_id, False)
        # همه چیز باز
        perms = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=True,
            can_invite_users=True,
            can_pin_messages=True
        )
        await context.bot.set_chat_permissions(chat_id, perms)
        msg = await update.message.reply_text("🔓 گروه باز شد.")
        await asyncio.sleep(3)
        await msg.delete()
        await update.message.delete()

# ────────────── ثبت هندلر ──────────────
def register_group_lock_handlers(application, group=-10):
    """
    ثبت هندلرهای قفل گروه
    استفاده: register_group_lock_handlers(application)
    """
    handler = MessageHandler(filters.TEXT & ~filters.COMMAND, group_lock_router)
    application.add_handler(handler, group=group)
    print(f"✅ هندلرهای قفل گروه ثبت شد (متن فقط).")
