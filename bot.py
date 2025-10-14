import asyncio
import os
import random
import zipfile
import shutil
from datetime import datetime
import aiofiles

from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# 📦 ماژول‌های اختصاصی
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

# مقداردهی اولیه فایل‌های حافظه
init_files()

# وضعیت کلی ربات
status = {
    "active": True,
    "learning": True,
    "welcome": True,
    "locked": False
}# ======================= 🔁 حالت ریپلای =======================
reply_mode = {"enabled": False}
REPLY_MODE_FILE = "reply_mode.json"


def load_reply_mode():
    """لود کردن وضعیت ریپلای از فایل"""
    if os.path.exists(REPLY_MODE_FILE):
        try:
            data = load_data(REPLY_MODE_FILE)
            reply_mode["enabled"] = data.get("enabled", False)
        except Exception:
            reply_mode["enabled"] = False
    else:
        reply_mode["enabled"] = False


def save_reply_mode():
    """ذخیره وضعیت ریپلای در فایل"""
    save_data(REPLY_MODE_FILE, {"enabled": reply_mode["enabled"]})


async def toggle_reply_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """روشن یا خاموش کردن حالت ریپلای"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    reply_mode["enabled"] = not reply_mode["enabled"]
    save_reply_mode()

    if reply_mode["enabled"]:
        await update.message.reply_text(
            "💬 حالت ریپلای *روشن* شد ✅", parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "🤫 حالت ریپلای *خاموش* شد ❌", parse_mode="Markdown"
        )


# در شروع برنامه وضعیت ریپلای از فایل خونده بشه
load_reply_mode()# ======================= ✳️ شروع و پیام فعال‌سازی با پنل شیشه‌ای =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش پیام خوش‌آمدگویی با دکمه‌های شیشه‌ای در چت خصوصی"""
    if update.message.chat.type != "private":
        await update.message.reply_text("سلام 😄 برای استفاده از من بیا پی‌وی ❤️")
        return

    keyboard = [
        [
            InlineKeyboardButton("🤖 معرفی ربات", callback_data="info"),
            InlineKeyboardButton("➕ افزودن به گروه", callback_data="add"),
        ],
        [
            InlineKeyboardButton("🧠 یادم بده", callback_data="learn"),
            InlineKeyboardButton("🛠 پشتیبانی", callback_data="support"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "🤖 *خنگول فارسی 8.5.1 Cloud+ Supreme Pro Stable+*\n"
        "✨ سلام! من یه ربات هوشمند، شوخ و یادگیرنده‌ام 😄\n"
        "یکی از گزینه‌های زیر رو انتخاب کن 👇"
    )

    await update.message.reply_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )


async def panel_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت دکمه‌های شیشه‌ای پنل شروع"""
    query = update.callback_query
    await query.answer()

    if query.data == "info":
        await query.message.reply_text("من یه ربات هوشمندم که ازت یاد می‌گیرم 😄")

    elif query.data == "add":
        me = await context.bot.get_me()
        await query.message.reply_text(
            f"برای افزودن به گروه: https://t.me/{me.username}?startgroup=true"
        )

    elif query.data == "learn":
        await query.message.reply_text(
            "برای آموزش جمله جدید بنویس:\n"
            "یادبگیر سلام\n"
            "سلام خوبی؟"
        )

    elif query.data == "support":
        await query.message.reply_text(
            "🛠 برای پشتیبانی با ادمین تماس بگیر یا اینجا پیام بفرست."
        )# ======================= ⚙️ خطایاب خودکار =======================
async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    """ارسال خطاهای رخ‌داده برای ادمین و چاپ در کنسول"""
    error_text = f"⚠️ خطا در ربات:\n\n{context.error}"
    print(error_text)

    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=error_text)
    except Exception:
        # اگر نتواند به ادمین پیام دهد، فقط خطا را در لاگ چاپ می‌کند
        pass


# ======================= 📘 راهنمای قابل ویرایش =======================
HELP_FILE = "custom_help.txt"


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /help یا 'راهنما' برای نمایش متن راهنما از فایل"""
    if not os.path.exists(HELP_FILE):
        return await update.message.reply_text(
            "ℹ️ هنوز هیچ متنی برای راهنما ثبت نشده.\n"
            "مدیر اصلی می‌تونه با ریپلای و نوشتن «ثبت راهنما» تنظیمش کنه."
        )

    async with aiofiles.open(HELP_FILE, "r", encoding="utf-8") as f:
        text = await f.read()

    await update.message.reply_text(text)


async def save_custom_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ذخیره یا بروزرسانی متن راهنما با ریپلای (فقط توسط مدیر اصلی)"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه راهنما رو تنظیم کنه!")

    if not update.message.reply_to_message or not update.message.reply_to_message.text:
        return await update.message.reply_text("❗ برای ثبت راهنما باید روی یک پیام متنی ریپلای کنی!")

    text = update.message.reply_to_message.text

    async with aiofiles.open(HELP_FILE, "w", encoding="utf-8") as f:
        await f.write(text)

    await update.message.reply_text("✅ متن راهنما با موفقیت ذخیره شد!")# ======================= 🎭 تغییر مود =======================
