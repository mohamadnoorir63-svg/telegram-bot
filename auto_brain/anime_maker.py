import os
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes

API_URL = "https://api-inference.huggingface.co/models/akhaliq/AnimeGANv2"
API_KEY = os.getenv("HF_API_KEY")

async def anime_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.photo:
        return await update.message.reply_text("📸 لطفاً یه عکس بفرست تا کارتونی‌ش کنم!")

    msg = await update.message.reply_text("🎨 در حال کارتونی کردن عکس...")

    try:
        photo = update.message.photo[-1]
        tg_file = await photo.get_file()
        img_bytes = await tg_file.download_as_bytearray()

        headers = {"Authorization": f"Bearer {API_KEY}"}

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, data=img_bytes) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    with open("anime_out.jpg", "wb") as f:
                        f.write(data)
                    await update.message.reply_photo("anime_out.jpg", caption="✨ نسخه کارتونی آماده شد 😍")
                else:
                    await update.message.reply_text(f"⚠️ خطا در پردازش عکس (کد {resp.status})")

    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

    try:
        await msg.delete()
    except:
        pass
