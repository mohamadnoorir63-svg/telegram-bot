import re
import os
import requests
from telegram import Update
from telegram.ext import ContextTypes

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

URL_RE = re.compile(r"(https?://[^\s]+)")

# -----------------------------
#  Helper: Send file to user
# -----------------------------
async def send_file(path, chat_id, bot, caption):
    ext = path.split(".")[-1].lower()
    with open(path, "rb") as f:
        if ext in ["mp4", "mov"]:
            await bot.send_video(chat_id, f, caption=caption)
        else:
            await bot.send_photo(chat_id, f, caption=caption)

    os.remove(path)

# -----------------------------
#  1️⃣ Try saveig.app
# -----------------------------
def download_from_saveig(url):
    api = "https://saveig.app/api/ajaxSearch"
    resp = requests.post(api, data={"q": url, "t": "media"})
    if resp.status_code != 200:
        return None

    data = resp.json()
    if "data" not in data:
        return None

    links = re.findall(r'https://[^"]+', data["data"])
    return links[0] if links else None

# -----------------------------
#  2️⃣ Try igram.io
# -----------------------------
def download_from_igram(url):
    api = "https://igram.io/api/instagram"
    resp = requests.get(api, params={"url": url})
    if resp.status_code != 200:
        return None

    data = resp.json()
    if "medias" not in data:
        return None

    return data["medias"][0]["url"]

# -----------------------------
#  3️⃣ Try snapinsta.app
# -----------------------------
def download_from_snapinsta(url):
    api = "https://snapinsta.app/wp-json/aio-dl/video-data/"
    resp = requests.post(api, data={"url": url})
    if resp.status_code != 200:
        return None

    data = resp.json()
    if "url" not in data:
        return None

    return data["url"]

# -----------------------------
#  Instagram Handler
# -----------------------------
async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    chat_id = update.effective_chat.id

    m = URL_RE.search(text)
    if not m:
        return

    url = m.group(0)

    msg = await update.message.reply_text("📥 در حال بررسی لینک اینستاگرام...")

    # سعی با سایت اول
    dl = download_from_saveig(url)
    if not dl:
        dl = download_from_igram(url)
    if not dl:
        dl = download_from_snapinsta(url)

    if not dl:
        await msg.edit_text("❌ متاسفانه نتوانستم این لینک را دانلود کنم. دوباره امتحان کن!")
        return

    # دانلود فایل
    filename = os.path.join(DOWNLOAD_FOLDER, "ig_" + os.path.basename(dl.split("?")[0]))

    r = requests.get(dl, stream=True)
    if r.status_code != 200:
        await msg.edit_text("❌ دانلود فایل انجام نشد.")
        return

    with open(filename, "wb") as f:
        for chunk in r.iter_content(1024 * 1024):
            f.write(chunk)

    await msg.edit_text("⬇️ دانلود کامل شد — ارسال فایل...")

    await send_file(filename, chat_id, context.bot, "📥 دانلود اینستاگرام")

    await msg.delete()
