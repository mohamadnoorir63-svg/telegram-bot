import re
import os
import yt_dlp
import asyncio
from telegram import Update
from telegram.ext import ContextTypes

# مسیر فایل کوکی
COOKIE_FILE = "modules/youtube_cookie.txt2"

# کوکی *کاملاً صحیح* بدون هیچ خط اضافی
COOKIE_CONTENT = """# Netscape HTTP Cookie File
# This is a generated file! Do not edit.
.youtube.com	TRUE	/	TRUE	1799284338	SOCS	CAISNQgDEitib3FfaWRlbnRpdHlmcm9udGVuZHVpc2VydmVyXzIwMjUxMjAzLjA4X3AwGgJkZSACGgYIgKrYyQY
.youtube.com	TRUE	/	TRUE	1780708338	VISITOR_INFO1_LIVE	OBpYWqO2PUs
.youtube.com	TRUE	/	TRUE	1780708338	__Secure-BUCKET	CMwB
.youtube.com	TRUE	/	TRUE	1799716339	LOGIN_INFO	AFmmF2swRQIgYVveaSordutJGSFaMl84shpElRnOPoIJgsy-CxerUAICIQD-N79Q6VXrD9fAWQSUENWRJGYd-rZwrVEXNZ9Fbim1Ng:QUQ3MjNmeWdnTGZhMDdETlh0VnZJSjdQTmlsdlNLT25wQjdMR0V4RDhjbTNPQmdpc1BkT2ZjTzdaeUFFbGpmOGl6dVJiZ0Z4aXpnTXRlZ0hOaFFyZmdPaVhSSUotdEpxYjZBUWxIR1VpbzdENW5YZk9VUWUyU09MVDhlYVJLSW5Ua2dIX0NxUE1reC01cXJiZ3Q5Q2k1WHEzQjFTWUU1X2JR
"""

# ایجاد پوشه و نوشتن کوکی
os.makedirs("modules", exist_ok=True)
with open(COOKIE_FILE, "w", encoding="utf-8") as f:
    f.write(COOKIE_CONTENT)

# جلوگیری از کاراکترهای غیرمجاز
def safe_name(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

# دانلود صوت بدون تبدیل
def download_audio(query):
    opts = {
        "format": "bestaudio",
        "noplaylist": True,
        "cookiefile": COOKIE_FILE,
        "outtmpl": "downloads/%(title).200s.%(ext)s",
    }

    url = query if re.match(r'https?://', query) else f"ytsearch1:{query}"

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

    filename = f"downloads/{safe_name(info['title'])}.{info['ext']}"
    return filename, info

async def youtube_mp3_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    msg = await update.message.reply_text("⏳ در حال دانلود...")

    loop = asyncio.get_running_loop()
    try:
        file_path, info = await loop.run_in_executor(None, download_audio, text)

        await update.message.reply_audio(
            audio=open(file_path, "rb"),
            caption=info["title"]
        )

        os.remove(file_path)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا:\n{e}")
