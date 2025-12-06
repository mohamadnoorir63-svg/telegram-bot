# modules/tiktok_downloader.py
import os
import requests
import subprocess
from telegram.ext import MessageHandler, filters

def convert_to_mp3(video_path):
    mp3_path = video_path.rsplit(".", 1)[0] + ".mp3"
    command = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-ab", "192k", "-ar", "44100", "-f", "mp3", mp3_path
    ]
    subprocess.run(command)
    return mp3_path

def register_tiktok_handler(app):
    async def tiktok_downloader(update, context):
        url = update.message.text.strip()
        chat_id = update.effective_chat.id
        msg = await update.message.reply_text("⬇️ در حال پردازش رسانه ...")

        # ... کد دانلود ویدیو/عکس + ارسال همزمان صوت ...

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), tiktok_downloader))
