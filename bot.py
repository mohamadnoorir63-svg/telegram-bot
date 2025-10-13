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
        "🤖 خنگول فارسی 8.5.1 Cloud+ Supreme Pro Stable+\n"
        "📘 برای دیدن لیست دستورات بنویس: راهنما"
    )

async def notify_admin_on_startup(app):
    try:
        await app.bot.send_message(
            chat_id=ADMIN_ID,
            text="🚀 ربات خنگول 8.5.1 Cloud+ Supreme Pro Stable+ با موفقیت فعال شد ✅"
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
        "📘 راهنمای خنگول فارسی 8.5.1 Cloud+ Supreme Pro Stable+\n\n"
        "🧠 یادگیری:\n"
        "▪️ یادبگیر جمله سپس در خطوط بعد پاسخ‌ها رو بنویس\n"
        "▪️ لیست → نمایش جملات یادگرفته‌شده\n"
        "▪️ جمله بساز → ساخت جمله تصادفی\n\n"
        "😂 جوک و فال:\n"
        "▪️ ثبت جوک یا ثبت فال با ریپلای\n"
        "▪️ لیست جوک‌ها و لیست فال‌ها\n"
        "▪️ بنویس «جوک» یا «فال» برای تصادفی\n\n"
        "☁️ بک‌آپ:\n"
        "▫️ خودکار هر ۱۲ ساعت برای سودو\n"
        "▫️ /cloudsync → بک‌آپ ابری دستی\n"
        "▫️ شامل json، عکس، صدا و استیکرها\n\n"
        "⚙️ مدیریت:\n"
        "▪️ /toggle → روشن/خاموش کردن ربات\n"
        "▪️ /welcome → فعال/غیرفعال کردن خوشامد\n"
        "▪️ /mode شوخ / غمگین / نرمال / بی‌ادب\n"
        "▪️ /stats → آمار خلاصه\n"
        "▪️ /fullstats → آمار کامل گروه‌ها\n"
        "▪️ /backup → بک‌آپ ZIP در چت\n"
        "▪️ /reset → پاک‌کردن کامل داده‌ها\n"
        "▪️ /reload → بارگذاری مجدد حافظه\n"
        "▪️ /broadcast → ارسال همگانی\n"
        "▪️ /leave → خروج از گروه\n"
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

# ======================= 📊 آمار خلاصه =======================
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

# ======================= 📊 آمار کامل گروه‌ها =======================
async def fullstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار کامل گروه‌ها و اعضا (سازگار با group_manager جدید)"""
    try:
        data = load_data("group_data.json")
        groups = data.get("groups", {})

        if not groups:
            return await update.message.reply_text("ℹ️ هنوز هیچ گروهی ثبت نشده.")

        text = "📈 آمار کامل گروه‌ها:\n\n"

        for group_id, info in groups.items():
            title = info.get("title", f"Group_{group_id}")
            members = len(info.get("members", []))
            last_active = info.get("last_active", "نامشخص")

            # 🎯 تلاش برای گرفتن نام واقعی گروه از تلگرام
            try:
                chat = await context.bot.get_chat(group_id)
                if chat.title:
                    title = chat.title
            except:
                pass

            text += f"🏠 گروه: {title}\n👥 اعضا: {members}\n🕓 آخرین فعالیت: {last_active}\n\n"

        if len(text) > 4000:
            text = text[:3990] + "..."

        await update.message.reply_text(text)

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در آمار گروه‌ها:\n{e}")

# ======================= 👋 خوشامد با عکس پروفایل =======================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not status["welcome"]:
        return
    for member in update.message.new_chat_members:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        text = (
            f"🎉 خوش اومدی {member.first_name}!\n"
            f"📅 {now}\n"
            f"🏠 گروه: {update.message.chat.title}\n"
            f"😄 امیدوارم لحظات خوبی داشته باشی!"
        )
        try:
            photos = await context.bot.get_user_profile_photos(member.id, limit=1)
            if photos.total_count > 0:
                file_id = photos.photos[0][-1].file_id
                await update.message.reply_photo(file_id, caption=text)
            else:
                await update.message.reply_text(text)
        except:
            await update.message.reply_text(text)

# ======================= ☁️ بک‌آپ خودکار و دستی =======================
async def auto_backup(context: ContextTypes.DEFAULT_TYPE):
    while True:
        await asyncio.sleep(43200)
        await cloudsync_internal(context.bot, "Auto Backup")

async def cloudsync_internal(bot, reason="Manual Backup"):
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"backup_{now}.zip"

    with zipfile.ZipFile(filename, "w") as zipf:
        for root, _, files in os.walk("."):
            for file in files:
                if file.endswith((".json", ".jpg", ".png", ".webp", ".mp3", ".ogg", ".zip")):
                    path = os.path.join(root, file)
                    zipf.write(path)

    try:
        await bot.send_document(chat_id=ADMIN_ID, document=open(filename, "rb"), filename=filename)
        await bot.send_message(chat_id=ADMIN_ID, text=f"☁️ {reason} انجام شد ✅")
    except Exception as e:
        print(f"[CLOUD BACKUP ERROR] {e}")
    finally:
        os.remove(filename)

async def cloudsync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await cloudsync_internal(context.bot, "Manual Cloud Backup")

# ======================= 💾 بک‌آپ و بازیابی ZIP در چت =======================
async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filename = f"backup_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.zip"
    with zipfile.ZipFile(filename, "w") as zipf:
        for root, _, files in os.walk("."):
            for file in files:
                if file.endswith((".json", ".jpg", ".png", ".webp", ".mp3", ".ogg")):
                    zipf.write(os.path.join(root, file))
    await update.message.reply_document(document=open(filename, "rb"), filename=filename)
    await update.message.reply_text("✅ بک‌آپ کامل گرفته شد!")
    os.remove(filename)


async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📂 فایل ZIP بک‌آپ را ارسال کن تا بازیابی شود.")
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
    await update.message.reply_text("✅ بازیابی کامل انجام شد!")# ======================= 💬 پاسخ، یادگیری، جوک و فال =======================
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

    # ✅ جوک تصادفی (پشتیبانی از عکس، ویدیو، استیکر و متن)
    if text == "جوک":
        if os.path.exists("jokes.json"):
            data = load_data("jokes.json")
            if data:
                key, val = random.choice(list(data.items()))
                t = val.get("type", "text")
                v = val.get("value", "")
                try:
                    if t == "text":
                        await update.message.reply_text("😂 " + v)
                    elif t == "photo":
                        await update.message.reply_photo(photo=open(v, "rb"), caption="😂 جوک تصویری!")
                    elif t == "video":
                        await update.message.reply_video(video=open(v, "rb"), caption="😂 جوک ویدیویی!")
                    elif t == "sticker":
                        await update.message.reply_sticker(sticker=open(v, "rb"))
                    else:
                        await update.message.reply_text("⚠️ نوع فایل پشتیبانی نمی‌شود.")
                except Exception as e:
                    await update.message.reply_text(f"⚠️ خطا در ارسال جوک: {e}")
            else:
                await update.message.reply_text("هنوز جوکی ثبت نشده 😅")
        else:
            await update.message.reply_text("📂 فایل جوک‌ها پیدا نشد 😕")
        return

    # ✅ فال تصادفی (پشتیبانی از عکس، ویدیو، استیکر و متن)
    if text == "فال":
        if os.path.exists("fortunes.json"):
            data = load_data("fortunes.json")
            if data:
                key, val = random.choice(list(data.items()))
                t = val.get("type", "text")
                v = val.get("value", "")
                try:
                    if t == "text":
                        await update.message.reply_text("🔮 " + v)
                    elif t == "photo":
                        await update.message.reply_photo(photo=open(v, "rb"), caption="🔮 فال تصویری!")
                    elif t == "video":
                        await update.message.reply_video(video=open(v, "rb"), caption="🔮 فال ویدیویی!")
                    elif t == "sticker":
                        await update.message.reply_sticker(sticker=open(v, "rb"))
                    else:
                        await update.message.reply_text("⚠️ نوع فایل پشتیبانی نمی‌شود.")
                except Exception as e:
                    await update.message.reply_text(f"⚠️ خطا در ارسال فال: {e}")
            else:
                await update.message.reply_text("هنوز فالی ثبت نشده 😔")
        else:
            await update.message.reply_text("📂 فایل فال‌ها پیدا نشد 😕")
        return

    # ✅ ثبت جوک و فال
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

    # ✅ لیست جملات
    if text == "لیست":
        await update.message.reply_text(list_phrases())
        return

    # ✅ یادگیری هوشمند
    if text.startswith("یادبگیر "):
        parts = text.replace("یادبگیر ", "").split("\n")
        if len(parts) > 1:
            phrase = parts[0].strip()
            responses = [p.strip() for p in parts[1:] if p.strip()]
            msg = learn(phrase, *responses)
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("❗ بعد از 'یادبگیر' جمله و پاسخ‌هاش رو با خط جدید بنویس.")
        return

    # ✅ جمله تصادفی
    if text == "جمله بساز":
        await update.message.reply_text(generate_sentence())
        return

    # ✅ پاسخ هوشمند و یادگیری واقعی
    learned_reply = get_reply(text)
    if learned_reply:
        reply_text = enhance_sentence(learned_reply)
    else:
        emotion = detect_emotion(text)
        reply_text = smart_response(text, emotion) or enhance_sentence(text)

    await update.message.reply_text(reply_text)
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
    await update.message.reply_text(f"📨 پیام به {sent} کاربر ارسال شد ✅")

# ======================= 🚪 خروج از گروه =======================
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("🫡 خدافظ! تا دیدار بعدی 😂")
        await context.bot.leave_chat(update.message.chat.id)

# ======================= 🚀 اجرای نهایی =======================
if name == "main":
    print("🤖 خنگول فارسی 8.5.1 Cloud+ Supreme Pro Stable+ آماده به خدمت است ...")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_error_handler(handle_error)

    # 🔹 دستورات اصلی
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
    app.add_handler(CommandHandler("leave", leave))

    # 🔹 پیام‌ها و اسناد
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    # 🔹 هنگام استارت
    async def on_startup(app):
        await notify_admin_on_startup(app)
        app.create_task(auto_backup(app))
        print("🌙 [SYSTEM] Startup tasks scheduled ✅")

    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)
