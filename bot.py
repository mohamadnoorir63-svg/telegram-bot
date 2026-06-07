import asyncio
import os
import random
import re
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
from reply_keyboard_fixed import MAIN_KEYBOARD, fixed_button_handler

from welcome_module import (
    open_welcome_panel,
    welcome_panel_buttons,
    welcome_input_handler,
    welcome
)
from telegram.ext import InlineQueryHandler

from selective_backup import selective_backup_menu, selective_backup_buttons
from auto_brain import auto_backup
from command_manager import (
    save_command,
    delete_command,
    edit_command,      # ⬅️ اینو اضافه کن
    handle_custom_command,
    list_commands,
    cleanup_group_commands
)
from group_control.daily_stats import (
    record_message_activity,
    record_new_members,
    record_left_members,
    show_user_id,       # تابع آیدی
    show_group_stats,   # تابع آمار گروه
    send_nightly_stats
)

from panels.panel_menu import (
    Tastatur_menu,
    Tastatur_buttons,
    toggle_lock_button,
    handle_lock_page_switch,
    handle_fun_buttons,
    
)
from data_manager import register_private_user, register_group
# ======================= 🧾 ثبت گروه و کاربران =======================

async def pv_logger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        register_private_user(update.effective_user)


async def group_logger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ["group", "supergroup"]:
        register_group(update.effective_chat, update.effective_user)
from group_control.origin_title import register_origin_title_handlers
from ai_chat.chatgpt_panel import show_ai_panel, chat, start_ai_chat, stop_ai_chat
from weather_module.weather_panel import show_weather
from modules.azan_module import get_azan_time, get_ramadan_status
from panels.link_panel import link_panel, link_panel_buttons
from panels.panel_menu import Tastatur_menu, Tastatur_buttons
from group_cleanup.funny_cleanup import register_cleanup_handlers
from telegram.ext import (
    MessageHandler,
    CallbackQueryHandler,
    filters
)

# ======================= ⚙️ تنظیمات پایه و سودوها =======================
from telegram import Update
from telegram.ext import ContextTypes

async def add_sudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in SUDO_IDS:
        return await update.message.reply_text("⛔ فقط مدیر اصلی یا سودوها می‌تونن سودو اضافه کنن!")

    if not context.args:
        return await update.message.reply_text("🔹 استفاده: /addsudo <ID>")

    try:
        new_id = int(context.args[0])
        if new_id in SUDO_IDS:
            return await update.message.reply_text("⚠️ این کاربر از قبل سودو هست!")

        SUDO_IDS.append(new_id)
        save_sudos(SUDO_IDS)
        await update.message.reply_text(
            f"✅ کاربر با آیدی <code>{new_id}</code> به لیست سودوها اضافه شد.",
            parse_mode="HTML"
        )
    except:
        await update.message.reply_text("⚠️ لطفاً آیدی عددی معتبر وارد کن!")


async def del_sudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in SUDO_IDS:
        return await update.message.reply_text("⛔ فقط مدیر اصلی یا سودوها می‌تونن حذف کنن!")

    if not context.args:
        return await update.message.reply_text("🔹 استفاده: /delsudo <ID>")

    try:
        rem_id = int(context.args[0])
        if rem_id not in SUDO_IDS:
            return await update.message.reply_text("⚠️ این کاربر سودو نیست!")

        SUDO_IDS.remove(rem_id)
        save_sudos(SUDO_IDS)
        await update.message.reply_text(
            f"🗑️ کاربر <code>{rem_id}</code> از لیست سودوها حذف شد.",
            parse_mode="HTML"
        )
    except:
        await update.message.reply_text("⚠️ آیدی معتبر وارد کن!")


async def list_sudos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in SUDO_IDS:
        return await update.message.reply_text("⛔ فقط سودوها مجازند!")

    text = "👑 <b>لیست سودوهای فعلی:</b>\n\n"
    for i, sid in enumerate(SUDO_IDS, start=1):
        text += f"{i}. <code>{sid}</code>\n"

    await update.message.reply_text(text, parse_mode="HTML")
# 🧠 نکته مهم:
# ❌ از اینجا دیگه admin_panel رو import نکن!
# ✅ اون رو بعد از ساخت app در بخش اصلی فایل (پایین) اضافه خواهیم کرد.
# 🎯 تنظیمات پایه
TOKEN = os.getenv("BOT_TOKEN")
import json

ADMIN_FILE = "sudo_list.json"

