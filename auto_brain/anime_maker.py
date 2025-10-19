# -*- coding: utf-8 -*-
import io
import requests
from telegram import Update
from telegram.ext import ContextTypes

API_URL = "https://image-to-anime.vercel.app/api"

async def anime_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت عکس و ارسال نسخه کارتونی‌شده (انیمه)"""
    if not update.message or not update.message.photo:
        return await update.message.reply_text("📸 لطفاً یه عکس بفرست تا کارتونی‌ش کنم!")

    msg = await update.message.reply_text("🎨 در حال کارتونی کردن عکس... صبر کن 💫")

    try:
        # گرفتن عکس از تلگرام
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        img_bytes = await photo_file.download_as_bytearray()

        # فرستادن به API جدید
        files = {"image": ("photo.jpg", io.BytesIO(img_bytes), "image/jpeg")}
        response = requests.post(API_URL, files=files, timeout=90)

        if response.status_code == 200:
            # خروجی کارتونی به صورت باینری (تصویر)
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
