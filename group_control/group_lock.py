# group_control/group_lock.py
import asyncio
from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes

# وضعیت قفل گروه (در حافظه)
GROUP_LOCKS = {}  # chat_id: True/False

# ────────────── فعال / غیرفعال کردن قفل ──────────────
def set_group_lock(chat_id: int, status: bool):
    GROUP_LOCKS[chat_id] = status

def is_group_locked(chat_id: int) -> bool:
    return GROUP_LOCKS.get(chat_id, False)

# ────────────── حذف پیام متنی وقتی گروه قفل است ──────────────
async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    if is_group_locked(chat_id):
        try:
            await update.message.delete()
            warn = await update.message.reply_text("🚫 گروه قفل است: ارسال پیام متنی ممنوع.")
            await asyncio.sleep(3)
            await warn.delete()
        except:
            pass

# ────────────── دستورات قفل / باز کردن گروه ──────────────
async def group_lock_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    user = update.effective_user

    member = await context.bot.get_chat_member(chat_id, user.id)
    if member.status not in ("administrator", "creator"):
        return await update.message.reply_text("🚫 فقط مدیران می‌توانند این دستور را اجرا کنند.")

    if text == "قفل گروه":
        set_group_lock(chat_id, True)
        msg = await update.message.reply_text("🔒 گروه قفل شد (فقط پیام متنی).")
        await asyncio.sleep(3)
        await msg.delete()
        await update.message.delete()

    elif text in ("باز کردن گروه", "بازکردن گروه"):
        set_group_lock(chat_id, False)
        msg = await update.message.reply_text("🔓 گروه باز شد.")
        await asyncio.sleep(3)
        await msg.delete()
        await update.message.delete()

# ────────────── ثبت هندلر ──────────────
def register_group_lock_handlers(application, group=-10):
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages),
        group=group
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, group_lock_router),
        group=group
    )
    print(f"✅ هندلرهای قفل گروه ثبت شد (متن فقط).")
