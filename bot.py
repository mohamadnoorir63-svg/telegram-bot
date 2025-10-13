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


# ======================= 👤 ثبت کاربر =======================
def register_user(user_id):
    """ثبت خودکار کاربران در حافظه"""
    data = load_data("memory.json")
    users = data.get("users", [])
    if user_id not in users:
        users.append(user_id)
        data["users"] = users
        save_data("memory.json", data)


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
    try:
        data = load_data("group_data.json")
        groups = data.get("groups", {})

        if isinstance(groups, list):
            if not groups:
                return await update.message.reply_text("ℹ️ هنوز هیچ گروهی ثبت نشده.")
            text = "📈 آمار کامل گروه‌ها:\n\n"
            for g in groups:
                gid = g.get("id", "نامشخص")
                title = g.get("title", f"Group_{gid}")
                members = len(g.get("members", []))
                last = g.get("last_active", "نامشخص")
                try:
                    chat = await context.bot.get_chat(gid)
                    if chat.title:
                        title = chat.title
                except:
                    pass
                text += f"🏠 گروه: {title}\n👥 اعضا: {members}\n🕓 آخرین فعالیت: {last}\n\n"
        elif isinstance(groups, dict):
            if not groups:
                return await update.message.reply_text("ℹ️ هنوز هیچ گروهی ثبت نشده.")
            text = "📈 آمار کامل گروه‌ها:\n\n"
            for gid, info in groups.items():
                title = info.get("title", f"Group_{gid}")
                members = len(info.get("members", []))
                last = info.get("last_active", "نامشخص")
                try:
                    chat = await context.bot.get_chat(gid)
                    if chat.title:
                        title = chat.title
                except:
                    pass
                text += f"🏠 گروه: {title}\n👥 اعضا: {members}\n🕓 آخرین فعالیت: {last}\n\n"
        else:
            return await update.message.reply_text("⚠️ ساختار group_data.json نامعتبر است!")

        if len(text) > 4000:
            text = text[:3990] + "..."

        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در آمار گروه‌ها:\n{e}")


# ======================= 👋 خوشامد =======================
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


# ======================= ☁️ بک‌آپ =======================
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
                    zipf.write(os.path.join(root, file))
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


# ======================= 💬 پاسخ و یادگیری =======================
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    uid = update.effective_user.id
    chat_id = update.effective_chat.id

    register_user(uid)
    register_group_activity(chat_id, uid)

    if not status["locked"]:
        auto_learn_from_text(text)

    if not status["active"]:
        shadow_learn(text, "")
        return

    # ✅ جوک‌ها و فال‌ها
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
                except Exception as e:
                    await update.message.reply_text(f"⚠️ خطا در ارسال جوک: {e}")
            else:
                await update.message.reply_text("هیچ جوکی ثبت نشده 😅")
        return

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
                except Exception as e:
                    await update.message.reply_text(f"⚠️ خطا در ارسال فال: {e}")
            else:
                await update.message.reply_text("هیچ فالی ثبت نشده 😔")
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

    if text == "جمله بساز":
        await update.message.reply_text(generate_sentence())
        return

    learned_reply = get_reply(text)
    if learned_reply:
        reply_text = enhance_sentence(learned_reply)
    else:
        emotion = detect_emotion(text)
        reply_text = smart_response(text, emotion) or enhance_sentence(text)

    await update.message.reply_text(reply_text)


# ======================= 📨 ارسال همگانی =======================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)
    if not msg:
        return await update.message.reply_text("❗ بعد از /broadcast پیام را بنویس.")

    data_users = load_data("memory.json").get("users", [])
    data_groups = load_data("group_data.json").get("groups", {})

    group_ids = []
    if isinstance(data_groups, dict):
        group_ids = list(data_groups.keys())
    elif isinstance(data_groups, list):
        group_ids = [g.get("id") for g in data_groups if "id" in g]

    sent = 0
    failed = 0

    # 📩 ارسال به کاربران
    for uid in data_users:
        try:
            await context.bot.send_message(chat_id=uid, text=msg)
            sent += 1
        except:
            failed += 1

    # 📢 ارسال به گروه‌ها
    for gid in group_ids:
        try:
            await context.bot.send_message(chat_id=int(gid), text=msg)
            sent += 1
        except:
            failed += 1

    await update.message.reply_text(f"📨 پیام به {sent} چت ارسال شد ✅\n⚠️ شکست‌خورده: {failed}")


# ======================= 🚪 خروج از گروه =======================
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("🫡 خدافظ! تا دیدار بعدی 😂")
        await context.bot.leave_chat(update.message.chat.id)


# ======================= 🚀 اجرای نهایی =======================
if __name__ == "__main__":
    print("🤖 خنگول فارسی 8.5.1 Cloud+ Supreme Pro Stable+ آماده به خدمت است ...")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_error_handler(handle_error)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("toggle", toggle))
    app.add_handler(CommandHandler("welcome", toggle_welcome))
    app.add_handler(CommandHandler("lock", lock_learning))
    app.add_handler(CommandHandler("unlock", unlock_learning))
    app.add_handler(CommandHandler("mode", mode_change))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("fullstats", fullstats))
    app.add_handler(CommandHandler("backup", cloudsync))
    app.add_handler(CommandHandler("reset", start))
    app.add_handler(CommandHandler("reload", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("leave", leave))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    async def on_startup(app):
        await notify_admin_on_startup(app)
        app.create_task(auto_backup(app))
        print("🌙 [SYSTEM] Startup tasks scheduled✅")

    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)
