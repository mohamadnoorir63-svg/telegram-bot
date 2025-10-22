# ======================= 🕌 Azan Module — زمان اذان شیعه و سنی =======================
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes

async def get_azan_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت زمان اذان با API برای شهر و مذهب"""
    text = update.message.text.strip().replace("اذان", "").strip()
    if not text:
        return await update.message.reply_text(
            "🕌 لطفاً نام شهر و مذهب را بنویس.\nمثلاً:\n"
            "اذان مشهد شیعه\nاذان کابل سنی\nاذان تهران",
            parse_mode="HTML"
        )

    parts = text.split()
    city = parts[0]
    madhab = "sunni"
    if len(parts) > 1 and parts[1] in ["شیعه", "جعفری"]:
        madhab = "shia"

    # تنظیمات بر اساس مذهب
    method = 7 if madhab == "shia" else 2
    school = 0 if madhab == "shia" else 1

    url = f"https://api.aladhan.com/v1/timingsByCity?city={city}&country=&method={method}&school={school}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                if res.status != 200:
                    return await update.message.reply_text("⚠️ خطا در دریافت داده از سرور اذان!")
                data = await res.json()
    except Exception as e:
        return await update.message.reply_text(f"⚠️ خطای اتصال: {e}")

    if "data" not in data:
        return await update.message.reply_text("🚫 اطلاعات اذان برای این شهر یافت نشد!")

    timings = data["data"]["timings"]
    date = data["data"]["date"]["readable"]

    result = (
        f"🕌 <b>زمان اذان در شهر {city}</b>\n"
        f"📅 تاریخ: <code>{date}</code>\n\n"
        f"🌅 اذان صبح: <b>{timings['Fajr']}</b>\n"
        f"☀️ طلوع آفتاب: <b>{timings['Sunrise']}</b>\n"
        f"🌞 اذان ظهر: <b>{timings['Dhuhr']}</b>\n"
        f"🌇 اذان عصر: <b>{timings['Asr']}</b>\n"
        f"🌆 اذان مغرب: <b>{timings['Maghrib']}</b>\n"
        f"🌙 اذان عشا: <b>{timings['Isha']}</b>\n\n"
        f"🕋 مذهب: {'شیعه (جعفری)' if madhab=='shia' else 'اهل سنت'}"
    )

    await update.message.reply_text(result, parse_mode="HTML")
