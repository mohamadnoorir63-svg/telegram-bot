import requests
from telegram import Update
from telegram.ext import ContextTypes
import os

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

async def instagram_downloader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    url = update.message.text.strip()

    if "instagram.com" not in url:
        return

    msg = await update.message.reply_text("📥 در حال پردازش لینک اینستاگرام...")

    try:
        api_url = "https://igram.io/api/instagram"
        response = requests.post(api_url, data={"url": url})

        data = response.json()

        if "data" not in data or len(data["data"]) == 0:
            await msg.edit_text("❌ نتوانستم لینک دانلود را پیدا کنم!")
            return

        download_link = data["data"][0]["url"]

        file_content = requests.get(download_link).content
        file_path = os.path.join(DOWNLOAD_FOLDER, "insta.mp4")

        with open(file_path, "wb") as f:
            f.write(file_content)

        await update.message.reply_video(video=open(file_path, "rb"), caption="✅ دانلود شد!")

        os.remove(file_path)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا: {e}")
