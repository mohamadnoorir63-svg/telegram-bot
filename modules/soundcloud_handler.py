# modules/soundcloud_handler.py
import os, shutil, subprocess, yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# حافظه موقت برای نتایج جستجو با صفحه‌بندی
track_store = {}  # {chat_id: {"tracks": [...], "page": 0}}

async def convert_to_mp3(file_path: str) -> str:
    mp3_path = file_path.rsplit(".", 1)[0] + ".mp3"
    if not shutil.which("ffmpeg"):
        return None
    cmd = [
        "ffmpeg", "-y", "-i", file_path,
        "-vn", "-ab", "192k", "-ar", "44100",
        "-f", "mp3", mp3_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return mp3_path

# نمایش یک صفحه از نتایج
def build_keyboard(chat_id: int):
    store = track_store[chat_id]
    tracks = store["tracks"]
    page = store["page"]
    per_page = 5
    start = page * per_page
    end = start + per_page

    keyboard = []
    for i, track in enumerate(tracks[start:end], start=start):
        title = track.get("title", "SoundCloud Track")
        keyboard.append([InlineKeyboardButton(f"{i+1}. {title}", callback_data=f"music_select:{i}")])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data="music_page:prev"))
    if end < len(tracks):
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data="music_page:next"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    return InlineKeyboardMarkup(keyboard)

async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.effective_chat.id

    if not text.lower().startswith("آهنگ "):
        return

    query = text.replace("آهنگ ", "", 1).strip()
    if not query:
        await update.message.reply_text("❌ لطفاً نام یا متن آهنگ را وارد کنید.")
        return

    msg = await update.message.reply_text("🔍 در حال جستجو در SoundCloud...")

    ydl_opts = {"format": "bestaudio/best", "quiet": True, "noplaylist": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"scsearch50:{query}", download=False)  # تا 50 نتیجه
            if not info or "entries" not in info or not info["entries"]:
                await msg.edit_text("❌ آهنگ پیدا نشد.")
                return

            tracks = info["entries"]
            track_store[chat_id] = {"tracks": tracks, "page": 0}

            await msg.edit_text(
                f"🎵 {len(tracks)} آهنگ پیدا شد، یکی را انتخاب کنید:",
                reply_markup=build_keyboard(chat_id)
            )

    except Exception as e:
        await msg.edit_text(f"❌ خطا در جستجوی موزیک:\n{e}")

# هندلر انتخاب آهنگ
async def music_select_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    if query.data.startswith("music_select:"):
        idx = int(query.data.split(":")[1])
        if chat_id not in track_store or idx >= len(track_store[chat_id]["tracks"]):
            await query.edit_message_text("❌ آهنگ پیدا نشد یا منقضی شده.")
            return

        track = track_store[chat_id]["tracks"][idx]
        track_id = track.get("id")
        title = track.get("title", "SoundCloud Track")

        msg = await query.edit_message_text(f"⬇️ در حال دانلود: {title} ... لطفا صبر کنید.")
        ydl_opts = {"format": "bestaudio/best", "quiet": True, "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(id)s.%(ext)s")}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://soundcloud.com/i/tracks/{track_id}", download=True)
                filename = ydl.prepare_filename(info)

            mp3_path = await convert_to_mp3(filename)
            if mp3_path and os.path.exists(mp3_path):
                await context.bot.send_audio(chat_id, mp3_path, caption=f"🎵 {title}")
                os.remove(mp3_path)
            else:
                await context.bot.send_document(chat_id, filename, caption=f"🎵 {title}")

            if os.path.exists(filename):
                os.remove(filename)

            await msg.delete()
        except Exception as e:
            await query.edit_message_text(f"❌ خطا در دانلود آهنگ:\n{e}")

    elif query.data.startswith("music_page:"):
        direction = query.data.split(":")[1]
        store = track_store[chat_id]
        if direction == "next":
            store["page"] += 1
        elif direction == "prev":
            store["page"] -= 1
        await query.edit_message_reply_markup(reply_markup=build_keyboard(chat_id))
