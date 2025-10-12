import asyncio
import random
import os
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from memory_manager import (
    init_files, load_data, save_data, learn, shadow_learn,
    merge_shadow_memory, get_reply, get_mode, set_mode,
    get_stats, enhance_sentence
)

# 🔑 تنظیمات اولیه
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7089376754  # آیدی مدیر
init_files()

# 🧠 وضعیت‌ها
status = {"active": True, "learning": True, "welcome": True, "last_joke": datetime.now()}

# 🎴 استیکرهای خوشامد
WELCOME_STICKERS = [
    "CAACAgQAAxkBAAEFZ7dlcMuDGz4GdjvJt2bqWJqPBuYcNwAC9QADVp29Cq5MlK4mD1LqNgQ",
    "CAACAgUAAxkBAAEFZ7tlcMuwY5TuPQABomE5pWIEUEyN2k0AAg4AA6t8rAR5-xb2PMshpDYE",
    "CAACAgUAAxkBAAEFZ71lcMu6UcvJY-6TJPj6zIuE2eAqKwACuQADVp29CsjIX1vH3W9eNgQ"
]


# ========================= ✳️ دستورات =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🤖 خنگول فول 7.1 با موفقیت روشن شد!\nبگو چی یاد بگیرم؟ 😎"
    await update.message.reply_text(msg)


async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """خاموش یا روشن کردن ربات"""
    status["active"] = not status["active"]
    await update.message.reply_text("✅ خنگول روشن شد!" if status["active"] else "💤 خنگول خاموش شد!")


async def toggle_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """خاموش یا روشن کردن خوشامد"""
    status["welcome"] = not status["welcome"]
    await update.message.reply_text("🎉 خوشامد فعال شد!" if status["welcome"] else "🚫 خوشامد خاموش شد!")


async def learn_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """روشن یا خاموش کردن یادگیری"""
    status["learning"] = not status["learning"]
    if status["learning"]:
        merge_shadow_memory()
        await update.message.reply_text("📚 یادگیری فعال شد!")
    else:
        await update.message.reply_text("😴 یادگیری غیرفعال شد (پنهانی ادامه دارد!)")


async def mode_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تغییر مود گفتار"""
    if not context.args:
        await update.message.reply_text("🎭 دستور استفاده: /mode شوخ / بی‌ادب / غمگین / نرمال")
        return
    mood = context.args[0].lower()
    if mood in ["شوخ", "بی‌ادب", "غمگین", "نرمال"]:
        set_mode(mood)
        await update.message.reply_text(f"مود به {mood} تغییر کرد 😎")
    else:
        await update.message.reply_text("❌ مود نامعتبر است!")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار حافظه"""
    data = get_stats()
    msg = (
        f"📊 آمار خنگول فول:\n"
        f"• جملات: {data['phrases']}\n"
        f"• پاسخ‌ها: {data['responses']}\n"
        f"• مود فعلی: {data['mode']}\n"
    )
    await update.message.reply_text(msg)


# ========================= 🎉 خوشامد =========================

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not status["welcome"]:
        return
    for member in update.message.new_chat_members:
        time_str = datetime.now().strftime("%H:%M")
        date_str = datetime.now().strftime("%Y-%m-%d")
        chat_title = update.message.chat.title
        welcome_text = (
            f"🎉 خوش اومدی {member.first_name}!\n"
            f"🕒 ساعت: {time_str}\n"
            f"📅 تاریخ: {date_str}\n"
            f"📍 گروه: {chat_title}"
        )
        await update.message.reply_text(welcome_text)
        await update.message.reply_sticker(random.choice(WELCOME_STICKERS))


# ========================= 📨 ارسال همگانی =========================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پیام همگانی برای همه کاربران"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    if len(context.args) == 0:
        return await update.message.reply_text("📨 استفاده: /broadcast متن پیام")

    message = " ".join(context.args)
    data = load_data("memory.json")
    users = data.get("users", [])
    sent = 0
    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=message)
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✅ پیام به {sent} کاربر ارسال شد!")


# ========================= 💬 پاسخ به پیام =========================

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    # ثبت کاربر
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


# ========================= 🚀 اجرای ربات =========================

if __name__ == "__main__":
    print("🤖 خنگول فول 7.1 آماده به خدمت است ...")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("toggle", toggle))
    app.add_handler(CommandHandler("toggle_welcome", toggle_welcome))
    app.add_handler(CommandHandler("learn", learn_mode))
    app.add_handler(CommandHandler("mode", mode_change))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    app.run_polling()
