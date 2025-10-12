import asyncio
import random
import os
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from memory_manager import (
    init_files, load_data, save_data, learn, shadow_learn,
    merge_shadow_memory, get_reply, set_mode, get_stats, enhance_sentence
)

# ====================== تنظیمات پایه ======================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7089376754  # آیدی سودو (مدیر اصلی)
init_files()

status = {
    "active": True,
    "learning": True,
    "last_joke": datetime.now(),
    "welcome": True
}


# ====================== ✳️ دستورات پایه ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🤖 خنگول فارسی 7.6 با موفقیت فعال شد!\nبیا ببینم چی می‌خوای ازم یاد بگیری 😜"
    await update.message.reply_text(msg)


async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return
    status["active"] = not status["active"]
    await update.message.reply_text(
        "✅ خنگول فعال شد!" if status["active"] else "💤 خنگول خاموش شد!"
    )


async def learn_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return
    status["learning"] = not status["learning"]
    if status["learning"]:
        merge_shadow_memory()
        await update.message.reply_text("📚 یادگیری دوباره فعال شد!")
    else:
        await update.message.reply_text("😴 یادگیری خاموش شد (در حالت پنهان ادامه دارد!)")


async def mode_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return
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
    if not await is_admin(update):
        return
    data = get_stats()
    msg = (
        f"📊 آمار خنگول:\n"
        f"• جملات: {data['phrases']}\n"
        f"• پاسخ‌ها: {data['responses']}\n"
        f"• مود فعلی: {data['mode']}\n"
    )
    await update.message.reply_text(msg)


# ====================== 👋 خوشامد ======================

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not status["welcome"]:
        return
    member = update.message.new_chat_members[0]
    group = update.message.chat.title
    now = datetime.now().strftime("%Y-%m-%d ⏰ %H:%M")
    msg = f"🎉 خوش اومدی {member.mention_html()} به گروه <b>{group}</b>!\n📅 {now}"
    await update.message.reply_html(msg)


async def toggle_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return
    arg = context.args[0].lower() if context.args else ""
    if arg == "on":
        status["welcome"] = True
        await update.message.reply_text("👋 خوشامدگویی فعال شد!")
    elif arg == "off":
        status["welcome"] = False
        await update.message.reply_text("🔕 خوشامدگویی غیرفعال شد!")
    else:
        await update.message.reply_text("⚙️ استفاده صحیح: /welcome on یا /welcome off")


# ====================== 📨 ارسال همگانی ======================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    # حالت مستقیم: /broadcast پیام
    if context.args:
        message = " ".join(context.args)
    else:
        await update.message.reply_text("📝 پیام بعدی که می‌فرستی به همه ارسال میشه.")
        context.user_data["await_broadcast"] = True
        return

    await send_broadcast(update, context, message)


async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("await_broadcast") and update.effective_user.id == ADMIN_ID:
        message = update.message.text
        context.user_data["await_broadcast"] = False
        await send_broadcast(update, context, message)


async def send_broadcast(update, context, message):
    def safe_load(filename):
        try:
            return load_data(filename)
        except:
            save_data(filename, {})
            return {}

    groups = safe_load("group_data.json")
    memory = safe_load("memory.json")
    users = memory.get("users", [])

    sent, failed = 0, 0
    for chat_id in list(groups.keys()) + users:
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
            sent += 1
        except:
            failed += 1

    await update.message.reply_text(f"✅ ارسال موفق به {sent} چت\n⚠️ ناموفق: {failed}")


# ====================== 💬 پاسخ و یادگیری ======================

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user_id = update.effective_user.id

    # ذخیره کاربران
    data = load_data("memory.json")
    data.setdefault("users", [])
    if user_id not in data["users"]:
        data["users"].append(user_id)
        save_data("memory.json", data)

    # وضعیت فعال نبودن
    if not status["active"]:
        if status["learning"]:
            shadow_learn(text, "")
        return

    # شوخی خودکار هر ساعت
    if datetime.now() - status["last_joke"] > timedelta(hours=1):
        await update.message.reply_text(random.choice([
            "می‌دونی فرق تو با خر چیه؟ 😜 هیچی فقط خر مودب‌تره!",
            "من از بس با شما حرف زدم باهوش شدم 😎",
            "می‌خواستم جدی باشم ولی نمیشه با تو 😂"
        ]))
        status["last_joke"] = datetime.now()

    # یادگیری دستی
    if text.startswith("یادبگیر "):
        parts = text.replace("یادبگیر ", "").split("\n")
        if len(parts) > 1:
            phrase = parts[0]
            for p in parts[1:]:
                learn(phrase, p)
            await update.message.reply_text(f"🧠 یاد گرفتم {len(parts) - 1} پاسخ برای '{phrase}'!")
        else:
            await update.message.reply_text("❗ بعد از 'یادبگیر' بنویس جمله و پاسخ‌هاش رو با خط جدید جدا کن.")
        return

    # پاسخ معمولی
    reply_text = enhance_sentence(get_reply(text))
    await update.message.reply_text(reply_text)


# ====================== 🧷 توابع کمکی ======================

async def is_admin(update: Update):
    """بررسی اینکه کاربر سودو یا مدیر گروهه"""
    user = update.effective_user
    chat = update.effective_chat
    if user.id == ADMIN_ID:
        return True
    if chat.type in ["group", "supergroup"]:
        member = await chat.get_member(user.id)
        return member.status in ["administrator", "creator"]
    return False


# ====================== 🚀 اجرای ربات ======================

if __name__ == "__main__":
    print("🤖 خنگول فارسی 7.6 نهایی آماده به خدمت است ...")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("toggle", toggle))
    app.add_handler(CommandHandler("learn", learn_mode))
    app.add_handler(CommandHandler("mode", mode_change))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("welcome", toggle_welcome))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID), broadcast_message))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    app.run_polling()
