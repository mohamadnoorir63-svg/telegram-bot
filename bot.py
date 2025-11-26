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

# 📦 ماژول‌ها

from memory_manager import (
    init_files,
    load_data,
    save_data,
    learn,
    long_learn,
    shadow_learn,
    get_reply,
    set_mode,
    get_stats,
    enhance_sentence,
    generate_sentence,
    list_phrases,
    delete_phrase,
    delete_response   # ← این خط اضافه شد
)
from welcome_module import (
    open_welcome_panel,
    welcome_panel_buttons,
    welcome_input_handler,
    welcome
)
from jokes_manager import save_joke, delete_joke, list_jokes, send_random_joke
from fortune_manager import save_fortune, list_fortunes, send_random_fortune, delete_fortune
from group_manager import register_group_activity, get_group_stats
from ai_learning import auto_learn_from_text
from smart_reply import detect_emotion, smart_response
from emotion_memory import init_emotion_memory, remember_emotion, get_last_emotion, emotion_context_reply
from auto_brain.auto_brain import start_auto_brain_loop
from selective_backup import selective_backup_menu, selective_backup_buttons
from auto_brain import auto_backup
from command_manager import (
    save_command,
    delete_command,
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

from group_control.origin_title import register_origin_title_handlers
from context_memory import ContextMemory
from brain_bridge_group import process_group_message

# 🧠 حافظه کوتاه‌مدت گفتگو برای Context AI
context_memory = ContextMemory()

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
init_files()

status = {
    "active": True,
    "learning": True,
    "welcome": True,
    "locked": False
}
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

# ────────────────────────────── پایان بخش ترجمه رپلی ──────────────────────────────
# ======================= 🧠 جلوگیری از پاسخ تکراری و پاسخ به خودش =======================
def is_valid_message(update):
    """فیلتر برای جلوگیری از پاسخ تکراری یا پاسخ به پیام‌های ربات"""
    msg = update.effective_message
    if not msg:
        return False

    # جلوگیری از پاسخ به خودش (پیام ربات)
    if msg.from_user and msg.from_user.is_bot:
        return False
        # 🚫 جلوگیری از پاسخ سخنگو به پیام‌های دستوری

        
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
            if text.lower() in ["ربات کجایی", " پینگ ؟", "کجایی ربات"]:
                return await update.message.reply_text("😄 من اینجام! فقط روی پیام‌هام ریپلای کن 💬")

            # اگر پیام ریپلای به خود ربات نبود، پاسخی نده
            if not update.message.reply_to_message or update.message.reply_to_message.from_user.id != context.bot.id:
                return True  # یعنی بقیه تابع reply اجرا نشود
    return False
# ======================= 🧾 ثبت کاربر =======================
import json
import os

USERS_FILE = "users.json"

async def register_user(user):
    """
    ذخیره آیدی و نام کاربر در فایل users.json
    """
    data = []

    # بارگذاری داده‌های موجود در صورت وجود فایل
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            data = []

    # بررسی وجود کاربر و افزودن در صورت نبود
    if user.id not in [u["id"] for u in data]:
        data.append({"id": user.id, "name": user.first_name})
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
# ======================= 🧠 شروع ساده بدون افکت =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع ساده بدون انیمیشن یا افکت"""
    from datetime import datetime
    user = update.effective_user
    now = datetime.now().strftime("%Y/%m/%d - %H:%M:%S")

    

    # نمایش مستقیم پنل اصلی
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
    ADMIN_ID = int(os.getenv("ADMIN_ID", "8588347189"))
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
                        f"🎉 خوش اومدی رئیس! مغز ربات دوباره بیدار شد 🤖✨"
                    )
                else:
                    text = (
                        f"👑 <b>سازنده‌ی ربات وارد گروه شد!</b>\n"
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
            f"🕯️ تا بازگشت دوباره‌ی ربات در حالت خودکار می‌مونیم."
        )
        await message.reply_text(text, parse_mode="HTML")

