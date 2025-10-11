# -- coding: utf-8 --
import os, requests, telebot
from telebot import types

TOKEN = os.environ.get("BOT_TOKEN")  # توکن از متغیر محیطی
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

API_URL = "https://api-v2.vedba.com/search?query="  # منبع جستجو

# ------------------ شروع / راهنما ------------------
@bot.message_handler(commands=['start', 'help'])
def start(m):
    txt = (
        "🎵 <b>سلام!</b>\n"
        "من یه ربات جستجوگر موزیک هستم 🎧\n"
        "اسم آهنگ یا خواننده رو بفرست تا برات بیارم ❤️\n\n"
        "مثلاً بنویس:\n<code>imagine dragons believer</code>\n"
    )
    bot.send_message(m.chat.id, txt)

# ------------------ جستجو ------------------
@bot.message_handler(func=lambda m: True)
def search_music(m):
    query = m.text.strip()
    bot.send_message(m.chat.id, f"🔎 در حال جستجوی آهنگ: <b>{query}</b> ...")

    try:
        r = requests.get(API_URL + query, timeout=10)
        data = r.json().get("data", [])
    except Exception as e:
        return bot.send_message(m.chat.id, "❗ خطا در ارتباط با سرور موزیک.")

    if not data:
        return bot.send_message(m.chat.id, "❗ آهنگی با این نام پیدا نشد.")

    markup = types.InlineKeyboardMarkup()
    for item in data[:5]:
        title = item.get("title", "Unknown")
        url = item.get("url")
        btn = types.InlineKeyboardButton(text=title[:45], callback_data=url)
        markup.add(btn)

    bot.send_message(
        m.chat.id,
        "🎶 آهنگ مورد نظرت رو از بین نتایج زیر انتخاب کن 👇",
        reply_markup=markup
    )

# ------------------ انتخاب و ارسال آهنگ ------------------
@bot.callback_query_handler(func=lambda c: True)
def send_music(c):
    url = c.data
    try:
        info = requests.get(f"https://api-v2.vedba.com/download?url={url}").json()
        title = info.get("title", "Music")
        artist = info.get("channel", "Unknown Artist")
        thumb = info.get("thumbnail")
        dl_link = info.get("url_audio")

        caption = f"🎵 <b>{title}</b>\n👤 <i>{artist}</i>\n\n🔗 <a href='{dl_link}'>دانلود MP3</a>"

        if thumb:
            bot.send_photo(c.message.chat.id, thumb, caption=caption)
        else:
            bot.send_message(c.message.chat.id, caption)

    except Exception as e:
        bot.send_message(c.message.chat.id, "❗ خطا در دریافت اطلاعات آهنگ.")

print("✅ Music Search Bot is Running...")
bot.infinity_polling()
