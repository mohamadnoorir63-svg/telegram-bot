# modules/translate_module.py
import os
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes
from typing import List, Optional
from googletrans import Translator

# 🌍 سرورهای رایگان LibreTranslate
PUBLIC_ENDPOINTS: List[str] = [
    "https://translate.argosopentech.com",
    "https://translate.mentality.rip",
    "https://translate.1g.gay",
    "https://libretranslate.de",
    "https://translate.privatix.one"
]

LANG_NAMES = {
    "fa": "فارسی",
    "en": "انگلیسی",
    "de": "آلمانی",
    "fr": "فرانسوی",
    "es": "اسپانیایی",
    "ar": "عربی",
    "tr": "ترکی",
    "ru": "روسی",
    "hi": "هندی",
    "ur": "اردو",
    "ps": "پشتو",
}

async def _detect_language(session: aiohttp.ClientSession, base: str, text: str) -> Optional[str]:
    url = f"{base.rstrip('/')}/detect"
    try:
        async with session.post(url, data={"q": text}, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                if isinstance(data, list) and len(data) > 0:
                    return data[0].get("language")
    except Exception:
        pass
    return None

async def _translate(session: aiohttp.ClientSession, base: str, text: str, src: str, tgt: str) -> Optional[str]:
    url = f"{base.rstrip('/')}/translate"
    try:
        async with session.post(url, data={"q": text, "source": src, "target": tgt, "format": "text"}, timeout=15) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("translatedText")
    except Exception:
        pass
    return None

async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    if not msg.reply_to_message or not (msg.reply_to_message.text or msg.reply_to_message.caption):
        return await msg.reply_text("برای ترجمه، روی یک پیام متنی ریپلای کن و بنویس: «ترجمه» ✅")

    text = (msg.reply_to_message.text or msg.reply_to_message.caption).strip()

    # تلاش با LibreTranslate
    async with aiohttp.ClientSession() as session:
        for base in PUBLIC_ENDPOINTS:
            try:
                src_lang = await _detect_language(session, base, text) or "auto"
                target_lang = "en" if src_lang in ["fa", "ar", "ur", "ps"] else "fa"
                translated = await _translate(session, base, text, src_lang, target_lang)
                if translated:
                    src_name = LANG_NAMES.get(src_lang, src_lang)
                    tgt_name = LANG_NAMES.get(target_lang, target_lang)
                    return await msg.reply_text(f"🈯️ ترجمه از {src_name} → {tgt_name}:\n\n{translated}")
            except Exception:
                continue

    # اگر LibreTranslate از کار افتاد → Google Translate
    try:
        translator = Translator()
        detect_lang = translator.detect(text).lang
        target_lang = "en" if detect_lang in ["fa", "ar", "ur", "ps"] else "fa"
        translated = translator.translate(text, src=detect_lang, dest=target_lang).text
        src_name = LANG_NAMES.get(detect_lang, detect_lang)
        tgt_name = LANG_NAMES.get(target_lang, target_lang)
        return await msg.reply_text(f"🌐 ترجمه از {src_name} → {tgt_name} (Google):\n\n{translated}")
    except Exception as e:
        return await msg.reply_text(f"⚠️ ترجمه انجام نشد. لطفاً بعداً دوباره امتحان کن.\n🪫 ({e})")
