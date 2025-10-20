import os
import aiohttp
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

# 🌍 کلید API
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


# ======================= ☁️ تابع دریافت اطلاعات از API =======================
async def get_weather(city: str):
    """دریافت اطلاعات آب‌وهوا از OpenWeather API"""
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


# ======================= 🌆 نمایش وضعیت آب‌وهوا =======================
async def show_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش وضعیت آب‌وهوا برای چت و پنل"""
    city = None
    message = None

    # 🗨️ اگر از چت مستقیم بود
    if update.message:
        message = update.message
        text = message.text.strip()
        parts = text.split(maxsplit=2)
        if len(parts) >= 3:
            city = parts[-1]
        else:
            return await message.reply_text("🌤 لطفاً بنویس:\nآب و هوا [نام شهر]\nمثلاً: آب و هوا تهران")

    # 🔘 اگر از پنل فشرده شد
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.reply_text("🏙 لطفاً نام شهری که می‌خوای بدونی رو بنویس 🌦")
        context.user_data["awaiting_city"] = True
        return

    # 📩 اگر کاربر بعد از پنل شهر را ارسال کرد
    elif context.user_data.get("awaiting_city"):
        message = update.message
        city = message.text.strip()
        context.user_data["awaiting_city"] = False

    # 🚫 اگر هنوز شهری مشخص نشده
    if not city:
        return

    data = await get_weather(city)
    if not data or data.get("cod") != 200:
        return await message.reply_text("⚠️ شهر مورد نظر پیدا نشد یا API خطا داد.")

    # 🧩 استخراج داده‌ها
    name = data["name"]
    country = data["sys"].get("country", "")
    temp = round(data["main"]["temp"])
    humidity = data["main"]["humidity"]
    wind = data["wind"]["speed"]
    desc = data["weather"][0]["description"]
    icon = data["weather"][0]["icon"]

    # 🕒 زمان محلی
    dt = datetime.utcfromtimestamp(data["dt"])
    local_time = dt.strftime("%H:%M")

    emoji = get_weather_emoji(icon)
    flag = flag_emoji(country)

    text = (
        f"{emoji} <b>وضعیت آب‌وهوا</b>\n\n"
        f"🏙 شهر: {name} {flag}\n"
        f"🌤 وضعیت: {desc}\n"
        f"🌡 دما: {temp}°C\n"
        f"💧 رطوبت: {humidity}%\n"
        f"💨 باد: {wind} km/h\n"
        f"🕒 آخرین بروزرسانی: {local_time}"
    )

    await message.reply_text(text, parse_mode="HTML")


# ======================= 🎨 کمک‌کننده‌ها =======================
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
