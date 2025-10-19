import os
import requests
from telegram import Update
from telegram.ext import ContextTypes, filters

# 🔐 خواندن توکن از متغیرهای محیطی (هاست)
HUGGINGFACE_API_KEY = os.getenv("HF_API_KEY")
API_URL = "https://api-inference.huggingface.co/models/akhaliq/AnimeGANv2"
HEADERS = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}


# 🎨 کارتونی‌ساز خنگول
async def anime_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        return

    chat_type = update.effective_chat.type
    msg = await update.message.reply_text("🎨 در حال کارتونی کردن عکس... صبر کن 💫")

    # در گروه‌ها → فقط لینک بده به پیوی
    if chat_type in ["group", "supergroup"]:
        await msg.edit_text("✨ برای کارتونی کردن عکس‌هات لطفاً به پیوی من بیا 🌸")
        return

    # دریافت عکس
    try:
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        image_bytes = await photo_file.download_as_bytearray()

        # درخواست به API
        response = requests.post(API_URL, headers=HEADERS, data=image_bytes)

        if response.status_code == 200:
            with open("anime_photo.jpg", "wb") as f:
                f.write(response.content)
            await update.message.reply_photo("anime_photo.jpg", caption="✨ اینم نسخه کارتونی عکست 😍")
        else:
            await update.message.reply_text("⚠️ خطا در پردازش عکس، لطفاً دوباره امتحان کن 🙏")

    except Exception as e:
        await update.message.reply_text(f"❌ خطا در اتصال به سرور:\n{e}")

    await msg.delete()
