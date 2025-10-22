import requests
from datetime import datetime
import jdatetime
from telegram import Update
from telegram.ext import ContextTypes

# ===================== 🌙 تنظیمات پایه =====================
AZAN_API = "https://api.aladhan.com/v1/timingsByCity"
G_TO_H_API = "https://api.aladhan.com/v1/gToH"

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
        today_hijri = shia["data"]["date"]["hijri"]["date"]
        today_jalali = jdatetime.date.today().strftime("%Y/%m/%d")

        msg = (
            f"🌍 <b>شهر:</b> {city_fa}\n"
            f"🏳️ <b>کشور:</b> {country}\n\n"
            f"📅 <b>تاریخ میلادی:</b> {today_gregorian}\n"
            f"🗓 <b>تاریخ شمسی:</b> {today_jalali}\n"
            f"🕌 <b>تاریخ هجری:</b> {today_hijri}\n\n"
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

# ===================== 🌙 بررسی وضعیت رمضان و مناسبت‌ها =====================
async def get_ramadan_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # تاریخ امروز میلادی
        today = datetime.utcnow().strftime("%Y-%m-%d")
        response = requests.get(f"{G_TO_H_API}/{today}")
        hijri = response.json()["data"]["hijri"]

        hijri_date = hijri["date"]
        hijri_day = int(hijri["day"])
        month_name_en = hijri["month"]["en"]
        month_name_fa = hijri["month"]["ar"]
        year = hijri["year"]

        gregorian_date = response.json()["data"]["gregorian"]["date"]
        jalali_date = jdatetime.date.today().strftime("%Y/%m/%d")

        msg = (
            f"📅 <b>تاریخ میلادی:</b> {gregorian_date}\n"
            f"🗓 <b>تاریخ شمسی:</b> {jalali_date}\n"
            f"🕌 <b>تاریخ هجری:</b> {hijri_date} ({month_name_fa})\n\n"
        )

        # مناسبت‌ها
        special_days = []

        if month_name_en == "Ramadan":
            msg += "🌙 اکنون در ماه مبارک <b>رمضان</b> هستیم 🤲\n\n"
            if hijri_day in [1, 2]:
                special_days.append("🌅 آغاز ماه رمضان")
            elif hijri_day in [17]:
                special_days.append("⚔️ غزوه بدر و میلاد امام حسن (ع)")
            elif hijri_day in [19, 21, 23]:
                special_days.append("🌌 شب‌های قدر")
            elif hijri_day == 27:
                special_days.append("📖 نزول قرآن کریم")
            elif hijri_day >= 29:
                special_days.append("🌕 پایان ماه رمضان و آماده‌سازی برای عید فطر")

        elif month_name_en == "Shawwal" and hijri_day in [1, 2]:
            special_days.append("🎉 عید سعید فطر")

        elif month_name_en == "Muharram":
            if hijri_day == 10:
                special_days.append("😢 روز عاشورا")

        # اضافه کردن مناسبت‌ها
        if special_days:
            msg += "\n".join(special_days)
        else:
            msg += "📿 امروز مناسبت مذهبی خاصی ندارد."

        await update.message.reply_text(msg, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بررسی ماه رمضان: {e}")
