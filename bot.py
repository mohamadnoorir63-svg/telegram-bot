import asyncio
import random
import os
from datetime import datetime, timedelta
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
    if not reply_text:
        return
    reply_text = enhance_sentence(reply_text)
    await update.message.reply_text(reply_text)


# ========================= 🚀 اجرای ربات =========================

if __name__ == "__main__":
    print("🤖 خنگول 6.0 آماده به خدمت است...")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler(["start", "شروع"], start))
    app.add_handler(CommandHandler(["toggle", "روشن"], toggle))
    app.add_handler(CommandHandler(["learn", "یادگیری"], learn_mode))
    app.add_handler(CommandHandler(["mode", "مود"], mode_change))
    app.add_handler(CommandHandler(["stats", "آمار"], stats))
    app.add_handler(CommandHandler(["leave", "خروج"], leave_group))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    app.run_polling()