# ==========================================================
# 🤖 پاسخ ویژه برای سازنده (سودو اصلی)
# ==========================================================
import os
import random
from telegram import Update
from telegram.ext import ContextTypes

async def sudo_bot_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """وقتی سازنده پیام «ربات» بفرسته — پاسخ‌های مخصوص فقط برای سودو اصلی"""
    ADMIN_ID = int(os.getenv("ADMIN_ID", "8588347189"))
    user_id = update.effective_user.id

    # 🚫 فقط برای ادمین اصلی (سودو)
    if user_id != ADMIN_ID:
        return

    replies = [
        "👑 جانم سودو؟ 😎",
        "🤖 در خدمتتم رئیس!",
        "⚡ بفرما قربان!",
        "🧠 گوش به فرمانتم!",
        "✨ دستور بده شاه !",
        "😄 آماده‌م برای هر کاری!",
        "🔥 بگو رئیس، منتظرم!"
    ]

    # 🎲 انتخاب تصادفی پاسخ
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
# حافظه وضعیت گروه‌ها
GROUP_STATUS = {}  # chat_id: {"active": True, "welcome": True, "locked": False}

# تابع کمکی برای گرفتن یا ساخت وضعیت گروه
def get_group_status(chat_id: int):
    if chat_id not in GROUP_STATUS:
        # پیش‌فرض سخنگو خاموش، بقیه روشن
        GROUP_STATUS[chat_id] = {"active": False, "welcome": True, "locked": True}
    return GROUP_STATUS[chat_id]

# ────────────── خاموش/روشن سخنگو برای هر گروه ──────────────
async def mute_speaker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """خاموش کردن سخنگو فقط برای این گروه"""
    chat_id = update.effective_chat.id
    status = get_group_status(chat_id)
    status["active"] = False
    await update.message.reply_text(
        "😴 سخنگو خاموش شد!\n(جوک و فال همچنان فعال هستند)"
    )

async def unmute_speaker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """روشن کردن سخنگو فقط برای این گروه"""
    chat_id = update.effective_chat.id
    status = get_group_status(chat_id)
    status["active"] = True
    await update.message.reply_text(
        "✅ سخنگو روشن شد!\n(همه پیام‌ها پاسخ داده می‌شوند)"
    )

async def toggle_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فعال/غیرفعال کردن خوشامد فقط برای این گروه"""
    chat_id = update.effective_chat.id
    status = get_group_status(chat_id)
    status["welcome"] = not status["welcome"]
    await update.message.reply_text(
        "👋 خوشامد فعال شد!" if status["welcome"] else "🚫 خوشامد غیرفعال شد!"
    )

async def lock_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قفل یادگیری فقط برای این گروه"""
    chat_id = update.effective_chat.id
    status = get_group_status(chat_id)
    status["locked"] = True
    await update.message.reply_text("🔒 یادگیری قفل شد!")

async def unlock_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """باز کردن یادگیری فقط برای این گروه"""
    chat_id = update.effective_chat.id
    status = get_group_status(chat_id)
    status["locked"] = False
    await update.message.reply_text("🔓 یادگیری باز شد!")
    
# ======================= 📊 آمار ربات واقعی =======================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار کلی — فقط برای مدیر اصلی یا سودوها"""
    ADMIN_ID = int(os.getenv("ADMIN_ID", "8588347189"))
    user = update.effective_user
    user_id = user.id

    # ✅ فقط مدیر اصلی یا سودوها مجازند
    if user_id != ADMIN_ID and user_id not in SUDO_IDS:
        return await update.message.reply_text("⛔ فقط مدیر اصلی یا سودوها اجازه مشاهده آمار را دارند.")

    # 🧠 دریافت اطلاعات از حافظه و فایل گروه‌ها
    data = get_stats()
    groups_data = load_data("group_data.json").get("groups", [])

    # ✅ شمارش گروه‌ها (سازگار با دیکشنری یا لیست)
    groups = len(groups_data) if isinstance(groups_data, (dict, list)) else 0

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
        f"📊 <b> آمار کلی ربات:</b>\n\n"
        f"👤 کاربران واقعی: <b>{users}</b>\n"
        f"👥 گروه‌های فعال: <b>{groups}</b>\n"
        f"🧩 جملات ذخیره‌شده: <b>{data['phrases']}</b>\n"
        f"💬 پاسخ‌های یادگرفته: <b>{data['responses']}</b>\n"
        f"🎭 مود فعلی: <b>{data['mode']}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📨 <i>درخواست توسط:</i> <b>{user.first_name}</b> (<code>{user_id}</code>)"
    )

    await update.message.reply_text(msg, parse_mode="HTML")


