import os
import shutil
import subprocess
import requests
import yt_dlp
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

SUDO_USERS = [8588347189]
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)

video_store = {}
executor = asyncio.get_running_loop().run_in_executor  # استفاده از ThreadPool

# ================================
# چک مدیر بودن
# ================================
async def is_admin(update, context):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        return True
    if user.id in SUDO_USERS:
        return True
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        admin_ids = [a.user.id for a in admins]
        return user.id in admin_ids
    except:
        return False

# ================================
# تبدیل به mp3
# ================================
def _convert_to_mp3_blocking(video_path: str) -> str:
    mp3_path = video_path.rsplit(".", 1)[0] + ".mp3"
    if not shutil.which("ffmpeg"):
        return None
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-vn", "-ab", "192k", "-ar", "44100", mp3_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return mp3_path

async def convert_to_mp3(video_path: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _convert_to_mp3_blocking, video_path)

# ================================
# دانلود و پردازش ویدیو
# ================================
def _download_tiktok_blocking(url: str) -> dict:
    ydl_opts = {
        "quiet": True,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
        "format": "mp4",
        "fragment_retries": 3,
        "retries": 3,
        "concurrent_fragment_downloads": 8,
        "http_headers": {
            "User-Agent": USER_AGENT,
            "Referer": "https://www.tiktok.com/"
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if not info:
            return None
        info['filename'] = ydl.prepare_filename(info)
        return info

# ================================
# هندلر اصلی TikTok
# ================================
async def tiktok_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    url = update.message.text.strip()

    if ("tiktok.com" not in url and 
        "vm.tiktok.com" not in url and 
        "vt.tiktok.com" not in url):
        return

    if update.effective_chat.type != "private":
        allowed = await is_admin(update, context)
        if not allowed:
            return

    msg = await update.message.reply_text("⬇️ در حال پردازش TikTok ...")
    chat_id = update.effective_chat.id

    if "vm.tiktok.com" in url or "vt.tiktok.com" in url:
        try:
            resp = requests.get(url, allow_redirects=True, headers={"User-Agent": USER_AGENT})
            url = resp.url
        except Exception as e:
            await msg.edit_text(f"❌ خطا در ریدایرکت لینک: {e}")
            return

    if "/photo/" in url:
        await msg.edit_text("❌ عکس‌های TikTok پشتیبانی نمی‌شوند.")
        return

    loop = asyncio.get_running_loop()
    try:
        info = await loop.run_in_executor(None, _download_tiktok_blocking, url)
        if not info:
            await msg.edit_text("❌ ویدیو یافت نشد یا دانلود ممکن نیست.")
            return

        filename = info['filename']
        video_id = info.get("id")
        video_store[video_id] = filename

        # دکمه‌ها عمودی
        keyboard = []
        if update.effective_chat.type == "private":
            keyboard.append([
                InlineKeyboardButton(
                    "➕ افزودن به گروه",
                    url="https://t.me/AFGR63_bot?startgroup=true"
                )
            ])
        keyboard.append([
            InlineKeyboardButton(
                "📥 دانلود صوتی",
                callback_data=f"tiktok_audio:{video_id}"
            )
        ])

        await context.bot.send_video(
            chat_id,
            filename,
            caption=f"🎬 {info.get('title', 'TikTok Video')}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود: {e}")

# ================================
# هندلر دانلود صوتی
# ================================
async def tiktok_audio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()

    video_id = cq.data.split(":")[1]
    if video_id not in video_store:
        return await cq.edit_message_text("❌ فایل ویدیو پیدا نشد.")

    video_path = video_store[video_id]
    mp3_path = await convert_to_mp3(video_path)

    if not mp3_path or not os.path.exists(mp3_path):
        return await cq.edit_message_text("❌ تبدیل به صوت ممکن نیست.")

    try:
        await context.bot.send_audio(
            cq.message.chat_id,
            mp3_path,
            caption="🎵 نسخه صوتی TikTok"
        )
    except Exception as e:
        await cq.edit_message_text(f"❌ خطا در ارسال صوت: {e}")
    finally:
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
