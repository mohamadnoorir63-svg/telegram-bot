import re
import os
import yt_dlp
import asyncio
from telegram import Update
from telegram.ext import ContextTypes

# ================================
# سودو
# ================================
SUDO_USERS = [8588347189]

# ================================
# مسیر دانلود
# ================================
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ================================
# کوکی یوتیوب (داخل کد قرار داده شده)
# ================================
YOUTUBE_COOKIES = """\
# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file! Do not edit.

.youtube.com	TRUE	/	TRUE	1799284338	SOCS	CAISNQgDEitib3FfaWRlbnRpdHlmcm9udGVuZHVpc2VydmVyXzIwMjUxMjAzLjA4X3AwGgJkZSACGgYIgKrYyQY
.youtube.com	TRUE	/	TRUE	1780708338	VISITOR_INFO1_LIVE	OBpYWqO2PUs
.youtube.com	TRUE	/	TRUE	1780708338	__Secure-BUCKET	CMwB
.youtube.com	TRUE	/	TRUE	1799716339	LOGIN_INFO	AFmmF2swRQIgYVveaSordutJGSFaMl84shpElRnOPoIJgsy-CxerUAICIQD-N79Q6VXrD9fAWQSUENWRJGYd-rZwrVEXNZ9Fbim1Ng:QUQ3MjNmeWdnTGZhMDdETlh0VnZJSjdQTmlsdlNLT25wQjdMR0V4RDhjbTNPQmdpc1BkT2ZjTzdaeUFFbGpmOGl6dVJiZ0Z4aXpnTXRlZ0hOaFFyZmdPaVhSSUotdEpxYjZBUWxIR1VpbzdENW5YZk9VUWUyU09MVDhlYVJLSW5Ua2dIX0NxUE1reC01cXJiZ3Q5Q2k1WHEzQjFTWUU1X2JR
.youtube.com	TRUE	/	FALSE	1799902985	SID	g.a0004Qh-SyGsKnh8jK0W8abn607R1S57deRp4xAuoGuSyRoyjhy0873JEYZeawVWl1V8fWZ3yAACgYKAcsSARISFQHGX2MiKoRExCpwFo1j0Z2uWxlVUBoVAUF8yKoCTcwmJwJ3RR0AdknIa2X50076
# (سایر کوکی‌ها را اینجا ادامه بده)
"""

# ================================
# regex برای لینک
# ================================
URL_RE = re.compile(r"(https?://[^\s]+)")

# ================================
# تابع دانلود مستقیم بدون تبدیل
# ================================
def download_audio_stream(query):
    # فایل موقت کوکی
    cookie_path = os.path.join(DOWNLOAD_FOLDER, "youtube_cookie.txt")
    with open(cookie_path, "w", encoding="utf-8") as f:
        f.write(YOUTUBE_COOKIES.strip())

    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "cookiefile": cookie_path,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title).200s.%(ext)s"),
    }

    url_or_search = query if URL_RE.match(query) else f"ytsearch1:{query}"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url_or_search, download=True)

        # اگر جستجو برگشت داده شد
        if 'entries' in info:
            info = info['entries'][0]

        filename = ydl.prepare_filename(info)
        # پیدا کردن فایل واقعی با هر پسوندی که yt-dlp ساخته
        for ext in ['webm','m4a','mp4','mp3','opus']:
            path = os.path.splitext(filename)[0] + f".{ext}"
            if os.path.exists(path):
                return path, info

    raise FileNotFoundError("❌ فایل دانلود نشد یا نام فایل معتبر نیست.")

# ================================
# هندلر تلگرام
# ================================
async def youtube_mp3_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    msg = await update.message.reply_text("🎵 در حال آماده‌سازی فایل ...")

    loop = asyncio.get_running_loop()
    try:
        mp3_file, info = await loop.run_in_executor(None, download_audio_stream, text)

        await update.message.reply_audio(
            audio=open(mp3_file, "rb"),
            caption=f"🎵 {info.get('title', 'Audio')}"
        )
        os.remove(mp3_file)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود یا ارسال.\n{e}")
