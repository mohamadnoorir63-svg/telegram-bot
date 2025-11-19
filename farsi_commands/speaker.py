from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

# وضعیت گروه‌ها
GROUP_STATUS = {}  # chat_id: {"active": True, "welcome": True, "locked": False}

def get_group_status(chat_id: int):
    if chat_id not in GROUP_STATUS:
        GROUP_STATUS[chat_id] = {"active": True, "welcome": True, "locked": False}
    return GROUP_STATUS[chat_id]

# خاموش/روشن سخنگو
async def mute_speaker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    status = get_group_status(chat_id)
    status["active"] = False
    await update.message.reply_text(
        "😴 سخنگو خاموش شد!\n(جوک و فال همچنان فعال هستند)"
    )

async def unmute_speaker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    status = get_group_status(chat_id)
    status["active"] = True
    await update.message.reply_text(
        "✅ سخنگو روشن شد!\n(همه پیام‌ها پاسخ داده می‌شوند)"
    )

# ثبت هندلرها
def register_speaker_commands(application):
    application.add_handler(
        MessageHandler(filters.Regex(r"^سخنگو_خاموش$"), mute_speaker),
        group=4
    )
    application.add_handler(
        MessageHandler(filters.Regex(r"^سخنگو_روشن$"), unmute_speaker),
        group=4
    )
