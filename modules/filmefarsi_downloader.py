# =====================================
#   FilmeFarsi Downloader (Final)
#   With Cookies + Cloudflare Bypass
# =====================================

import os
import re
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes

# ------------------------
# مسیر کوکی مخصوص سایت تو
# ------------------------
COOKIE_FILE = "modules/filmefarsi_cookie.txt"

# اگر وجود ندارد → بساز
os.makedirs("modules", exist_ok=True)
if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write("# Paste FilmeFarsi cookies here (Netscape format)\n")

# پوشه دانلود
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# تشخیص لینک‌های فیلم‌فارسی
FF_RE = re.compile(r"(https?://(?:www\.)?filmefarsi\.com/[^\s]+)")


# ============================
#    دانلود‌کننده فیلم‌فارسی
# ============================
async def filmefarsi_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    m = FF_RE.search(text)
    if not m:
        return  # لینک فیلم‌فارسی نبود → کاری نکن

    url = m.group(1)

    msg = await update.message.reply_text("🎬 در حال پردازش لینک FilmeFarsi...")

    # ------------------------------------------
    # تنظیمات yt-dlp مخصوص Cloudflare + Cookie
    # ------------------------------------------
    ydl_opts = {
        "cookiefile": COOKIE_FILE,
        "quiet": True,
        "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",

        # دور زدن Cloudflare (Impersonation)
        "extractor_args": {
            "generic": {
                "impersonate": "chrome"   # ← ضروری
            }
        },

        # بهترین کیفیت ممکن
        "format": "best",

        "concurrent_fragment_downloads": 8,
        "retries": 10,
        "http_headers": {
            "User-Agent": "Mozilla/5.0"
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        filepath = ydl.prepare_filename(info)
        title = info.get("title", "Video")

        await msg.edit_text("⬇ در حال ارسال فایل...")

        with open(filepath, "rb") as f:
            await update.message.reply_video(
                video=f,
                caption=f"🎬 {title}"
            )

        os.remove(filepath)

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود:\n`{e}`")
