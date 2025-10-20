import os
import re
import aiohttp
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

# 🗝 کلید API از تنظیمات محیطی Heroku
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# ======================= 🌤 دریافت اطلاعات از API =======================
async def get_weather(city: str):
    """دریافت اطلاعات آب‌وهوا از OpenWeather"""
    if not WEATHER_API_KEY:
        return {"_error": "NO_API_KEY"}

    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric",
        "lang": "fa"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL, params=params) as resp:
            try:
                data = await resp.json()
            except Exception:
                data = {}
            data["_status"] = resp.status
            return data

# ======================= 🌆 نمایش آب‌وهوا =======================
async def show_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    📍 دو حالت:
    1. از چت: «آب و هوا تهران» یا «آب‌وهوا هرات»
    2. از پنل: دکمه را می‌زنی → ازت شهر می‌پرسد → فقط اسم شهر را بفرست
    """
    message = update.message or (update.callback_query.message if update.callback_query else None)
    if not message:
        return

    # جلوگیری از ارسال دوباره پیام درخواست شهر
    if context.user_data.get("weather_waiting_prompt_sent", False):
        return

    # 🌦 حالت پنل
    if update.callback_query:
        await update.callback_query.answer()
        context.user_data["awaiting_city_weather"] = True

        # فقط یک بار پیام درخواست بفرست
        if not context.user_data.get("weather_prompt_active", False):
            context.user_data["weather_prompt_active"] = True
            await message.reply_text("🏙 لطفاً نام شهر را بنویس تا وضعیت آب‌وهوا را بگویم 🌤")
            context.user_data["weather_waiting_prompt_sent"] = True
        return

    # 🌤 حالت چت مستقیم
    txt = (message.text or "").strip()

    # اگر جمله شامل "آب و هوا" بود
    match = re.match(r"^(?:آب[\u200c\s]*و[\u200c\s]*هوا(?:ی)?|آب‌وهوا(?:ی)?|weather)\s+(.+)$", txt, flags=re.IGNORECASE)
    if match:
        city = match.group(1).strip()
        context.user_data["weather_prompt_active"] = False
        return await _process_weather(message, city)

    # اگر کاربر بعد از پنل شهر را فرستاده
    if context.user_data.get("awaiting_city_weather"):
        context.user_data["awaiting_city_weather"] = False
        context.user_data["weather_prompt_active"] = False
        context.user_data["weather_waiting_prompt_sent"] = False

        city = txt
        if not city:
            return await message.reply_text("⚠️ نام شهر خالیه. دوباره بفرست.")
        return await _process_weather(message, city)

    # در غیر اینصورت، پیام را نادیده بگیر
    return

# ======================= 🧠 پردازش پاسخ =======================
async def _process_weather(message, city: str):
    data = await get_weather(city)

    # 🛑 اگر کلید API تنظیم نشده
    if isinstance(data, dict) and data.get("_error") == "NO_API_KEY":
        return await message.reply_text("⚠️ کلید API در تنظیمات محیطی تنظیم نشده!")

    # 🛑 اگر API یا شهر خطا داد
    if (not isinstance(data, dict)) or data.get("cod") != 200:
        api_msg = data.get("message") if isinstance(data, dict) else None
        hint = "مثلاً: Herat یا Tehran یا Kabul"
        return await message.reply_text(f"⚠️ شهر پیدا نشد یا API خطا داد. {('پیام: ' + api_msg) if api_msg else hint}")

    # استخراج داده‌ها
    name = data["name"]
    country = data["sys"].get("country", "")
    temp = round(data["main"]["temp"])
    humidity = data["main"]["humidity"]
    wind_ms = data["wind"]["speed"]
    wind_kmh = round(float(wind_ms) * 3.6)
    desc = data["weather"][0]["description"]
    icon = data["weather"][0]["icon"]
    dt = datetime.fromtimestamp(data["dt"])
    local_time = dt.strftime("%H:%M")

    # ایموجی و پرچم
    emoji = _get_weather_emoji(icon)
    flag = _flag_emoji(country)

    # ساخت متن نهایی
    text = (
        f"{emoji} <b>آب‌وهوا</b>\n\n"
        f"🏙 شهر: <b>{name}</b> {flag}\n"
        f"🌤 وضعیت: {desc}\n"
        f"🌡 دما: {temp}°C\n"
        f"💧 رطوبت: {humidity}%\n"
        f"💨 باد: {wind_kmh} km/h\n"
        f"🕒 آخرین بروزرسانی: {local_time}"
    )

    await message.reply_text(text, parse_mode="HTML")

# ======================= 🎨 توابع کمکی =======================
def _get_weather_emoji(icon: str):
    mapping = {
        "01d": "☀️", "01n": "🌙",
        "02d": "🌤", "02n": "🌥",
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
    try:
        return "".join(chr(0x1F1E6 - 65 + ord(c)) for c in country_code.upper())
    except:
        return ""
