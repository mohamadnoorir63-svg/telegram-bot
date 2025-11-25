from deep_translator import GoogleTranslator
from telegram.ext import CommandHandler

# تابع داخلی برای ترجمه متن
def translate_reply(text: str, target_lang="en"):
    try:
        return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except Exception as e:
        return f"⚠️ خطا در ترجمه: {e}"

# تابعی که هندلر رو به Application اضافه می‌کنه
def register_translate_handler(app, target_lang="en"):
    async def translate_command(update, context):
        text_to_translate = " ".join(context.args)
        if not text_to_translate:
            await update.message.reply_text("⚠️ لطفا متنی برای ترجمه وارد کنید!")
            return
        translated_text = translate_reply(text_to_translate, target_lang=target_lang)
        await update.message.reply_text(translated_text)

    app.add_handler(CommandHandler("ترجمه", translate_command))
