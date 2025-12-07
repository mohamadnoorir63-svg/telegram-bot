# modules/youtube_downloader.py
import os
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes
import re

# ================================
# 📌 کوکی‌های یوتیوب (اینجا قرار بده!)
# ================================
YOUTUBE_COOKIES = r"""
# 👉👉 همین داخل کوکی‌های یوتیوب خودت را قرار بده 👇
# مثال:
# .youtube.com    TRUE    /    TRUE    1234567890    SID    abcdefg12345

# 🔥 توجه: 
# 1- هیچ کاراکتر عجیب مثل … یا " اضافه نکن
# 2- فقط متن دقیق خروجی افزونه Cookie-Editor را کپی کن
# 3- اگر یک خط خراب باشد yt-dlp ارور می‌دهد

# ===============================
#      👇 از این خط پایین شروع کن
# ===============================
# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file! Do not edit.

.youtube.com	TRUE	/	TRUE	1796681120	__Secure-1PSIDTS	sidts-CjUBflaCdQcOtbfDt-nRp2oFwMBpfscyZZMzEzZ6aJ1sLKd1IcwA5pmRFHD6glmEEpfV0YCuARAA
.youtube.com	TRUE	/	TRUE	1796681120	__Secure-3PSIDTS	sidts-CjUBflaCdQcOtbfDt-nRp2oFwMBpfscyZZMzEzZ6aJ1sLKd1IcwA5pmRFHD6glmEEpfV0YCuARAA
.youtube.com	TRUE	/	FALSE	1799705120	HSID	AjTGPu3s0ssOMGmdt
.youtube.com	TRUE	/	TRUE	1799705120	SSID	AoWSAlkTiFw-Dz-vx
.youtube.com	TRUE	/	FALSE	1799705120	APISID	HxvXQSYkXGNgYpof/AFT19W4Wez3p3UcIH
.youtube.com	TRUE	/	TRUE	1799705120	SAPISID	_rcraLOX-PKvwhu4/AF9NcPAxfy-kfJMFD
.youtube.com	TRUE	/	TRUE	1799705120	__Secure-1PAPISID	_rcraLOX-PKvwhu4/AF9NcPAxfy-kfJMFD
.youtube.com	TRUE	/	TRUE	1799705120	__Secure-3PAPISID	_rcraLOX-PKvwhu4/AF9NcPAxfy-kfJMFD
.youtube.com	TRUE	/	FALSE	1799705120	SID	g.a0004Qi6jym_HRITeYANcuvacvEX1n3U2f-12S7BODezxV102T6kO9WpabcF0iQ30aKxMecIPAACgYKATsSARUSFQHGX2MijUWJ-ZsvcGEkOR_AeAJs4hoVAUF8yKpEcRbtGGH1RWTfllFjA0LL0076
.youtube.com	TRUE	/	TRUE	1799705120	__Secure-1PSID	g.a0004Qi6jym_HRITeYANcuvacvEX1n3U2f-12S7BODezxV102T6kuenCZ93IQFHAlg5uLVgQmQACgYKAW8SARUSFQHGX2MiIQNKrQhBYpDgboHODYMFexoVAUF8yKotd0bxWtWYAAyyIEh4HcXo0076
.youtube.com	TRUE	/	TRUE	1799705120	__Secure-3PSID	g.a0004Qi6jym_HRITeYANcuvacvEX1n3U2f-12S7BODezxV102T6kFJyk7bFhNUN7bNDub2dfLgACgYKAQoSARUSFQHGX2Mi7FGyLoUu8qk9JF6vqv8bMBoVAUF8yKq_x7FJo417PItBJsFLw86X0076
.youtube.com	TRUE	/	TRUE	1799273122	__Secure-YENID	12.YTE=f9vE4vK3YUiY_OjlR-l77MfUqzPeJzNhJJU9_kF1-mM3Ib47J55X3h5pK9X2lE8J7AECeFYGRCz4xja-1Ef_SkjkaTZNHMcb0N2yhKQcRcnNQO2Wq923actq6vLoS7UMoGjueDZhrzqX_PKedKu1ww6q1lTmMcvfPDXwcREyjrsapRoyrRRsPNIfbqksSIs0Gffs7wAwBEnuy0PmC5IAr1RKEMChxDzyB9s36eY3cUaunRi9SDpH3n80zoOIXaKYhaK8Z1a86KttJsHFaYlx2-A_C87QMfz2LcJF4qvty6KT4SBN3LjcyEv7Sl3WvByZieu7uB9_pCDBnDCHaDNPsA
.youtube.com	TRUE	/	TRUE	1799706276	PREF	tz=Europe.Berlin
.youtube.com	TRUE	/	TRUE	1799705908	LOGIN_INFO	AFmmF2swRgIhAO3xrj60ZCTjahn6F9PyI8rgA6gN9TOA5QB8YbHUbqSHAiEAmHpniMLKXL5tjE8w0oW59c4nz_9rQfiIGbuksF4499A:QUQ3MjNmekJPUmQyT1hjRGUzQjd0bDBBaEZMVzJzMFRQSFhQTHBzZEd1V1F4S3B2V2pKYnJtbGR0ZkpDdmdSREh0b3JnRE0zU1g3YzlVU3dKUEowSGIyNTJ5VF8xTmctSmt1Y2JLNTFycmgwa0hQWlRCWWJRdmh2UFFwSHFVZUlpbWZDa29scGFxYWdiam1NRzY0a0dnUkp0aENQVjFrcDhB
.youtube.com	TRUE	/	TRUE	1799273123	__Secure-YEC	CgttMWFsbFhqZXQxNCik_dfJBjIKCgJERRIEEgAgFGLgAgrdAjEyLllURT1mOXZFNHZLM1lVaVlfT2psUi1sNzdNZlVxelBlSnpOaEpKVTlfa0YxLW1NM0liNDdKNTVYM2g1cEs5WDJsRThKN0FFQ2VGWUdSQ3o0eGphLTFFZl9Ta2prYVRaTkhNY2IwTjJ5aEtRY1Jjbk5RTzJXcTkyM2FjdHE2dkxvUzdVTW9HanVlRFpocnpxWF9QS2VkS3Uxd3c2cTFsVG1NY3ZmUERYd2NSRXlqcnNhcFJveXJSUnNQTklmYnFrc1NJczBHZmZzN3dBd0JFbnV5MFBtQzVJQXIxUktFTUNoeER6eUI5czM2ZVkzY1VhdW5SaTlTRHBIM244MHpvT0lYYUtZaGFLOFoxYTg2S3R0SnNIRmFZbHgyLUFfQzg3UU1mejJMY0pGNHF2dHk2S1Q0U0JOM0xqY3lFdjdTbDNXdkJ5WmlldTd1QjlfcENEQm5EQ0hhRE5Qc0E%3D
.youtube.com	TRUE	/	FALSE	1796682276	SIDCC	AKEyXzWM6NggqZiqJqNPbrP8Fx8whTqqFOVPkSwDdflSmRmZPooKZVCHmEn_GZxZCrORyL70oA
.youtube.com	TRUE	/	TRUE	1796682276	__Secure-1PSIDCC	AKEyXzUP5l0_6tcnpoOEDmsXxUKrZ6R800VaJxNL077KJTwgQzk8dPMe13dWFdz0YDsdu3sx
.youtube.com	TRUE	/	TRUE	1796682276	__Secure-3PSIDCC	AKEyXzWYo038v1sezYDWBx81URCwKdjUtn2oflMpeUHtbjlQH2w4E_cERFpEthA-4TrVD8Tq


(اینجا کوکی‌های خودت را بگذار)

# ===============================
#      👆 تا این خط بالا ادامه بده
# ===============================

"""

