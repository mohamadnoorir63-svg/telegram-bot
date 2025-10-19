import io
import os
import requests
from telegram import Update
from telegram.ext import ContextTypes

# 🔐 گرفتن API Key از متغیر محیطی (که در Heroku گذاشتی)
API_KEY = os.getenv("HF_API_KEY")
API_URL = "https://api-inference.huggingface.co/models/akhaliq/AnimeGANv2"

HEADERS = {"Authorization": f"Bearer {API_KEY}"}

async def anime_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.photo:
        return await update.message.reply_text("📸 لطفاً یه عکس بفرست تا کارتونی‌ش کنم!")

    msg = await update.message.reply_text("🎨 در حال کارتونی کردن عکس... لطفاً صبر کن 💫")

    try:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        image_bytes = await file.download_as_bytearray()

        response = requests.post(API_URL, headers=HEADERS, data=image_bytes, timeout=120)

        if response.status_code == 200:
            await update.message.reply_photo(io.BytesIO(response.content), caption="✨ اینم نسخه کارتونی عکست 😍")
        else:
            await update.message.reply_text(f"⚠️ خطا در پردازش عکس (کد: {response.status_code})")

    except Exception as e:
        await update.message.reply_text(f"❌ خطا در ارتباط با سرور:\n{e}")

    finally:
        try:
            await msg.delete()
        except:
            pass
