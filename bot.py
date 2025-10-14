import asyncio
import os
import random
import zipfile
from datetime import datetime
from telegram import Update, InputFile, ChatMember
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import aiofiles
import shutil

# 📦 ماژول‌ها
from memory_manager import (
    init_files, load_data, save_data, learn, shadow_learn, get_reply,
    set_mode, get_stats, enhance_sentence, generate_sentence, list_phrases
)
from jokes_manager import save_joke, list_jokes
from fortune_manager import save_fortune, list_fortunes
from group_manager import register_group_activity, get_group_stats
from ai_learning import auto_learn_from_text
from smart_reply import detect_emotion, smart_response
from emotion_memory import remember_emotion, get_last_emotion, emotion_context_reply
from auto_brain.auto_brain import start_auto_brain_loop

# 🎯 تنظیمات پایه
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))
init_files()

# ⚙️ وضعیت سیستم
status = {
    "active": True,
    "learning": True,
    "welcome": True,
    "locked": False,
    "replay_mode": False  # 🆕 حالت جدید ریپلی
}

# 🧠 بررسی اینکه کاربر مدیر گروه است یا نه
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER] or user_id == ADMIN_ID
    except:
        return False

# ======================= ✳️ شروع و پیام فعال‌سازی =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 خنگول فارسی 8.5.1 Cloud+ Supreme Pro Stable+\n"
        "📘 برای دیدن لیست دستورات بنویس: راهنما"
    )

