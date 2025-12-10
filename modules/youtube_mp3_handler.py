import re
import os
import yt_dlp
import asyncio
from telegram import Update
from telegram.ext import ContextTypes

# ================================
# کوکی یوتیوب (مستقیم داخل کد)
# ================================
COOKIE_FILE = "modules/youtube_cookie.txt"

YOUTUBE_COOKIE_DATA = """# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file! Do not edit.

.youtube.com	TRUE	/	TRUE	1799284338	SOCS	CAISNQgDEitib3FfaWRlbnRpdHlmcm9udGVuZHVpc2VydmVyXzIwMjUxMjAzLjA4X3AwGgJkZSACGgYIgKrYyQY
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
.youtube.com	TRUE	/	TRUE	1799958078	PREF	tz=Europe.Berlin&repeat=NONE&autoplay=true
"""

os.makedirs("modules", exist_ok=True)
with open(COOKIE_FILE, "w", encoding="utf-8") as f:
    f.write(YOUTUBE_COOKIE_DATA)

# ================================
# دانلود بدون تبدیل
# ================================
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

URL_RE = re.compile(r"(https?://[^\s]+)")

def download_direct_audio(query):
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
        "noplaylist": True,
    }

    url = query if URL_RE.match(query) else f"ytsearch1:{query}"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename, info

# ================================
# هندلر تلگرام
# ================================
async def youtube_mp3_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    msg = await update.message.reply_text("🎶 در حال دریافت فایل صوتی...")

    loop = asyncio.get_running_loop()

    try:
        file_path, info = await loop.run_in_executor(None, download_direct_audio, text)

        await update.message.reply_audio(
            audio=open(file_path, "rb"),
            caption=f"🎵 {info.get('title','Music')}"
        )

        os.remove(file_path)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا:\n{e}")
