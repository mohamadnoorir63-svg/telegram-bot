import asyncio
import random
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

# 🔑 تنظیمات اصلی
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7089376754  # آیدی سودو (مدیر اصلی)

# 🧠 مقداردهی اولیه فایل‌ها
init_files()

# وضعیت‌های کلی
status = {
    "active": True,
    "learning": True,
    "welcome": True,
    "last_joke": datetime.now()
}

# ========================= ✳️ دستورات =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "😜 خنگول فارسی با موفقیت فعال شد!\n\nبرای دیدن راهنما دستور /help رو بفرست."
    await update.message.reply_text(msg)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📘 راهنمای خنگول 7.5\n\n"
        "🧠 یادگیری:\n"
        "یادبگیر جمله\nپاسخ اول\nپاسخ دوم...\n\n"
        "🎭 مودها:\n/mode شوخ | بی‌ادب | غمگین | نرمال\n\n"
        "⚙️ کنترل‌ها:\n"
        "/toggle - روشن/خاموش ربات\n"
        "/learn - روشن/خاموش یادگیری\n"
        "/welcome - روشن/خاموش خوشامد\n"
        "/stats - آمار حافظه (فقط سودو)\n"
        "/broadcast - ارسال همگانی (فقط سودو)\n"
        "/leave - خروج از گروه (فقط سودو)\n"
        "/backup - بکاپ دستی حافظه (فقط سودو)\n"
    )
    await update.message.reply_text(msg)

# ========================= ⚙️ کنترل وضعیت =========================

async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_or_sudo(update):
        return
    status["active"] = not status["active"]
    msg = "✅ خنگول فعال شد!" if status["active"] else "💤 خنگول خاموش شد!"
    await update.message.reply_text(msg)

async def learn_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_or_sudo(update):
        return
    status["learning"] = not status["learning"]
    if status["learning"]:
        merge_shadow_memory()
        await update.message.reply_text("📚 یادگیری دوباره فعال شد!")
    else:
        await update.message.reply_text("😴 یادگیری خاموش شد (در حالت پنهان ادامه دارد!)")

async def welcome_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_or_sudo(update):
        return
    status["welcome"] = not status["welcome"]
    msg = "👋 خوشامد فعال شد!" if status["welcome"] else "🚫 خوشامد غیرفعال شد!"
    await update.message.reply_text(msg)

async def mode_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🎭 استفاده: /mode شوخ | بی‌ادب | غمگین | نرمال")
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
        f"📊 آمار خنگول:\n"
        f"• جملات: {data['phrases']}\n"
        f"• پاسخ‌ها: {data['responses']}\n"
        f"• مود فعلی: {data['mode']}\n"
    )
    await update.message.reply_text(msg)

# ========================= 📨 ارسال و بکاپ =========================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) == 0:
        await update.message.reply_text("✏️ بعد از دستور /broadcast پیام خود را بنویس.")
        return
    message = " ".join(context.args)
    groups = load_data("group_data.json")
    sent = 0
    for chat_id in groups.keys():
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✅ پیام به {sent} گروه ارسال شد!")

async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("🫡 خداحافظ، من رفتم!")
    await context.bot.leave_chat(update.message.chat_id)

async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    import shutil
    os.makedirs("backups", exist_ok=True)
    shutil.copy("memory.json", f"backups/memory_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    await update.message.reply_text("💾 بکاپ از حافظه گرفته شد!")

# ========================= 👋 خوشامد =========================

async def welcome_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not status["welcome"]:
        return
    for member in update.message.new_chat_members:
        now = datetime.now().strftime("%Y/%m/%d ⏰ %H:%M")
        text = (
            f"👋 خوش اومدی {member.first_name}!\n"
            f"📅 تاریخ: {now}\n"
            f"🏠 گروه: {update.message.chat.title}"
        )
        await update.message.reply_text(text)

# ========================= 💬 پاسخ و یادگیری =========================

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not status["active"]:
        if status["learning"]:
            shadow_learn(text, "")
        return

    # شوخی خودکار
    if datetime.now() - status["last_joke"] > timedelta(hours=1):
        joke = random.choice([
            "می‌دونی فرق تو با خر چیه؟ 😜 هیچی فقط خر مودب‌تره!",
            "من از بس با شما حرف زدم باهوش شدم 😎",
            "می‌خواستم جدی باشم ولی با تو نمیشه 😂"
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

    # پاسخ طبیعی
    reply_text = get_reply(text)
    reply_text = enhance_sentence(reply_text)
    await update.message.reply_text(reply_text)

# ========================= 🔐 بررسی ادمین =========================

async def is_admin_or_sudo(update: Update):
    if update.effective_user.id == ADMIN_ID:
        return True
    chat_member = await update.effective_chat.get_member(update.effective_user.id)
    return chat_member.status in ["administrator", "creator"]

# ========================= 🚀 اجرای ربات =========================

if __name__ == "__main__":
    print("🤖 خنگول فارسی 7.5 نهایی آماده به خدمت است ...")
    app = ApplicationBuilder().token(TOKEN).build()

    # فرمان‌ها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("mode", mode_change))
    app.add_handler(CommandHandler("toggle", toggle))
    app.add_handler(CommandHandler("learn", learn_mode))
    app.add_handler(CommandHandler("welcome", welcome_toggle))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("leave", leave))
    app.add_handler(CommandHandler("backup", backup))

    # خوشامد به کاربران جدید
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_user))

    # پیام‌های معمولی
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    app.run_polling()
