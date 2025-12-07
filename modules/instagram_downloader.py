import re
import requests
from telegram import Update
from telegram.ext import ContextTypes

URL_RE = re.compile(r"(https?://[^\s]+)")

API_URL = "https://instagram-downloader-api.vercel.app/?url={}"

async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    match = URL_RE.search(text)

    if not match:
        return

    url = match.group(1)

    if "instagram.com" not in url:
        return

    msg = await update.message.reply_text("📥 در حال بررسی لینک اینستاگرام...")

    try:
        r = requests.get(API_URL.format(url), timeout=15)
        data = r.json()

        # آیا لینک دانلود ویدیو وجود دارد؟
        if "download_url" in data:
            video_url = data["download_url"]

            await msg.edit_text("⬇ در حال دانلود ویدیو...")

            file = requests.get(video_url, timeout=15)

            await update.message.reply_video(
                video=file.content,
                caption="📥 ویدیو با موفقیت دانلود شد!"
            )

            await msg.delete()
            return

        else:
            await msg.edit_text("❌ فایل ویدیو پیدا نشد! شاید پست خصوصی است.")
            return

    except Exception as e:
        await msg.edit_text("❌ متاسفانه نتوانستم این لینک را دانلود کنم.\n🔁 دوباره تلاش کن!")
