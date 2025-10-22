# ======================= 🕌 Azan Module — اذان شیعه و سنی با تاریخ شمسی و میلادی =======================
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes

async def get_azan_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت زمان اذان شیعه و سنی + تاریخ شمسی و میلادی + وضعیت رمضان"""
    text = update.message.text.strip().replace("اذان", "").strip()
    if not text:
        return await update.message.reply_text(
            "🕌 لطفاً نام شهر را بنویس.\nمثلاً:\nاذان هرات\nاذان تهران\nاذان مشهد",
            parse_mode="HTML"
        )

    city = text.split()[0]

    # تابع کمکی برای گرفتن زمان اذان با مذهب مشخص
    async def fetch_timings(city, madhab_name, method, school):
        url = f"https://api.aladhan.com/v1/timingsByCity?city={city}&country=&method={method}&school={school}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                data = await res.json()
                return data

    try:
        # 🎚 دریافت اطلاعات شیعه و سنی جداگانه
        shia_data = await fetch_timings(city, "شیعه", 7, 0)
        sunni_data = await fetch_timings(city, "سنی", 2, 1)
    except Exception as e:
        return await update.message.reply_text(f"⚠️ خطای اتصال به سرور اذان:\n{e}")

    # بررسی صحت داده‌ها
    if "data" not in shia_data or "data" not in sunni_data:
        return await update.message.reply_text("🚫 اطلاعات اذان برای این شهر پیدا نشد!")

    shia_timings = shia_data["data"]["timings"]
    sunni_timings = sunni_data["data"]["timings"]

    date_greg = shia_data["data"]["date"]["gregorian"]["date"]
    date_hijri = shia_data["data"]["date"]["hijri"]["date"]
    month_hijri = shia_data["data"]["date"]["hijri"]["month"]["en"]
    month_number = shia_data["data"]["date"]["hijri"]["month"]["number"]

    # تشخیص رمضان 🌙
    is_ramadan = month_number == 9
    ramadan_text = ""
    if is_ramadan:
        ramadan_day = shia_data["data"]["date"]["hijri"]["day"]
        ramadan_text = f"\n🌙 <b>ماه مبارک رمضان</b>\n📅 روز {ramadan_day} از {month_hijri}"

    # ساخت خروجی نهایی
    text_msg = (
        f"🕌 <b>اذان شهر {city}</b>\n\n"
        f"📅 میلادی: <code>{date_greg}</code>\n"
        f"📆 هجری قمری: <code>{date_hijri}</code>\n\n"
        f"🕋 <b>اهل سنت:</b>\n"
        f"🌅 صبح: {sunni_timings['Fajr']}\n"
        f"☀️ طلوع: {sunni_timings['Sunrise']}\n"
        f"🌞 ظهر: {sunni_timings['Dhuhr']}\n"
        f"🌇 عصر: {sunni_timings['Asr']}\n"
        f"🌆 مغرب: {sunni_timings['Maghrib']}\n"
        f"🌙 عشا: {sunni_timings['Isha']}\n\n"
        f"🕌 <b>شیعه (جعفری):</b>\n"
        f"🌅 صبح: {shia_timings['Fajr']}\n"
        f"☀️ طلوع: {shia_timings['Sunrise']}\n"
        f"🌞 ظهر: {shia_timings['Dhuhr']}\n"
        f"🌇 عصر: {shia_timings['Asr']}\n"
        f"🌆 مغرب: {shia_timings['Maghrib']}\n"
        f"🌙 عشا: {shia_timings['Isha']}"
    )

    if ramadan_text:
        text_msg += "\n\n" + ramadan_text

    await update.message.reply_text(text_msg, parse_mode="HTML")
