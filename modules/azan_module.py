# modules/azan_module.py
import requests
from datetime import datetime, timedelta
import jdatetime
from hijri_converter import convert
from telegram import Update
from telegram.ext import ContextTypes

AZAN_API = "https://api.aladhan.com/v1/timingsByCity"

# شهرهای فارسی → معادل لاتین + کشور (می‌تونی گسترش بدی)
CITIES = {
    "هرات": {"city": "Herat", "country": "Afghanistan"},
    "کابل": {"city": "Kabul", "country": "Afghanistan"},
    "قندهار": {"city": "Kandahar", "country": "Afghanistan"},
    "مزار": {"city": "Mazar-e-Sharif", "country": "Afghanistan"},
    "تهران": {"city": "Tehran", "country": "Iran"},
    "مشهد": {"city": "Mashhad", "country": "Iran"},
    "اصفهان": {"city": "Isfahan", "country": "Iran"},
}

__all__ = ["get_azan_time", "get_ramadan_status"]  # ← اطمینان از اکسپورت

# --------------------- 🕌 زمان اذان بر اساس شهر ---------------------
async def get_azan_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ورودی متن کاربر مثل: «اذان هرات» یا وقتی از پنل پرچم awaiting_azan_city ست شده و کاربر فقط اسم شهر رو می‌فرسته.
    """
    text = (update.message.text or "").strip()

    # اگر از پنل روی "اذان" اومده باشه، ممکنه کاربر فقط نام شهر بفرسته
    # در این صورت همین متن رو شهر فرض می‌کنیم.
    city_fa = None
    country = None
    city_en = None

    # حالت 1: جملات مثل «اذان هرات»
    for name_fa, info in CITIES.items():
        if name_fa in text:
            city_fa = name_fa
            city_en = info["city"]
            country = info["country"]
            break

    # حالت 2: وقتی از پنل گفتیم "اسم شهرت رو بنویس" و کاربر فقط «هرات» فرستاد
    if not city_fa:
        only_city = text.replace("اذان", "").strip()
        if only_city in CITIES:
            info = CITIES[only_city]
            city_fa = only_city
            city_en = info["city"]
            country = info["country"]

    if not city_fa:
        return await update.message.reply_text(
            "❗ لطفاً نام شهر را بنویس مثل:\n"
            "<code>اذان هرات</code> یا <code>اذان تهران</code>",
            parse_mode="HTML"
        )

    try:
        # method=2 (UMM Al-Qura) برای اهل سنت، method=12 برای شیعه جعفری
        sunni = requests.get(f"{AZAN_API}?city={city_en}&country={country}&method=2").json()
        shia  = requests.get(f"{AZAN_API}?city={city_en}&country={country}&method=12").json()

        if sunni.get("code") != 200 or shia.get("code") != 200:
            return await update.message.reply_text("⚠️ دریافت اوقات شرعی ناموفق بود.")

        sunni_data = sunni["data"]["timings"]
        shia_data  = shia["data"]["timings"]

        # تاریخ‌ها
        today_gregorian = sunni["data"]["date"]["gregorian"]["date"]  # DD-MM-YYYY
        today_hijri     = sunni["data"]["date"]["hijri"]["date"]      # DD-MM-YYYY (Hijri)
        today_jalali    = jdatetime.date.today().strftime("%Y/%m/%d")

        msg = (
            f"📍 <b>شهر:</b> {city_fa}\n"
            f"🏳️ <b>کشور:</b> {country}\n\n"
            f"📅 <b>میلادی:</b> {today_gregorian}\n"
            f"🗓 <b>شمسی:</b> {today_jalali}\n"
            f"🕌 <b>هجری قمری:</b> {today_hijri}\n\n"
            f"🕌 <b>اهل تسنن (سنی)</b>\n"
            f"🌅 اذان صبح: {sunni_data['Fajr']}\n"
            f"🏙 اذان ظهر: {sunni_data['Dhuhr']}\n"
            f"🌇 اذان مغرب: {sunni_data['Maghrib']}\n"
            f"🌙 نیمه شب: {sunni_data['Midnight']}\n\n"
            f"🕋 <b>اهل تشیع (شیعه)</b>\n"
            f"🌅 اذان صبح: {shia_data['Fajr']}\n"
            f"🏙 اذان ظهر: {shia_data['Dhuhr']}\n"
            f"🌇 اذان مغرب: {shia_data['Maghrib']}\n"
            f"🌙 نیمه شب: {shia_data['Midnight']}\n"
        )

        # یادآور نزدیک اذان مغرب (با منطقه زمانی کابل برای سادگی)
        try:
            maghrib_time = datetime.strptime(sunni_data["Maghrib"], "%H:%M")
            now = datetime.utcnow() + timedelta(hours=4.5)
            maghrib_today = now.replace(hour=maghrib_time.hour, minute=maghrib_time.minute, second=0, microsecond=0)
            delta_sec = (maghrib_today - now).total_seconds()
            if 0 < delta_sec <= 600:
                minutes = int(delta_sec // 60)
                msg += f"\n⏰ <b>{minutes} دقیقه تا اذان مغرب باقی مانده...</b> 🌇"
            elif delta_sec <= 0:
                msg += "\n🌇 اذان مغرب گذشته است."
        except Exception:
            pass

        await update.message.reply_text(msg, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در دریافت اوقات شرعی: {e}")

# --------------------- 🌙 وضعیت رمضان و مناسبت‌ها ---------------------
async def get_ramadan_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # کابل (UTC+4:30) برای یکسانی
        now = datetime.utcnow() + timedelta(hours=4.5)
        gregorian_date = now.strftime("%Y-%m-%d")
        jalali_date = jdatetime.date.today().strftime("%Y/%m/%d")

        # تبدیل دقیق میلادی → قمری
        hijri = convert.Gregorian(now.year, now.month, now.day).to_hijri()
        hijri_date = f"{hijri.day} {hijri.month_name('ar')} {hijri.year}"
        hijri_day = hijri.day
        month_name_en = hijri.month_name('en')
        month_name_fa = hijri.month_name('ar')

        msg = (
            f"📅 <b>تاریخ میلادی:</b> {gregorian_date}\n"
            f"🗓 <b>تاریخ شمسی:</b> {jalali_date}\n"
            f"🕌 <b>تاریخ هجری قمری:</b> {hijri_date} ({month_name_fa})\n\n"
        )

        # مناسبت‌ها
        special_days = []
        if month_name_en == "Ramadan":
            msg += "🌙 اکنون در ماه مبارک <b>رمضان</b> هستیم 🤲\n\n"
            if hijri_day in [1, 2]:
                special_days.append("🌅 آغاز ماه مبارک رمضان")
            if hijri_day == 17:
                special_days.append("⚔️ غزوه بدر و میلاد امام حسن (ع)")
            if hijri_day in [19, 21, 23]:
                special_days.append("🌌 شب‌های قدر")
            if hijri_day == 27:
                special_days.append("📖 نزول قرآن کریم")
            if hijri_day >= 29:
                special_days.append("🌕 پایان ماه رمضان و آماده‌سازی برای عید فطر")
        elif month_name_en == "Shawwal" and hijri_day in [1, 2]:
            special_days.append("🎉 عید سعید فطر")
        elif month_name_en == "Muharram" and hijri_day == 10:
            special_days.append("😢 روز عاشورا")

        msg += "\n".join(special_days) if special_days else "📿 امروز مناسبت مذهبی خاصی ندارد."
        await update.message.reply_text(msg, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بررسی ماه رمضان: {e}")
