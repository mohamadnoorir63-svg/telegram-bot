import re
import requests
from telegram import Update
from telegram.ext import ContextTypes

URL_RE = re.compile(r"(https?://[^\s]+)")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://snapinsta.app/"
}

async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    m = URL_RE.search(text)

    if not m:
        return

    insta_url = m.group(1)

    if "instagram.com" not in insta_url:
        return

    msg = await update.message.reply_text("📥 در حال بررسی لینک اینستاگرام...")

    try:
        # ارسال لینک به SnapInsta
        api_url = "https://snapinsta.app/action.php"
        data = {"url": insta_url, "action": "post"}

        r = requests.post(api_url, headers=HEADERS, data=data, timeout=15)

        # استخراج لینک ویدیو
        links = re.findall(r"https?://[^\"']+\.mp4", r.text)

        if not links:
            await msg.edit_text("❌ نتوانستم لینک دانلود را پیدا کنم.")
            return

        video_url = links[0]

        await msg.edit_text("⬇ در حال دانلود ویدیو...")

        file_data = requests.get(video_url, headers=HEADERS, timeout=20).content

        await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=file_data,
            caption="📥 ویدیو با موفقیت دانلود شد!"
        )

        await msg.delete()
        return

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود: {e}")
        return
