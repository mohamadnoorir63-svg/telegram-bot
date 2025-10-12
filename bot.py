# ================== خنگول 4.0 نهایی ==================
# 😎 نویسنده: هوش مصنوعی نسخه GPT-5
# 📅 ویژگی‌ها: موددار، شوخ، یادگیر، پنل‌دار، خوش‌آمدگو، شوخی خودکار
# =====================================================

import os, json, random, asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, ChatMemberHandler
)

# ================== تنظیمات اولیه ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7089376754  # آیدی تو

MEMORY_FILE = "memory.json"

# اگر فایل حافظه وجود نداشت، بساز
if not os.path.exists(MEMORY_FILE):
    data = {
        "active": True,
        "learning": True,
        "mode": "normal",
        "chats": {},
        "groups": []
    }
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================== توابع کمکی ==================
def load_data():
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================== مودها ==================
MODES = {
    "normal": ["آره بابا 😎", "چه خبر؟", "من اینجام هنوز 😁"],
    "funny": ["ههه 😂 خنده‌دار بود!", "عه تو خیلی باحالی 🤪", "من خنگولم ولی تو یه چیز دیگه‌ای 😆"],
    "sad": ["دلم گرفته 😢", "هیچ‌کی منو درک نمی‌کنه 😔", "بغضم گرفته..."],
    "rude": ["خفه شو 😏", "چیه بازم؟ 😒", "اوه اوه چه زر زیادی می‌زنی 😈"]
}

# ================== شوخی‌ها ==================
JOKES = [
    "می‌دونی اگه مغزت شارژ داشت، برق کشور قطع می‌شد؟ 😂",
    "می‌گن خنده بر هر درد بی‌درمان دواست، جز امتحان و قسط عقب‌افتاده 😩",
    "یه روز خنگول رفتم دکتر، گفت چته؟ گفتم هیچی فقط خواستم ببینم شما زنده‌ای یا نه 😜",
    "می‌خواستم زرنگ شم، اما مغزم گفت: لطفاً ازم سوءاستفاده نکن 😅"
]# ================== پاسخ‌گویی و یادگیری ==================
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip()
    user_id = update.message.from_user.id
    data = load_data()

    # اگر ربات خاموشه
    if not data.get("active", True):
        return

    # مود فعلی
    mode = data.get("mode", "normal")

    # پاسخ خاص برای مودها
    base_reply = random.choice(MODES[mode])

    # اگر جمله‌ی یادگرفته شده وجود داشته باشه
    chats = data.get("chats", {})
    if msg in chats:
        response = random.choice(chats[msg])
    else:
        # اگر یادگیری فعاله، جمله جدید رو بسازه و ذخیره کنه
        if data.get("learning", True):
            if msg not in chats:
                chats[msg] = []
            new_sentence = random.choice(MODES[mode])
            chats[msg].append(new_sentence)
            data["chats"] = chats
            save_data(data)
        response = base_reply

    await update.message.reply_text(response)

# ================== یادگیری دستی ==================
async def learn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    text = update.message.text.replace("یادبگیر", "", 1).strip()
    if not text:
        await update.message.reply_text("بگو چی یاد بگیرم 😁")
        return

    # پیام بعدی رو منتظر بمون برای جواب‌ها
    await update.message.reply_text(f"باشه! حالا جواب‌هاتو برای «{text}» بفرست. وقتی تموم شد بنویس تموم.")

    def check_response(msg):
        return msg.from_user.id == update.message.from_user.id

    chats = data.get("chats", {})
    chats[text] = []

    while True:
        msg = await context.application.bot.wait_for("message", check=check_response)
        reply_text = msg.text.strip()
        if reply_text == "تموم":
            break
        chats[text].append(reply_text)
        await update.message.reply_text("یاد گرفتم 😎")

    data["chats"] = chats
    save_data(data)
    await update.message.reply_text(f"تموم شد! حالا هر کی گفت «{text}» یکی از جواب‌هاتو می‌گم 🤪")

