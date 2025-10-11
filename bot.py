# -*- coding: utf-8 -*-
import os, json, random, asyncio
from telegram import Update, ChatAction, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ================= تنظیمات پایه ==================
TOKEN = os.environ.get("BOT_TOKEN")
MEMORY_FILE = "memory.json"

# بارگذاری یا ایجاد حافظه
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = json.load(f)
else:
    memory = {}

# وضعیت روشن یا خاموش بودن ربات
active_chats = set()

# پاسخ‌های پیش‌فرض خنده‌دار
funny_responses = [
    "عه 😆 جدی میگی؟",
    "برو بابا 😂",
    "خنگول گیج شد 😵‍💫",
    "نزن تو مخم 😜",
    "اوه اوه چی گفتی 😳",
    "دمت گرم 😎",
    "عههه 😁 دوباره بگو!",
    "نه خب راست میگی 😅",
    "الان خنگول قاط زد 🤯",
    "بذار یه چایی بخورم بعد جواب بدم ☕"
]

# ================= توابع کمکی ==================
def save_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

# ================= دستورات ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام 😁 خنگول آنلاینه و آماده شوخیه!")

async def on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    active_chats.add(chat_id)
    await update.message.reply_text("خنگول فعاله 😎 بریم بخندیم!")

async def off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in active_chats:
        active_chats.remove(chat_id)
        await update.message.reply_text("خنگول رفت بخوابه 😴")
    else:
        await update.message.reply_text("الان که خاموشه 😴")

async def learn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.replace("/یادگیری", "").strip()
        if "=" in text:
            key, value = text.split("=", 1)
            memory[key.strip()] = value.strip()
            save_memory()
            await update.message.reply_text(f"یاد گرفتم 😁 وقتی گفتی «{key.strip()}» میگم «{value.strip()}»")
        else:
            await update.message.reply_text("فرمت درست: /یادگیری کلمه = جواب")
    except:
        await update.message.reply_text("یه مشکلی پیش اومد 😅 دوباره امتحان کن.")

# ================= پاسخ‌دهی خودکار ==================
async def reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text.strip().lower()

    # اگه ربات در این گروه خاموشه
    if chat_id not in active_chats:
        return

    # اگه کاربر چیزی گفت که توی حافظه هست
    for key, value in memory.items():
        if key in text:
            await update.message.reply_text(value)
            return

    # اگه اسم ربات رو گفتن یا شانسی خودش بخواد جواب بده
    if "خنگول" in text or random.random() < 0.15:
        response = random.choice(funny_responses)

        # گاهی استیکر بفرسته به‌جای متن 😁
        if random.random() < 0.2:
            stickers = [
                "CAACAgQAAxkBAAEB1jpmV3h6hXG4FQABh8K8bdcybphN3q8AAn8AAykxyxPDHQAAAczmVjAE",
                "CAACAgQAAxkBAAEB1j5mV3iq6f8j8s8N1QkD3a74BwsIjAAC4wADVp29Cio5jB_g4Rw9MAQ",
                "CAACAgIAAxkBAAEByKtlV3i58ZrhU7ijj7kyrkM-Zw7cCwACpAIAAkcVaUvb1zNn-J-DsTAQ"
            ]
            await update.message.reply_sticker(random.choice(stickers))
        else:
            await update.message.reply_text(response)

# ================= اجرای ربات ==================
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("روشن", on))
    app.add_handler(CommandHandler("خاموش", off))
    app.add_handler(CommandHandler("یادگیری", learn))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_message))

    print("🤖 خنگول آماده‌ست!")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
