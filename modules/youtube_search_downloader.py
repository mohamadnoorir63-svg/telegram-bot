import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
import yt_dlp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

SUDO_USERS = [8588347189]
COOKIE_FILE = "modules/youtube_cookie.txt2"
URL_RE = re.compile(r"(https?://[^\s]+)")
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

executor = ThreadPoolExecutor(max_workers=4)
pending_links = {}

# ================================
def clean_parts():
    """حذف فایل‌های .part برای جلوگیری از خطا"""
    for f in os.listdir(DOWNLOAD_FOLDER):
        if f.endswith(".part") or "Frag" in f:
            try:
                os.remove(os.path.join(DOWNLOAD_FOLDER, f))
            except:
                pass

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
def _download_to_disk(url, audio=False):
    """دانلود پایدار و بدون خطای Frag"""
    clean_parts()

    ydl_opts = {
        "quiet": True,
        "noplaylist": True,
        "cookiefile": COOKIE_FILE,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "concurrent_fragment_downloads": 4,   # 🔥 پایدار و سریع
        "retries": 10,                        # 🔁 ریترای اتوماتیک
        "fragment_retries": 10,
    }

    if audio:
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
        if audio:
            filename = filename.rsplit(".", 1)[0] + ".mp3"
        return info, filename

# ================================
async def youtube_search_handler(update, context):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    m = URL_RE.search(text)

    if not m:
        return

    url = m.group(1)
    if "youtube" not in url:
        return

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    pending_links[update.effective_chat.id] = url

    kb = [
        [InlineKeyboardButton("🎵 Audio (MP3)", callback_data="yt_audio")],
        [InlineKeyboardButton("🎬 Video (MP4)", callback_data="yt_video")],
    ]

    await update.message.reply_text(
        "🎧 لطفاً نوع دانلود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ================================
async def youtube_quality_handler(update, context):
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
    msg = await cq.message.reply_text("⬇ در حال دانلود پایدار ...")

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
            caption=info.get("title", "file"),
            reply_markup=get_add_btn(update.effective_chat.type)
        )

    except Exception as e:
        await msg.edit_text(f"❌ خطا: {e}")
        return

    finally:
        clean_parts()
        if os.path.exists(file_path):
            os.remove(file_path)
        await msg.delete()
