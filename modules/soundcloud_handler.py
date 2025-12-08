import yt_dlp
import asyncio
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

executor = ThreadPoolExecutor(max_workers=10)
track_store = {}

MSG = {
    "fa": {
        "searching": "🔍 در حال جستجو…",
        "select": "🎵 {n} آهنگ پیدا شد — انتخاب کنید:",
        "downloading": "⬇️ در حال ارسال آهنگ…",
        "yt_fallback": "❌ نتیجه‌ای در SoundCloud نبود — در حال جستجو در یوتیوب...",
    }
}


# ================================
# 1) گرفتن لینک مستقیم (بدون دانلود)
# ================================
def get_direct_link_sc(url):
    opts = {
        "quiet": True,
        "skip_download": True,
        "format": "bestaudio/best",
    }
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=False)
        return info, info["url"]


def get_direct_link_youtube(query):
    opts = {
        "quiet": True,
        "format": "bestaudio/best",
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(f"ytsearch1:{query}", download=False)
        info = info["entries"][0]
        return info, info["url"]


# ================================
# 2) جستجو در SoundCloud
# ================================
def search_sc_sync(q):
    with yt_dlp.YoutubeDL({"quiet": True}) as y:
        return y.extract_info(f"scsearch10:{q}", download=False)


# ================================
# 3) هندلر جستجو آهنگ
# ================================
async def soundcloud_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    txt = update.message.text.strip()
    if not txt.startswith("آهنگ "):
        return

    query = txt.replace("آهنگ ", "").strip()
    msg = await update.message.reply_text(MSG["fa"]["searching"])

    loop = asyncio.get_running_loop()

    # --- search soundcloud
    try:
        sc = await loop.run_in_executor(executor, search_sc_sync, query)
    except:
        sc = None

    # --- fallback youtube
    if not sc or "entries" not in sc or len(sc["entries"]) == 0:
        await msg.edit_text(MSG["fa"]["yt_fallback"])

        info, link = await loop.run_in_executor(
            executor, get_direct_link_youtube, query
        )

        await update.message.reply_audio(
            audio=link,
            caption=f"🎵 {info['title']}"
        )
        return

    # ساخت دکمه‌ها
    entries = sc["entries"]
    track_store[update.effective_chat.id] = entries

    keyboard = [
        [InlineKeyboardButton(t["title"], callback_data=f"msc:{t['id']}")]
        for t in entries
    ]

    await msg.edit_text(
        MSG["fa"]["select"].format(n=len(entries)),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================================
# 4) انتخاب آهنگ و ارسال سریع
# ================================
async def music_select_handler(update, context: ContextTypes.DEFAULT_TYPE):

    cq = update.callback_query
    await cq.answer()

    chat = cq.message.chat_id
    track_id = cq.data.split(":")[1]

    tracks = track_store.get(chat, [])
    track = next((t for t in tracks if str(t["id"]) == track_id), None)

    if not track:
        return await cq.edit_message_text("❌ آهنگ پیدا نشد.")

    await cq.edit_message_text(MSG["fa"]["downloading"])

    loop = asyncio.get_running_loop()

    # گرفتن لینک مستقیم
    info, direct_link = await loop.run_in_executor(
        executor, get_direct_link_sc, track["webpage_url"]
    )

    await context.bot.send_audio(
        chat,
        direct_link,
        caption=f"🎵 {info['title']}"
    )

    await cq.message.delete()
