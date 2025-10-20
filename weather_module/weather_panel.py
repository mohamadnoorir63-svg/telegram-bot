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

# ======================= 🌆 نمایش آب‌وهوا =======================
async def show_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش وضعیت آب‌وهوا هم از چت و هم از پنل"""
    city = None
    message = update.message or update.callback_query.message

    # اگر از چت مستقیم نوشته شده
    if update.message:
        text = update.message.text.strip()
        parts = text.split(maxsplit=3)
        # اگر نوشته "آب و هوا تهران"
        if len(parts) >= 3 and ("آب" in text and "هوا" in text):
            city = parts[-1]
        # اگر فقط شهر نوشته شده بعد از پنل
        elif getattr(context.user_data, "waiting_for_city", False):
            city = text
        # اگر فقط "آب و هوا" نوشته بدون شهر
        elif "آب" in text and "هوا" in text:
            return await message.reply_text(
                "🌆 لطفاً بنویس:\nآب و هوا [نام شهر]\nمثلاً: آب و هوا تهران"
            )
        else:
            return  # هیچ کاری نکن تا سایر ماژول‌ها پاسخ بدن

    # اگر از پنل دکمه‌ای بود
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        # فقط یک‌بار بگه، نه دوبار
        if not getattr(context.user_data, "waiting_for_city", False):
            await query.message.reply_text("🏙 لطفاً نام شهر را بنویس تا وضعیت آب‌وهوا را بگویم 🌤")
            context.user_data["waiting_for_city"] = True
        return

    # اگر شهر مشخص شد
    if city:
        data = await get_weather(city)
        context.user_data["waiting_for_city"] = False  # ریست حالت انتظار

        if not data or data.get("cod") != 200:
            return await message.reply_text("⚠️ شهر مورد نظر پیدا نشد یا API خطا داد.")

        # استخراج داده‌ها
        name = data["name"]
        country = data["sys"].get("country", "")
        temp = round(data["main"]["temp"])
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]
        desc = data["weather"][0]["description"]
        icon = data["weather"][0]["icon"]

        # زمان محلی
        dt = datetime.fromtimestamp(data["dt"])
        local_time = dt.strftime("%H:%M")

        # ایموجی‌ها
        emoji = get_weather_emoji(icon)
        flag = flag_emoji(country)

        text = (
            f"{emoji} <b>آب‌وهوا 🌤</b>\n\n"
            f"🏙 شهر: {flag} <b>{name}</b>\n"
            f"🌤 وضعیت: {desc}\n"
            f"🌡 دما: <b>{temp}°C</b>\n"
            f"💧 رطوبت: <b>{humidity}%</b>\n"
            f"💨 باد: <b>{wind} km/h</b>\n"
            f"🕒 به‌روزرسانی: <b>{local_time}</b>"
        )

        await message.reply_text(text, parse_mode="HTML")

# ======================= 🎨 تابع‌های کمکی =======================
def get_weather_emoji(icon):
    """تبدیل کد آیکون API به ایموجی"""
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
    """تبدیل کد کشور (مثل AF یا IR) به پرچم ایموجی"""
    if not country_code:
        return ""
    try:
        return "".join(chr(127397 + ord(c)) for c in country_code.upper())
    except:
        return ""
