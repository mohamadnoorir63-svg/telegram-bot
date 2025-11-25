# translator_module/translator.py

from googletrans import Translator
from telegram import Update
from telegram.ext import ContextTypes

translator = Translator()

async def translate_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ترجمه متن ریپلای شده یا با دستور /translate <زبان>
    """
    msg = update.message or update.edited_message
    if not msg:
        return

    # بررسی اینکه روی پیام ریپلای شده
    if not msg.reply_to_message or not msg.reply_to_message.text:
        await msg.reply_text("⚠️ لطفاً روی یک پیام ریپلای کنید تا ترجمه شود!")
        return

    text_to_translate = msg.reply_to_message.text
    target_lang = "en"

    if context.args:
        target_lang = context.args[0]

    try:
        result = translator.translate(text_to_translate, dest=target_lang)
        reply_text = f"🌐 ترجمه ({target_lang}):\n{result.text}"
    except Exception as e:
        reply_text = f"⚠️ خطا در ترجمه: {e}"

    await msg.reply_text(reply_text)
