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
import aiofiles
from font_maker import font_maker, next_font, prev_font
# 📦 ماژول‌ها
from memory_manager import (
    init_files, load_data, save_data, learn, shadow_learn, get_reply,
    set_mode, get_stats, enhance_sentence, generate_sentence, list_phrases
)

from jokes_manager import save_joke, list_jokes
from fortune_manager import save_fortune, list_fortunes, send_random_fortune
from group_manager import register_group_activity, get_group_stats
from ai_learning import auto_learn_from_text
from smart_reply import detect_emotion, smart_response
from emotion_memory import remember_emotion, get_last_emotion, emotion_context_reply
from auto_brain.auto_brain import start_auto_brain_loop
from selective_backup import selective_backup_menu, selective_backup_buttons
from auto_brain import auto_backup
from auto_brain.command_manager import (
    save_command,
    delete_command,
    handle_custom_command,
    list_commands,
    cleanup_group_commands
)
from context_memory import ContextMemory  # ✅ باید قبل از استفاده ازش باشه
from brain_bridge_group import process_group_message
# 🧠 حافظه کوتاه‌مدت گفتگو برای Context AI
context_memory = ContextMemory()

from ai_chat.chatgpt_panel import show_ai_panel, chat, start_ai_chat, stop_ai_chat
from weather_module.weather_panel import show_weather
from modules.azan_module import get_azan_time, get_ramadan_status
# ======================= 👑 مدیریت سودوها =======================
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
    return [7089376754]  # آیدی مدیر اصلی به‌صورت پیش‌فرض

def save_sudos(data):
    with open(ADMIN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

SUDO_IDS = load_sudos()
init_files()

status = {
    "active": True,
    "learning": True,
    "welcome": True,
    "locked": False
}
# ======================= 🧠 جلوگیری از پاسخ تکراری و پاسخ به خودش =======================
def is_valid_message(update):
    """فیلتر برای جلوگیری از پاسخ تکراری یا پاسخ به پیام‌های ربات"""
    msg = update.effective_message
    if not msg:
        return False

    # جلوگیری از پاسخ به خودش (پیام ربات)
    if msg.from_user and msg.from_user.is_bot:
        return False

    text = msg.text or msg.caption or ""
    if not text.strip():
        return False

    # حافظه کوتاه برای جلوگیری از تکرار
    global LAST_MESSAGES
    if "LAST_MESSAGES" not in globals():
        LAST_MESSAGES = {}

    user_id = msg.from_user.id if msg.from_user else None
    last_msg = LAST_MESSAGES.get(user_id)

    if last_msg == text:
        return False  # پیام تکراری → پاسخ نده

    LAST_MESSAGES[user_id] = text
    return True
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


# ======================= 🚀 استارت سینمایی خفن خنگول =======================
# ======================= 📢 اطلاع به ادمین هنگام استارت =======================
async def notify_admin_on_startup(app):
    """ارسال پیام فعال‌سازی به ادمین هنگام استارت"""
    ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))  # اگر از قبل داری، خطش رو تکرار نکن
    try:
        await app.bot.send_message(
            chat_id=ADMIN_ID,
            text="🚀 ربات خنگول با موفقیت راه‌اندازی شد ✅"
        )
        print("[INFO] Startup notification sent ✅")
    except Exception as e:
        print(f"[ERROR] Failed to notify admin: {e}")
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from datetime import datetime

    user = update.effective_user
    now = datetime.now().strftime("%Y/%m/%d - %H:%M:%S")

    # مرحله اول: شروع بوت
    msg = await update.message.reply_text(
        f"🧠 <b>در حال راه‌اندازی سیستم خنگول...</b>\n"
        f"👤 کاربر: <b>{user.first_name}</b>\n"
        f"🕓 زمان اجرا: <code>{now}</code>",
        parse_mode="HTML"
    )

    # مراحل بوت خنگول با افکت نوری
    steps = [
        "📡 اتصال به مغز مرکزی...",
        "🔍 بررسی سلامت حافظه و داده‌ها...",
        "💬 بارگذاری سیستم شوخ‌طبعی...",
        "🎭 فعال‌سازی احساسات دیجیتالی...",
        "🤖 در حال همگام‌سازی با نسخه Cloud+ Supreme...",
        "🚀 آماده به خدمت 😎"
    ]

    colors = ["🔵", "🟢", "🟣", "🟡", "🔴"]
    bar_len = 14

    for i, step in enumerate(steps, start=1):
        percent = int((i / len(steps)) * 100)
        color = colors[i % len(colors)]
        filled = "█" * int(bar_len * (percent / 100))
        empty = "░" * (bar_len - len(filled))
        bar = f"{color}[{filled}{empty}] {percent}%"

        await asyncio.sleep(1.1)
        try:
            await msg.edit_text(
                f"🧠 <b>بوت سیستم خنگول...</b>\n\n{bar}\n\n{step}\n\n"
                f"👤 کاربر: <b>{user.first_name}</b>\n"
                f"🕓 <code>{now}</code>",
                parse_mode="HTML"
            )
        except:
            pass

    # پایان بوت و نمایش خوشامد نهایی
    await asyncio.sleep(1.2)
    await msg.edit_text(
        f"✨ <b>سیستم خنگول فارسی با موفقیت راه‌اندازی شد!</b>\n\n"
        f"👤 کاربر: <b>{user.first_name}</b>\n"
        f"🕓 زمان اجرا: <code>{now}</code>\n"
        "💬 آماده‌ای برای خنده، احساس و هوش مصنوعی 😎\n\n"
        "👇 از دکمه‌های زیر استفاده کن:",
        parse_mode="HTML"
    )

    # نمایش پنل اصلی بعد از افکت نهایی
    await asyncio.sleep(0.8)
    await show_main_panel(update, context)
# ======================= ⚙️ خطایاب خودکار =======================
async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    error_text = f"⚠️ خطا در ربات:\n\n{context.error}"
    print(error_text)
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=error_text)
    except:
        pass



# ======================= 👑 شناسایی ورود، خروج و صدا زدن سازنده =======================
import random
import os
from memory_manager import load_data, save_data
from telegram import Update
from telegram.ext import ContextTypes

