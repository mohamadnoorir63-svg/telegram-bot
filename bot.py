import json, random, os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
MEMORY_FILE = "memory.json"

# ===================== حافظه =====================
def init_memory():
    """اگر فایل وجود ندارد یا ناقص است، بساز یا تکمیلش کن"""
    base = {"learning": True, "active": True, "chats": {}}
    if not os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=2)
        return base

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        data = base

    # اگر کلیدها نبودند اضافه کن
    for key in base:
        if key not in data:
            data[key] = base[key]

    save_data(data)
    return data

def load_data():
    return init_memory()

def save_data(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===================== تولید جمله تصادفی =====================
def make_sentence(word):
    parts = [
        f"در مورد {word} نظر خاصی ندارم ولی بامزه‌ست 😂",
        f"{word}؟ هم خنده‌داره هم جدی 😅",
        f"آره {word} جالبه 😄",
        f"{word}؟ هه، خوب گفتی 😎",
        f"{word}؟ بگو ببینم چی تو ذهنت بود 🤔"
    ]
    return random.choice(parts)

# ===================== پاسخ اصلی =====================
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    data = load_data()

    # بررسی فعال بودن
    if not data.get("active", True):
        return

    # --- دستورات فارسی ---
    if text.lower() == "یادبگیر روشن":
        data["learning"] = True
        save_data(data)
        await update.message.reply_text("🧠 یادگیری روشن شد! هرچی بگی یاد می‌گیرم 😁")
        return

    if text.lower() == "یادبگیر خاموش":
        data["learning"] = False
        save_data(data)
        await update.message.reply_text("😴 یادگیری خاموش شد. فعلاً هیچی یاد نمی‌گیرم.")
        return

    if text.lower() == "بازنشانی":
        data = {"learning": True, "active": True, "chats": {}}
        save_data(data)
        await update.message.reply_text("🧹 حافظه پاک شد! مثل روز اول شدم 😄")
        return

    if text.lower() == "وضعیت":
        learn_status = "روشن ✅" if data.get("learning", True) else "خاموش ❌"
        active_status = "روشن ✅" if data.get("active", True) else "خاموش ❌"
        await update.message.reply_text(f"🤖 خنگول فعاله: {active_status}\n🧠 یادگیری: {learn_status}")
        return

    if text.lower() == "خنگول خاموش":
        data["active"] = False
        save_data(data)
        await update.message.reply_text("😴 خنگول خاموش شد. بیدارش نکن فعلاً!")
        return

    if text.lower() == "خنگول روشن":
        data["active"] = True
        save_data(data)
        await update.message.reply_text("😎 خنگول برگشت! بریم حرف بزنیم 😁")
        return

    # --- پاسخ‌های یادگرفته‌شده ---
    chats = data.get("chats", {})
    response = None

    for key in chats.keys():
        if key in text:
            response = random.choice(chats[key])
            break

    # --- اگر بلد نیست و یادگیری فعاله ---
    if not response and data.get("learning", True):
        if text not in chats:
            chats[text] = []
        response = make_sentence(text)
        chats[text].append(response)
        data["chats"] = chats
        save_data(data)

    # --- اگر هیچ پاسخی پیدا نشد ---
    if not response:
        response = random.choice([
            "عه جالب گفتی 😆",
            "نمیدونم چی بگم 😅",
            "بیشتر بگو ببینم 🤔",
            "عه جدی؟ 😯",
            "هه... ادامه بده ببینم چی میشه 😁"
        ])

    await update.message.reply_text(response)

# ===================== شروع =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام من خنگولم 🤪 بیا باهم حرف بزنیم!")

# ===================== اجرای ربات =====================
if __name__ == "__main__":
    init_memory()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    print("🤖 خنگول آفلاین نهایی در حال اجراست ...")
    app.run_polling()
