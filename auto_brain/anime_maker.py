# -*- coding: utf-8 -*-
import io
import requests
from telegram import Update
from telegram.ext import ContextTypes

API_URL = "https://api.boringapis.com/image/anime"  # 🎨 API پایدار کارتونی‌ساز

async def anime_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت عکس و تبدیل به سبک انیمه"""
    if not update.message or not update.message.photo:
        return await update.message.reply_text("📸 لطفاً یه عکس بفرست تا کارتونی‌ش کنم!")

    msg = await update.message.reply_text("🎨 در حال کارتونی کردن عکس... صبر کن 💫")

    try:
        # 📥 دریافت فایل از تلگرام
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        img_bytes = await photo_file.download_as_bytearray()

        # 🚀 ارسال به API
        files = {"image": ("photo.jpg", io.BytesIO(img_bytes), "image/jpeg")}
        response = requests.post(API_URL, files=files, timeout=90)

        # 🧩 بررسی پاسخ
        if response.status_code == 200:
            # خروجی به صورت تصویر برمی‌گرده
            out_bytes = response.content
            await update.message.reply_photo(out_bytes, caption="✨ اینم نسخه کارتونی عکست 😍")
        else:
            await update.message.reply_text(f"⚠️ خطا در پردازش عکس. کد وضعیت: {response.status_code}")

    except Exception as e:
        await update.message.reply_text(f"❌ خطا در ارتباط با سرور:\n{e}")

    finally:
        try:
            await msg.delete()
        except:
            pass
