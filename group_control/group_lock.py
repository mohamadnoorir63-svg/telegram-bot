from telegram import ChatPermissions, Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

# ------------------------- قفل گروه -------------------------
async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # فقط ارسال پیام بسته می‌شود
        await update.effective_chat.set_permissions(
            ChatPermissions(
                can_send_messages=False
            )
        )
        await update.message.reply_text(
            "🔒 گروه *قفل* شد.\nاعضا اجازه ارسال پیام ندارند.",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

# ------------------------- باز کردن گروه -------------------------
async def unlock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # فقط ارسال پیام باز می‌شود
        await update.effective_chat.set_permissions(
            ChatPermissions(
                can_send_messages=True
            )
        )
        await update.message.reply_text(
            "🔓 گروه *باز* شد.\nاعضا می‌توانند پیام بفرستند.",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

# ------------------------- هندلر متن -------------------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace("‌", "").lower()

    if text in ["قفل گروه", "قفل"]:
        await lock_group(update, context)

    elif text in ["باز کردن گروه", "باز", "بازگروه"]:
        await unlock_group(update, context)

# ------------------------- ثبت هندلر -------------------------
def register_group_lock_handlers(app: Application, group: int = 17):
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text), group=group)
