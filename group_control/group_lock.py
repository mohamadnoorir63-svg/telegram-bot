from telegram import ChatPermissions, Update
from telegram.ext import CommandHandler, Application, ContextTypes  # <--- اضافه کردن Application

# قفل کردن گروه
async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat.type.endswith("group"):
        return await update.message.reply_text("این دستور فقط در گروه کار می‌کند.")
    try:
        await update.effective_chat.set_permissions(
            ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            )
        )
        await update.message.reply_text("🔒 گروه *قفل* شد.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

# باز کردن گروه
async def unlock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat.type.endswith("group"):
        return await update.message.reply_text("این دستور فقط در گروه کار می‌کند.")
    try:
        await update.effective_chat.set_permissions(
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await update.message.reply_text("🔓 گروه *باز* شد.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

# ثبت هندلرها
def register_handlers(app: Application):
    app.add_handler(CommandHandler("قفل_گروه", lock_group))
    app.add_handler(CommandHandler("بازکردن_گروه", unlock_group))
