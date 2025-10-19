# -*- coding: utf-8 -*-
import io
import requests
from telegram import Update
from telegram.ext import ContextTypes

API_URL = "https://tenapi.cn/v2/cartoon"  # 🎨 API رایگان کارتونی‌ساز

async def anime_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.photo:
        return await update.message.reply_text("📸 لطفاً یه عکس بفرست تا کارتونی‌ش کنم!")

    msg = await update.message.reply_text("🎨 در حال کارتونی کردن عکس... صبر کن 💫")

    try:
        # گرفتن عکس از تلگرام
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        img_bytes = await photo_file.download_as_bytearray()

        # فرستادن عکس به API
        files = {"file": ("image.jpg", io.BytesIO(img_bytes), "image/jpeg")}
        response = requests.post(API_URL, files=files, timeout=60)

        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200 and data.get("url"):
                await update.message.reply_photo(
                    data["url"], caption="✨ اینم نسخه کارتونی عکست 😍"
                )
            else:
                await update.message.reply_text("⚠️ خطا در پردازش عکس، لطفاً دوباره تلاش کن 🙏")
        else:
            await update.message.reply_text(f"⚠️ خطای سرور: {response.status_code}")

    except Exception as e:
        await update.message.reply_text(f"❌ خطا در پردازش تصویر:\n{e}")

    finally:
        try:
            await msg.delete()
        except:
            pass
