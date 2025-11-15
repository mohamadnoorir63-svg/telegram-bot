from telegram import ChatPermissions, Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.effective_chat.set_permissions(
            ChatPermissions(
                can_send_messages=False  # فقط پیام متنی مسدود می‌شود
            )
        )
        await update.message.reply_text("🔒 گروه قفل شد (فقط پیام متنی).")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

async def unlock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.effective_chat.set_permissions(
            ChatPermissions(
                can_send_messages=True  # پیام متنی آزاد شد، مدیا بدون تغییر
            )
        )
        await update.message.reply_text("🔓 گروه باز شد.")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace("‌", "").lower()
    if text == "قفل گروه":
        await lock_group(update, context)
    elif text == "بازکردن گروه":
        await unlock_group(update, context)

def register_group_lock_handlers(app: Application, group: int = 17):
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text), group=group)
