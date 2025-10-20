import os
import aiohttp
import re
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

# 📦 کلید API از تنظیمات محیطی (Heroku یا Local)
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# 🌍 آدرس‌های API
CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

# ======================= 🌤 دریافت اطلاعات =======================
async def get_weather(city: str):
    """دریافت وضعیت فعلی آب‌وهوا"""
    params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric", "lang": "fa"}
    async with aiohttp.ClientSession() as session:
        async with session.get(CURRENT_URL, params=params) as response:
            if response.status != 200:
                return None
            return await response.json()


async def get_forecast(city: str):
    """دریافت پیش‌بینی ۵ روز آینده (هر ۳ ساعت یک‌بار)"""
    params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric", "lang": "fa"}
    async with aiohttp.ClientSession() as session:
        async with session.get(FORECAST_URL, params=params) as response:
            if response.status != 200:
                return None
            return await response.json()


# ======================= 🌆 نمایش آب‌وهوا (چت + پنل) =======================
async def show_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message or update.callback_query.message

    # حالت ۱️⃣: از پنل
    if update.callback_query:
        query = update.callback_query
        await query.answer()

        if context.user_data.get("weather_prompt_sent"):
            return

        await query.message.reply_text("🏙 لطفاً نام شهر را بنویس تا وضعیت آب‌وهوا را بگویم 🌤")
        context.user_data["awaiting_city"] = True
        context.user_data["weather_prompt_sent"] = True
        return

    # حالت ۲️⃣: وقتی در انتظار شهر هستیم
    if context.user_data.get("awaiting_city"):
        city = update.message.text.strip()
        context.user_data["awaiting_city"] = False
        context.user_data["weather_prompt_sent"] = False
        await process_weather_request(update, city)
        return

    # حالت ۳️⃣: اگر دستور مستقیم بود (آب و هوای شهر)
    text = (update.message.text or "").strip()
    match = re.match(r"^آب[\u200c\s]*و[\u200c\s]*هوا(?:ی)?\s+(.+)$", text)
    if match:
        city = match.group(1).strip()
        await process_weather_request(update, city)
        return


# ======================= 🧩 پردازش داده و ارسال پاسخ =======================
async def process_weather_request(update: Update, city: str):
    """دریافت اطلاعات از API و نمایش وضعیت فعلی + پیش‌بینی"""
    current = await get_weather(city)
    if not current or current.get("cod") != 200:
        return await update.message.reply_text("⚠️ شهر مورد نظر پیدا نشد یا API خطا داد.")

    forecast = await get_forecast(city)

    # داده فعلی
    name = current["name"]
    country = current["sys"].get("country", "")
    temp = round(current["main"]["temp"])
    humidity = current["main"]["humidity"]
    wind = round(current["wind"]["speed"] * 3.6, 1)
    desc = current["weather"][0]["description"]
    icon = current["weather"][0]["icon"]
    dt = datetime.fromtimestamp(current["dt"])
    local_time = dt.strftime("%H:%M")

    # 🗓 پیش‌بینی ۳ روز آینده
    forecast_text = ""
    if forecast and forecast.get("list"):
        labels = ["امروز", "فردا", "پس‌فردا"]
        # هر ۸ داده تقریباً یک روزه → انتخاب سه روز
        for i, item in enumerate(forecast["list"][::8][:3]):
            day_temp = round(item["main"]["temp"])
            day_desc = item["weather"][0]["description"]
            day_icon = item["weather"][0]["icon"]
            forecast_text += f"📅 {labels[i]}: {day_desc} {get_weather_emoji(day_icon)} — {day_temp}°C\n"

    # 🧾 پیام نهایی
    text = (
        f"{get_weather_emoji(icon)} <b>وضعیت آب‌وهوا</b>\n\n"
        f"🏙 شهر: {name} {flag_emoji(country)}\n"
        f"{forecast_text}\n"
        f"💧 رطوبت: {humidity}%\n"
        f"💨 باد: {wind} km/h\n"
        f"🕒 آخرین بروزرسانی: {local_time}"
    )

    await update.message.reply_text(text, parse_mode="HTML")


# ======================= 🎨 تابع‌های کمکی =======================
def get_weather_emoji(icon):
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


def flag_emoji(country_code):
    if not country_code:
        return ""
    return "".join(chr(127397 + ord(c)) for c in country_code.upper())
