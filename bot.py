import json, random, os, asyncio
from telegram import Update, ChatMember
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, ChatMemberHandler
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
MEMORY_FILE = "memory.json"
OWNER_ID = 7089376754  # آیدی تو

# 📂 اگر فایل حافظه وجود ندارد، بساز
if not os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "active": True,
            "mode": "normal",
            "memory": {},
            "groups": []
        }, f, ensure_ascii=False, indent=2)


def load_data():
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ========================= پاسخ خنگول =========================
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data["active"]:
        return

    text = update.message.text.strip().lower()
    memory = data["memory"]
    mode = data["mode"]

    if text in memory:
        response = random.choice(memory[text])
    else:
        # تولید پاسخ خودکار بر اساس مود
        if mode == "بی ادب":
            response = random.choice(["برو بابا 😏", "چته دیگه؟ 😒", "مزاحم نشو الان 😤"])
        elif mode == "غمگین":
            response = random.choice(["دلم گرفته 😔", "هیچی حوصله ندارم 😢", "تنهاییم..."])
        elif mode == "شوخ":
            response = random.choice(["هاهاها 😂", "عه تو بازم اومدی؟ 😜", "می‌دونی من کی‌ام؟ سلطان خنده 😎"])
        else:
            response = random.choice(["عه جالبه 😁", "آره دقیقا همینه 😅", "درسته 😎"])

    await update.message.reply_text(response)

    # یادگیری خودکار
    if text not in memory:
        memory[text] = [response]
    elif response not in memory[text]:
        memory[text].append(response)

    save_data(data)


# ========================= یادگیری دستی =========================
user_learning = {}

async def learn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.replace("یادبگیر", "").strip()

    if not text:
        await update.message.reply_text("بعد از 'یادبگیر' بنویس چی می‌خوای یاد بگیرم 😄")
        return

    user_learning[user_id] = text
    await update.message.reply_text(f"باشه! حالا جواب‌های '{text}' رو یکی یکی بفرست، بعد بنویس «تموم» 😎")


async def collect_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if user_id not in user_learning:
        await reply(update, context)
        return

    data = load_data()
    key = user_learning[user_id]

    if text == "تموم":
        del user_learning[user_id]
        save_data(data)
        await update.message.reply_text("یاد گرفتم! 😁")
        return

    if key not in data["memory"]:
        data["memory"][key] = []
    data["memory"][key].append(text)
    save_data(data)
    await update.message.reply_text("ثبت شد ✅")


# ========================= کنترل روشن/خاموش =========================
async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if "روشن" in update.message.text:
        data["active"] = True
        msg = "خنگول روشن شد 🤪"
    else:
        data["active"] = False
        msg = "خنگول خاموش شد 😴"
    save_data(data)
    await update.message.reply_text(msg)


# ========================= تغییر مود =========================
async def change_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = update.message.text.strip()
    data = load_data()
    data["mode"] = mode
    save_data(data)
    await update.message.reply_text(f"مود من الان {mode} شد 😎")


# ========================= پنل مدیر =========================
async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        await update.message.reply_text("فقط صاحب من به پنل دسترسی داره 😏")
        return

    data = load_data()
    groups = len(data["groups"])
    mem = len(data["memory"])

    panel_text = (
        f"📊 پنل خنگول 🤖\n\n"
        f"🔹 گروه‌ها: {groups}\n"
        f"🔹 کلمات یادگرفته: {mem}\n"
        f"🔹 وضعیت: {'روشن' if data['active'] else 'خاموش'}\n"
        f"🔹 مود فعلی: {data['mode']}"
    )
    await update.message.reply_text(panel_text)


# ========================= شوخی خودکار =========================
async def auto_joke(app):
    jokes = [
        "می‌دونی چرا خنگول خندید؟ چون خودش رو تو آینه دید 😆",
        "رفتم سرکار، گفتن کارت چیه؟ گفتم خندوندن شما 😎",
        "اگه کسی ناراحتت کرد، منم ناراحتم 😢 ولی بعدش می‌خندیم 😂"
    ]
    while True:
        await asyncio.sleep(3600)  # هر ۱ ساعت
        for group_id in load_data().get("groups", []):
            try:
                await app.bot.send_message(chat_id=group_id, text=random.choice(jokes))
            except:
                pass


# ========================= خوش‌آمد =========================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    if result.new_chat_member.status == "member":
        name = result.new_chat_member.user.first_name
        await update.chat_member.chat.send_message(f"🎉 خوش اومدی {name} عزیز 😍")


# ========================= لفت بده =========================
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id == OWNER_ID:
        await update.message.reply_text("باشه من رفتم 😢")
        await context.bot.leave_chat(update.effective_chat.id)
    else:
        await update.message.reply_text("تو کی هستی که بگی برم؟ 😏")


# ========================= اجرای نهایی =========================
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

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^پنل$"), panel))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("یادبگیر"), learn))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("روشن|خاموش"), toggle))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("بی ادب|غمگین|شوخ|نورمال"), change_mode))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^لفت بده$"), leave))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_answers))
    app.add_handler(ChatMemberHandler(welcome, ChatMemberHandler.CHAT_MEMBER))

    async def main():
        asyncio.create_task(auto_joke(app))
        await app.run_polling()

    asyncio.run(main())