# ذخیره خودکار کوکی‌ها داخل فایل
COOKIE_FILE = "youtube_cookie.txt"
with open(COOKIE_FILE, "w", encoding="utf-8") as f:
    f.write(YOUTUBE_COOKIES)

# مسیر دانلود فایل‌ها
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

URL_RE = re.compile(r"(https?://[^\s]+)")

async def youtube_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    match = URL_RE.search(text)

    if not match:
        return

    url = match.group(1)

    if "youtube.com" not in url and "youtu.be" not in url:
        return

    msg = await update.message.reply_text("📥 در حال پردازش لینک یوتیوب...")

    # تنظیمات yt-dlp
    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "format": "best",
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
        "noplaylist": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        title = info.get("title", "YouTube Video")

        await msg.edit_text("⬇ در حال ارسال ویدیو...")
        await update.message.reply_video(
            video=open(filename, "rb"),
            caption=f"📥 {title}"
        )

        # تبدیل به فایل صوتی
        mp3_file = filename.replace(".mp4", ".mp3")
        os.system(f'ffmpeg -i "{filename}" -vn -ab 192k "{mp3_file}" -y')

        await update.message.reply_audio(
            audio=open(mp3_file, "rb"),
            caption=f"🎵 {title}"
        )

        os.remove(filename)
        os.remove(mp3_file)

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود یوتیوب:\n{e}")
