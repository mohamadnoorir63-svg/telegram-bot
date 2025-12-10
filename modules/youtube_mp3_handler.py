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
# کوکی یوتیوب (مستقیم داخل کد)
# ================================
YOUTUBE_COOKIES = """
# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file! Do not edit.

.youtube.com	TRUE	/	TRUE	1799284338	SOCS	CAISNQgDEitib3FfaWRlbnRpdHlmcm9udGVuZHVpc2VydmVyXzIwMjUxMjAzLjA4X3AwGgJkZSACGgYIgKrYyQY
.youtube.com	TRUE	/	TRUE	1780708338	VISITOR_INFO1_LIVE	OBpYWqO2PUs
.youtube.com	TRUE	/	TRUE	1780708338	__Secure-BUCKET	CMwB
.youtube.com	TRUE	/	TRUE	1799716339	LOGIN_INFO	AFmmF2swRQIgYVveaSordutJGSFaMl84shpElRnOPoIJgsy-CxerUAICIQD-N79Q6VXrD9fAWQSUENWRJGYd-rZwrVEXNZ9Fbim1Ng:QUQ3MjNmeWdnTGZhMDdETlh0VnZJSjdQTmlsdlNLT25wQjdMR0V4RDhjbTNPQmdpc1BkT2ZjTzdaeUFFbGpmOGl6dVJiZ0Z4aXpnTXRlZ0hOaFFyZmdPaVhSSUotdEpxYjZBUWxIR1VpbzdENW5YZk9VUWUyU09MVDhlYVJLSW5Ua2dIX0NxUE1reC01cXJiZ3Q5Q2k1WHEzQjFTWUU1X2JR
.youtube.com	TRUE	/	FALSE	1799902985	SID	g.a0004Qh-SyGsKnh8jK0W8abn607R1S57deRp4xAuoGuSyRoyjhy0873JEYZeawVWl1V8fWZ3yAACgYKAcsSARISFQHGX2MiKoRExCpwFo1j0Z2uWxlVUBoVAUF8yKoCTcwmJwJ3RR0AdknIa2X50076
.youtube.com	TRUE	/	TRUE	1799902985	__Secure-1PSID	g.a0004Qh-SyGsKnh8jK0W8abn607R1S57deRp4xAuoGuSyRoyjhy08cLiOpa6QvgO36aY8klWZgACgYKAYESARISFQHGX2MiU0SzeJZC32XQec7taO4fxhoVAUF8yKpFB12uvfXu4rLqEQefZpRZ0076
.youtube.com	TRUE	/	TRUE	1799902985	__Secure-3PSID	g.a0004Qh-SyGsKnh8jK0W8abn607R1S57deRp4xAuoGuSyRoyjhy0dv2lIWUBJzJaBA1sqO54uAACgYKAXgSARISFQHGX2Mi8ac0ChIXv4A2jf5p9urOTRoVAUF8yKoSVZCW7nP5DTelIPs-Eof_0076
"""

# ================================
# مسیرها
# ================================
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

TEMP_COOKIE_FILE = os.path.join(DOWNLOAD_FOLDER, "yt_cookie.txt")

# ذخیره کوکی در فایل
with open(TEMP_COOKIE_FILE, "w", encoding="utf-8") as f:
    f.write(YOUTUBE_COOKIES.strip())

# ================================
# regex برای تشخیص لینک
# ================================
URL_RE = re.compile(r"(https?://[^\s]+)")

# ================================
# تابع دانلود MP3
# ================================
def download_audio_stream(query):
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "cookiefile": TEMP_COOKIE_FILE,
        "noplaylist": True,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    search = query if URL_RE.match(query) else f"ytsearch1:{query}"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search, download=True)
        base = ydl.prepare_filename(info)
        mp3_file = os.path.splitext(base)[0] + ".mp3"

    return mp3_file, info

# ================================
# هندلر اصلی تلگرام
# ================================
async def youtube_mp3_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    msg = await update.message.reply_text("🎵 در حال آماده‌سازی MP3...")

    loop = asyncio.get_running_loop()

    try:
        mp3_file, info = await loop.run_in_executor(None, download_audio_stream, text)

        if not os.path.exists(mp3_file):
            await msg.edit_text("❌ فایل خروجی پیدا نشد. (مشکل نام فایل نبود، یوتیوب جواب نداده)")
            return

        await update.message.reply_audio(
            audio=open(mp3_file, "rb"),
            caption=f"🎶 {info.get('title', 'Audio')}",
        )

        os.remove(mp3_file)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود یا تبدیل MP3:\n{e}")
