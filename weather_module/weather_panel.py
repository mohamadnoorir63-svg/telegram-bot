import os, aiohttp, re, io, imageio
from datetime import datetime
from PIL import Image, ImageDraw, ImageEnhance
from telegram import Update
from telegram.ext import ContextTypes

# 🔑 کلید API
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
GEO_URL = "https://api.openweathermap.org/geo/1.0/direct"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
TILE_BASE = "https://tile.openweathermap.org/map"


# 📍 گرفتن مختصات شهر
async def get_city_coordinates(city):
    params = {"q": city, "limit": 1, "appid": WEATHER_API_KEY}
    async with aiohttp.ClientSession() as s:
        async with s.get(GEO_URL, params=params) as r:
            if r.status != 200:
                return None
            data = await r.json()
            return data[0] if data else None


# 🌦 گرفتن داده‌های پیش‌بینی
async def get_forecast(lat, lon):
    params = {"lat": lat, "lon": lon, "appid": WEATHER_API_KEY, "units": "metric", "lang": "fa"}
    async with aiohttp.ClientSession() as s:
        async with s.get(FORECAST_URL, params=params) as r:
            return await r.json() if r.status == 200 else None


# 🎨 تبدیل دما به رنگ (گرادیان آبی تا قرمز)
def temp_to_color(temp_c):
    if temp_c <= 0:
        return (0, 100, 255)  # آبی
    elif temp_c <= 15:
        return (0, 255, 150)  # سبزآبی
    elif temp_c <= 25:
        return (255, 255, 0)  # زرد
    else:
        return (255, 80, 0)  # قرمز


# 🎥 ساخت ویدیو با گرادیان رنگی دما
async def create_heat_timelapse(lat, lon, forecast_list):
    tile_zoom = 5
    x_tile = int((lon + 180) / 360 * (2 ** tile_zoom))
    y_tile = int((1 - ((lat + 90) / 180)) * (2 ** tile_zoom))

    frames = []
    async with aiohttp.ClientSession() as s:
        for item in forecast_list[:8]:  # حدود ۲۴ ساعت
            t = round(item["main"]["temp"])
            d = item["weather"][0]["description"]
            ic = item["weather"][0]["icon"]

            # گرفتن نقشه‌ها
            temp_url = f"{TILE_BASE}/temp_new/{tile_zoom}/{x_tile}/{y_tile}.png?appid={WEATHER_API_KEY}"
            clouds_url = f"{TILE_BASE}/clouds_new/{tile_zoom}/{x_tile}/{y_tile}.png?appid={WEATHER_API_KEY}"

            async with s.get(temp_url) as t_res, s.get(clouds_url) as c_res:
                if t_res.status != 200 or c_res.status != 200:
                    continue
                temp_img = Image.open(io.BytesIO(await t_res.read())).convert("RGBA")
                clouds_img = Image.open(io.BytesIO(await c_res.read())).convert("RGBA")
                base = Image.blend(temp_img, clouds_img, alpha=0.4)

                # رنگ‌گذاری با گرادیان حرارتی
                color_overlay = Image.new("RGBA", base.size, temp_to_color(t) + (90,))
                base = Image.alpha_composite(base, color_overlay)

                # نقاشی نقطه قرمز 📍
                draw = ImageDraw.Draw(base)
                cx, cy = base.width // 2, base.height // 2
                draw.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=(255, 0, 0, 255))
                draw.text((10, 10), f"{t}°C", fill=(255, 255, 255, 255))
                draw.text((10, 25), d, fill=(255, 255, 255, 255))

                frames.append(base)

    if not frames:
        return None

    buf = io.BytesIO()
    imageio.mimsave(buf, frames, fps=2, codec="libx264", format="mp4")
    buf.seek(0)
    return buf


# 🌤 هندلر اصلی
async def show_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message or update.callback_query.message

    if update.callback_query:
        await update.callback_query.answer()
        await message.reply_text("🏙 لطفاً نام شهر را بنویس تا ویدیوی دمای رنگی بسازم 🌡🎨")
        context.user_data["awaiting_city_heat"] = True
        return

    text = (update.message.text or "").strip()
    match = re.match(r"^(?:آب[\u200c\s]*و[\u200c\s]*هوا(?:ی)?|weather(?: in)?)\s+(.+)$", text, re.IGNORECASE)
    if match:
        await process_city(update, match.group(1))
        return

    if context.user_data.get("awaiting_city_heat"):
        context.user_data["awaiting_city_heat"] = False
        await process_city(update, text)
        return


# ⚙️ پردازش داده‌ها و تولید خروجی
async def process_city(update: Update, city):
    geo = await get_city_coordinates(city)
    if not geo:
        return await update.message.reply_text("⚠️ شهر پیدا نشد یا API خطا داد.")

    lat, lon = geo["lat"], geo["lon"]
    city_name = geo["name"]
    country_code = geo.get("country", "")

    forecast = await get_forecast(lat, lon)
    if not forecast or not forecast.get("list"):
        return await update.message.reply_text("⚠️ داده‌های پیش‌بینی یافت نشد.")

    # 📝 پیش‌بینی ۳ روز آینده (خلاصه)
    labels = ["امروز", "فردا", "پس‌فردا"]
    text = f"🌡 <b>پیش‌بینی دما - {city_name} {flag_emoji(country_code)}</b>\n\n"
    for i, item in enumerate(forecast["list"][::8][:3]):
        t = round(item["main"]["temp"])
        d = item["weather"][0]["description"]
        ic = item["weather"][0]["icon"]
        text += f"📅 {labels[i]}: {d} {get_weather_emoji(ic)} — {t}°C\n"

    await update.message.reply_text(text, parse_mode="HTML")

    # 🎥 ویدیو با رنگ‌کُد دما
    buf = await create_heat_timelapse(lat, lon, forecast["list"])
    if buf:
        await update.message.reply_video(buf, caption="🌍 تغییر رنگ دمای منطقه در ۲۴ ساعت آینده 🎨🔥")
    else:
        await update.message.reply_text("⚠️ خطا در ساخت ویدیو.")


# 🧩 ابزارها
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
