# utils/safe_send.py
from telegram import Update
from telegram.ext import ContextTypes

async def safe_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, reply_to: bool = True):
    msg = update.message or update.edited_message
    chat = update.effective_chat
    if not msg or not chat:
        print("⚠️ پیام یا چت موجود نیست، ارسال رد شد.")
        return

    reply_id = msg.message_id if reply_to else None
    try:
        await context.bot.send_message(
            chat_id=chat.id,
            text=text,
            reply_to_message_id=reply_id,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"⚠️ خطا در ارسال پیام: {e}")


async def handle_group_reply_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.edited_message
    chat = update.effective_chat
    if not msg or not chat:
        return False

    if chat.type not in ["group", "supergroup"]:
        return False

    chat_id = chat.id
    if is_group_reply_enabled(chat_id):
        text = (msg.text or msg.caption or "").strip()
        if not text:
            return False

        if not msg.reply_to_message or not msg.reply_to_message.from_user:
            return True

        if msg.reply_to_message.from_user.id != context.bot.id:
            return True

    return False