async def mode_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تغییر مود ربات (شوخ، بی‌ادب، غمگین، نرمال)"""
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
    """روشن یا خاموش کردن عملکرد کلی ربات"""
    status["active"] = not status["active"]
    await update.message.reply_text("✅ فعال شد!" if status["active"] else "😴 خاموش شد!")


async def toggle_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فعال یا غیرفعال کردن خوشامدگویی"""
    status["welcome"] = not status["welcome"]
    await update.message.reply_text("👋 خوشامد فعال شد!" if status["welcome"] else "🚫 خوشامد غیرفعال شد!")


async def lock_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قفل کردن یادگیری"""
    status["locked"] = True
    await update.message.reply_text("🔒 یادگیری قفل شد!")


async def unlock_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """باز کردن قفل یادگیری"""
    status["locked"] = False
    await update.message.reply_text("🔓 یادگیری باز شد!")


# ======================= 📊 آمار خلاصه =======================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار کلی ربات"""
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

        # 🔹 حالت لیستی
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

        # 🔹 حالت دیکشنری
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

        # محدودیت طول پیام
        if len(text) > 4000:
            text = text[:3990] + "..."

        await update.message.reply_text(text)

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در آمار گروه‌ها:\n{e}")# ======================= 👋 خوشامد با عکس پروفایل =======================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پیام خوشامدگویی به اعضای جدید همراه با عکس پروفایل"""
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
        except Exception:
            await update.message.reply_text(text)


# ======================= 👤 ثبت خودکار کاربران =======================
def register_user(user_id: int):
    """ثبت خودکار کاربران جدید در فایل memory.json"""
    data = load_data("memory.json")
    users = data.get("users", [])
    if user_id not in users:
        users.append(user_id)
    data["users"] = users
    save_data("memory.json", data)


# ======================= ☁️ بک‌آپ خودکار و دستی (نسخه امن) =======================
async def auto_backup(bot):
    """بک‌آپ خودکار هر ۱۲ ساعت"""
    while True:
        await asyncio.sleep(43200)
        await cloudsync_internal(bot, "Auto Backup")


def _should_include_in_backup(path: str) -> bool:
    """بررسی اینکه چه فایل‌هایی در بک‌آپ گنجانده شوند"""
    lowered = path.lower()
    skip_dirs = ["__pycache__", ".git", "venv", "restore_temp"]
    if any(sd in lowered for sd in skip_dirs):
        return False
    if lowered.endswith(".zip") or os.path.basename(lowered).startswith("backup_"):
        return False
    return lowered.endswith((".json", ".jpg", ".png", ".webp", ".mp3", ".ogg"))


async def cloudsync_internal(bot, reason="Manual Backup"):
    """ایجاد و ارسال بک‌آپ فشرده برای ادمین (Cloud Safe)"""
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
            await bot.send_document(chat_id=ADMIN_ID, document=f, filename=filename)
        await bot.send_message(chat_id=ADMIN_ID, text=f"☁️ {reason} انجام شد ✅")

    except Exception as e:
        print(f"[CLOUD BACKUP ERROR] {e}")
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=f"⚠️ خطا در Cloud Backup:\n{e}")
        except Exception:
            pass
    finally:
        if os.path.exists(filename):
            os.remove(filename)


async def cloudsync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اجرای دستی بک‌آپ ابری"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    await cloudsync_internal(context.bot, "Manual Cloud Backup")


