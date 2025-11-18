from telegram.ext import CommandHandler, ContextTypes
from telegram import Update
from bot import get_group_status  # مسیر واقعی به تابع get_group_status

# --- خاموش و روشن سخنگو ---

async def mute_speaker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """خاموش کردن سخنگو فقط برای این گروه"""
    chat_id = update.effective_chat.id
    status = get_group_status(chat_id)
    status["active"] = False
    await update.message.reply_text(
        "😴 سخنگو خاموش شد!\n(جوک و فال همچنان فعال هستند)"
    )

async def unmute_speaker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """روشن کردن سخنگو فقط برای این گروه"""
    chat_id = update.effective_chat.id
    status = get_group_status(chat_id)
    status["active"] = True
    await update.message.reply_text(
        "✅ سخنگو روشن شد!\n(همه پیام‌ها پاسخ داده می‌شوند)"
    )

# ---------- ثبت هندلرها ----------
def register_speaker_commands(app):
    app.add_handler(CommandHandler("خاموش_سخنگو", mute_speaker))
    app.add_handler(CommandHandler("روشن_سخنگو", unmute_speaker))