async def detect_admin_movement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشخیص ورود، خروج یا بازگشت سازنده خنگول در گروه‌ها (حتی اگر خوشامد خاموش باشد)"""
    ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))
    chat = update.effective_chat
    message = update.message

    if not message:
        return

    # 📥 ورود سازنده
    if message.new_chat_members:
        for member in message.new_chat_members:
            if member.id == ADMIN_ID:
                data = load_data("group_data.json")
                sudo_status = data.setdefault("sudo_status", {})

                if str(chat.id) in sudo_status:
                    text = (
                        f"👑 <b>بازگشت دوباره‌ی {member.first_name}!</b>\n"
                        f"🎉 خوش اومدی رئیس! مغز خنگول دوباره بیدار شد 🤖✨"
                    )
                else:
                    text = (
                        f"👑 <b>سازنده‌ی خنگول وارد گروه شد!</b>\n"
                        f"✨ حضور {member.first_name} باعث افتخار خنگوله 😎\n"
                        f"🧠 حالت مدیریتی فعال شد و همه آماده‌ی خدمتن!"
                    )

                sudo_status[str(chat.id)] = True
                save_data("group_data.json", data)

                await message.reply_text(text, parse_mode="HTML")
                return

    # 📤 خروج سازنده
    if message.left_chat_member and message.left_chat_member.id == ADMIN_ID:
        data = load_data("group_data.json")
        sudo_status = data.get("sudo_status", {})

        if str(chat.id) in sudo_status:
            sudo_status.pop(str(chat.id))
            save_data("group_data.json", data)

        text = (
            f"😢 <b>سازنده از گروه خارج شد...</b>\n"
            f"🔕 حالت مدیریتی موقتاً غیرفعال شد.\n"
            f"🕯️ تا بازگشت دوباره‌ی خنگول در حالت خودکار می‌مونیم."
        )
        await message.reply_text(text, parse_mode="HTML")

# ======================= 🤖 پاسخ اختصاصی به کلمه "ربات" برای سودو =======================
async def sudo_bot_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """وقتی سازنده بگه 'ربات' — پاسخ‌های ویژه فقط برای سودو"""
    ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        return  # فقط برای سازنده فعاله

    replies = [
        "👑 جانم سودو؟ 😎",
        "🤖 در خدمتتم رئیس!",
        "⚡ بفرما قربان!",
        "🧠 گوش به فرمانتم!",
        "✨ دستور بده شاه خنگول!",
        "😄 آماده‌م برای هر کاری!",
        "🔥 بگو رئیس، منتظرم!"
    ]

    reply = random.choice(replies)
    await update.message.reply_text(reply)
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


# ======================= 📊 آمار خنگول واقعی =======================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_stats()
    groups_data = load_data("group_data.json").get("groups", [])

    # ✅ شمارش گروه‌ها (سازگار با دیکشنری یا لیست)
    if isinstance(groups_data, dict):
        groups = len(groups_data)
    else:
        groups = len(groups_data)

    # ✅ شمارش کاربران از users.json
    users_list = []
    if os.path.exists("users.json"):
        try:
            import json
            with open("users.json", "r", encoding="utf-8") as f:
                users_list = json.load(f)
        except:
            users_list = []
    users = len(users_list)

    # ✅ ساخت پیام نهایی
    msg = (
        f"📊 <b>آمار کلی خنگول:</b>\n\n"
        f"👤 کاربران واقعی: <b>{users}</b>\n"
        f"👥 گروه‌های فعال: <b>{groups}</b>\n"
        f"🧩 جملات ذخیره‌شده: <b>{data['phrases']}</b>\n"
        f"💬 پاسخ‌های یادگرفته: <b>{data['responses']}</b>\n"
        f"🎭 مود فعلی: <b>{data['mode']}</b>"
    )

    await update.message.reply_text(msg, parse_mode="HTML")

# ======================= 📊 آمار کامل گروه‌ها (اصلاح‌شده) =======================
async def fullstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار فقط برای گروه‌ها (فیلتر کاربران از group_data.json)"""
    try:
        data = load_data("group_data.json")
        groups = data.get("groups", {})

        text = "📈 آمار کامل گروه‌ها:\n\n"

        # حالت 1: اگر groups لیست باشه
        if isinstance(groups, list):
            valid_groups = [g for g in groups if str(g.get("id", "")).startswith("-")]
            if not valid_groups:
                return await update.message.reply_text("ℹ️ هنوز هیچ گروهی ثبت نشده.")
            for g in valid_groups:
                group_id = g.get("id")
                title = g.get("title", f"Group_{group_id}")
                members = len(g.get("members", []))
                last_active = g.get("last_active", "نامشخص")

                try:
                    chat = await context.bot.get_chat(group_id)
                    title = chat.title or title
                except:
                    pass

                text += f"🏠 گروه: {title}\n👥 اعضا: {members}\n🕓 آخرین فعالیت: {last_active}\n\n"

        # حالت 2: اگر groups دیکشنری باشه
        elif isinstance(groups, dict):
            valid_items = {gid: info for gid, info in groups.items() if str(gid).startswith("-")}
            if not valid_items:
                return await update.message.reply_text("ℹ️ هنوز هیچ گروهی ثبت نشده.")
            for gid, info in valid_items.items():
                title = info.get("title", f"Group_{gid}")
                members = len(info.get("members", []))
                last_active = info.get("last_active", "نامشخص")

                try:
                    chat = await context.bot.get_chat(gid)
                    title = chat.title or title
                except:
                    pass

                text += f"🏠 گروه: {title}\n👥 اعضا: {members}\n🕓 آخرین فعالیت: {last_active}\n\n"

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
        now = datetime.now().strftime("%Y/%m/%d ⏰ %H:%M")
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



# ======================= ☁️ بک‌آپ خودکار و دستی (نسخه هماهنگ با bot.py) =======================
import os
import zipfile
import shutil
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

# 🧩 تنظیمات پایه
BACKUP_FOLDER = "backups"
ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))

# ======================= ⚙️ توابع اصلی =======================

def _should_include_in_backup(path: str) -> bool:
    """فقط فایل‌های مهم داخل بک‌آپ بروند"""
    lowered = path.lower()
    skip_dirs = ["__pycache__", ".git", "venv", "restore_temp", BACKUP_FOLDER]
    if any(sd in lowered for sd in skip_dirs):
        return False
    if lowered.endswith(".zip") or os.path.basename(lowered).startswith("backup_"):
        return False
    return lowered.endswith((".json", ".jpg", ".png", ".webp", ".mp3", ".ogg"))

# ======================= ☁️ بک‌آپ خودکار =======================

async def auto_backup(bot):
    """بک‌آپ خودکار هر ۶ ساعت"""
    while True:
        await cloudsync_internal(bot, "Auto Backup")
        await asyncio.sleep(6 * 60 * 60)  # ⏰ هر ۶ ساعت

# ======================= 💾 ساخت و ارسال بک‌آپ =======================

async def cloudsync_internal(bot, reason="Manual Backup"):
    """ایجاد و ارسال فایل ZIP به ادمین"""
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

        size_mb = os.path.getsize(filename) / (1024 * 1024)
        caption = (
            f"🧠 <b>بک‌آپ جدید ساخته شد!</b>\n"
            f"📅 تاریخ: <code>{now}</code>\n"
            f"💾 حجم: <code>{size_mb:.2f} MB</code>\n"
            f"☁️ نوع: {reason}"
        )

        # ارسال فایل بک‌آپ برای ادمین
        with open(filename, "rb") as f:
            await bot.send_document(chat_id=ADMIN_ID, document=f, caption=caption, parse_mode="HTML")
        print(f"✅ بک‌آپ ارسال شد ({size_mb:.2f} MB)")

    except Exception as e:
        print(f"[CLOUD BACKUP ERROR] {e}")
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=f"⚠️ خطا در Cloud Backup:\n{e}")
        except:
            pass
    finally:
        if os.path.exists(filename):
            os.remove(filename)

# ======================= 💬 دستور /cloudsync برای سودو =======================

async def cloudsync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اجرای دستی بک‌آپ ابری"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")
    await cloudsync_internal(context.bot, "Manual Cloud Backup")

# ======================= 💾 بک‌آپ و بازیابی ZIP در چت =======================

