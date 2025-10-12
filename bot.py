import json
import random
import os

# مسیر فایل‌های حافظه
MAIN_MEMORY = "memory.json"
SHADOW_MEMORY = "shadow_memory.json"
GROUP_MEMORY = "group_data.json"


# 🧠 اگر فایل‌ها وجود نداشتن، بسازشون
def init_files():
    for file_name, default_data in [
        (MAIN_MEMORY, {"replies": {}, "learning": True, "mode": "normal"}),
        (SHADOW_MEMORY, {"hidden": {}}),
        (GROUP_MEMORY, {}),
    ]:
        if not os.path.exists(file_name):
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)


# 📂 خواندن داده‌ها از فایل
def load_data(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        return json.load(f)


# 💾 ذخیره داده‌ها در فایل
def save_data(file_name, data):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 🔄 گرفتن مود فعلی (شوخ، بی‌ادب، غمگین...)
def get_mode():
    data = load_data(MAIN_MEMORY)
    return data.get("mode", "normal")


# ✍️ تغییر مود
def set_mode(new_mode):
    data = load_data(MAIN_MEMORY)
    data["mode"] = new_mode
    save_data(MAIN_MEMORY, data)


# 💡 اضافه کردن جمله جدید به حافظه
def learn(phrase, response):
    data = load_data(MAIN_MEMORY)
    phrase = phrase.lower().strip()
    response = response.strip()

    if phrase not in data["replies"]:
        data["replies"][phrase] = []

    if response not in data["replies"][phrase]:
        data["replies"][phrase].append(response)

    save_data(MAIN_MEMORY, data)


# 🕵️ یادگیری پنهان در حالت خاموش
def shadow_learn(phrase, response):
    data = load_data(SHADOW_MEMORY)
    phrase = phrase.lower().strip()
    response = response.strip()

    if phrase not in data["hidden"]:
        data["hidden"][phrase] = []

    if response not in data["hidden"][phrase]:
        data["hidden"][phrase].append(response)

    save_data(SHADOW_MEMORY, data)


# 🔁 ادغام حافظه پنهان با اصلی وقتی روشن میشه
def merge_shadow_memory():
    main = load_data(MAIN_MEMORY)
    shadow = load_data(SHADOW_MEMORY)

    for phrase, replies in shadow.get("hidden", {}).items():
        if phrase not in main["replies"]:
            main["replies"][phrase] = replies
        else:
            for r in replies:
                if r not in main["replies"][phrase]:
                    main["replies"][phrase].append(r)

    shadow["hidden"] = {}
    save_data(MAIN_MEMORY, main)
    save_data(SHADOW_MEMORY, shadow)


# 🎲 گرفتن پاسخ تصادفی بر اساس مود
def get_reply(text):
    data = load_data(MAIN_MEMORY)
    replies = data.get("replies", {})
    text = text.lower().strip()

    if text in replies:
        return random.choice(replies[text])

    # اگر بلد نبود، یه جمله بامزه بسازه
    random_words = ["عه", "جدی؟", "باشه", "نمی‌دونم والا", "جالبه 😅", "اوه"]
    return random.choice(random_words)


# 📊 آمار حافظه
def get_stats():
    data = load_data(MAIN_MEMORY)
    total_phrases = len(data.get("replies", {}))
    total_responses = sum(len(v) for v in data["replies"].values())
    mode = data.get("mode", "normal")
    return {
        "phrases": total_phrases,
        "responses": total_responses,
        "mode": mode,
    }


# 🧩 تقویت طبیعی پاسخ‌ها (تغییر ساختار جمله)
def enhance_sentence(sentence):
    replacements = {
        "خوب": ["عالی", "باحال", "اوکی"],
        "نه": ["نخیر", "اصلاً", "نچ"],
        "آره": ["آرههه", "اوهوم", "قطعاً"],
    }

    words = sentence.split()
    new_words = []
    for word in words:
        if word in replacements and random.random() < 0.4:
            new_words.append(random.choice(replacements[word]))
        else:
            new_words.append(word)

    return " ".join(new_words)
    import asyncio
import random
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from memory_manager import (
    init_files, load_data, save_data, learn, shadow_learn,
    merge_shadow_memory, get_reply, get_mode, set_mode,
    get_stats, enhance_sentence
)

# 🔑 توکن از تنظیمات هاست
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7089376754  # آیدی تو

# 🧠 مقداردهی اولیه حافظه
init_files()

# 🔄 وضعیت برای کنترل یادگیری و فعال بودن ربات
status = {"active": True, "learning": True, "last_joke": datetime.now()}


# ========================= ✳️ دستورات =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "😜 نصب خنگول با موفقیت انجام شد!\n\nبیا ببینم چی می‌خوای ازم یاد بگیری!"
    await update.message.reply_text(msg)


async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["active"] = not status["active"]
    await update.message.reply_text("✅ خنگول فعال شد!" if status["active"] else "💤 خنگول خاموش شد!")


async def learn_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["learning"] = not status["learning"]
    if status["learning"]:
        merge_shadow_memory()
        await update.message.reply_text("📚 یادگیری دوباره فعال شد!")
    else:
        await update.message.reply_text("😴 یادگیری خاموش شد (در حالت پنهان ادامه دارد!)")


async def mode_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🎭 دستور استفاده: /mode شوخ / بی‌ادب / غمگین / نرمال")
        return
    mood = context.args[0].lower()
    if mood in ["شوخ", "بی‌ادب", "غمگین", "نرمال"]:
        set_mode(mood)
        await update.message.reply_text(f"مود به {mood} تغییر کرد 😎")
    else:
        await update.message.reply_text("❌ مود نامعتبر است!")


async def leave_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        await update.message.reply_text("🫡 خدافظ! من رفتم ولی دلم برات تنگ میشه 😂")
        await context.bot.leave_chat(update.message.chat_id)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_stats()
    msg = (
        f"📊 آمار خنگول:\n"
        f"• تعداد جملات: {data['phrases']}\n"
        f"• پاسخ‌ها: {data['responses']}\n"
        f"• مود فعلی: {data['mode']}\n"
    )
    await update.message.reply_text(msg)


# ========================= ⚙️ پنل مدیر =========================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه وارد پنل بشه!")

    keyboard = [
        [InlineKeyboardButton("📨 ارسال همگانی", callback_data="broadcast")],
        [InlineKeyboardButton("📊 آمار", callback_data="stats")],
        [InlineKeyboardButton("🧠 وضعیت یادگیری", callback_data="learn_status")],
        [InlineKeyboardButton("💤 خاموش / روشن", callback_data="toggle_bot")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔧 پنل مدیریتی خنگول", reply_markup=markup)


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "stats":
        s = get_stats()
        await query.edit_message_text(
            f"📈 آمار خنگول:\n"
            f"جملات: {s['phrases']}\nپاسخ‌ها: {s['responses']}\nمود فعلی: {s['mode']}"
        )

    elif data == "learn_status":
        text = "✅ فعال" if status["learning"] else "🚫 غیرفعال"
        await query.edit_message_text(f"📚 وضعیت یادگیری: {text}")

    elif data == "toggle_bot":
        status["active"] = not status["active"]
        await query.edit_message_text("⚙️ وضعیت: فعال ✅" if status["active"] else "😴 خنگول خاموش شد!")

    elif data == "broadcast":
        await query.edit_message_text("پیامت رو بنویس تا به همه چت‌ها ارسال کنم:")
        context.user_data["broadcast_mode"] = True


# ========================= 💬 پاسخ به پیام =========================

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not status["active"]:
        # یادگیری پنهان
        if status["learning"]:
            shadow_learn(text, "")
        return

    # شوخی خودکار هر ساعت
    if datetime.now() - status["last_joke"] > timedelta(hours=1):
        joke = random.choice([
            "می‌دونی فرق تو با خر چیه؟ 😜 هیچی، فقط خر مودب‌تره!",
            "من از بس با شما حرف زدم باهوش شدم 😎",
            "می‌خواستم جدی باشم ولی نمیشه با تو 😂"
        ])
        await update.message.reply_text(joke)
        status["last_joke"] = datetime.now()

    # یادگیری دستی
    if text.startswith("یادبگیر "):
        parts = text.replace("یادبگیر ", "").split("\n")
        if len(parts) > 1:
            phrase = parts[0].strip()
            responses = [p.strip() for p in parts[1:] if p.strip()]
            for r in responses:
                learn(phrase, r)
            await update.message.reply_text(f"🧠 یاد گرفتم {len(responses)} پاسخ برای '{phrase}'!")
        else:
            await update.message.reply_text("❗ بعد از 'یادبگیر' بنویس جمله و پاسخ‌هاش رو با خط جدید جدا کن.")
        return

    # پاسخ دادن
    reply_text = get_reply(text)
    reply_text = enhance_sentence(reply_text)
    await update.message.reply_text(reply_text)


# ========================= 🚀 اجرای ربات =========================

if __name__ == "__main__":
    print("🤖 خنگول 6.0 آماده به خدمت است...")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", admin_panel))
    app.add_handler(CommandHandler("toggle", toggle))
    app.add_handler(CommandHandler("learn", learn_mode))
    app.add_handler(CommandHandler("mode", mode_change))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("leave", leave_group))
    app.add_handler(CallbackQueryHandler(admin_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    app.run_polling()
