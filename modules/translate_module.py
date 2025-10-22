# modules/translate_module.py
import os
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes
from typing import List, Optional

# ===============================
# 🌐 سرورهای فعال LibreTranslate
# ===============================
PUBLIC_ENDPOINTS: List[str] = [
    "https://translate.argosopentech.com",
    "https://lt.vern.cc",
    "https://translate.api.skitzen.com",
    "https://translate.josstorer.com",
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

# ===============================
# 🔍 تشخیص زبان متن
# ===============================
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

# ===============================
# 🌐 ترجمه متن
# ===============================
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

# ===============================
# 🧠 تابع اصلی ترجمه
# ===============================
async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    # بررسی اینکه پیام ریپلای دارد یا نه
    if not msg.reply_to_message or not (msg.reply_to_message.text or msg.reply_to_message.caption):
        return await msg.reply_text("برای ترجمه، روی یک پیام متنی ریپلای کن و بنویس: «ترجمه» ✅")

    text = (msg.reply_to_message.text or msg.reply_to_message.caption).strip()

    endpoints = PUBLIC_ENDPOINTS
    async with aiohttp.ClientSession() as session:
        for base in endpoints:
            try:
                # تشخیص زبان
                src_lang = await _detect_language(session, base, text) or "auto"

                # مقصد خودکار: اگر فارسی بود → انگلیسی، در غیر اینصورت → فارسی
                target_lang = "en" if src_lang in ["fa", "ar", "ur", "ps"] else "fa"

                translated = await _translate(session, base, text, src_lang, target_lang)
                if translated:
                    src_name = LANG_NAMES.get(src_lang, src_lang)
                    tgt_name = LANG_NAMES.get(target_lang, target_lang)
                    return await msg.reply_text(f"🈯️ ترجمه از {src_name} → {tgt_name}:\n\n{translated}")

            except Exception:
                continue

    await msg.reply_text("⚠️ ترجمه انجام نشد. احتمالاً تمام سرورهای رایگان لحظه‌ای محدود شده‌اند. بعداً دوباره امتحان کن.")