async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بک‌آپ دستی و ارسال در چت"""
    await cloudsync_internal(context.bot, "Manual Backup")
    await update.message.reply_text("✅ بک‌آپ کامل گرفته شد و ارسال شد!")

async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت فایل ZIP برای بازیابی"""
    await update.message.reply_text("📂 فایل ZIP بک‌آپ را بفرست تا بازیابی شود.")
    context.user_data["await_restore"] = True

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش فایل ZIP و بازیابی ایمن"""
    if not context.user_data.get("await_restore"):
        return

    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith(".zip"):
        return await update.message.reply_text("❗ لطفاً فقط فایل ZIP معتبر بفرست.")

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

        from memory_manager import init_files
        init_files()

        if moved_any:
            await update.message.reply_text("✅ بازیابی کامل انجام شد!")
        else:
            await update.message.reply_text("ℹ️ فایلی برای جایگزینی پیدا نشد.")

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
    

    # 🚫 جلوگیری از پاسخ هوشمند در صورت اجرای دستور سفارشی
    if context.user_data.get("custom_handled"):
        context.user_data["custom_handled"] = False
        return
    

    # 🧩 اطمینان از اینکه پیام معتبره
    if not update.message or not update.message.text:
        return
        reply_text = process_group_message(uid, chat_id, text)
        # 🧠 فعال‌سازی حافظهٔ کوتاه‌مدت گفتگو
    uid = update.effective_user.id
    text = update.message.text.strip()

    # 🧠 ثبت پیام در حافظه کوتاه‌مدت
    context_memory.add_message(uid, text)

    # 🧠 گرفتن کل تاریخچه اخیر کاربر
    recent_context = context_memory.get_context(uid)

    # 🧩 ترکیب سه پیام آخر برای درک بهتر ادامه گفتگو
    full_context = " ".join(recent_context[-3:]) if recent_context else text

    text = update.message.text.strip()
    lower_text = text.lower()
    uid = update.effective_user.id
    chat_id = update.effective_chat.id

    # 🚫 جلوگیری از پاسخ در پیوی (فقط جوک و فال مجازند)
    if update.effective_chat.type == "private" and lower_text not in ["جوک", "فال"]:
        return
    if re.search(r"(هوای|آب[\s‌]*و[\s‌]*هوا)", text):
        return

    # ✅ جلوگیری از پاسخ به دستورات خاص (مثل راهنما، خوشامد، ربات و غیره)
    protected_words = [
        "راهنما", "ثبت راهنما", "خوشامد", "ثبت خوشامد",
        "ربات", "save", "del", "panel", "backup", "cloudsync", "leave"
    ]
    if any(lower_text.startswith(word) for word in protected_words):
        return

    # 🧠 بررسی حالت ریپلی مود گروهی
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
        await update.message.reply_text(list_phrases(), parse_mode="HTML")
        return

    # ✅ یادگیری دستی با استایل زیبا و خروجی حرفه‌ای
    if text.startswith("یادبگیر "):
        parts = text.replace("یادبگیر ", "").split("\n")

        if len(parts) > 1:
            phrase = parts[0].strip()
            responses = [p.strip() for p in parts[1:] if p.strip()]

            msg = learn(phrase, *responses)

            # 🎨 ساخت خروجی نمایشی با جزئیات و اموجی‌ها
            visual = (
                f"🧠 <b>خنگول یاد گرفت!</b>\n"
                f"💬 <b>جمله:</b> <code>{phrase}</code>\n"
                f"✨ <b>تعداد پاسخ‌ها:</b> {len(responses)}\n"
                f"➕ <i>{msg}</i>\n\n"
                f"📘 حالا هوش خنگول باهوش‌تر شد 🤖💫"
            )

            await update.message.reply_text(visual, parse_mode="HTML")

            # 💾 یادگیری سایه برای تقویت حافظه
            for r in responses:
                shadow_learn(phrase, r)

        else:
            await update.message.reply_text(
                "❗ بعد از 'یادبگیر' جمله و پاسخ‌هاش رو در خطوط جدا بنویس.\n\n"
                "📘 مثال:\n"
                "<code>یادبگیر سلام\nسلام خنگول 😄</code>",
                parse_mode="HTML"
            )
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
        reply_text = smart_response(full_context, uid) or enhance_sentence(full_context)

    await update.message.reply_text(reply_text)




# ======================= 🧹 ریست و ریلود =======================
import asyncio, os, json, random
from datetime import datetime

# ======================= 🧹 ریست و 🔄 ریلود لوکس خنگول با افکت =======================
async def reset_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاکسازی کامل مغز خنگول فقط برای مدیر اصلی"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    loading_text = "🧠 <b>در حال پاکسازی کامل مغز خنگول...</b>\n"
    msg = await update.message.reply_text(loading_text, parse_mode="HTML")

    steps = [
        "🧹 حذف حافظه جملات...",
        "🗑 پاکسازی داده‌های گروهی...",
        "💾 حذف فایل‌های جوک و فال...",
        "👤 حذف کاربران ذخیره‌شده...",
        "🧩 بازسازی ساختار حافظه جدید...",
        "🤖 آماده‌سازی مغز تازه...",
        "🌙 نهایی‌سازی سیستم هوش مصنوعی..."
    ]

    files_to_remove = ["memory.json", "group_data.json", "stickers.json", "jokes.json", "fortunes.json", "users.json"]

    for i, step in enumerate(steps, start=1):
        percent = int((i / len(steps)) * 100)
        bar_len = 12
        filled = "█" * int(bar_len * (percent / 100))
        empty = "░" * (bar_len - len(filled))
        bar = f"[{filled}{empty}] {percent}%"

        await asyncio.sleep(random.uniform(0.5, 1.0))
        try:
            await msg.edit_text(f"{loading_text}\n{bar}\n\n{step}", parse_mode="HTML")
        except:
            pass

        # حذف مرحله‌ای فایل‌ها
        if i <= len(files_to_remove):
            f = files_to_remove[i - 1]
            if os.path.exists(f):
                os.remove(f)

    init_files()

    await asyncio.sleep(1.2)
    await msg.edit_text(
        "✅ <b>پاکسازی مغز خنگول کامل شد!</b>\n"
        "🧠 حافظه جدید ساخته شد و آماده‌ی بوت است.\n\n"
        "🔄 اکنون دستور <b>/reload</b> را برای راه‌اندازی سیستم بفرست.",
        parse_mode="HTML"
    )

# ======================= 🔄 بوت هوش مصنوعی + افکت نوری =======================
async def reload_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بوت سیستم خنگول با افکت نوری و گزارش نهایی — فقط برای مدیر اصلی"""
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه سیستم رو بوت کنه!")

    loading_text = "🤖 <b>در حال بوت سیستم هوش مصنوعی خنگول...</b>\n"
    msg = await update.message.reply_text(loading_text, parse_mode="HTML")

    steps = [
        "📡 اتصال به هسته‌ی هوش مصنوعی...",
        "🔍 بررسی سلامت فایل‌های حافظه...",
        "🧩 بازسازی ساختار داده‌ها...",
        "💬 بارگذاری پاسخ‌ها و جملات...",
        "👥 شناسایی کاربران و گروه‌ها...",
        "🧠 فعال‌سازی هوش اجتماعی و شوخ‌طبعی...",
        "⚙️ همگام‌سازی با مغز ابری Cloud+...",
        "🚀 نهایی‌سازی سیستم خنگول..."
    ]

    colors = ["🔵", "🟢", "🟣", "🟡", "🔴"]
    for i, step in enumerate(steps, start=1):
        percent = int((i / len(steps)) * 100)
        color = random.choice(colors)
        bar_len = 14
        filled = "█" * int(bar_len * (percent / 100))
        empty = "░" * (bar_len - len(filled))
        bar = f"{color}[{filled}{empty}] {percent}%"

        await asyncio.sleep(random.uniform(0.6, 1.2))
        try:
            await msg.edit_text(f"{loading_text}\n{bar}\n\n{step}", parse_mode="HTML")
        except:
            pass

    # بازسازی فایل‌ها
    init_files()

    # محاسبه آمار
    def count_items(file):
        if not os.path.exists(file):
            return 0
        try:
            data = load_data(file)
            if isinstance(data, dict):
                return len(data)
            elif isinstance(data, list):
                return len(data)
        except:
            return 0
        return 0

    phrases = len(load_data("memory.json").get("phrases", {}))
    responses = sum(len(v) for v in load_data("memory.json").get("phrases", {}).values())
    groups = len(load_data("group_data.json").get("groups", []))
    users = count_items("users.json")
    jokes = count_items("jokes.json")
    fortunes = count_items("fortunes.json")

    await asyncio.sleep(1.3)
    now = datetime.now().strftime("%Y/%m/%d - %H:%M:%S")

    final_text = (
        "✨ <b>سیستم با موفقیت بوت شد!</b>\n\n"
        "💻 <b>گزارش نهایی خنگول:</b>\n"
        f"🧠 جملات: {phrases}\n"
        f"💬 پاسخ‌ها: {responses}\n"
        f"👤 کاربران: {users}\n"
        f"👥 گروه‌ها: {groups}\n"
        f"😂 جوک‌ها: {jokes}\n"
        f"🔮 فال‌ها: {fortunes}\n\n"
        f"🕓 زمان اجرا: <i>{now}</i>\n"
        "🌙 <b>اتصال به مغز مرکزی برقرار شد.</b>\n"
        "🤖 هوش اجتماعی و شوخ‌طبعی فعال شدند.\n"
        "✅ <b>سیستم خنگول Cloud+ آماده‌ به‌ خدمت است!</b>"
    )

    await msg.edit_text(final_text, parse_mode="HTML")

    # 🎬 افکت نهایی — ارسال استیکر یا انیمیشن
    try:
        stickers = [
            "CAACAgUAAxkBAAIKf2aGZOkzDgP0xldu-7nKn3E7VnyjAAJgAwACGvSIVVRS9HZ5QbPoNgQ",  # برق مغز
            "CAACAgQAAxkBAAIKfmaGZOmEDEsNbdR7IZNmb0LsvhH7AAKGAQAC-8E0BvZ-QTzM2m0GNgQ",  # سیستم فعال شد
            "CAACAgIAAxkBAAIKfWaGZOnC7fMZr1bWPSGfOpg8UVltAAI4AAPANk8TfgAAAY7e1LoeNgQ",  # سلام دوباره
        ]
        await asyncio.sleep(1.5)
        await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=random.choice(stickers))
    except Exception as e:
        print(f"[Sticker Error] {e}")

