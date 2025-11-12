import os
import json
import random
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters, CallbackQueryHandler

# ================= ⚙️ تنظیمات اولیه =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACTIVITY_FILE = os.path.join(BASE_DIR, "activity.json")
SUDO_IDS = [8588347189]

if not os.path.exists(ACTIVITY_FILE):
    with open(ACTIVITY_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

# ---------- یوزربات ----------
try:
    from userbot_module.userbot import client as userbot_client
except ImportError:
    userbot_client = None  # اگر یوزربات نصب نبود

# ================= 📁 توابع کمکی =================
def _load_activity():
    try:
        with open(ACTIVITY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def _save_activity(data):
    with open(ACTIVITY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================= 🔐 بررسی دسترسی =================
async def _has_access(context, chat_id, user_id):
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False

# ================= 🧾 ثبت فعالیت کاربران =================
async def record_user_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not msg or chat.type not in ("group", "supergroup") or user.is_bot:
        return

    data = _load_activity()
    chat_key = str(chat.id)
    if chat_key not in data:
        data[chat_key] = {}
    data[chat_key][str(user.id)] = datetime.utcnow().timestamp()
    _save_activity(data)

# ================= 👥 آماده سازی تگ با یوزربات =================
async def fetch_users_via_userbot(chat_id):
    participants = []
    if userbot_client:
        try:
            members = await userbot_client.get_participants(chat_id)
            participants.extend([m for m in members if not m.bot])
        except:
            pass
    return participants

# ================= 👥 ساخت پنل تگ =================
def build_tag_panel():
    keyboard = [
        [InlineKeyboardButton("تگ کاربران مقام دار", callback_data="tag_admins")],
        [InlineKeyboardButton("تگ کردن 50 کاربر بدون مقام", callback_data="tag_50")],
        [InlineKeyboardButton("تگ کردن 300 کاربر بدون مقام", callback_data="tag_300")],
        [InlineKeyboardButton("تگ کردن 500 کاربر گروه", callback_data="tag_500")],
        [InlineKeyboardButton("بستن", callback_data="close_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ================= 👥 هندلر باز کردن پنل =================
async def open_tag_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not await _has_access(context, chat.id, user.id):
        # پیام فقط برای کاربر ارسال شود (PM-like)
        return await msg.reply_text("🚫 فقط مدیران یا سودوها مجاز به استفاده از این پنل هستند!", quote=True)

    # پیام پنل هم فقط برای کاربر ارسال شود
    await msg.reply_text("• حالت تگ کردن را انتخاب کنید :", reply_markup=build_tag_panel(), quote=True)

# ================= 👥 هندلر کلیک روی پنل =================
async def handle_tag_panel_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    chat = query.message.chat
    await query.answer()

    # فقط اجازه برای مدیر یا سودو
    if not await _has_access(context, chat.id, user.id):
        return await query.answer("🚫 فقط مدیران یا سودوها مجاز هستند!", show_alert=True)

    mentions = []

    if query.data == "close_panel":
        await query.message.delete()
        return

    # ---------- تگ کاربران مقام دار ----------
    elif query.data == "tag_admins":
        try:
            admins = await context.bot.get_chat_administrators(chat.id)
            mentions = [f"[{a.user.first_name}](tg://user?id={a.user.id})" for a in admins if not a.user.is_bot]
        except:
            await query.message.edit_text("⚠️ خطا در دریافت مدیران گروه")
            return

    # ---------- تگ تعداد مشخص کاربران بدون مقام ----------
    elif query.data in ("tag_50", "tag_300", "tag_500"):
        count_map = {"tag_50": 50, "tag_300": 300, "tag_500": 500}
        count = count_map[query.data]

        participants = await fetch_users_via_userbot(chat.id)
        if not participants:
            participants = []
            try:
                members = await context.bot.get_chat_administrators(chat.id)
                participants = [m.user for m in await context.bot.get_chat(chat.id).get_members() if not m.user.is_bot]
            except:
                participants = []

        if participants:
            sample = random.sample(participants, min(count, len(participants)))
            mentions = [f"[{m.first_name}](tg://user?id={m.id})" for m in sample]

    # ---------- ارسال تگ روی ربات اصلی ----------
    if mentions:
        chunk_size = 20
        for i in range(0, len(mentions), chunk_size):
            chunk = mentions[i:i + chunk_size]
            await query.message.reply_text("👥 " + " ".join(chunk), parse_mode="Markdown")
            await asyncio.sleep(1)

# ================= 🔧 ثبت هندلرها =================
def register_tag_handlers(application, group_number: int = 14):
    application.add_handler(
        MessageHandler(
            filters.Regex(r"^(تگ)$") & filters.ChatType.GROUPS,
            open_tag_panel,
        ),
        group=group_number,
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_tag_panel_click,
            pattern=r"^tag_.*|close_panel$"
        ),
        group=group_number + 1,
    )
    application.add_handler(
        MessageHandler(
            filters.ALL & filters.ChatType.GROUPS,
            record_user_activity,
        ),
        group=group_number + 2,
    )
