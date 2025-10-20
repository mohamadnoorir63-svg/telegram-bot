import os
import aiohttp
import re
import io
from PIL import Image, ImageDraw
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

# 🗝 کلید API
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# 🌍 API URLs
CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
GEO_URL = "https://api.openweathermap.org/geo/1.0/direct"

# 🛰 لایه‌های ماهواره‌ای
TILE_BASE = "https://tile.openweathermap.org/map"
LAYER_TEMP = "temp_new"
LAYER_CLOUDS = "clouds_new"


# ======================= 📍 مختصات دقیق شهر =======================
async def get_city_coordinates(city_text: str):
    """استخراج مختصات دقیق شهر (با تشخیص کشور)"""
    if not WEATHER_API_KEY:
        return None

    parts = city_text.split()
    if len(parts) >= 2:
        city = " ".join(parts[:-1])
        country = parts[-1]
    else:
        city = city_text
        country = None

    params = {"q": f"{city},{country}" if country else city, "limit": 1, "appid": WEATHER_API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(GEO_URL, params=params) as response:
            if response.status != 200:
                return None
            data = await response.json()
            return data[0] if data else None


# ======================= 🌤 داده‌های هواشناسی =======================
async def get_weather(lat: float, lon: float):
    params = {"lat": lat, "lon": lon, "appid": WEATHER_API_KEY, "units": "metric", "lang": "fa"}
    async with aiohttp.ClientSession() as session:
        async with session.get(CURRENT_URL, params=params) as response:
            if response.status != 200:
                return None
            return await response.json()


async def get_forecast(lat: float, lon: float):
    params = {"lat": lat, "lon": lon, "appid": WEATHER_API_KEY, "units": "metric", "lang": "fa"}
    async with aiohttp.ClientSession() as session:
        async with session.get(FORECAST_URL, params=params) as response:
            if response.status != 200:
                return None
            return await response.json()


# ======================= 🌆 هندلر اصلی =======================
async def show_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message or update.callback_query.message

    if update.callback_query:
        await update.callback_query.answer()
        if context.user_data.get("weather_prompt_sent"):
            return
        await message.reply_text("🏙 لطفاً نام شهر را بنویس تا وضعیت آب‌وهوا را بگویم 🌤")
        context.user_data["awaiting_city"] = True
        context.user_data["weather_prompt_sent"] = True
        return

    if context.user_data.get("awaiting_city"):
        city = update.message.text.strip()
        context.user_data["awaiting_city"] = False
        context.user_data["weather_prompt_sent"] = False
        await process_weather(update, city)
        return

    text = (update.message.text or "").strip()
    match = re.match(r"^(?:آب[\u200c\s]*و[\u200c\s]*هوا(?:ی)?|weather(?: in)?)\s+(.+)$", text, flags=re.IGNORECASE)
    if match:
        await process_weather(update, match.group(1).strip())
        return

    if re.match(r"^[A-Za-zآ-ی\s]{2,40}$", text):
        await process_weather(update, text)
        return


# ======================= 🧩 پردازش و ارسال =======================
async def process_weather(update: Update, city_text: str):
    geo = await get_city_coordinates(city_text)
    if not geo:
        return await update.message.reply_text("⚠️ شهر پیدا نشد یا API خطا داد.")

    lat, lon = geo["lat"], geo["lon"]
    city_name = geo["name"]
    country_code = geo.get("country", "")

    current = await get_weather(lat, lon)
    forecast = await get_forecast(lat, lon)
    if not current or current.get("cod") != 200:
        return await update.message.reply_text("⚠️ خطا در دریافت داده‌های آب‌وهوا.")

    # 📊 اطلاعات فعلی
    temp = round(current["main"]["temp"])
    humidity = current["main"]["humidity"]
    wind = round(current["wind"]["speed"] * 3.6, 1)
    desc = current["weather"][0]["description"]
    icon = current["weather"][0]["icon"]
    dt = datetime.fromtimestamp(current["dt"])
    local_time = dt.strftime("%H:%M")

    # 📅 پیش‌بینی
    forecast_text = ""
    if forecast and forecast.get("list"):
        labels = ["امروز", "فردا", "پس‌فردا"]
        for i, item in enumerate(forecast["list"][::8][:3]):
            day_temp = round(item["main"]["temp"])
            day_desc = item["weather"][0]["description"]
            day_icon = item["weather"][0]["icon"]
            forecast_text += f"📅 {labels[i]}: {day_desc} {get_weather_emoji(day_icon)} — {day_temp}°C\n"

    emoji = get_weather_emoji(icon)
    text = (
        f"{emoji} <b>آب‌وهوا</b>\n\n"
        f"🏙 شهر: {city_name} {flag_emoji(country_code)}\n"
        f"{forecast_text}\n"
        f"🌤 وضعیت فعلی: {desc}\n"
        f"🌡 دما: {temp}°C\n"
        f"💧 رطوبت: {humidity}%\n"
        f"💨 باد: {wind} km/h\n"
        f"🕒 بروزرسانی: {local_time}"
    )

    await update.message.reply_text(text, parse_mode="HTML")

    # 📍 ارسال موقعیت
    try:
        await update.message.reply_location(latitude=lat, longitude=lon)
    except Exception:
        pass

    # 🛰 نقشه ترکیبی با علامت شهر
    tile_zoom = 5
    x_tile = int((lon + 180) / 360 * (2 ** tile_zoom))
    y_tile = int((1 - ((lat + 90) / 180)) * (2 ** tile_zoom))

    temp_url = f"{TILE_BASE}/{LAYER_TEMP}/{tile_zoom}/{x_tile}/{y_tile}.png?appid={WEATHER_API_KEY}"
    cloud_url = f"{TILE_BASE}/{LAYER_CLOUDS}/{tile_zoom}/{x_tile}/{y_tile}.png?appid={WEATHER_API_KEY}"

    async with aiohttp.ClientSession() as session:
        async with session.get(temp_url) as t_res, session.get(cloud_url) as c_res:
            if t_res.status == 200 and c_res.status == 200:
                temp_img = Image.open(io.BytesIO(await t_res.read())).convert("RGBA")
                clouds_img = Image.open(io.BytesIO(await c_res.read())).convert("RGBA")

                # ترکیب شفافیت ابرها روی نقشه دما
                combined = Image.blend(temp_img, clouds_img, alpha=0.45)

                # 🟥 رسم دایره قرمز در مرکز نقشه (نشانه شهر)
                draw = ImageDraw.Draw(combined)
                w, h = combined.size
                cx, cy = w // 2, h // 2
                r = 6
                draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 0, 0, 255))

                # ارسال به کاربر
                buf = io.BytesIO()
                combined.save(buf, format="PNG")
                buf.seek(0)
                await update.message.reply_photo(buf, caption="🌍 نقشه ترکیبی دما و ابرها + موقعیت شهر 📍")
            else:
                await update.message.reply_text("⚠️ دریافت نقشه ماهواره‌ای با خطا مواجه شد.")


# ======================= 🎨 کمکی‌ها =======================
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
