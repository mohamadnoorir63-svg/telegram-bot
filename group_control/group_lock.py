# group_lock.py
import asyncio
from telegram import ChatPermissions, Update
from telegram.ext import ContextTypes


# ─────────────────────────────── قفل کردن گروه ───────────────────────────────
async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    # بررسی ادمین بودن
    member = await context.bot.get_chat_member(chat.id, user.id)
    if member.status not in ("administrator", "creator"):
        return await update.message.reply_text("🚫 فقط مدیران می‌توانند گروه را قفل کنند.")

    # قفل کامل گروه (فقط خواندن)
    perms = ChatPermissions(
        can_send_messages=False
    )

    await context.bot.set_chat_permissions(chat.id, perms)

    msg = await update.message.reply_text("🔒 گروه با موفقیت قفل شد.")
    await asyncio.sleep(5)
    await update.message.delete()
    await msg.delete()


# ─────────────────────────────── باز کردن گروه ───────────────────────────────
async def unlock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    # بررسی ادمین بودن
    member = await context.bot.get_chat_member(chat.id, user.id)
    if member.status not in ("administrator", "creator"):
        return await update.message.reply_text("🚫 فقط مدیران می‌توانند گروه را باز کنند.")

    # باز کردن گروه (اجازه ارسال پیام)
    perms = ChatPermissions(
        can_send_messages=True
    )

    await context.bot.set_chat_permissions(chat.id, perms)

    msg = await update.message.reply_text("🔓 گروه با موفقیت باز شد.")
    await asyncio.sleep(5)
    await update.message.delete()
    await msg.delete()


# ─────────────────────────────── هندلر دستورات قفل / باز کردن ───────────────────────────────
async def handle_group_lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بررسی دستور و اجرای قفل یا باز کردن گروه"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if text == "قفل گروه":
        return await lock_group(update, context)

    if text in ("باز کردن گروه", "بازکردن گروه", "باز کردن چت"):
        return await unlock_group(update, context)
