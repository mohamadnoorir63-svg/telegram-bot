import json, random, os, asyncio
from gtts import gTTS
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
MEMORY_FILE = "memory.json"

# ===================== حافظه =====================
def init_memory():
    base = {"learning": True, "mood": "happy", "chats": {}}
    if not os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=2)
    else:
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                json.load(f)
        except:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(base, f, ensure_ascii=False, indent=2)

def load_data():
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

init_memory()

# ===================== صدا =====================
def make_voice(text, filename="voice.ogg"):
    try:
        tts = gTTS(text=text, lang="fa")
        tts.save(filename)
        return filename
    except Exception as e:
        print("خطا در تولید صدا:", e)
        return None

# ===================== پاسخ خودکار =====================
async def khengool_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip().lower()
    data = load_data()
    chats = data.get("chats", {})
    mood = data.get("mood", "happy")

    # پاسخ‌های پیش‌فرض هر مود
    mood_replies = {
        "happy": ["عه چه باحال گفتی 😂", "اوه چه جالب 😄", "منم همینو فکر می‌کردم 😆", "زندگی قشنگه نه؟ 😎"],
        "sad": ["بی‌حوصله‌ام 😔", "غم دارم امروز 😢", "نمی‌دونم چرا دلم گرفته 😞"],
        "angry": ["ولم کن اعصاب ندارم 😡", "الان وقتش نیست 😤", "می‌خوای دعوا کنیم؟ 😠"]
    }

    # اگر جمله جدید بود، یه جواب خلاق بساز
    if text not in chats:
        base_reply = random.choice(mood_replies[mood])
        creative_end = random.choice([
            " ولی تو باحالی 😅",
            " راستی دیشب خواب پیتزا دیدم 🍕",
            " اینو بنویسم یادم نره 😜",
            " بگو بازم، حرفات جالبه 😁"
        ])
        chats[text] = [base_reply + creative_end]
    else:
        # اگر جمله قبلاً ذخیره شده، یه جواب جدید بساز که تکراری نباشه
        old_replies = chats[text]
        new_reply = random.choice(mood_replies[mood])
        while new_reply in old_replies and len(old_replies) < 10:
            new_reply = random.choice(mood_replies[mood])
        old_replies.append(new_reply)
        chats[text] = old_replies[-10:]  # فقط 10 پاسخ آخر ذخیره کن

    data["chats"] = chats
    save_data(data)

    # انتخاب پاسخ نهایی
    response = random.choice(chats[text])

    # ارسال پاسخ متنی و صوتی
    await update.message.reply_text(response)
    voice_path = make_voice(response)
    if voice_path:
        with open(voice_path, "rb") as voice:
            await update.message.reply_voice(voice)

    # گاهی خودش وسط چت شروع می‌کنه 😂
    if random.random() < 0.2:
        await asyncio.sleep(random.randint(3, 7))
        auto_talk = random.choice([
            "من هنوز اینجام 😁",
            "می‌دونی دلم چی می‌خواد؟ پیتزاااا 🍕",
            "اوه حوصله‌م سر رفت 😴",
            "می‌خوای یه لطیفه بگم؟ 😜"
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
        await update.message.reply_text(f"مود فعلی: {data.get('mood', 'happy')}")

async def learn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if context.args:
        state = context.args[0].lower()
        if state == "on":
            data["learning"] = True
            msg = "یادگیری روشن شد 😁"
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, khengool_reply))
    print("🤖 Khengool Plus Creative Mode Started ...")
    app.run_polling()            
