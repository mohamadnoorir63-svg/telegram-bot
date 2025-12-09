import os
import asyncio
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
import json
import requests

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import os
# --- Audd.io API Key ---
AUDD_API_KEY = "1e24769c4b1e81d488e54e02e610de3d"

# ================================
# سودوها
# ================================
SUDO_USERS = [8588347189]

# ================================
# تنظیمات
# ================================
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

COOKIE_FILE = "modules/youtube_cookie.txt"

executor = ThreadPoolExecutor(max_workers=8)

track_store = {}

# ================================
# کش تلگرام
# ================================
CACHE_FILE = "data/custom_commands.json"
os.makedirs("data", exist_ok=True)

if not os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

with open(CACHE_FILE, "r", encoding="utf-8") as f:
    try:
        SC_CACHE = json.load(f)
    except json.JSONDecodeError:
        SC_CACHE = {}

def save_cache():
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(SC_CACHE, f, ensure_ascii=False, indent=2)

# ================================
# پیام‌ها
# ================================
LANG_MESSAGES = {
    "fa": {
        "searching": "🔍 در حال جستجو ...",
        "downloading": "⬇️ در حال دانلود...",
        "select_song": "🎵 {n} آهنگ پیدا شد — انتخاب کن:",
        "notfound": "❌ در SoundCloud چیزی پیدا نشد. جستجو در یوتیوب...",
    },
    "en": {
        "searching": "🔍 Searching...",
        "downloading": "⬇️ Downloading...",
        "select_song": "🎵 {n} songs found — choose one:",
        "notfound": "❌ No SoundCloud results. Searching YouTube...",
    },
    "ar": {
        "searching": "🔍 جاري البحث ...",
        "downloading": "⬇️ جاري التنزيل...",
        "select_song": "🎵 تم العثور على {n} أغنية — اختر:",
        "notfound": "❌ لا يوجد نتائج في ساوند كلاود. البحث في يوتيوب...",
    },
}

# ================================
# yt_dlp settings
# ================================
BASE_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    "noprogress": True,
    "nopart": True,
    "retries": 20,
    "fragment_retries": 20,
    "concurrent_fragment_downloads": 20,
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
# Admin check
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
        ids = [a.user.id for a in admins]
        return user.id in ids
    except Exception:
        return False

# ================================
# فایل کش لوکال
# ================================
def cache_check(id_: str):
    for file in os.listdir(DOWNLOAD_FOLDER):
        if file.startswith(id_) and file.endswith(".mp3"):
            return os.path.join(DOWNLOAD_FOLDER, file)
    return None

# ================================
# SoundCloud download
# ================================
def _sc_download_sync(url: str):
    opts = BASE_OPTS.copy()
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        track_id = str(info.get("id"))

        cached = cache_check(track_id)
        if cached:
            return info, cached

        fname = y.prepare_filename(info)
        mp3 = fname.rsplit(".", 1)[0] + ".mp3"
        return info, mp3

# ================================
# YouTube fallback
# ================================
def _youtube_fallback_sync(query: str):
    opts = BASE_OPTS.copy()
    if os.path.exists(COOKIE_FILE):
        opts["cookiefile"] = COOKIE_FILE

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(f"ytsearch1:{query}", download=True)
        if "entries" in info:
            info = info["entries"][0]

        vid = str(info.get("id"))
        cached = cache_check(vid)
        if cached:
            return info, cached

        fname = y.prepare_filename(info)
        return info, fname.rsplit(".", 1)[0] + ".mp3"

# ================================
# Trigger sender (برای voice/audio)
# ================================
async def fake_trigger(query, update, context):
    fake = update
    fake.message.text = "music " + query
    await soundcloud_handler(fake, context)

