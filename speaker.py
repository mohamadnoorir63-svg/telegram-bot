from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

# ======================= خاموش و روشن سخنگو =======================
async def mute_speaker(update: Update, context: ContextTypes.DEFAULT_TYPE, get_group_status):
    chat_id = update.effective_chat.id
    status = get_group_status(chat_id)
    status["active"] = False
    await update.message.reply_text("😴 سخنگو خاموش شد!\n(جوک و فال همچنان فعال هستند)")

async def unmute_speaker(update: Update, context: ContextTypes.DEFAULT_TYPE, get_group_status):
    chat_id = update.effective_chat.id
    status = get_group_status(chat_id)
    status["active"] = True
    await update.message.reply_text("✅ سخنگو روشن شد!\n(همه پیام‌ها پاسخ داده می‌شوند)")

# تابع ثبت هندلرهای فارسی داخل application
def register_speaker_commands(application, get_group_status):
    application.add_handler(
        MessageHandler(
            filters.Regex(r"^سخنگو_خاموش$"),
            lambda update, context: mute_speaker(update, context, get_group_status)
        ),
        group=4
    )
    application.add_handler(
        MessageHandler(
            filters.Regex(r"^سخنگو_روشن$"),
            lambda update, context: unmute_speaker(update, context, get_group_status)
        ),
        group=4
    )
