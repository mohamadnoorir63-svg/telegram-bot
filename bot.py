import asyncio
import os
import random
import zipfile
import shutil
import base64
import io
from datetime import datetime
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
import aiofiles
import qrcode
from PIL import Image, ImageDraw, ImageFont

# 📦 ماژول‌های جانبی
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

# 🎯 تنظیمات اصلی
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))

# 📂 مقداردهی فایل‌های پایه
init_files()

status = {
    "active": True,
    "learning": True,
    "welcome": True,
    "locked": False
}
# ======================= 💬 ریپلی مود گروهی =======================
import json

REPLY_FILE = "reply_status.json"

def load_reply_status():
    """خواندن وضعیت ریپلی مود گروه‌ها"""
    if os.path.exists(REPLY_FILE):
        try:
            with open(REPLY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_reply_status(data):
    """ذخیره وضعیت ریپلی مود"""
    with open(REPLY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

reply_status = load_reply_status()

def is_group_reply_enabled(chat_id):
    return reply_status.get(str(chat_id), {}).get("enabled", False)

async def toggle_reply_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فعال/غیرفعال کردن ریپلی مود توسط مدیر"""
    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text("⚠️ فقط در گروه قابل اجراست!")

    is_main_admin = (user.id == ADMIN_ID)
    is_group_admin = False

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status in ["creator", "administrator"]:
            is_group_admin = True
    except:
        pass

    if not (is_main_admin or is_group_admin):
        return await update.message.reply_text("⛔ فقط مدیران مجازند!")

    group_id = str(chat.id)
    current = reply_status.get(group_id, {}).get("enabled", False)
    reply_status[group_id] = {"enabled": not current}
    save_reply_status(reply_status)

    if reply_status[group_id]["enabled"]:
        await update.message.reply_text("💬 ریپلی مود فعال شد! فقط روی پیام‌های من ریپلای کنید 😄")
    else:
        await update.message.reply_text("🗨️ ریپلی مود غیرفعال شد! الان به همه پیام‌ها جواب می‌دهم 😎")

async def handle_group_reply_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """در حالت ریپلی مود فقط اگر ریپلای باشد پاسخ بده"""
    if update.effective_chat.type in ["group", "supergroup"]:
        chat_id = update.effective_chat.id
        if is_group_reply_enabled(chat_id):
            if not update.message.reply_to_message or update.message.reply_to_message.from_user.id != context.bot.id:
                return True
    return False

# ======================= 🧾 ثبت کاربران =======================
USERS_FILE = "users.json"

async def register_user(user):
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
# ======================= ✳️ شروع و راهنما =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 خنگول فارسی 8.7 Cloud+ Supreme Pro Stable+\n"
        "📘 برای دیدن لیست دستورات بنویس: راهنما"
    )

async def notify_admin_on_startup(app):
    try:
        await app.bot.send_message(
            chat_id=ADMIN_ID,
            text="🚀 ربات خنگول با موفقیت فعال شد ✅"
        )
        print("[INFO] Startup notification sent ✅")
    except Exception as e:
        print(f"[ERROR] Admin notify failed: {e}")

# ======================= ⚙️ خطایاب =======================
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
    if not os.path.exists(HELP_FILE):
        return await update.message.reply_text(
            "ℹ️ هنوز متنی برای راهنما ثبت نشده.\nمدیر اصلی می‌تونه با «ثبت راهنما» تنظیم کنه."
        )
    async with aiofiles.open(HELP_FILE, "r", encoding="utf-8") as f:
        text = await f.read()
    await update.message.reply_text(text)

async def save_custom_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه تنظیم کنه!")

    if not update.message.reply_to_message or not update.message.reply_to_message.text:
        return await update.message.reply_text("❗ باید روی پیام متنی ریپلای کنی!")

    text = update.message.reply_to_message.text
    async with aiofiles.open(HELP_FILE, "w", encoding="utf-8") as f:
        await f.write(text)
    await update.message.reply_text("✅ متن راهنما ذخیره شد!")

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
# ======================= 👋 سیستم خوشامد پویا =======================
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import json, asyncio

WELCOME_FILE = "welcome_settings.json"

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
        return await update.message.reply_text("⛔ فقط مدیران مجازند!")

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

# ✅ مدیریت دکمه‌ها
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
        msg = "✅ خوشامد فعال شد!"
    elif data == "welcome_disable":
        welcome_settings[chat_id]["enabled"] = False
        msg = "🚫 خوشامد غیرفعال شد!"
    elif data == "welcome_setmedia":
        msg = "🖼 روی عکس ریپلای کن و بنویس: ثبت عکس خوشامد"
    elif data == "welcome_settext":
        msg = "📜 روی پیام متنی ریپلای کن و بنویس: ثبت خوشامد"
    elif data == "welcome_setrules":
        msg = "📎 لینک قوانین گروه را بفرست، مثل:\nتنظیم قوانین https://t.me/example"
    elif data == "welcome_setdelete":
        msg = "⏳ زمان حذف خودکار خوشامد را بنویس (ثانیه)"

    save_welcome_settings(welcome_settings)
    await query.message.reply_text(msg, parse_mode="HTML")

# ✅ ثبت متن خوشامد
async def set_welcome_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = update.effective_user
    member = await context.bot.get_chat_member(chat_id, user.id)

    if member.status not in ["administrator", "creator"] and user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیران مجازند!")

    if not update.message.reply_to_message or not update.message.reply_to_message.text:
        return await update.message.reply_text("❗ باید روی پیام متنی ریپلای بزنی!")

    text = update.message.reply_to_message.text
    welcome_settings.setdefault(chat_id, {})["text"] = text
    save_welcome_settings(welcome_settings)
    await update.message.reply_text("✅ متن خوشامد ذخیره شد!")

# ✅ ثبت عکس خوشامد
async def set_welcome_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = update.effective_user
    member = await context.bot.get_chat_member(chat_id, user.id)

    if member.status not in ["administrator", "creator"] and user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیران مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("❗ باید روی عکس ریپلای بزنی!")

    file = update.message.reply_to_message
    if file.photo:
        file_id = file.photo[-1].file_id
    elif file.animation:
        file_id = file.animation.file_id
    else:
        return await update.message.reply_text("⚠️ فقط عکس یا گیف قابل قبول است!")

    welcome_settings.setdefault(chat_id, {})["media"] = file_id
    save_welcome_settings(welcome_settings)
    await update.message.reply_text("✅ عکس خوشامد ذخیره شد!")

# ✅ تنظیم لینک قوانین
async def set_rules_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    text = update.message.text.strip().split(maxsplit=2)
    if len(text) < 3:
        return await update.message.reply_text("📎 مثال: تنظیم قوانین https://t.me/example")

    link = text[2]
    welcome_settings.setdefault(chat_id, {})["rules"] = link
    save_welcome_settings(welcome_settings)
    await update.message.reply_text(f"✅ لینک قوانین ذخیره شد:\n{link}")

# ✅ تنظیم زمان حذف خودکار
async def set_welcome_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    text = update.message.text.strip().split()
    if len(text) < 3:
        return await update.message.reply_text("⚙️ مثال: تنظیم حذف 60 (ثانیه)")

    try:
        seconds = int(text[2])
        if not 10 <= seconds <= 86400:
            return await update.message.reply_text("⏳ عدد باید بین 10 تا 86400 باشد!")
    except:
        return await update.message.reply_text("⚠️ عدد معتبر نیست!")

    welcome_settings.setdefault(chat_id, {})["delete_after"] = seconds
    save_welcome_settings(welcome_settings)
    await update.message.reply_text(f"✅ حذف خودکار پس از {seconds} ثانیه تنظیم شد!")

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
        now = datetime.now().strftime("%Y/%m/%d ⏰ %H:%M")
        msg_text = (
            f"🌙 <b>سلام {member.first_name}!</b>\n"
            f"📅 تاریخ: <b>{now}</b>\n🏠 گروه: <b>{update.effective_chat.title}</b>\n\n{text}"
        )
        if rules:
            msg_text += f"\n\n📜 <a href='{rules}'>قوانین گروه</a>"

        try:
            if media:
                msg = await update.message.reply_photo(media, caption=msg_text, parse_mode="HTML")
            else:
                msg = await update.message.reply_text(msg_text, parse_mode="HTML")
            if delete_after > 0:
                await asyncio.sleep(delete_after)
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
        except Exception as e:
            print(f"[WELCOME ERROR] {e}")
# ======================= ☁️ NOORI Secure QR Backup v11.1 =======================
import io, shutil, base64, qrcode
from PIL import Image, ImageDraw, ImageFont

BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

IMPORTANT_FILES = [
    "memory.json", "group_data.json", "jokes.json",
    "fortunes.json", "warnings.json", "aliases.json"
]

def _should_include_in_backup(path: str) -> bool:
    skip_dirs = ["pycache", ".git", "venv", "restore_temp", "backups"]
    lowered = path.lower()
    if any(sd in lowered for sd in skip_dirs): return False
    if lowered.endswith(".zip"): return False
    return lowered.endswith((".json", ".jpg", ".png", ".webp", ".mp3", ".ogg"))

def create_zip_backup():
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"backup_{now}.zip"
    zip_path = os.path.join(BACKUP_DIR, filename)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk("."):
            for file in files:
                full_path = os.path.join(root, file)
                if _should_include_in_backup(full_path):
                    arcname = os.path.relpath(full_path, ".")
                    zipf.write(full_path, arcname=arcname)
    return zip_path, now

def generate_qr_image(text, timestamp):
    qr = qrcode.QRCode(version=2, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#0044cc", back_color="white").convert("RGB")

    shield = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shield)
    draw.ellipse((0, 0, 120, 120), fill="#0044cc")
    draw.polygon([(60, 20), (100, 50), (85, 95), (35, 95), (20, 50)], fill="white")
    qr_w, qr_h = qr_img.size
    shield = shield.resize((qr_w // 3, qr_h // 3))
    qr_img.paste(shield, ((qr_w - shield.size[0]) // 2, (qr_h - shield.size[1]) // 2), mask=shield)

    canvas = Image.new("RGB", (qr_w, qr_h + 80), "white")
    canvas.paste(qr_img, (0, 0))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("arial.ttf", 26)
    except:
        font = ImageFont.load_default()
    label = f"Backup @NOORI — {timestamp}"
    w, h = draw.textsize(label, font=font)
    draw.text(((qr_w - w) // 2, qr_h + 20), label, fill="#0044cc", font=font)

    output = io.BytesIO()
    canvas.save(output, format="PNG")
    output.seek(0)
    return output

# 💾 بک‌آپ دستی
async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    zip_path, timestamp = create_zip_backup()
    with open(zip_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")[:1500]
    qr_img = generate_qr_image(encoded, timestamp)

    await update.message.reply_photo(photo=qr_img, caption=f"☁️ بک‌آپ ساخته شد ✅\n🕓 {timestamp}")
    await update.message.reply_document(InputFile(zip_path))
    os.remove(zip_path)

# ☁️ بک‌آپ ابری
async def cloudsync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    zip_path, timestamp = create_zip_backup()
    with open(zip_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")[:1500]
    qr_img = generate_qr_image(encoded, timestamp)

    await context.bot.send_photo(chat_id=ADMIN_ID, photo=qr_img, caption=f"☁️ Cloud Backup — {timestamp}")
    await context.bot.send_document(chat_id=ADMIN_ID, document=InputFile(zip_path))
    os.remove(zip_path)

# ♻️ بازیابی با نوار درصد
async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه بازیابی کنه!")
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        return await update.message.reply_text("📎 فایل ZIP بک‌آپ را ریپلای کن و بعد دستور /restore بزن.")

    file = await update.message.reply_to_message.document.get_file()
    path = os.path.join(BACKUP_DIR, "restore_temp.zip")
    await file.download_to_drive(path)

    msg = await update.message.reply_text("♻️ شروع بازیابی...\n0% [▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒]")
    restore_dir = "restore_temp"
    if os.path.exists(restore_dir):
        shutil.rmtree(restore_dir)
    os.makedirs(restore_dir, exist_ok=True)

    with zipfile.ZipFile(path, "r") as zip_ref:
        files = zip_ref.namelist()
        total = len(files)
        done = 0
        for file in files:
            zip_ref.extract(file, restore_dir)
            done += 1
            percent = int(done / total * 100)
            bars = int(percent / 5)
            progress_bar = "█" * bars + "▒" * (20 - bars)
            await msg.edit_text(f"♻️ بازیابی {percent}% [{progress_bar}]")
            await asyncio.sleep(0.2)

    moved = 0
    for f in IMPORTANT_FILES:
        src = os.path.join(restore_dir, f)
        if os.path.exists(src):
            shutil.move(src, f)
            moved += 1

    shutil.rmtree(restore_dir)
    os.remove(path)
    await msg.edit_text(f"✅ بازیابی کامل شد!\n📦 {moved} فایل بازگردانی گردید.\n🤖 سیستم آماده است.")

# 🕓 بک‌آپ خودکار هر ۶ ساعت
async def auto_backup(bot):
    while True:
        try:
            zip_path, timestamp = create_zip_backup()
            with open(zip_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")[:1500]
            qr_img = generate_qr_image(encoded, timestamp)
            await bot.send_photo(chat_id=ADMIN_ID, photo=qr_img, caption=f"🤖 Auto Backup — {timestamp}")
            await bot.send_document(chat_id=ADMIN_ID, document=InputFile(zip_path))
            print(f"[AUTO BACKUP] {timestamp} sent ✅")
            os.remove(zip_path)
        except Exception as e:
            print(f"[AUTO BACKUP ERROR] {e}")
        await asyncio.sleep(21600)
# ======================= 💬 پاسخ و هوش مصنوعی =======================
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    uid = update.effective_user.id
    chat_id = update.effective_chat.id

    # 🧠 بررسی ریپلی مود گروهی
    if await handle_group_reply_mode(update, context):
        return

    # ثبت کاربر و گروه
    await register_user(update.effective_user)
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
                details.append("⚪ حافظه در حال یادگیری است")

        if os.path.exists("jokes.json"):
            data = load_data("jokes.json")
            count = len(data)
            if count > 10:
                score += 15
                details.append("😂 جوک‌های زیاد 😎")
            elif count > 0:
                score += 10
                details.append("😅 چند جوک موجود است")

        if os.path.exists("fortunes.json"):
            data = load_data("fortunes.json")
            count = len(data)
            if count > 10:
                score += 15
                details.append("🔮 فال‌ها متنوع 💫")
            elif count > 0:
                score += 10
                details.append("🔮 چند فال موجود است")

        try:
            test = smart_response("سلام", "شاد")
            if test:
                score += 25
                details.append("💬 پاسخ هوشمند فعال 🤖")
        except:
            details.append("⚠️ خطا در smart_response")

        if score > 100: score = 100
        result = (
            f"🤖 درصد هوش خنگول: *{score}%*\n\n" +
            "\n".join(details) +
            f"\n\n🕓 {datetime.now().strftime('%Y/%m/%d %H:%M')}"
        )
        await update.message.reply_text(result, parse_mode="Markdown")
        return

    # ✅ درصد هوش اجتماعی
    if text.lower() == "درصد هوش اجتماعی":
        score = 0
        details = []
        memory = load_data("memory.json")
        users = len(memory.get("users", []))
        groups = load_data("group_data.json").get("groups", {})
        gcount = len(groups) if isinstance(groups, dict) else len(groups)

        if users > 50: score += 25; details.append("👥 کاربران زیاد و فعال ✅")
        elif users > 10: score += 15; details.append("🟢 کاربران متوسط")
        else: details.append("⚪ کاربران کم")

        if gcount > 10: score += 25; details.append("🏠 گروه‌های زیاد ✅")
        elif gcount > 3: score += 15; details.append("🏠 گروه‌های متوسط")
        else: details.append("⚪ گروه کم")

        try:
            activity = get_group_stats()
            total = activity.get("messages", 0)
            if total > 200: score += 25; details.append("💬 تعامل زیاد 😎")
            elif total > 50: score += 15; details.append("💬 تعامل متوسط")
        except:
            details.append("⚠️ آمار تعاملات نامشخص")

        result = (
            f"🧠 هوش اجتماعی: *{score}%*\n\n" +
            "\n".join(details) +
            f"\n\n🕓 {datetime.now().strftime('%Y/%m/%d %H:%M')}"
        )
        await update.message.reply_text(result, parse_mode="Markdown")
        return

    # ✅ هوش کلی
    if text.lower() == "هوش کلی":
        score = 0
        details = []

        if os.path.exists("memory.json"):
            data = load_data("memory.json")
            p = len(data.get("phrases", {}))
            r = sum(len(v) for v in data.get("phrases", {}).values()) if p else 0
            if p > 20 and r > 30:
                score += 25
                details.append("🧠 یادگیری گسترده ✅")
            elif p > 10:
                score += 15
                details.append("🧩 یادگیری متوسط")

        if os.path.exists("jokes.json"):
            c = len(load_data("jokes.json"))
            if c > 10: score += 10; details.append("😂 شوخ‌طبع 😄")
            elif c > 0: score += 5; details.append("😅 چند جوک دارد")

        try:
            if smart_response("سلام", "شاد"):
                score += 20
                details.append("💬 پاسخ هوشمند فعال 🤖")
        except:
            details.append("⚠️ خطا در پاسخ")

        users = len(load_data("memory.json").get("users", []))
        if users > 20: score += 10; details.append(f"👥 کاربران زیاد ({users})")

        iq = min(160, int((score / 100) * 160))
        if iq >= 130: level = "🌟 نابغه دیجیتال"
        elif iq >= 110: level = "🧠 تحلیل‌گر"
        elif iq >= 90: level = "🙂 یادگیرنده"
        else: level = "🤪 خنگول کلاسیک 😅"

        await update.message.reply_text(
            f"🤖 IQ کلی خنگول: *{iq}*\n{level}\n\n" +
            "\n".join(details) +
            f"\n\n📈 نسخه Cloud+ Supreme Pro\n🕓 {datetime.now().strftime('%Y/%m/%d %H:%M')}",
            parse_mode="Markdown"
        )
        return

    # ✅ جوک تصادفی
    if text == "جوک":
        if os.path.exists("jokes.json"):
            data = load_data("jokes.json")
            if data:
                key, val = random.choice(list(data.items()))
                t, v = val.get("type", "text"), val.get("value", "")
                try:
                    if t == "text":
                        await update.message.reply_text("😂 " + v)
                    elif t == "photo":
                        await update.message.reply_photo(photo=v, caption="😂 جوک تصویری!")
                    elif t == "video":
                        await update.message.reply_video(video=v, caption="😂 جوک ویدیویی!")
                except Exception as e:
                    await update.message.reply_text(f"⚠️ خطا در ارسال جوک: {e}")
            else:
                await update.message.reply_text("😅 هنوز جوکی نیست.")
        return

    # ✅ فال تصادفی
    if text == "فال":
        if os.path.exists("fortunes.json"):
            data = load_data("fortunes.json")
            if data:
                k, v = random.choice(list(data.items()))
                t, val = v.get("type", "text"), v.get("value", "")
                if t == "text":
                    await update.message.reply_text("🔮 " + val)
                elif t == "photo":
                    await update.message.reply_photo(photo=val, caption="🔮 فال تصویری!")
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

    # ✅ جمله تصادفی
    if text == "جمله بساز":
        await update.message.reply_text(generate_sentence())
        return

    # ✅ پاسخ هوشمند
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
# ======================= 🧹 ریست و ریلود =======================
async def reset_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    for f in ["memory.json", "group_data.json", "stickers.json", "jokes.json", "fortunes.json"]:
        if os.path.exists(f):
            os.remove(f)
    init_files()
    await update.message.reply_text("🧹 تمام داده‌ها پاک شد!")

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

# ======================= 🌟 پنل اصلی خنگول =======================
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import datetime

FEATURES_FILE = "features.txt"

async def show_main_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    """نمایش پنل اصلی برای کاربران"""
    if os.path.exists(FEATURES_FILE):
        async with aiofiles.open(FEATURES_FILE, "r", encoding="utf-8") as f:
            about_text = await f.read()
    else:
        about_text = (
            "✨ <b>خنگول فارسی 8.7 Cloud+ Supreme Pro</b>\n"
            "🤖 هوش اجتماعی، شوخ‌طبعی و احساس واقعی در یک ربات!\n"
            "💬 همراهی با خنده، فال، و حافظه‌ی اجتماعی بی‌نظیر 🌙"
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
    markup = InlineKeyboardMarkup(keyboard)

    if edit:
        await update.callback_query.edit_message_text(about_text, reply_markup=markup, parse_mode="HTML")
    else:
        await update.message.reply_text(about_text, reply_markup=markup, parse_mode="HTML")

# ======================= 🚀 استارت با انیمیشن =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ <b>در حال بارگذاری سیستم خنگول...</b>", parse_mode="HTML")
    await asyncio.sleep(1.5)

    welcome_text = (
        f"🌙 <b>سلام {update.effective_user.first_name}!</b>\n"
        f"🤖 من <b>خنگول فارسی 8.7 Cloud+ Supreme Pro</b> هستم.\n"
        f"✨ رباتی با احساس، شوخ‌طبعی و حافظه‌ی اجتماعی 😄"
    )
    await msg.edit_text(welcome_text, parse_mode="HTML")
    await asyncio.sleep(1)
    await show_main_panel(update, context)

# ======================= ✍️ ذخیره قابلیت‌ها =======================
async def save_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    if not update.message.reply_to_message or not update.message.reply_to_message.text:
        return await update.message.reply_text("❗ باید روی پیام متنی ریپلای بزنی!")

    text = update.message.reply_to_message.text
    async with aiofiles.open(FEATURES_FILE, "w", encoding="utf-8") as f:
        await f.write(text)

    await update.message.reply_text("✅ متن قابلیت‌ها ذخیره شد!")

# ======================= 🎛 دکمه‌های تعاملی =======================
async def feature_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "feature_info":
        user = query.from_user
        now = datetime.datetime.now().strftime("%Y/%m/%d - %H:%M:%S")
        info = (
            f"🆔 آیدی شما: <code>{user.id}</code>\n"
            f"👤 نام: <b>{user.first_name}</b>\n"
            f"📅 زمان فعلی: <b>{now}</b>"
        )
        await query.message.reply_text(info, parse_mode="HTML")

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
        async def fullstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار کامل گروه‌ها"""
    try:
        data = load_data("group_data.json")
        groups = data.get("groups", {})

        if not groups:
            return await update.message.reply_text("ℹ️ هنوز هیچ گروهی ثبت نشده.")

        text = "📈 آمار کامل گروه‌ها:\n\n"
        if isinstance(groups, list):
            for g in groups:
                title = g.get("title", "نامشخص")
                members = len(g.get("members", []))
                last_active = g.get("last_active", "نامشخص")
                text += f"🏠 گروه: {title}\n👥 اعضا: {members}\n🕓 آخرین فعالیت: {last_active}\n\n"
        else:
            for gid, info in groups.items():
                title = info.get("title", "نامشخص")
                members = len(info.get("members", []))
                last_active = info.get("last_active", "نامشخص")
                text += f"🏠 گروه: {title}\n👥 اعضا: {members}\n🕓 آخرین فعالیت: {last_active}\n\n"

        if len(text) > 4000:
            text = text[:3990] + "..."

        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در نمایش آمار:\n{e}")
# ======================= 🚀 اجرای نهایی ربات =======================
if __name__ == "__main__":
    print("🤖 خنگول فارسی 8.7 Cloud+ Supreme Pro Stable+ آماده به خدمت است ...")

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
    app.add_handler(CommandHandler("reply", toggle_reply_mode))

    # 🔹 قابلیت‌ها و پنل‌ها
    app.add_handler(MessageHandler(filters.Regex("^ثبت قابلیت$"), save_features))
    app.add_handler(CallbackQueryHandler(feature_button_handler, pattern="^feature_"))

    # 🔹 سیستم خوشامد پویا
    app.add_handler(MessageHandler(filters.Regex("^خوشامد$"), open_welcome_panel), group=-1)
    app.add_handler(CallbackQueryHandler(welcome_panel_buttons, pattern="^welcome_"), group=-1)
    app.add_handler(MessageHandler(filters.Regex("^ثبت خوشامد$"), set_welcome_text), group=-1)
    app.add_handler(MessageHandler(filters.Regex("^ثبت عکس خوشامد$"), set_welcome_media), group=-1)
    app.add_handler(MessageHandler(filters.Regex(r"^تنظیم قوانین"), set_rules_link))
    app.add_handler(MessageHandler(filters.Regex(r"^تنظیم حذف"), set_welcome_timer))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome), group=-1)

    # 🔹 راهنما
    app.add_handler(MessageHandler(filters.Regex("^ثبت راهنما$"), save_custom_help))
    app.add_handler(MessageHandler(filters.Regex("^راهنما$"), show_custom_help))

    # 🔹 بازیابی فایل‌ها
    async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.user_data.get("await_restore"):
            return

        doc = update.message.document
        if not doc or not doc.file_name.lower().endswith(".zip"):
            return await update.message.reply_text("❗ لطفاً یک فایل ZIP معتبر بفرست.")

        restore_zip = "restore.zip"
        restore_dir = "restore_temp"
        try:
            tg_file = await doc.get_file()
            await update.message.reply_text("📥 در حال دریافت بک‌آپ (20%)")
            await tg_file.download_to_drive(restore_zip)

            await update.message.reply_text("📂 آماده‌سازی بازگردانی (40%)")
            if os.path.exists(restore_dir):
                shutil.rmtree(restore_dir)
            os.makedirs(restore_dir, exist_ok=True)

            await update.message.reply_text("📦 در حال استخراج فایل‌ها (60%)")
            with zipfile.ZipFile(restore_zip, "r") as zip_ref:
                zip_ref.extractall(restore_dir)

            important_files = ["memory.json", "group_data.json", "jokes.json", "fortunes.json"]
            moved = 0
            for f in important_files:
                src = os.path.join(restore_dir, f)
                if os.path.exists(src):
                    shutil.move(src, f)
                    moved += 1

            init_files()
            await update.message.reply_text(f"✅ بازیابی کامل شد! ({moved} فایل بازگردانی شد)")
        except Exception as e:
            await update.message.reply_text(f"⚠️ خطا در بازیابی:\n{e}")
        finally:
            if os.path.exists(restore_zip): os.remove(restore_zip)
            if os.path.exists(restore_dir): shutil.rmtree(restore_dir)
            context.user_data["await_restore"] = False

    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # 🔹 پاسخ عمومی (در انتها)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    # 🔹 وظایف شروع
    async def on_startup(app):
        await notify_admin_on_startup(app)
        app.create_task(auto_backup(app.bot))
        app.create_task(start_auto_brain_loop(app.bot))
        print("🌙 [SYSTEM] Startup tasks scheduled ✅")

    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)
