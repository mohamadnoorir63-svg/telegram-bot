import re
import requests
from telegram import Update
from telegram.ext import ContextTypes

DOWNLOAD_SOURCES = [
    "https://snapinsta.app/action.php",
    "https://saveig.app/api/ajaxSearch",
    "https://igram.io/api/ajaxSearch"
]

INSTAGRAM_URL_RE = re.compile(r"(https?://(www\.)?instagram\.com/[^\s]+)")

async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    match = INSTAGRAM_URL_RE.search(text)
    if not match:
        return

    insta_url = match.group(1)

    msg = await update.message.reply_text("📥 در حال بررسی لینک اینستاگرام...")

    # تلاش برای دانلود از ۳ سایت کمکی
    for source in DOWNLOAD_SOURCES:
        try:
            result = download_from_service(insta_url, source)
            if result:
                await msg.edit_text("📥 در حال دانلود فایل ...")
                await context.bot.send_video(update.effective_chat.id, result)
                await msg.delete()
                return
        except Exception:
            continue

    await msg.edit_text("❌ متاسفانه نتوانستم این لینک را دانلود کنم. دوباره امتحان کن!")

def download_from_service(url, api_url):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Origin": api_url.split("/")[0] + "//" + api_url.split("/")[2],
        "Referer": api_url
    }

    data = {"url": url}

    r = requests.post(api_url, data=data, headers=headers, timeout=10)

    if r.status_code != 200:
        return None

    # استخراج لینک MP4
    matches = re.findall(r"https?://[^\'\"\s]+\.mp4", r.text)
    return matches[0] if matches else None
