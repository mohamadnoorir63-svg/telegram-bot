import requests
import asyncio
from datetime import datetime, timedelta
import jdatetime
from hijri_converter import convert
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

AZAN_API = "https://api.aladhan.com/v1/timingsByCity"
G_TO_H_API = "https://api.aladhan.com/v1/gToH"

# ===================== 🌙 بررسی وضعیت رمضان و مناسبت‌ها =====================
async def get_ramadan_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # اگر از دکمه‌ی پنل فراخوانی شد
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            message = query.message
        else:
            message = update.message

        # تاریخ‌های محلی فعلی
        now = datetime.utcnow() + timedelta(hours=4.5)  # ساعت کابل
        gregorian_date = now.strftime("%Y-%m-%d")
        jalali_date = jdatetime.date.today().strftime("%Y/%m/%d")

        # تبدیل میلادی به قمری با کتابخانه دقیق‌تر
        hijri = convert.Gregorian(now.year, now.month, now.day).to_hijri()
        hijri_date = f"{hijri.day} {hijri.month_name('ar')} {hijri.year}"
        hijri_day = hijri.day
        month_name_en = hijri.month_name('en')
        month_name_fa = hijri.month_name('ar')

        # 📅 ساخت پیام
        msg = (
            f"📅 <b>تاریخ میلادی:</b> {gregorian_date}\n"
            f"🗓 <b>تاریخ شمسی:</b> {jalali_date}\n"
            f"🕌 <b>تاریخ هجری قمری:</b> {hijri_date} ({month_name_fa})\n\n"
        )

        # ✅ مناسبت‌های مذهبی
        special_days = []

        if month_name_en == "Ramadan":
            msg += "🌙 اکنون در ماه مبارک <b>رمضان</b> هستیم 🤲\n\n"
            if hijri_day in [1, 2]:
                special_days.append("🌅 آغاز ماه مبارک رمضان")
            elif hijri_day == 17:
                special_days.append("⚔️ غزوه بدر و میلاد امام حسن (ع)")
            elif hijri_day in [19, 21, 23]:
                special_days.append("🌌 شب‌های قدر")
            elif hijri_day == 27:
                special_days.append("📖 نزول قرآن کریم")
            elif hijri_day >= 29:
                special_days.append("🌕 پایان ماه رمضان و آماده‌سازی برای عید فطر")

        elif month_name_en == "Shawwal" and hijri_day in [1, 2]:
            special_days.append("🎉 عید سعید فطر")

        elif month_name_en == "Muharram" and hijri_day == 10:
            special_days.append("😢 روز عاشورا")

        msg += "\n".join(special_days) if special_days else "📿 امروز مناسبت مذهبی خاصی ندارد."

        # دکمه‌ی بازگشت به منوی اصلی
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_main")]]
        markup = InlineKeyboardMarkup(keyboard)

        await message.reply_text(msg, parse_mode="HTML", reply_markup=markup)

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بررسی ماه رمضان: {e}")
