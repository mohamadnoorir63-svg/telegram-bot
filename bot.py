# -*- coding: utf-8 -*-
import os, json, random, asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ================= تنظیمات =================
TOKEN = os.getenv("BOT_TOKEN")
SUDO_ID = int(os.getenv("SUDO_ID", "0"))
MEMORY_FILE = "memory.json"

# ================= حافظه =================
if not os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "active": True,
            "learning": True,
            "mood": "normal",
            "replies": {},
            "groups": []
        }, f, ensure_ascii=False, indent=2)

def load_data():
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================= توابع کمکی =================
async def send_message(update, text):
    try:
        await update.message.reply_text(text)
    except:
        pass

def random_reply(arr):
    return random.choice(arr) if arr else "نمیدونم چی بگم 😅"

# ================= ربات =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "سلام من خنگولم 🤪 آماده‌ام باهات حرف بزنم!"
    await send_message(update, msg)

async def new_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    chat_id = update.message.chat_id
    if chat_id not in data["groups"]:
        data["groups"].append(chat_id)
        save_data(data)
        await send_message(update, "😂 نصب خنگول با موفقیت انجام شد!\nآماده‌ام گند بزنم به جو گروه 😜")

# ================= یادگیری =================
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data["active"]:
        return

    text = update.message.text.strip()
    replies = data["replies"]

    # پاسخ از حافظه
    if text in replies:
        resp = random_reply(replies[text])
        await send_message(update, resp)
    elif data["learning"]:
        # اگر در حال یادگیریه، پاسخ رو ذخیره کن
        last_key = getattr(context.chat_data, "last_teach", None)
        if last_key:
            replies.setdefault(last_key, []).append(text)
            context.chat_data["last_teach"] = None
            await send_message(update, f"😄 یاد گرفتم که وقتی گفتن «{last_key}» بگم «{text}»")
            data["replies"] = replies
            save_data(data)
    else:
        # اگر نمی‌دونه و یادگیری خاموشه
        await send_message(update, random.choice(["هومم 🤔", "چی گفتی؟ 😅", "من نمی‌دونم 😁"]))

# ================= دستور یادگیری =================
async def learn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    msg = update.message.text.strip().replace("یادبگیر ", "")
    context.chat_data["last_teach"] = msg
    await send_message(update, f"باشه 😎 حالا جواب‌های «{msg}» رو بفرست، وقتی تموم شد بنویس تموم")

async def finish_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.chat_data.get("last_teach"):
        context.chat_data["last_teach"] = None
        await send_message(update, "👌 یادگیری این بخش تموم شد")
    else:
        await send_message(update, "الان چیزی برای یادگیری فعال نیست 😅")# ================= مودها =================
async def set_mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    msg = update.message.text.lower().replace("مود ", "").strip()

    moods = {
        "شوخ": "funny",
        "غمگین": "sad",
        "بی‌ادب": "rude",
        "نرمال": "normal"
    }

    if msg in moods:
        data["mood"] = moods[msg]
        save_data(data)
        await send_message(update, f"مود خنگول تغییر کرد به: {msg} 😎")
    else:
        await send_message(update, "مودها: شوخ / غمگین / بی‌ادب / نرمال")

# ================= خاموش / روشن =================
async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    msg = update.message.text.strip()

    if "خاموش" in msg:
        data["active"] = False
        save_data(data)
        await send_message(update, "😴 خنگول خاموش شد... بیدارش نکن!")
    elif "روشن" in msg:
        data["active"] = True
        save_data(data)
        await send_message(update, "😎 خنگول برگشت! بگو چی شده؟")

# ================= شوخی خودکار =================
async def auto_joke(app):
    jokes = [
        "می‌دونی چرا کامپیوتر من همیشه خسته‌ست؟ چون همیشه داره run می‌کنه 😂",
        "گفتن خنگول شوخ شو، منم مود شوخ زدم 😜",
        "یه روزی من باهوش می‌شم... شاید 🤔",
        "تو گفتی یادبگیر، من یاد گرفتم چطور گند بزنم 😈"
    ]
    while True:
        await asyncio.sleep(3600)  # هر یک ساعت
        data = load_data()
        for gid in data.get("groups", []):
            try:
                await app.bot.send_message(chat_id=gid, text=random.choice(jokes))
            except:
                pass

# ================= خوش‌آمد =================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.new_chat_members[0].first_name
    await send_message(update, f"به به! 😁 خوش اومدی {name} ❤️ اینجا خونه‌ی خنگوله 🤪")

# ================= پنل ادمین =================
async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != SUDO_ID:
        return
    data = load_data()
    text = (
        f"📊 وضعیت خنگول:\n"
        f"🔹 فعال: {'✅' if data['active'] else '❌'}\n"
        f"🔹 یادگیری: {'✅' if data['learning'] else '❌'}\n"
        f"🔹 مود فعلی: {data['mood']}\n"
        f"👥 تعداد گروه‌ها: {len(data['groups'])}"
    )
    await send_message(update, text)

# ================= خروج از گروه =================
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != SUDO_ID:
        return
    await send_message(update, "باشه 😢 خداحافظ همه‌تون 😜")
    await context.bot.leave_chat(update.message.chat_id)

# ================= اجرای ربات =================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^یادبگیر "), learn))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^تموم$"), finish_learning))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(مود )"), set_mood))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(خاموش|روشن)$"), toggle))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^پنل$"), panel))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^لفت بده$"), leave))
    app.add_handler(MessageHandler(filters.ALL, reply))

    loop = asyncio.get_event_loop()
    loop.create_task(auto_joke(app))

    print("🤖 خنگول 5.0 آماده است ...")
    app.run_polling()
