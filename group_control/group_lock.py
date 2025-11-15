# group_control/group_lock.py
import asyncio
from telegram import Update, ChatPermissions
from telegram.ext import MessageHandler, filters, ContextTypes

# ────────────── قفل گروه (پیام متنی) ──────────────
async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    member = await context.bot.get_chat_member(chat.id, user.id)
    if member.status not in ("administrator", "creator"):
        return await update.message.reply_text("🚫 فقط مدیران می‌توانند گروه را قفل کنند.")

    # فقط ارسال پیام متنی را مسدود می‌کنیم
    perms = ChatPermissions(can_send_messages=False)
    await context.bot.set_chat_permissions(chat.id, perms)

    msg = await update.message.reply_text("🔒 گروه قفل شد (فقط پیام متنی).")
    await asyncio.sleep(4)
    await msg.delete()
    await update.message.delete()


# ────────────── باز کردن گروه ──────────────
async def unlock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    member = await context.bot.get_chat_member(chat.id, user.id)
    if member.status not in ("administrator", "creator"):
        return await update.message.reply_text("🚫 فقط مدیران می‌توانند گروه را باز کنند.")

    # اگر گروه از قبل باز است، کاری نکن
    if chat.permissions and chat.permissions.can_send_messages:
        msg = await update.message.reply_text("🔓 گروه از قبل باز است.")
        await asyncio.sleep(3)
        return await msg.delete()

    # فقط پیام متنی را آزاد کن، بقیه مدیا دست‌نخورده بماند
    perms = ChatPermissions(can_send_messages=True)
    await context.bot.set_chat_permissions(chat.id, perms)

    msg = await update.message.reply_text("🔓 گروه باز شد (فقط پیام متنی).")
    await asyncio.sleep(4)
    await msg.delete()
    await update.message.delete()


# ────────────── هندلر دستورات ──────────────
async def group_lock_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if text == "قفل گروه":
        return await lock_group(update, context)

    if text in ("باز کردن گروه", "بازکردن گروه"):
        return await unlock_group(update, context)


# ────────────── ثبت هندلر ──────────────
def register_group_lock_handlers(application, group=-10):
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, group_lock_router),
        group=group
    )
    print(f"✅ هندلرهای قفل گروه ثبت شد (فقط پیام متنی).")