# ================================
# 🎧 تشخیص آهنگ از فایل صوتی
# ================================
# ================================
# 🎧 تشخیص آهنگ از فایل صوتی (نسخه دیباگ)
# ================================
async def audio_recognizer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not (update.message.audio or update.message.voice):
        return

    msg = await update.message.reply_text("🎧 در حال تشخیص آهنگ...")

    file = update.message.audio or update.message.voice
    tg_file = await file.get_file()
    path = f"tmp_{file.file_unique_id}.ogg"
    await tg_file.download_to_drive(path)

    # ارسال به Audd.io
    with open(path, "rb") as f:
        res = requests.post(
            "https://api.audd.io/",
            data={"api_token": AUDD_API_KEY, "return": "timecode"},
            files={"file": f}
        ).json()

    # حذف فایل موقت
    os.remove(path)

    # لاگ کامل پاسخ API برای دیباگ
    print("Audd.io API response:", res)

    if not res.get("result"):
        return await msg.edit_text(f"❌ نتونستم آهنگ رو تشخیص بدم.\n\nFull API response:\n{res}")

    title = res["result"]["title"]
    artist = res["result"]["artist"]

    await msg.edit_text(f"🎵 آهنگ شناسایی شد:\n{title} - {artist}\n\nدر حال جستجو...")

    query = f"{title} {artist}"
    await fake_trigger(query, update, context)
   
# ================================
# main SoundCloud handler
# ================================
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    triggers = ["آهنگ ", "music ", "اغنية ", "أغنية "]

    if not any(text.lower().startswith(t) for t in triggers):
        return

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    lang = "fa"
    query = ""
    for t in triggers:
        if text.lower().startswith(t):
            query = text[len(t):].strip()
            lang = "en" if t.startswith("music") else ("ar" if "غ" in t else "fa")
            break

    msg = await update.message.reply_text(LANG_MESSAGES[lang]["searching"])

    def _search():
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch3:{query}", download=False)

    loop = asyncio.get_running_loop()
    sc_info = await loop.run_in_executor(executor, _search)

    if not sc_info or not sc_info.get("entries"):
        await msg.edit_text(LANG_MESSAGES[lang]["notfound"])

        try:
            info, mp3 = await loop.run_in_executor(
                executor, _youtube_fallback_sync, query
            )
        except Exception as e:
            return await msg.edit_text(f"❌ خطا:\n{e}")

        vid = str(info.get("id"))
        key = f"yt_{vid}"

        if key in SC_CACHE:
            try: await msg.delete()
            except: pass
            return await update.message.reply_audio(SC_CACHE[key], caption=info.get("title"))

        try:
            with open(mp3, "rb") as f:
                sent = await update.message.reply_audio(f, caption=info.get("title"))
        except Exception as e:
            return await msg.edit_text(f"❌ خطا:\n{e}")
        finally:
            if os.path.exists(mp3): os.remove(mp3)

        SC_CACHE[key] = sent.audio.file_id
        save_cache()
        try: await msg.delete()
        except: pass
        return

    entries = sc_info["entries"]
    track_store[update.effective_chat.id] = entries

    keyboard = [
        [InlineKeyboardButton(t["title"], callback_data=f"music_select:{t['id']}")]
        for t in entries
    ]

    await msg.edit_text(
        LANG_MESSAGES[lang]["select_song"].format(n=len(entries)),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ================================
# انتخاب آهنگ
# ================================
async def music_select_handler(update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    chat = cq.message.chat_id

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    tid = cq.data.split(":")[1]
    key = f"sc_{tid}"

    if key in SC_CACHE:
        return await context.bot.send_audio(chat, SC_CACHE[key])

    tracks = track_store.get(chat, [])
    track = next((t for t in tracks if str(t["id"]) == tid), None)

    if not track:
        return await cq.edit_message_text("❌ آهنگ پیدا نشد.")

    msg = await cq.edit_message_text("⬇️ در حال دانلود...")

    loop = asyncio.get_running_loop()
    try:
        info, mp3 = await loop.run_in_executor(executor, _sc_download_sync, track["webpage_url"])
    except Exception as e:
        return await msg.edit_text(f"❌ خطا:\n{e}")

    try:
        with open(mp3, "rb") as f:
            sent = await context.bot.send_audio(chat, f, caption=info.get("title"))
    except Exception as e:
        return await msg.edit_text(f"❌ خطا:\n{e}")

    SC_CACHE[key] = sent.audio.file_id
    save_cache()

    try: await msg.delete()
    except: pass
