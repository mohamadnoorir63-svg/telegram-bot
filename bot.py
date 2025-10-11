import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# تابع جست‌وجو در JioSaavn
def search_song(query):
    url = f"https://saavn.dev/api/search/songs?query={query}"
    r = requests.get(url)
    data = r.json()
    if data.get("data") and len(data["data"]["results"]) > 0:
        return data["data"]["results"][0]
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 سلام! اسم آهنگ رو بنویس تا برات MP3 بفرستم 🎧")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    await update.message.reply_text("🔎 در حال جست‌وجو در JioSaavn... لطفاً صبر کنید ⏳")

    song = search_song(query)
    if not song:
        await update.message.reply_text("❌ آهنگی پیدا نشد. دوباره تلاش کن!")
        return

    title = song["name"]
    artist = song["artists"]["primary"][0]["name"]
    mp3_url = song["downloadUrl"][-1]["url"]

    caption = f"🎶 {title}\n👤 {artist}\n💽 از JioSaavn"
    await update.message.reply_audio(audio=mp3_url, caption=caption)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
