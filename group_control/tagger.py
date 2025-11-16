"""
tagger.py
نسخه‌ی کامل و نهایی — پنل تگ حرفه‌ای، سریع، زیبا و دقیقاً شبیه عکس
"""

import os
import json
import random
import asyncio
from datetime import datetime, timedelta
from typing import List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# ===================== تنظیمات اولیه =====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACTIVITY_FILE = os.path.join(BASE_DIR, "activity.json")

SUDO_IDS = [8588347189]

if not os.path.exists(ACTIVITY_FILE):
    with open(ACTIVITY_FILE, "w", encoding="utf-8") as f:
        json.dump({"activity": {}, "joined": {}}, f, ensure_ascii=False, indent=2)

# ---------- یوزربات (اختیاری) ----------
try:
    from userbot_module.userbot import client as userbot_client
except Exception:
    userbot_client = None

# ===================== توابع کمکی فایل =====================
def _load_data():
    try:
        with open(ACTIVITY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"activity": {}, "joined": {}}

def _save_data(data):
    with open(ACTIVITY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===================== بررسی دسترسی =====================
async def _has_access(context, chat_id, user_id):
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except Exception:
        return False

# ===================== ثبت فعالیت و عضو شدن =====================
async def record_user_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not msg or not user or not chat:
        return
    if chat.type not in ("group", "supergroup"):
        return
    if user.is_bot:
        return

    data = _load_data()
    chat_key = str(chat.id)

    data.setdefault("activity", {})
    data["activity"].setdefault(chat_key, {})
    data["activity"][chat_key][str(user.id)] = datetime.utcnow().timestamp()

    _save_data(data)

async def record_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    new_members = msg.new_chat_members or []
    if not new_members:
        return

    chat = update.effective_chat
    chat_key = str(chat.id)

    data = _load_data()
    data.setdefault("joined", {})
    data["joined"].setdefault(chat_key, {})

    for member in new_members:
        if not member.is_bot:
            data["joined"][chat_key][str(member.id)] = datetime.utcnow().timestamp()

    _save_data(data)

# ===================== ساخت پنل (زیبا و کش‌سان) =====================
def build_tag_panel():
    keyboard = [
        [InlineKeyboardButton("𓃬ꪰ همه اعضا", callback_data="tg_all")],
        [InlineKeyboardButton("𓃬ꪰ ادمین‌های فعال", callback_data="tg_admin_active")],
        [InlineKeyboardButton("𓃬ꪰ ادمین‌های غیرفعال", callback_data="tg_admin_inactive")],
        [InlineKeyboardButton("𓃬ꪰ همه کاربران", callback_data="tg_users_all")],
        [InlineKeyboardButton("𓃬ꪰ کاربران فعال", callback_data="tg_users_active")],
        [InlineKeyboardButton("𓃬ꪰ کاربران غیرفعال", callback_data="tg_users_inactive")],
        [InlineKeyboardButton("𓃬ꪰ کاربران جدید", callback_data="tg_new")],
        [InlineKeyboardButton("𓃬ꪰ لیست سفارشی (ریپلای)", callback_data="tg_custom")],
        [InlineKeyboardButton("❌ بستن", callback_data="tg_close")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ===================== باز کردن پنل =====================
async def open_tag_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if chat.type not in ("group", "supergroup"):
        return

    if not await _has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها اجازه دارند!", quote=True)

    await msg.reply_text("🔽 حالت تگ را انتخاب کنید:", reply_markup=build_tag_panel(), quote=True)

# ===================== ساخت متن تگ =====================
def build_mention_text(items: List[str]) -> List[str]:
    out = []
    chunk = 20
    for i in range(0, len(items), chunk):
        out.append("     ".join(items[i:i+chunk]))
    return out

# ===================== اعضا با یوزربات =====================
async def get_all_members_via_userbot(chat_id: int):
    if not userbot_client:
        return []
    try:
        return await userbot_client.get_participants(chat_id)
    except Exception:
        return []

# ===================== هندلر تگ =====================
async def handle_tag_panel_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    chat = query.message.chat

    if not await _has_access(context, chat.id, user.id):
        return await query.answer("🚫 مجاز نیستید!", show_alert=True)

    data = _load_data()
    chat_key = str(chat.id)

    mentions = []

    # ------------------- بستن -------------------
    if query.data == "tg_close":
        await query.message.delete()
        return

    try:
        # ------------------- همه اعضا -------------------
        if query.data == "tg_all":
            members = await get_all_members_via_userbot(chat.id)
            if not members:
                await query.message.edit_text("⚠️ یوزربات در دسترس نیست.")
                await asyncio.sleep(1)
                await query.message.delete()
                return

            mentions = [
                f"𓃬ꪰ #[{m.first_name}](tg://user?id={m.id})"
                for m in members if not getattr(m, "bot", False)
            ]

        # ------------------- ادمین فعال/غیرفعال -------------------
        elif query.data in ("tg_admin_active", "tg_admin_inactive"):
            admins = await context.bot.get_chat_administrators(chat.id)
            active_cutoff = datetime.utcnow() - timedelta(hours=24)

            for a in admins:
                if a.user.is_bot: 
                    continue

                uid = str(a.user.id)
                last_ts = data.get("activity", {}).get(chat_key, {}).get(uid)

                is_active = (
                    last_ts and datetime.utcfromtimestamp(last_ts) > active_cutoff
                )

                if query.data == "tg_admin_active" and is_active:
                    mentions.append(f"𓃬ꪰ #[{a.user.first_name}](tg://user?id={a.user.id})")

                if query.data == "tg_admin_inactive" and not is_active:
                    mentions.append(f"𓃬ꪰ #[{a.user.first_name}](tg://user?id={a.user.id})")

        # ------------------- همه کاربران -------------------
        elif query.data == "tg_users_all":
            members = await get_all_members_via_userbot(chat.id)
            if not members:
                await query.message.edit_text("⚠️ این گزینه فقط با یوزربات فعال است.")
                await asyncio.sleep(1)
                await query.message.delete()
                return

            admins = [a.user.id for a in await context.bot.get_chat_administrators(chat.id)]

            mentions = [
                f"𓃬ꪰ #[{m.first_name}](tg://user?id={m.id})"
                for m in members
                if not getattr(m, "bot", False) and m.id not in admins
            ]

        # ------------------- کاربران فعال/غیرفعال -------------------
        elif query.data in ("tg_users_active", "tg_users_inactive"):
            active_cutoff = datetime.utcnow() - timedelta(hours=24)
            users = data.get("activity", {}).get(chat_key, {})

            for uid, ts in users.items():
                is_active = datetime.utcfromtimestamp(ts) > active_cutoff

                if query.data == "tg_users_active" and is_active:
                    mentions.append(f"𓃬ꪰ #[کاربر](tg://user?id={uid})")

                if query.data == "tg_users_inactive" and not is_active:
                    mentions.append(f"𓃬ꪰ #[کاربر](tg://user?id={uid})")

        # ------------------- کاربران جدید -------------------
        elif query.data == "tg_new":
            cutoff = datetime.utcnow() - timedelta(days=7)
            joined = data.get("joined", {}).get(chat_key, {})

            for uid, ts in joined.items():
                if datetime.utcfromtimestamp(ts) > cutoff:
                    mentions.append(f"𓃬ꪰ #[کاربر جدید](tg://user?id={uid})")

        # ------------------- لیست سفارشی -------------------
        elif query.data == "tg_custom":
            rep = query.message.reply_to_message
            if not rep:
                return await query.answer("روی پیام کاربر ریپلای کن!", show_alert=True)

            u = rep.from_user
            if u and not u.is_bot:
                mentions = [f"𓃬ꪰ #[{u.first_name}](tg://user?id={u.id})"]

    except:
        await query.message.edit_text("⚠️ خطا در پردازش")
        await asyncio.sleep(1)
        await query.message.delete()
        return

    # ------------------- بستن پنل -------------------
    try:
        await query.message.delete()
    except:
        pass

    # ------------------- ارسال تگ‌ها -------------------
    if mentions:
        parts = build_mention_text(mentions)
        for p in parts:
            try:
                await context.bot.send_message(chat.id, p, parse_mode="Markdown")
            except:
                await context.bot.send_message(chat.id, p)
            await asyncio.sleep(0.2)   # سرعت بالا
    else:
        await context.bot.send_message(chat.id, "⚠️ هیچ کاربری یافت نشد.")

# ===================== ثبت هندلرها =====================
def register_tag_handlers(application, group_number: int = 14):

    application.add_handler(
        MessageHandler(filters.Regex("^تگ$") & filters.ChatType.GROUPS, open_tag_panel),
        group=group_number,
    )

    application.add_handler(
        CallbackQueryHandler(handle_tag_panel_click, pattern=r"^tg_"),
        group=group_number + 1,
    )

    application.add_handler(
        MessageHandler(filters.ALL & filters.ChatType.GROUPS, record_user_activity),
        group=group_number + 2,
    )

    application.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, record_new_member),
        group=group_number + 3,
    )

# ===================== پایان فایل =====================