# ======================= 💾 بک‌آپ و بازیابی ZIP در چت =======================
async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بک‌آپ محلی و ارسال فایل در چت"""
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
    """دریافت فایل ZIP برای بازیابی داده‌ها"""
    await update.message.reply_text("📂 فایل ZIP بک‌آپ را ارسال کن تا بازیابی شود.")
    context.user_data["await_restore"] = True


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش فایل ZIP و بازیابی ایمن با پوشه موقت"""
    if not context.user_data.get("await_restore"):
        return

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

        important_files = ["memory.json", "group_data.json", "jokes.json", "fortunes.json"]
        moved_any = False

        for fname in important_files:
            src = os.path.join(restore_dir, fname)
            if os.path.exists(src):
                shutil.move(src, fname)
                moved_any = True

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
        context.user_data["await_restore"] = False# ======================= 💬 پاسخ و هوش مصنوعی (با پشتیبانی از حالت ریپلای) =======================
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاسخ‌دهی اصلی هوش مصنوعی و سیستم یادگیری با کنترل حالت ریپلای"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    is_private = update.message.chat.type == "private"

    # ثبت کاربر و گروه
    register_user(uid)
    register_group_activity(chat_id, uid)

    # حالت ریپلای فعال باشد → فقط در صورت ریپلای پاسخ بده
    if not is_private and reply_mode["enabled"]:
        if not update.message.reply_to_message:
            return
        else:
            if update.message.reply_to_message.from_user.id != (await context.bot.get_me()).id:
                return

    # یادگیری خودکار
    if not status["locked"]:
        auto_learn_from_text(text)

    # اگر ربات خاموش باشد
    if not status["active"]:
        shadow_learn(text, "")
        return

    # ✅ درصد هوش
    if text.lower() in ["درصد هوش", "درصد هوش اجتماعی", "هوش کلی"]:
        if text.lower() == "درصد هوش":
            await update.message.reply_text("🤖 درصد هوش فعلی خنگول: 70%")
        elif text.lower() == "درصد هوش اجتماعی":
            await update.message.reply_text("💬 درصد هوش اجتماعی خنگول: 85%")
        else:
            await update.message.reply_text("🧠 هوش کلی خنگول: 120 | سطح: یادگیرنده فعال 😄")
        return

    # ✅ جوک تصادفی
    if text.lower() == "جوک":
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
                except Exception as e:
                    await update.message.reply_text(f"⚠️ خطا در ارسال جوک: {e}")
            else:
                await update.message.reply_text("هیچ جوکی ثبت نشده 😅")
        return

    # ✅ فال تصادفی
    if text.lower() == "فال":
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
                except Exception as e:
                    await update.message.reply_text(f"⚠️ خطا در فال: {e}")
            else:
                await update.message.reply_text("فالی ثبت نشده 😔")
        return

    # ✅ ثبت جوک و فال با ریپلای
    if text.lower() == "ثبت جوک" and update.message.reply_to_message:
        await save_joke(update)
        return
    if text.lower() == "ثبت فال" and update.message.reply_to_message:
        await save_fortune(update)
        return

    # ✅ لیست‌ها
    if text.lower() == "لیست جوک‌ها":
        await list_jokes(update)
        return
    if text.lower() == "لیست فال‌ها":
        await list_fortunes(update)
        return

    # ✅ لیست جملات یادگرفته
    if text.lower() == "لیست":
        await update.message.reply_text(list_phrases())
        return

    # ✅ یادگیری دستی (یادبگیر)
    if text.startswith("یادبگیر "):
        parts = text.replace("یادبگیر ", "").split("\n")
        if len(parts) > 1:
            phrase = parts[0].strip()
            responses = [p.strip() for p in parts[1:] if p.strip()]
            msg = learn(phrase, *responses)
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("❗ بعد از 'یادبگیر' جمله و پاسخ‌هاش رو در خطوط بعدی بنویس.")
        return

    # ✅ جمله تصادفی
    if text.lower() == "جمله بساز":
        await update.message.reply_text(generate_sentence())
        return

    # ✅ پاسخ هوشمند و احساسی
    learned_reply = get_reply(text)
    emotion = detect_emotion(text)
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


