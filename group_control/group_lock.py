# group_control/group_lock.py
import asyncio
from telegram import ChatPermissions, Update
from telegram.ext import MessageHandler, filters, ContextTypes

# وضعیت قفل گروه
GROUP_LOCKS = {}  # chat_id: True/False

def set_group_lock(chat_id: int, status: bool):
    GROUP_LOCKS[chat_id] = status

def is_group_locked(chat_id: int) -> bool:
    return GROUP_LOCKS.get(chat_id, False)

# ────────────── دستورات قفل / باز کردن گروه ──────────────
async def group_lock_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    user = update.effective_user

    try:
        member = await context.bot.get_chat_member(chat_id, user.id)
    except:
        return

    if member.status not in ("administrator", "creator"):
        return await update.message.reply_text("🚫 فقط مدیران می‌توانند این دستور را اجرا کنند.")

    if text == "قفل گروه":
        # فقط پیام متنی را ببند
        perms = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=False,
            can_invite_users=True,
            can_pin_messages=False
        )
        await context.bot.set_chat_permissions(chat_id, perms)
        set_group_lock(chat_id, True)
        msg = await update.message.reply_text("🔒 گروه قفل شد (فقط پیام متنی).")
        await asyncio.sleep(3)
        await msg.delete()
        await update.message.delete()
        return

    elif text in ("باز کردن گروه", "بازکردن گروه"):
        # اجازه ارسال همه پیام‌ها را بده
        perms = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=False,
            can_invite_users=True,
            can_pin_messages=False
        )
        await context.bot.set_chat_permissions(chat_id, perms)
        set_group_lock(chat_id, False)
        msg = await update.message.reply_text("🔓 گروه باز شد.")
        await asyncio.sleep(3)
        await msg.delete()
        await update.message.delete()
        return

# ────────────── ثبت هندلر ──────────────
def register_group_lock_handlers(application, group=-10):
    from telegram.ext import MessageHandler, filters
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, group_lock_router),
        group=group
    )
    print(f"✅ هندلرهای قفل گروه ثبت شد (فقط پیام متنی).")
