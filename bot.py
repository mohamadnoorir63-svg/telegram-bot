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

# 📦 ماژول‌ها
from memory_manager import (
    init_files, load_data, save_data, learn, shadow_learn,
    get_reply, set_mode, get_stats, enhance_sentence, generate_sentence
)
from jokes_manager import save_joke, list_jokes
from fortune_manager import save_fortune, list_fortunes
from group_manager import register_group_activity, get_group_stats
from ai_learning import auto_learn_from_text
from smart_reply import detect_emotion, smart_response

# 🎯 تنظیمات پایه
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))
init_files()

status = {
    "active": True,
    "learning": True,
    "welcome": True,
    "last_joke": datetime.now(),
    "locked": False
}

# ======================= ✳️ شروع و راهنما =======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 خنگول فارسی 8.1 هوشمند پلاس (Ultimate AI Edition)\n"
        "برای دیدن لیست دستورات بنویس: راهنما 📘"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📘 *راهنمای خنگول 8.1 هوشمند پلاس*\n\n"
        "🧠 یادگیری:\n"
        "▪️ `یادبگیر جمله` سپس در خطوط بعد پاسخ‌ها رو بنویس\n"
        "▪️ `لیست` → نمایش جملات یادگرفته‌شده\n"
        "▪️ `جمله بساز` → ساخت جمله تصادفی\n\n"
        "🧩 یادگیری خودکار:\n"
        "▫️ یادگیری خودکار از چت‌های کاربران و گروه‌ها فعال است\n"
        "▫️ می‌تونی با `/lock` قفلش کنی یا با `/unlock` بازش کنی\n\n"
        "😂 جوک و فال:\n"
        "▪️ ریپلای روی عکس یا متن بزن و بنویس: `ثبت جوک` یا `ثبت فال`\n"
        "▪️ لیست جوک‌ها و فال‌ها → نمایش همه موارد ذخیره‌شده\n\n"
        "⚙️ مدیریت:\n"
        "▪️ /toggle → روشن/خاموش کردن ربات\n"
        "▪️ /mode شوخ/بی‌ادب/غمگین/نرمال → تغییر مود\n"
        "▪️ /stats → نمایش آمار کامل کاربران و گروه‌ها\n"
        "▪️ /backup → بک‌آپ از کل داده‌ها\n"
        "▪️ /restore → بازیابی فایل ZIP بک‌آپ\n"
        "▪️ /broadcast → ارسال همگانی (فقط سودو)\n"
        "▪️ /leave → خروج از گروه (فقط سودو)\n"
        "▪️ /reset → پاک کردن کل حافظه (فقط سودو)\n"
        "▪️ /reload → بارگذاری مجدد حافظه بدون خاموشی\n\n"
        "👋 خوشامد:\n"
        "▪️ /welcome → روشن/خاموش کردن خوشامد خودکار\n\n"
        "😄 خنگول از همه گروه‌ها یاد می‌گیره و مودش رو خودش تشخیص می‌ده!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ======================= ⚙️ کنترل حالت =======================

async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["active"] = not status["active"]
    await update.message.reply_text("✅ فعال شد!" if status["active"] else "😴 خاموش شد!")

async def toggle_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["welcome"] = not status["welcome"]
    await update.message.reply_text("👋 خوشامد فعال شد!" if status["welcome"] else "🚫 خوشامد غیرفعال شد!")

async def lock_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["locked"] = True
    await update.message.reply_text("🔒 یادگیری قفل شد!")

async def unlock_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["locked"] = False
    await update.message.reply_text("🔓 یادگیری باز شد!")

# ======================= 📊 آمار =======================

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_stats()
    memory = load_data("memory.json")
    groups = len(load_data("group_data.json").get("groups", []))
    users = len(memory.get("users", []))
    msg = (
        f"📊 آمار خنگول:\n"
        f"👤 کاربران: {users}\n"
        f"👥 گروه‌ها: {groups}\n"
        f"🧩 جملات: {data['phrases']}\n"
        f"💬 پاسخ‌ها: {data['responses']}\n"
        f"🎭 مود فعلی: {data['mode']}"
    )
    await update.message.reply_text(msg)

