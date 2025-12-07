import re
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes

# ================================
#   📌 کوکی‌های اینستاگرام (داخل کد)
# ================================
INSTAGRAM_COOKIES = """
# Netscape HTTP Cookie File
.instagram.com	TRUE	/	TRUE	1799701606	csrftoken	--d8oLwWArIVOTuxrKibqa
.instagram.com	TRUE	/	TRUE	1799687399	datr	47Q1aZceuWl7nLkf_Uzh_kVW
.instagram.com	TRUE	/	TRUE	1796663399	ig_did	615B02DC-3964-40ED-864D-5EDD6E7C4EA3
.instagram.com	TRUE	/	TRUE	1799687399	mid	aTW04wABAAHoKpxsaAJbAfLsgVU3
.instagram.com	TRUE	/	TRUE	1765732343	dpr	2
.instagram.com	TRUE	/	TRUE	1772917606	ds_user_id	79160628834
.instagram.com	TRUE	/	TRUE	1796663585	sessionid	79160628834%3AtMYF1zDBj9tXx3%3A7%3AAYhX_MD6k4rrVPUaIBvVhJLqxdAzNqJ0SkLDHb-ymQ
.instagram.com	TRUE	/	TRUE	1765746400	wd	360x683
.instagram.com	TRUE	/	TRUE	0	rur	"FRC\05479160628834\0541796677606:01feeadcb720f15c682519c2475d06626b55e5e1646ce3648355ab004152c377c46ba081"
"""

COOKIE_FILE = "insta_cookie.txt"

# ذخیره کوکی
with open(COOKIE_FILE, "w") as f:
    f.write(INSTAGRAM_COOKIES.strip())

# استخراج لینک از پیام
URL_RE = re.compile(r"(https?://[^\s]+)")


async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    m = URL_RE.search(text)

    if not m:
        return

    url = m.group(1)

    if "instagram.com" not in url:
        return

    msg = await update.message.reply_text("📥 در حال بررسی لینک اینستاگرام...")

    ydl_opts = {
        "quiet": True,
        "cookiefile": COOKIE_FILE,
        "format": "best",
        "outtmpl": "downloads/%(id)s.%(ext)s",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        await msg.edit_text("⬇ ارسال فایل‌ها...")

        sent_any = False

        # ------------------------------
        # 📌 ارسال ویدیو (اگر موجود بود)
        # ------------------------------
        if "requested_downloads" in info:
            for file in info["requested_downloads"]:
                fpath = file.get("filepath")
                ext = fpath.split(".")[-1].lower()

                if ext in ["mp4", "mkv", "webm"]:
                    await update.message.reply_video(
                        video=open(fpath, "rb"),
                        caption="📥 ویدیو با موفقیت دانلود شد!"
                    )
                    sent_any = True

                # ------------------------------
                # 🎵 ارسال فایل صوتی (اگر موجود بود)
                # ------------------------------
                if ext in ["mp3", "m4a", "aac", "ogg", "opus"]:
                    await update.message.reply_audio(
                        audio=open(fpath, "rb"),
                        caption="🎵 فایل صوتی پست"
                    )
                    sent_any = True

        if not sent_any:
            await msg.edit_text("⚠️ هیچ ویدیو یا صوتی در این پست پیدا نشد!")
        else:
            await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ نتوانستم دانلود کنم.\n⚠️ خطا: {e}")
