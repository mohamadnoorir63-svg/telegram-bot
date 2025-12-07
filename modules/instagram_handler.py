# modules/instagram_downloader.py
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes

API_LIST = [
    "https://snapinsta.app/action.php?url={}",
    "https://saveig.app/api/ajax?url={}",
    "https://igram.io/api/ajax?url={}",
    "https://instasave.one/action.php?url={}"
]

async def fetch_api(session, url):
    async with session.get(url, timeout=15) as resp:
        if resp.status == 200:
            return await resp.text()
        return None

async def extract_download_link(html: str) -> str:
    """
    از HTML لینک دانلود را استخراج می‌کند.
    """
    import re
    # پیدا کردن لینک MP4 یا JPG
    match = re.search(r'https?://[^"]+\.(mp4|jpg|jpeg|png)', html)
    return match.group(0) if match else None

async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    if "instagram.com" not in text:
        return  # لینک نیست

    msg = await update.message.reply_text("🔍 در حال پردازش لینک اینستاگرام...")

    async with aiohttp.ClientSession() as session:
        for api in API_LIST:
            api_url = api.format(text)
            try:
                html = await fetch_api(session, api_url)
                if not html:
                    continue

                download_url = await extract_download_link(html)
                if download_url:
                    await msg.edit_text("⬇️ لینک آماده شد، در حال دانلود...")

                    await context.bot.send_video(
                        update.effective_chat.id,
                        download_url,
                        caption="📥 ویدیو با موفقیت دانلود شد."
                    )
                    await msg.delete()
                    return

            except Exception:
                continue

    await msg.edit_text("❌ متاسفانه نتوانستم این لینک را دانلود کنم. دوباره امتحان کن!")
