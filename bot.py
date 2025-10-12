import asyncio
import os
import random
import zipfile
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import aiofiles

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
    "locked": False
}

# ======================= ✳️ شروع و پیام فعال‌سازی =======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 خنگول فارسی 8.4 Cloud+ Supreme Edition\n"
        "برای دیدن لیست دستورات بنویس: راهنما 📘"
    )

async def notify_admin_on_startup(app):
    """ارسال پیام فعال‌سازی ربات به سودو در شروع"""
    try:
        await app.bot.send_message(
            chat_id=ADMIN_ID,
            text="🚀 ربات با موفقیت در سرور فعال شد و آماده به خدمت است ✅"
        )
        print("[INFO] Startup message sent to ADMIN ✅")
    except Exception as e:
        print(f"[ERROR] Failed to notify admin: {e}")

# ======================= 📘 راهنما =======================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📘 *راهنمای خنگول 8.4 Cloud+ Supreme*\n\n"
        "🧠 یادگیری:\n"
        "▪️ `یادبگیر جمله` سپس در خطوط بعد پاسخ‌ها رو بنویس\n"
        "▪️ `لیست` → نمایش جملات یادگرفته‌شده\n"
        "▪️ `جمله بساز` → ساخت جمله تصادفی\n\n"
        "☁️ یادگیری ابری:\n"
        "▫️ بک‌آپ خودکار هر ۱۲ ساعت انجام می‌شود و فقط برای سودو ارسال می‌شود\n"
        "▫️ `/cloudsync` → بک‌آپ ابری فوری\n\n"
        "😂 جوک و فال:\n"
        "▪️ `ثبت جوک` یا `ثبت فال` با ریپلای\n"
        "▪️ `لیست جوک‌ها` و `لیست فال‌ها`\n\n"
        "⚙️ مدیریت:\n"
        "▪️ /toggle → روشن/خاموش کردن ربات\n"
        "▪️ /welcome → فعال/غیرفعال کردن خوشامد خودکار\n"
        "▪️ /mode شوخ/بی‌ادب/غمگین/نرمال → تغییر مود\n"
        "▪️ /stats → آمار خلاصه\n"
        "▪️ /fullstats → آمار کامل گروه‌ها و کاربران\n"
        "▪️ /backup → بک‌آپ دستی ZIP\n"
        "▪️ /restore → بازیابی بک‌آپ ZIP\n"
        "▪️ /reset → پاک‌کردن کامل حافظه\n"
        "▪️ /reload → بارگذاری مجدد حافظه\n"
        "▪️ /broadcast → ارسال همگانی (فقط سودو)\n"
        "▪️ /leave → خروج از گروه\n\n"
        "👋 خوشامد:\n"
        "▪️ پیام خوش‌آمد با ساعت، تاریخ و نام گروه\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

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

async def lock_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["locked"] = True
    await update.message.reply_text("🔒 یادگیری قفل شد!")

async def unlock_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status["locked"] = False
    await update.message.reply_text("🔓 یادگیری باز شد!")

# ======================= 📊 آمار و آمار کامل =======================

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

async def fullstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_data = load_data("group_data.json").get("groups", {})
    text = "📈 آمار کامل گروه‌ها و اعضا:\n\n"
    for gid, info in group_data.items():
        text += f"🏠 گروه: {info.get('title', 'بدون‌نام')}\n"
        text += f"👥 اعضا: {len(info.get('members', []))}\n"
        text += f"🕓 آخرین فعالیت: {info.get('last_active', 'نامشخص')}\n\n"
    await update.message.reply_text(text if len(text) < 4000 else text[:3990] + "...")

# ======================= 👋 خوشامد =======================

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not status["welcome"]:
        return
    for member in update.message.new_chat_members:
        now = datetime.now()
        await update.message.reply_text(
            f"🎉 خوش اومدی {member.first_name}!\n"
            f"🕒 {now.strftime('%H:%M')} | 📅 {now.strftime('%Y-%m-%d')}\n"
            f"🏠 گروه: {update.message.chat.title}\n"
            f"😄 خوش اومدی به جمعمون!"
        )