async def notify_admin_on_startup(app):
    """ارسال پیام فعال‌سازی به ادمین هنگام استارت"""
    try:
        await app.bot.send_message(
            chat_id=ADMIN_ID,
            text="🚀 ربات خنگول با موفقیت فعال شد ✅"
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

# ======================= 🎭 تغییر مود =======================
async def mode_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تغییر مود فقط توسط مدیران و سودو"""
    if not await is_admin(update, context):
        return await update.message.reply_text("⛔ فقط مدیران گروه یا مدیر اصلی مجازند!")

    if not context.args:
        return await update.message.reply_text("🎭 استفاده: /mode شوخ / بی‌ادب / غمگین / نرمال")

    mood = context.args[0].lower()
    if mood in ["شوخ", "بی‌ادب", "غمگین", "نرمال"]:
        set_mode(mood)
        await update.message.reply_text(f"🎭 مود به {mood} تغییر کرد 😎")
    else:
        await update.message.reply_text("❌ مود نامعتبر است!")

# ======================= 🗣 حالت ریپلی =======================
async def toggle_replay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """روشن یا خاموش کردن حالت ریپلی — فقط مدیران یا سودو"""
    if not await is_admin(update, context):
        return await update.message.reply_text("⛔ فقط مدیران گروه یا مدیر اصلی مجازند!")

    status["replay_mode"] = not status["replay_mode"]
    if status["replay_mode"]:
        await update.message.reply_text("💬 حالت ریپلی فعال شد — فقط با ریپلای جواب می‌دم 😇")
    else:
        await update.message.reply_text("💬 حالت ریپلی غیرفعال شد — به همه جواب می‌دم 😎")# ======================= 📘 راهنمای قابل ویرایش =======================
HELP_FILE = "custom_help.txt"

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش help — فقط برای مدیر اصلی (سودو)"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ این دستور فقط برای مدیر اصلی فعاله!")

    if not os.path.exists(HELP_FILE):
        return await update.message.reply_text(
            "ℹ️ هنوز هیچ متنی برای راهنما ثبت نشده.\n"
            "می‌تونی با ریپلای و نوشتن «ثبت راهنما» تنظیمش کنی."
        )
    async with aiofiles.open(HELP_FILE, "r", encoding="utf-8") as f:
        text = await f.read()
    await update.message.reply_text(text)

async def show_custom_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور 'راهنما' — فقط برای مدیران و سودو"""
    if not await is_admin(update, context):
        return await update.message.reply_text("⛔ فقط مدیران گروه یا مدیر اصلی می‌تونن راهنما رو ببینن!")

    if not os.path.exists(HELP_FILE):
        return await update.message.reply_text(
            "ℹ️ هنوز هیچ متنی برای راهنما ثبت نشده.\n"
            "مدیر اصلی می‌تونه با ریپلای و نوشتن «ثبت راهنما» تنظیمش کنه."
        )
    async with aiofiles.open(HELP_FILE, "r", encoding="utf-8") as f:
        text = await f.read()
    await update.message.reply_text(text)

async def save_custom_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ذخیره متن راهنما با ریپلای (فقط توسط ADMIN_ID)"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    if not update.message.reply_to_message or not update.message.reply_to_message.text:
        return await update.message.reply_text("❗ برای ثبت راهنما باید روی یک پیام متنی ریپلای کنی!")

    text = update.message.reply_to_message.text
    async with aiofiles.open(HELP_FILE, "w", encoding="utf-8") as f:
        await f.write(text)

    await update.message.reply_text("✅ متن راهنما ذخیره شد!")

# ======================= ⚙️ کنترل وضعیت‌های مدیریتی =======================
async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """روشن و خاموش کردن ربات — فقط برای سودو"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ این دستور فقط برای مدیر اصلی فعاله!")
    status["active"] = not status["active"]
    await update.message.reply_text("✅ فعال شد!" if status["active"] else "😴 خاموش شد!")

async def toggle_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """روشن یا خاموش کردن خوشامد — مدیران یا سودو"""
    if not await is_admin(update, context):
        return await update.message.reply_text("⛔ فقط مدیران گروه یا مدیر اصلی مجازند!")

    status["welcome"] = not status["welcome"]
    await update.message.reply_text("👋 خوشامد فعال شد!" if status["welcome"] else "🚫 خوشامد غیرفعال شد!")

async def lock_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قفل کردن یادگیری — فقط سودو"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    status["locked"] = True
    await update.message.reply_text("🔒 یادگیری قفل شد!")

async def unlock_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """باز کردن یادگیری — فقط سودو"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    status["locked"] = False
    await update.message.reply_text("🔓 یادگیری باز شد!")# ======================= 💬 پاسخ و هوش مصنوعی =======================
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاسخ‌دهی اصلی ربات — با کنترل ریپلی و سطح دسترسی"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    uid = update.effective_user.id
    chat_id = update.effective_chat.id

    # اگر ربات خاموشه
    if not status["active"]:
        return

    # ✅ کنترل ریپلی در گروه‌ها
    if update.message.chat.type in ["group", "supergroup"]:
        # وقتی ریپلی روشنه
        if status["replay_mode"]:
            # فقط اگر روی پیامش ریپلای شده جواب بده
            if not update.message.reply_to_message or update.message.reply_to_message.from_user.id != (await context.bot.get_me()).id:
                # پاسخ به "خنگول کجایی" وقتی ریپلی روشنه
                if "خنگول کجایی" in text:
                    await update.message.reply_text("اینجام 😋 داشتی دنبالم می‌گشتی؟")
                return  # ❌ جواب نده مگر ریپلای شده باشه

    # ثبت کاربر و گروه
    from group_manager import register_group_activity
    register_group_activity(chat_id, uid)

    # فقط سودو بتونه دستورهای هوش رو اجرا کنه
    if text.lower() in ["درصد هوش", "درصد هوش اجتماعی", "هوش کلی"]:
        if uid != ADMIN_ID:
            return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه این اطلاعات رو ببینه!")

    # ==================== 💡 درصد هوش کلی و جزئی ====================
    if text.lower() == "درصد هوش":
        data = load_data("memory.json")
        phrases = len(data.get("phrases", {}))
        jokes = len(load_data("jokes.json"))
        fortunes = len(load_data("fortunes.json"))
        score = min(100, phrases + jokes + fortunes)
        await update.message.reply_text(f"🧠 درصد هوش فعلی: {score}%")
        return

    if text.lower() == "درصد هوش اجتماعی":
        groups_data = load_data("group_data.json").get("groups", {})
        users = len(load_data("memory.json").get("users", []))
        groups = len(groups_data) if isinstance(groups_data, dict) else len(groups_data)
        score = min(100, (users + groups * 5))
        await update.message.reply_text(f"🤝 درصد هوش اجتماعی: {score}%")
        return

    if text.lower() == "هوش کلی":
        await update.message.reply_text("🤖 IQ کلی خنگول: 132\n🌟 نابغه دیجیتال 😎")
        return

    # ==================== 😂 جوک / فال ====================
    if text == "جوک":
        data = load_data("jokes.json")
        if not data:
            return await update.message.reply_text("هنوز جوکی ندارم 😅")
        key, val = random.choice(list(data.items()))
        v = val.get("value", "")
        if val.get("type") == "text":
            await update.message.reply_text("😂 " + v)
        elif val.get("type") == "photo":
            await update.message.reply_photo(photo=v, caption="😂 جوک تصویری!")
        elif val.get("type") == "video":
            await update.message.reply_video(video=v, caption="😂 جوک ویدیویی!")
        elif val.get("type") == "sticker":
            await update.message.reply_sticker(sticker=v)
        return

    if text == "فال":
        data = load_data("fortunes.json")
        if not data:
            return await update.message.reply_text("فالی بلد نیستم 😔")
        key, val = random.choice(list(data.items()))
        v = val.get("value", "")
        if val.get("type") == "text":
            await update.message.reply_text("🔮 " + v)
        elif val.get("type") == "photo":
            await update.message.reply_photo(photo=v, caption="🔮 فال تصویری!")
        elif val.get("type") == "video":
            await update.message.reply_video(video=v, caption="🔮 فال ویدیویی!")
        elif val.get("type") == "sticker":
            await update.message.reply_sticker(sticker=v)
        return

    # ==================== ✍️ یادبگیر (فقط برای سودو) ====================
    if text.startswith("یادبگیر "):
        if uid != ADMIN_ID:
            return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه یادم بده!")

        parts = text.replace("یادبگیر ", "").split("\n")
        if len(parts) > 1:
            phrase = parts[0].strip()
            responses = [p.strip() for p in parts[1:] if p.strip()]
            msg = learn(phrase, *responses)
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("❗ بعد از 'یادبگیر' جمله و پاسخ‌هاش رو با خط جدید بنویس.")
        return

    # ==================== 🧠 یادگیری و پاسخ طبیعی ====================
    if not status["locked"]:
        from ai_learning import auto_learn_from_text
        auto_learn_from_text(text)

    learned_reply = get_reply(text)
    emotion = detect_emotion(text)

    if learned_reply:
        await update.message.reply_text(learned_reply)
    else:
        response = smart_response(text, emotion)
        if response:
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("هوم... مطمئن نیستم 😅")# ======================= ☁️ بک‌آپ و بازیابی فقط برای سودو =======================
async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بک‌آپ محلی (فقط مدیر اصلی)"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"backup_{now}.zip"

    try:
        with zipfile.ZipFile(filename, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk("."):
                for file in files:
                    full_path = os.path.join(root, file)
                    if full_path.endswith(".json"):
                        zipf.write(full_path)
        with open(filename, "rb") as f:
            await update.message.reply_document(document=f, filename=filename)
        await update.message.reply_text("✅ بک‌آپ کامل گرفته شد!")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بک‌آپ: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت فایل ZIP برای بازیابی"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    await update.message.reply_text("📂 فایل ZIP بک‌آپ را ارسال کن تا بازیابی شود.")
    context.user_data["await_restore"] = True

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بازیابی بک‌آپ ZIP (فقط سودو)"""
    if not context.user_data.get("await_restore"):
        return
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith(".zip"):
        return await update.message.reply_text("❗ لطفاً فایل ZIP معتبر بفرست.")

    restore_zip = "restore.zip"
    try:
        tg_file = await doc.get_file()
        await tg_file.download_to_drive(restore_zip)

        with zipfile.ZipFile(restore_zip, "r") as zip_ref:
            zip_ref.extractall(".")
        await update.message.reply_text("✅ بازیابی موفقیت‌آمیز بود!")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بازیابی:\n{e}")
    finally:
        if os.path.exists(restore_zip):
            os.remove(restore_zip)
        context.user_data["await_restore"] = False

# ======================= 🧹 ریست و ریلود =======================
async def reset_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    for f in ["memory.json", "group_data.json", "jokes.json", "fortunes.json"]:
        if os.path.exists(f):
            os.remove(f)
    init_files()
    await update.message.reply_text("🧹 تمام داده‌ها با موفقیت پاک شدند!")

async def reload_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    init_files()
    await update.message.reply_text("🔄 حافظه بارگذاری مجدد شد!")

# ======================= 📨 ارسال همگانی فقط سودو =======================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

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
    await update.message.reply_text(f"📨 ارسال به {sent} کاربر انجام شد ✅")

# ======================= 🚪 خروج از گروه =======================
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فقط مدیر اصلی"""
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("🫡 خدافظ! تا دیدار بعدی 😂")
        await context.bot.leave_chat(update.message.chat.id)

# ======================= 🚀 اجرای نهایی =======================
if __name__ == "__main__":
    print("🤖 خنگول فارسی 8.5.1 Cloud+ Supreme Pro Stable+ آماده به خدمت است ...")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_error_handler(handle_error)

    # 🔹 دستورات اصلی
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("mode", mode_change))
    app.add_handler(CommandHandler("toggle", toggle))
    app.add_handler(CommandHandler("welcome", toggle_welcome))
    app.add_handler(CommandHandler("lock", lock_learning))
    app.add_handler(CommandHandler("unlock", unlock_learning))
    app.add_handler(CommandHandler("backup", backup))
    app.add_handler(CommandHandler("restore", restore))
    app.add_handler(CommandHandler("reset", reset_memory))
    app.add_handler(CommandHandler("reload", reload_memory))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("leave", leave))
    app.add_handler(CommandHandler("replay", toggle_replay))

    # 🔹 راهنمای قابل ویرایش
    app.add_handler(MessageHandler(filters.Regex("^ثبت راهنما$"), save_custom_help))
    app.add_handler(MessageHandler(filters.Regex("^راهنما$"), show_custom_help))

    # 🔹 فایل‌ها و پیام‌ها
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    # 🔹 خوشامدگویی خودکار
    from telegram.ext import MessageHandler
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))

    # 🌙 راه‌اندازی خودکار
    async def on_startup(app):
        await notify_admin_on_startup(app)
        app.create_task(start_auto_brain_loop(app.bot))
        print("🌙 [SYSTEM] Startup tasks scheduled ✅")

    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)
