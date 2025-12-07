import re
import requests
from telegram import Update
from telegram.ext import ContextTypes

URL_RE = re.compile(r"(https?://[^\s]+)")

# ۳ سرور پایدار — تست‌شده
INSTAGRAM_APIS = [
    "https://saveig.app/api/ajax?url={}",
    "https://snapinsta.io/core/ajax.php?url={}",
    "https://igram.world/api/ig?url={}"
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

    for api in INSTAGRAM_APIS:
        try:
            api_url = api.format(url)
            r = requests.get(api_url, timeout=10)

            if r.status_code != 200:
                continue

            # استخراج هر لینک mp4
            mp4_links = re.findall(r"https?://[^\"'\s]+\.mp4", r.text)

            if not mp4_links:
                continue

            download_url = mp4_links[0]

            await msg.edit_text("⬇ ویدیو پیدا شد — در حال دانلود...")

            video_data = requests.get(download_url, timeout=20)

            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video_data.content,
                caption="📥 ویدیو با موفقیت دانلود شد!"
            )

            await msg.delete()
            return

        except Exception as e:
            print("API Error:", e)
            continue

    await msg.edit_text("❌ متاسفانه نتوانستم این لینک را دانلود کنم.\n🔁 دوباره تلاش کن!")
