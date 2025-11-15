# group_control/group_lock.py

import asyncio
from telegram import ChatPermissions, Update
from telegram.ext import MessageHandler, filters, ContextTypes


# ─────────────────────────────── قفل کردن گروه ───────────────────────────────
async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    member = await context.bot.get_chat_member(chat.id, user.id)
    if member.status not in ("administrator", "creator"):
        return await update.message.reply_text("🚫 فقط مدیران می‌توانند گروه را قفل کنند.")

    perms = ChatPermissions(can_send_messages=False)
    await context.bot.set_chat_permissions(chat.id, perms)

    msg = await update.message.reply_text("🔒 گروه قفل شد.")
    await asyncio.sleep(4)
    await msg.delete()
    await update.message.delete()


# ─────────────────────────────── باز کردن گروه ───────────────────────────────
async def unlock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    member = await context.bot.get_chat_member(chat.id, user.id)
    if member.status not in ("administrator", "creator"):
        return await update.message.reply_text("🚫 فقط مدیران می‌توانند گروه را باز کنند.")

    perms = ChatPermissions(can_send_messages=True)
    await context.bot.set_chat_permissions(chat.id, perms)

    msg = await update.message.reply_text("🔓 گروه باز شد.")
    await asyncio.sleep(4)
    await msg.delete()
    await update.message.delete()


# ─────────────────────────────── مدیریت دستورها ───────────────────────────────
async def group_lock_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """این تابع دستورات قفل / باز کردن را مدیریت می‌کند."""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if text == "قفل گروه":
        return await lock_group(update, context)

    if text in ("باز کردن گروه", "بازکردن گروه", "باز کردن چت"):
        return await unlock_group(update, context)


# ─────────────────────────────── ثبت هندلر در Bot.py ───────────────────────────────
def register_group_lock_handlers(application, group=-10):
    """
    ثبت هندلرهای قفل گروه با شماره گروه دلخواه
    """
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, group_lock_router),
        group=group
    )

    print(f"✅ هندلرهای قفل گروه ثبت شد. (group = {group})")