# ======================= ☁️ بک‌آپ خودکار و دستی =======================

async def auto_backup(context: ContextTypes.DEFAULT_TYPE):
    while True:
        await asyncio.sleep(43200)
        await cloudsync_internal(context.bot, "Auto Backup")

async def cloudsync_internal(bot, reason="Manual Backup"):
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"backup_{now}.zip"
    with zipfile.ZipFile(filename, "w") as zipf:
        for file in ["memory.json", "group_data.json", "stickers.json", "jokes.json", "fortunes.json"]:
            if os.path.exists(file):
                zipf.write(file)
    try:
        await bot.send_document(chat_id=ADMIN_ID, document=open(filename, "rb"), filename=filename)
        await bot.send_message(chat_id=ADMIN_ID, text=f"☁️ {reason} انجام شد ✅")
        print(f"[CLOUD BACKUP] {reason} sent ✅")
    except Exception as e:
        print(f"[CLOUD BACKUP ERROR] {e}")
    finally:
        os.remove(filename)

async def cloudsync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await cloudsync_internal(context.bot, "Manual Cloud Backup")

# ======================= 💾 بک‌آپ و بازیابی دستی =======================

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
    context.user_data["await_restore"] = False
    await update.message.reply_text("✅ بازیابی کامل انجام شد!")

# ======================= 🧹 ریست و ریلود =======================

async def reset_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    for f in ["memory.json", "group_data.json", "stickers.json", "jokes.json", "fortunes.json"]:
        if os.path.exists(f):
            os.remove(f)
    init_files()
    await update.message.reply_text("🧹 تمام داده‌ها با موفقیت پاک شدند!")

async def reload_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_files()
    await update.message.reply_text("🔄 حافظه بارگذاری مجدد شد!")

# ======================= 📨 ارسال همگانی =======================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    msg = " ".join(context.args)
    if not msg:
        return await update.message.reply_text("❗ بعد از /broadcast پیام را بنویس.")
    users = load_data("memory.json").get("users", [])
    sent = 0
    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=msg)
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✅ پیام به {sent} کاربر ارسال شد.")

# ======================= 💬 پاسخ و یادگیری =======================

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
        msg = "🧾 جملات یادگرفته‌شده:\n" + "\n".join(phrases[:40]) if phrases else "هنوز چیزی یاد نگرفتم 😅"
        await update.message.reply_text(msg)
        return

    if text == "جمله بساز":
        await update.message.reply_text(generate_sentence())
        return

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

    emotion = detect_emotion(text)
    reply_text = smart_response(text, emotion) or enhance_sentence(get_reply(text))
    await update.message.reply_text(reply_text)

# ======================= 🚪 خروج از گروه =======================

async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("🫡 خدافظ! تا دیدار بعدی 😂")
        await context.bot.leave_chat(update.message.chat.id)
if __name__ == "__main__":
    print("🤖 خنگول فارسی 8.4 Cloud+ Supreme Edition آماده به خدمت است ...")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("toggle", toggle))
    app.add_handler(CommandHandler("welcome", toggle_welcome))
    app.add_handler(CommandHandler("lock", lock_learning))
    app.add_handler(CommandHandler("unlock", unlock_learning))
    app.add_handler(CommandHandler("mode", mode_change))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("fullstats", fullstats))
    app.add_handler(CommandHandler("backup", backup))
    app.add_handler(CommandHandler("restore", restore))
    app.add_handler(CommandHandler("reset", reset_memory))
    app.add_handler(CommandHandler("reload", reload_memory))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("cloudsync", cloudsync))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    app.add_handler(CommandHandler("leave", leave))

    # ✅ اصلاح‌شده برای هماهنگی با python-telegram-bot v20+
    async def on_startup(app):
        await notify_admin_on_startup(app)
        app.create_task(auto_backup(app))
        print("🌙 [SYSTEM] Startup tasks scheduled ✅")

    app.post_init = on_startup  # به‌جای create_task مستقیم

    app.run_polling(allowed_updates=Update.ALL_TYPES)
