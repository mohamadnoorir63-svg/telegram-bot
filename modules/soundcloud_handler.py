# modules/soundcloud_handler.py

import os
import asyncio
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
import json
from typing import Optional

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.ext import ContextTypes

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
executor = ThreadPoolExecutor(max_workers=6)  # برای سرعت بهتر
track_store = {}

# ================================
# کش تلگرام
# ================================
CACHE_FILE = "data/sc_cache.json"
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
        "searching": "🔍 در حال جستجو...",
        "downloading": "⌛ در حال دانلود...",
        "select_song": "🎵 {n} آهنگ پیدا شد — لطفاً انتخاب کنید:",
        "notfound": "⚠️ نتیجه‌ای پیدا نشد!",
    }
}

# ================================
# yt_dlp
# ================================
BASE_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "outtmpl": f"{DOWNLOAD_FOLDER}/%(id)s.%(ext)s",
    "noprogress": True,
    "nopart": True,
    "retries": 5,
    "fragment_retries": 5,
    "concurrent_fragment_downloads": 4,
    "overwrites": True,
    "postprocessors": [
        {"key": "FFmpegExtractAudio","preferredcodec": "mp3","preferredquality": "128"}
    ],
}

# ================================
# بررسی مدیر بودن
# ================================
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        return True
    if user and user.id in SUDO_USERS:
        return True
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        ids = [a.user.id for a in admins]
        return user.id in ids
    except Exception:
        return False

# ================================
# چک کش محلی
# ================================
def cache_check(id_: str) -> Optional[str]:
    for file in os.listdir(DOWNLOAD_FOLDER):
        if file.startswith(id_) and file.endswith(".mp3"):
            return os.path.join(DOWNLOAD_FOLDER, file)
    return None

# ================================
# دانلود SoundCloud
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
# fallback یوتیوب
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
        mp3 = fname.rsplit(".", 1)[0] + ".mp3"
        return info, mp3

# ================================
# هندلر پیام عادی
# ================================
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    triggers = ["آهنگ ","music ","اغنية ","أغنية ","موزیک ","داستان ","Music ","Musik ","اهنگ "]
    if not any(text.lower().startswith(t) for t in triggers):
        return

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    query = next((text[len(t):].strip() for t in triggers if text.lower().startswith(t)), "")
    msg = await update.message.reply_text(LANG_MESSAGES["fa"]["searching"])

    def _search(): 
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch8:{query}", download=False)

    loop = asyncio.get_running_loop()
    try:
        sc_info = await loop.run_in_executor(executor, _search)
    except Exception as e:
        await msg.edit_text(f"❌ خطا در جستجو:\n{e}")
        return

    if not sc_info or not sc_info.get("entries"):
        await msg.edit_text(LANG_MESSAGES["fa"]["notfound"])
        return

    # ذخیره نتایج
    entries = {str(t["id"]): t for t in sc_info["entries"]}
    track_store[update.message.message_id] = entries

    keyboard = [[InlineKeyboardButton(t["title"], callback_data=f"music_select:{update.message.message_id}:{t_id}")] for t_id,t in entries.items()]
    await msg.edit_text(LANG_MESSAGES["fa"]["select_song"].format(n=len(entries)),
                        reply_markup=InlineKeyboardMarkup(keyboard))

# ================================
# callback دکمه‌ها
# ================================
async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    chat_id = cq.message.chat.id

    try:
        _, msg_id, track_id = cq.data.split(":")
    except:
        return await cq.edit_message_text("❌ خطا در callback.")

    tracks = track_store.get(int(msg_id), {})
    track = tracks.get(track_id)
    if not track:
        return await cq.edit_message_text("❌ آهنگ پیدا نشد.")

    cache_key = f"sc_{track_id}"
    if cache_key in SC_CACHE:
        try: await cq.edit_message_text("⚡ ارسال از کش...")
        except: pass
        return await context.bot.send_audio(chat_id, SC_CACHE[cache_key])

    msg = await cq.edit_message_text(LANG_MESSAGES["fa"]["downloading"])
    loop = asyncio.get_running_loop()
    try:
        info, mp3 = await loop.run_in_executor(executor, _sc_download_sync, track["webpage_url"])
    except Exception as e:
        return await msg.edit_text(f"❌ خطا در دانلود:\n{e}")

    try:
        with open(mp3,"rb") as f:
            keyboard = [[InlineKeyboardButton("➕ افزودن به گروه", url="https://t.me/AFGR63_bot?startgroup=true")]] if update.effective_chat.type=="private" else None
            sent = await context.bot.send_audio(chat_id,f,
                caption=f"🎵 {info.get('title','Music')}\n\n📥 <a href='https://t.me/AFGR63_bot'>دانلود موزیک</a>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
            )
    finally:
        if os.path.exists(mp3): os.remove(mp3)

    SC_CACHE[cache_key] = sent.audio.file_id
    save_cache()
    try: await msg.delete()
    except: pass

# ================================
# هندلر جستجوی inline
# ================================
async def inline_sc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    if not query:
        return

    def _search(): 
        with yt_dlp.YoutubeDL({"quiet": True}) as y:
            return y.extract_info(f"scsearch5:{query}", download=False)

    loop = asyncio.get_running_loop()
    try:
        sc_info = await loop.run_in_executor(executor, _search)
    except:
        return

    results = []
    for t in sc_info.get("entries", [])[:5]:
        track_id = str(t["id"])
        track_store[f"inline_{track_id}"] = t
        results.append(
            InlineQueryResultArticle(
                id=track_id,
                title=t["title"],
                input_message_content=InputTextMessageContent(f"دانلود {t['title']}"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("دانلود", callback_data=f"music_inline:{track_id}")]])
            )
        )
    await update.inline_query.answer(results, cache_time=10)
