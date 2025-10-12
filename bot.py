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
    get_stats, enhance_sentence, ai_sentence
)

# ========================= 🔑 تنظیمات اولیه =========================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7089376754  # آیدی مدیر اصلی (سودو)

init_files()

status = {
    "active": True,
    "learning": True,
    "welcome": True,
    "last_joke": datetime.now(),
}


# ========================= ✳️ دستورات عمومی =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🤖 سلام! من خنگول فارسی 7.4 هستم!\n"
        "🧠 هوشمند، خلاق و همیشه آماده برای یادگیری.\n\n"
        "برای دیدن راهنما بنویس:\n👉 /help"
    )
    await update.message.reply_text(msg)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📘 راهنمای خنگول فارسی 7.4\n\n"
        "🧠 یادگیری:\n"
        "یادبگیر جمله\nپاسخ ۱\nپاسخ ۲\n\n"
        "🎭 مودها: /mode شوخ / بی‌ادب / غمگین / نرمال\n"
        "💤 خاموش یا روشن کردن: /toggle\n"
        "📚 روشن/خاموش یادگیری: /learn\n"
        "👋 خوشامد روشن/خاموش: /welcome\n"
        "📊 آمار حافظه: /stats (فقط مدیر اصلی)\n"
        "📢 ارسال همگانی: /broadcast (فقط مدیر اصلی)\n"
        "🚪 خروج از گروه: /leave (فقط مدیر اصلی)\n"
    )
    await update.message.reply_text(msg)


async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    status["active"] = not status["active"]
    await update.message.reply_text("✅ فعال شد!" if status["active"] else "💤 خاموش شد!")


async def learn_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    status["learning"] = not status["learning"]
    if status["learning"]:
        merge_shadow_memory()
        await update.message.reply_text("📚 یادگیری فعال شد!")
    else:
        await update.message.reply_text("😴 یادگیری خاموش شد.")


async def mode_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🎭 استفاده: /mode شوخ / بی‌ادب / غمگین / نرمال")
        return
    mood = context.args[0].lower()
    if mood in ["شوخ", "بی‌ادب", "غمگین", "نرمال"]:
        set_mode(mood)
        await update.message.reply_text(f"مود به {mood} تغییر کرد 😎")
    else:
        await update.message.reply_text("❌ مود نامعتبر است!")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    data = get_stats()
    msg = (
        f"📊 آمار حافظه:\n"
        f"• جمله‌ها: {data['phrases']}\n"
        f"• پاسخ‌ها: {data['responses']}\n"
        f"• مود فعلی: {data['mode']}\n"
        f"• وضعیت یادگیری: {'فعال' if status['learning'] else 'خاموش'}"
    )
    await update.message.reply_text(msg)


async def leave_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID and update.message.chat.type != "private":
        await update.message.reply_text("👋 خدانگه‌دار! من رفتم 😜")
        await context.bot.leave_chat(update.message.chat_id)


# ========================= 👋 خوشامد =========================
async def welcome_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    status["welcome"] = not status["welcome"]
    await update.message.reply_text(
        "👋 خوشامد فعال شد!" if status["welcome"] else "🚫 خوشامد غیرفعال شد."
    )


async def welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not status["welcome"]:
        return
    for member in update.message.new_chat_members:
        now = datetime.now()
        text = (
            f"🎉 خوش اومدی {member.first_name}!\n\n"
            f"🕒 ساعت: {now.strftime('%H:%M')}\n"
            f"📅 تاریخ: {now.strftime('%Y/%m/%d')}\n"
            f"📍 گروه: {update.effective_chat.title}"
        )
        await update.message.reply_text(text)


# ========================= 📨 ارسال همگانی (فقط سودو) =========================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه این کار رو بکنه!")
    await update.message.reply_text("📢 پیامت رو بفرست تا به همه ارسال کنم:")
    context.user_data["broadcast_mode"] = True


async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.user_data.get("broadcast_mode"):
        return
    context.user_data["broadcast_mode"] = False
    text = update.message.text
    groups = load_data("group_data.json")
    sent = 0
    for gid in groups.keys():
        try:
            await context.bot.send_message(chat_id=gid, text=text)
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✅ پیام به {sent} گروه ارسال شد!")


# ========================= 💬 پاسخ خودکار و یادگیری =========================
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()

    if not status["active"]:
        if status["learning"]:
            shadow_learn(text, "")
        return

    if datetime.now() - status["last_joke"] > timedelta(hours=1):
        joke = random.choice([
            "می‌دونی فرق تو با خر چیه؟ 😜 هیچی، فقط خر مودب‌تره!",
            "من از بس با شما حرف زدم باهوش شدم 😎",
            "می‌خواستم جدی باشم ولی نشد 😂"
        ])
        await update.message.reply_text(joke)
        status["last_joke"] = datetime.now()

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
    if not reply_text:
        reply_text = ai_sentence(text)  # ساخت جمله جدید اگر چیزی بلد نبود
    reply_text = enhance_sentence(reply_text)
    await update.message.reply_text(reply_text)


# ========================= 🚀 اجرای ربات =========================
if __name__ == "__main__":
    print("🤖 خنگول فارسی 7.4 Ultimate AI آماده به خدمت است ...")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("toggle", toggle))
    app.add_handler(CommandHandler("learn", learn_mode))
    app.add_handler(CommandHandler("mode", mode_change))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("leave", leave_group))
    app.add_handler(CommandHandler("welcome", welcome_toggle))
    app.add_handler(CommandHandler("broadcast", broadcast))

    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID), broadcast_handler))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    app.run_polling()
