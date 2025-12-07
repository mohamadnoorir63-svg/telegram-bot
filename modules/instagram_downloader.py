import re
import requests
from telegram import Update
from telegram.ext import ContextTypes

URL_RE = re.compile(r"(https?://[^\s]+)")

API_LIST = [
    "https://api.sssinstagram.com/st-tik/instagram?url={}",   # بسیار پایدار
    "https://saveig.app/api/ajax?url={}"                       # جایگزین
]

async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    match = URL_RE.search(text)

    if not match:
        return

    url = match.group(1)
    if "instagram.com" not in url:
        return

    msg = await update.message.reply_text("📥 در حال بررسی لینک اینستاگرام...")

    for api in API_LIST:
        try:
            api_url = api.format(url)
            r = requests.get(api_url, timeout=12)

            if r.status_code != 200:
                continue

            # استخراج لینک MP4
            mp4 = re.findall(r"https?://[^\"'\s]+\.mp4", r.text)

            if mp4:
                download_url = mp4[0]

                await msg.edit_text("⬇ در حال دانلود ویدیو...")

                video = requests.get(download_url, timeout=30)

                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=video.content,
                    caption="📥 ویدیو با موفقیت دانلود شد!"
                )

                await msg.delete()
                return

        except Exception as e:
            continue

    await msg.edit_text("❌ متاسفانه نتوانستم این لینک را دانلود کنم. دوباره امتحان کن!")
