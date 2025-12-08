# modules/soundcloud_handler.py
import os
import asyncio
import yt_dlp
from concurrent.futures import ProcessPoolExecutor
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# ================================
# سودوها
# ================================
SUDO_USERS = [8588347189]   # ← آیدی شما

# ================================
# تنظیمات پایه
# ================================
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

COOKIE_FILE = "modules/youtube_cookie.txt"

# استفاده از ProcessPoolExecutor برای سرعت وحشی روی تمام هسته‌های CPU
executor = ProcessPoolExecutor(max_workers=os.cpu_count() or 4)

# ذخیره‌ی نتایج جستجو برای هر چت
track_store = {}

# ================================
# پیام‌ها سه زبانه
# ================================
LANG_MESSAGES = {
    "fa": {
        "searching": "🔍 در حال جستجو ... لطفاً صبر کنید",
        "downloading": "⬇️ در حال دانلود آهنگ...",
        "select_song": "🎵 {n} آهنگ پیدا شد — لطفاً انتخاب کنید:",
        "notfound": "❌ در SoundCloud چیزی پیدا نشد. در حال جستجو در یوتیوب...",
        "notfound_sc": "❌ در SoundCloud نتیجه‌ای یافت نشد.",
        "download_error": "❌ در دانلود آهنگ خطایی رخ داد.",
        "track_not_found": "❌ آهنگ پیدا نشد.",
    },
    "en": {
        "searching": "🔍 Searching... please wait",
        "downloading": "⬇️ Downloading...",
        "select_song": "🎵 {n} songs found — choose one:",
        "notfound": "❌ No results in SoundCloud. Searching YouTube...",
        "notfound_sc": "❌ No SoundCloud results.",
        "download_error": "❌ Error while downloading the track.",
        "track_not_found": "❌ Track not found.",
    },
    "ar": {
        "searching": "🔍 جاري البحث ... يرجى الانتظار",
        "downloading": "⬇️ جاري تنزيل الأغنية...",
        "select_song": "🎵 تم العثور على {n} أغنية — يرجى الاختيار:",
        "notfound": "❌ لا توجد نتائج في ساوند كلاود. يتم البحث في يوتيوب...",
        "notfound_sc": "❌ لا توجد نتائج في ساوند كلاود.",
        "download_error": "❌ حدث خطأ أثناء تنزيل الأغنية.",
        "track_not_found": "❌ لم يتم العثور على الأغنية.",
    },
}

# ================================
# تابع چک مدیر بودن
# ================================
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user

    # پیوی → همه مجاز
    if chat.type == "private":
        return True

    # سودو → همیشه مجاز
    if user and user.id in SUDO_USERS:
        return True

    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        admin_ids = [a.user.id for a in admins]
    except Exception:
        return False

    return user.id in admin_ids if user else False


# ================================
# تنظیمات مشترک yt_dlp (سریع و موازی)
# ================================
BASE_YTDLP_OPTS = {
    "quiet": True,
    "format": "bestaudio/best",
    "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s"),
    "noprogress": True,
    "nopart": True,
    "retries": 20,
    "fragment_retries": 20,
    "concurrent_fragment_downloads": 20,  # دانلود موازی قطعه‌ها → سرعت ماکس
    "overwrites": True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
}


# ================================
# کمک‌کننده: پیدا کردن مسیر mp3 از روی id
# ================================
def _find_mp3_by_id(track_id: str) -> str | None:
    """
    به صورت سریع در پوشه downloads دنبال فایلی می‌گردد که با id شروع شده و mp3 باشد.
    """
    expected = os.path.join(DOWNLOAD_FOLDER, f"{track_id}.mp3")
    if os.path.exists(expected):
        return expected

    # در صورتی که نام کمی متفاوت باشد اما id در ابتدای نام باشد
    for fname in os.listdir(DOWNLOAD_FOLDER):
        if fname.startswith(track_id) and fname.endswith(".mp3"):
            return os.path.join(DOWNLOAD_FOLDER, fname)

    return None


# ================================
# جستجو در SoundCloud (فوق‌سریع)
# ================================
def _sc_search_sync(query: str):
    # تعداد نتایج را کم کردیم برای سرعت بیشتر (۳ به‌جای ۱۰)
    opts = {"quiet": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(f"scsearch3:{query}", download=False)


# ================================
# دانلود از SoundCloud (بدون تبدیل جداگانه)
# ================================
def _sc_download_sync(webpage_url: str):
    opts = BASE_YTDLP_OPTS.copy()
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(webpage_url, download=True)
        track_id = info.get("id")
        mp3_path = _find_mp3_by_id(track_id) if track_id else None
        if not mp3_path:
            # fallback: اگر چیزی پیدا نشد، از prepare_filename
