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
    message = update.message or update.callback_query.message

    # حالت ۱️⃣: وقتی از پنل (دکمه) زده میشه
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.reply_text("🏙 لطفاً نام شهر را بنویس تا وضعیت آب‌وهوا را بگویم 🌤")
        context.user_data["awaiting_city"] = True
        return

    # حالت ۲️⃣: وقتی در انتظار نام شهر هستیم
    if context.user_data.get("awaiting_city"):
        city = update.message.text.strip()
        context.user_data["awaiting_city"] = False  # بعد از دریافت شهر، حالت انتظار غیرفعال شود
        await process_weather_request(update, city)
        return

    # حالت ۳️⃣: وقتی کاربر مستقیماً نوشت "آب و هوا [شهر]"
    if update.message and update.message.text:
        text = update.message.text.strip()
        if text.startswith("آب و هوا"):
            parts = text.split(maxsplit=2)
            if len(parts) < 3:
                return await update.message.reply_text(
                    "🌆 لطفاً بنویس:\nآب و هوا [نام شهر]\nمثلاً: آب و هوا تهران"
                )
            city = parts[-1]
            await process_weather_request(update, city)
            return


# ======================= 🧩 پردازش داده و ارسال نتیجه =======================
async def process_weather_request(update: Update, city: str):
    """دریافت اطلاعات از API و ساخت پیام خروجی"""
    data = await get_weather(city)
    if not data or data.get("cod") != 200:
        return await update.message.reply_text("⚠️ شهر مورد نظر پیدا نشد یا API خطا داد.")

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

    await update.message.reply_text(text, parse_mode="HTML")


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
