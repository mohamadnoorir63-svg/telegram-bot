import asyncio
import random
import os
import json
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

# ========================= 🔑 تنظیمات اولیه =========================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7089376754  # آیدی مدیر اصلی
GROUP_FILE = "group_data.json"
USER_FILE = "users.json"

init_files()
status = {"active": True, "learning": True, "last_joke": datetime.now()}


# ========================= ⚙️ توابع کمکی =========================
def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)


# ========================= ✳️ دستورات =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "😜 خنگول با موفقیت راه افتاد!\n\nبیا ببینم چی می‌خوای ازم یاد بگیری!"
    await update.message.reply_text(msg)

    # ثبت کاربر
    user_id = str(update.effective_user.id)
    users = load_json(USER_FILE)
    if user_id not in users:
        users[user_id] = {"name": update.effective_user.first_name}
        save_json(USER_FILE, users)


async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["active"] = not status["active"]
    msg = "✅ خنگول فعال شد!" if status["active"] else "💤 خنگول خاموش شد!"
    await update.message.reply_text(msg)


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


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_stats()
    msg = (
        f"📊 آمار خنگول:\n"
        f"• جملات یاد گرفته: {data['phrases']}\n"
        f"• پاسخ‌ها: {data['responses']}\n"
        f"• مود فعلی: {data['mode']}\n"
    )
    await update.message.reply_text(msg)


# ========================= 📢 ارسال همگانی =========================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی اجازه ارسال همگانی دارد.")
    
    if not context.args:
        return await update.message.reply_text("📨 استفاده: /broadcast <متن پیام>")
    
    message = " ".join(context.args)
    sent = 0

    users = load_json(USER_FILE)
    groups = load_json(GROUP_FILE)

    for uid in users.keys():
        try:
            await context.bot.send_message(chat_id=uid, text=message)
            sent += 1
        except:
            pass

    for gid in groups.keys():
        try:
            await context.bot.send_message(chat_id=gid, text=message)
            sent += 1
        except:
            pass

    await update.message.reply_text(f"✅ پیام به {sent} چت ارسال شد!")


# ========================= 💬 پاسخ به پیام =========================
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    text = update.message.text.strip()
    user_id = str(update.effective_user.id)

    # ثبت گروه یا کاربر برای ارسال همگانی
    if chat.type in ["group", "supergroup"]:
        groups = load_json(GROUP_FILE)
        if str(chat.id) not in groups:
            groups[str(chat.id)] = {"title": chat.title}
            save_json(GROUP_FILE, groups)
    else:
        users = load_json(USER_FILE)
        if user_id not in users:
            users[user_id] = {"name": update.effective_user.first_name}
            save_json(USER_FILE, users)

    # بررسی وضعیت فعال بودن
    if not status["active"]:
        if status["learning"]:
            shadow_learn(text, "")
        return

    # شوخی خودکار
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

    # پاسخ‌دهی
    reply_text = get_reply(text)
    if reply_text:
        reply_text = enhance_sentence(reply_text)
        await update.message.reply_text(reply_text)


# ========================= 🚀 اجرای ربات =========================
if __name__ == "__main__":
    print("🤖 خنگول فارسی 6.5 آماده به خدمت است ...")
    app = ApplicationBuilder().token(TOKEN).build()

    # دستورات اصلی
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("toggle", toggle))
    app.add_handler(CommandHandler("learn", learn_mode))
    app.add_handler(CommandHandler("mode", mode_change))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))

    # پاسخ به پیام‌های عادی
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    app.run_polling()
