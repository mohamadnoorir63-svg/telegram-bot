import os
import aiohttp
import re
from datetime import datetime, timedelta, timezone
from telegram import Update
from telegram.ext import ContextTypes
from khayyam import JalaliDatetime  # ✅ برای تاریخ شمسی

# 🗝 کلید API از محیط
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# 🌍 URLهای اصلی
CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

# ======================= 📡 دریافت اطلاعات =======================
async def get_weather(city: str):
    """دریافت وضعیت فعلی"""
    params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric", "lang": "fa"}
    async with aiohttp.ClientSession() as session:
        async with session.get(CURRENT_URL, params=params) as response:
            if response.status != 200:
                return None
            return await response.json()


async def get_forecast(city: str):
    """دریافت پیش‌بینی ۵ روز آینده (هر ۳ ساعت)"""
    params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric", "lang": "fa"}
    async with aiohttp.ClientSession() as session:
        async with session.get(FORECAST_URL, params=params) as response:
            if response.status != 200:
                return None
            return await response.json()


# ======================= 🌆 هندلر اصلی =======================
async def show_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message or update.callback_query.message

    # فقط از طریق دکمه پنل فعال شود
    if update.callback_query:
        await update.callback_query.answer()
        if not context.user_data.get("awaiting_city", False):
            await message.reply_text("🏙 لطفاً نام شهر را بنویس تا وضعیت آب‌وهوا را بگویم 🌤")
            context.user_data["awaiting_city"] = True
        return

    # اگر از دکمه وارد شده و هنوز منتظر شهر هستیم
    if context.user_data.get("awaiting_city"):
        city = update.message.text.strip()
        context.user_data["awaiting_city"] = False
        await process_weather(update, city)
        return

    # تشخیص خودکار پیام‌هایی مثل «هوای تهران» یا «آب و هوای مشهد»
    text = update.message.text.strip()
    pattern = r"(?i)(?:هوا|آب[\s‌]*و[\s‌]*هوا)\s*(?:ی)?\s*([\wآ-ی\s]+)?"
    match = re.search(pattern, text)
    if match:
        city = match.group(1)
        if city and len(city.strip()) > 1:
            await process_weather(update, city.strip())
            return
    return


# ======================= 🧩 پردازش نهایی =======================
async def process_weather(update: Update, city: str):
    """گرفتن داده‌های فعلی و پیش‌بینی (با پرچم، تاریخ شمسی و ساعت محلی دقیق)"""
    current = await get_weather(city)
    if not current or current.get("cod") != 200:
        return await update.message.reply_text("⚠️ شهر مورد نظر پیدا نشد یا API خطا داد.")

    forecast = await get_forecast(city)

    # 📍 اطلاعات فعلی
    name = current["name"]
    country = current["sys"].get("country", "")
    flag = flag_emoji(country)

    temp_now = round(current["main"]["temp"], 1)
    feels_like = round(current["main"]["feels_like"], 1)
    temp_min = round(current["main"]["temp_min"], 1)
    temp_max = round(current["main"]["temp_max"], 1)
    humidity = current["main"]["humidity"]
    pressure = current["main"]["pressure"]
    wind_speed = round(current["wind"]["speed"] * 3.6, 1)
    wind_deg = current["wind"].get("deg", 0)
    visibility = current.get("visibility", 0) / 1000
    desc = current["weather"][0]["description"].capitalize()
    icon = current["weather"][0]["icon"]
    emoji = get_weather_emoji(icon)

    # 🕒 زمان محلی دقیق با timezone API
    tz_offset = current.get("timezone", 0)  # به ثانیه
    utc_time = datetime.utcfromtimestamp(current["dt"])
    local_time = utc_time + timedelta(seconds=tz_offset)
    persian_date = JalaliDatetime(local_time).strftime("%A %d %B %Y")
    local_time_str = local_time.strftime("%H:%M")

    # 📅 پیش‌بینی ۳ روز آینده
    forecast_text = ""
    if forecast and forecast.get("list"):
        daily = forecast["list"][::8][:3]
        labels = ["فردا", "پس‌فردا", "سه‌روز بعد"]
        for i, entry in enumerate(daily):
            day_temp_min = round(entry["main"]["temp_min"], 1)
            day_temp_max = round(entry["main"]["temp_max"], 1)
            day_desc = entry["weather"][0]["description"].capitalize()
            day_icon = entry["weather"][0]["icon"]
            forecast_text += (
                f"◂ <b>{labels[i]}:</b>\n"
                f" ◂ دمای حداکثر: {day_temp_max}°C\n"
                f" ◂ دمای حداقل: {day_temp_min}°C\n"
                f" ◂ حالت: {day_desc} {get_weather_emoji(day_icon)}\n"
            )

    # 🧾 پیام نهایی (با استایل فارسی و پرچم)
    text = (
        f"◄ <b>وضعیت هوای {name} {flag}</b> :\n"
        f"• <b>تاریخ:</b> {persian_date}\n"
        f"• <b>ساعت:</b> {local_time_str}\n\n"
        f"<b>وضعیت دما</b>\n"
        f"◂ دمای کنونی: {temp_now}°C\n"
        f"◂ دمای احساسی: {feels_like}°C\n"
        f"◂ حداکثر دما: {temp_max}°C\n"
        f"◂ حداقل دما: {temp_min}°C\n\n"
        f"<b>وضعیت جَوی</b>\n"
        f"◂ حالت فعلی: {desc} {emoji}\n"
        f"◂ رطوبت: {humidity}%\n"
        f"◂ فشار هوا: {pressure} میلی‌بار\n"
        f"◂ سرعت باد: {wind_speed} km/h\n"
        f"◂ جهت باد: {wind_deg}°\n"
        f"◂ محدوده دید: {visibility:.1f} km\n\n"
        f"<b>وضعیت مکانی</b>\n"
        f"◂ موقعیت: {flag} {country}-{name}\n\n"
        f"<b>پیش‌بینی روزهای بعد</b>\n"
        f"{forecast_text}"
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