def load_sudos():
    if os.path.exists(ADMIN_FILE):
        try:
            with open(ADMIN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return [8588347189]  # آیدی مدیر اصلی به‌صورت پیش‌فرض

def save_sudos(data):
    with open(ADMIN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

SUDO_IDS = load_sudos()



# ────────────────────────────── ترجمه با رپلی ──────────────────────────────
async def translate_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return  # فقط روی ریپلی

    text = update.message.reply_to_message.text
    if not text:
        return

    cmd = update.message.text.strip().lower()

    target_lang = None
    if "ترجمه به فارسی" in cmd:
        target_lang = "fa"
    elif "ترجمه به انگلیسی" in cmd:
        target_lang = "en"
    elif "ترجمه به آلمانی" in cmd:
        target_lang = "de"
    else:
        return  # اگر دستور معتبر نیست، هیچ کاری نکند

    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        await update.message.reply_text(f"🌐 ترجمه ({target_lang}):\n{translated}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ترجمه: {e}")

# ======================= 🧠 شروع ساده بدون افکت =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استارت → نمایش پنل اصلی + کیبورد ثابت"""

    # 1) نمایش پنل اصلی
    await show_main_panel(update, context)

    # 2) نمایش کیبورد ثابت  
    await update.message.reply_text(  
        "👇❣️:",  
        reply_markup=MAIN_KEYBOARD  
    )

# ==========================================================
# 🤖 پاسخ ویژه برای سازنده (سودو اصلی)
# ==========================================================
import os
import random
from telegram import Update
from telegram.ext import ContextTypes

SUDO_USERS = [8588347189, 98765432]  # آیدی سودوها

async def sudo_bot_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """وقتی کاربر پیام 'ربات' فرستاد — پاسخ مخصوص سودو یا مدیران گروه"""
    ADMIN_ID = int(os.getenv("ADMIN_ID", "8588347189"))
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type

    has_access = False

    # پیام در گروه → فقط مدیران یا سودوها
    if chat_type in ["group", "supergroup"]:
        try:
            member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
            if member.status in ["administrator", "creator"] or user_id in SUDO_USERS:
                has_access = True
        except:
            pass
    else:  # پیوی → فقط سودو اصلی
        if user_id == ADMIN_ID or user_id in SUDO_USERS:
            has_access = True

    if not has_access:
        return  # سکوت برای بقیه

    replies = [
        "👑 جانم فدات؟ 😎",
        "🤖 در خدمتتم رئیس!",
        "⚡ بفرما قربان!",
        "🧠 گوش به فرمانتم!",
        "✨ دستور بده شاه !",
        "😄 آماده‌م برای هر کاری!",
        "🔥 بگو رئیس، منتظرم!"
    ]

    # انتخاب تصادفی پاسخ
    reply = random.choice(replies)
    await update.message.reply_text(reply)
# ======================= 📊 آمار ربات واقعی =======================
    import json
import os
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes


# مسیر فایل‌ها
GROUP_FILE = "data/groups.json"
USER_FILE = "data/users.json"


# =====================================================================
#  🔥 حذف خودکار گروه و کاربر وقتی ربات کیک/حذف/بلاک می‌شود
# =====================================================================
async def bot_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    مراقب تغییر وضعیت ربات است.
    - اگر از گروه حذف شد → حذف از groups.json
    - اگر کاربر ربات را بلاک کرد → حذف از users.json
    """
    data = update.my_chat_member
    chat = data.chat
    new = data.new_chat_member

    # اگر ربات از چت حذف شد
    if new.status in ("left", "kicked"):

        # ==============================================================
        # 🏠 اگر گروه باشد → حذف گروه
        # ==============================================================
        if chat.type in ("group", "supergroup"):

            if os.path.exists(GROUP_FILE):
                try:
                    with open(GROUP_FILE, "r", encoding="utf-8") as f:
                        groups = json.load(f)

                    gid = str(chat.id)

                    if gid in groups:
                        del groups[gid]

                        with open(GROUP_FILE, "w", encoding="utf-8") as f:
                            json.dump(groups, f, indent=4, ensure_ascii=False)

                except:
                    pass

            return

        # ==============================================================
        # 👤 اگر PV باشد → کاربر ربات را بلاک کرده → حذف
        # ==============================================================
        if chat.type == "private":

            if os.path.exists(USER_FILE):
                try:
                    with open(USER_FILE, "r", encoding="utf-8") as f:
                        users = json.load(f)

                    uid = str(chat.id)

                    if uid in users:
                        del users[uid]

                        with open(USER_FILE, "w", encoding="utf-8") as f:
                            json.dump(users, f, indent=4, ensure_ascii=False)

                except:
                    pass

            return



# =====================================================================
# 📊 دستور /stats — آمار کلی
# =====================================================================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # --- کاربران ---
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, "r", encoding="utf-8") as f:
                users = json.load(f)
            total_users = len(users)
        except:
            total_users = 0
    else:
        total_users = 0

    # --- گروه‌ها ---
    if os.path.exists(GROUP_FILE):
        try:
            with open(GROUP_FILE, "r", encoding="utf-8") as f:
                groups = json.load(f)
            total_groups = len(groups)
            total_members = sum(len(g.get("members", [])) for g in groups.values())
        except:
            total_groups = 0
            total_members = 0
    else:
        total_groups = 0
        total_members = 0

    text = (
        "📊 <b>آمار کلی ربات</b>\n\n"
        f"👤 کاربران پیوی: <b>{total_users}</b>\n"
        f"🏠 گروه‌ها: <b>{total_groups}</b>\n"
        f"👥 اعضای ثبت‌شده در گروه‌ها: <b>{total_members}</b>\n"
        f"🕓 آخرین بروزرسانی: <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>"
    )

    await update.message.reply_text(text, parse_mode="HTML")



# =====================================================================
# 🏠 دستور /fullstats — آمار کامل گروه‌ها
# =====================================================================
async def fullstats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    ADMIN_ID = int(os.getenv("ADMIN_ID", "123"))
    SUDO_IDS = [ADMIN_ID]

    if update.effective_user.id not in SUDO_IDS:
        return await update.message.reply_text("⛔ فقط مدیر اصلی اجازه دارد.")

    # وجود فایل
    if not os.path.exists(GROUP_FILE):
        return await update.message.reply_text("ℹ️ هیچ گروهی ثبت نشده است.")

    # خواندن فایل
    try:
        with open(GROUP_FILE, "r", encoding="utf-8") as f:
            groups = json.load(f)
    except:
        return await update.message.reply_text("⚠️ خطا در خواندن فایل گروه‌ها.")

    if not groups:
        return await update.message.reply_text("ℹ️ هنوز هیچ گروهی ثبت نشده.")

    text = "📈 <b>آمار کامل گروه‌ها</b>:\n\n"

    for gid, info in groups.items():
        title = info.get("title", "بدون‌نام")
        members = len(info.get("members", []))
        last = info.get("last_active", "نامشخص")

        text += (
            f"🏠 <b>{title}</b>\n"
            f"🆔 <code>{gid}</code>\n"
            f"👥 تعداد اعضا: <b>{members}</b>\n"
            f"🕓 آخرین فعالیت: <b>{last}</b>\n"
            f"━━━━━━━━━━━━━━\n"
        )

    # جلوگیری از ارور 400
    if len(text) > 4000:
        text = text[:3990] + "..."

    await update.message.reply_text(text, parse_mode="HTML")
  # ======================= ☁️ بک‌آپ و بازیابی هماهنگ =======================
    import os
import zipfile
import shutil
import asyncio
import json
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes


BACKUP_FOLDER = "backups"
ADMIN_ID = int(os.getenv("ADMIN_ID", "8588347189"))

# -----------------------------------------------------
# ایجاد فایل‌ها و پوشه‌های ضروری در صورت نبودن
# -----------------------------------------------------
def init_files():

    base_files = [
        "data/groups.json",
        "data/users.json",
        "data/custom_commands.json",
        "jokes.json",
        "fortunes.json",
        "stickers.json",

        # ⚡️ فایل‌های جدید که باید همیشه ساخته شوند
        "data/youtube_cache.json",
        "data/sound_cache.json",
    ]

    for f in base_files:
        folder = os.path.dirname(f)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

        if not os.path.exists(f):
            if f.endswith(".json"):
                with open(f, "w", encoding="utf-8") as fp:
                    json.dump({}, fp, ensure_ascii=False, indent=2)


# -----------------------------------------------------
# فایل‌هایی که باید در بکاپ قرار بگیرند
# -----------------------------------------------------
def _should_include_in_backup(path: str) -> bool:
    lowered = path.lower()

    skip_dirs = ["__pycache__", ".git", "venv", "restore_temp", BACKUP_FOLDER]
    if any(sd in lowered for sd in skip_dirs):
        return False

    if lowered.endswith(".zip") or os.path.basename(lowered).startswith("backup_"):
        return False

    important_files = [

        # فایل‌های قدیمی
        "data/groups.json",
        "data/users.json",
        "data/custom_commands.json",
        "jokes.json",
        "fortunes.json",
        "stickers.json",
        "fortunes_media",

        # ⚡️ فایل‌های جدید مهم:
        "data/youtube_cache.json",
        "data/youtube_cache_backup.json",
        "data/sound_cache.json",
        "data/sound_cache_backup.json",
    ]

    if any(path.endswith(f) or f in path for f in important_files):
        return True

    if lowered.endswith((".jpg", ".jpeg", ".png", ".webp", ".mp3", ".ogg")):
        return True

    return False


# -----------------------------------------------------
# بکاپ‌گیری خودکار هر ۶ ساعت
# -----------------------------------------------------
async def auto_backup(bot):
    while True:
        await cloudsync_internal(bot, "Auto Backup")
        await asyncio.sleep(21600)  # هر ۶ ساعت


# -----------------------------------------------------
# ایجاد فایل بکاپ ZIP و ارسال به مدیر
# -----------------------------------------------------
async def cloudsync_internal(bot, reason="Manual Backup"):

    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"backup_{now}.zip"

    try:
        with zipfile.ZipFile(filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk("."):
                for f in files:
                    full = os.path.join(root, f)
                    if _should_include_in_backup(full):
                        arc = os.path.relpath(full, ".")
                        zipf.write(full, arc)

        size = os.path.getsize(filename) / (1024 * 1024)

        caption = (
            "🧠 <b>بک‌آپ موفق!</b>\n"
            f"📆 <code>{now}</code>\n"
            f"💾 حجم: <code>{size:.2f}MB</code>\n"
            f"☁️ نوع: {reason}"
        )

        with open(filename, "rb") as fp:
            await bot.send_document(ADMIN_ID, fp, caption=caption, parse_mode="HTML")

    except Exception as e:
        try:
            await bot.send_message(ADMIN_ID, f"⚠️ خطا در بکاپ:\n{e}")
        except:
            pass

    finally:
        if os.path.exists(filename):
            os.remove(filename)


# -----------------------------------------------------
# دستور /cloudsync برای مدیر
# -----------------------------------------------------
async def cloudsync(update, context):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی!")
    await cloudsync_internal(context.bot, "Manual Cloud Backup")


# -----------------------------------------------------
# دستور بکاپ‌گیری دستی
# -----------------------------------------------------
async def backup(update, context):
    await cloudsync_internal(context.bot, "Manual Backup")
    await update.message.reply_text("✅ بک‌آپ کامل ساخته و ارسال شد!")


# -----------------------------------------------------
# شروع فرآیند بازیابی
# -----------------------------------------------------
async def restore(update, context):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی!")

    context.user_data["await_restore"] = True
    return await update.message.reply_text("📂 لطفاً فایل ZIP بک‌آپ را ارسال کنید.")


# -----------------------------------------------------
# پیدا کردن فایل داخل بکاپ استخراج‌شده
# -----------------------------------------------------
def _find_in_extracted(root, target):
    result = []
    for r, dirs, files in os.walk(root):
        for d in dirs:
            full = os.path.join(r, d)
            if full.replace("\\", "/").endswith(target):
                result.append(full)
        for f in files:
            full = os.path.join(r, f)
            if full.replace("\\", "/").endswith(target):
                result.append(full)
    return result


# -----------------------------------------------------
# پردازش ZIP و بازیابی فایل‌ها
# -----------------------------------------------------
async def handle_document(update, context):

    if not context.user_data.get("await_restore"):
        return

    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی!")

    doc = update.message.document
    if not doc or not doc.file_name.endswith(".zip"):
        return await update.message.reply_text("❗ لطفاً یک ZIP معتبر ارسال کنید.")

    restore_zip = "restore.zip"
    restore_dir = "restore_temp"

    try:
        tg_file = await doc.get_file()
        await tg_file.download_to_drive(restore_zip)

        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        os.makedirs(restore_dir)

        with zipfile.ZipFile(restore_zip, "r") as z:
            z.extractall(restore_dir)

        important = [

            "jokes.json",
            "fortunes.json",
            "stickers.json",

            "data/groups.json",
            "data/users.json",
            "data/custom_commands.json",

            "data/youtube_cache.json",
            "data/sound_cache.json",

            "fortunes_media",
        ]

        moved = False

        for f in important:

            candidates = _find_in_extracted(restore_dir, f)
            if not candidates:
                continue

            src = candidates[0]
            dst = f
            dst_dir = os.path.dirname(dst)

            if os.path.isdir(src):
                if not os.path.exists(dst):
                    os.makedirs(dst, exist_ok=True)

                for r, _, files in os.walk(src):
                    for file in files:
                        p_src = os.path.join(r, file)
                        rel = os.path.relpath(p_src, src)
                        p_dst = os.path.join(dst, rel)
                        os.makedirs(os.path.dirname(p_dst), exist_ok=True)
                        if os.path.exists(p_dst):
                            os.remove(p_dst)
                        shutil.move(p_src, p_dst)

                moved = True

            else:
                if dst_dir and not os.path.exists(dst_dir):
                    os.makedirs(dst_dir, exist_ok=True)
                if os.path.exists(dst):
                    os.remove(dst)
                shutil.move(src, dst)
                moved = True

        init_files()

        if moved:
            await update.message.reply_text("✅ بازیابی کامل انجام شد!")
        else:
            await update.message.reply_text("ℹ️ فایل مهمی برای جایگزینی پیدا نشد.")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بازیابی:\n{e}")

    finally:
        if os.path.exists(restore_zip):
            os.remove(restore_zip)
        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        context.user_data["await_restore"] = False


# -----------------------------------------------------
# پاکسازی حافظه
# -----------------------------------------------------
async def reset_memory(update, context):

    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی!")

    for f in [
        "data/groups.json",
        "data/users.json",
        "data/custom_commands.json",
        "jokes.json",
        "fortunes.json",
        "stickers.json",
        "data/youtube_cache.json",
        "data/sound_cache.json",
    ]:
        if os.path.exists(f):
            os.remove(f)

    init_files()
    await update.message.reply_text("🧹 حافظه کامل ریست شد و دوباره ساخته شد.")


# -----------------------------------------------------
# اطلاعات سیستم
# -----------------------------------------------------
async def reload_memory(update, context):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر!")

    init_files()

    def count(path):
        if not os.path.exists(path):
            return 0
        try:
            with open(path, "r", encoding="utf-8") as fp:
                d = json.load(fp)
                return len(d) if isinstance(d, (dict, list)) else 0
        except:
            return 0

    msg = (
        "🔄 سیستم بوت شد!\n"
        f"👥 گروه‌ها: {count('data/groups.json')}\n"
        f"👤 کاربران: {count('data/users.json')}\n"
        f"😂 جوک‌ها: {count('jokes.json')}\n"
        f"🔮 فال‌ها: {count('fortunes.json')}"
    )

    await update.message.reply_text(msg)
# ======================= فال جوک =======================
import os
import json
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# -----------------------------
# فایل‌های ذخیره
# -----------------------------
FILE_JOKES = "jokes.json"
FILE_FORTUNES = "fortunes.json"

# -----------------------------
# توابع کمکی JSON
# -----------------------------
def load_data(file_name):
    if os.path.exists(file_name):
        with open(file_name, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_data(file_name, data):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# -----------------------------
# ---------- جوک -------------
# -----------------------------
async def send_random_joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data(FILE_JOKES)
    if not data:
        await update.message.reply_text("هیچ جوکی ثبت نشده 😔")
        return
    key, val = random.choice(list(data.items()))
    await update.message.reply_text(val.get("value"))

async def save_joke(update: Update):
    reply_msg = update.message.reply_to_message
    if not reply_msg or not reply_msg.text:
        await update.message.reply_text("لطفاً روی پیام جوک ریپلای کنید.")
        return

    data = load_data(FILE_JOKES)
    # جلوگیری از تکراری بودن
    if any(v.get("value") == reply_msg.text for v in data.values()):
        await update.message.reply_text("⚠️ این جوک قبلاً ثبت شده است.")
        return

    new_id = str(max([int(k) for k in data.keys()], default=0) + 1)
    data[new_id] = {"value": reply_msg.text}
    save_data(FILE_JOKES, data)
    await update.message.reply_text("✅ جوک ثبت شد!")

async def delete_joke(update: Update):
    reply_msg = update.message.reply_to_message
    if not reply_msg:
        await update.message.reply_text("لطفاً روی پیام جوک ریپلای کنید.")
        return

    data = load_data(FILE_JOKES)
    to_delete = None
    for k, v in data.items():
        if v.get("value") == (reply_msg.text or ""):
            to_delete = k
            break
    if to_delete:
        del data[to_delete]
        save_data(FILE_JOKES, data)
        await update.message.reply_text("✅ جوک حذف شد!")
    else:
        await update.message.reply_text("⚠️ جوک پیدا نشد.")

async def list_jokes(update: Update):
    data = load_data(FILE_JOKES)
    if not data:
        await update.message.reply_text("هیچ جوکی ثبت نشده 😔")
        return

    msg = "📜 لیست جوک‌ها:\n"
    for k, v in data.items():
        msg += f"{k}: {v.get('value')[:50]}{'...' if len(v.get('value',''))>50 else ''}\n"
    await update.message.reply_text(msg)

# -----------------------------
# ---------- فال -------------
# -----------------------------
async def send_fortune(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data(FILE_FORTUNES)
    if not data:
        await update.message.reply_text("هنوز فالی ثبت نشده 😔")
        return

    key, val = random.choice(list(data.items()))
    content_type = val.get("type", "text")
    value = val.get("value", "")

    try:
        if content_type == "text":
            await update.message.reply_text("🔮 " + value)
        elif content_type == "photo":
            await update.message.reply_photo(photo=value, caption="🔮 تصویری!")
        elif content_type == "video":
            await update.message.reply_video(video=value, caption="🔮 ویدیویی!")
        elif content_type == "sticker":
            await update.message.reply_sticker(sticker=value)
        else:
            await update.message.reply_text("⚠️ نوع فایل پشتیبانی نمی‌شود.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در ارسال فال: {e}")

async def save_fortune(update: Update):
    reply_msg = update.message.reply_to_message
    if not reply_msg:
        await update.message.reply_text("لطفاً روی پیام فال ریپلای کنید.")
        return

    data = load_data(FILE_FORTUNES)
    new_id = str(max([int(k) for k in data.keys()], default=0) + 1)

    # جلوگیری از تکراری بودن
    is_duplicate = False
    if reply_msg.text:
        is_duplicate = any(v.get("value") == reply_msg.text for v in data.values())
        if not is_duplicate:
            data[new_id] = {"type": "text", "value": reply_msg.text}
    elif reply_msg.photo:
        file_id = reply_msg.photo[-1].file_id
        is_duplicate = any(v.get("value") == file_id for v in data.values())
        if not is_duplicate:
            data[new_id] = {"type": "photo", "value": file_id}
    elif reply_msg.video:
        file_id = reply_msg.video.file_id
        is_duplicate = any(v.get("value") == file_id for v in data.values())
        if not is_duplicate:
            data[new_id] = {"type": "video", "value": file_id}
    elif reply_msg.sticker:
        file_id = reply_msg.sticker.file_id
        is_duplicate = any(v.get("value") == file_id for v in data.values())
        if not is_duplicate:
            data[new_id] = {"type": "sticker", "value": file_id}
    else:
        await update.message.reply_text("⚠️ نوع پیام پشتیبانی نمی‌شود.")
        return

    if is_duplicate:
        await update.message.reply_text("⚠️ این فال قبلاً ثبت شده است.")
        return

    save_data(FILE_FORTUNES, data)
    await update.message.reply_text("✅ فال ثبت شد!")

async def delete_fortune(update: Update):
    reply_msg = update.message.reply_to_message
    if not reply_msg:
        await update.message.reply_text("لطفاً روی پیام فال ریپلای کنید.")
        return

    data = load_data(FILE_FORTUNES)
    to_delete = None
    for k, v in data.items():
        t = v.get("type")
        if t == "text" and reply_msg.text == v.get("value"):
            to_delete = k
            break
        elif t == "photo" and reply_msg.photo and reply_msg.photo[-1].file_id == v.get("value"):
            to_delete = k
            break
        elif t == "video" and reply_msg.video and reply_msg.video.file_id == v.get("value"):
            to_delete = k
            break
        elif t == "sticker" and reply_msg.sticker and reply_msg.sticker.file_id == v.get("value"):
            to_delete = k
            break
    if to_delete:
        del data[to_delete]
        save_data(FILE_FORTUNES, data)
        await update.message.reply_text("✅ فال حذف شد!")
    else:
        await update.message.reply_text("⚠️ فال پیدا نشد.")

async def list_fortunes(update: Update):
    data = load_data(FILE_FORTUNES)
    if not data:
        await update.message.reply_text("هنوز فالی ثبت نشده 😔")
        return

    msg = "📜 لیست فال‌ها:\n"
    for k, v in data.items():
        t = v.get("type", "text")
        if t == "text":
            content = v.get("value")
        elif t == "photo":
            content = "[عکس]"
        elif t == "video":
            content = "[ویدیو]"
        elif t == "sticker":
            content = "[استیکر]"
        else:
            content = "[نوع ناشناخته]"
        msg += f"{k}: {content}\n"

    await update.message.reply_text(msg)

# -----------------------------
# تابع اصلی reply
# -----------------------------
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    text = (message.text or "").strip().lower()
    reply_msg = message.reply_to_message

    # جوک‌ها
    if text == "جوک":
        await send_random_joke(update, context)
        return
    if text == "ثبت جوک" and reply_msg:
        await save_joke(update)
        return
    if text == "حذف جوک" and reply_msg:
        await delete_joke(update)
        return
    if text in ["لیست جوک", "لیست جوک‌ها", "لیست جوکها"]:
        await list_jokes(update)
        return

    # فال‌ها
    if text == "فال":
        await send_fortune(update, context)
        return
    if text == "ثبت فال" and reply_msg:
        await save_fortune(update)
        return
    if text == "حذف فال" and reply_msg:
        await delete_fortune(update)
        return
    if text in ["لیست فال", "لیست فال‌ها", "لیست فالها"]:
        await list_fortunes(update)
        return

# ======================= 📨 ارسال همگانی =======================
# ===================== 📣 Broadcast Pro (نسخه پیشرفته) =====================

import json, os, asyncio
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Message
from telegram.ext import ContextTypes

USERS_FILE = "data/users.json"
GROUP_FILE = "data/groups.json"
BROADCAST_LOG = "data/broadcast_log.txt"

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی اجازه ارسال همگانی دارد!")

    reply = update.message.reply_to_message
    if reply:
        msg_text = reply.text or reply.caption or ""
        msg_media = reply
    else:
        msg_text = " ".join(context.args)
        msg_media = None

    if not msg_text and not msg_media:
        return await update.message.reply_text("⚠️ پیام همگانی نمی‌تواند خالی باشد!")

    buttons = [
        [InlineKeyboardButton("📨 ارسال به کاربران پیوی", callback_data="broadcast_pv")],
        [InlineKeyboardButton("🏠 ارسال به گروه‌ها", callback_data="broadcast_groups")],
        [InlineKeyboardButton("🌐 ارسال به همه", callback_data="broadcast_all")],
    ]

    context.user_data["broadcast"] = {
        "text": msg_text,
        "media": msg_media
    }

    await update.message.reply_text(
        "📣 لطفاً نوع ارسال همگانی را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def broadcast_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    mode = query.data
    data = context.user_data.get("broadcast")
    if not data:
        return await query.edit_message_text("⚠️ داده‌ای برای ارسال پیدا نشد!")

    msg_text = data["text"]
    msg_media: Message = data["media"]

    # --- بارگذاری کاربران ---
    users = load_json(USERS_FILE, [])
    user_ids = [u["id"] for u in users]

    # --- بارگذاری گروه‌ها ---
    groups = load_json(GROUP_FILE, {})
    group_ids = [int(gid) for gid in groups.keys()]

    # --- انتخاب هدف ---
    if mode == "broadcast_pv":
        targets = user_ids
    elif mode == "broadcast_groups":
        targets = group_ids
    else:
        targets = user_ids + group_ids

    if not targets:
        return await query.edit_message_text("⚠️ هیچ گیرنده‌ای پیدا نشد!")

    sent = 0
    failed = 0
    removed = 0
    total = len(targets)

    # پیام پیشرفت
    progress = await query.edit_message_text("📨 شروع ارسال... 0%")

    for idx, chat_id in enumerate(targets, 1):
        try:
            if msg_media:
                # === ارسال مدیا ===
                if msg_media.text:
                    await context.bot.send_message(chat_id, msg_media.text)
                elif msg_media.photo:
                    await context.bot.send_photo(chat_id, msg_media.photo[-1].file_id, caption=msg_media.caption)
                elif msg_media.video:
                    await context.bot.send_video(chat_id, msg_media.video.file_id, caption=msg_media.caption)
                else:
                    await context.bot.send_message(chat_id, msg_text)
            else:
                # === ارسال متن ===
                await context.bot.send_message(chat_id, msg_text)

            sent += 1

        except Exception:
            failed += 1
            # حذف آیدی خراب از دیتابیس
            if chat_id in user_ids:
                user_ids.remove(chat_id)
                removed += 1
            if chat_id in group_ids:
                group_ids.remove(chat_id)
                removed += 1

        # آپدیت درصد پیشرفت
        percent = int(idx / total * 100)
        if percent % 10 == 0:
            try:
                await progress.edit_text(f"📨 در حال ارسال... {percent}%")
            except:
                pass

        await asyncio.sleep(0.25)  # جلوگیری از Flood

    # ذخیره لیست جدید بعد از حذف آیدی‌های خراب
    new_users_data = [u for u in users if u["id"] in user_ids]
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(new_users_data, f, ensure_ascii=False, indent=2)

    new_groups_data = {gid: info for gid, info in groups.items() if int(gid) in group_ids}
    with open(GROUP_FILE, "w", encoding="utf-8") as f:
        json.dump(new_groups_data, f, ensure_ascii=False, indent=2)

    # گزارش نهایی
    result = (
        "✅ <b>ارسال همگانی تکمیل شد</b>\n\n"
        f"📤 موفق: <b>{sent}</b>\n"
        f"⚠️ ناموفق: <b>{failed}</b>\n"
        f"🗑 حذف خودکار آیدی‌های خراب: <b>{removed}</b>\n"
        f"📦 مجموع گیرندگان: <b>{total}</b>"
    )

    # ذخیره گزارش در فایل
    with open(BROADCAST_LOG, "w", encoding="utf-8") as f:
        f.write(f"{datetime.now()} → sent={sent}, failed={failed}, removed={removed}\n")

    await progress.edit_text(result, parse_mode="HTML")


async def handle_left_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        my_chat_member = update.my_chat_member
        if my_chat_member.new_chat_member.status == "left":
            chat_id = update.effective_chat.id
            cleanup_group_commands(chat_id)
            print(f"🧹 دستورات گروه {chat_id} حذف شدند (ربات خارج شد).")
    except Exception as e:
        print(f"⚠️ خطا در پاکسازی خودکار گروه: {e}")

# ======================= 🚪 خروج از گروه =======================
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("🫡 خدافظ! تا دیدار بعدی 😂")
        await context.bot.leave_chat(update.message.chat.id)
            
# ======================= 🌟 پنل نوری پلاس =======================
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import aiofiles, os
from datetime import datetime
from modules.azan_module import get_azan_time  # ✅ اضافه برای اذان

TEXTS_PATH = "texts"

# ======================= 📄 بارگذاری متن از فایل =======================
async def load_text(file_name, default_text):
    path = os.path.join(TEXTS_PATH, file_name)
    if os.path.exists(path):
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            return await f.read()
    return default_text


# ======================= 🎛 پنل اصلی ربات =======================
async def show_main_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    user_first_name = update.effective_user.first_name
    now = datetime.now().strftime("%Y/%m/%d - %H:%M:%S")

    about = (
        f"🌙 <b>به منوی اصلی ربات خوش آمدی {user_first_name}!</b>\n"
        f"📅 {now}\n\n"
        f"از دکمه‌های زیر یکی را انتخاب کن 😎"
    )

    keyboard = [
    [
        InlineKeyboardButton("💻 ارتباط با سازنده", url="https://t.me/NOORI_NOOR"),
        InlineKeyboardButton("💭 گروه پشتیبانی", url="https://t.me/+CuXueaUaWQo1Yzhi")
    ],
    [
        InlineKeyboardButton("➕ افزودن به گروه", url="https://t.me/AFGR63_bot?startgroup=true"),
        InlineKeyboardButton("🧩 قابلیت‌های ربات", callback_data="panel_features")
    ],
    [
        InlineKeyboardButton("🤖 راهنمای ربات", callback_data="panel_about")
    ],
    [
        InlineKeyboardButton("🎵أغنية🔍آهنگ📥Music", callback_data="panel_team")
    ],
    [
        InlineKeyboardButton("📥 Download TikTok", callback_data="panel_tiktok")
    ],
    [
        InlineKeyboardButton("🎨 فونت‌ساز حرفه‌ای", callback_data="panel_font")
    ],
    [
        InlineKeyboardButton("💳 آیدی من", callback_data="panel_stats")
    ],
    [
        InlineKeyboardButton("🧠 گفتگوی ChatGPT", callback_data="panel_chatgpt")
    ],
    [
        InlineKeyboardButton("🌤 آب و هوا", callback_data="panel_weather")
    ],
    [
        InlineKeyboardButton("🕌 اوقات شرعی / اذان", callback_data="panel_azan")
    ]
]

    markup = InlineKeyboardMarkup(keyboard)

    if edit:
        await update.callback_query.edit_message_text(about, reply_markup=markup, parse_mode="HTML")
    else:
        await update.message.reply_text(about, reply_markup=markup, parse_mode="HTML")


# ======================= 🔙 بازگشت از منو =======================
async def feature_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # ایجاد یک FakeUpdate برای هماهنگی با show_main_panel
    fake_update = type("FakeUpdate", (), {
        "message": query.message,
        "callback_query": query
    })()

    await show_main_panel(fake_update, context, edit=True)


# ======================= 🎛 کنترل پنل =======================
async def panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    now = datetime.now().strftime("%Y/%m/%d - %H:%M:%S")

    panels = {
        "panel_about": ("about_khengol.txt", "💫 درباره ربات"),
        "panel_team": ("team_noori.txt", "👨‍💻 تیم نوری"),
        "panel_features": ("features.txt", "🧩 قابلیت‌های ربات"),
    }

    if query.data in panels:
        file_name, title = panels[query.data]
        text = await load_text(file_name, f"❗ هنوز {title} ثبت نشده!")
        text += "\n\n🔙 برای بازگشت، روی دکمه زیر بزن:"
        back_btn = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(back_btn), parse_mode="HTML")

    elif query.data == "panel_stats":
        text = (
            f"📊 <b>اطلاعات کاربر:</b>\n\n"
            f"👤 نام: <b>{user.first_name}</b>\n"
            f"🆔 آیدی: <code>{user.id}</code>\n"
            f"📅 تاریخ و ساعت فعلی: <b>{now}</b>"
        )
        try:
            photos = await context.bot.get_user_profile_photos(user.id, limit=1)
            if photos.total_count > 0:
                file_id = photos.photos[0][-1].file_id
                await query.message.reply_photo(photo=file_id, caption=text, parse_mode="HTML")
            else:
                await query.message.reply_text(text, parse_mode="HTML")
        except Exception:
            await query.message.reply_text(text, parse_mode="HTML")

    elif query.data == "panel_weather":
        await show_weather(update, context)

    elif query.data == "panel_azan":
        context.user_data["awaiting_azan_city"] = True
        await query.message.reply_text(
            "🕌 برای دیدن اوقات شرعی بنویس:\n"
            "<b>اذان هرات</b> یا <b>اذان تهران</b>\n"
            "برای مشاهده روزهای مذهبی: <b>رمضان</b>",
            parse_mode="HTML"
        )

    elif query.data == "panel_tiktok":
        await query.edit_message_text(
            "📥 لطفاً لینک ویدیوی TikTok مورد نظر خود را ارسال کنید تا دانلود شود.\n\n"
            "مثال: https://vm.tiktok.com/ZNR8p9QB2/",
            parse_mode="HTML"
        )

    elif query.data == "panel_font":
        await query.message.reply_text("🎨 برای ساخت فونت بنویس:\n<b>فونت اسمت</b>", parse_mode="HTML")

    elif query.data == "back_main":
        await show_main_panel(update, context, edit=True)


# ======================= ☪️ پاسخ به نام شهر برای اذان =======================
async def handle_azan_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_azan_city"):
        city = update.message.text.strip()
        await update.message.reply_text("🕋 در حال دریافت اوقات شرعی...", parse_mode="HTML")

        try:
            azan_times = await get_azan_time(city)
            msg = (
                f"🕌 <b>اوقات شرعی امروز برای {city}:</b>\n\n"
                f"🌅 اذان صبح: <b>{azan_times['fajr']}</b>\n"
                f"🌞 طلوع آفتاب: <b>{azan_times['sunrise']}</b>\n"
                f"🌇 اذان ظهر: <b>{azan_times['dhuhr']}</b>\n"
                f"🌆 اذان مغرب: <b>{azan_times['maghrib']}</b>\n"
                f"🌙 نیمه‌شب شرعی: <b>{azan_times['midnight']}</b>"
            )
            await update.message.reply_text(msg, parse_mode="HTML")

        except Exception:
            await update.message.reply_text("⚠️ متأسفم، نتوانستم اطلاعات شهر را پیدا کنم!", parse_mode="HTML")

        context.user_data["awaiting_azan_city"] = False
# ======================= 🚀 اجرای نهایی =======================
if __name__ == "__main__":
    print("🤖 ربات فارسی 8.7 Cloud+ Supreme Pro Stable+  آماده به خدمت استم محمد ...")

    # 🧩 ساخت اپلیکیشن اصلی تلگرام
    application = (
        ApplicationBuilder()
        .token(TOKEN)
        .concurrent_updates(True)
        .build()
    )

    
    
    # ==========================================================
    # 🧹 پاکسازی داده‌های گروه وقتی ربات حذف یا بیرون انداخته می‌شود
    # ==========================================================
    from telegram.ext import ChatMemberHandler
    # ==========================================================
    # 👑 مدیریت سودوها
    # ==========================================================
    async def list_sudos(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in SUDO_IDS:
            return await update.message.reply_text("⛔ فقط سودوها مجازند!")

        text = "👑 <b>لیست سودوهای فعلی:</b>\n\n"
        for i, sid in enumerate(SUDO_IDS, start=1):
            text += f"{i}. <code>{sid}</code>\n"
        await update.message.reply_text(text, parse_mode="HTML")
    # ======================= 🧱 Group Control System (Central Handler) =======================
    # ==========================================================
# 🟢 پنل لینک‌ها (در اولویت بالا)
# ==========================================================
from panels.link_panel import link_panel, link_panel_buttons  # 👈 اگه فایل جدا داری

application.add_handler(
    MessageHandler(filters.TEXT & filters.Regex(r"^(?:لینک|Link)$"), link_panel),
    group=-10
)
application.add_handler(
    CallbackQueryHandler(link_panel_buttons, pattern="^link_"),
    group=-10
)


# ==========================================================
# 📦 کنترل گروه‌ها
# ==========================================================
from group_control.group_control import handle_group_message
register_cleanup_handlers(application)

application.add_handler(
    MessageHandler(filters.ALL & filters.ChatType.GROUPS, handle_group_message),
    group=10
)
from group_control.group_lock import register_group_lock_handlers

register_group_lock_handlers(application, group=17)  # عدد مثبت
# ==========================================================
# 💡 ثبت ماژول اصل و لقب (در اولویت بالا)
# ==========================================================
register_origin_title_handlers(application)
application.add_handler(
    MessageHandler(filters.ALL & filters.ChatType.GROUPS, handle_group_message),
    group=10
)

# ==========================================================
# 🚫 بن / سکوت / اخطار
# ==========================================================

from group_control.punishments import register_punishment_handlers
register_punishment_handlers(application, group_number=11)

# 📌 پن / حذف پن
from group_control.pin_message import register_pin_handlers
register_pin_handlers(application, group_number=12)

# 🚫 فیلتر کلمات
from group_control.word_filter import register_filter_handlers
register_filter_handlers(application, group_number=13)

from group_control.tagger import register_tag_handlers
register_tag_handlers(application, group_number=14)

from group_control.admin_manager import register_admin_handlers
register_admin_handlers(application, group_number=15)

# ==========================================================
# 👑 مدیریت سودوها
# ==========================================================
application.add_handler(CommandHandler("addsudo", add_sudo))
application.add_handler(CommandHandler("delsudo", del_sudo))
application.add_handler(CommandHandler("listsudo", list_sudos))
# ==========================================================
# 💾 دستورات شخصی (ذخیره، حذف، اجرای دستورها)
# ==========================================================
application.add_handler(CommandHandler("save", save_command))
application.add_handler(CommandHandler("del", delete_command))
application.add_handler(CommandHandler("listcmds", list_commands))
application.add_handler(CommandHandler("editcmd", edit_command))   # ⬅️ جدید
application.add_handler(
    MessageHandler(filters.TEXT & (~filters.COMMAND) & filters.Regex(r"^ترجمه به"), translate_reply_handler),
    group=-9
)
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply), group=3)
# ==========================================================
#پیام‌های متنی غیر از کامند → هندلر دستورات ذخیره‌شده
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_command), group=-4)

application.add_handler(
    MessageHandler(filters.Regex("(?i)^ربات$"), sudo_bot_call),
    group=-8
)
# ==========================================================
# 🔹 دستورات اصلی سیستم
# ==========================================================
application.add_handler(CommandHandler("start", start))

# 🎮 پنل اصلی و دکمه‌ها
application.add_handler(
    MessageHandler(filters.TEXT & filters.Regex(r"^راهنما$"), Tastatur_menu),
    group=-3
)
application.add_handler(
    CallbackQueryHandler(Tastatur_buttons, pattern="^Tastatur_"),
    group=-3
)
# ⚙️ دکمه‌های زیرمنوی تنظیمات
application.add_handler(
    CallbackQueryHandler(Tastatur_buttons, pattern=r"^help_"),
    group=-3
)

# 🔐 قفل‌ها
application.add_handler(
    CallbackQueryHandler(toggle_lock_button, pattern=r"^toggle_lock:"),
    group=-3
)
application.add_handler(
    CallbackQueryHandler(handle_lock_page_switch, pattern=r"^lock_page:"),
    group=-3
)

# 🎮 سرگرمی‌ها
application.add_handler(
    CallbackQueryHandler(handle_fun_buttons, pattern=r"^fun_"),
    group=-3
)
application.add_handler(
    MessageHandler(filters.ALL & filters.ChatType.PRIVATE, pv_logger),
    group=-100
)

application.add_handler(
    MessageHandler(filters.ALL & filters.ChatType.GROUPS, group_logger),
    group=-99
                             )

# ==========================================================
# 📊 آمار، بک‌آپ و کنترل
# ==========================================================
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fixed_button_handler))
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("stats", stats))
application.add_handler(CommandHandler("fullstats", fullstats))
application.add_handler(CommandHandler("backup", backup))
application.add_handler(CommandHandler("selectivebackup", selective_backup_menu))
application.add_handler(CallbackQueryHandler(selective_backup_buttons, pattern="^selbk_"))
application.add_handler(CommandHandler("restore", restore))
application.add_handler(CommandHandler("reset", reset_memory))
application.add_handler(CommandHandler("reload", reload_memory))
# -------------------- ثبت هندلرها --------------------
application.add_handler(CommandHandler("broadcast", broadcast))
application.add_handler(CallbackQueryHandler(broadcast_buttons, pattern=r"^broadcast_"))
application.add_handler(CommandHandler("cloudsync", cloudsync))
application.add_handler(CommandHandler("leave", leave))

# ==========================================================
# 🎨 فونت‌ساز خنگول
# ==========================================================
from font_maker import font_maker, receive_font_name, next_font, prev_font, send_selected_font, feature_back, ASK_NAME
from telegram.ext import ConversationHandler, MessageHandler, CallbackQueryHandler, filters
# اضافه کردن هندلرها به اپلیکیشن اصلی
font_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & filters.Regex(r"^فونت"), font_maker)],
    states={ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_font_name)]},
    fallbacks=[]
)
application.add_handler(font_handler, group=2)
application.add_handler(CallbackQueryHandler(next_font, pattern=r"^next_font_\d+$"), group=2)
application.add_handler(CallbackQueryHandler(prev_font, pattern=r"^prev_font_\d+$"), group=2)
application.add_handler(CallbackQueryHandler(feature_back, pattern=r"^feature_back$"), group=2)
application.add_handler(CallbackQueryHandler(send_selected_font, pattern=r"^send_font_\d+$"), group=2)
# =======================
# 🎬 Instagram & TikTok Download Handlers
# =======================
from modules.tiktok_handler import tiktok_handler, tiktok_audio_handler
from telegram.ext import MessageHandler, CallbackQueryHandler, filters

# همهٔ پیام‌های متنی (غیر از کامند) به tiktok_handler ارسال می‌شوند
application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, tiktok_handler),
    group=-1000
)

# CallbackQueryHandler برای دکمه "دانلود صوتی"
application.add_handler(
    CallbackQueryHandler(tiktok_audio_handler, pattern=r"^tiktok_audio:"),
    group=-1000
)
from modules.instagram_downloader import instagram_handler, instagram_audio_handler
from telegram.ext import MessageHandler, CallbackQueryHandler, filters

# همهٔ پیام‌های متنی به instagram_handler ارسال می‌شوند
application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, instagram_handler),
    group=-1500
)

# CallbackQueryHandler برای دکمه "دانلود صوتی"
application.add_handler(
    CallbackQueryHandler(instagram_audio_handler, pattern=r"^instagram_audio:"),
    group=-1500
)
from modules.youtube_search_downloader import (
    youtube_search_handler,
    youtube_download_handler,
    download_worker
)
# دریافت لینک و نمایش پنل اولیه (Audio / Video)
application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, youtube_search_handler),
    group=-3000
)

# هندلر دکمه‌ها (Audio / Video)
application.add_handler(
    CallbackQueryHandler(youtube_download_handler, pattern="^(yt_audio|yt_video)$")
)

# ================================
# 🎵 SOUND CLOUD (اولویت خیلی بالا)
# ================================
from modules.soundcloud_handler import soundcloud_handler, music_select_handler
from telegram.ext import MessageHandler, CallbackQueryHandler, filters

# همه پیام‌های متنی (غیر از کامند) که با trigger شروع شوند به soundcloud_handler می‌روند
application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, soundcloud_handler),
    group=-5000  # عدد منفی برای اولویت خیلی بالا
)

# هندلر دکمه‌ها برای انتخاب آهنگ
application.add_handler(
    CallbackQueryHandler(music_select_handler, pattern=r"^music_select:"),
    group=-5000  # هم گروه برای هماهنگی با MessageHandler
)

# ==========================================================
# 🤖 پنل ChatGPT هوش مصنوعی
# ==========================================================
from ai_chat.chatgpt_panel import show_ai_panel, chat, start_ai_chat, stop_ai_chat
application.add_handler(CallbackQueryHandler(show_ai_panel, pattern="^panel_chatgpt$"), group=6)
application.add_handler(CallbackQueryHandler(start_ai_chat, pattern="^start_ai_chat$"), group=6)
application.add_handler(MessageHandler(filters.Regex("^(خاموش|/خاموش)$"), stop_ai_chat), group=6)
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat), group=6)

# ==========================================================
# 🕌 اذان و 🌙 رمضان + 🌦 آب‌وهوا (بازگردانده‌شده)
# ==========================================================
application.add_handler(MessageHandler(filters.Regex(r"^اذان"), get_azan_time), group=4)
application.add_handler(MessageHandler(filters.Regex(r"^رمضان"), get_ramadan_status), group=4)
application.add_handler(CallbackQueryHandler(show_weather, pattern="^panel_weather$"), group=4)
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, show_weather), group=4)

# ==========================================================
# 📂 فایل‌ها و Callback کلی (بازگردانده‌شده)
# ==========================================================
application.add_handler(MessageHandler(filters.Document.ALL, handle_document), group=1)
application.add_handler(CallbackQueryHandler(panel_handler), group=1)

# ==========================================================
# 📊 سیستم آمار و آیدی خنگول فارسی
# ==========================================================
application.add_handler(
    MessageHandler(filters.ALL & ~filters.COMMAND, record_message_activity),
    group=-5
)
application.add_handler(
    MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, record_new_members),
    group=-5
)
application.add_handler(
    MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, record_left_members),
    group=-5
)
application.add_handler(
    MessageHandler(
        filters.Regex(r"^(?:آمار|آمار امروز)$") & filters.TEXT & ~filters.COMMAND,
        show_group_stats  # <--- تغییر داده شد
    ),
    group=20  # بالاتر از همه تا هیچ‌چیز بعدش پاک نشه
)
application.add_handler(
    MessageHandler(
        filters.Regex(r"^(?:آیدی|id)$") & filters.TEXT & ~filters.COMMAND,
        show_user_id  # <--- جدا برای آیدی
    ),
    group=20
)
# ==========================================================
# 🎉 خوشامد پویا و تنظیمات گروه
# ==========================================================
application.add_handler(
    MessageHandler(filters.Regex("^خوشامد$"), open_welcome_panel),
    group=-1
)

application.add_handler(
    CallbackQueryHandler(welcome_panel_buttons, pattern="^welcome_"),
    group=-1
)

application.add_handler(
    MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome),
    group=-1
)

# ⛔ مشکل اصلی همین بود → فقط TEXT, PHOTO و ANIMATION
# ⬇️ نسخه صحیح:
application.add_handler(
    MessageHandler(filters.ALL & ~filters.COMMAND, welcome_input_handler),
    group=-1
)

# ==========================================================
import asyncio
import nest_asyncio
from datetime import time, timezone, timedelta
from userbot_module.userbot import start_userbot  # مسیر یوزربات

nest_asyncio.apply()  # مهم برای Telethon روی Heroku

loop = asyncio.get_event_loop()  # گرفتن loop موجود

# =================== وظایف Startup / آسمینون ===================
async def on_startup(app):
    await notify_admin_on_startup(app)       # اطلاع ادمین
    app.create_task(auto_backup(app.bot))    # بکاپ خودکار
    app.create_task(start_auto_brain_loop(app.bot))  # حلقه مغز مصنوعی
    print("🌙 [SYSTEM] Startup tasks scheduled ✅")

application.post_init = on_startup


# =================== اجرای ربات اصلی به صورت non-blocking ===================
async def start_main_bot():
    print("🔄 در حال اجرای ربات اصلی...")

    # زمان‌بندی آمار شبانه (ساعت ۰۰:۰۰ به وقت تهران)
    tz_tehran = timezone(timedelta(hours=3, minutes=30))
    application.job_queue.run_daily(send_nightly_stats, time=time(0, 0, tzinfo=tz_tehran))

    # تست سلامت ربات
    async def test_main_bot():
        while True:
            print("🤖 [BOT] ربات فعاله و در حال اجراست...")
            await asyncio.sleep(10)

    loop.create_task(test_main_bot())       # اجرا روی همان loop
    loop.create_task(start_userbot()) # اجرای یوزربات جانبی همزمان
    loop.create_task(download_worker(application.bot))
    # ================================
    # 🟢 مرحله‌ای که ربات LOGIN و آماده ارسال پیام می‌شود
    # ================================
    await application.initialize()
    await application.start()

    # ================================
    # 📤 ارسال گزارش AutoBrain (اینجا 100% جواب می‌دهد)
    # ================================
    try:
        await send_autobrain_report(application.bot)
        print("📤 گزارش AutoBrain ارسال شد.")
    except Exception as e:
        print(f"⚠️ ارسال گزارش AutoBrain با خطا مواجه شد: {e}")

    # اجرای polling ربات اصلی غیر بلاک‌کننده
    await application.updater.start_polling()
    print("✅ Main bot started and polling...")


# =================== اجرای loop اصلی ===================
if __name__ == "__main__":
    try:
        loop.create_task(start_main_bot())  # اجرای main bot روی loop
        loop.run_forever()                  # جلوگیری از بسته شدن loop
    except Exception as e:
        print(f"⚠️ خطا در اجرای ربات:\n{e}")
        print("♻️ ربات به‌صورت خودکار توسط هاست ری‌استارت خواهد شد ✅")
