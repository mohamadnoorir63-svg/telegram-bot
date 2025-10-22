# modules/translate_module.py
import asyncio
import os
from typing import Optional, Tuple, List
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes

# می‌تونی URL اختصاصی بذاری (اختیاری). اگه خالی باشه از لیست عمومی استفاده می‌کنیم.
LIBRE_URL_ENV = os.getenv("LIBRETRANSLATE_URL", "").strip()
PUBLIC_ENDPOINTS: List[str] = [
    # ترتیب تست؛ اول سریع‌تر/پایدارتر
    "https://translate.astian.org",
    "https://libretranslate.com",
]

LANG_NAMES = {
    "fa": "فارسی",
    "en": "انگلیسی",
    "ar": "عربی",
    "tr": "ترکی",
    "ru": "روسی",
    "de": "آلمانی",
    "fr": "فرانسوی",
    "es": "اسپانیایی",
    "hi": "هندی",
    "ur": "اردو",
    "ps": "پشتو",
}

def _lang_name(code: str) -> str:
    return LANG_NAMES.get(code, code)

async def _detect(session: aiohttp.ClientSession, base: str, text: str) -> Optional[str]:
    url = f"{base.rstrip('/')}/detect"
    try:
        async with session.post(url, data={"q": text}, timeout=15) as r:
            if r.status == 200:
                data = await r.json()
                # پاسخ معمولاً لیستی از کاندیدهاست: [{"language":"fa","confidence":...}, ...]
                if isinstance(data, list) and data:
                    return data[0].get("language")
    except Exception:
        pass
    return None

async def _translate(session: aiohttp.ClientSession, base: str, text: str, src: str, tgt: str, api_key: Optional[str]) -> Optional[str]:
    url = f"{base.rstrip('/')}/translate"
    payload = {"q": text, "source": src, "target": tgt, "format": "text"}
    if api_key:
        payload["api_key"] = api_key
    try:
        async with session.post(url, data=payload, timeout=20) as r:
            if r.status == 200:
                data = await r.json()
                # {"translatedText": "..."}
                return data.get("translatedText")
    except Exception:
        pass
    return None

def _choose_endpoints() -> List[str]:
    if LIBRE_URL_ENV:
        return [LIBRE_URL_ENV] + PUBLIC_ENDPOINTS
    return PUBLIC_ENDPOINTS

def _parse_target_arg(text: str) -> Optional[str]:
    """
    پترن‌های قابل قبول:
      - 'ترجمه en'  یا  'ترجمه به en'
      - '/translate fa'
      - 'ترجمه انگلیسی' (چند مورد پرکاربرد نگاشت می‌کنیم)
    """
    t = text.strip().lower().replace("به ", " ").split()
    # مثال: ["ترجمه","en"]
    if len(t) >= 2:
        maybe = t[1]
        map_words = {
            "فارسی": "fa", "انگلیسی": "en", "عربی": "ar", "ترکی": "tr",
            "روسی": "ru", "آلمانی": "de", "فرانسوی": "fr", "اسپانیایی": "es",
            "هندی":"hi","اردو":"ur","پشتو":"ps"
        }
        return map_words.get(maybe, maybe)  # اگر کد بود همان، اگر کلمه بود نگاشت
    return None

async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    استفاده:
      ▸ روی یک پیام ریپلای کن و بنویس:
        «ترجمه»  → خودکار: اگر متن فارسی بود → انگلیسی؛ در غیر اینصورت → فارسی
        «ترجمه en» یا «ترجمه به en»
        «/translate fa»
        «ترجمه انگلیسی / ترجمه فارسی / ...»
    """
    msg = update.effective_message
    if not msg.reply_to_message or not (msg.reply_to_message.text or msg.reply_to_message.caption):
        return await msg.reply_text("برای ترجمه، روی یک پیام متنی ریپلای کن و بنویس: «ترجمه» یا «ترجمه en»")

    original = (msg.reply_to_message.text or msg.reply_to_message.caption).strip()
    if not original:
        return await msg.reply_text("این پیام متنی ندارد.")

    # هدف موردنظر کاربر (اختیاری)
    user_text = msg.text or msg.caption or ""
    user_text = user_text.strip()

    explicit_target = _parse_target_arg(user_text)  # مثلا "en"
    api_key = os.getenv("LIBRETRANSLATE_API_KEY", "").strip() or None

    endpoints = _choose_endpoints()
    errors = []

    async with aiohttp.ClientSession() as session:
        for base in endpoints:
            try:
                # تشخیص زبان
                src = await _detect(session, base, original) or "auto"

                # اگر کاربر مقصد را مشخص نکرد:
                if not explicit_target:
                    # منطق ساده: اگر منبع فارسی/عربی/اردو/پشتو بود → انگلیسی؛ در غیر این صورت → فارسی
                    rtl_like = {"fa", "ar", "ur", "ps"}
                    target = "en" if src in rtl_like else "fa"
                else:
                    target = explicit_target

                # اگر src و target یکسان شدند، مقصد را برعکس می‌کنیم تا خروجی داشته باشیم
                if src == target:
                    target = "fa" if target != "fa" else "en"

                translated = await _translate(session, base, original, src, target, api_key)
                if translated:
                    await msg.reply_text(
                        f"🈯️ ترجمه ({_lang_name(src)} → {_lang_name(target)}):\n\n{translated}"
                    )
                    return
                else:
                    errors.append(f"{base}: no result")
            except Exception as e:
                errors.append(f"{base}: {e}")

    await msg.reply_text(
        "⚠️ ترجمه انجام نشد. ممکنه سرویس رایگان لحظه‌ای محدود شده باشه. کمی بعد دوباره امتحان کن."
    )
