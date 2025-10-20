import os
import aiohttp
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

# 📦 کلید API از تنظیمات محیطی (Heroku یا Local)
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# 🌍 URL پایه‌ی API
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


# ======================= 🌤 دریافت اطلاعات از API =======================
async def get_weather(city: str):
    """دریافت اطلاعات آب‌وهوا از OpenWeather"""
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric",
        "lang": "fa"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL, params=params) as response:
            if response.status != 200:
                return None
            return await response.json()


# ======================= 🌆 نمایش آب‌وهوا (عمومی و از پنل) =======================
async def show_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش وضعیت آب‌وهوا هم از چت و هم از پنل"""
    city = None
    message = update.message or update.callback_query.message

    # اگر از چت مستقیم نوشتن "آب و هوا تهران"
    if update.message:
        text = update.message.text.strip()
        parts = text.split(maxsplit=3)
        if len(parts) >= 3:
            city = parts[-1]
        else:
            return await update.message.reply_text("🌆 لطفاً بنویس:\nآب و هوا [نام شهر]\nمثلاً: آب و هوا تهران")

    # اگر از پنل دکمه‌ای بود
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.reply_text("🏙 لطفاً نام شهر را بنویس تا وضعیت آب‌وهوا را بگویم 🌤")
        return

    # اگر نام شهر مشخص شد
    if city:
        data = await get_weather(city)
        if not data or data.get("cod") != 200:
            return await message.reply_text("⚠️ شهر مورد نظر پیدا نشد یا API خطا داد.")

        name = data["name"]
        country = data["sys"].get("country", "")
        temp = round(data["main"]["temp"])
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]
        desc = data["weather"][0]["description"]
        icon = data["weather"][0]["icon"]

        dt = datetime.fromtimestamp(data["dt"])
        local_time = dt.strftime("%H:%M")

        emoji = get_weather_emoji(icon)

        text = (
            f"{emoji} <b>وضعیت آب‌وهوا</b>\n\n"
            f"🏙 شهر: {name} {flag_emoji(country)}\n"
            f"🌤 وضعیت: {desc}\n"
            f"🌡 دما: {temp}°C\n"
            f"💧 رطوبت: {humidity}%\n"
            f"💨 باد: {wind} km/h\n"
            f"🕒 آخرین بروزرسانی: {local_time}"
        )

        await message.reply_text(text, parse_mode="HTML")


# ======================= 🎨 تابع‌های کمکی =======================
def get_weather_emoji(icon):
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


def flag_emoji(country_code):
    if not country_code:
        return ""
    return "".join(chr(127397 + ord(c)) for c in country_code.upper())