# ======================= 📨 ارسال همگانی =======================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه پیام همگانی بفرسته!")

    msg_text = " ".join(context.args)
    if not msg_text:
        return await update.message.reply_text("❗ بعد از /broadcast پیام مورد نظر رو بنویس.")

    import json, os

    # ✅ خواندن کاربران از users.json
    users = []
    user_names = []
    if os.path.exists("users.json"):
        try:
            with open("users.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                users = [u["id"] for u in data]
                user_names = [u.get("name", str(u["id"])) for u in data]
        except:
            pass

    # ✅ خواندن گروه‌ها از group_data.json (سازگار با هر دو ساختار)
    groups_data = load_data("group_data.json").get("groups", {})
    group_ids, group_names = [], []
    if isinstance(groups_data, dict):
        for gid, info in groups_data.items():
            group_ids.append(gid)
            group_names.append(info.get("title", f"Group_{gid}"))
    elif isinstance(groups_data, list):
        for g in groups_data:
            if "id" in g:
                group_ids.append(g["id"])
                group_names.append(g.get("title", f"Group_{g['id']}"))

    total_targets = len(users) + len(group_ids)
    if total_targets == 0:
        return await update.message.reply_text("⚠️ هیچ کاربر یا گروهی برای ارسال پیدا نشد!")

    # 🕓 پیام اولیه
    progress_msg = await update.message.reply_text(
        f"📨 در حال ارسال همگانی...\n"
        f"👤 کاربران: {len(users)} | 👥 گروه‌ها: {len(group_ids)}\n"
        f"📊 پیشرفت: 0%"
    )

    sent, failed = 0, 0
    last_percent = 0

    async def update_progress():
        percent = int(((sent + failed) / total_targets) * 100)
        nonlocal last_percent
        if percent - last_percent >= 10 or percent == 100:
            last_percent = percent
            try:
                await progress_msg.edit_text(
                    f"📨 در حال ارسال همگانی...\n"
                    f"👤 کاربران: {len(users)} | 👥 گروه‌ها: {len(group_ids)}\n"
                    f"📊 پیشرفت: {percent}%"
                )
            except:
                pass

    # 🔸 ارسال به کاربران
    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=msg_text)
            sent += 1
        except:
            failed += 1
        await update_progress()
        await asyncio.sleep(0.3)

    # 🔸 ارسال به گروه‌ها
    for gid in group_ids:
        try:
            await context.bot.send_message(chat_id=int(gid), text=msg_text)
            sent += 1
        except:
            failed += 1
        await update_progress()
        await asyncio.sleep(0.3)

    # ✅ نتیجه نهایی با لیست نمونه
    example_users = "، ".join(user_names[:3]) if user_names else "—"
    example_groups = "، ".join(group_names[:3]) if group_names else "—"

    result = (
        "✅ <b>ارسال همگانی با موفقیت انجام شد!</b>\n\n"
        f"👤 کاربران: <b>{len(users)}</b>\n"
        f"👥 گروه‌ها: <b>{len(group_ids)}</b>\n"
        f"📦 مجموع گیرندگان: <b>{total_targets}</b>\n"
        f"📤 موفق: <b>{sent}</b>\n"
        f"⚠️ ناموفق: <b>{failed}</b>\n\n"
        f"👤 نمونه کاربران: <i>{example_users}</i>\n"
        f"🏠 نمونه گروه‌ها: <i>{example_groups}</i>"
    )

    await progress_msg.edit_text(result, parse_mode="HTML")
    # 🧹 وقتی ربات از گروه حذف می‌شود، دستورهای مربوط به آن گروه پاک می‌شوند
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
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import aiofiles, os, asyncio
from datetime import datetime

TEXTS_PATH = "texts"

async def load_text(file_name, default_text):
    path = os.path.join(TEXTS_PATH, file_name)
    if os.path.exists(path):
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            return await f.read()
    return default_text




    # ======================= 🎛 پنل اصلی خنگول =======================
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes

async def show_main_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    about = "🌙 <b>به منوی اصلی خنگول خوش آمدی!</b>\nاز دکمه‌های زیر یکی رو انتخاب کن 😎"

    keyboard = [
        [
            InlineKeyboardButton("💬 ارتباط با سازنده", url="https://t.me/NOORI_NOOR"),
            InlineKeyboardButton("💭 گروه پشتیبانی", url="https://t.me/Poshtibahni")
        ],
        [
            InlineKeyboardButton("➕ افزودن به گروه", url="https://t.me/Khenqol_bot?startgroup=true"),
            InlineKeyboardButton("🧩 قابلیت‌های ربات", callback_data="panel_features")
        ],
        [
            InlineKeyboardButton("🤖 درباره خنگول", callback_data="panel_about"),
            InlineKeyboardButton("👨‍💻 درباره تیم ما", callback_data="panel_team")
        ],
        [
            InlineKeyboardButton("🔮 فال امروز", callback_data="panel_fortune"),
            InlineKeyboardButton("😂 جوک خنده‌دار", callback_data="panel_joke")
        ],
        [
            InlineKeyboardButton("🎨 فونت‌ساز حرفه‌ای", callback_data="panel_font"),
            InlineKeyboardButton("💳 آیدی خنگولی من", callback_data="panel_stats")
        ],
        [
            InlineKeyboardButton("🧠 گفتگوی ChatGPT", callback_data="panel_chatgpt")
        ],
        [
            InlineKeyboardButton("🌤 آب و هوا", callback_data="panel_weather")
        ]
    ]

    markup = InlineKeyboardMarkup(keyboard)

    if edit:
        await update.callback_query.edit_message_text(about, reply_markup=markup, parse_mode="HTML")
    else:
        await update.message.reply_text(about, reply_markup=markup, parse_mode="HTML")
        # ======================= 🎛 بازگشت از منوی فونت یا سایر قابلیت‌ها =======================
async def feature_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # ✅ ساخت یک آبجکت ساده که هم message داره، هم callback_query
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
        "panel_about": ("about_khengol.txt", "💫 درباره خنگول"),
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
        user = query.from_user
        now = datetime.now().strftime("%Y/%m/%d - %H:%M:%S")

        text = (
            f"📊 <b>اطلاعات کاربر:</b>\n\n"
            f"👤 نام: <b>{user.first_name}</b>\n"
            f"🆔 آیدی: <code>{user.id}</code>\n"
            f"📅 تاریخ و ساعت فعلی: <b>{now}</b>"
        )

        try:
            # 📸 اگر عکس پروفایل دارد، نمایش بده
            photos = await context.bot.get_user_profile_photos(user.id, limit=1)
            if photos.total_count > 0:
                file_id = photos.photos[0][-1].file_id
                await query.message.reply_photo(photo=file_id, caption=text, parse_mode="HTML")
            else:
                await query.message.reply_text(text, parse_mode="HTML")
        except Exception as e:
            # اگر خطا یا محدودیت بود، فقط متن بفرست
            await query.message.reply_text(text, parse_mode="HTML")

    elif query.data == "panel_weather":
        await show_weather(update, context)

    elif query.data == "panel_fortune":
        await query.message.reply_text("🔮 برای دیدن فال بنویس:\n<b>فال</b>", parse_mode="HTML")

    elif query.data == "panel_joke":
        await query.message.reply_text("😂 برای دیدن جوک بنویس:\n<b>جوک</b>", parse_mode="HTML")

    elif query.data == "panel_font":
        await query.message.reply_text("🎨 برای ساخت فونت بنویس:\n<b>فونت اسم‌ت</b>", parse_mode="HTML")

    elif query.data == "back_main":
        await show_main_panel(update, context, edit=True)

# ======================= 🔐 ثبت فایل‌ها فقط توسط مدیر اصلی =======================
async def save_panel_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه متن‌ها رو تغییر بده!")

    if not update.message.reply_to_message or not update.message.reply_to_message.text:
        return await update.message.reply_text("❗ باید روی یک پیام متنی ریپلای بزنی!")

    parts = update.message.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        return await update.message.reply_text("❗ بنویس: ثبت درباره یا ثبت تیم")

    cmd = parts[1]
    filename = None
    if cmd == "درباره":
        filename = "about_khengol.txt"
    elif cmd == "تیم":
        filename = "team_noori.txt"
    elif cmd == "قابلیت":
        filename = "features.txt"

    if filename:
        os.makedirs(TEXTS_PATH, exist_ok=True)
        async with aiofiles.open(os.path.join(TEXTS_PATH, filename), "w", encoding="utf-8") as f:
            await f.write(update.message.reply_to_message.text)
        await update.message.reply_text(f"✅ متن «{cmd}» ذخیره شد!")
    else:
        await update.message.reply_text("❗ دستور اشتباه است — باید یکی از این‌ها باشد:\nثبت درباره / ثبت تیم / ثبت قابلیت")
# ======================= 🧾 سیستم ثبت دستی راهنما و help =======================
# بدون نیاز به ویرایش فایل‌ها یا پوشه‌ها
# ==============================================================
import os, json
from telegram import Update
from telegram.ext import ContextTypes

# 📦 مسیر ذخیره داده‌ها
DATA_FILE = "help_data.json"

# 🔐 مدیر اصلی
ADMIN_ID = int(os.getenv("ADMIN_ID", "7089376754"))

# ======================= 📦 توابع کمکی =======================
def load_help_data():
    """خواندن فایل help_data.json"""
    if not os.path.exists(DATA_FILE):
        return {"help": "", "guide": ""}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"help": "", "guide": ""}


