import os
import aiohttp
import re
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




# ======================= 🌆 نمایش آب‌وهوا (هوشمند) =======================
async def show_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش وضعیت آب‌وهوا (خودکار و از پنل)"""
    message = update.message or update.callback_query.message

    # حالت ۱️⃣: از پنل دکمه‌ای
    if update.callback_query:
        query = update.callback_query
        await query.answer()

        # ✅ ضدتکرار — فقط یکبار پیام بفرستد
        if not context.user_data.get("weather_prompt_sent"):
            await query.message.reply_text("🏙 لطفاً نام شهر را بنویس تا وضعیت آب‌وهوا را بگویم 🌤")
            context.user_data["awaiting_city"] = True
            context.user_data["weather_prompt_sent"] = True
        return

    # حالت ۲️⃣: اگر در انتظار نام شهر هستیم
    if context.user_data.get("awaiting_city"):
        city = update.message.text.strip()
        context.user_data["awaiting_city"] = False
        context.user_data["weather_prompt_sent"] = False
        await process_weather_request(update, city)
        return

    # حالت ۳️⃣: اگر پیام با «آب و هوا ...» شروع شده باشد
    if update.message and update.message.text:
        text = update.message.text.strip()

        match = re.match(r"^(?:آب[\u200c\s]*و[\u200c\s]*هوا(?:ی)?)\s+(.+)$", text)
        if match:
            city = match.group(1).strip()
            await process_weather_request(update, city)
            return

        # 🌍 حالت ۴️⃣: تشخیص هوشمند شهر بدون دستور
        # اگر متن فقط شامل حروف فارسی/انگلیسی و فاصله باشد، و طولش معقول باشد (۲ تا ۲۰)
        if re.match(r"^[A-Za-zآ-ی\s]{2,20}$", text):
            city = text.strip()
            await process_weather_request(update, city)
            return

    # 🚫 اگر هیچ‌کدام نبود — پاسخ نده
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
