import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
import yt_dlp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ================================
# تنظیمات
# ================================
SUDO_USERS = [8588347189]
COOKIE_FILE = "modules/youtube_cookie.txt"
URL_RE = re.compile(r"(https?://[^\s]+)")
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

executor = ThreadPoolExecutor(max_workers=6)  # 🔥 افزایش سرعت

pending_links = {}

# ================================
def get_add_btn(chat_type):
    if chat_type == "private":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ افزودن ربات به گروه", url="https://t.me/AFGR63_bot?startgroup=true")]
        ])
    return None

# ================================
async def is_admin(update, context):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private" or user.id in SUDO_USERS:
        return True
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        return user.id in [a.user.id for a in admins]
    except:
        return False

# ================================
# دانلود ویدیو یا صوت روی دیسک
# ================================
def _download_to_disk(url, audio_only=False):
    ydl_opts = {
        "quiet": True,
        "noplaylist": True,
        "noprogress": True,
        "cookiefile": COOKIE_FILE,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "concurrent_fragment_downloads": 16,   # 🔥 سرعت آتشی
    }

    if audio_only:
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    else:
        ydl_opts["format"] = "bestvideo+bestaudio/best"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

        if audio_only:
            filename = filename.rsplit(".", 1)[0] + ".mp3"

        return info, filename

# ================================
async def youtube_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    match = URL_RE.search(text)
    if not match:
        return

    url = match.group(1)
    if "youtube.com" not in url and "youtu.be" not in url:
        return

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    pending_links[update.effective_chat.id] = url

    keyboard = [
        [InlineKeyboardButton("🎵 Audio (MP3)", callback_data="yt_audio")],
        [InlineKeyboardButton("🎬 Video (MP4)", callback_data="yt_video")],
    ]

    await update.message.reply_text(
        "🎬 لطفاً نوع دانلود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================================
async def youtube_quality_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    chat_id = cq.message.chat_id
    await cq.answer()

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    url = pending_links.get(chat_id)
    if not url:
        return await cq.message.reply_text("❌ لینک معتبر یافت نشد.")

    choice = cq.data

    msg = await cq.message.reply_text("⬇ در حال دانلود با سرعت آتشی ...")

    loop = asyncio.get_running_loop()

    try:
        if choice == "yt_audio":
            info, file_path = await loop.run_in_executor(
                executor, _download_to_disk, url, True
            )
        else:
            info, file_path = await loop.run_in_executor(
                executor, _download_to_disk, url, False
            )

        await msg.edit_text("⬆ در حال ارسال ...")

        await context.bot.send_document(
            chat_id,
            document=open(file_path, "rb"),
            caption=info.get("title", "File"),
            reply_markup=get_add_btn(update.effective_chat.type)
        )

    except Exception as e:
        await msg.edit_text(f"❌ خطا: {e}")
        return

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)  # حذف فایل بعد ارسال
        await msg.delete()
