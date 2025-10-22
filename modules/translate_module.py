from telegram import Update
from telegram.ext import ContextTypes
from googletrans import Translator

translator = Translator()

# 🌍 لیست زبان‌ها
LANGS = {
    "انگلیسی": "en",
    "فارسی": "fa",
    "عربی": "ar",
    "پشتو": "ps",
    "فرانسه": "fr",
    "ترکی": "tr",
    "اردو": "ur",
    "آلمانی": "de",
    "روسی": "ru",
    "چینی": "zh-cn",
    "ژاپنی": "ja"
}

async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # بررسی ریپلای
    if not update.message.reply_to_message:
        await update.message.reply_text("🔁 لطفاً روی یک پیام ریپلای کنید و بنویسید مثلاً:\n<code>ترجمه کن به انگلیسی</code>", parse_mode="HTML")
        return

    # بررسی زبان
    target_lang = None
    for fa_name, code in LANGS.items():
        if fa_name in text or code in text.lower():
            target_lang = code
            break

    if not target_lang:
        await update.message.reply_text("❗ لطفاً زبان مقصد را مشخص کنید. مثال:\n<code>ترجمه کن به فارسی</code> یا <code>translate to en</code>", parse_mode="HTML")
        return

    # گرفتن متن پیام اصلی
    original_text = update.message.reply_to_message.text
    if not original_text:
        await update.message.reply_text("⚠️ متن قابل ترجمه‌ای پیدا نشد.")
        return

    # ترجمه
    try:
        translated = translator.translate(original_text, dest=target_lang)
        await update.message.reply_text(
            f"🌐 <b>ترجمه به {target_lang.upper()}</b>:\n\n{translated.text}",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ترجمه: {e}")