# ======================= 📊 آمار کامل گروه‌ها (فقط برای مدیر اصلی و سودوها) =======================
async def fullstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار فقط برای گروه‌ها — فقط مدیر اصلی و سودوها"""
    ADMIN_ID = int(os.getenv("ADMIN_ID", "8588347189"))
    user = update.effective_user
    user_id = user.id

    # ✅ فقط مدیر اصلی یا سودوها مجازند
    if user_id != ADMIN_ID and user_id not in SUDO_IDS:
        return await update.message.reply_text("⛔ فقط مدیر اصلی یا سودوها اجازه مشاهده آمار کامل گروه‌ها را دارند.")

    try:
        data = load_data("group_data.json")
        groups = data.get("groups", {})

        text = "📈 <b>آمار کامل گروه‌ها:</b>\n\n"

        # ✅ حالت 1: اگر groups لیست باشه
        if isinstance(groups, list):
            valid_groups = [g for g in groups if str(g.get("id", "")).startswith("-")]
            if not valid_groups:
                return await update.message.reply_text("ℹ️ هنوز هیچ گروهی ثبت نشده.", parse_mode="HTML")
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

                text += (
                    f"🏠 <b>گروه:</b> {title}\n"
                    f"👥 <b>اعضا:</b> {members}\n"
                    f"🕓 <b>آخرین فعالیت:</b> {last_active}\n\n"
                )

        # ✅ حالت 2: اگر groups دیکشنری باشه
        elif isinstance(groups, dict):
            valid_items = {gid: info for gid, info in groups.items() if str(gid).startswith("-")}
            if not valid_items:
                return await update.message.reply_text("ℹ️ هنوز هیچ گروهی ثبت نشده.", parse_mode="HTML")
            for gid, info in valid_items.items():
                title = info.get("title", f"Group_{gid}")
                members = len(info.get("members", []))
                last_active = info.get("last_active", "نامشخص")

                try:
                    chat = await context.bot.get_chat(gid)
                    title = chat.title or title
                except:
                    pass

                text += (
                    f"🏠 <b>گروه:</b> {title}\n"
                    f"👥 <b>اعضا:</b> {members}\n"
                    f"🕓 <b>آخرین فعالیت:</b> {last_active}\n\n"
                )

        else:
            return await update.message.reply_text("⚠️ ساختار فایل group_data.json نامعتبر است!", parse_mode="HTML")

        # جلوگیری از پیام بیش از حد طولانی
        if len(text) > 4000:
            text = text[:3990] + "..."

        await update.message.reply_text(text, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در آمار گروه‌ها:\n{e}")
# ======================= 👋 سیستم خوشامد پویا برای هر گروه =======================

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
ADMIN_ID = int(os.getenv("ADMIN_ID", "8588347189"))

# ======================= ⚙️ توابع اصلی =======================
def _should_include_in_backup(path: str) -> bool:
    """فقط فایل‌های مهم داخل بک‌آپ بروند"""
    lowered = path.lower()
    skip_dirs = ["__pycache__", ".git", "venv", "restore_temp", BACKUP_FOLDER]
    
    # ۱. بررسی پوشه‌هایی که نباید شامل شوند
    if any(sd in lowered for sd in skip_dirs):
        return False
    
    # ۲. بررسی فایل‌های ZIP یا فایل‌های بک‌آپ خودکار
    if lowered.endswith(".zip") or os.path.basename(lowered).startswith("backup_"):
        return False
    
    if os.path.basename(path) in [
        "data/custom_commands.json",
        "custom_commands_backup.json"
]:
        return True
    
    # ۴. فایل‌های مهم دیگر بر اساس پسوند
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

        # 🧩 فایل‌ها و پوشه‌های مهم برای بازیابی
        important_files = [
        "memory.json",
        "group_data.json",
        "jokes.json",
        "fortunes.json",
        "aliases.json",
        "data/members.json",
        "users.json",

        # مسیر اصلی
        "group_control/aliases.json",

        # پوشه رسانه فال‌ها
        "fortunes_media",

        
        "custom_commands_backup.json",
        "data/custom_commands.json"
        ]

        moved_any = False
        for fname in important_files:
            src = os.path.join(restore_dir, fname)
            dest = fname
            dest_dir = os.path.dirname(dest)

            if os.path.exists(src):
                if os.path.isdir(src):
                    # اگر src یک پوشه است، کل محتواش منتقل شود
                    if not os.path.exists(dest):
                        os.makedirs(dest, exist_ok=True)
                    for root, _, files in os.walk(src):
                        for file in files:
                            file_src = os.path.join(root, file)
                            rel_path = os.path.relpath(file_src, src)
                            file_dest = os.path.join(dest, rel_path)
                            os.makedirs(os.path.dirname(file_dest), exist_ok=True)
                            shutil.move(file_src, file_dest)
                    moved_any = True
                    print(f"♻️ بازیابی پوشه: {fname}")
                else:
                    # اگر فایل معمولی است
                    if dest_dir and not os.path.exists(dest_dir):
                        os.makedirs(dest_dir, exist_ok=True)
                    shutil.move(src, dest)
                    moved_any = True
                    print(f"♻️ بازیابی فایل: {fname}")

        # 🔁 بازسازی حافظه‌ها
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

    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    lower_text = text.lower()

    # 🧠 گرفتن وضعیت گروه (قبل از هر استفاده)
    status = get_group_status(chat_id)

    # 🧠 ثبت پیام در حافظه کوتاه‌مدت
    context_memory.add_message(uid, text)

    # 🧠 گرفتن کل تاریخچه اخیر کاربر
    recent_context = context_memory.get_context(uid)
    
   # 🧩 ترکیب سه پیام آخر برای درک بهتر ادامه گفتگو
    full_context = " ".join(recent_context[-3:]) if recent_context else text


    # 🚫 جلوگیری از پاسخ در پیوی (فقط جوک و فال مجازند)
    if update.effective_chat.type == "private" and lower_text not in ["جوک", "فال"]:
        return

    if re.search(r"(هوای|آب[\s‌]*و[\s‌]*هوا)", text):
        return

    # حافظه کوتاه برای جلوگیری از تکرار
    global LAST_MESSAGES
    if "LAST_MESSAGES" not in globals():
        LAST_MESSAGES = {}

    last_msg = LAST_MESSAGES.get(uid)
    if last_msg == text:
        return False  # پیام تکراری → پاسخ نده

    # تابع کمکی برای بررسی پیام معتبر
    def is_valid_message(update):
        """فیلتر برای جلوگیری از پاسخ تکراری یا پاسخ به پیام‌های ربات"""
        msg = update.effective_message
        if not msg:
            return False

        # ✅ جلوگیری از پاسخ به دستورات خاص (مثل راهنما، خوشامد، ربات و غیره)
        protected_words = [
            "راهنما", "ثبت راهنما", "خوشامد", "ثبت خوشامد",
            "save", "del", "panel", "backup", "cloudsync", "leave"
        ]
        if any(lower_text.startswith(word) for word in protected_words):
            return False

        return True

    if not is_valid_message(update):
        return

    # 🧠 بررسی حالت ریپلی مود گروهی
    if await handle_group_reply_mode(update, context):
        return

    # ثبت کاربر و گروه
    await register_user(update.effective_user)
    register_group_activity(chat_id, uid)

    # یادگیری خودکار و شرایط فعال/غیر فعال
    if not status["locked"]:
        auto_learn_from_text(text)

    # اگر سخنگو خاموش است → فقط پاسخ هوش مصنوعی غیرفعال شود
    # دستورات (جوک، فال، یادبگیر، مدیریت،…) همچنان کار می‌کنند
    if not status["active"]:
        if lower_text not in ["جوک", "فال" ,"ربات" ,"یادبگیر"]:
            return

    # ادامه‌ی منطق پاسخ‌دهی هوش مصنوعی...
        
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
            f"🤖 درصد هوش فعلی خنگول: *{score}%*\n\n"
            + "\n".join(details)
            + f"\n\n📈 نسخه Cloud+ Supreme Pro Stable+\n🕓 {datetime.now().strftime('%Y/%m/%d %H:%M')}"
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
        return

    # ✅ هوش کلی (ترکیب هوش منطقی + اجتماعی)
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

    # 🗑️ حذف جوک و فال
    if text.lower() == "حذف جوک" and update.message.reply_to_message:
        await delete_joke(update)
        return

    if text.lower() == "حذف فال" and update.message.reply_to_message:
        await delete_fortune(update)
        return
        
        # ✅ لیست‌ها
    if text.strip() in ["لیست جوک", "لیست جوک‌ها", "لیست جوک‌", "لیست جوکها"]:
        await list_jokes(update)
        return

    if text.strip() in ["لیست فال", "لیست فال‌ها", "لیست فال‌", "لیست فالها"]:
        await list_fortunes(update)
        return


    # ✅ لیست جملات
    if text == "لیست":
        await update.message.reply_text(list_phrases(), parse_mode="HTML")
        return
        # ✅ حذف جمله یا جملات از حافظه
    if text.startswith("حذف جمله"):
        phrase = text[len("حذف جمله"):].strip()  # مطمئن می‌شویم فاصله اضافی حذف شود
        if not phrase:
            await update.message.reply_text(
                "❗ لطفاً جمله‌ای برای حذف جمله بنویس.\n\n"
                "📘 مثال:\n"
                "<code>حذف جمله سلام</code>\n"
                "یا برای حذف چند جمله مشابه:\n"
                "<code>حذف جمله سلام*</code>",
                parse_mode="HTML"
            )
            return

        # بررسی ستاره برای حذف جزئی
        partial = False
        if phrase.endswith("*"):
            partial = True
            phrase = phrase[:-1].strip()

        msg = delete_phrase(phrase, partial=partial)
        await update.message.reply_text(msg, parse_mode="HTML")
        return
        # ✅ حذف پاسخ مشخص
    if text.startswith("حذف پاسخ "):
        response_text = text[len("حذف پاسخ"):].strip()
        if not response_text:
            await update.message.reply_text(
                "❗ لطفاً متنی برای حذف پاسخ بنویس.\n\n"
                "📘 مثال:\n"
                "<code>حذف پاسخ علیک</code>",
                parse_mode="HTML"
            )
            return

        msg = delete_response(response_text)
        await update.message.reply_text(msg, parse_mode="HTML")
        return

        # اگر کاربر ستاره گذاشته باشد یعنی حذف جزئی (partial)
        partial = phrase.endswith("*")
        if partial:
            phrase = phrase[:-1].strip()

        msg = delete_phrase(phrase, partial=partial)
        await update.message.reply_text(msg, parse_mode="HTML")
        return
        # ✅ یادگیری چندخطی (طولانی یادبگیر)
    if text.startswith("طولانی یادبگیر "):
        parts = text.replace("طولانی یادبگیر ", "").split("\n")

        if len(parts) > 1:
            phrase = parts[0].strip()
            lines = [p.strip() for p in parts[1:] if p.strip()]
            msg = long_learn(phrase, *lines)

            visual = (
                f"🧠 <b>یادگیری چندخطی انجام شد!</b>\n"
                f"💬 <b>جمله:</b> <code>{phrase}</code>\n"
                f"📜 <b>تعداد خطوط:</b> {len(lines)}\n"
                f"➕ <i>{msg}</i>"
            )

            await update.message.reply_text(visual, parse_mode="HTML")
        else:
            await update.message.reply_text(
                "❗ بعد از 'طولانی یادبگیر' جمله‌ی اصلی و متن چندخطی رو بنویس.\n\n"
                "📘 مثال:\n"
                "<code>طولانی یادبگیر بیو\n"
                "ای پادشاه خوبان داد از غم تنهایی دل بی\n"
                "دل بی‌تو به جان آمد ❤️</code>",
                parse_mode="HTML"
            )
        return

    # ✅ یادگیری دستی با استایل زیبا و خروجی حرفه‌ای
    if text.startswith("یادبگیر "):
        parts = text.replace("یادبگیر ", "").split("\n")

        if len(parts) > 1:
            phrase = parts[0].strip()
            responses = [p.strip() for p in parts[1:] if p.strip()]
            msg = learn(phrase, *responses)

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

    loading_text = "🧠 <b>در حال پاکسازی کامل مغز ربات...</b>\n"
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

    files_to_remove = ["memory.json", "group_data.json","data/custom_commands.json", "stickers.json", "jokes.json", "fortunes.json", "users.json"]

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
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Message
from telegram.ext import ContextTypes
import os, json, asyncio

USERS_FILE = "users.json"

# -------------------- دستور broadcast --------------------
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی می‌تونه پیام همگانی بفرسته!")

    # پیام ریپلی شده
    reply_msg: Message = update.message.reply_to_message
    if reply_msg:
        msg_text = reply_msg.text or reply_msg.caption or ""
        msg_media = reply_msg
    else:
        msg_text = " ".join(context.args)
        msg_media = None

    if not msg_text and not msg_media:
        return await update.message.reply_text("❗ بعد از /broadcast پیام مورد نظر رو بنویس یا روی پیام ریپلی کن.")

    # منوی انتخاب نوع ارسال
    keyboard = [
        [InlineKeyboardButton("📨 فقط پیوی‌ها", callback_data=f"broadcast_pv")],
        [InlineKeyboardButton("🏠 فقط گروه‌ها", callback_data=f"broadcast_groups")],
        [InlineKeyboardButton("🌐 همه", callback_data=f"broadcast_all")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # ذخیره موقت در context.user_data برای دکمه‌ها
    context.user_data["broadcast"] = {"text": msg_text, "media": msg_media}

    await update.message.reply_text(
        "لطفاً نوع ارسال همگانی را انتخاب کنید:", 
        reply_markup=reply_markup
    )

# -------------------- هندلر دکمه‌ها --------------------
async def broadcast_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mode = query.data  # فقط broadcast_pv / broadcast_groups / broadcast_all

    if "broadcast" not in context.user_data:
        return await query.edit_message_text("⚠️ داده‌ای برای ارسال پیدا نشد!")

    msg_data = context.user_data.pop("broadcast")
    msg_text = msg_data.get("text")
    msg_media: Message = msg_data.get("media")

    # بارگذاری کاربران
    users, user_names = [], []
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                users = [u["id"] for u in data]
                user_names = [u.get("name", str(u["id"])) for u in data]
        except:
            pass

    # بارگذاری گروه‌ها
    group_ids, group_names = [], []
    groups_data = load_data("group_data.json").get("groups", {})
    if isinstance(groups_data, dict):
        for gid, info in groups_data.items():
            group_ids.append(int(gid))
            group_names.append(info.get("title", f"Group_{gid}"))
    elif isinstance(groups_data, list):
        for g in groups_data:
            if "id" in g:
                group_ids.append(int(g["id"]))
                group_names.append(g.get("title", f"Group_{g['id']}"))

    # تعیین لیست هدف
    targets = []
    if mode == "broadcast_pv":
        targets = [(uid, "user") for uid in users]
    elif mode == "broadcast_groups":
        targets = [(gid, "group") for gid in group_ids]
    elif mode == "broadcast_all":
        targets = [(uid, "user") for uid in users] + [(gid, "group") for gid in group_ids]

    if not targets:
        return await query.edit_message_text("⚠️ هیچ گیرنده‌ای پیدا نشد!")

    # پیام پیشرفت
    sent, failed = 0, 0
    total = len(targets)
    progress_msg = await query.edit_message_text(f"📨 در حال ارسال... 0%")

    for idx, (cid, ctype) in enumerate(targets, start=1):
        try:
            if msg_media:
                # ارسال پیام ریپلی (متن + مدیا)
                if msg_media.text:
                    await context.bot.send_message(chat_id=cid, text=msg_media.text)
                elif msg_media.photo:
                    await context.bot.send_photo(chat_id=cid, photo=msg_media.photo[-1].file_id, caption=msg_media.caption)
                elif msg_media.video:
                    await context.bot.send_video(chat_id=cid, video=msg_media.video.file_id, caption=msg_media.caption)
                # می‌تونی انواع مدیا دیگر هم اضافه کنی (animation, document, audio ...)
            else:
                await context.bot.send_message(chat_id=cid, text=msg_text)
            sent += 1
        except:
            failed += 1

        # بروزرسانی پیشرفت هر ۱۰٪
        percent = int(idx / total * 100)
        if percent % 10 == 0 or percent == 100:
            try:
                await progress_msg.edit_text(
                    f"📨 در حال ارسال...\n"
                    f"👤 کاربران: {len(users)} | 👥 گروه‌ها: {len(group_ids)}\n"
                    f"📊 پیشرفت: {percent}%"
                )
            except:
                pass
        await asyncio.sleep(0.3)  # جلوگیری از Flood تلگرام

    # نمایش نتیجه نهایی با نمونه
    example_users = "، ".join(user_names[:3]) if user_names else "—"
    example_groups = "، ".join(group_names[:3]) if group_names else "—"

    await progress_msg.edit_text(
        "✅ ارسال همگانی انجام شد!\n\n"
        f"👤 کاربران: <b>{len(users)}</b>\n"
        f"👥 گروه‌ها: <b>{len(group_ids)}</b>\n"
        f"📦 مجموع گیرندگان: <b>{total}</b>\n"
        f"📤 موفق: <b>{sent}</b>\n"
        f"⚠️ ناموفق: <b>{failed}</b>\n\n"
        f"👤 نمونه کاربران: <i>{example_users}</i>\n"
        f"🏠 نمونه گروه‌ها: <i>{example_groups}</i>",
        parse_mode="HTML"
    )

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
import aiofiles, os, asyncio
from datetime import datetime
from modules.azan_module import get_azan_time  # ✅ اضافه برای اذان

TEXTS_PATH = "texts"

async def load_text(file_name, default_text):
    path = os.path.join(TEXTS_PATH, file_name)
    if os.path.exists(path):
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            return await f.read()
    return default_text


# ======================= 🎛 پنل اصلی خنگول =======================
from datetime import datetime

async def show_main_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    user_first_name = update.effective_user.first_name
    now = datetime.now().strftime("%Y/%m/%d - %H:%M:%S")

    about = (
        f"🌙 <b>به منوی اصلی ربات خوش آمدی {user_first_name}!</b>\n"
        f"📅 {now}\n"
        f"از دکمه‌های زیر یکی رو انتخاب کن 😎"
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
            InlineKeyboardButton("🤖 راهنمای ربات", callback_data="panel_about"),
            InlineKeyboardButton("👨‍💻 درباره تیم ما", callback_data="panel_team")
        ],
        [
            InlineKeyboardButton("🔮 فال امروز", callback_data="panel_fortune"),
            InlineKeyboardButton("😂 جوک خنده‌دار", callback_data="panel_joke")
        ],
        [
            InlineKeyboardButton("🎨 فونت‌ساز حرفه‌ای", callback_data="panel_font"),
            InlineKeyboardButton("💳 آیدی من", callback_data="panel_stats")
        ],
        [
            InlineKeyboardButton("🧠 گفتگوی ChatGPT", callback_data="panel_chatgpt")
        ],
        [
            InlineKeyboardButton("🌤 آب و هوا", callback_data="panel_weather"),
            InlineKeyboardButton("🕌 اوقات شرعی / اذان", callback_data="panel_azan")
        ]
    ]

    markup = InlineKeyboardMarkup(keyboard)

    if edit:
        await update.callback_query.edit_message_text(
            about, reply_markup=markup, parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            about, reply_markup=markup, parse_mode="HTML"
        )

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
        user = query.from_user
        now = datetime.now().strftime("%Y/%m/%d - %H:%M:%S")

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
        await query.message.reply_text(
            "🕌 برای دیدن اوقات شرعی بنویس:\n<b>اذان هرات</b> یا <b>اذان تهران</b>یا برای دیدن روز های مذهبی<b>رمضان</b>",
            parse_mode="HTML"
        )

    elif query.data == "panel_ramadan":
        # ✅ نمایش وضعیت رمضان و تاریخ‌های قمری/شمسی/میلادی
        await get_ramadan_status(update, context)

    elif query.data == "panel_fortune":
        await query.message.reply_text("🔮 لطفاً کلمه فال رو بفرستید تا فال ارسال شود:\n<b> فال </b>", parse_mode="HTML")

    elif query.data == "panel_joke":
        await query.message.reply_text("🎭 لطفاً کلمه جوک رو بفرستید تا جوک ارسال شود:\n<b> جوک </b>", parse_mode="HTML")
        
    elif query.data == "panel_font":
        await query.message.reply_text("🎨 برای ساخت فونت بنویس:\n<b> فونت اسمت </b>", parse_mode="HTML")

    elif query.data == "back_main":
        await show_main_panel(update, context, edit=True)

# ======================= ☁️ پاسخ به نام شهر برای اذان =======================
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

    # ⚙️ مدیریت خطاهای کلی
    application.add_error_handler(handle_error)
    
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

application.add_handler(
    MessageHandler(filters.TEXT & (~filters.COMMAND) & filters.Regex(r"^ترجمه به"), translate_reply_handler),
    group=-9
)
# ==========================================================
#پیام‌های متنی غیر از کامند → هندلر دستورات ذخیره‌شده
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_command), group=-4)

# ==========================================================
# 👑 مدیریت وضعیت ادمین (ورود و خروج)
# ==========================================================
application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, detect_admin_movement))
application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, detect_admin_movement))
application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, handle_left_chat))

application.add_handler(
    MessageHandler(filters.Regex("(?i)^ربات$"), sudo_bot_call),
    group=-8
)

# ==========================================================
# 🔹 دستورات اصلی سیستم
# ==========================================================
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("welcome", toggle_welcome))
application.add_handler(CommandHandler("lock", lock_learning))
application.add_handler(CommandHandler("unlock", unlock_learning))
application.add_handler(CommandHandler("mode", mode_change))

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

# ==========================================================
# 📊 آمار، بک‌آپ و کنترل
# ==========================================================
application.add_handler(CommandHandler("mute", mute_speaker))
application.add_handler(CommandHandler("unmute", unmute_speaker))
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
application.add_handler(CommandHandler("reply", toggle_reply_mode))

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
# ==========================================================
# 🤖 پنل ChatGPT هوش مصنوعی
# ==========================================================
from ai_chat.chatgpt_panel import show_ai_panel, chat, start_ai_chat, stop_ai_chat
application.add_handler(CallbackQueryHandler(show_ai_panel, pattern="^panel_chatgpt$"), group=3)
application.add_handler(CallbackQueryHandler(start_ai_chat, pattern="^start_ai_chat$"), group=3)
application.add_handler(MessageHandler(filters.Regex("^(خاموش|/خاموش)$"), stop_ai_chat), group=3)
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat), group=3)

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
# 🎭 سخنگوی خنگول (پاسخ معمولی)
# ==========================================================
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply), group=5)

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
    loop.create_task(start_userbot())       # اجرای یوزربات جانبی همزمان

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
