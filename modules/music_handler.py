import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# -----------------------
# جستجوی موزیک از API جهانی رایگان
# -----------------------
async def music_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    query = update.message.text.replace("/موزیک", "").replace("موزیک", "").strip()
    if not query:
        await update.message.reply_text("❌ لطفاً نام موزیک یا خواننده را وارد کنید.")
        return

    msg = await update.message.reply_text("🔍 در حال جستجو...")

    try:
        # مثال API رایگان (سایت های موسیقی جهانی مثل api.lyrics.ovh یا سایر رایگان ها)
        # اینجا از یک API نمونه استفاده می‌کنیم که جستجو و لینک mp3 می‌دهد
        url = f"https://api.lyrics.ovh/suggest/{query}"
        resp = requests.get(url, timeout=10).json()
        songs = resp.get("data", [])[:5]

        if not songs:
            await msg.edit_text("❌ آهنگی پیدا نشد.")
            return

        keyboard = []
        for i, song in enumerate(songs, start=1):
            title = song.get("title")
            artist = song.get("artist", {}).get("name", "Unknown")
            song_id = f"{title}||{artist}"
            keyboard.append([InlineKeyboardButton(f"{i}. {title} - {artist}", callback_data=f"music_select:{song_id}")])

        await msg.edit_text("🎵 لطفاً یک آهنگ را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        await msg.edit_text(f"❌ خطا در جستجوی موزیک: {e}")

# -----------------------
# انتخاب موزیک و دانلود
# -----------------------
async def music_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    song_id = query.data.replace("music_select:", "")
    title, artist = song_id.split("||")

    msg = await query.edit_message_text(f"⬇ در حال دانلود آهنگ: {title} - {artist}\nلطفاً صبر کنید...")

    try:
        # لینک mp3 نمونه از سایت رایگان
        # اینجا می‌توانی هر API رایگان موزیک جهانی که لینک مستقیم mp3 می‌دهد قرار دهی
        # مثال فرضی:
        mp3_url = f"https://mp3-sample-api.example.com/download?title={title}&artist={artist}"

        file_path = os.path.join(DOWNLOAD_FOLDER, f"{title}_{artist}.mp3")
        r = requests.get(mp3_url, stream=True, timeout=20)
        if r.status_code == 200:
            with open(file_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
        else:
            await query.edit_message_text("❌ خطا در دانلود موزیک.")
            return

        # ارسال موزیک
        await context.bot.send_audio(chat_id=query.message.chat.id, audio=open(file_path, "rb"), caption=f"🎵 {title} - {artist}")
        os.remove(file_path)
        await query.edit_message_text(f"✅ آهنگ {title} - {artist} دانلود شد.")

    except Exception as e:
        await query.edit_message_text(f"❌ خطا در دانلود موزیک: {e}")
