import requests
from datetime import datetime
import jdatetime
from telegram import Update
from telegram.ext import ContextTypes

# ===================== 🌙 تنظیمات پایه =====================
AZAN_API = "https://api.aladhan.com/v1/timingsByCity"

# شهرها و کشورها
CITIES = {
    "هرات": {"city": "Herat", "country": "Afghanistan"},
    "کابل": {"city": "Kabul", "country": "Afghanistan"},
    "قندهار": {"city": "Kandahar", "country": "Afghanistan"},
    "تهران": {"city": "Tehran", "country": "Iran"},
    "مشهد": {"city": "Mashhad", "country": "Iran"},
    "اصفهان": {"city": "Isfahan", "country": "Iran"},
}

# ===================== 🕌 دریافت زمان اذان =====================
async def get_azan_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # تشخیص شهر از متن
    for name, info in CITIES.items():
        if name in text:
            return await send_azan_info(update, info["city"], info["country"], name)

    await update.message.reply_text(
        "❗ لطفاً نام شهر را بنویس مثل:\n"
        "<code>اذان هرات</code> یا <code>اذان تهران</code>",
        parse_mode="HTML"
    )

async def send_azan_info(update, city, country, city_fa):
    try:
        # 🕋 اذان شیعه (Method 12)
        shia = requests.get(f"{AZAN_API}?city={city}&country={country}&method=12").json()
        # 🕌 اذان سنی (Method 2)
        sunni = requests.get(f"{AZAN_API}?city={city}&country={country}&method=2").json()

        shia_data = shia["data"]["timings"]
        sunni_data = sunni["data"]["timings"]

        # تاریخ‌ها
        today_gregorian = shia["data"]["date"]["gregorian"]["date"]
        today_jalali = jdatetime.date.today().strftime("%Y/%m/%d")

        msg = (
            f"🌍 <b>شهر:</b> {city_fa}\n"
            f"🏳️ <b>کشور:</b> {country}\n\n"
            f"📅 <b>تاریخ میلادی:</b> {today_gregorian}\n"
            f"🗓 <b>تاریخ شمسی:</b> {today_jalali}\n\n"
            f"🕋 <b>اهل تشیع (شیعه)</b>\n"
            f"🌅 اذان صبح: {shia_data['Fajr']}\n"
            f"🏙 اذان ظهر: {shia_data['Dhuhr']}\n"
            f"🌇 اذان مغرب: {shia_data['Maghrib']}\n"
            f"🌙 نیمه شب: {shia_data['Midnight']}\n\n"
            f"🕌 <b>اهل تسنن (سنی)</b>\n"
            f"🌅 اذان صبح: {sunni_data['Fajr']}\n"
            f"🏙 اذان ظهر: {sunni_data['Dhuhr']}\n"
            f"🌇 اذان مغرب: {sunni_data['Maghrib']}\n"
            f"🌙 نیمه شب: {sunni_data['Midnight']}\n"
        )

        await update.message.reply_text(msg, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در دریافت اوقات شرعی: {e}")

# ===================== 🌙 بررسی وضعیت رمضان =====================
async def get_ramadan_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get("https://api.aladhan.com/v1/gToH")
        hijri = response.json()["data"]["hijri"]

        hijri_date = hijri["date"]
        month_name = hijri["month"]["en"]

        msg = f"🕌 <b>تاریخ هجری:</b> {hijri_date}\n📅 <b>ماه:</b> {month_name}\n\n"

        if "Ramadan" in month_name:
            msg += "🌙 اکنون در ماه مبارک <b>رمضان</b> هستیم! 🤲"
        else:
            msg += "☀️ اکنون خارج از ماه رمضان هستیم."

        await update.message.reply_text(msg, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بررسی ماه رمضان: {e}")
