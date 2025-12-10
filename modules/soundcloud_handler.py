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
# مسیر کوکی یوتیوب
# ================================
COOKIE_FILE = "youtube_cookie.txt"

# کوکی را در فایل ذخیره کنید
YOUTUBE_COOKIES = """\
# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file! Do not edit.
.youtube.com	TRUE	/	TRUE	1799284338	SOCS	CAISNQgDEitib3FfaWRlbnRpdHlmcm9udGVpc2VydmVyXzIwMjUxMjAzLjA4X3AwGgJkZSACGgYIgKrYyQY
.youtube.com	TRUE	/	TRUE	1780708338	VISITOR_INFO1_LIVE	OBpYWqO2PUs
.youtube.com	TRUE	/	TRUE	1780708338	__Secure-BUCKET	CMwB
.youtube.com	TRUE	/	TRUE	1799716339	LOGIN_INFO	AFmmF2swRQIgYVveaSordutJGSFaMl84shpElRnOPoIJgsy-CxerUAICIQD-N79Q6VXrD9fAWQSUENWRJGYd-rZwrVEXNZ9Fbim1Ng:QUQ3MjNmeWdnTGZhMDdETlh0VnZJSjdQTmlsdlNLT25wQjdMR0V4RDhjbTNPQmdpc1BkT2ZjTzdaeUFFbGpmOGl6dVJiZ0Z4aXpnTXRlZ0hOaFFyZmdPaVhSSUotdEpxYjZBUWxIR1VpbzdENW5YZk9VUWUyU09MVDhlYVJLSW5Ua2dIX0NxUE1reC01cXJiZ3Q5Q2k1WHEzQjFTWUU1X2JR
.youtube.com	TRUE	/	FALSE	1799902985	SID	g.a0004Qh-SyGsKnh8jK0W8abn607R1S57deRp4xAuoGuSyRoyjhy0873JEYZeawVWl1V8fWZ3yAACgYKAcsSARISFQHGX2MiKoRExCpwFo1j0Z2uWxlVUBoVAUF8yKoCTcwmJwJ3RR0AdknIa2X50076
.youtube.com	TRUE	/	TRUE	1799902985	__Secure-1PSID	g.a0004Qh-SyGsKnh8jK0W8abn607R1S57deRp4xAuoGuSyRoyjhy08cLiOpa6QvgO36aY8klWZgACgYKAYESARISFQHGX2MiU0SzeJZC32XQec7taO4fxhoVAUF8yKpFB12uvfXu4rLqEQefZpRZ0076
.youtube.com	TRUE	/	TRUE	1799902985	__Secure-3PSID	g.a0004Qh-SyGsKnh8jK0W8abn607R1S57deRp4xAuoGuSyRoyjhy0dv2lIWUBJzJaBA1sqO54uAACgYKAXgSARISFQHGX2Mi8ac0ChIXv4A2jf5p9urOTRoVAUF8yKoSVZCW7nP5DTelIPs-Eof_0076
.youtube.com	TRUE	/	FALSE	1799902985	HSID	ACot7wsidbZkE1cpX
.youtube.com	TRUE	/	TRUE	1799902985	SSID	ADvnhaZMQnQ0bacl-
.youtube.com	TRUE	/	FALSE	1799902985	APISID	m-DWZeLhqcxzseLm/APqdatThKfQoxN_ZP
.youtube.com	TRUE	/	TRUE	1799902985	SAPISID	l6jBIc-jxjFq-2tm/AOyKuClMF0-1v6JIZ
.youtube.com	TRUE	/	TRUE	1799902985	__Secure-1PAPISID	l6jBIc-jxjFq-2tm/AOyKuClMF0-1v6JIZ
.youtube.com	TRUE	/	TRUE	1799902985	__Secure-3PAPISID	l6jBIc-jxjFq-2tm/AOyKuClMF0-1v6JIZ
.youtube.com	TRUE	/	TRUE	1796878985	__Secure-1PSIDTS	sidts-CjUBflaCdbjZgNKbdvEZh-mKCYMD-QE6Z336jix30OspuuLGc8NRnhCuCeW9n65rlA_5Z1qMeBAA
.youtube.com	TRUE	/	TRUE	1796878985	__Secure-3PSIDTS	sidts-CjUBflaCdbjZgNKbdvEZh-mKCYMD-QE6Z336jix30OspuuLGc8NRnhCuCeW9n65rlA_5Z1qMeBAA
.youtube.com	TRUE	/	FALSE	1799958016	_ga	GA1.1.1553215078.1765398016
.youtube.com	TRUE	/	FALSE	1799958049	_ga_VCGEPY40VB	GS2.1.s1765398016$o1$g1$t1765398048$j28$l0$h0
.youtube.com	TRUE	/	FALSE	1796934050	SIDCC	AKEyXzU8fipXVikWA6SVgmxGVxE1_ZS_-xxwLPJHK1aLW8ycotr44asseNgT1QvRwbZXxRMd
.youtube.com	TRUE	/	TRUE	1796934050	__Secure-1PSIDCC	AKEyXzUTZaBB6qcnqXafifJQ5yPZaoeanVvTgvWL3uIkPb2y50gaVTTG5Hu0jLVrqZHL1hvq
.youtube.com	TRUE	/	TRUE	1796934050	__Secure-3PSIDCC	AKEyXzVuuMH7JU1MtDoD_-BrXZd_5hI8OuyyNAe7nAMMsBQY-fV3ce5mGKnrzXrkbi3wL97x
.youtube.com	TRUE	/	TRUE	1765398673	CONSISTENCY	APeVyi9Fm9rqX0u26WqAyxARuyP4Q9X7H1-c-er2T6sQbzUMdoNSncCLFdAMx3h8HZu24fZuxX9pUzAgGWxCDEV76Hqdy4PMCjmb_eGmzgXzcorZu8sJP6xEBJbA84MuKBLjS_wvuFiBu2KnJhI0bim2yc-cPnLaD6kzmpUYWgSBKKCiC50f4eTT_SE-SB-EKpA
.youtube.com	TRUE	/	TRUE	1799958078	PREF	tz=Europe.Berlin&repeat=NONE&autoplay=true
"""

with open(COOKIE_FILE, "w", encoding="utf-8") as f:
    f.write(YOUTUBE_COOKIES.strip())

# ================================
# مسیر دانلود
# ================================
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ================================
# regex برای لینک
# ================================
URL_RE = re.compile(r"(https?://[^\s]+)")

# ================================
# تابع دانلود مستقیم MP3 با کوکی
# ================================
def download_audio_stream(url_or_search):
    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "extractaudio": True,
        "audioformat": "mp3",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url_or_search, download=True)
        filename = ydl.prepare_filename(info)
        mp3_file = os.path.splitext(filename)[0] + ".mp3"
    return mp3_file, info

# ================================
# هندلر تلگرام
# ================================
async def youtube_mp3_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    msg = await update.message.reply_text("🎵 در حال آماده‌سازی MP3 ...")

    loop = asyncio.get_running_loop()
    try:
        url_or_search = text if URL_RE.match(text) else f"ytsearch:{text}"
        mp3_file, info = await loop.run_in_executor(None, download_audio_stream, url_or_search)

        await update.message.reply_audio(audio=open(mp3_file, "rb"),
                                         caption=f"🎵 {info.get('title', 'Audio')}")
        os.remove(mp3_file)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود یا ارسال MP3.\n{e}")
