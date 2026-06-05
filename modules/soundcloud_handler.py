import os
import asyncio
import yt_dlp
import json
import uuid
from concurrent.futures import ThreadPoolExecutor

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

SUDO_USERS = [8588347189]

DATA_FOLDER = "data"
DOWNLOAD_FOLDER = "downloads"
CACHE_FILE = os.path.join(DATA_FOLDER, "sc_cache.json")

os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            SC_CACHE = json.load(f)
    except:
        SC_CACHE = {}
else:
    SC_CACHE = {}

executor = ThreadPoolExecutor(max_workers=6)
track_store = {}

MUSIC_CAPTION = "[دانلود موزیک با ربات](https://t.me/AFGR63_bot)"

ADD_BTN = InlineKeyboardMarkup([
    [InlineKeyboardButton("➕ افزودن ربات به گروه", url="https://t.me/AFGR63_bot?startgroup=true")]
])


def save_cache():
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(SC_CACHE, f, indent=2, ensure_ascii=False)


def clean_file(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except:
        pass


def safe_title(name):
    return "".join(c for c in name if c.isalnum() or c in " ._-")[:60] or "music"


BASE_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "noprogress": True,
    "nopart": True,
    "noplaylist": True,
    "overwrites": True,
    "socket_timeout": 25,
    "retries": 3,
    "fragment_retries": 3,
    "format": "bestaudio/best",
}


def _search_soundcloud(query):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "socket_timeout": 20,
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(f"scsearch8:{query}", download=False)


def _download_audio(url):
    file_key = str(uuid.uuid4())

    opts = BASE_OPTS.copy()
    opts["outtmpl"] = os.path.join(DOWNLOAD_FOLDER, f"{file_key}.%(ext)s")

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)

        if not os.path.exists(file_path):
            base = os.path.splitext(file_path)[0]
            for ext in ["mp3", "m4a", "webm", "opus"]:
                test = base + "." + ext
                if os.path.exists(test):
                    file_path = test
                    break

        return info, file_path


def _youtube_fallback_sync(query):
    file_key = str(uuid.uuid4())

    opts = BASE_OPTS.copy()
    opts["outtmpl"] = os.path.join(DOWNLOAD_FOLDER, f"{file_key}.%(ext)s")

    cookie_file = os.path.join("modules", "youtube_cookie.txt")
    if os.path.exists(cookie_file):
        opts["cookiefile"] = cookie_file

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"ytsearch1:{query}", download=True)

        if "entries" in info and info["entries"]:
            info = info["entries"][0]

        file_path = ydl.prepare_filename(info)

        if not os.path.exists(file_path):
            base = os.path.splitext(file_path)[0]
            for ext in ["mp3", "m4a", "webm", "opus"]:
                test = base + "." + ext
                if os.path.exists(test):
                    file_path = test
                    break

        return info, file_path


async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    low = text.lower()

    triggers = ["آهنگ ", "اهنگ ", "music ", "musik ", "موزیک ", "اغنية ", "أغنية "]

    if not any(low.startswith(t.lower()) for t in triggers):
        return

    query = ""
    for t in triggers:
        if low.startswith(t.lower()):
            query = text[len(t):].strip()
            break

    if not query:
        return await update.message.reply_text("🎵 اسم آهنگ را بنویس.")

    msg = await update.message.reply_text("🔍 در حال جستجو...")

    loop = asyncio.get_running_loop()

    try:
        result = await loop.run_in_executor(executor, _search_soundcloud, query)
    except:
        result = None

    if not result or not result.get("entries"):
        await msg.edit_text("🔁 در SoundCloud پیدا نشد؛ جستجو در YouTube...")

        try:
            info, file_path = await loop.run_in_executor(executor, _youtube_fallback_sync, query)
        except Exception as e:
            return await msg.edit_text(f"❌ آهنگ پیدا نشد:\n{e}")

        if not file_path or not os.path.exists(file_path):
            return await msg.edit_text("❌ فایل آهنگ دانلود نشد.")

        try:
            with open(file_path, "rb") as audio:
                sent = await context.bot.send_audio(
                    chat_id=update.effective_chat.id,
                    audio=audio,
                    caption=MUSIC_CAPTION,
                    parse_mode="MarkdownV2",
                    title=info.get("title") or "Music",
                    reply_markup=ADD_BTN if update.effective_chat.type == "private" else None,
                    read_timeout=120,
                    write_timeout=120,
                    connect_timeout=60,
                )

            if sent.audio:
                SC_CACHE[f"yt_{info.get('id')}"] = {
                    "file_id": sent.audio.file_id,
                    "caption": MUSIC_CAPTION,
                }
                save_cache()

            await msg.delete()

        except Exception as e:
            await msg.edit_text(f"❌ خطا در ارسال آهنگ:\n{e}")

        finally:
            clean_file(file_path)

        return

    entries = []
    for item in result.get("entries", []):
        if not item:
            continue

        tid = str(item.get("id") or uuid.uuid4())
        title = item.get("title") or "Unknown"
        url = item.get("url") or item.get("webpage_url")

        if not url:
            continue

        entries.append((tid, title, url))

    if not entries:
        return await msg.edit_text("❌ نتیجه قابل دانلود پیدا نشد.")

    entries = entries[:8]

    track_store[update.message.message_id] = {
        tid: {"title": title, "url": url}
        for tid, title, url in entries
    }

    keyboard = [
        [InlineKeyboardButton(title[:55], callback_data=f"music_select:{update.message.message_id}:{tid}")]
        for tid, title, url in entries
    ]

    await msg.edit_text("🎶 یکی را انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))


async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer("⏳ در حال آماده‌سازی...")

    try:
        _, msg_id, tid = cq.data.split(":", 2)
        msg_id = int(msg_id)
    except:
        return await cq.message.reply_text("❌ داده دکمه خراب است.")

    track = track_store.get(msg_id, {}).get(tid)

    if not track:
        return await cq.message.reply_text("❌ آهنگ پیدا نشد. دوباره جستجو کن.")

    cache_key = f"sc_{tid}"
    chat_id = cq.message.chat.id

    if cache_key in SC_CACHE:
        cached = SC_CACHE[cache_key]
        return await context.bot.send_audio(
            chat_id=chat_id,
            audio=cached["file_id"],
            caption=cached.get("caption", MUSIC_CAPTION),
            parse_mode="MarkdownV2",
            reply_markup=ADD_BTN if cq.message.chat.type == "private" else None,
        )

    msg = await cq.edit_message_text("⚡ در حال دانلود آهنگ...")

    file_path = None

    try:
        loop = asyncio.get_running_loop()
        info, file_path = await loop.run_in_executor(executor, _download_audio, track["url"])

        if not file_path or not os.path.exists(file_path):
            return await msg.edit_text("❌ فایل دانلود نشد.")

        title = info.get("title") or track.get("title") or "Music"

        with open(file_path, "rb") as audio:
            sent = await context.bot.send_audio(
                chat_id=chat_id,
                audio=audio,
                caption=MUSIC_CAPTION,
                parse_mode="MarkdownV2",
                title=title,
                reply_markup=ADD_BTN if cq.message.chat.type == "private" else None,
                read_timeout=120,
                write_timeout=120,
                connect_timeout=60,
            )

        if sent.audio:
            SC_CACHE[cache_key] = {
                "file_id": sent.audio.file_id,
                "caption": MUSIC_CAPTION,
            }
            save_cache()

        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود:\n{e}")

    finally:
        clean_file(file_path)
