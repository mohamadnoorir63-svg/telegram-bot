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
    filters,
)
from memory_manager import (
    init_files, load_data, save_data, learn, shadow_learn,
    merge_shadow_memory, get_reply, get_mode, set_mode,
    get_stats, enhance_sentence
)

# 🔑 توکن از محیط هاست
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7089376754  # آیدی مدیر اصلی

# 🧠 مقداردهی اولیه حافظه
init_files()

# 🔄 وضعیت‌ها
status = {
    "active": True,
    "learning": True,
    "welcome": True,
    "last_joke": datetime.now()
}


# ========================= ✳️ دستورات اصلی =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "😜 خنگول 7.2 با موفقیت فعال شد!\nبیا ببینم چی می‌خوای ازم یاد بگیری!"
    await update.message.reply_text(msg)


async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["active"] = not status["active"]
    await update.message.reply_text("✅ خنگول روشن شد!" if status["active"] else "💤 خنگول خاموش شد!")


async def learn_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["learning"] = not status["learning"]
    if status["learning"]:
        merge_shadow_memory()
        await update.message.reply_text("📚 یادگیری دوباره فعال شد!")
    else:
        await update.message.reply_text("😴 یادگیری خاموش شد (در حالت پنهان ادامه دارد!)")


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


async def welcome_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["welcome"] = not status["welcome"]
    await update.message.reply_text("👋 خوش‌آمد روشن شد!" if status["welcome"] else "🚫 خوش‌آمد خاموش شد!")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_stats()
    users = load_data("memory.json").get("users", [])
    groups = load_data("group_data.json")
    msg = (
        f"📊 آمار خنگول:\n"
        f"• جملات: {data['phrases']}\n"
        f"• پاسخ‌ها: {data['responses']}\n"
        f"• کاربران: {len(users)}\n"
        f"• گروه‌ها: {len(groups)}\n"
        f"• مود فعلی: {data['mode']}"
    )
    await update.message.reply_text(msg)


async def leave_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ["group", "supergroup"]:
        await update.message.reply_text("🫡 خدافظ! من رفتم ولی دلم برات تنگ میشه 😂")
        await context.bot.leave_chat(update.message.chat_id)


# ========================= 📢 ارسال همگانی =========================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("📨 دستور: /broadcast پیام_شما")
        return

    message = " ".join(context.args)
    groups = load_data("group_data.json")
    users = load_data("memory.json").get("users", [])
    sent = 0

    for chat_id in list(groups.keys()) + users:
        try:
            await context.bot.send_message(chat_id=int(chat_id), text=message)
            sent += 1
        except:
            pass

    await update.message.reply_text(f"✅ پیام به {sent} چت ارسال شد!")


# ========================= 👋 خوش‌آمد به اعضای جدید =========================

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not status["welcome"]:
        return

    for member in update.message.new_chat_members:
        name = member.first_name
        group_name = update.message.chat.title
        time_now = datetime.now().strftime("%H:%M:%S")
        date_now = datetime.now().strftime("%Y-%m-%d")

        text = (
            f"👋 خوش اومدی {name}!\n"
            f"به گروه 🌟 {group_name}\n"
            f"🕒 ساعت: {time_now}\n📅 تاریخ: {date_now}"
        )
        await update.message.reply_text(text)


# ========================= 💬 پاسخ‌گویی و یادگیری =========================

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat = update.effective_chat
    user_id = update.effective_user.id

    # ذخیره خودکار کاربر یا گروه
    if chat.type in ["group", "supergroup"]:
        data = load_data("group_data.json")
        if str(chat.id) not in data:
            data[str(chat.id)] = {"title": chat.title}
            save_data("group_data.json", data)
    else:
        data = load_data("memory.json")
        if "users" not in data:
            data["users"] = []
        if user_id not in data["users"]:
            data["users"].append(user_id)
            save_data("memory.json", data)

    # در حالت خاموش فقط یادگیری پنهان
    if not status["active"]:
        if status["learning"]:
            shadow_learn(text, "")
        return

    # شوخی خودکار
    if datetime.now() - status["last_joke"] > timedelta(hours=1):
        joke = random.choice([
            "می‌دونی فرق تو با خر چیه؟ 😜 هیچی فقط خر مودب‌تره!",
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

    # پاسخ‌دهی
    reply_text = get_reply(text)
    reply_text = enhance_sentence(reply_text)
    await update.message.reply_text(reply_text)


# ========================= 🚀 اجرای ربات =========================

if __name__ == "__main__":
    print("🤖 خنگول فارسی 7.2 آماده به خدمت است ...")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("toggle", toggle))
    app.add_handler(CommandHandler("learn", learn_mode))
    app.add_handler(CommandHandler("mode", mode_change))
    app.add_handler(CommandHandler("welcome", welcome_toggle))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("leave", leave_group))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    app.run_polling()