def save_help_data(data):
    """ذخیره‌سازی help_data.json"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================= 💾 ثبت help =======================
async def save_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ثبت یا تغییر متن /help فقط برای مدیر اصلی"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return await update.message.reply_text("😜 فقط مغز اصلی (سودو) می‌تونه help رو تغییر بده!")

    if not update.message.reply_to_message or not update.message.reply_to_message.text:
        return await update.message.reply_text("ℹ️ لطفاً روی متن جدید help ریپلای کن و بنویس: ثبت help")

    text = update.message.reply_to_message.text
    data = load_help_data()
    data["help"] = text
    save_help_data(data)

    await update.message.reply_text("✅ متن help با موفقیت ذخیره شد، رئیس!")

# ======================= 💾 ثبت راهنما =======================
async def save_custom_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ثبت یا تغییر متن 'راهنما' فقط برای مدیر اصلی"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return await update.message.reply_text("😎 فقط رئیس خنگول اجازه ویرایش راهنما رو داره!")

    if not update.message.reply_to_message or not update.message.reply_to_message.text:
        return await update.message.reply_text("ℹ️ لطفاً روی متن جدید راهنما ریپلای کن و بنویس: ثبت راهنما")

    text = update.message.reply_to_message.text
    data = load_help_data()
    data["guide"] = text
    save_help_data(data)

    await update.message.reply_text("✅ متن راهنمای عمومی با موفقیت ذخیره شد 😄")

# ======================= 📖 نمایش help (فقط برای مدیر اصلی) =======================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش متن /help — فقط برای مدیر اصلی"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        funny_replies = [
            "🤖 اوووه نه نه نه! این بخش مخصوص مغز خنگوله 😜",
            "😎 تو مجاز به دیدن منوی سودو نیستی!",
            "🧠 فقط رئیس می‌تونه به /help اصلی دسترسی داشته باشه!",
            "🚫 ورود ممنوع! فقط خنگول اعظم اجازه داره!",
            "😂 فکر کردی می‌تونی کدهای مخفی منو ببینی؟"
        ]
        import random
        return await update.message.reply_text(random.choice(funny_replies))

    data = load_help_data()
    text = data.get("help", "")
    if not text:
        return await update.message.reply_text("ℹ️ هنوز متنی برای help ثبت نشده.")
    await update.message.reply_text(text)

# ======================= 📖 نمایش راهنما (برای همه کاربران) =======================
async def show_custom_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش متن 'راهنما' برای همه کاربران"""
    data = load_help_data()
    text = data.get("guide", "")
    if not text:
        return await update.message.reply_text("ℹ️ هنوز متنی برای راهنما ثبت نشده.")
    await update.message.reply_text(text)
# ======================= ⚙️ سیستم مدیریت گروه =======================
# ======================= ⚙️ سیستم مدیریت گروه (نسخه نهایی) =======================
import json, os
from datetime import datetime
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes

# 🔧 فایل‌های ذخیره
GROUP_CTRL_FILE = "group_control.json"
ALIASES_FILE = "aliases.json"

# 👑 سودوها (آی‌دی خودت و افراد مجاز)
SUDO_IDS = [123456789, 7089376754]  # 👈 آی‌دی‌هات رو اینجا بذار

# ✅ alias پیش‌فرض (قابل تغییر توسط سودوها)
ALIASES = {
    "ban": ["ban", "بن", "اخراج"],
    "unban": ["unban", "آزاد", "رفع‌بن"],
    "warn": ["warn", "اخطار", "هشدار"],
    "unwarn": ["unwarn", "پاک‌اخطار", "حذف‌اخطار"],
    "mute": ["mute", "سکوت", "خفه"],
    "unmute": ["unmute", "آزادسکوت", "رفع‌سکوت"],
    "addadmin": ["addadmin", "افزودنمدیر", "ادمین"],
    "removeadmin": ["removeadmin", "حذفمدیر", "برکنار"],
    "admins": ["admins", "مدیران", "ادمینها"],
    "lock": ["lock", "قفل"],
    "unlock": ["unlock", "باز"],
    "alias": ["alias", "تغییر"]
}

