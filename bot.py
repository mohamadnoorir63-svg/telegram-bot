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
    filters
)
from telegram.ext import CallbackQueryHandler
import aiofiles

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

status = {
    "active": True,
    "learning": True,
    "welcome": True,
    "locked": False
}
# ======================= 💬 ریپلی مود گروهی و محدود به مدیران =======================
REPLY_FILE = "reply_status.json"

def load_reply_status():
    """خواندن وضعیت ریپلی مود برای تمام گروه‌ها"""
    import json, os
    if os.path.exists(REPLY_FILE):
        try:
            with open(REPLY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}  # ساختار داده: { "group_id": {"enabled": True/False} }


def save_reply_status(data):
    """ذخیره وضعیت ریپلی مود برای همه گروه‌ها"""
    import json
    with open(REPLY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


reply_status = load_reply_status()


def is_group_reply_enabled(chat_id):
    """بررسی فعال بودن ریپلی مود در گروه خاص"""
    return reply_status.get(str(chat_id), {}).get("enabled", False)


async def toggle_reply_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تغییر وضعیت ریپلی مود — فقط مدیران گروه یا ادمین اصلی مجازند"""
    chat = update.effective_chat
    user = update.effective_user

    # فقط در گروه قابل استفاده است
    if chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text("⚠️ این دستور فقط داخل گروه کار می‌کند!")

    # بررسی ادمین اصلی یا مدیر گروه بودن
    is_main_admin = (user.id == ADMIN_ID)
    is_group_admin = False

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status in ["creator", "administrator"]:
            is_group_admin = True
    except:
        pass

    if not (is_main_admin or is_group_admin):
        return await update.message.reply_text("⛔ فقط مدیران گروه یا ادمین اصلی می‌توانند این تنظیم را تغییر دهند!")

    # تغییر وضعیت مخصوص همان گروه
    group_id = str(chat.id)
    current = reply_status.get(group_id, {}).get("enabled", False)
    reply_status[group_id] = {"enabled": not current}
    save_reply_status(reply_status)

    if reply_status[group_id]["enabled"]:
        await update.message.reply_text("💬 ریپلی مود در این گروه فعال شد!\nفقط با ریپلای به پیام‌های من چت کنید 😄")
    else:
        await update.message.reply_text("🗨️ ریپلی مود در این گروه غیرفعال شد!\nالان به همه پیام‌ها جواب می‌دهم 😎")


# ======================= 🧠 بررسی حالت ریپلی مود گروهی =======================
async def handle_group_reply_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اگر ریپلی مود فعال باشد، فقط در صورت ریپلای به ربات پاسخ بده"""
    if update.effective_chat.type in ["group", "supergroup"]:
        chat_id = update.effective_chat.id
        if is_group_reply_enabled(chat_id):
            text = update.message.text.strip()

            # واکنش به درخواست حضور
            if text.lower() in ["خنگول کجایی", "خنگول کجایی؟", "کجایی خنگول"]:
                return await update.message.reply_text("😄 من اینجام! فقط روی پیام‌هام ریپلای کن 💬")

            # اگر پیام ریپلای به خود ربات نبود، پاسخی نده
            if not update.message.reply_to_message or update.message.reply_to_message.from_user.id != context.bot.id:
                return True  # یعنی بقیه تابع reply اجرا نشود
    return False
# ======================= 🧾 ثبت کاربر =======================
import json, os

USERS_FILE = "users.json"

async def register_user(user):
    """ذخیره آیدی و نام کاربر در فایل users.json"""
    data = []
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            data = []

    if user.id not in [u["id"] for u in data]:
        data.append({"id": user.id, "name": user.first_name})
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
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

# ======================= 📘 راهنمای قابل ویرایش =======================
HELP_FILE = "custom_help.txt"

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /help و واژه 'راهنما' از فایل custom_help.txt بخونن"""
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
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه راهنما رو تنظیم کنه!")

    if not update.message.reply_to_message or not update.message.reply_to_message.text:
        return await update.message.reply_text("❗ برای ثبت راهنما باید روی یک پیام متنی ریپلای کنی!")

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

 # ======================= 👋 سیستم خوشامد پویا برای هر گروه =======================
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
import datetime, json, os, asyncio

WELCOME_FILE = "welcome_settings.json"

# ✅ بارگذاری و ذخیره‌سازی تنظیمات
def load_welcome_settings():
    if os.path.exists(WELCOME_FILE):
        with open(WELCOME_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_welcome_settings(data):
    with open(WELCOME_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

welcome_settings = load_welcome_settings()

# ✅ پنل تنظیم خوشامد
async def open_welcome_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    member = await context.bot.get_chat_member(chat.id, user.id)

    if member.status not in ["administrator", "creator"] and user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیران یا ادمین اصلی می‌تونن خوشامد رو تنظیم کنن!")

    keyboard = [
        [InlineKeyboardButton("🟢 فعال‌سازی خوشامد", callback_data="welcome_enable")],
        [InlineKeyboardButton("🔴 غیرفعال‌سازی خوشامد", callback_data="welcome_disable")],
        [InlineKeyboardButton("🖼 تنظیم عکس خوشامد", callback_data="welcome_setmedia")],
        [InlineKeyboardButton("📜 تنظیم متن خوشامد", callback_data="welcome_settext")],
        [InlineKeyboardButton("📎 تنظیم لینک قوانین", callback_data="welcome_setrules")],
        [InlineKeyboardButton("⏳ تنظیم حذف خودکار", callback_data="welcome_setdelete")]
    ]
    await update.message.reply_text(
        "👋 تنظیمات خوشامد برای این گروه:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ✅ دکمه‌های پنل
async def welcome_panel_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = str(query.message.chat.id)
    await query.answer()

    if chat_id not in welcome_settings:
        welcome_settings[chat_id] = {
            "enabled": False,
            "text": None,
            "media": None,
            "rules": None,
            "delete_after": 0
        }

    data = query.data
    msg = "❗ گزینه نامعتبر"

    if data == "welcome_enable":
        welcome_settings[chat_id]["enabled"] = True
        msg = "✅ خوشامد برای این گروه فعال شد!"
    elif data == "welcome_disable":
        welcome_settings[chat_id]["enabled"] = False
        msg = "🚫 خوشامد برای این گروه غیرفعال شد!"
    elif data == "welcome_setmedia":
        msg = "🖼 روی عکس یا گیف ریپلای کن و بنویس:\n<b>ثبت عکس خوشامد</b>"
    elif data == "welcome_settext":
        msg = "📜 روی پیام متنی ریپلای کن و بنویس:\n<b>ثبت خوشامد</b>"
    elif data == "welcome_setrules":
        msg = "📎 لینک قوانین گروه را بفرست:\nمثلاً:\nتنظیم قوانین https://t.me/example"
    elif data == "welcome_setdelete":
        msg = "⏳ زمان حذف خودکار خوشامد را بنویس:\nمثلاً:\nتنظیم حذف 60 (به ثانیه)"

    save_welcome_settings(welcome_settings)
    await query.message.reply_text(msg, parse_mode="HTML")

# ✅ ثبت متن خوشامد
async def set_welcome_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = update.effective_user

    member = await context.bot.get_chat_member(chat_id, user.id)
    if member.status not in ["administrator", "creator"] and user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیران می‌تونن متن خوشامد رو تنظیم کنن!")

    if not update.message.reply_to_message or not update.message.reply_to_message.text:
        return await update.message.reply_text("❗ باید روی پیام متنی ریپلای بزنی!")

    text = update.message.reply_to_message.text
    welcome_settings.setdefault(chat_id, {})["text"] = text
    save_welcome_settings(welcome_settings)
    await update.message.reply_text("✅ متن خوشامد با موفقیت ذخیره شد!")

# ✅ ثبت عکس خوشامد
async def set_welcome_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = update.effective_user

    member = await context.bot.get_chat_member(chat_id, user.id)
    if member.status not in ["administrator", "creator"] and user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیران مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("❗ باید روی عکس یا گیف ریپلای بزنی!")

    file = update.message.reply_to_message
    if file.photo:
        file_id = file.photo[-1].file_id
    elif file.animation:
        file_id = file.animation.file_id
    else:
        return await update.message.reply_text("⚠️ فقط عکس یا گیف قابل تنظیم است!")

    welcome_settings.setdefault(chat_id, {})["media"] = file_id
    save_welcome_settings(welcome_settings)
    await update.message.reply_text("✅ عکس خوشامد ذخیره شد!")

# ✅ تنظیم لینک قوانین (بدون /)
async def set_rules_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = update.effective_user
    member = await context.bot.get_chat_member(chat_id, user.id)

    if member.status not in ["administrator", "creator"] and user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیران می‌تونن قوانین رو تنظیم کنن!")

    text = update.message.text.strip().split(maxsplit=2)
    if len(text) < 3:
        return await update.message.reply_text("📎 لطفاً لینک قوانین را بنویس، مثلاً:\nتنظیم قوانین https://t.me/example")

    link = text[2]
    welcome_settings.setdefault(chat_id, {})["rules"] = link
    save_welcome_settings(welcome_settings)
    await update.message.reply_text(f"✅ لینک قوانین ذخیره شد:\n{link}")

# ✅ تنظیم حذف خودکار (بدون /)
async def set_welcome_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = update.effective_user
    member = await context.bot.get_chat_member(chat_id, user.id)

    if member.status not in ["administrator", "creator"] and user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیران مجازند!")

    text = update.message.text.strip().split()
    if len(text) < 3:
        return await update.message.reply_text("⚙️ لطفاً عدد زمان حذف را بنویس، مثلاً:\nتنظیم حذف 60 (به ثانیه)")

    try:
        seconds = int(text[2])
        if not 10 <= seconds <= 86400:
            return await update.message.reply_text("⏳ عدد باید بین 10 تا 86400 باشه!")
    except:
        return await update.message.reply_text("⚠️ لطفاً عدد معتبر وارد کن!")

    welcome_settings.setdefault(chat_id, {})["delete_after"] = seconds
    save_welcome_settings(welcome_settings)
    await update.message.reply_text(f"✅ پیام خوشامد بعد از {seconds} ثانیه حذف خواهد شد!")

# ✅ ارسال خوشامد
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not welcome_settings.get(chat_id, {}).get("enabled"):
        return

    cfg = welcome_settings[chat_id]
    text = cfg.get("text") or "🎉 خوش اومدی به گروه!"
    media = cfg.get("media")
    rules = cfg.get("rules")
    delete_after = cfg.get("delete_after", 0)

    for member in update.message.new_chat_members:
        now = datetime.datetime.now().strftime("%Y/%m/%d ⏰ %H:%M")
        message_text = (
            f"🌙 <b>سلام {member.first_name}!</b>\n"
            f"📅 تاریخ و ساعت: <b>{now}</b>\n"
            f"🏠 گروه: <b>{update.effective_chat.title}</b>\n\n"
            f"{text}"
        )
        if rules:
            message_text += f"\n\n📜 <a href='{rules}'>مشاهده قوانین گروه</a>"

        try:
            if media:
                msg = await update.message.reply_photo(media, caption=message_text, parse_mode="HTML")
            else:
                msg = await update.message.reply_text(message_text, parse_mode="HTML")

            if delete_after > 0:
                await asyncio.sleep(delete_after)
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
        except Exception as e:
            print(f"[WELCOME ERROR] {e}")

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
    # 🚫 جلوگیری از پاسخ در پیوی (فقط جوک و فال مجازند)
    if update.effective_chat.type == "private":
        text = update.message.text.strip().lower()
        allowed = ["جوک", "فال"]

        # اگه پیام جزو مجازها نیست، نادیده بگیر
        if text not in allowed:
            return
    """پاسخ‌دهی اصلی هوش مصنوعی و سیستم یادگیری"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    uid = update.effective_user.id
    chat_id = update.effective_chat.id

    # 🧠 بررسی حالت ریپلی مود گروهی
    if await handle_group_reply_mode(update, context):
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
# ======================= 🌟 پنل اصلی خنگول (استارت + قابلیت‌ها طلایی) =======================
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import datetime, aiofiles, os, asyncio

FEATURES_FILE = "features.txt"

# ======================= 🎨 نمایش پنل =======================
async def show_main_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    """نمایش پنل اصلی برای همه کاربران"""
    # 📖 متن معرفی یا قابلیت‌های سفارشی
    if os.path.exists(FEATURES_FILE):
        async with aiofiles.open(FEATURES_FILE, "r", encoding="utf-8") as f:
            about_text = await f.read()
    else:
        about_text = (
            "✨ <b>خنگول فارسی 8.7 Cloud+ Supreme Pro</b>\n"
            "🤖 هوش اجتماعی، شوخ‌طبعی و احساس واقعی در یک ربات!\n"
            "💬 همراهی با خنده، فال، و هوش اجتماعی بی‌نظیر 🌙"
        )

    keyboard = [
        [InlineKeyboardButton("💬 ارتباط با سازنده", url="https://t.me/NOORI_NOOR")],
        [InlineKeyboardButton("💭 گروه پشتیبانی", url="https://t.me/Poshtibahni")],
        [InlineKeyboardButton("⏰ آیدی و ساعت", callback_data="feature_info")],
        [InlineKeyboardButton("🔮 فال امروز", callback_data="feature_fortune")],
        [InlineKeyboardButton("😂 جوک تصادفی", callback_data="feature_joke")],
        [InlineKeyboardButton("➕ افزودن به گروه", url="https://t.me/Khenqol_bot?startgroup=true")],
        [InlineKeyboardButton("🧩 قابلیت ربات", callback_data="feature_about")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if edit:
        await update.callback_query.edit_message_text(about_text, reply_markup=reply_markup, parse_mode="HTML")
    else:
        await update.message.reply_text(about_text, reply_markup=reply_markup, parse_mode="HTML")


# ======================= 🚀 استارت با انیمیشن لوکس =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انیمیشن خوش‌آمد + نمایش پنل اصلی"""
    msg = await update.message.reply_text("⏳ <b>در حال بارگذاری سیستم خنگول...</b>", parse_mode="HTML")
    await asyncio.sleep(1.7)

    welcome_text = (
        f"🌙 <b>سلام {update.effective_user.first_name}!</b>\n"
        f"🤖 من <b>خنگول فارسی 8.7 Cloud+ Supreme Pro</b> هستم.\n"
        f"✨ رباتی با احساس، شوخ‌طبعی و حافظه‌ی اجتماعی 😄"
    )

    await msg.edit_text(welcome_text, parse_mode="HTML")
    await asyncio.sleep(1.2)

    # 🔹 نمایش منوی اصلی (پیام جدا)
    await show_main_panel(update, context, edit=False)


# ======================= 🧩 ویرایش قابلیت‌ها (فقط ادمین) =======================
async def save_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ثبت یا ویرایش متن قابلیت‌ها فقط برای مدیر اصلی"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه متن قابلیت‌ها رو تغییر بده!")

    if not update.message.reply_to_message or not update.message.reply_to_message.text:
        return await update.message.reply_text("❗ باید روی یک پیام متنی ریپلای بزنی!")

    text = update.message.reply_to_message.text
    async with aiofiles.open(FEATURES_FILE, "w", encoding="utf-8") as f:
        await f.write(text)

    await update.message.reply_text("✅ متن قابلیت‌ها با موفقیت ذخیره شد!")


# ======================= 🎛 دکمه‌های تعاملی =======================
async def feature_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "feature_info":
        user = query.from_user
        now = datetime.datetime.now().strftime("%Y/%m/%d - %H:%M:%S")
        text = (
            f"🆔 آیدی شما: <code>{user.id}</code>\n"
            f"👤 نام: <b>{user.first_name}</b>\n"
            f"📅 تاریخ و ساعت فعلی: <b>{now}</b>"
        )
        try:
            photos = await context.bot.get_user_profile_photos(user.id, limit=1)
            if photos.total_count > 0:
                file_id = photos.photos[0][-1].file_id
                await query.message.reply_photo(file_id, caption=text, parse_mode="HTML")
            else:
                await query.message.reply_text(text, parse_mode="HTML")
        except:
            await query.message.reply_text(text, parse_mode="HTML")

    elif query.data == "feature_joke":
        await query.message.reply_text("😂 برای دیدن جوک بنویس:\n<b>جوک</b>", parse_mode="HTML")

    elif query.data == "feature_fortune":
        await query.message.reply_text("🔮 برای دیدن فال بنویس:\n<b>فال</b>", parse_mode="HTML")

    elif query.data == "feature_about":
        if os.path.exists(FEATURES_FILE):
            async with aiofiles.open(FEATURES_FILE, "r", encoding="utf-8") as f:
                text = await f.read()
        else:
            text = "🧩 هنوز توضیحی برای قابلیت‌ها ثبت نشده!"
        await query.message.reply_text(text, parse_mode="HTML")
        # ======================= Group Protector — خنگول =======================
# قرار بده در فایل اصلی ربات (قبل از app.run_polling)
import json, os, time, asyncio
from telegram import Update
from telegram.ext import ContextTypes

# تنظیمات: نام متغیر Admin ID که تو پروژه استفاده میشه
ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))  # یا مقدار دلخواهت

