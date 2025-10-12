import asyncio
import os
import random
import zipfile
from datetime import datetime
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import aiofiles

# 📦 ماژول‌ها
from memory_manager import (
    init_files, load_data, save_data, learn, shadow_learn,
    get_reply, set_mode, get_stats, enhance_sentence,
    generate_sentence, list_phrases
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
    "locked": False
}

# ======================= ✳️ شروع و پیام فعال‌سازی =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 خنگول فارسی 8.5.1 Cloud+ Supreme Pro Stable+ Adamson Edition\n"
        "📘 برای دیدن لیست دستورات بنویس: راهنما"
    )

async def notify_admin_on_startup(app):
    try:
        await app.bot.send_message(
            chat_id=ADMIN_ID,
            text="🚀 Adamson Edition با موفقیت فعال شد ✅"
        )
        print("[INFO] Startup notification sent ✅")
    except Exception as e:
        print(f"[ERROR] Admin notify failed: {e}")

# ======================= ⚙️ خطایاب خودکار =======================
async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    error_text = f"⚠️ خطا در ربات:\n\n{context.error}"
    print(error_text)
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=error_text)
    except:
        pass

# ======================= 📘 راهنما =======================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📘 راهنمای Adamson Edition:\n\n"
        "🧠 یادگیری:\n"
        "▪️ یادبگیر جمله سپس در خطوط بعد پاسخ‌ها رو بنویس\n"
        "▪️ لیست → نمایش جملات یادگرفته‌شده\n"
        "▪️ جمله بساز → ساخت جمله تصادفی\n\n"
        "😂 جوک و فال:\n"
        "▪️ ثبت جوک یا ثبت فال با ریپلای (متن، عکس، ویدیو، استیکر)\n"
        "▪️ لیست جوک‌ها و لیست فال‌ها\n"
        "▪️ بنویس «جوک» یا «فال» برای تصادفی\n\n"
        "☁️ بک‌آپ:\n"
        "▫️ /cloudsync → بک‌آپ ابری\n"
        "▫️ /backup → فشرده در چت\n\n"
        "⚙️ مدیریت:\n"
        "▪️ /toggle ▪️ /welcome ▪️ /mode ▪️ /stats ▪️ /fullstats ▪️ /reset ▪️ /reload"
    )
    await update.message.reply_text(text)

# ======================= 🎭 تغییر مود =======================
async def mode_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("🎭 استفاده: /mode شوخ / بی‌ادب / غمگین / نرمال")
    mood = context.args[0].lower()
    if mood in ["شوخ", "بی‌ادب", "غمگین", "نرمال"]:
        set_mode(mood)
        await update.message.reply_text(f"🎭 مود به {mood} تغییر کرد 😎")
    else:
        await update.message.reply_text("❌ مود نامعتبر است!")

# ======================= ⚙️ کنترل وضعیت =======================
async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["active"] = not status["active"]
    await update.message.reply_text("✅ فعال شد!" if status["active"] else "😴 خاموش شد!")

async def toggle_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["welcome"] = not status["welcome"]
    await update.message.reply_text("👋 خوشامد فعال شد!" if status["welcome"] else "🚫 خوشامد غیرفعال شد!")

# ======================= 📊 آمار =======================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_stats()
    memory = load_data("memory.json")
    groups = len(load_data("group_data.json").get("groups", []))
    users = len(memory.get("users", []))
    msg = (
        f"📊 آمار ربات:\n"
        f"👤 کاربران: {users}\n"
        f"👥 گروه‌ها: {groups}\n"
        f"🧩 جملات: {data['phrases']}\n"
        f"💬 پاسخ‌ها: {data['responses']}\n"
        f"🎭 مود فعلی: {data['mode']}"
    )
    await update.message.reply_text(msg)

# ======================= 💬 پاسخ، یادگیری، جوک و فال =======================
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    uid = update.effective_user.id
    chat_id = update.effective_chat.id

    register_group_activity(chat_id, uid)
    if not status["locked"]:
        auto_learn_from_text(text)
    if not status["active"]:
        shadow_learn(text, "")
        return

    # ✅ جوک تصادفی
    if text == "جوک":
        if os.path.exists("jokes.json"):
            data = load_data("jokes.json")
            if data:
                key, val = random.choice(list(data.items()))
                t, v = val.get("type"), val.get("value")
                if t == "text":
                    await update.message.reply_text("😂 " + v)
                elif t == "photo":
                    await update.message.reply_photo(open(v, "rb"), caption="😂 جوک تصویری!")
                elif t == "sticker":
                    await update.message.reply_sticker(open(v, "rb"))
                elif t == "video":
                    await update.message.reply_video(open(v, "rb"))
            else:
                await update.message.reply_text("😅 هنوز جوکی ثبت نشده.")
        else:
            await update.message.reply_text("📂 فایل جوک‌ها وجود ندارد.")
        return

    # ✅ فال تصادفی
    if text == "فال":
        if os.path.exists("fortunes.json"):
            data = load_data("fortunes.json")
            if data:
                key, val = random.choice(list(data.items()))
                t, v = val.get("type"), val.get("value")
                if t == "text":
                    await update.message.reply_text("🔮 " + v)
                elif t == "photo":
                    await update.message.reply_photo(open(v, "rb"), caption="🔮 فال تصویری!")
                elif t == "sticker":
                    await update.message.reply_sticker(open(v, "rb"))
                elif t == "video":
                    await update.message.reply_video(open(v, "rb"))
            else:
                await update.message.reply_text("😔 هنوز فالی ثبت نشده.")
        else:
            await update.message.reply_text("📂 فایل فال‌ها وجود ندارد.")
        return

    # ✅ ثبت جوک یا فال
    if text.lower() == "ثبت جوک" and update.message.reply_to_message:
        await save_joke(update)
        return
    if text.lower() == "ثبت فال" and update.message.reply_to_message:
        await save_fortune(update)
        return

    # ✅ لیست‌ها
    if text == "لیست جوک‌ها":
        await list_jokes(update)
        return
    if text == "لیست فال‌ها":
        await list_fortunes(update)
        return

    # ✅ جمله تصادفی
    if text == "جمله بساز":
        await update.message.reply_text(generate_sentence())
        return

    # ✅ پاسخ هوشمند
    emotion = detect_emotion(text)
    reply_text = smart_response(text, emotion) or enhance_sentence(get_reply(text))
    await update.message.reply_text(reply_text)

# ======================= 🧹 ریست و ریلود =======================
async def reset_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    for f in ["memory.json", "group_data.json", "stickers.json", "jokes.json", "fortunes.json"]:
        if os.path.exists(f):
            os.remove(f)
    init_files()
    await update.message.reply_text("🧹 همه داده‌ها پاک شد!")

async def reload_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_files()
    await update.message.reply_text("🔄 حافظه بارگذاری مجدد شد!")

# ======================= 🚀 اجرای نهایی =======================
if __name__ == "__main__":
    print("🤖 Adamson Edition آماده به خدمت است ...")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_error_handler(handle_error)

    # 🧩 دستورات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("mode", mode_change))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("reset", reset_memory))
    app.add_handler(CommandHandler("reload", reload_memory))

    # 💬 پیام‌ها
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    async def on_startup(app):
        await notify_admin_on_startup(app)
        print("🌙 [SYSTEM] Adamson Edition Active ✅")

    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)
