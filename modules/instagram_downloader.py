# modules/instagram_downloader.py
import os
import re
import requests
from telegram import Update
from telegram.ext import ContextTypes

# پوشه ذخیره موقت
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# پیدا کردن اولین لینک در متن
URL_RE = re.compile(r"(https?://[^\s]+)")

# هدر شبیه مرورگر برای دور زدن بعضی چک‌ها
COMMON_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# لیست سایت‌های واسط برای دانلود اینستاگرام
HELPERS = [
    {
        "name": "igram.world (GET)",
        "method": "GET",
        "url": "https://igram.world/api/ig?url={url}",
        "data_name": None,
    },
    {
        "name": "saveig.app (POST)",
        "method": "POST",
        "url": "https://saveig.app/api/ajaxSearch",
        "data_name": "url",
    },
    {
        "name": "snapinsta.app (POST)",
        "method": "POST",
        "url": "https://snapinsta.app/action.php",
        "data_name": "url",
    },
    {
        "name": "instasave.one (GET)",
        "method": "GET",
        "url": "https://instasave.one/wp-json/instagram-downloader/api?url={url}",
        "data_name": None,
    },
]


def _extract_media_url_from_html(html: str) -> str | None:
    """
    سعی می‌کنیم لینک mp4 یا عکس رو از HTML سایت واسط پیدا کنیم.
    اولویت: mp4 → بعد jpg/png
    """
    # ویدیو
    mp4s = re.findall(r"https?://[^\s\"']+\.mp4", html)
    if mp4s:
        return mp4s[0]

    # عکس
    imgs = re.findall(r"https?://[^\s\"']+\.(?:jpe?g|png|webp)", html)
    if imgs:
        return imgs[0]

    return None


def _download_file(url: str, filename: str) -> str:
    """
    دانلود فایل از لینک مستقیم media و ذخیره در downloads
    """
    resp = requests.get(url, headers=COMMON_HEADERS, timeout=30, stream=True)
    resp.raise_for_status()

    full_path = os.path.join(DOWNLOAD_DIR, filename)

    with open(full_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 64):
            if not chunk:
                continue
            f.write(chunk)

    return full_path


async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    هندلر اصلی اینستاگرام:
    - اگر پیام لینک اینستا داشته باشد، تلاش برای دانلود
    - از چند سایت واسط کمک می‌گیرد
    """
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    m = URL_RE.search(text)
    if not m:
        return

    ig_url = m.group(1)

    # فقط لینک‌های اینستاگرام
    if "instagram.com" not in ig_url:
        return

    chat_id = update.effective_chat.id
    msg = await update.message.reply_text("📥 در حال بررسی لینک اینستاگرام...")

    media_url = None

    # یکی یکی سایت‌های واسط را امتحان می‌کنیم
    for helper in HELPERS:
        try:
            name = helper["name"]
            method = helper["method"]
            base_url = helper["url"]
            data_name = helper["data_name"]

            # ساخت URL / DATA
            if method == "GET":
                url = base_url.format(url=ig_url)
                resp = requests.get(url, headers=COMMON_HEADERS, timeout=20)
            else:  # POST
                url = base_url
                data = {data_name: ig_url} if data_name else {}
                resp = requests.post(url, headers=COMMON_HEADERS, data=data, timeout=20)

            if resp.status_code != 200 or not resp.text:
                continue

            media_url = _extract_media_url_from_html(resp.text)
            if media_url:
                break

        except Exception:
            # اگر این سایت خطا داد، می‌ریم سراغ بعدی
            continue

    if not media_url:
        await msg.edit_text(
            "❌ متاسفانه نتوانستم این لینک را دانلود کنم.\n"
            "🔁 دوباره امتحان کن یا چند دقیقه بعد تلاش کن."
        )
        return

    # حالا خود فایل media را می‌گیریم
    await msg.edit_text("⬇ در حال دانلود رسانه از اینستاگرام...")

    try:
        # اسم فایل بر اساس نوع
        if ".mp4" in media_url:
            filename = "instagram_video.mp4"
        else:
            filename = "instagram_media" + os.path.splitext(media_url)[-1]

        file_path = _download_file(media_url, filename)

        # ویدیو یا عکس؟
        if filename.endswith(".mp4"):
            await context.bot.send_video(
                chat_id=chat_id,
                video=open(file_path, "rb"),
                caption="📥 ویدیو اینستاگرام با موفقیت دانلود شد!",
            )
        else:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=open(file_path, "rb"),
                caption="📥 رسانه اینستاگرام با موفقیت دانلود شد!",
            )

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود رسانه:\n{e}")
        return
    finally:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass

    await msg.delete()