# 📂 بارگذاری و ذخیره فایل‌ها
def load_json_file(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return default

def save_json_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

group_data = load_json_file(GROUP_CTRL_FILE, {})
ALIASES = load_json_file(ALIASES_FILE, ALIASES)

# 🧠 بررسی مجاز بودن
async def is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if user.id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ["administrator", "creator"]
    except:
        return False

# 🧱 بررسی هدف (تا روی مدیر / سودو / ربات اجرا نشه)
async def can_act_on_target(update, context, target):
    bot = await context.bot.get_me()
    chat = update.effective_chat

    if target.id == bot.id:
        replies = [
            "😏 می‌خوای منو بن کنی؟ من اینجارو ساختم!",
            "😂 جدی؟ منو سکوت می‌کنی؟ خودت خفه شو بهتره.",
            "😎 منو اخطار می‌دی؟ خودتو جمع کن رفیق."
        ]
        await update.message.reply_text(replies[hash(target.id) % len(replies)])
        return False

    if target.id in SUDO_IDS or target.id == int(os.getenv("ADMIN_ID", "7089376754")):
        await update.message.reply_text("⚠️ این کاربر از مدیران ارشد یا سازنده است — نمی‌تونی کاریش کنی!")
        return False

    try:
        member = await context.bot.get_chat_member(chat.id, target.id)
        if member.status in ["administrator", "creator"]:
            await update.message.reply_text("⚠️ نمی‌تونی روی مدیر گروه کاری انجام بدی!")
            return False
    except:
        pass
    return True


# 🚫 بن و رفع‌بن
async def handle_ban(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران یا سودوها می‌توانند بن کنند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید روی پیام کاربر ریپلای بزنی.")
    target = update.message.reply_to_message.from_user
    chat = update.effective_chat

    if not await can_act_on_target(update, context, target):
        return

    try:
        await context.bot.ban_chat_member(chat.id, target.id)
        await update.message.reply_text(f"🚫 <b>{target.first_name}</b> بن شد.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")


async def handle_unban(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران یا سودوها مجازند!")

    chat = update.effective_chat
    user_id = None

    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
    elif context.args:
        user_id = int(context.args[0])
    else:
        return await update.message.reply_text("🔹 باید روی پیام فرد ریپلای بزنی یا آیدی وارد کنی.")

    try:
        await context.bot.unban_chat_member(chat.id, user_id)
        await update.message.reply_text("✅ کاربر از بن خارج شد.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در رفع بن:\n<code>{e}</code>", parse_mode="HTML")


# ⚠️ اخطار (۳ اخطار = بن)
async def handle_warn(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید روی پیام کاربر ریپلای بزنی.")
    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)

    if not await can_act_on_target(update, context, target):
        return

    group = group_data.get(chat_id, {"warns": {}, "admins": []})
    warns = group["warns"]
    warns[str(target.id)] = warns.get(str(target.id), 0) + 1
    count = warns[str(target.id)]
    group["warns"] = warns
    group_data[chat_id] = group
    save_json_file(GROUP_CTRL_FILE, group_data)

    if count >= 3:
        try:
            await context.bot.ban_chat_member(chat_id, target.id)
            await update.message.reply_text(f"🚫 <b>{target.first_name}</b> سه اخطار گرفت و بن شد!", parse_mode="HTML")
            warns[str(target.id)] = 0
        except:
            pass
    else:
        await update.message.reply_text(f"⚠️ <b>{target.first_name}</b> اخطار شماره <b>{count}</b> گرفت.", parse_mode="HTML")


# 🤐 سکوت / رفع سکوت (بهبود یافته)
async def handle_mute(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید روی پیام کاربر ریپلای بزنی.")

    target = update.message.reply_to_message.from_user
    chat = update.effective_chat
    user = update.effective_user

    if not await can_act_on_target(update, context, target):
        return

    try:
        await context.bot.restrict_chat_member(chat.id, target.id, permissions=ChatPermissions(can_send_messages=False))
        time_str = datetime.now().strftime("%H:%M - %d/%m/%Y")
        await update.message.reply_text(
            f"🤐 <b>{target.first_name}</b> ساکت شد و دیگر نمی‌تواند پیام بفرستد.\n\n"
            f"👤 <b>توسط:</b> {user.first_name}\n"
            f"🕒 <b>زمان:</b> {time_str}",
            parse_mode="HTML"
        )
    except:
        await update.message.reply_text("⚠️ نمی‌توان این کاربر را ساکت کرد (احتمالاً مدیر یا مالک است).", parse_mode="HTML")


async def handle_unmute(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید روی پیام کاربر ریپلای بزنی.")

    target = update.message.reply_to_message.from_user
    chat = update.effective_chat
    user = update.effective_user

    try:
        await context.bot.restrict_chat_member(chat.id, target.id, permissions=ChatPermissions(can_send_messages=True))
        time_str = datetime.now().strftime("%H:%M - %d/%m/%Y")
        await update.message.reply_text(
            f"🔊 <b>{target.first_name}</b> از حالت سکوت خارج شد و اکنون می‌تواند صحبت کند.\n\n"
            f"👤 <b>توسط:</b> {user.first_name}\n"
            f"🕒 <b>زمان:</b> {time_str}",
            parse_mode="HTML"
        )
    except:
        await update.message.reply_text("⚠️ نمی‌توان سکوت این کاربر را برداشت (احتمالاً مدیر یا صاحب گروه است).", parse_mode="HTML")


# 🔐 قفل / باز کردن گروه (با وضعیت، زمان و اجراکننده)
async def handle_lock(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران یا سودوها مجازند قفل کنند!")

    chat = update.effective_chat
    chat_id = str(chat.id)
    user = update.effective_user

    group = group_data.get(chat_id, {"locked": False})
    locked = group.get("locked", False)

    if locked:
        return await update.message.reply_text("🔒 گروه از قبل قفل بوده است!", parse_mode="HTML")

    try:
        await context.bot.set_chat_permissions(chat.id, ChatPermissions(can_send_messages=False))
        group["locked"] = True
        group_data[chat_id] = group
        save_json_file(GROUP_CTRL_FILE, group_data)

        time_str = datetime.now().strftime("%H:%M - %d/%m/%Y")
        await update.message.reply_text(
            f"🔒 <b>گروه با موفقیت قفل شد!</b>\n"
            f"📵 فقط مدیران و سودوها می‌توانند پیام بفرستند.\n\n"
            f"👤 <b>توسط:</b> {user.first_name}\n"
            f"🕒 <b>زمان:</b> {time_str}",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در قفل کردن:\n<code>{e}</code>", parse_mode="HTML")


async def handle_unlock(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران یا سودوها مجازند باز کنند!")

    chat = update.effective_chat
    chat_id = str(chat.id)
    user = update.effective_user

    group = group_data.get(chat_id, {"locked": False})
    locked = group.get("locked", False)

    if not locked:
        return await update.message.reply_text("🔓 گروه از قبل باز بوده است!", parse_mode="HTML")

    try:
        await context.bot.set_chat_permissions(chat.id, ChatPermissions(can_send_messages=True))
        group["locked"] = False
        group_data[chat_id] = group
        save_json_file(GROUP_CTRL_FILE, group_data)

        time_str = datetime.now().strftime("%H:%M - %d/%m/%Y")
        await update.message.reply_text(
            f"🔓 <b>گروه باز شد!</b>\n"
            f"💬 همه اعضا می‌توانند گفتگو کنند.\n\n"
            f"👤 <b>توسط:</b> {user.first_name}\n"
            f"🕒 <b>زمان:</b> {time_str}",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در باز کردن:\n<code>{e}</code>", parse_mode="HTML")


# ⚙️ alias فقط توسط سودوها
async def handle_alias(update, context):
    user = update.effective_user
    if user.id not in SUDO_IDS:
        return await update.message.reply_text("🚫 فقط سودوها می‌توانند alias را تغییر دهند!")

    text = update.message.text.split(" ", 2)
    if len(text) < 3:
        return await update.message.reply_text("🔹 استفاده: alias [دستور_اصلی] [نام_جدید]\nمثلاً: alias lock قفل گروه")

    base = text[1].lower()
    new = text[2].strip().lower()

    if base not in ALIASES:
        return await update.message.reply_text("⚠️ چنین دستوری وجود ندارد!")

    for cmd, a_list in ALIASES.items():
        if new in a_list:
            return await update.message.reply_text("⚠️ این نام از قبل استفاده شده است!")

    ALIASES[base].append(new)
    save_json_file(ALIASES_FILE, ALIASES)
    await update.message.reply_text(f"✅ دستور <b>{base}</b> اکنون با <b>{new}</b> نیز قابل اجراست.", parse_mode="HTML")


# 📡 هندلر نهایی برای تمام alias‌ها (بدون /)
async def group_command_handler(update, context):
    text = update.message.text.strip().lower()

    if text.startswith("alias "):
        return await handle_alias(update, context)

    for cmd, aliases in ALIASES.items():
        for alias in aliases:
            if text == alias:
                handlers = {
                    "ban": handle_ban, "unban": handle_unban,
                    "warn": handle_warn, "unwarn": handle_warn,
                    "mute": handle_mute, "unmute": handle_unmute,
                    "lock": handle_lock, "unlock": handle_unlock
                }
                if cmd in handlers:
                    return await handlers[cmd](update, context)
    return
    # ======================= 🔒 سیستم قفل‌های پیشرفته گروه =======================
from telegram import ChatPermissions
from datetime import datetime

# ✅ لیست قفل‌های پشتیبانی‌شده
LOCK_TYPES = {
    "links": "ارسال لینک‌ها",
    "photos": "ارسال عکس",
    "videos": "ارسال ویدیو",
    "files": "ارسال فایل",
    "gifs": "ارسال گیف",
    "voices": "ارسال ویس",
    "vmsgs": "ارسال ویدیو مسیج",
    "stickers": "ارسال استیکر",
    "forward": "ارسال فوروارد",
    "ads": "ارسال تبلیغ / تبچی",
    "usernames": "ارسال یوزرنیم / تگ",
    "bots": "افزودن ربات",
    "join": "ورود عضو جدید",
    "chat": "ارسال پیام در چت",
    "media": "ارسال تمام مدیاها"
}

# ✅ alias پیش‌فرض برای هر قفل
for lock in LOCK_TYPES:
    ALIASES[f"lock_{lock}"] = [f"lock {lock}"]
    ALIASES[f"unlock_{lock}"] = [f"unlock {lock}"]

save_json_file(ALIASES_FILE, ALIASES)

# ⚙️ تابع کمکی: بروزرسانی وضعیت قفل
def set_lock_status(chat_id, lock_name, status):
    chat_id = str(chat_id)
    group = group_data.get(chat_id, {"locks": {}})
    locks = group.get("locks", {})
    locks[lock_name] = status
    group["locks"] = locks
    group_data[chat_id] = group
    save_json_file(GROUP_CTRL_FILE, group_data)

# 📊 گرفتن وضعیت قفل‌ها
def get_lock_status(chat_id, lock_name):
    chat_id = str(chat_id)
    group = group_data.get(chat_id, {"locks": {}})
    locks = group.get("locks", {})
    return locks.get(lock_name, False)

# 🔐 قفل یک بخش
async def handle_lock_generic(update, context, lock_name):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند قفل کنند!")

    chat = update.effective_chat
    chat_id = str(chat.id)
    user = update.effective_user

    if get_lock_status(chat_id, lock_name):
        return await update.message.reply_text(f"🔒 {LOCK_TYPES[lock_name]} از قبل قفل بوده است!")

    set_lock_status(chat_id, lock_name, True)
    time_str = datetime.now().strftime("%H:%M - %d/%m/%Y")
    await update.message.reply_text(
        f"🔒 <b>{LOCK_TYPES[lock_name]} قفل شد!</b>\n"
        f"📵 اعضا اجازه انجام آن را ندارند.\n\n"
        f"👤 توسط: <b>{user.first_name}</b>\n🕒 {time_str}",
        parse_mode="HTML"
    )

# 🔓 باز کردن قفل
async def handle_unlock_generic(update, context, lock_name):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند باز کنند!")

    chat = update.effective_chat
    chat_id = str(chat.id)
    user = update.effective_user

    if not get_lock_status(chat_id, lock_name):
        return await update.message.reply_text(f"🔓 {LOCK_TYPES[lock_name]} از قبل باز بوده است!")

    set_lock_status(chat_id, lock_name, False)
    time_str = datetime.now().strftime("%H:%M - %d/%m/%Y")
    await update.message.reply_text(
        f"🔓 <b>{LOCK_TYPES[lock_name]} باز شد!</b>\n"
        f"💬 اعضا اکنون می‌توانند از آن استفاده کنند.\n\n"
        f"👤 توسط: <b>{user.first_name}</b>\n🕒 {time_str}",
        parse_mode="HTML"
    )

# 🧹 بررسی و حذف پیام‌های خلاف قفل‌ها
async def check_message_locks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = str(update.effective_chat.id)
    user = update.effective_user
    message = update.message

    locks = group_data.get(chat_id, {}).get("locks", {})
    if not locks:
        return

    delete_reason = None

    # 🔍 بررسی نوع پیام
    if locks.get("links") and ("t.me/" in message.text.lower() or "http" in message.text.lower()):
        delete_reason = "ارسال لینک"
    elif locks.get("photos") and message.photo:
        delete_reason = "ارسال عکس"
    elif locks.get("videos") and message.video:
        delete_reason = "ارسال ویدیو"
    elif locks.get("files") and message.document:
        delete_reason = "ارسال فایل"
    elif locks.get("gifs") and message.animation:
        delete_reason = "ارسال گیف"
    elif locks.get("voices") and message.voice:
        delete_reason = "ارسال ویس"
    elif locks.get("vmsgs") and message.video_note:
        delete_reason = "ارسال ویدیو مسیج"
    elif locks.get("stickers") and message.sticker:
        delete_reason = "ارسال استیکر"
    elif locks.get("forward") and message.forward_from:
        delete_reason = "ارسال فوروارد"
    elif locks.get("ads") and ("join" in message.text.lower() or "channel" in message.text.lower()):
        delete_reason = "ارسال تبلیغ / تبچی"
    elif locks.get("usernames") and ("@" in message.text):
        delete_reason = "ارسال یوزرنیم یا تگ"
    elif locks.get("media") and (message.photo or message.video or message.animation):
        delete_reason = "ارسال مدیا (قفل کلی)"
    elif locks.get("chat") and message.text:
        delete_reason = "ارسال پیام متنی"

    if delete_reason:
        try:
            await message.delete()
        except:
            return

        warn_msg = await message.chat.send_message(
            f"🚫 پیام <b>{user.first_name}</b> حذف شد!\n🎯 دلیل: <b>{delete_reason}</b>",
            parse_mode="HTML"
        )

        # حذف پیام هشدار بعد از چند ثانیه برای تمیزی
        try:
            await context.application.create_task(
                context.bot.delete_message(chat_id, warn_msg.message_id)
            )
        except:
            pass

# 🧾 وضعیت همه قفل‌ها
async def handle_locks_status(update, context):
    chat_id = str(update.effective_chat.id)
    locks = group_data.get(chat_id, {}).get("locks", {})

    if not locks:
        return await update.message.reply_text("🔓 هیچ قفلی فعال نیست!", parse_mode="HTML")

    text = "🧱 <b>وضعیت قفل‌های گروه:</b>\n\n"
    for lock, desc in LOCK_TYPES.items():
        status = "🔒 فعال" if locks.get(lock, False) else "🔓 غیرفعال"
        text += f"▫️ <b>{desc}:</b> {status}\n"

    await update.message.reply_text(text, parse_mode="HTML")

# 🎮 اضافه کردن همه هندلرها به group_command_handler
async def group_command_handler(update, context):
    text = update.message.text.strip().lower()

    # alias اختصاصی تغییر نام
    if text.startswith("alias "):
        return await handle_alias(update, context)

    # وضعیت قفل‌ها
    if text in ["locks", "lock status", "وضعیت قفل"]:
        return await handle_locks_status(update, context)

    # بررسی دستورات قفل / باز کردن
    for cmd, aliases in ALIASES.items():
        if text in aliases:
            # lock_xx / unlock_xx
            for lock in LOCK_TYPES:
                if cmd == f"lock_{lock}":
                    return await handle_lock_generic(update, context, lock)
                elif cmd == f"unlock_{lock}":
                    return await handle_unlock_generic(update, context, lock)

            # بقیه دستورات (مثل بن، سکوت، ... از قبل داری)
            handlers = {
                "ban": handle_ban, "unban": handle_unban,
                "warn": handle_warn, "unwarn": handle_warn,
                "mute": handle_mute, "unmute": handle_unmute,
                "addadmin": handle_addadmin, "removeadmin": handle_removeadmin,
                "admins": handle_admins
            }
            if cmd in handlers:
                return await handlers[cmd](update, context)
    return
    # ======================= 🧠 فیلتر کلمات + تگ کاربران =======================
import json, os, re, asyncio
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

FILTER_FILE = "filters.json"
TAG_LIMIT = 5  # چند نفر در هر پیام تگ شوند

# ✅ alias‌ها
ALIASES_ADV = {
    "addfilter": ["addfilter", "addfilterword", "افزودن‌فیلتر", "فیلترکن"],
    "delfilter": ["delfilter", "removefilter", "حذف‌فیلتر", "پاک‌فیلتر"],
    "filters": ["filters", "filterlist", "لیست‌فیلتر", "فیلترها"],
    "tagall": ["tagall", "تگ‌کاربران", "تگ‌همه", "منشن‌همگانی"],
    "tagactive": ["tagactive", "تگ‌فعال", "تگ‌آنلاین"]
}

# 📁 فایل فیلترها
def load_filters():
    if os.path.exists(FILTER_FILE):
        try:
            with open(FILTER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_filters(data):
    with open(FILTER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

filters_data = load_filters()

# 🧩 بررسی مجاز بودن
async def can_manage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if user.id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ["administrator", "creator"]
    except:
        return False

# ➕ افزودن فیلتر
async def handle_addfilter(update, context):
    if not await can_manage(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند فیلتر اضافه کنند!")

    if len(context.args) < 1:
        return await update.message.reply_text("📝 استفاده: addfilter [کلمه]\nمثلاً: addfilter تبلیغ")

    word = " ".join(context.args).strip().lower()
    chat_id = str(update.effective_chat.id)
    chat_filters = filters_data.get(chat_id, [])

    if word in chat_filters:
        return await update.message.reply_text("⚠️ این کلمه از قبل در فیلتر است!")

    chat_filters.append(word)
    filters_data[chat_id] = chat_filters
    save_filters(filters_data)
    await update.message.reply_text(f"✅ کلمه <b>{word}</b> به لیست فیلتر اضافه شد.", parse_mode="HTML")

# ❌ حذف فیلتر
async def handle_delfilter(update, context):
    if not await can_manage(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if len(context.args) < 1:
        return await update.message.reply_text("📝 استفاده: delfilter [کلمه]\nمثلاً: delfilter تبلیغ")

    word = " ".join(context.args).strip().lower()
    chat_id = str(update.effective_chat.id)
    chat_filters = filters_data.get(chat_id, [])

    if word not in chat_filters:
        return await update.message.reply_text("⚠️ این کلمه در فیلتر وجود ندارد!")

    chat_filters.remove(word)
    filters_data[chat_id] = chat_filters
    save_filters(filters_data)
    await update.message.reply_text(f"🗑️ کلمه <b>{word}</b> از فیلتر حذف شد.", parse_mode="HTML")

# 📋 لیست فیلترها
async def handle_filters(update, context):
    chat_id = str(update.effective_chat.id)
    chat_filters = filters_data.get(chat_id, [])
    if not chat_filters:
        return await update.message.reply_text("ℹ️ هنوز هیچ کلمه‌ای فیلتر نشده است.")
    text = "🚫 <b>لیست کلمات فیلتر شده:</b>\n\n" + "\n".join([f"{i+1}. {w}" for i, w in enumerate(chat_filters)])
    await update.message.reply_text(text, parse_mode="HTML")

# 🧹 بررسی پیام‌ها و حذف موارد فیلترشده
async def check_filtered_messages(update, context):
    if not update.message or not update.message.text:
        return
    chat_id = str(update.effective_chat.id)
    chat_filters = filters_data.get(chat_id, [])
    text = update.message.text.lower()
    for word in chat_filters:
        if word in text:
            try:
                await update.message.delete()
                await context.bot.send_message(
                    chat_id,
                    f"🚫 پیام از <b>{update.effective_user.first_name}</b> حذف شد.\n"
                    f"🧾 دلیل: استفاده از کلمه‌ی فیلتر شده <b>{word}</b>",
                    parse_mode="HTML"
                )
            except:
                pass
            return

# 📣 تگ همه کاربران
async def handle_tagall(update, context):
    if not await can_manage(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    chat = update.effective_chat
    args_text = " ".join(context.args) if context.args else ""
    await update.message.reply_text("📣 درحال منشن همه کاربران...\n⏳ لطفاً صبر کنید.", parse_mode="HTML")

    members = []
    try:
        async for member in context.bot.get_chat_members(chat.id, limit=200):
            if not member.user.is_bot:
                members.append(member.user)
    except Exception as e:
        return await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")

    text_group = ""
    counter = 0
    for user in members:
        text_group += f"[{user.first_name}](tg://user?id={user.id}) "
        counter += 1
        if counter % TAG_LIMIT == 0:
            try:
                await context.bot.send_message(chat.id, f"{text_group}\n\n{args_text}", parse_mode="Markdown")
            except:
                pass
            await asyncio.sleep(1.5)
            text_group = ""
    if text_group:
        await context.bot.send_message(chat.id, f"{text_group}\n\n{args_text}", parse_mode="Markdown")

    await update.message.reply_text("✅ تگ همه کاربران انجام شد.", parse_mode="HTML")

# 👥 تگ کاربران فعال (آنلاین / پریمیوم)
async def handle_tagactive(update, context):
    if not await can_manage(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    chat = update.effective_chat
    args_text = " ".join(context.args) if context.args else ""
    await update.message.reply_text("👥 درحال منشن کاربران فعال...", parse_mode="HTML")

    members = []
    try:
        async for member in context.bot.get_chat_members(chat.id, limit=300):
            if not member.user.is_bot and member.user.is_premium:
                members.append(member.user)
    except Exception as e:
        return await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")

    if not members:
        return await update.message.reply_text("ℹ️ کاربر فعالی یافت نشد.")

    text_group = ""
    counter = 0
    for user in members:
        text_group += f"[{user.first_name}](tg://user?id={user.id}) "
        counter += 1
        if counter % TAG_LIMIT == 0:
            try:
                await context.bot.send_message(chat.id, f"{text_group}\n\n{args_text}", parse_mode="Markdown")
            except:
                pass
            await asyncio.sleep(1.5)
            text_group = ""
    if text_group:
        await context.bot.send_message(chat.id, f"{text_group}\n\n{args_text}", parse_mode="Markdown")

    await update.message.reply_text("✅ تگ کاربران فعال انجام شد.", parse_mode="HTML")

# 🧠 هندلر کلی (alias)
async def group_text_handler_adv(update, context):
    text = update.message.text.strip().lower()
    for cmd, aliases in ALIASES_ADV.items():
        for alias in aliases:
            if text.startswith(alias):
                args = text.replace(alias, "").strip().split()
                context.args = args
                handlers = {
                    "addfilter": handle_addfilter,
                    "delfilter": handle_delfilter,
                    "filters": handle_filters,
                    "tagall": handle_tagall,
                    "tagactive": handle_tagactive
                }
                if cmd in handlers:
                    return await handlers[cmd](update, context)
    
# ======================= 🚀 اجرای نهایی =======================

if __name__ == "__main__":
    print("🤖 خنگول فارسی 8.7 Cloud+ Supreme Pro Stable+ آماده به خدمت است ...")

    # 🧩 ساخت اپلیکیشن اصلی تلگرام
    app = ApplicationBuilder().token(TOKEN).build()

    # ⚙️ مدیریت خطاهای کلی
    app.add_error_handler(handle_error)

    # ==========================================================
    app.add_handler(CommandHandler("addsudo", add_sudo))
    app.add_handler(CommandHandler("delsudo", del_sudo))
    app.add_handler(CommandHandler("listsudos", list_sudos))
    # 💾 دستورات شخصی (ذخیره، حذف، اجرای دستورها)
    # ==========================================================
    app.add_handler(CommandHandler("save", save_command))
    app.add_handler(CommandHandler("del", delete_command))
    app.add_handler(CommandHandler("listcmds", list_commands))

    # ✉️ پیام‌های متنی غیر از کامند → هندلر دستورات ذخیره‌شده
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_command), group=-4)

    # ==========================================================
    # 👑 مدیریت وضعیت ادمین (ورود و خروج)
    # ==========================================================
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, detect_admin_movement))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, detect_admin_movement))
    # 🧹 پاکسازی خودکار دستورات گروه هنگام حذف ربات
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, handle_left_chat))

    # ==========================================================
    # 🤖 پاسخ به "ربات" توسط سودو
    # ==========================================================
    app.add_handler(MessageHandler(filters.Regex("(?i)^ربات$"), sudo_bot_call))

    # ==========================================================
    # 🔹 دستورات اصلی سیستم
    # ==========================================================
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
    app.add_handler(CommandHandler("selectivebackup", selective_backup_menu))
    app.add_handler(CallbackQueryHandler(selective_backup_buttons, pattern="^selbk_"))
    app.add_handler(CommandHandler("restore", restore))
    app.add_handler(CommandHandler("reset", reset_memory))
    app.add_handler(CommandHandler("reload", reload_memory))
    app.add_handler(CommandHandler("broadcast", broadcast))
    # 📡 اضافه کردن کنترل دستورات گروهی (بدون /)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, group_command_handler))
    # ======================= 📡 فعال‌سازی هندلرها =======================
    from telegram.ext import MessageHandler, filters

    # برای اجرای دستورات بدون /
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, group_text_handler_adv))

    # برای بررسی پیام‌های فیلتر شده
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_filtered_messages))
    # ======================= 👑 مدیریت سودوها =======================
    async def list_sudos(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in SUDO_IDS:
            return await update.message.reply_text("⛔ فقط سودوها مجازند!")

        text = "👑 <b>لیست سودوهای فعلی:</b>\n\n"
        for i, sid in enumerate(SUDO_IDS, start=1):
            text += f"{i}. <code>{sid}</code>\n"

        await update.message.reply_text(text, parse_mode="HTML")

    # ✅ اضافه‌شدن به هندلرها باید بیرون از تابع باشه
    app.add_handler(CommandHandler("cloudsync", cloudsync))
    app.add_handler(CommandHandler("leave", leave))
    app.add_handler(CommandHandler("reply", toggle_reply_mode))
    
    # ==========================================================
    # 🎨 فونت‌ساز خنگول (با حالت گفت‌وگویی و ضد اسپم گروه)
    # ==========================================================
    from telegram.ext import ConversationHandler
    from font_maker import font_maker, receive_font_name, next_font, prev_font, ASK_NAME

    # 💎 گفت‌وگوی فونت‌ساز
    font_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex(r"^فونت"), font_maker)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_font_name)],
        },
        fallbacks=[],
    )
    app.add_handler(font_handler)

    # 🔁 کنترل صفحات فونت
    app.add_handler(CallbackQueryHandler(next_font, pattern="^next_font"))
    app.add_handler(CallbackQueryHandler(prev_font, pattern="^prev_font"))
    app.add_handler(CallbackQueryHandler(feature_back, pattern="^feature_back$"))

    # ======================= 🤖 پنل ChatGPT هوش مصنوعی =======================
    from ai_chat.chatgpt_panel import show_ai_panel, chat, start_ai_chat, stop_ai_chat

    # ⚡️ ترتیب مهم است: ChatGPT باید قبل از panel_handler بیاید
    app.add_handler(CallbackQueryHandler(show_ai_panel, pattern="^panel_chatgpt$"))
    app.add_handler(CallbackQueryHandler(start_ai_chat, pattern="^start_ai_chat$"))
    app.add_handler(MessageHandler(filters.Regex("^(خاموش|/خاموش)$"), stop_ai_chat))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat), group=3)

    # ==========================================================
    # 🎉 خوشامد پویا و تنظیمات گروه
    # ==========================================================
    app.add_handler(MessageHandler(filters.Regex("^خوشامد$"), open_welcome_panel), group=-1)
    app.add_handler(CallbackQueryHandler(welcome_panel_buttons, pattern="^welcome_"), group=-1)
    app.add_handler(MessageHandler(filters.Regex("^ثبت خوشامد$"), set_welcome_text), group=-1)
    app.add_handler(MessageHandler(filters.Regex("^ثبت عکس خوشامد$"), set_welcome_media), group=-1)
    app.add_handler(MessageHandler(filters.Regex(r"^تنظیم قوانین"), set_rules_link), group=-1)
    app.add_handler(MessageHandler(filters.Regex(r"^تنظیم حذف"), set_welcome_timer), group=-1)
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome), group=-1)
    
    # ======================= 🕌 اذان =======================
    
    app.add_handler(MessageHandler(filters.Regex(r"^اذان"), get_azan_time))
    app.add_handler(MessageHandler(filters.Regex(r"^رمضان"), get_ramadan_status))
    
    # ==========================================================
    # 🌦 آب‌وهوا — باید قبل از reply و سایر MessageHandlerها باشه
    # ==========================================================
    app.add_handler(CallbackQueryHandler(show_weather, pattern="^panel_weather$"), group=-3)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, show_weather), group=-3)

    # ==========================================================
    # 🧾 راهنمای قابل ویرایش
    # ==========================================================
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.Regex("^ثبت help$"), save_help))
    app.add_handler(MessageHandler(filters.Regex("^راهنما$"), show_custom_guide))
    app.add_handler(MessageHandler(filters.Regex("^ثبت راهنما$"), save_custom_guide))
    
    # ==========================================================
    # 📂 فایل‌ها و پنل‌ها
    # ==========================================================
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document), group=1)

    # ⚠️ این باید آخرین CallbackQueryHandler باشد
    app.add_handler(CallbackQueryHandler(panel_handler))
    
    # ==========================================================
    # 🎭 پاسخ هوشمند خنگول (در انتهای اولویت)
    # ==========================================================
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply), group=2)
    # ==========================================================
    # ==========================================================
    # 🔹 وظایف استارتاپ
    # ==========================================================

    async def on_startup(app):
        await notify_admin_on_startup(app)
        app.create_task(auto_backup(app.bot))
        app.create_task(start_auto_brain_loop(app.bot))
        print("🌙 [SYSTEM] Startup tasks scheduled ✅")

    app.post_init = on_startup

    # ==========================================================
    # 🚀 اجرای نهایی ربات (بدون خطای Event loop)
    # ==========================================================
    try:
        print("🔄 در حال اجرای ربات...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"⚠️ خطا در اجرای ربات:\n{e}")
        print("♻️ ربات به‌صورت خودکار توسط هاست ری‌استارت خواهد شد ✅")
