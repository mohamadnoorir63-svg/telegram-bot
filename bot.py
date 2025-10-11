import json
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 📁 فایل حافظه
MEMORY_FILE = "memory.json"

def load_memory():
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"active": True, "learning": True, "chats": {}}

def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 🤖 پاسخ‌دهی
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    data = load_memory()

    # 🔹 دستور روشن — همیشه چک می‌شود
    if "روشن" in text:
        if data["active"]:
            await update.message.reply_text("من که روشنم آقا 😎")
        else:
            data["active"] = True
            save_memory(data)
            await update.message.reply_text("ربات روشن شد 😍 بریم شروع کنیم!")
        return

    # 🔹 اگر خاموش است، هیچ پاسخی نده
    if not data["active"]:
        return

    # 🔹 دستور خاموش
    if "خاموش" in text:
        data["active"] = False
        save_memory(data)
        await update.message.reply_text("ربات خاموش شد 😴 تا بعد!")
        return

    # 🔹 یادگیری
    if text.startswith("یادبگیر"):
        parts = text.split("\n")
        if len(parts) >= 2:
            key = parts[0].replace("یادبگیر", "").strip()
            answers = [p.strip() for p in parts[1:] if p.strip()]

            # بررسی تکراری بودن و تغییر جواب‌ها
            if key in data["chats"]:
                for ans in answers:
                    if ans not in data["chats"][key]:
                        data["chats"][key].append(ans)
            else:
                data["chats"][key] = answers

            save_memory(data)
            await update.message.reply_text(f"جملات جدید برای «{key}» یاد گرفتم 🤓")
        else:
            await update.message.reply_text("بگو چی رو یاد بگیرم 😅")
        return

    # 🔹 پاسخ از حافظه
    for key, responses in data["chats"].items():
        if key in text:
            response = random.choice(responses)
            await update.message.reply_text(response)
            return

    # 🔹 fallback — جمله خاصی بلد نیست
    await update.message.reply_text(random.choice([
        "عجب؟ بگو ببینم چی تو ذهنت بود 🤔",
        "جالب گفتی، بیشتر بگو 😏",
        "نمیدونم دقیق 😅 ولی سعی می‌کنم یاد بگیرم!",
        "ها؟ دوباره بگو ببینم 😜"
    ]))

# 🚀 راه‌اندازی ربات
def main():
    from os import getenv
    TOKEN = getenv("BOT_TOKEN")  # توکن تلگرام تو در هاست تنظیم شده
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    print("🤖 خنگول 2.5 آماده‌ست...")
    app.run_polling()

if __name__ == "__main__":
    main()