# مسیر فایل‌ها
DATA_DIR = "moderation_data"
os.makedirs(DATA_DIR, exist_ok=True)
BANS_FILE     = os.path.join(DATA_DIR, "bans.json")
MUTES_FILE    = os.path.join(DATA_DIR, "mutes.json")
WARNS_FILE    = os.path.join(DATA_DIR, "warns.json")
LOCKS_FILE    = os.path.join(DATA_DIR, "locks.json")
ALIASES_FILE  = os.path.join(DATA_DIR, "aliases.json")

def _load(fname, default):
    try:
        if os.path.exists(fname):
            with open(fname, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return default

def _save(fname, data):
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

bans   = _load(BANS_FILE, {})    # { "chat_id": [user_id,...] }
mutes  = _load(MUTES_FILE, {})   # { "chat_id": { user_id: until_ts_or_0 } }
warns  = _load(WARNS_FILE, {})   # { "chat_id": { user_id: count } }
locks  = _load(LOCKS_FILE, {})   # { "chat_id": { "links":True, "photo":True, ... } }
aliases= _load(ALIASES_FILE, {}) # { "farsi_word": "ban", ... }

# تنظیم پیش‌فرض lock types
ALL_LOCK_TYPES = ["links","photo","video","audio","voice","sticker","file","forward","username","gif","text"]
def ensure_chat_struct(chat_id):
    cid = str(chat_id)
    if cid not in bans:   bans[cid] = []
    if cid not in mutes:  mutes[cid] = {}
    if cid not in warns:  warns[cid] = {}
    if cid not in locks:  locks[cid] = {k: False for k in ALL_LOCK_TYPES}
    _save(BANS_FILE, bans); _save(MUTES_FILE, mutes); _save(WARNS_FILE, warns); _save(LOCKS_FILE, locks)

# ---------- کمک‌کننده‌ها ----------
async def is_admin(user_id: int, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """بررسی مدیر بودن (ادمین یا creator) یا ADMIN_ID"""
    if user_id == ADMIN_ID:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator","creator")
    except:
        return False

def style_header(title: str, by_user: str):
    return f"╔══{title}══╗\n{by_user}\n╚" + "═"*20 + "╝"

def find_target_from_arg_or_reply(update: Update, arg:str):
    """بررسی هدف از ریپلای یا آرگومان (id/username) — برمی‌گرداند user_id or None"""
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user.id
    if not arg:
        return None
    # اگر username است شروع با @
    if arg.startswith("@"):
        return arg  # برگشت username (برای ارسال پیام یا جستجو باید resolve کنی)
    # سعی کن به int تبدیل کنی
    try:
        return int(arg)
    except:
        return None

# resolve username -> user_id (ساده، تلاش برای get_chat)
async def resolve_username_to_id(username: str, context: ContextTypes.DEFAULT_TYPE):
    if not username or not username.startswith("@"):
        return None
    try:
        chat = await context.bot.get_chat(username)
        return chat.id
    except:
        return None

# ---------- فرمان‌ها ----------
async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if not await is_admin(user.id, chat_id, context):
        return await update.message.reply_text("⛔ فقط مدیران مجاز به استفاده از این دستور هستند.")
    arg = " ".join(context.args) if context.args else ""
    target = find_target_from_arg_or_reply(update, arg)
    if isinstance(target, str) and target.startswith("@"):
        target = await resolve_username_to_id(target, context)
    if not target:
        return await update.message.reply_text("❗ کاربر هدف را ریپلای کن یا آیدی/یوزرنیم را بده.")
    try:
        await context.bot.ban_chat_member(chat_id, target)
    except Exception as e:
        # گاهی دسترسی نداریم
        await update.message.reply_text(f"⚠️ خطا در بن کردن: {e}")
        return
    ensure_chat_struct(chat_id)
    cid=str(chat_id)
    if target not in bans[cid]:
        bans[cid].append(target)
    _save(BANS_FILE, bans)
    header = style_header("🚫 بن شد 🚫", f"❌ کاربر <code>{target}</code> توسط <b>{user.first_name}</b> بن شد!")
    await update.message.reply_text(header, parse_mode="HTML")

async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if not await is_admin(user.id, chat_id, context):
        return await update.message.reply_text("⛔ فقط مدیران مجاز هستند.")
    arg = " ".join(context.args) if context.args else ""
    target = find_target_from_arg_or_reply(update, arg)
    if isinstance(target, str) and target.startswith("@"):
        target = await resolve_username_to_id(target, context)
    if not target:
        return await update.message.reply_text("❗ کاربر هدف را ریپلای کن یا آیدی/یوزرنیم را بده.")
    try:
        await context.bot.unban_chat_member(chat_id, target)
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در آنبن: {e}")
        return
    cid=str(chat_id)
    if cid in bans and target in bans[cid]:
        bans[cid].remove(target)
        _save(BANS_FILE, bans)
    header = style_header("✅ آنبن شد ✅", f"✅ کاربر <code>{target}</code> توسط <b>{user.first_name}</b> آزاد شد!")
    await update.message.reply_text(header, parse_mode="HTML")

async def cmd_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if not await is_admin(user.id, chat_id, context):
        return await update.message.reply_text("⛔ فقط مدیران می‌تونن اخراج کنن.")
    arg = " ".join(context.args) if context.args else ""
    target = find_target_from_arg_or_reply(update, arg)
    if isinstance(target, str) and target.startswith("@"):
        target = await resolve_username_to_id(target, context)
    if not target:
        return await update.message.reply_text("❗ ریپلای یا آیدی/یوزرنیم بفرست.")
    try:
        await context.bot.ban_chat_member(chat_id, target)
        await context.bot.unban_chat_member(chat_id, target, only_if_banned=False)
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در اخراج: {e}")
        return
    header = style_header("👢 اخراج شد 👢", f"👢 کاربر <code>{target}</code> توسط <b>{user.first_name}</b> اخراج شد!")
    await update.message.reply_text(header, parse_mode="HTML")

async def cmd_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if not await is_admin(user.id, chat_id, context):
        return await update.message.reply_text("⛔ فقط مدیران می‌تونن بی‌صدا کنن.")
    target = find_target_from_arg_or_reply(update, " ".join(context.args) if context.args else "")
    if isinstance(target, str) and target.startswith("@"):
        target = await resolve_username_to_id(target, context)
    if not target:
        return await update.message.reply_text("❗ کاربر را ریپلای کن یا آیدی بده.")
    # default indefinite mute (store as 0)
    ensure_chat_struct(chat_id)
    cid=str(chat_id)
    mutes[cid][str(target)] = 0
    _save(MUTES_FILE, mutes)
    header = style_header("🔇 بی‌صدا شد 🔇", f"🔇 کاربر <code>{target}</code> توسط <b>{user.first_name}</b> بی‌صدا شد!")
    await update.message.reply_text(header, parse_mode="HTML")

async def cmd_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if not await is_admin(user.id, chat_id, context):
        return await update.message.reply_text("⛔ فقط مدیران مجازند.")
    target = find_target_from_arg_or_reply(update, " ".join(context.args) if context.args else "")
    if isinstance(target, str) and target.startswith("@"):
        target = await resolve_username_to_id(target, context)
    if not target:
        return await update.message.reply_text("❗ کاربر را ریپلای کن یا آیدی بده.")
    cid=str(chat_id)
    if cid in mutes and str(target) in mutes[cid]:
        del mutes[cid][str(target)]
        _save(MUTES_FILE, mutes)
    header = style_header("🔊 از بی‌صدا خارج شد 🔊", f"🔊 کاربر <code>{target}</code> توسط <b>{user.first_name}</b> از بی‌صدا بیرون آمد!")
    await update.message.reply_text(header, parse_mode="HTML")

async def cmd_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if not await is_admin(user.id, chat_id, context):
        return await update.message.reply_text("⛔ فقط مدیران می‌تونن اخطار بدن.")
    target = find_target_from_arg_or_reply(update, " ".join(context.args) if context.args else "")
    if isinstance(target, str) and target.startswith("@"):
        target = await resolve_username_to_id(target, context)
    if not target:
        return await update.message.reply_text("❗ کاربر را ریپلای کن یا آیدی بده.")
    ensure_chat_struct(chat_id)
    cid=str(chat_id)
    warns[cid][str(target)] = warns[cid].get(str(target), 0) + 1
    _save(WARNS_FILE, warns)
    count = warns[cid][str(target)]
    header = style_header("⚠️ اخطار داده شد ⚠️", f"⚠️ کاربر <code>{target}</code> توسط <b>{user.first_name}</b> اخطار گرفت! (تعداد: {count})")
    await update.message.reply_text(header, parse_mode="HTML")

async def cmd_unwarn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if not await is_admin(user.id, chat_id, context):
        return await update.message.reply_text("⛔ فقط مدیران مجازند.")
    target = find_target_from_arg_or_reply(update, " ".join(context.args) if context.args else "")
    if isinstance(target, str) and target.startswith("@"):
        target = await resolve_username_to_id(target, context)
    if not target:
        return await update.message.reply_text("❗ کاربر را ریپلای کن یا آیدی بده.")
    cid=str(chat_id)
    if cid in warns and str(target) in warns[cid]:
        warns[cid][str(target)] = max(0, warns[cid][str(target)] - 1)
        _save(WARNS_FILE, warns)
    header = style_header("✅ اخطار حذف شد ✅", f"✅ یک اخطار از کاربر <code>{target}</code> توسط <b>{user.first_name}</b> حذف شد.")
    await update.message.reply_text(header, parse_mode="HTML")

async def cmd_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف پیام ریپلای شده"""
    chat_id = update.effective_chat.id
    user = update.effective_user
    if not await is_admin(user.id, chat_id, context):
        return await update.message.reply_text("⛔ فقط مدیران می‌تونن پیام رو پاک کنن.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("❗ روی پیام مورد نظر ریپلای کن.")
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.reply_to_message.message_id)
        header = style_header("🗑 پیام پاک شد 🗑", f"✅ پیام توسط <b>{user.first_name}</b> حذف شد.")
        await update.message.reply_text(header, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در حذف پیام: {e}")

async def cmd_purge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاکسازی تعداد زیاد پیام — استفاده: /purge 100 (حداکثر 9999)"""
    chat_id = update.effective_chat.id
    user = update.effective_user
    if not await is_admin(user.id, chat_id, context):
        return await update.message.reply_text("⛔ فقط مدیران می‌تونن پاکسازی کنن.")
    if not context.args:
        return await update.message.reply_text("❗ تعداد پیام برای پاکسازی را بده: /purge 100")
    try:
        n = int(context.args[0])
        if n < 1 or n > 9999:
            return await update.message.reply_text("⚠️ عدد باید بین 1 تا 9999 باشد.")
    except:
        return await update.message.reply_text("⚠️ عدد معتبر وارد کن.")
    # قراره از پیام فعلی تا n پیام قبل رو حذف کنیم
    deleted = 0
    try:
        # get chat history (bot can only delete messages that bot can delete)
        async for msg in context.bot.get_chat(chat_id).iter_history(limit=n):
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg.message_id)
                deleted += 1
            except:
                pass
    except Exception:
        # fallback: تلاش حذف پیام‌های اطراف با استفاده از پیام ریپلای شده (ساده‌تر)
        pass
    header = style_header("🧹 پاکسازی انجام شد 🧹", f"✅ {deleted} پیام توسط <b>{user.first_name}</b> پاک شد.")
    await update.message.reply_text(header, parse_mode="HTML")

# ---------- قفل‌ها ----------
async def cmd_lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قفل کردن نوعی از محتوا: /lock photo"""
    chat_id = update.effective_chat.id
    user = update.effective_user
    if not await is_admin(user.id, chat_id, context):
        return await update.message.reply_text("⛔ فقط مدیران مجازند.")
    if not context.args:
        return await update.message.reply_text("❗ نام قفل را بده. نمونه‌ها: links, photo, video, sticker, audio, voice, file, gif, text")
    locktype = context.args[0].lower()
    if locktype not in ALL_LOCK_TYPES:
        return await update.message.reply_text("⚠️ نوع قفل نامعتبر است.")
    ensure_chat_struct(chat_id)
    locks[str(chat_id)][locktype] = True
    _save(LOCKS_FILE, locks)
    await update.message.reply_text(style_header("🔒 قفل شد 🔒", f"🔒 {locktype} توسط <b>{user.first_name}</b> قفل شد."), parse_mode="HTML")

async def cmd_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if not await is_admin(user.id, chat_id, context):
        return await update.message.reply_text("⛔ فقط مدیران مجازند.")
    if not context.args:
        return await update.message.reply_text("❗ نام قفل را بده: links, photo, video, sticker, audio, voice, file, gif, text")
    locktype = context.args[0].lower()
    if locktype not in ALL_LOCK_TYPES:
        return await update.message.reply_text("⚠️ نوع قفل نامعتبر است.")
    ensure_chat_struct(chat_id)
    locks[str(chat_id)][locktype] = False
    _save(LOCKS_FILE, locks)
    await update.message.reply_text(style_header("🔓 باز شد 🔓", f"🔓 {locktype} توسط <b>{user.first_name}</b> باز شد."), parse_mode="HTML")

# ---------- alias system ----------
async def cmd_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ایجاد alias: /alias ban بن"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    if not await is_admin(user.id, chat_id, context):
        return await update.message.reply_text("⛔ فقط مدیران می‌تونن alias بسازن.")
    if len(context.args) < 2:
        return await update.message.reply_text("❗ استفاده: /alias <target_command> <alias_word>  (مثال: /alias ban بن)")
    target = context.args[0].lower()
    alias_word = context.args[1]
    # ذخیره (global)
    aliases[alias_word] = target
    _save(ALIASES_FILE, aliases)
    await update.message.reply_text(f"✅ alias ثبت شد: <b>{alias_word}</b> ⇒ <code>{target}</code>", parse_mode="HTML")

async def cmd_unalias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    if not await is_admin(user.id, chat_id, context):
        return await update.message.reply_text("⛔ فقط مدیران می‌تونن حذف alias کنن.")
    if not context.args:
        return await update.message.reply_text("❗ استفاده: /unalias <alias_word>")
    alias_word = context.args[0]
    if alias_word in aliases:
        del aliases[alias_word]
        _save(ALIASES_FILE, aliases)
        await update.message.reply_text(f"✅ alias <b>{alias_word}</b> حذف شد.", parse_mode="HTML")
    else:
        await update.message.reply_text("⚠️ alias پیدا نشد.")

# ---------- پردازش پیام‌ها با alias (بدون /) ----------
async def alias_message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اگر پیام برابر یکی از alias ها بود، فراخوانی توابع معادل انجام میشه."""
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip().split()
    if not text:
        return
    first = text[0]
    # اگر اول کلمه مستقیما alias است
    if first in aliases:
        mapped = aliases[first]  # ex: "ban"
        # ساخت یک fake context.args تا تابع اصلی کار کنه
        rest = text[1:]
        # دایرکت کال به تابع مناسب — لیست map
        mapping = {
            "ban": cmd_ban,
            "unban": cmd_unban,
            "kick": cmd_kick,
            "mute": cmd_mute,
            "unmute": cmd_unmute,
            "warn": cmd_warn,
            "unwarn": cmd_unwarn,
            "del": cmd_del,
            "purge": cmd_purge,
            "lock": cmd_lock,
            "unlock": cmd_unlock,
            "alias": cmd_alias,
            "unalias": cmd_unalias
        }
        func = mapping.get(mapped)
        if func:
            # ساخت موقت context.args
            context.args = rest
            await func(update, context)
            return
    # اگر پیام با نقطه‌گذاری /command هم اومده (مثلا بدون slash) نادیده گرفته میشه — هدف alias کلمات ساده است

# ---------- ثبت handler ها (راحت داخل main اضافه کن) ----------
# در main بعد از ساخت app این‌ها را اضافه کن:
#
#    app.add_handler(CommandHandler("ban", cmd_ban))
#    app.add_handler(CommandHandler("unban", cmd_unban))
#    app.add_handler(CommandHandler("kick", cmd_kick))
#    app.add_handler(CommandHandler("mute", cmd_mute))
#    app.add_handler(CommandHandler("unmute", cmd_unmute))
#    app.add_handler(CommandHandler("warn", cmd_warn))
#    app.add_handler(CommandHandler("unwarn", cmd_unwarn))
#    app.add_handler(CommandHandler("del", cmd_del))
#    app.add_handler(CommandHandler("purge", cmd_purge))
#    app.add_handler(CommandHandler("lock", cmd_lock))
#    app.add_handler(CommandHandler("unlock", cmd_unlock))
#    app.add_handler(CommandHandler("alias", cmd_alias))
#    app.add_handler(CommandHandler("unalias", cmd_unalias))
#
# و برای پشتیبانی از alias های بدون /:
#    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, alias_message_router))
#
# -------------------------------------------------------
# توجه: اگر از قبل MessageHandler ای برای reply (مثل هوش مصنوعی) دادی که تمامی پیامها رو می‌گیرد،
# باید alias_message_router را قبل از آن handler اضافه کنی تا اول alias بررسی شود.
# همچنین برخی عملیات حذف/بن نیاز به پرمیشن ربات دارد (ربات باید ادمین گروه باشد).
# =======================================================
# ======================= 🚀 اجرای نهایی =======================
if __name__ == "__main__":
    print("🤖 خنگول فارسی 8.7 Cloud+ Supreme Pro Stable+ آماده به خدمت است ...")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_error_handler(handle_error)

    # =================== 🔒 Group Protector Handlers ===================
    app.add_handler(CommandHandler("ban", cmd_ban))
    app.add_handler(CommandHandler("unban", cmd_unban))
    app.add_handler(CommandHandler("kick", cmd_kick))
    app.add_handler(CommandHandler("mute", cmd_mute))
    app.add_handler(CommandHandler("unmute", cmd_unmute))
    app.add_handler(CommandHandler("warn", cmd_warn))
    app.add_handler(CommandHandler("unwarn", cmd_unwarn))
    app.add_handler(CommandHandler("del", cmd_del))
    app.add_handler(CommandHandler("purge", cmd_purge))
    app.add_handler(CommandHandler("lock", cmd_lock))
    app.add_handler(CommandHandler("unlock", cmd_unlock))
    app.add_handler(CommandHandler("alias", cmd_alias))
    app.add_handler(CommandHandler("unalias", cmd_unalias))

    # 🧠 سیستم alias بدون / باید قبل از reply قرار بگیره
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, alias_message_router))

    # ================================================================
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
    app.add_handler(CommandHandler("reply", toggle_reply_mode))

    # 🔹 پنل اصلی و قابلیت‌ها
    app.add_handler(MessageHandler(filters.Regex("^ثبت قابلیت$"), save_features))
    app.add_handler(CallbackQueryHandler(feature_button_handler, pattern="^feature_"))

    # 🔹 سیستم خوشامد پویا و پنل گرافیکی
    app.add_handler(MessageHandler(filters.Regex("^خوشامد$"), open_welcome_panel), group=-1)
    app.add_handler(CallbackQueryHandler(welcome_panel_buttons, pattern="^welcome_"), group=-1)
    app.add_handler(MessageHandler(filters.Regex("^ثبت خوشامد$"), set_welcome_text), group=-1)
    app.add_handler(MessageHandler(filters.Regex("^ثبت عکس خوشامد$"), set_welcome_media), group=-1)
    app.add_handler(MessageHandler(filters.Regex(r"^تنظیم قوانین"), set_rules_link))
    app.add_handler(MessageHandler(filters.Regex(r"^تنظیم حذف"), set_welcome_timer))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome), group=-1)

    # 🔹 راهنمای قابل ویرایش
    app.add_handler(MessageHandler(filters.Regex("^ثبت راهنما$"), save_custom_help))
    app.add_handler(MessageHandler(filters.Regex("^راهنما$"), show_custom_help))

    # 🔹 پیام‌ها و اسناد
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # 🔹 هندلر عمومیِ آخر
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    # 🔹 هنگام استارت
    async def on_startup(app):
        await notify_admin_on_startup(app)
        app.create_task(auto_backup(app.bot))
        app.create_task(start_auto_brain_loop(app.bot))
        print("🌙 [SYSTEM] Startup tasks scheduled ✅")

    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)
