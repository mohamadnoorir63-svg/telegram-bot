import requests
from telegram import Update
from telegram.ext import ContextTypes

# 🧠 API از DeepAI
API_URL = "https://api.deepai.org/api/toonify"
API_KEY = 

HEADERS = {"api-key": API_KEY}

async def anime_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        return await update.message.reply_text("📸 لطفاً یه عکس بفرست تا کارتونی‌ش کنم!")

    msg = await update.message.reply_text("🎨 در حال کارتونی کردن عکس... صبر کن 💫")

    try:
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        image_bytes = await photo_file.download_as_bytearray()

        response = requests.post(API_URL, headers=HEADERS, files={"image": image_bytes})

        if response.status_code == 200:
            result_url = response.json().get("output_url")
            if result_url:
                await update.message.reply_photo(result_url, caption="✨ کارتونی شد 😍")
            else:
                await update.message.reply_text("⚠️ خطا در دریافت خروجی از سرور.")
        else:
            await update.message.reply_text(f"⚠️ خطا در پردازش عکس (کد: {response.status_code})")

    except Exception as e:
        await update.message.reply_text(f"❌ خطا در ارتباط با سرور:\n{e}")

    await msg.delete()
