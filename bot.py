import asyncio
import os
import random
import zipfile
from datetime import datetime
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler
)
import aiofiles

# 🧠 پنل پاسخ حرفه‌ای (Reply Panel Pro++)
from reply_panel_pro import add_reply_command, message_collector, button_handler, auto_reply

# 📦 ماژول‌های هوش و حافظه
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

status = {
    "active": True,
    "learning": True,
    "welcome": True,
    "locked": False
}
# ======================= 💬 ریپلی مود =======================
REPLY_FILE = "reply_status.json"

def load_reply_status():
    """خواندن وضعیت ریپلی مود برای همه گروه‌ها"""
    if os.path.exists(REPLY_FILE):
        try:
            import json
            with open(REPLY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_reply_status(data):
    """ذخیره وضعیت ریپلی مود برای همه گروه‌ها"""
    import json
    with open(REPLY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

reply_status = load_reply_status()

async def toggle_reply_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تغییر وضعیت ریپلی مود به‌صورت جداگانه برای هر گروه (فقط مدیران و سودو)"""
    user = update.effective_user
    chat = update.effective_chat
    chat_id_str = str(chat.id)

    # فقط داخل گروه مجاز است
    if chat.type == "private":
        return await update.message.reply_text("⛔ فقط داخل گروه می‌تونی ریپلی مود رو تغییر بدی!")

    # بررسی دسترسی (سودو یا مدیر)
    if user.id != ADMIN_ID:
        try:
            member = await context.bot.get_chat_member(chat.id, user.id)
            if member.status not in ["administrator", "creator"]:
                return await update.message.reply_text("⛔ فقط مدیران یا سودو می‌تونن ریپلی مود رو روشن یا خاموش کنن!")
        except Exception as e:
            return await update.message.reply_text(f"⚠️ خطا در بررسی دسترسی: {e}")

    # تغییر وضعیت مخصوص همین گروه
    current = reply_status.get(chat_id_str, False)
    reply_status[chat_id_str] = not current
    save_reply_status(reply_status)

    if reply_status[chat_id_str]:
        await update.message.reply_text("💬 ریپلی مود برای این گروه *فعال* شد ✅", parse_mode="Markdown")
    else:
        await update.message.reply_text("🗨️ ریپلی مود برای این گروه *غیرفعال* شد ❌", parse_mode="Markdown")
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
import os

# ======================= ✳️ پنل شروع مخصوص خنگول =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پنل ساده و حرفه‌ای — افزودن به گروه یا پشتیبانی مستقیم"""

    # 🔹 مسیر عکس لوگو
    photo_path = "logo.jpg"
    photo_link = "https://i.ibb.co/QmW8thT/robot-logo.jpg"

    # 🔹 دکمه‌ها
    keyboard = [
        [
            InlineKeyboardButton(
                "➕ افزودن به گروه",
                url="https://t.me/Khenqol_bot?startgroup=true"  # لینک مستقیم ربات خودت
            )
        ],
        [
            InlineKeyboardButton(
                "💬 پشتیبانی (ارتباط با مدیر)",
                url="https://t.me/NOORI_NOOR"  # لینک مستقیم پیوی خودت
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # 🔹 متن پنل
    text = (
        "🤖 به *خنگول فارسی* خوش اومدی!\n\n"
        "من یه ربات هوش مصنوعی هستم که می‌تونم حرف بزنم، یاد بگیرم و فال یا جوک بگم 😄\n\n"
        "برای شروع، منو به گروهت اضافه کن یا مستقیم با پشتیبانی در تماس باش 👇"
    )

    # 🔹 ارسال پنل
    try:
        if os.path.exists(photo_path):
            await update.message.reply_photo(
                photo=InputFile(photo_path),
                caption=text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_photo(
                photo=photo_link,
                caption=text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
    except Exception:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

async def notify_admin_on_startup(app):
    """ارسال پیام فعال‌سازی به ادمین هنگام استارت"""
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

# ======================= 📘 راهنمای عمومی و مخصوص سودو =======================
HELP_FILE = "custom_help.txt"

# 🧩 راهنمای مخصوص سودو (/help)
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """راهنمای مخصوص مدیر اصلی (ADMIN_ID)"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی اجازه دسترسی به /help رو داره!")

    text = (
        "🧠 دستورات مخصوص مدیر اصلی:\n\n"
        "/toggle - روشن/خاموش کردن ربات\n"
        "/welcome - فعال/غیرفعال کردن خوشامد گروه\n"
        "/reply - تغییر حالت ریپلی مود گروه\n"
        "/lock /unlock - قفل یا باز کردن یادگیری\n"
        "/backup /restore - بک‌آپ یا بازیابی داده‌ها\n"
        "/reset - پاک کردن کامل حافظه\n"
        "/reload - بارگذاری مجدد حافظه\n"
        "/broadcast [متن] - ارسال پیام همگانی\n"
        "/cloudsync - بک‌آپ ابری برای مدیر\n"
        "/leave - خروج از گروه\n\n"
        "⚙️ نسخه Cloud+ Supreme Pro Stable+"
    )

    await update.message.reply_text(text)


# 📘 راهنمای قابل ویرایش (برای همه کاربران)
async def show_custom_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش متن راهنما از فایل custom_help.txt"""
    if not os.path.exists(HELP_FILE):
        return await update.message.reply_text(
            "ℹ️ هنوز هیچ متنی برای راهنما ثبت نشده.\n"
            "مدیر اصلی می‌تونه با ریپلای و نوشتن «ثبت راهنما» تنظیمش کنه."
        )
    async with aiofiles.open(HELP_FILE, "r", encoding="utf-8") as f:
        text = await f.read()
    await update.message.reply_text(text)


# ✏️ ذخیره راهنما با ریپلای (فقط برای ADMIN_ID)
async def save_custom_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ذخیره یا ویرایش راهنمای عمومی"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه راهنما رو تنظیم کنه!")

    if not update.message.reply_to_message or not update.message.reply_to_message.text:
        return await update.message.reply_text("❗ باید روی یک پیام متنی ریپلای کنی تا به عنوان راهنما ذخیره بشه!")

    text = update.message.reply_to_message.text
    async with aiofiles.open(HELP_FILE, "w", encoding="utf-8") as f:
        await f.write(text)

    await update.message.reply_text("✅ متن راهنما با موفقیت ذخیره شد!")
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
        # ======================= 👋 مدیریت خوشامد جدا برای هر گروه =======================
WELCOME_FILE = "welcome_status.json"

def load_welcome_status():
    """خواندن وضعیت خوشامد برای هر گروه از فایل"""
    import json, os
    if os.path.exists(WELCOME_FILE):
        try:
            with open(WELCOME_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_welcome_status(data):
    """ذخیره وضعیت خوشامد گروه‌ها در فایل"""
    import json
    with open(WELCOME_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

welcome_status = load_welcome_status()

# ======================= ⚙️ کنترل وضعیت =======================
async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """روشن/خاموش کردن ربات — فقط برای سودو"""
    user = update.effective_user

    # فقط سودو اجازه داره
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه ربات رو روشن یا خاموش کنه!")

    # تغییر وضعیت
    status["active"] = not status["active"]
    await update.message.reply_text("✅ ربات فعال شد!" if status["active"] else "😴 ربات خاموش شد!")
async def toggle_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """روشن/خاموش کردن خوشامد برای هر گروه به‌صورت جداگانه (فقط مدیران و سودو)"""

    user = update.effective_user
    chat = update.effective_chat
    chat_id = str(chat.id)

    # 🧩 فقط مدیران یا سودو
    if chat.type == "private":
        return await update.message.reply_text("⛔ فقط داخل گروه می‌تونی خوشامد رو تنظیم کنی!")

    if user.id != ADMIN_ID:
        try:
            member = await context.bot.get_chat_member(chat.id, user.id)
            if member.status not in ["administrator", "creator"]:
                return await update.message.reply_text("⛔ فقط مدیران یا سودو می‌تونن خوشامد رو روشن یا خاموش کنن!")
        except Exception as e:
            return await update.message.reply_text(f"⚠️ خطا در بررسی دسترسی: {e}")

    # 🔄 تغییر وضعیت مخصوص همین گروه
    current = welcome_status.get(chat_id, True)
    welcome_status[chat_id] = not current
    save_welcome_status(welcome_status)

    if welcome_status[chat_id]:
        await update.message.reply_text("👋 خوشامد برای این گروه *فعال* شد ✅", parse_mode="Markdown")
    else:
        await update.message.reply_text("🚫 خوشامد برای این گروه *غیرفعال* شد ❌", parse_mode="Markdown")

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
    """نمایش آمار کامل گروه‌ها (سازگار با ساختار جدید و قدیمی group_data.json)"""
    try:
        data = load_data("group_data.json")
        groups = data.get("groups", {})

        if isinstance(groups, list):
            if not groups:
                return await update.message.reply_text("ℹ️ هنوز هیچ گروهی ثبت نشده.")

            text = "📈 آمار کامل گروه‌ها:\n\n"
            for g in groups:
                group_id = g.get("id", "نامشخص")
                title = g.get("title", f"Group_{group_id}")
                members = len(g.get("members", []))
                last_active = g.get("last_active", "نامشخص")

                try:
                    chat = await context.bot.get_chat(group_id)
                    if chat.title:
                        title = chat.title
                except Exception:
                    pass

                text += (
                    f"🏠 گروه: {title}\n"
                    f"👥 اعضا: {members}\n"
                    f"🕓 آخرین فعالیت: {last_active}\n\n"
                )

        elif isinstance(groups, dict):
            if not groups:
                return await update.message.reply_text("ℹ️ هنوز هیچ گروهی ثبت نشده.")

            text = "📈 آمار کامل گروه‌ها:\n\n"
            for group_id, info in groups.items():
                title = info.get("title", f"Group_{group_id}")
                members = len(info.get("members", []))
                last_active = info.get("last_active", "نامشخص")

                try:
                    chat = await context.bot.get_chat(group_id)
                    if chat.title:
                        title = chat.title
                except Exception:
                    pass

                text += (
                    f"🏠 گروه: {title}\n"
                    f"👥 اعضا: {members}\n"
                    f"🕓 آخرین فعالیت: {last_active}\n\n"
                )

        else:
            return await update.message.reply_text("⚠️ ساختار فایل group_data.json نامعتبر است!")

        if len(text) > 4000:
            text = text[:3990] + "..."

        await update.message.reply_text(text)

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در آمار گروه‌ها:\n{e}")

# ======================= 👋 خوشامد با عکس پروفایل =======================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پیام خوشامد با تشخیص سازنده (سودو) و عکس پروفایل"""
    import json, os

    for member in update.message.new_chat_members:
        # 👑 تشخیص ورود سازنده (سودو)
        if member.id == ADMIN_ID:
            record_file = "creator_entries.json"
            try:
                # بررسی و ذخیره‌ی تاریخ ورود
                if os.path.exists(record_file):
                    with open(record_file, "r", encoding="utf-8") as f:
                        record = json.load(f)
                else:
                    record = {}

                group_id = str(update.effective_chat.id)
                now = datetime.now().strftime("%Y-%m-%d %H:%M")

                # اگر قبلاً وارد شده بود → پیام بازگشت
                if group_id in record:
                    msg = (
                        "⚡ سیستم مرکزی به‌روزرسانی شد.\n"
                        "👑 سازنده‌ی اصلی به گروه بازگشت!\n\n"
                        f"🕓 زمان ورود مجدد: {now}"
                    )
                else:
                    msg = (
                        "🕶️ حضور چهره‌ی اصلی سیستم شناسایی شد...\n"
                        "⚡ قدرت مرکزی ربات فعال گردید.\n\n"
                        "👑 خوش آمدی *سازنده اصلی خنگول*.\n"
                        "تمام ماژول‌ها در حالت احترام کامل قرار گرفتند 💠\n\n"
                        f"🕓 زمان ورود اول: {now}"
                    )
                    record[group_id] = now

                with open(record_file, "w", encoding="utf-8") as f:
                    json.dump(record, f, ensure_ascii=False, indent=2)

                await update.message.reply_text(msg, parse_mode="Markdown")
                return  # فقط پیام مخصوص سازنده ارسال شود

            except Exception as e:
                await update.message.reply_text(f"⚠️ خطا در خوشامد سازنده: {e}")
                return

    # 🚫 اگر خوشامد خاموش است، برای بقیه کاری نکن
    if not status["welcome"]:
        return

    # 👋 خوشامد برای سایر اعضا
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
        except Exception:
            await update.message.reply_text(text)
# ======================= 👤 ثبت خودکار کاربران =======================
def register_user(user_id):
    """ثبت کاربر در فایل memory.json"""
    data = load_data("memory.json")
    users = data.get("users", [])
    if user_id not in users:
        users.append(user_id)
    data["users"] = users
    save_data("memory.json", data)

# ======================= ☁️ بک‌آپ خودکار و دستی (نسخه امن) =======================
import shutil

async def auto_backup(bot):
    """بک‌آپ خودکار هر ۱۲ ساعت"""
    while True:
        await asyncio.sleep(43200)
        await cloudsync_internal(bot, "Auto Backup")

def _should_include_in_backup(path: str) -> bool:
    """فقط فایل‌های داده‌ای مهم داخل بک‌آپ بروند"""
    lowered = path.lower()
    # پوشه‌ها و فایل‌هایی که باید نادیده بگیریم
    skip_dirs = ["__pycache__", ".git", "venv", "restore_temp"]
    if any(sd in lowered for sd in skip_dirs):
        return False
    # خودِ فایل‌های zip و بک‌آپ‌های قبلی نه!
    if lowered.endswith(".zip") or os.path.basename(lowered).startswith("backup_"):
        return False
    # فقط پسوندهای داده‌ای
    return lowered.endswith((".json", ".jpg", ".png", ".webp", ".mp3", ".ogg"))

async def cloudsync_internal(bot, reason="Manual Backup"):
    """ایجاد و ارسال فایل بک‌آپ به ادمین (Cloud Safe)"""
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"backup_{now}.zip"

    try:
        with zipfile.ZipFile(filename, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk("."):
                for file in files:
                    full_path = os.path.join(root, file)
                    if _should_include_in_backup(full_path):
                        # مسیر داخل آرشیو رو نسبی بنویس تا بازگردانی ساده باشد
                        arcname = os.path.relpath(full_path, ".")
                        zipf.write(full_path, arcname=arcname)

        # ارسال بک‌آپ
        with open(filename, "rb") as f:
            await bot.send_document(chat_id=ADMIN_ID, document=f, filename=filename)
        await bot.send_message(chat_id=ADMIN_ID, text=f"☁️ {reason} انجام شد ✅")

    except Exception as e:
        print(f"[CLOUD BACKUP ERROR] {e}")
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=f"⚠️ خطا در Cloud Backup:\n{e}")
        except:
            pass
    finally:
        if os.path.exists(filename):
            os.remove(filename)

async def cloudsync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اجرای دستی بک‌آپ ابری"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    await cloudsync_internal(context.bot, "Manual Cloud Backup")

# ======================= 💾 بک‌آپ و بازیابی ZIP در چت (نسخه امن) =======================

async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بک‌آپ محلی و ارسال داخل همین چت"""
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"backup_{now}.zip"

    try:
        with zipfile.ZipFile(filename, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk("."):
                for file in files:
                    full_path = os.path.join(root, file)
                    if _should_include_in_backup(full_path):
                        arcname = os.path.relpath(full_path, ".")
                        zipf.write(full_path, arcname=arcname)

        with open(filename, "rb") as f:
            await update.message.reply_document(document=f, filename=filename)
        await update.message.reply_text("✅ بک‌آپ کامل گرفته شد!")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در گرفتن بک‌آپ:\n{e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت فایل ZIP برای بازیابی"""
    await update.message.reply_text("📂 فایل ZIP بک‌آپ را ارسال کن تا بازیابی شود.")
    context.user_data["await_restore"] = True

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش فایل ZIP و بازیابی ایمن با پوشه موقتی"""
    if not context.user_data.get("await_restore"):
        return

    # فقط فایل zip را قبول کن
    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith(".zip"):
        return await update.message.reply_text("❗ لطفاً یک فایل ZIP معتبر بفرست.")

    restore_zip = "restore.zip"
    restore_dir = "restore_temp"

    try:
        tg_file = await doc.get_file()
        await tg_file.download_to_drive(restore_zip)

        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        os.makedirs(restore_dir, exist_ok=True)

        with zipfile.ZipFile(restore_zip, "r") as zip_ref:
            zip_ref.extractall(restore_dir)

        # فقط فایل‌های داده‌ای کلیدی را جابه‌جا کن
        important_files = ["memory.json", "group_data.json", "jokes.json", "fortunes.json"]
        moved_any = False
        for fname in important_files:
            src = os.path.join(restore_dir, fname)
            if os.path.exists(src):
                shutil.move(src, fname)
                moved_any = True

        # بعد از ریستور، ساختار را بازسازی کن
        init_files()

        if moved_any:
            await update.message.reply_text("✅ بازیابی کامل انجام شد!")
        else:
            await update.message.reply_text("ℹ️ فایلی برای جایگزینی پیدا نشد. مطمئنی ZIP درست را دادی؟")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بازیابی:\n{e}")
    finally:
        if os.path.exists(restore_zip):
            os.remove(restore_zip)
        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        context.user_data["await_restore"] = False

# ======================= 💬 پاسخ و هوش مصنوعی =======================
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاسخ‌دهی اصلی هوش مصنوعی و سیستم یادگیری"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    uid = update.effective_user.id
    chat_id = update.effective_chat.id

    # 🧠 بررسی حالت ریپلی مود مخصوص هر گروه
    chat_key = str(chat_id)
    if reply_status.get(chat_key, False):
        # اگه کسی گفت "خنگول کجایی؟"
        if text.lower() in ["خنگول کجایی", "خنگول کجایی؟", "کجایی خنگول"]:
            return await update.message.reply_text("😄 من اینجام! برای صحبت فقط روی پیام‌هام ریپلای کن 💬")

        # فقط به پیام‌هایی جواب بده که ریپلای خودش هستن
        if not update.message.reply_to_message or update.message.reply_to_message.from_user.id != context.bot.id:
            return

    # ثبت کاربر و گروه
    register_user(uid)
    register_group_activity(chat_id, uid)

    if not status["locked"]:
        auto_learn_from_text(text)

    if not status["active"]:
        shadow_learn(text, "")
        return

    # ✅ درصد هوش منطقی
    if text.lower() == "درصد هوش":
        score = 0
        details = []

        if os.path.exists("memory.json"):
            data = load_data("memory.json")
            phrases = len(data.get("phrases", {}))
            responses = sum(len(v) for v in data.get("phrases", {}).values()) if phrases else 0
            if phrases > 15 and responses > 25:
                score += 30
                details.append("🧠 حافظه فعال و گسترده ✅")
            elif phrases > 5:
                score += 20
                details.append("🧩 حافظه محدود ولی کارا 🟢")
            else:
                score += 10
                details.append("⚪ حافظه هنوز در حال یادگیری است")

        if os.path.exists("jokes.json"):
            data = load_data("jokes.json")
            count = len(data)
            if count > 10:
                score += 15
                details.append("😂 جوک‌های زیاد و متنوع 😎")
            elif count > 0:
                score += 10
                details.append("😅 چند جوک فعال وجود دارد")
            else:
                details.append("⚪ هنوز جوکی ثبت نشده")

        if os.path.exists("fortunes.json"):
            data = load_data("fortunes.json")
            count = len(data)
            if count > 10:
                score += 15
                details.append("🔮 فال‌ها متنوع و فعال 💫")
            elif count > 0:
                score += 10
                details.append("🔮 چند فال ثبت شده")
            else:
                details.append("⚪ هنوز فالی ثبت نشده")

        try:
            test = smart_response("سلام", "شاد")
            if test:
                score += 25
                details.append("💬 پاسخ هوشمند فعاله 🤖")
            else:
                score += 10
                details.append("⚪ پاسخ هوشمند غیرفعاله")
        except:
            details.append("⚠️ خطا در smart_response")

        essential_files = ["memory.json", "group_data.json", "jokes.json", "fortunes.json"]
        stable_count = sum(os.path.exists(f) for f in essential_files)
        if stable_count == len(essential_files):
            score += 15
            details.append("💾 حافظه و داده‌ها پایدار ✅")
        elif stable_count >= 2:
            score += 10
            details.append("⚠️ برخی فایل‌ها ناقصند")
        else:
            details.append("🚫 خطا در حافظه داده")

        if score > 100:
            score = 100

        result = (
            f"🤖 درصد هوش فعلی خنگول: *{score}%*\n\n" +
            "\n".join(details) +
            f"\n\n📈 نسخه Cloud+ Supreme Pro Stable+\n🕓 {datetime.now().strftime('%Y/%m/%d %H:%M')}"
        )

        await update.message.reply_text(result, parse_mode="Markdown")
        return

    # ✅ درصد هوش اجتماعی
    if text.lower() == "درصد هوش اجتماعی":
        score = 0
        details = []

        memory = load_data("memory.json")
        users = len(memory.get("users", []))
        if users > 100:
            score += 25
            details.append(f"👤 کاربران زیاد ({users} نفر)")
        elif users > 30:
            score += 20
            details.append(f"👥 کاربران فعال ({users} نفر)")
        elif users > 10:
            score += 10
            details.append(f"🟢 کاربران محدود ({users})")
        else:
            details.append("⚪ کاربران کم")

        groups_data = load_data("group_data.json").get("groups", {})
        group_count = len(groups_data) if isinstance(groups_data, dict) else len(groups_data)
        if group_count > 15:
            score += 25
            details.append(f"🏠 گروه‌های فعال زیاد ({group_count}) ✅")
        elif group_count > 5:
            score += 15
            details.append(f"🏠 گروه‌های متوسط ({group_count})")
        elif group_count > 0:
            score += 10
            details.append(f"🏠 گروه‌های محدود ({group_count})")
        else:
            details.append("🚫 هنوز در هیچ گروهی عضو نیست")

        try:
            activity = get_group_stats()
            active_chats = activity.get("active_chats", 0)
            total_msgs = activity.get("messages", 0)
            if active_chats > 10 and total_msgs > 200:
                score += 25
                details.append("💬 تعاملات زیاد و مداوم 😎")
            elif total_msgs > 50:
                score += 15
                details.append("💬 تعاملات متوسط")
            elif total_msgs > 0:
                score += 10
                details.append("💬 تعامل کم ولی فعال")
            else:
                details.append("⚪ تعامل خاصی ثبت نشده")
        except:
            details.append("⚠️ آمار تعاملات در دسترس نیست")

        if os.path.exists("memory.json"):
            phrases = len(memory.get("phrases", {}))
            if phrases > 50:
                score += 20
                details.append("🧠 حافظه گفتاری قوی")
            elif phrases > 10:
                score += 10
                details.append("🧠 حافظه محدود")
            else:
                details.append("⚪ حافظه در حال رشد")

        if score > 100:
            score = 100

        result = (
            f"🤖 درصد هوش اجتماعی خنگول: *{score}%*\n\n"
            + "\n".join(details)
            + f"\n\n📊 شاخص تعامل اجتماعی فعال 💬\n🕓 {datetime.now().strftime('%Y/%m/%d %H:%M')}"
        )

        await update.message.reply_text(result, parse_mode="Markdown")
        return# ✅ هوش کلی (ترکیب هوش منطقی + اجتماعی)
    if text.lower() == "هوش کلی":
        score = 0
        details = []

        # 🧠 حافظه و یادگیری
        if os.path.exists("memory.json"):
            data = load_data("memory.json")
            phrases = len(data.get("phrases", {}))
            responses = sum(len(v) for v in data.get("phrases", {}).values()) if phrases else 0
            if phrases > 20 and responses > 30:
                score += 25
                details.append("🧠 یادگیری گسترده و دقیق ✅")
            elif phrases > 10:
                score += 15
                details.append("🧩 یادگیری متوسط ولی فعال")
            else:
                score += 5
                details.append("⚪ حافظه در حال رشد")

        # 😂 شوخ‌طبعی و جوک‌ها
        if os.path.exists("jokes.json"):
            data = load_data("jokes.json")
            count = len(data)
            if count > 10:
                score += 10
                details.append("😂 شوخ‌طبع و بامزه 😄")
            elif count > 0:
                score += 5
                details.append("😅 کمی شوخ‌طبع")
            else:
                details.append("⚪ هنوز شوخی بلد نیست 😶")

        # 💬 پاسخ‌دهی هوشمند
        try:
            test = smart_response("سلام", "شاد")
            if test:
                score += 20
                details.append("💬 پاسخ هوشمند فعال 🤖")
            else:
                score += 10
                details.append("⚪ پاسخ ساده")
        except:
            details.append("⚠️ خطا در پاسخ‌دهی هوش مصنوعی")

        # 👥 کاربران و گروه‌ها
        memory = load_data("memory.json")
        users = len(memory.get("users", []))
        groups_data = load_data("group_data.json").get("groups", {})
        group_count = len(groups_data) if isinstance(groups_data, dict) else len(groups_data)

        if users > 50:
            score += 10
            details.append(f"👤 کاربران زیاد ({users})")
        elif users > 10:
            score += 5
            details.append(f"👥 کاربران محدود ({users})")

        if group_count > 10:
            score += 10
            details.append(f"🏠 گروه‌های زیاد ({group_count}) ✅")
        elif group_count > 0:
            score += 5
            details.append(f"🏠 گروه‌های محدود ({group_count})")

        # 💾 پایداری سیستم
        essential_files = ["memory.json", "group_data.json", "jokes.json", "fortunes.json"]
        stability = sum(os.path.exists(f) for f in essential_files)
        if stability == len(essential_files):
            score += 10
            details.append("💾 سیستم پایدار و سالم ✅")
        elif stability >= 2:
            score += 5
            details.append("⚠️ بخشی از سیستم ناقصه")
        else:
            details.append("🚫 حافظه آسیب‌دیده")

        # ✨ محاسبه IQ
        iq = min(160, int((score / 100) * 160))

        # تعیین سطح هوش
        if iq >= 130:
            level = "🌟 نابغه دیجیتال"
        elif iq >= 110:
            level = "🧠 باهوش و تحلیل‌گر"
        elif iq >= 90:
            level = "🙂 نرمال ولی یادگیرنده"
        else:
            level = "🤪 خنگول کلاسیک 😅"

        result = (
            f"🤖 IQ کلی خنگول: *{iq}*\n"
            f"{level}\n\n"
            + "\n".join(details)
            + f"\n\n📈 نسخه Cloud+ Supreme Pro Stable+\n🕓 {datetime.now().strftime('%Y/%m/%d %H:%M')}"
        )

        await update.message.reply_text(result, parse_mode="Markdown")
        return

    # ✅ جوک تصادفی
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
                        await update.message.reply_photo(photo=v, caption="😂 جوک تصویری!")
                    elif t == "video":
                        await update.message.reply_video(video=v, caption="😂 جوک ویدیویی!")
                    elif t == "sticker":
                        await update.message.reply_sticker(sticker=v)
                    else:
                        await update.message.reply_text("⚠️ نوع فایل پشتیبانی نمی‌شود.")
                except Exception as e:
                    await update.message.reply_text(f"⚠️ خطا در ارسال جوک: {e}")
            else:
                await update.message.reply_text("هنوز جوکی ثبت نشده 😅")
        else:
            await update.message.reply_text("📂 فایل جوک‌ها پیدا نشد 😕")
        return

    # ✅ فال تصادفی
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
                        await update.message.reply_photo(photo=v, caption="🔮 فال تصویری!")
                    elif t == "video":
                        await update.message.reply_video(video=v, caption="🔮 فال ویدیویی!")
                    elif t == "sticker":
                        await update.message.reply_sticker(sticker=v)
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

    # ✅ یادگیری دستی
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

    # ✅ پاسخ هوشمند و احساسی
    learned_reply = get_reply(text)
    emotion = detect_emotion(text)

    # ذخیره و واکنش احساسی
    last_emotion = get_last_emotion(uid)
    context_reply = emotion_context_reply(emotion, last_emotion)
    remember_emotion(uid, emotion)

    if context_reply:
        reply_text = enhance_sentence(context_reply)
    elif learned_reply:
        reply_text = enhance_sentence(learned_reply)
    else:
        reply_text = smart_response(text, uid) or enhance_sentence(text)

    await update.message.reply_text(reply_text)

# ======================= 🧾 راهنمای قابل ویرایش =======================
HELP_FILE = "custom_help.txt"

async def show_custom_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش متن راهنما برای همه کاربران"""
    if not os.path.exists(HELP_FILE):
        return await update.message.reply_text(
            "ℹ️ هنوز هیچ متنی برای راهنما ثبت نشده.\n"
            "مدیر اصلی می‌تونه با ریپلای و نوشتن «ثبت راهنما» تنظیمش کنه."
        )
    async with aiofiles.open(HELP_FILE, "r", encoding="utf-8") as f:
        text = await f.read()
    await update.message.reply_text(text)

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
    groups_data = load_data("group_data.json").get("groups", {})
    group_ids = []

    if isinstance(groups_data, dict):
        group_ids = list(groups_data.keys())
    elif isinstance(groups_data, list):
        group_ids = [g.get("id") for g in groups_data if "id" in g]

    sent, failed = 0, 0
    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=msg)
            sent += 1
        except:
            failed += 1
    for gid in group_ids:
        try:
            await context.bot.send_message(chat_id=int(gid), text=msg)
            sent += 1
        except:
            failed += 1

    await update.message.reply_text(
        f"📨 ارسال همگانی انجام شد ✅\n"
        f"👤 کاربران: {len(users)} | 👥 گروه‌ها: {len(group_ids)}\n"
        f"✅ موفق: {sent} | ⚠️ ناموفق: {failed}"
    )

# ======================= 🚪 خروج از گروه =======================
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("🫡 خدافظ! تا دیدار بعدی 😂")
        await context.bot.leave_chat(update.message.chat.id)

if __name__ == "__main__":
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
    app.add_handler(CommandHandler("replymode", toggle_reply_mode))

    # ======================= 🧠 Reply Panel Pro++ =======================
    app.add_handler(CommandHandler("reply", add_reply_command))
    app.add_handler(MessageHandler(filters.ALL, message_collector))
    app.add_handler(CallbackQueryHandler(button_handler))

    # ======================= 📘 راهنمای قابل ویرایش =======================
    app.add_handler(MessageHandler(filters.Regex("^ثبت راهنما$"), save_custom_help))
    app.add_handler(MessageHandler(filters.Regex("^راهنما$"), show_custom_help))

    # ======================= 🗂 اسناد و عضویت جدید =======================
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))

    # ======================= ⚙️ مغز یادگیری و پاسخ =======================
    # ⚙️ ابتدا پاسخ‌های گفت‌وگو و یادگیری
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    # ⚙️ سپس پاسخ خودکار هوشمند (پایان زنجیره)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))

    # ======================= 🚀 هنگام استارت =======================
    async def on_startup(app):
        await notify_admin_on_startup(app)
        app.create_task(auto_backup(app.bot))
        app.create_task(start_auto_brain_loop(app.bot))  # 🧠 مغز خودکار
        print("🌙 [SYSTEM] Startup tasks scheduled ✅")

    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)
