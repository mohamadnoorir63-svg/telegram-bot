import json, random, os
from gtts import gTTS
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ==============================
# تنظیمات پایه
# ==============================
TOKEN = os.getenv("BOT_TOKEN")  # توکن ربات از Config Vars
MEMORY_FILE = "memory.json"

# اگر فایل حافظه وجود ندارد بساز
if not os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

# تابع کمکی برای خواندن حافظه
def load_memory():
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# تابع ذخیره در حافظه
def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==============================
# بخش صدا
# ==============================
def make_voice(text, filename="voice.ogg"):
    tts = gTTS(text=text, lang="fa")
    tts.save(filename)
    return filename

# ==============================
# پاسخ خودکار خنگول
# ==============================
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    memory = load_memory()

    # اگر جمله جدید است، ذخیره کن
    if text not in memory:
        memory[text] = []
        save_memory(memory)

    # پاسخ‌های آماده و تصادفی
    funny_replies = [
        "عه جدی؟ 😂",
        "یعنی چی؟ من نفهمیدم 😅",
        "اوه اوه اینو باید یادم بمونه 🤔",
        "عه سلام! فکر کردم رفتی 😁",
        "باز اومدی؟ من که خسته شدم 😜",
        "تو خیلی حرف میزنی ولی من بیشتر 😎",
        "باشه باشه تو بردی 🤫",
        "عه منم همینو می‌خواستم بگم 😆",
    ]

    response = random.choice(funny_replies)

    # ارسال پیام متنی
    await update.message.reply_text(response)

    # تولید صدا و ارسال
    voice_path = make_voice(response)
    with open(voice_path, "rb") as voice:
        await update.message.reply_voice(voice)

# ==============================
# دستور /start
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "سلام من خنگولم 🤪 بیا با هم حرف بزنیم!"
    await update.message.reply_text(msg)
    voice_path = make_voice(msg)
    with open(voice_path, "rb") as voice:
        await update.message.reply_voice(voice)

# ==============================
# اجرای ربات
# ==============================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    print("🤖 KhengoolBot started...")
    app.run_polling()