# ================== روشن/خاموش ==================
async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    txt = update.message.text.strip()

    if "خاموش" in txt:
        data["active"] = False
        msg = "😴 خنگول خاموش شد!"
    elif "روشن" in txt:
        data["active"] = True
        msg = "🤖 خنگول دوباره روشن شد!"
    else:
        msg = "بگو «روشن شو» یا «خاموش شو»"

    save_data(data)
    await update.message.reply_text(msg)

# ================== تغییر مود ==================
async def change_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    txt = update.message.text.strip()

    if "بی ادب" in txt:
        data["mode"] = "rude"
        msg = "😈 از الان بی‌ادب می‌شم!"
    elif "غمگین" in txt:
        data["mode"] = "sad"
        msg = "🥀 دلم گرفته..."
    elif "شوخ" in txt:
        data["mode"] = "funny"
        msg = "😂 از الان شوخ و خنده‌دارم!"
    elif "نورمال" in txt:
        data["mode"] = "normal"
        msg = "😎 دوباره معمولی شدم!"
    else:
        msg = "مودهای قابل استفاده: شوخ، غمگین، بی ادب، نورمال"

    save_data(data)
    await update.message.reply_text(msg)# ================== شوخی خودکار ==================
async def auto_joke(app):
    while True:
        await asyncio.sleep(3600)  # هر یک ساعت
        data = load_data()
        for chat_id in data.get("groups", []):
            joke = random.choice(JOKES)
            try:
                await app.bot.send_message(chat_id=chat_id, text=f"😂 شوخی خنگول:\n{joke}")
            except Exception:
                pass

# ================== خوش‌آمدگویی ==================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = update.chat_member.new_chat_member.user
    chat_id = update.chat_member.chat.id
    data = load_data()

    if chat_id not in data["groups"]:
        data["groups"].append(chat_id)
        save_data(data)

    name = member.first_name or "کاربر جدید"
    await context.bot.send_message(chat_id=chat_id, text=f"🎉 خوش اومدی {name}! من خنگولم 🤪")

# ================== پنل مدیر ==================
async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = load_data()

    if user_id != ADMIN_ID:
        await update.message.reply_text("فقط رئیس من می‌تونه پنل رو ببینه 😏")
        return

    groups = len(data.get("groups", []))
    learned = len(data.get("chats", {}))
    active = "✅ روشن" if data.get("active", True) else "❌ خاموش"
    mode = data.get("mode", "normal")

    msg = (
        f"🧠 پنل مدیریتی خنگول:\n"
        f"وضعیت: {active}\n"
        f"مود فعلی: {mode}\n"
        f"تعداد گروه‌ها: {groups}\n"
        f"تعداد جملات یادگرفته: {learned}\n"
        f"📅 آخرین به‌روزرسانی: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    await update.message.reply_text(msg)

# ================== دستور لفت دادن ==================
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("فقط رئیس من می‌تونه منو از گروه بندازه بیرون 😏")
        return
    chat_id = update.message.chat.id
    await update.message.reply_text("😢 باشه من دارم می‌رم... خدافظ!")
    await context.bot.leave_chat(chat_id)# ================== اجرای نهایی ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام من خنگولم 🤪\n"
        "بگو تا باهات حال کنم! 😁\n\n"
        "دستورات:\n"
        "- یادبگیر <کلمه>\n"
        "- روشن شو / خاموش شو\n"
        "- بی ادب شو / شوخ شو / غمگین شو / نورمال شو\n"
        "- پنل\n"
        "- لفت بده\n"
    )

if __name__ == "__main__":
    print("🤖 خنگول 4.0 در حال اجراست ...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # دستورات اصلی
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^پنل$"), panel))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("یادبگیر"), learn))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("روشن|خاموش"), toggle))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("بی ادب|غمگین|شوخ|نورمال"), change_mode))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^لفت بده$"), leave))

    # پاسخ عادی به پیام‌ها
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    # خوش‌آمدگویی اعضای جدید
    app.add_handler(ChatMemberHandler(welcome, ChatMemberHandler.CHAT_MEMBER))

    # اجرای شوخی خودکار
    app.create_task(auto_joke(app))

    # اجرای ربات
    app.run_polling()
