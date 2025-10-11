import json, random, os, asyncio
from gtts import gTTS
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ===================== تنظیمات اصلی =====================
TOKEN = os.getenv("BOT_TOKEN")
MEMORY_FILE = "memory.json"

# اگر حافظه وجود نداشت بساز
if not os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "learning": True,
            "mood": "happy",
            "chats": {}
        }, f, ensure_ascii=False, indent=2)

# ===================== توابع حافظه =====================
def load_data():
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===================== تبدیل متن به صدا =====================
def make_voice(text, filename="voice.ogg"):
    try:
        tts = gTTS(text=text, lang="fa")
        tts.save(filename)
        return filename
    except Exception as e:
        print("خطا در تولید صدا:", e)
        return None

# ===================== پاسخ خودکار خنگول =====================
async def khengool_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # گرفتن متن پیام
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip().lower()
    data = load_data()
    chats = data.get("chats", {})

    # مود فعلی خنگول
    mood = data.get("mood", "happy")

    mood_responses = {
        "happy": ["عه سلام 😄", "اوه چه باحال گفتی 😂", "منم همینو می‌خواستم بگم 😆", "آره دیگه زندگی همینه 😎"],
        "sad": ["اوه حوصله ندارم 😔", "بیخیال حرف نزن الان 😕", "غم دارم امروز 😢"],
        "angry": ["ولم کن اعصاب ندارم 😡", "باز شروع شد؟ 😤", "می‌خوای دعوا کنیم؟ 😠"]
    }

    # پاسخ‌های یاد گرفته‌شده
    learned_responses = chats.get(text, [])

    # ترکیب پاسخ‌ها
    possible_replies = mood_responses[mood] + learned_responses if learned_responses else mood_responses[mood]
    response = random.choice(possible_replies)

    # اگر حالت یادگیری روشن بود، ذخیره کن
    if data.get("learning", True):
        if text not in chats:
            chats[text] = []
        if response not in chats[text]:
            chats[text].append(response)
        data["chats"] = chats
        save_data(data)

    # ارسال پاسخ متنی
    await update.message.reply_text(response)

    # ارسال صدا
    voice_path = make_voice(response)
    if voice_path:
        with open(voice_path, "rb") as voice:
            await update.message.reply_voice(voice)

    # گاهی خودش شروع به حرف زدن می‌کند
    if random.random() < 0.15:
        await asyncio.sleep(random.randint(3, 7))
        auto_talk = random.choice([
            "من هنوز اینجام 😁",
            "برو حرف بزن، حوصله‌م سر رفت 😜",
            "هی منو یادت نره 😅",
            "می‌دونی دلم برات تنگ شده 😳"
        ])
        await update.message.reply_text(auto_talk)
        voice_path = make_voice(auto_talk)
        if voice_path:
            with open(voice_path, "rb") as voice:
                await update.message.reply_voice(voice)

# ===================== دستورات =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "سلام من خنگولم 🤪 بیا با هم حرف بزنیم!"
    await update.message.reply_text(msg)
    voice_path = make_voice(msg)
    if voice_path:
        with open(voice_path, "rb") as voice:
            await update.message.reply_voice(voice)

async def mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if context.args:
        new_mood = context.args[0].lower()
        if new_mood in ["happy", "sad", "angry"]:
            data["mood"] = new_mood
            save_data(data)
            await update.message.reply_text(f"مود خنگول تغییر کرد به: {new_mood} 😎")
        else:
            await update.message.reply_text("مودهای قابل استفاده: happy / sad / angry")
    else:
        await update.message.reply_text(f"مود فعلی: {data.get('mood','happy')}")

async def learn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if context.args:
        state = context.args[0].lower()
        if state == "on":
            data["learning"] = True
            msg = "یادگیری دوباره فعال شد 😁"
        elif state == "off":
            data["learning"] = False
            msg = "یادگیری خاموش شد 😴"
        else:
            msg = "فقط از 'on' یا 'off' استفاده کن 😅"
        save_data(data)
        await update.message.reply_text(msg)
    else:
        status = "روشن" if data.get("learning", True) else "خاموش"
        await update.message.reply_text(f"یادگیری الان {status} است.")

# ===================== اجرای ربات =====================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mood", mood))
    app.add_handler(CommandHandler("learn", learn))
    # حالا همه نوع پیام رو بگیره 👇
    app.add_handler(MessageHandler(filters.ALL, khengool_reply))
    print("🤖 Khengool Plus Started ...")
    app.run_polling()