# ======================= 🧹 ریست و ریلود حافظه =======================
async def reset_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاک کردن کامل حافظه (فقط مدیر اصلی)"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه این کار رو انجام بده!")

    for f in ["memory.json", "group_data.json", "stickers.json", "jokes.json", "fortunes.json"]:
        if os.path.exists(f):
            os.remove(f)
    init_files()
    await update.message.reply_text("🧹 تمام داده‌ها با موفقیت پاک شدند و حافظه بازسازی شد!")


async def reload_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بارگذاری مجدد حافظه بدون پاک شدن داده‌ها"""
    init_files()
    await update.message.reply_text("🔄 حافظه با موفقیت دوباره بارگذاری شد!")


# ======================= 📨 ارسال همگانی =======================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پیام همگانی به تمام کاربران و گروه‌ها"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    msg = " ".join(context.args)
    if not msg:
        return await update.message.reply_text("❗ بعد از /broadcast متن پیام را بنویس.")

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
        except Exception:
            failed += 1

    for gid in group_ids:
        try:
            await context.bot.send_message(chat_id=int(gid), text=msg)
            sent += 1
        except Exception:
            failed += 1

    await update.message.reply_text(
        f"📢 ارسال همگانی انجام شد ✅\n"
        f"👤 کاربران: {len(users)} | 👥 گروه‌ها: {len(group_ids)}\n"
        f"✅ موفق: {sent} | ⚠️ ناموفق: {failed}"
    )


# ======================= 🚪 خروج از گروه =======================
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """خروج ربات از گروه فعلی (فقط مدیر اصلی)"""
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("👋 خداحافظ! امیدوارم دوباره منو دعوت کنی 😄")
    await context.bot.leave_chat(update.message.chat.id)


# ======================= 🧭 پنل شیشه‌ای شروع ربات =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش پنل شیشه‌ای معرفی و امکانات"""
    me = await context.bot.get_me()
    keyboard = [
        [
            InlineKeyboardButton("💎 معرفی من", callback_data="about_me"),
            InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/{me.username}?startgroup=true"),
        ],
        [
            InlineKeyboardButton("🧠 یادم بده", callback_data="teach_me"),
            InlineKeyboardButton("💬 پشتیبانی", callback_data="support"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🤖 سلام! من **خنگول فارسی 8.5.1 Cloud+ Supreme Pro Stable+** هستم 😄\n"
        "از دکمه‌های زیر استفاده کن 👇",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


# ======================= 💬 پشتیبانی مستقیم به ادمین =======================
async def support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پیام پشتیبانی به مدیر"""
    text = update.message.text
    if not text.startswith("پشتیبانی "):
        return

    message = text.replace("پشتیبانی ", "").strip()
    if not message:
        return await update.message.reply_text("❗ لطفاً بعد از 'پشتیبانی' متن پیام را بنویس.")

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 پیام پشتیبانی جدید از @{update.effective_user.username or update.effective_user.id}:\n\n{message}",
        )
        await update.message.reply_text("✅ پیام شما برای پشتیبانی ارسال شد.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ارسال پیام: {e}")


# ======================= 🔁 کنترل ریپلای‌مود =======================
async def toggle_reply_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تغییر وضعیت ریپلای‌مود (فقط مدیر اصلی)"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه این کارو انجام بده!")

    reply_mode["enabled"] = not reply_mode["enabled"]
    status_text = "فعال شد ✅" if reply_mode["enabled"] else "غیرفعال شد ❌"
    await update.message.reply_text(f"🔁 حالت ریپلای {status_text}")


# ======================= 🚀 اجرای نهایی ربات =======================
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

    # 🔹 پنل استارت
    app.add_handler(CallbackQueryHandler(panel_buttons))

    # 🔹 راهنمای قابل ویرایش
    app.add_handler(MessageHandler(filters.Regex("^ثبت راهنما$"), save_custom_help))
    app.add_handler(MessageHandler(filters.Regex("^راهنما$"), help_command))

    # 🔹 پیام‌ها و اسناد
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.Regex("^پشتیبانی "), support_message))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    # 🔹 هنگام استارت
    async def on_startup(app):
        app.create_task(auto_backup(app.bot))
        app.create_task(start_auto_brain_loop(app.bot))
        print("🌙 [SYSTEM] Startup tasks scheduled ✅")

    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)