# ======================= 💬 یادگیری و پاسخ =======================

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    uid = update.effective_user.id
    chat_id = update.effective_chat.id

    # ثبت گروه و کاربر
    register_group_activity(chat_id, uid)

    # یادگیری خودکار
    if not status["locked"]:
        auto_learn_from_text(text)

    # اگر غیرفعاله فقط ذخیره پنهان کن
    if not status["active"]:
        shadow_learn(text, "")
        return

    # دستور یادگیری دستی
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

    # لیست جملات
    if text == "لیست":
        phrases = list(load_data("memory.json").get("data", {}).keys())
        msg = "🧾 جملات یادگرفته‌شده:\n" + "\n".join(phrases[:40]) if phrases else "هیچی یاد نگرفتم 😅"
        await update.message.reply_text(msg)
        return

    # جوک و فال
    if text.lower() == "ثبت جوک" and update.message.reply_to_message:
        await save_joke(update)
        return
    if text.lower() == "ثبت فال" and update.message.reply_to_message:
        await save_fortune(update)
        return
    if text == "لیست جوک‌ها":
        await list_jokes(update)
        return
    if text == "لیست فال‌ها":
        await list_fortunes(update)
        return

    # پاسخ هوشمند
    emotion = detect_emotion(text)
    reply_text = smart_response(text, emotion)
    if not reply_text:
        reply_text = enhance_sentence(get_reply(text))

    await update.message.reply_text(reply_text)

# ======================= 📨 ارسال همگانی =======================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    msg = " ".join(context.args)
    if not msg:
        return await update.message.reply_text("❗ بعد از /broadcast پیام رو بنویس.")
    users = load_data("memory.json").get("users", [])
    sent = 0
    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=msg)
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✅ پیام به {sent} کاربر ارسال شد.")

# ======================= 💾 بک‌آپ و بازیابی =======================

async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filename = f"backup_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.zip"
    with zipfile.ZipFile(filename, "w") as zipf:
        for file in ["memory.json", "group_data.json", "stickers.json", "jokes.json", "fortunes.json"]:
            if os.path.exists(file):
                zipf.write(file)
    await update.message.reply_document(document=open(filename, "rb"), filename=filename)
    await update.message.reply_text("✅ بک‌آپ کامل گرفته شد!")
    os.remove(filename)

async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📂 فایل ZIP بک‌آپ را بفرست تا بازیابی شود.")
    context.user_data["await_restore"] = True

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("await_restore"):
        return
    file = await update.message.document.get_file()
    await file.download_to_drive("restore.zip")
    with zipfile.ZipFile("restore.zip", "r") as zip_ref:
        zip_ref.extractall(".")
    os.remove("restore.zip")
    await update.message.reply_text("✅ بازیابی کامل انجام شد!")
    context.user_data["await_restore"] = False

# ======================= 🚪 خروج از گروه =======================

async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("🫡 خدافظ! تا دیدار بعدی 😂")
        await context.bot.leave_chat(update.message.chat.id)

# ======================= 🚀 اجرای ربات =======================

if __name__ == "__main__":
    print("🤖 خنگول فارسی 8.1 نهایی هوشمند پلاس آماده به خدمت است ...")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("toggle", toggle))
    app.add_handler(CommandHandler("welcome", toggle_welcome))
    app.add_handler(CommandHandler("lock", lock_learning))
    app.add_handler(CommandHandler("unlock", unlock_learning))
    app.add_handler(CommandHandler("mode", mode_change))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("backup", backup))
    app.add_handler(CommandHandler("restore", restore))
    app.add_handler(CommandHandler("leave", leave))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    app.run_polling(allowed_updates=Update.ALL_TYPES)
