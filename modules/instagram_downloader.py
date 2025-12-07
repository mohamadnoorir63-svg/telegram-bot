import re
import requests
from telegram import Update
from telegram.ext import ContextTypes

# سایت‌های کمکی
INSTAGRAM_APIS = [
    "https://igram.world/api/ig?url={}",
    "https://saveig.app/api/ajax?url={}",
    "https://snapinsta.app/action.php?url={}",
    "https://instasave.one/wp-json/instagram-downloader/api?url={}"
]

# استخراج لینک از پیام
URL_RE = re.compile(r"(https?://[^\s]+)")

async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    match = URL_RE.search(text)

    if not match:
        return

    url = match.group(1)

    # فقط اگر لینک اینستاگرام بود
    if "instagram.com" not in url:
        return

    msg = await update.message.reply_text("📥 در حال بررسی لینک اینستاگرام...")

    for api in INSTAGRAM_APIS:
        try:
            api_url = api.format(url)
            r = requests.get(api_url, timeout=10)

            if r.status_code != 200 or len(r.text) < 5:
                continue

            # تلاش برای یافتن لینک دانلود (mp4)
            mp4_links = re.findall(r"https?://[^\"'\s]+\.mp4", r.text)

            if mp4_links:
                download_url = mp4_links[0]

                await msg.edit_text("⬇ در حال دانلود ویدیو...")

                video = requests.get(download_url, timeout=15)

                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=video.content,
                    caption="📥 ویدیو با موفقیت دانلود شد!"
                )

                await msg.delete()
                return

        except Exception:
            continue

    # اگر هیچ سایتی جواب نداد
    await msg.edit_text("❌ متاسفانه نتوانستم این لینک را دانلود کنم. دوباره امتحان کن!")
