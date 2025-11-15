from telegram import ChatPermissions, Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.effective_chat.set_permissions(
            ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            )
        )
        await update.message.reply_text("🔒 گروه *قفل* شد.\nاعضا اجازه ارسال پیام ندارند.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

async def unlock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.effective_chat.set_permissions(
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await update.message.reply_text("🔓 گروه *باز* شد.\nاعضا می‌توانند پیام ارسال کنند.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace("‌", "").lower()
    if text == "قفل گروه":
        await lock_group(update, context)
    elif text == "باز کردن گروه":
        await unlock_group(update, context)

def register_group_lock_handlers(app: Application, group: int = 0):
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text), group=group)
