import json, random, os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
MEMORY_FILE = "memory.json"

# ===================== حافظه =====================
if not os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump({"learning": True, "active": True, "chats": {}}, f, ensure_ascii=False, indent=2)

def load_data():
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===================== تولید جمله تصادفی =====================
def make_sentence(word):
    parts = [
        f"راستی در مورد {word} یه چیز خنده‌دار شنیدم 😂",
        f"آره {word} هم جالبه 😄",
        f"{word}? اوه یادم افتاد یه بار همچین چیزی گفتم 😅",
        f"به نظرم {word} چیز مهمیه 😎",
        f"{word}؟ بگو ببینم منظورت چیه دقیقا 🤔"
    ]
    return random.choice(parts)

# ===================== پاسخ به پیام =====================
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    data = load_data()

    if not data["active"]:
        return  # وقتی خاموشه هیچ کاری نکنه

    # بررسی دستورات فارسی بدون "/"
    if text.lower() == "یادبگیر روشن":
        data["learning"] = True
        save_data(data)
        await update.message.reply_text("🤓 حالت یادگیری روشن شد! هرچی بگی یاد می‌گیرم.")
        return

    if text.lower() == "یادبگیر خاموش":
        data["learning"] = False
        save_data(data)
        await update.message.reply_text("😴 یادگیری خاموش شد. فعلاً نمی‌خوام چیزی یاد بگیرم.")
        return

    if text.lower() == "بازنشانی":
        data = {"learning": True, "active": True, "chats": {}}
        save_data(data)
        await update.message.reply_text("🧹 حافظه‌ی من پاک شد، مثل روز اول شدم!")
        return

    if text.lower() == "وضعیت":
        learn_status = "روشن ✅" if data["learning"] else "خاموش ❌"
        active_status = "روشن ✅" if data["active"] else "خاموش ❌"
        await update.message.reply_text(f"🤖 خنگول فعاله: {active_status}\n🧠 یادگیری: {learn_status}")
        return

    if text.lower() == "خنگول خاموش":
        data["active"] = False
        save_data(data)
        await update.message.reply_text("😴 خنگول خاموش شد، بیدارش نکن!")
        return

    if text.lower() == "خنگول روشن":
        data["active"] = True
        save_data(data)
        await update.message.reply_text("😎 من برگشتم! بریم حرف بزنیم.")
        return

    # پاسخ هوشمند
    chats = data["chats"]
    response = None

    # اگه قبلاً چیزی مشابه یاد گرفته
    for key in chats.keys():
        if key in text:
            response = random.choice(chats[key])
            break

    # اگر بلد نیست و در حالت یادگیریه
    if not response and data["learning"]:
        if text not in chats:
            chats[text] = []
        response = make_sentence(text)
        chats[text].append(response)
        data["chats"] = chats
        save_data(data)

    # اگه هیچ پاسخی پیدا نشد
    if not response:
        response = random.choice([
            "نمیدونم چی بگم 😅", 
            "عه جالبه 😆", 
            "در موردش فکر نکرده بودم 🤔", 
            "می‌تونی بیشتر توضیح بدی؟ 😄"
        ])

    await update.message.reply_text(response)

# ===================== شروع =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام من خنگولم 🤪 بیا حرف بزنیم!")

# ===================== اجرای ربات =====================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    print("🤖 خنگول آفلاین در حال اجراست ...")
    app.run_polling()
