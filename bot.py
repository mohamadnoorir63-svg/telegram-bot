import asyncio
import random
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Sticker
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

# 🔑 دریافت توکن و شناسه مدیر
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7089376754  # آیدی تو

# 🧠 مقداردهی اولیه فایل‌های حافظه
init_files()

# 📊 وضعیت ربات
status = {"active": True, "learning": True, "last_joke": datetime.now()}

# 🎴 لیست استیکرهای خوشامد
WELCOME_STICKERS = [
    "CAACAgQAAxkBAAEFZ7dlcMuDGz4GdjvJt2bqWJqPBuYcNwAC9QADVp29Cq5MlK4mD1LqNgQ",
    "CAACAgUAAxkBAAEFZ7tlcMuwY5TuPQABomE5pWIEUEyN2k0AAg4AA6t8rAR5-xb2PMshpDYE",
    "CAACAgUAAxkBAAEFZ71lcMu6UcvJY-6TJPj6zIuE2eAqKwACuQADVp29CsjIX1vH3W9eNgQ"
]

# ✳️ شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "😜 خنگول فول نصب شد!\nبگو چی یاد بگیرم؟ 🤖"
    await update.message.reply_text(msg)

# 🔘 روشن / خاموش
async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["active"] = not status["active"]
    text = "✅ خنگول روشن شد!" if status["active"] else "💤 خنگول خاموش شد!"
    await update.message.reply_text(text)

# 🧠 فعال / غیرفعال‌سازی یادگیری
async def learn_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["learning"] = not status["learning"]
    if status["learning"]:
        merge_shadow_memory()
        await update.message.reply_text("📚 یادگیری فعال شد!")
    else:
        await update.message.reply_text("😴 یادگیری غیرفعال شد (پنهانی ادامه دارد!)")

# 🎭 تغییر مود
async def mode_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🎭 دستور: /mode شوخ / بی‌ادب / غمگین / نرمال")
        return
    mood = context.args[0].lower()
    if mood in ["شوخ", "بی‌ادب", "غمگین", "نرمال"]:
        set_mode(mood)
        await update.message.reply_text(f"مود به {mood} تغییر کرد 😎")
    else:
        await update.message.reply_text("❌ مود نامعتبر است!")

# 🧾 آمار
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_stats()
    msg = (
        f"📊 آمار خنگول فول:\n"
        f"• جملات: {data['phrases']}\n"
        f"• پاسخ‌ها: {data['responses']}\n"
        f"• مود فعلی: {data['mode']}\n"
    )
    await update.message.reply_text(msg)

# 💬 خوشامدگویی با تاریخ و ساعت
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        time_str = datetime.now().strftime("%H:%M")
        date_str = datetime.now().strftime("%Y-%m-%d")
        chat_title = update.message.chat.title
        welcome_text = f"🌟 خوش اومدی {member.first_name}!\n🕒 ساعت: {time_str}\n📅 تاریخ: {date_str}\n📍 گروه: {chat_title}"
        await update.message.reply_text(welcome_text)
        sticker_id = random.choice(WELCOME_STICKERS)
        await update.message.reply_sticker(sticker_id)

# 📨 ارسال همگانی فقط برای مدیر
async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.user_data.get("broadcast_mode"):
        return
    message = update.message.text
    context.user_data["broadcast_mode"] = False
    try:
        users = load_data("memory.json").get("users", [])
    except:
        users = []
    sent = 0
    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=message)
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✅ پیام به {sent} نفر ارسال شد!")

# 🎛 پنل مدیر
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    keyboard = [
        [InlineKeyboardButton("📨 ارسال همگانی", callback_data="broadcast")],
        [InlineKeyboardButton("📊 آمار", callback_data="stats")],
        [InlineKeyboardButton("💤 خاموش/روشن", callback_data="toggle")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔧 پنل مدیریتی خنگول فول", reply_markup=markup)

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "broadcast":
        await query.edit_message_text("پیام همگانی‌ت رو بنویس:")
        context.user_data["broadcast_mode"] = True
    elif query.data == "stats":
        s = get_stats()
        await query.edit_message_text(
            f"📈 آمار فعلی:\nجملات: {s['phrases']}\nپاسخ‌ها: {s['responses']}\nمود: {s['mode']}"
        )
    elif query.data == "toggle":
        status["active"] = not status["active"]
        await query.edit_message_text("✅ فعال شد" if status["active"] else "💤 خاموش شد")

# 💬 پاسخ‌ها
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    data = load_data("memory.json")
    if "users" not in data:
        data["users"] = []
    if user_id not in data["users"]:
        data["users"].append(user_id)
        save_data("memory.json", data)
    if not status["active"]:
        if status["learning"]:
            shadow_learn(text, "")
        return
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
    reply_text = get_reply(text)
    reply_text = enhance_sentence(reply_text)
    await update.message.reply_text(reply_text)

# 🚀 اجرای ربات
if __name__ == "__main__":
    print("🤖 خنگول فول 7.0 آماده به خدمت است ...")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("toggle", toggle))
    app.add_handler(CommandHandler("learn", learn_mode))
    app.add_handler(CommandHandler("mode", mode_change))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("panel", admin_panel))
    app.add_handler(CallbackQueryHandler(admin_callback))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID), broadcast_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    app.run_polling()
