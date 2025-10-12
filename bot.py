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

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7089376754
init_files()

status = {"active": True, "learning": True, "welcome": True, "last_joke": datetime.now()}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "😜 خنگول آماده‌ست! بیا ببینم چی می‌خوای یادم بدی!"
    await update.message.reply_text(msg)


async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه این کارو بکنه!")
    status["active"] = not status["active"]
    await update.message.reply_text("✅ فعال شد!" if status["active"] else "😴 خاموش شد!")


async def learn_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    status["learning"] = not status["learning"]
    if status["learning"]:
        merge_shadow_memory()
        await update.message.reply_text("📚 یادگیری دوباره فعال شد!")
    else:
        await update.message.reply_text("😴 یادگیری خاموش شد (در حالت پنهان ادامه دارد!)")


async def mode_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("🎭 دستور استفاده: /mode شوخ / بی‌ادب / غمگین / نرمال")
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
    msg = f"📊 آمار:\nجملات: {data['phrases']}\nپاسخ‌ها: {data['responses']}\nمود: {data['mode']}"
    await update.message.reply_text(msg)


async def toggle_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    status["welcome"] = not status["welcome"]
    await update.message.reply_text("👋 خوشامد فعال شد!" if status["welcome"] else "🚫 خوشامد غیرفعال شد!")


async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not status["welcome"]:
        return
    for member in update.message.new_chat_members:
        time_str = datetime.now().strftime("%H:%M")
        date_str = datetime.now().strftime("%Y-%m-%d")
        group_name = update.message.chat.title
        msg = (
            f"🎉 خوش اومدی {member.first_name}!\n"
            f"🕒 ساعت: {time_str}\n📅 تاریخ: {date_str}\n🏠 گروه: {group_name}\n"
            f"امیدوارم خوش بگذره 😄"
        )
        await update.message.reply_text(msg)


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    message = " ".join(context.args)
    if not message:
        return await update.message.reply_text("❗ بعد از /broadcast پیام رو بنویس")
    users = load_data("memory.json").get("users", [])
    count = 0
    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=message)
            count += 1
        except:
            pass
    await update.message.reply_text(f"✅ پیام به {count} کاربر ارسال شد!")


async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    uid = update.effective_user.id

    data = load_data("memory.json")
    if "users" not in data:
        data["users"] = []
    if uid not in data["users"]:
        data["users"].append(uid)
        save_data("memory.json", data)

    if not status["active"]:
        if status["learning"]:
            shadow_learn(text, "")
        return

    if datetime.now() - status["last_joke"] > timedelta(hours=1):
        await update.message.reply_text(random.choice([
            "من خنگ نیستم 😅 فقط بامزه‌ام!",
            "یکم استراحت بده دیگه 😂",
            "بیا باهم یاد بگیریم 😎"
        ]))
        status["last_joke"] = datetime.now()

    if text.startswith("یادبگیر "):
        parts = text.replace("یادبگیر ", "").split("\n")
        if len(parts) > 1:
            phrase, responses = parts[0].strip(), [p.strip() for p in parts[1:] if p.strip()]
            for r in responses:
                learn(phrase, r)
            return await update.message.reply_text(f"🧠 یاد گرفتم {len(responses)} پاسخ برای '{phrase}'!")
        return await update.message.reply_text("❗ بعد از یادبگیر جمله و پاسخ‌ها رو بنویس.")

    await update.message.reply_text(enhance_sentence(get_reply(text)))


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
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    try:
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except (KeyboardInterrupt, SystemExit):
        print("🛑 در حال خاموش شدن ...")
    finally:
        import asyncio
        try:
            asyncio.get_event_loop().close()
        except RuntimeError:
            pass
