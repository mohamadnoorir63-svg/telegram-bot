# modules/soundcloud_handler.py
import os, re, shutil, subprocess, yt_dlp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from rapidfuzz import fuzz

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def clean_text(t: str):
    t = t.lower()
    t = re.sub(r"[^\w\s]", " ", t)
    t = t.replace("آهنگ", "").replace("موزیک","")
    t = re.sub(r"\s+", " ", t)
    return t.strip()

async def convert_to_mp3(path: str):
    mp3 = path.rsplit(".", 1)[0] + ".mp3"
    if not shutil.which("ffmpeg"):
        return None
    subprocess.run(["ffmpeg","-y","-i",path,"-vn","-ab","192k","-ar","44100",mp3], 
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return mp3

# حافظه نتایج برای صفحه‌بندی
track_store = {}

def best_match(search_text, tracks):
    """بهترین تطابق fuzzy از میان نتایج"""
    search_clean = clean_text(search_text)
    scored = []
    for t in tracks:
        title = clean_text(t.get("title",""))
        score = fuzz.partial_ratio(search_clean, title)
        scored.append((score, t))
    scored.sort(reverse=True, key=lambda x: x[0])
    return scored[:30]  # حداکثر ۳۰ نتیجه قوی

async def soundcloud_handler(update:Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_chat.id

    if not text.startswith("آهنگ "):
        return

    query = clean_text(text.replace("آهنگ ", ""))

    msg = await update.message.reply_text("🔍 در حال جستجو در چند منبع ...")

    ydl_opts = {"quiet":True, "noplaylist":True}

    try:
        all_results = []

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            sc = ydl.extract_info(f"scsearch50:{query}", download=False)
            yt = ydl.extract_info(f"ytsearch50:{query}", download=False)

        if sc and "entries" in sc:
            all_results.extend(sc["entries"])
        if yt and "entries" in yt:
            all_results.extend(yt["entries"])

        if not all_results:
            await msg.edit_text("❌ آهنگی یافت نشد.")
            return

        # انتخاب نتایج بهتر با fuzzy match
        best = [t for _, t in best_match(query, all_results)]
        track_store[chat_id] = {"tracks": best, "page": 0}

        # دکمه انتخاب
        def build_page():
            page = track_store[chat_id]["page"]
            start = page * 5
            end = start + 5

            kb = []
            for i, t in enumerate(best[start:end], start=start):
                kb.append([InlineKeyboardButton(
                    f"{i+1}. {t.get('title')[:50]}",
                    callback_data=f"music_dl:{i}"
                )])

            nav = []
            if page > 0: nav.append(InlineKeyboardButton("⬅️", callback_data="page:prev"))
            if end < len(best): nav.append(InlineKeyboardButton("➡️", callback_data="page:next"))
            if nav: kb.append(nav)

            return InlineKeyboardMarkup(kb)

        await msg.edit_text("🎶 نتایج یافت‌شده:", reply_markup=build_page())

    except Exception as e:
        await msg.edit_text(f"❌ خطا:\n{e}")

async def music_select_handler(update, context):
    q = update.callback_query
    await q.answer()
    chat = q.message.chat_id
    data = q.data

    if data.startswith("page:"):
        if data=="page:next":
            track_store[chat]["page"] += 1
        else:
            track_store[chat]["page"] -= 1

        page = track_store[chat]["page"]
        tracks = track_store[chat]["tracks"]

        kb = []
        start = page*5
        end = start+5
        for i, t in enumerate(tracks[start:end], start=start):
            kb.append([InlineKeyboardButton(
                f"{i+1}. {t.get('title','')[:50]}",
                callback_data=f"music_dl:{i}"
            )])

        nav=[]
        if page>0: nav.append(InlineKeyboardButton("⬅️", callback_data="page:prev"))
        if end<len(tracks): nav.append(InlineKeyboardButton("➡️", callback_data="page:next"))
        if nav: kb.append(nav)

        await q.edit_message_reply_markup(InlineKeyboardMarkup(kb))
        return

    if data.startswith("music_dl:"):
        idx = int(data.split(":")[1])
        track = track_store[chat]["tracks"][idx]
        title = track.get("title","Track")
        url = track.get("webpage_url")

        msg = await q.edit_message_text(f"⬇ در حال دانلود {title} ...")

        ydl_opts = {"format":"bestaudio/best","quiet":True,"outtmpl":"downloads/%(id)s.%(ext)s"}

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            mp3 = await convert_to_mp3(filename)
            if mp3 and os.path.exists(mp3):
                await context.bot.send_audio(chat, mp3, caption=f"🎵 {title}")
                os.remove(mp3)
            else:
                await context.bot.send_document(chat, filename)

            if os.path.exists(filename):
                os.remove(filename)

            await msg.delete()
        except Exception as e:
            await q.edit_message_text(f"❌ خطا در دانلود:\n{e}")
