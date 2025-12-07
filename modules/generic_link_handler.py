# modules/generic_link_handler.py
import os
import re
import uuid
import shutil
import subprocess
import yt_dlp
import asyncio
from typing import Optional, Tuple
from telegram import Update
from telegram.ext import ContextTypes

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# regex ساده برای استخراج اولین URL از متن
URL_RE = re.compile(r"https?://[^\s]+")

def _safe_outtmpl():
    # قالب خروجی یکتا برای جلوگیری از تداخل نام‌ها
    return os.path.join(DOWNLOAD_FOLDER, "%(id)s_%(title).50s_%(uuid)s.%(ext)s")

def _blocking_download(url: str) -> Tuple[dict, str]:
    """
    اجرا در threadpool — دانلود با yt_dlp.
    برمی‌گرداند: (info_dict, filename)
    در صورت خطا استثنا پرتاب می‌کند.
    """
    # پارامتر uuid را به ydl اضافه می‌کنیم تا prepare_filename درست کار کند
    uuid_token = uuid.uuid4().hex
    ydl_opts = {
        "format": "best",                    # بهترین فرمت (video/audio)
        "outtmpl": _safe_outtmpl().replace("%(uuid)s", uuid_token),
        "noplaylist": False,                 # اگر پلی‌لیست بود می‌توانیم چندتا دانلود کنیم (یا محدود کنیم)
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": False,
        "cachedir": False,
        # اگر بخوای سرعت/اندازه محدود بشه میشه اینجا تنظیم کرد
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        # yt_dlp برای یک ویدیو dict برمی‌گرداند؛ برای پلی‌لیست dict با key "entries"
        if info is None:
            raise RuntimeError("yt-dlp returned no info")

        # اگر لیست (playlist) باشه، ما اولین مورد دانلود‌شده را باز می‌گردونیم
        if "entries" in info and info["entries"]:
            # find the first downloaded entry with a file on disk
            for entry in info["entries"]:
                try:
                    filename = ydl.prepare_filename(entry)
                    if os.path.exists(filename):
                        return entry, filename
                except Exception:
                    continue
            # fallback — اگر هیچ فایلی پیدا نشد، خطا
            raise RuntimeError("No file downloaded from playlist entries")
        else:
            filename = ydl.prepare_filename(info)
            if not os.path.exists(filename):
                # گاهی yt-dlp نام فایل تفاوت داره — تلاش برای یافتن نزدیک‌ترین فایل
                possible = [p for p in os.listdir(DOWNLOAD_FOLDER) if p.startswith(info.get("id", ""))]
                if possible:
                    filename = os.path.join(DOWNLOAD_FOLDER, possible[0])
                else:
                    raise RuntimeError("Downloaded file not found on disk")
            return info, filename

async def convert_to_mp3_if_needed(file_path: str) -> Optional[str]:
    """
    اگر فایل صوتی نیست ولی می‌توان MP3 ساخت، آن را می‌سازد (اختیاری).
    این تابع synchronous کار می‌کند اما سریع است؛ از subprocess استفاده می‌کند.
    اگر ffmpeg نصب نباشد None برمی‌گرداند.
    """
    ext = file_path.rsplit(".", 1)[-1].lower()
    audio_exts = {"mp3", "m4a", "aac", "ogg", "wav", "opus"}
    if ext in audio_exts:
        return file_path  # خودش صوت است
    # نیاز به ffmpeg
    if not shutil.which("ffmpeg"):
        return None
    mp3_path = file_path.rsplit(".", 1)[0] + ".mp3"
    cmd = ["ffmpeg", "-y", "-i", file_path, "-vn", "-ab", "192k", "-ar", "44100", mp3_path]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(mp3_path):
        return mp3_path
    return None

def _is_video_ext(ext: str) -> bool:
    return ext.lower() in {"mp4", "mkv", "webm", "mov", "flv"}

def _is_audio_ext(ext: str) -> bool:
    return ext.lower() in {"mp3", "m4a", "aac", "ogg", "wav", "opus"}

async def generic_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    هندلر اصلی — اگر پیام شامل لینک باشه سعی می‌کنه دانلود کنه و ارسال کنه.
    ثبت در application:
      MessageHandler(filters.TEXT & ~filters.COMMAND, generic_link_handler)
    """
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    # استخراج اولین URL
    m = URL_RE.search(text)
    if not m:
        return  # لینک پیدا نشد، نادیده بگیر

    url = m.group(0)
    chat_id = update.effective_chat.id

    msg = await update.message.reply_text("⬇️ لینک دریافت شد — بررسی و تلاش برای دانلود …")

    loop = asyncio.get_running_loop()
    try:
        # اجرای blocking download در threadpool
        info, filename = await loop.run_in_executor(None, _blocking_download, url)

        # تصمیم درباره نوع فایل بر اساس پسوند
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        title = info.get("title") if isinstance(info, dict) else None
        caption = f"📥 دانلود کامل شد\n<b>{title or os.path.basename(filename)}</b>"

        # اگر ویدئو باشد
        if _is_video_ext(ext):
            await context.bot.send_video(chat_id=chat_id, video=open(filename, "rb"), caption=caption, parse_mode="HTML")
        # اگر صوت باشد
        elif _is_audio_ext(ext):
            await context.bot.send_audio(chat_id=chat_id, audio=open(filename, "rb"), caption=caption, parse_mode="HTML")
        else:
            # تلاش برای تبدیل به mp3 اگر قابل انجام بود
            mp3 = await convert_to_mp3_if_needed(filename)
            if mp3 and os.path.exists(mp3):
                await context.bot.send_audio(chat_id=chat_id, audio=open(mp3, "rb"), caption=caption, parse_mode="HTML")
                try:
                    os.remove(mp3)
                except:
                    pass
            else:
                # ارسال به عنوان سند
                await context.bot.send_document(chat_id=chat_id, document=open(filename, "rb"), caption=caption, parse_mode="HTML")

        # پاکسازی فایل محلی
        try:
            os.remove(filename)
        except:
            pass

        await msg.delete()

    except yt_dlp.utils.DownloadError as e:
        # پیام ریز yt-dlp معمولاً علت auth/cookies است
        await msg.edit_text(f"❌ خطا در دانلود: {e}")
    except Exception as e:
        await msg.edit_text(f"❌ خطا: {e}")
