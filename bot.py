import json, random, os, time
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
MEMORY_FILE = "memory.json"

# =============== حافظه ===============
def init_memory():
    base = {
        "learning": True,
        "active": True,
        "mood": "happy",
        "chats": {},
        "teaching": None,  # حالت آموزش دستی
        "last_active": time.time()
    }
    if not os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=2)
        return base
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = base
    for k in base:
        if k not in data:
            data[k] = base[k]
    save_data(data)
    return data

def load_data():
    return init_memory()

def save_data(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =============== پاسخ خودکار ===============
def random_reply(text, mood):
    patterns = {
        "happy": [
            f"{text}؟ 😄", f"عه {text} گفتی؟ 😂", f"{text}؟ خندم گرفت 😆", f"در مورد {text} حرف بزن 😎"
        ],
        "sad": [
            f"{text} رو نگو دلم گرفت 😢", f"اه {text}؟ حوصله ندارم 😞", f"{text} واسم غم‌انگیزه 😔"
        ],
        "angry": [
            f"{text}؟ بازم اون؟ 😡", f"از {text} متنفرم 😤", f"ولش کن {text} رو 😠"
        ]
    }
    return random.choice(patterns[mood])

# =============== پیام‌ها ===============
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    data = load_data()

    # اگر خاموشه
    if not data.get("active", True):
        return

    # ======= حالت آموزش دستی =======
    if data.get("teaching"):
        key = data["teaching"]
        if text.lower() == "پایان":
            data["teaching"] = None
            save_data(data)
            await update.message.reply_text(f"✅ آموزش برای «{key}» تموم شد! حالا هر وقت کسی بگه «{key}» من یکی از جواب‌هایی که گفتی رو می‌گم 😁")
        else:
            data["chats"].setdefault(key, []).append(text)
            save_data(data)
            await update.message.reply_text(f"یاد گرفتم: «{text}» 😎\n(بنویس «پایان» وقتی تموم شد)")
        return

    # ======= شروع آموزش =======
    if text.startswith("یادبگیر "):
        key = text.replace("یادبگیر ", "").strip().lower()
        data["teaching"] = key
        save_data(data)
        await update.message.reply_text(f"🧠 حالت آموزش برای «{key}» فعال شد!\nحالا جواب‌هارو زیرش بنویس و آخرش بنویس «پایان» 😁")
        return

    # ======= سایر دستورات =======
    if text == "یادبگیر روشن":
        data["learning"] = True
        save_data(data)
        await update.message.reply_text("🧠 یادگیری خودکار روشن شد 😄")
        return

    if text == "یادبگیر خاموش":
        data["learning"] = False
        save_data(data)
        await update.message.reply_text("😴 یادگیری خودکار خاموش شد.")
        return

    if text == "بازنشانی":
        data = {"learning": True, "active": True, "mood": "happy", "chats": {}, "teaching": None}
        save_data(data)
        await update.message.reply_text("♻️ همه‌چیو از اول شروع کردم 😁")
        return

    if text == "خنگول خاموش":
        data["active"] = False
        save_data(data)
        await update.message.reply_text("😴 خنگول خوابید...")
        return

    if text == "خنگول روشن":
        data["active"] = True
        save_data(data)
        await update.message.reply_text("😎 بیدار شدم، بگو ببینم چی شده!")
        return

    if text == "وضعیت":
        await update.message.reply_text(
            f"🤖 فعال: {'روشن ✅' if data['active'] else 'خاموش ❌'}\n"
            f"🧠 یادگیری: {'روشن ✅' if data['learning'] else 'خاموش ❌'}\n"
            f"💬 مود: {data['mood']}"
        )
        return

    # ======= پاسخ =======
    chats = data["chats"]
    mood = data["mood"]
    response = None

    for key in chats:
        if key in text.lower():
            response = random.choice(chats[key])
            break

    # یادگیری خودکار
    if not response and data.get("learning", True):
        response = random_reply(text, mood)
        chats.setdefault(text.lower(), []).append(response)
        save_data(data)

    if not response:
        response = random.choice([
            "جالبه 😄", "اوه اینو قبلاً نشنیده بودم 😯", "ادامه بده ببینم 😅", "ههه جالب گفتی 😂"
        ])

    await update.message.reply_text(response)
    save_data(data)

# =============== شروع ===============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام من خنگول ۲.۵ هستم 🤪 بیا یادم بده چی بگم 😁")

# =============== اجرای ربات ===============
if __name__ == "__main__":
    init_memory()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    print("🤖 خنگول ۲.۵ در حال اجراست ...")
    app.run_polling()
