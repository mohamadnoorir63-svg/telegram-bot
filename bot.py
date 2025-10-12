import asyncio
import os
import random
import zipfile
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from memory_manager import (
    init_files, load_data, save_data, learn, shadow_learn,
    merge_shadow_memory, get_reply, set_mode, get_stats,
    enhance_sentence, generate_sentence
)

# 🎯 تنظیمات
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7089376754  # آیدی سودو
init_files()

# وضعیت ربات
status = {"active": True, "learning": True, "welcome": True, "last_joke": datetime.now()}


# ================== 🔹 دستورات عمومی ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("😎 خنگول 7.8 فول پلاس آماده‌ست! بیا یادم بده!")


async def mode_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("🎭 دستور: /mode شوخ / غمگین / نرمال / بی‌ادب")
    mood = context.args[0].lower()
    if mood in ["شوخ", "غمگین", "نرمال", "بی‌ادب"]:
        set_mode(mood)
        await update.message.reply_text(f"مود به {mood} تغییر کرد 😎")
    else:
        await update.message.reply_text("❌ مود نامعتبر است!")


async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not (update.effective_user.id == ADMIN_ID or update.effective_chat.get_member(update.effective_user.id).status in ["administrator", "creator"]):
        return
    status["active"] = not status["active"]
    await update.message.reply_text("✅ ربات فعال شد!" if status["active"] else "😴 ربات خاموش شد!")


async def toggle_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not (update.effective_user.id == ADMIN_ID or update.effective_chat.get_member(update.effective_user.id).status in ["administrator", "creator"]):
        return
    status["welcome"] = not status["welcome"]
    await update.message.reply_text("👋 خوشامد فعال شد!" if status["welcome"] else "🚫 خوشامد خاموش شد!")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    s = get_stats()
    await update.message.reply_text(f"📊 آمار خنگول:\nجملات: {s['phrases']}\nپاسخ‌ها: {s['responses']}\nمود فعلی: {s['mode']}")


async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("🫡 خدافظ! میرم ولی دلم برات تنگ میشه 😂")
        await context.bot.leave_chat(update.message.chat.id)


# ================== 💬 خوشامد ==================

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not status["welcome"]:
        return
    for member in update.message.new_chat_members:
        t = datetime.now().strftime("%H:%M")
        d = datetime.now().strftime("%Y-%m-%d")
        await update.message.reply_sticker("CAACAgIAAxkBAAEIBbVkn3IoRh6EPUbE4a7yR1yMG-4aFAACWQADVp29Cmb0vh8k0JtbNgQ")  # استیکر خوشامد
        await update.message.reply_text(
            f"🎉 خوش اومدی {member.first_name}!\n"
            f"🕒 ساعت: {t}\n📅 تاریخ: {d}\n🏠 گروه: {update.message.chat.title}\n😄 خوش بگذره!"
        )


# ================== 💬 پاسخ و یادگیری ==================

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
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

    # شوخی خودکار هر ساعت
    if datetime.now() - status["last_joke"] > timedelta(hours=1):
        await update.message.reply_text(random.choice([
            "می‌دونی فرق تو با خر چیه؟ هیچی فقط خر مودب‌تره 🤪",
            "من از بس باهات حرف زدم باهوش شدم 😎",
            "می‌خواستم جدی باشم ولی نمیشه با تو 😂"
        ]))
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
            await update.message.reply_text("❗ بعد از 'یادبگیر' جمله و پاسخ‌هاش رو با خط جدید بنویس.")
        return

    if text == "لیست":
        phrases = list(load_data("memory.json").get("data", {}).keys())
        if phrases:
            await update.message.reply_text("🧾 جملات یادگرفته شده:\n" + "\n".join(phrases[:20]))
        else:
            await update.message.reply_text("هنوز چیزی یاد نگرفتم 😅")
        return

    if text == "جمله بساز":
        await update.message.reply_text(generate_sentence())
        return

    reply_text = get_reply(text)
    reply_text = enhance_sentence(reply_text)
    await update.message.reply_text(reply_text)


# ================== 📨 ارسال همگانی ==================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    msg = " ".join(context.args)
    if not msg:
        return await update.message.reply_text("❗ بعد از /broadcast پیام رو بنویس.")

    users = load_data("memory.json").get("users", [])
    count = 0
    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=msg)
            count += 1
        except:
            pass
    await update.message.reply_text(f"✅ پیام به {count} کاربر ارسال شد.")


# ================== 💾 بک‌آپ و ری‌استور ==================

async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    filename = f"backup_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.zip"
    with zipfile.ZipFile(filename, "w") as zipf:
        for file in ["memory.json", "group_data.json", "stickers.json"]:
            if os.path.exists(file):
                zipf.write(file)
    await update.message.reply_document(document=open(filename, "rb"), filename=filename)
    await update.message.reply_text("✅ پشتیبان گرفته شد و برات ارسال شد!")
    os.remove(filename)


async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("🔁 بازیابی انجام شد (در نسخه بعدی فعال می‌شود).")


# ================== 🚀 اجرای ربات ==================

if __name__ == "__main__":
    print("🤖 خنگول فارسی 7.8 فول پلاس آماده به خدمت است ...")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mode", mode_change))
    app.add_handler(CommandHandler("toggle", toggle))
    app.add_handler(CommandHandler("welcome", toggle_welcome))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("leave", leave))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("backup", backup))
    app.add_handler(CommandHandler("restore", restore))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    try:
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        print("🛑 خاموش شدن ربات...")
    finally:
        import asyncio
        loop = asyncio.get_event_loop()
        if not loop.is_closed():
            loop.close()
