import os
import re
import aiohttp
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

# 🗝 نام متغیر محیطی دقیقاً باید همین باشد
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")  # در Heroku همین را ست کن
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# ========= لایه‌ی درخواست =========
async def get_weather(city: str):
    if not WEATHER_API_KEY:
        return {"_error": "NO_API_KEY"}

    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric",
        "lang": "fa",
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL, params=params) as resp:
            data = {}
            try:
                data = await resp.json()
            except Exception:
                pass
            data["_status"] = resp.status
            return data

# ========= هندلر اصلی =========
async def show_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    دو حالت:
    1) از چت: «آب و هوا هرات» یا «آب‌وهوا Bremen»
    2) از پنل: دکمه را می‌زنی → ازت شهر می‌پرسد → فقط اسم شهر را می‌فرستی
    """
    message = update.message or (update.callback_query.message if update.callback_query else None)
    if not message:
        return

    # اگر از پنل آمده‌ایم: فقط از کاربر شهر می‌خواهیم و فلگ می‌زنیم
    if update.callback_query:
        await update.callback_query.answer()
        context.user_data["awaiting_city_weather"] = True
        return await message.reply_text("🏙 لطفاً نام شهر را بنویس تا آب‌وهوا را بگویم 🌤")

    # اگر متن «آب و هوا ...» است، شهر را از همان پیام استخراج کن
    txt = (message.text or "").strip()

    # الگوهای رایج فارسی (با/بی نیم‌فاصله) و انگلیسی
    m = re.match(r"^(?:آب[\u200c\s]*و[\u200c\s]*هوا(?:ی)?|آب‌وهوا(?:ی)?|weather)\s+(.+)$", txt, flags=re.IGNORECASE)
    if m:
        city = m.group(1).strip()
        return await _process_weather(message, city)

    # اگر قبلاً از پنل فلگ زده بودیم، همین پیام را به‌عنوان نام شهر بگیر
    if context.user_data.get("awaiting_city_weather"):
        context.user_data["awaiting_city_weather"] = False
        city = txt
        if not city:
            return await message.reply_text("⚠️ نام شهر خالیه. دوباره بفرست.")
        return await _process_weather(message, city)

    # اگر نه پنل بوده نه الگوی «آب و هوا»، کاری نکن
    return

# ========= پردازش و ارسال پاسخ =========
async def _process_weather(message, city: str):
    data = await get_weather(city)

    # خطای کلید
    if isinstance(data, dict) and data.get("_error") == "NO_API_KEY":
        return await message.reply_text("⚠️ کلید API تنظیم نشده. در تنظیمات محیطی، متغیر «WEATHER_API_KEY» را ست کن.")

    # خطای API یا شهر نامعتبر
    if (not isinstance(data, dict)) or data.get("cod") != 200:
        api_msg = data.get("message") if isinstance(data, dict) else None
        hint = "مثلاً: Herat یا Herat, AF"
        return await message.reply_text(f"⚠️ شهر پیدا نشد یا API خطا داد. {('پیام: ' + api_msg) if api_msg else hint}")

    name = data["name"]
    country = data["sys"].get("country", "")
    temp = round(data["main"]["temp"])
    humidity = data["main"]["humidity"]
    # OpenWeather سرعت باد را به m/s می‌دهد؛ برای نمایش km/h ضربدر 3.6 کن
    wind_ms = data["wind"]["speed"]
    wind_kmh = round(float(wind_ms) * 3.6)
    desc = data["weather"][0]["description"]
    icon = data["weather"][0]["icon"]
    dt = datetime.fromtimestamp(data["dt"])
    local_time = dt.strftime("%H:%M")

    emoji = _get_weather_emoji(icon)
    text = (
        f"{emoji} <b>آب‌وهوا</b>\n\n"
        f"🏙 شهر: {name} { _flag_emoji(country) }\n"
        f"🌤 وضعیت: {desc}\n"
        f"🌡 دما: {temp}°C\n"
        f"💧 رطوبت: {humidity}%\n"
        f"💨 باد: {wind_kmh} km/h\n"
        f"🕒 به‌روزرسانی: {local_time}"
    )
    await message.reply_text(text, parse_mode="HTML")

# ========= کمکی‌ها =========
def _get_weather_emoji(icon: str):
    mapping = {
        "01d": "☀️", "01n": "🌙",
        "02d": "🌤", "02n": "☁️",
        "03d": "⛅️", "03n": "🌥",
        "04d": "☁️", "04n": "☁️",
        "09d": "🌧", "09n": "🌧",
        "10d": "🌦", "10n": "🌧",
        "11d": "⛈", "11n": "🌩",
        "13d": "❄️", "13n": "🌨",
        "50d": "🌫", "50n": "🌫",
    }
    return mapping.get(icon, "🌍")

def _flag_emoji(country_code: str):
    if not country_code:
        return ""
    return "".join(chr(0x1F1E6 - 65 + ord(c)) for c in country_code.upper())
