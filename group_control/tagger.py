import os
import json
import random
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, CallbackQueryHandler, filters

# ================= ⚙️ تنظیمات اولیه =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACTIVITY_FILE = os.path.join(BASE_DIR, "activity.json")
SUDO_IDS = [8588347189]  # آیدی سودوها

# ---------- یوزربات ----------
try:
    from userbot_module.userbot import client as userbot_client
except ImportError:
    userbot_client = None  # اگر یوزربات نصب نبود، فقط ربات اصلی فعال می‌ماند

if not os.path.exists(ACTIVITY_FILE):
    with open(ACTIVITY_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

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

# ================= 👥 آماده سازی تگ روی یوزربات بدون ارسال =================
async def send_tag_via_userbot(mentions, chat_id):
    # یوزربات سکوت می‌کند
    return

# ================= 📝 ساخت پنل تگ =================
def get_tag_panel():
    keyboard = [
        [InlineKeyboardButton("تگ کاربران مقام دار", callback_data="tag_admins")],
        [InlineKeyboardButton("تگ کردن 50 کاربر بدون مقام", callback_data="tag_50")],
        [InlineKeyboardButton("تگ کردن 300 کاربر بدون مقام", callback_data="tag_300")],
        [InlineKeyboardButton("تگ کردن 500 کاربر گروه", callback_data="tag_500")],
        [InlineKeyboardButton("تگ کاربران فعال", callback_data="tag_active")],
        [InlineKeyboardButton("تگ کاربران غیر فعال", callback_data="tag_inactive")],
        [InlineKeyboardButton("بستن", callback_data="close_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ================= 🧩 هندلر فرمان باز کردن پنل =================
async def show_tag_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not await _has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها مجاز به استفاده از این دستور هستند!")

    await msg.reply_text("• حالت تگ کردن را انتخاب کنید :", reply_markup=get_tag_panel())

# ================= 🧩 هندلر کلیک روی دکمه‌های پنل =================
async def handle_tag_panel_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = _load_activity()
    chat_id = query.message.chat_id
    mentions = []

    if query.data == "close_panel":
        await query.edit_message_text("پنل بسته شد.")
        return

    # ---------- تگ کاربران مقام دار ----------
    elif query.data == "tag_admins":
        try:
            admins = await context.bot.get_chat_administrators(chat_id)
            mentions = [f"[{a.user.first_name}](tg://user?id={a.user.id})" for a in admins if not a.user.is_bot]
        except:
            await query.message.reply_text("⚠️ خطا در دریافت مدیران گروه")

    # ---------- تگ 50 کاربر بدون مقام ----------
    elif query.data == "tag_50":
        participants = await get_group_members(context, chat_id)
        mentions = [f"[{m.first_name}](tg://user?id={m.id})" for m in participants[:50]]

    # ---------- تگ 300 کاربر بدون مقام ----------
    elif query.data == "tag_300":
        participants = await get_group_members(context, chat_id)
        mentions = [f"[{m.first_name}](tg://user?id={m.id})" for m in participants[:300]]

    # ---------- تگ 500 کاربر بدون مقام ----------
    elif query.data == "tag_500":
        participants = await get_group_members(context, chat_id)
        mentions = [f"[{m.first_name}](tg://user?id={m.id})" for m in participants[:500]]

    # ---------- تگ کاربران فعال ----------
    elif query.data == "tag_active":
        chat_data = data.get(str(chat_id), {})
        now = datetime.utcnow().timestamp()
        active_users = [uid for uid, t in chat_data.items() if now - t <= 24*3600]
        for uid in active_users:
            try:
                member = await context.bot.get_chat_member(chat_id, int(uid))
                if not member.user.is_bot:
                    mentions.append(f"[{member.user.first_name}](tg://user?id={member.user.id})")
            except:
                continue

    # ---------- تگ کاربران غیر فعال ----------
    elif query.data == "tag_inactive":
        chat_data = data.get(str(chat_id), {})
        now = datetime.utcnow().timestamp()
        inactive_users = [uid for uid, t in chat_data.items() if now - t > 24*3600]
        for uid in inactive_users:
            try:
                member = await context.bot.get_chat_member(chat_id, int(uid))
                if not member.user.is_bot:
                    mentions.append(f"[{member.user.first_name}](tg://user?id={member.user.id})")
            except:
                continue

    # ارسال تگ‌ها
    if mentions:
        chunk_size = 20
        for i in range(0, len(mentions), chunk_size):
            chunk = mentions[i:i + chunk_size]
            await query.message.reply_text("👥 " + " ".join(chunk), parse_mode="Markdown")
            await asyncio.sleep(1)
        await send_tag_via_userbot(mentions, chat_id)

# ================= 📥 دریافت اعضای گروه =================
async def get_group_members(context, chat_id):
    participants = []
    try:
        chat_members = await context.bot.get_chat_administrators(chat_id)
        participants.extend([m.user for m in chat_members if not m.user.is_bot])
    except:
        pass
    return participants

# ================= 🔧 ثبت هندلرها =================
def register_tag_panel(application):
    application.add_handler(MessageHandler(filters.Regex(r"^(پنل تگ)$"), show_tag_panel))
    application.add_handler(CallbackQueryHandler(handle_tag_panel_click))
    application.add_handler(
        MessageHandler(filters.ALL & filters.ChatType.GROUPS, record_user_activity)
    )
