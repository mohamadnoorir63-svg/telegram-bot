from deep_translator import GoogleTranslator

def translate_text(text: str, target_lang: str = "en") -> str:
    try:
        return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except Exception as e:
        print(f"⚠️ خطا در ترجمه: {e}")
        return text

async def translate_reply(update, context, target_lang="en"):
    msg = update.message or update.edited_message
    if not msg or not msg.text:
        return
    translated = translate_text(msg.text, target_lang)
    await context.bot.send_message(chat_id=msg.chat.id, text=translated)
