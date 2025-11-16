"""
tagger.py
نسخه‌ی کامل، نهایی، سریع و حرفه‌ای — همراه با یوزربات + fallback
"""

import os
import json
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

# ===================== تنظیمات =====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACTIVITY_FILE = os.path.join(BASE_DIR, "activity.json")

SUDO_IDS = [8588347189]   # شناسه سودو

if not os.path.exists(ACTIVITY_FILE):
    with open(ACTIVITY_FILE, "w", encoding="utf-8") as f:
        json.dump({"activity": {}, "joined": {}}, f, ensure_ascii=False, indent=2)

# ===================== یوزربات (اختیاری) =====================
try:
    from userbot_module.userbot import client as userbot_client
except Exception:
    userbot_client = None

# ===================== فایل داده‌ها =====================
def _load_data():
    try:
        with open(ACTIVITY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"activity": {}, "joined": {}}

def _save_data(data):
    with open(ACTIVITY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===================== دسترسی =====================
async def _has_access(context, chat_id, user_id):
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False


# ===================== رکورد فعالیت =====================
async def record_user_activity(update: Update, context):
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
    key = str(chat.id)

    data.setdefault("activity", {})
    data["activity"].setdefault(key, {})
    data["activity"][key][str(user.id)] = datetime.utcnow().timestamp()

    _save_data(data)


# ===================== رکورد ورود کاربران =====================
async def record_new_member(update: Update, context):
    msg = update.effective_message
    new_members = msg.new_chat_members or []
    if not new_members:
        return

    chat = update.effective_chat
    key = str(chat.id)

    data = _load_data()
    data.setdefault("joined", {})
    data["joined"].setdefault(key, {})

    for m in new_members:
        if not m.is_bot:
            data["joined"][key][str(m.id)] = datetime.utcnow().timestamp()

    _save_data(data)


# ===================== گرفتن همه اعضا (یوزربات + fallback) =====================
async def get_all_members(chat, context):
    # ------------------ 1) یوزربات ------------------
    if userbot_client:
        try:
            members = await userbot_client.get_participants(chat.id)
            if members:
                return [m for m in members if not getattr(m, "bot", False)]
        except:
            pass

    # ------------------ 2) fallback: ربات اصلی ------------------
    members = []
    try:
        count = await context.bot.get_chat_member_count(chat.id)
        for user_id in range(count):
            try:
                member = await context.bot.get_chat_member(chat.id, user_id)
                if member and not member.user.is_bot:
                    members.append(member.user)
            except:
                continue
    except:
        return []

    return members


# ===================== ساخت پنل =====================
def build_tag_panel():
    kb = [
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
    return InlineKeyboardMarkup(kb)


# ===================== بازکردن پنل =====================
async def open_tag_panel(update: Update, context):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if chat.type not in ("group", "supergroup"):
        return

    if not await _has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران اجازه دارند!", quote=True)

    await msg.reply_text("🔽 حالت تگ را انتخاب کنید:", reply_markup=build_tag_panel(), quote=True)


# ===================== ساخت متن تگ =====================
def build_mention_text(items: List[str]) -> List[str]:
    result = []
    chunk = 20
    for i in range(0, len(items), chunk):
        result.append("     ".join(items[i:i+chunk]))
    return result


# ===================== هندل تگ =====================
async def handle_tag_panel_click(update: Update, context):
    q = update.callback_query
    await q.answer()

    user = q.from_user
    chat = q.message.chat

    if not await _has_access(context, chat.id, user.id):
        return await q.answer("🚫 دسترسی ندارید!", show_alert=True)

    data = _load_data()
    key = str(chat.id)

    mentions = []

    # ------------------ بستن ------------------
    if q.data == "tg_close":
        await q.message.delete()
        return

    try:
        # ------------------ همه اعضا ------------------
        if q.data == "tg_all":
            members = await get_all_members(chat, context)
            mentions = [f"𓃬ꪰ #[{m.first_name}](tg://user?id={m.id})" for m in members]

        # ------------------ ادمین‌ها ------------------
        elif q.data in ("tg_admin_active", "tg_admin_inactive"):
            admins = await context.bot.get_chat_administrators(chat.id)
            cutoff = datetime.utcnow() - timedelta(hours=24)

            for a in admins:
                if a.user.is_bot:
                    continue

                uid = str(a.user.id)
                ts = data.get("activity", {}).get(key, {}).get(uid)
                active = ts and datetime.utcfromtimestamp(ts) > cutoff

                if q.data == "tg_admin_active" and active:
                    mentions.append(f"𓃬ꪰ #[{a.user.first_name}](tg://user?id={a.user.id})")

                if q.data == "tg_admin_inactive" and not active:
                    mentions.append(f"𓃬ꪰ #[{a.user.first_name}](tg://user?id={a.user.id})")

        # ------------------ همه کاربران ------------------
        elif q.data == "tg_users_all":
            members = await get_all_members(chat, context)
            admin_ids = [a.user.id for a in await context.bot.get_chat_administrators(chat.id)]
            mentions = [
                f"𓃬ꪰ #[{m.first_name}](tg://user?id={m.id})"
                for m in members if m.id not in admin_ids
            ]

        # ------------------ کاربران فعال/غیرفعال ------------------
        elif q.data in ("tg_users_active", "tg_users_inactive"):
            cutoff = datetime.utcnow() - timedelta(hours=24)
            act = data.get("activity", {}).get(key, {})

            for uid, ts in act.items():
                active = datetime.utcfromtimestamp(ts) > cutoff

                if q.data == "tg_users_active" and active:
                    mentions.append(f"𓃬ꪰ #[کاربر](tg://user?id={uid})")

                if q.data == "tg_users_inactive" and not active:
                    mentions.append(f"𓃬ꪰ #[کاربر](tg://user?id={uid})")

        # ------------------ کاربران جدید ------------------
        elif q.data == "tg_new":
            cutoff = datetime.utcnow() - timedelta(days=7)
            joined = data.get("joined", {}).get(key, {})

            for uid, ts in joined.items():
                if datetime.utcfromtimestamp(ts) > cutoff:
                    mentions.append(f"𓃬ꪰ #[کاربر جدید](tg://user?id={uid})")

        # ------------------ لیست سفارشی ------------------
        elif q.data == "tg_custom":
            rep = q.message.reply_to_message
            if not rep:
                return await q.answer("باید روی پیام کاربر ریپلای کنید!", show_alert=True)

            u = rep.from_user
            if u and not u.is_bot:
                mentions.append(f"𓃬ꪰ #[{u.first_name}](tg://user?id={u.id})")

    except:
        await q.message.edit_text("⚠️ خطا در پردازش!")
        await asyncio.sleep(1)
        await q.message.delete()
        return

    # ------------------ بستن پنل ------------------
    try:
        await q.message.delete()
    except:
        pass

    # ------------------ ارسال تگ‌ها ------------------
    if mentions:
        parts = build_mention_text(mentions)
        for p in parts:
            try:
                await context.bot.send_message(chat.id, p, parse_mode="Markdown")
            except:
                await context.bot.send_message(chat.id, p)
            await asyncio.sleep(0.2)
    else:
        await context.bot.send_message(chat.id, "⚠️ هیچ کاربری پیدا نشد.")


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


# ===================== پایان =====================
