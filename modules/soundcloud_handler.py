import os
import asyncio
import yt_dlp
import json
import uuid
from concurrent.futures import ThreadPoolExecutor

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

DATA_FOLDER = "data"
DOWNLOAD_FOLDER = "downloads"
CACHE_FILE = os.path.join(DATA_FOLDER, "sc_cache.json")

os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

try:
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        SC_CACHE = json.load(f)
except:
    SC_CACHE = {}

executor = ThreadPoolExecutor(max_workers=4)
track_store = {}

MUSIC_CAPTION = "🎵 دانلود موزیک با ربات @AFGR63_bot"

ADD_BTN = InlineKeyboardMarkup([
    [InlineKeyboardButton("➕ افزودن ربات به گروه", url="https://t.me/AFGR63_bot?startgroup=true")]
])

BASE_OPTS = {
    "format": "bestaudio[filesize<48M]/bestaudio[filesize_approx<48M]/worstaudio/best",
    "quiet": True,
    "no_warnings": True,
    "noprogress": True,
    "nopart": True,
    "noplaylist": True,
    "overwrites": True,
    "socket_timeout": 20,
    "retries": 2,
    "fragment_retries": 2,
    "concurrent_fragment_downloads": 4,
}


def save_cache():
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(SC_CACHE, f, indent=2, ensure_ascii=False)


def clean_file(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except:
        pass


def get_real_file(path):
    if path and os.path.exists(path):
        return path

    base = os.path.splitext(path)[0]
    for ext in ["mp3", "m4a", "webm", "opus"]:
        p = base + "." + ext
        if os.path.exists(p):
            return p

    return path


def _search_sc(query):
    with yt_dlp.YoutubeDL({
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "socket_timeout": 15,
    }) as y:
        return y.extract_info(f"scsearch8:{query}", download=False)


def _download_audio(url):
    file_key = str(uuid.uuid4())
    opts = BASE_OPTS.copy()
    opts["outtmpl"] = os.path.join(DOWNLOAD_FOLDER, f"{file_key}.%(ext)s")

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        path = get_real_file(y.prepare_filename(info))
        return info, path


def _youtube_fallback_sync(query):
    file_key = str(uuid.uuid4())
    opts = BASE_OPTS.copy()
    opts["outtmpl"] = os.path.join(DOWNLOAD_FOLDER, f"{file_key}.%(ext)s")

    cookie_file = os.path.join("modules", "youtube_cookie.txt")
    if os.path.exists(cookie_file):
        opts["cookiefile"] = cookie_file

    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(f"ytsearch1:{query}", download=True)

        if "entries" in info and info["entries"]:
            info = info["entries"][0]

        path = get_real_file(y.prepare_filename(info))
        return info, path


async def send_audio_file(context, chat_id, path, title, reply_markup=None):
    if not path or not os.path.exists(path):
        return None

    if os.path.getsize(path) > 49 * 1024 * 1024:
        return None

    with open(path, "rb") as audio:
        return await context.bot.send_audio(
            chat_id=chat_id,
            audio=audio,
            title=title or "Music",
            caption=MUSIC_CAPTION,
            reply_markup=reply_markup,
            read_timeout=180,
            write_timeout=180,
            connect_timeout=60,
        )


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
        result = await asyncio.wait_for(
            loop.run_in_executor(executor, _search_sc, query),
            timeout=25
        )
    except:
        result = None

    if not result or not result.get("entries"):
        await msg.edit_text("🔁 SoundCloud نتیجه نداشت، جستجو در YouTube...")

        path = None

        try:
            info, path = await asyncio.wait_for(
                loop.run_in_executor(executor, _youtube_fallback_sync, query),
                timeout=100
            )

            sent = await send_audio_file(
                context,
                update.effective_chat.id,
                path,
                info.get("title") or "Music",
                ADD_BTN if update.effective_chat.type == "private" else None
            )

            if not sent:
                return await msg.edit_text("❌ فایل بزرگ است یا تلگرام قبول نکرد.")

            if sent.audio:
                SC_CACHE[f"yt_{info.get('id')}"] = sent.audio.file_id
                save_cache()

            await msg.delete()

        except asyncio.TimeoutError:
            await msg.edit_text("⏳ دانلود طول کشید. آهنگ دیگری امتحان کن.")
        except Exception as e:
            await msg.edit_text(f"❌ خطا در دانلود:\n{e}")
        finally:
            clean_file(path)

        return

    entries = []
    for item in result.get("entries", []):
        if not item:
            continue

        tid = str(item.get("id") or uuid.uuid4())
        title = item.get("title") or "Unknown"
        url = item.get("url") or item.get("webpage_url")

        if url:
            entries.append((tid, title, url))

    if not entries:
        return await msg.edit_text("❌ نتیجه‌ای پیدا نشد.")

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
    await cq.answer("⚡ در حال آماده‌سازی...")

    try:
        _, msg_id, tid = cq.data.split(":", 2)
        msg_id = int(msg_id)
    except:
        return await cq.message.reply_text("❌ دکمه خراب است.")

    track = track_store.get(msg_id, {}).get(tid)

    if not track:
        return await cq.message.reply_text("❌ آهنگ پیدا نشد. دوباره جستجو کن.")

    cache_key = f"sc_{tid}"
    chat_id = cq.message.chat.id

    if cache_key in SC_CACHE:
        return await context.bot.send_audio(
            chat_id=chat_id,
            audio=SC_CACHE[cache_key],
            caption=MUSIC_CAPTION,
            reply_markup=ADD_BTN if cq.message.chat.type == "private" else None,
        )

    msg = await cq.edit_message_text("⚡ در حال دانلود مستقیم...")

    path = None

    try:
        loop = asyncio.get_running_loop()

        info, path = await asyncio.wait_for(
            loop.run_in_executor(executor, _download_audio, track["url"]),
            timeout=100
        )

        title = info.get("title") or track.get("title") or "Music"

        sent = await send_audio_file(
            context,
            chat_id,
            path,
            title,
            ADD_BTN if cq.message.chat.type == "private" else None
        )

        if not sent:
            return await msg.edit_text("❌ فایل بزرگ است یا تلگرام قبول نکرد.")

        if sent.audio:
            SC_CACHE[cache_key] = sent.audio.file_id
            save_cache()

        await msg.delete()

    except asyncio.TimeoutError:
        await msg.edit_text("⏳ دانلود طول کشید. یک نتیجه دیگر انتخاب کن.")

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود:\n{e}")

    finally:
        clean_file(path)
