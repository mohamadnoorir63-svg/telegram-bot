"""
tagger.py
پنل تگ دقیقاً مثل عکس — کلیک => تگ فوری => پنل بسته می‌شود
نیاز: python-telegram-bot v20+ و اختیاری userbot (Telethon/pyrogram client named 'client' در userbot_module.userbot)
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

# شناسه(های) سودو که همیشه اجازه دارند
SUDO_IDS = [8588347189]

# فایل داده‌ها (activity + joined)
if not os.path.exists(ACTIVITY_FILE):
    with open(ACTIVITY_FILE, "w", encoding="utf-8") as f:
        json.dump({"activity": {}, "joined": {}}, f, ensure_ascii=False, indent=2)

# ---------- یوزربات (اختیاری) ----------
try:
    # انتظار می‌رود در userbot_module.userbot یک client غیرهمزمان وجود داشته باشد
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
async def _has_access(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except Exception:
        return False

# ===================== ثبت فعالیت و عضو شدن =====================
async def record_user_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هر پیام کاربر => زمان آخرین فعالیت ذخیره شود"""
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
    if "activity" not in data:
        data["activity"] = {}
    if chat_key not in data["activity"]:
        data["activity"][chat_key] = {}
    data["activity"][chat_key][str(user.id)] = datetime.utcnow().timestamp()
    _save_data(data)

async def record_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """وقتی کاربری وارد گروه می‌شود زمان ورود ثبت شود (برای users_new)"""
    msg = update.effective_message
    chat = update.effective_chat
    if not msg or not chat:
        return
    if chat.type not in ("group", "supergroup"):
        return

    new_members = msg.new_chat_members or []
    if not new_members:
        return

    data = _load_data()
    chat_key = str(chat.id)
    if "joined" not in data:
        data["joined"] = {}
    if chat_key not in data["joined"]:
        data["joined"][chat_key] = {}
    for member in new_members:
        if member and not member.is_bot:
            data["joined"][chat_key][str(member.id)] = datetime.utcnow().timestamp()
    _save_data(data)

# ===================== ساخت پنل (دقیقاً مثل عکس) =====================
def build_tag_panel():
    keyboard = [
        [InlineKeyboardButton("همه اعضا", callback_data="tg_all")],
        [
            InlineKeyboardButton("ادمین‌های فعال", callback_data="tg_admin_active"),
            InlineKeyboardButton("ادمین‌های غیرفعال", callback_data="tg_admin_inactive"),
        ],
        [InlineKeyboardButton("همه کاربران", callback_data="tg_users_all")],
        [
            InlineKeyboardButton("کاربران فعال", callback_data="tg_users_active"),
            InlineKeyboardButton("کاربران غیرفعال", callback_data="tg_users_inactive"),
        ],
        [InlineKeyboardButton("کاربران جدید", callback_data="tg_new")],
        [InlineKeyboardButton("لیست سفارشی (ریپلای)", callback_data="tg_custom")],
        [InlineKeyboardButton("لغو/بستن", callback_data="tg_close")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ===================== باز کردن پنل =====================
async def open_tag_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not msg or not user or not chat:
        return

    if chat.type not in ("group", "supergroup"):
        return await msg.reply_text("این پنل فقط در گروه‌ها قابل استفاده است.", quote=True)

    if not await _has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها مجاز به استفاده از این پنل هستند!", quote=True)

    await msg.reply_text("🔽 حالت تگ را انتخاب کنید:", reply_markup=build_tag_panel(), quote=True)

# ===================== کمک: ساخت متن تگ (هر عنصر با '# ' جدا می‌شود) =====================
def build_mention_text(items: List[str]) -> List[str]:
    """دریافت لیست متن‌های mention (هر آیتم مثلا '# [name](tg://user?id=...)')
       و برگرداندن لیست پیام‌هایی که هر کدام تا 20 آیتم دارند."""
    out = []
    chunk = 20
    for i in range(0, len(items), chunk):
        part = items[i:i+chunk]
        # جداکننده: دو فاصله پس از #item برای خوانایی
        out.append("  ".join(part))
    return out

# ===================== گرفتن اعضا با یوزربات یا fallback =====================
async def get_all_members_via_userbot(chat_id: int):
    """اگر userbot موجود باشد اعضا را برمی‌گرداند (هر آیتم یک آبجکت دارای id, first_name).
       متأسفانه با API بات نمی‌توان همه اعضا را فچ کرد؛ بنابراین userbot لازم است برای 'همه اعضا'."""
    members = []
    if not userbot_client:
        return members
    try:
        # تابع اسمش ممکن است بسته به userbot متفاوت باشد؛ اینجا رایج‌ترین نام را می‌زنیم
        members = await userbot_client.get_participants(chat_id)
    except Exception:
        try:
            # بعضی کلاینت‌ها متد متفاوتی دارند؛ امتحان می‌کنیم فقط در صورت وجود
            members = await userbot_client.get_participants(chat_id)
        except Exception:
            members = []
    return members

# ===================== هندلر کلیک روی دکمه‌ها =====================
async def handle_tag_panel_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    user = query.from_user
    chat = query.message.chat

    # دسترسی چک
    if not await _has_access(context, chat.id, user.id):
        return await query.answer("🚫 فقط مدیران یا سودوها مجاز هستند!", show_alert=True)

    data = _load_data()
    chat_key = str(chat.id)
    mentions = []  # هر آیتم: '# [name](tg://user?id=ID)'

    # بستن پنل سریع
    if query.data == "tg_close":
        await query.message.delete()
        return

    # --------- دسته‌بندی‌ها ----------
    try:
        # 1) همه اعضا — نیاز به userbot
        if query.data == "tg_all":
            members = await get_all_members_via_userbot(chat.id)
            if not members:
                await query.message.edit_text("⚠️ برای این گزینه نیاز به یوزربات دارید. یوزربات در دسترس نیست.")
                await asyncio.sleep(1.5)
                await query.message.delete()
                return
            mentions = [f"# [{m.first_name}](tg://user?id={m.id})" for m in members if not getattr(m, "bot", False)]

        # 2) ادمین‌های فعال / غیرفعال
        elif query.data in ("tg_admin_active", "tg_admin_inactive"):
            admins = await context.bot.get_chat_administrators(chat.id)
            # فعال = وجود رکورد activity در 24 ساعت گذشته
            active_cutoff = datetime.utcnow() - timedelta(hours=24)
            for a in admins:
                if a.user.is_bot:
                    continue
                uid = str(a.user.id)
                last_ts = None
                if "activity" in data and chat_key in data["activity"]:
                    last_ts = data["activity"][chat_key].get(uid)
                is_active = False
                if last_ts:
                    is_active = datetime.utcfromtimestamp(last_ts) > active_cutoff
                if query.data == "tg_admin_active" and is_active:
                    mentions.append(f"# [{a.user.first_name}](tg://user?id={a.user.id})")
                if query.data == "tg_admin_inactive" and not is_active:
                    mentions.append(f"# [{a.user.first_name}](tg://user?id={a.user.id})")

        # 3) همه کاربران (غیر ادمین) — نیاز به userbot یا fallback محدود
        elif query.data == "tg_users_all":
            members = await get_all_members_via_userbot(chat.id)
            if not members:
                await query.message.edit_text("⚠️ برای دریافت همه کاربران نیاز به یوزربات است؛ در غیر این صورت این گزینه قابل استفاده نیست.")
                await asyncio.sleep(1.5)
                await query.message.delete()
                return
            # فیلتر ادمین/بات
            admins = [a.user.id for a in await context.bot.get_chat_administrators(chat.id)]
            mentions = [f"# [{m.first_name}](tg://user?id={m.id})" for m in members if not getattr(m, "bot", False) and m.id not in admins]

        # 4) کاربران فعال / غیرفعال (بر اساس activity.json)
        elif query.data in ("tg_users_active", "tg_users_inactive"):
            active_cutoff = datetime.utcnow() - timedelta(hours=24)
            if "activity" not in data or chat_key not in data["activity"]:
                # هیچ دیتا موجود نیست
                await query.message.edit_text("⚠️ دیتای فعالیت وجود ندارد. کاربران فعال/غیرفعال تشخیص داده نشدند.")
                await asyncio.sleep(1.5)
                await query.message.delete()
                return
            for uid, ts in data["activity"][chat_key].items():
                uid_int = int(uid)
                is_active = datetime.utcfromtimestamp(ts) > active_cutoff
                if query.data == "tg_users_active" and is_active:
                    mentions.append(f"# [کاربر](tg://user?id={uid_int})")
                if query.data == "tg_users_inactive" and not is_active:
                    mentions.append(f"# [کاربر](tg://user?id={uid_int})")

        # 5) کاربران جدید (مثلاً عضو شده در 7 روز گذشته)
        elif query.data == "tg_new":
            cutoff = datetime.utcnow() - timedelta(days=7)
            if "joined" not in data or chat_key not in data["joined"]:
                await query.message.edit_text("⚠️ داده‌ای برای کاربران جدید وجود ندارد.")
                await asyncio.sleep(1.5)
                await query.message.delete()
                return
            for uid, ts in data["joined"][chat_key].items():
                if datetime.utcfromtimestamp(ts) > cutoff:
                    mentions.append(f"# [کاربر جدید](tg://user?id={int(uid)})")

        # 6) لیست سفارشی (ساده): کاربر باید روی پیام موردنظر ریپلای کرده باشد
        elif query.data == "tg_custom":
            # اگر روی پیام ریپلای شده، یک یا چند کاربر می‌توانند از آن پیام استخراج شوند.
            # برای سادگی: اگر یک پیام ریپلای شده باشد، آن پیام فرستنده تگ می‌شود.
            if not query.message.reply_to_message:
                await query.answer("برای لیست سفارشی باید روی پیامِ کاربر ریپلای کنید.", show_alert=True)
                return
            target = query.message.reply_to_message.from_user
            if target and not target.is_bot:
                mentions = [f"# [{target.first_name}](tg://user?id={target.id})"]
            else:
                await query.answer("کاربر نامعتبر.", show_alert=True)
                return

        else:
            # الگو نامشخص
            await query.answer("🚫 گزینه نامشخص", show_alert=True)
            return

    except Exception as e:
        # خطا را به کاربر اطلاع بده و پنل را حذف کن
        try:
            await query.message.edit_text("⚠️ خطا هنگام پردازش درخواست.")
        except Exception:
            pass
        await asyncio.sleep(1.2)
        try:
            await query.message.delete()
        except Exception:
            pass
        return

    # ---------- حذف پنل بلافاصله ----------
    try:
        await query.message.delete()
    except Exception:
        pass

    # ---------- ارسال تگ‌ها به صورت دسته‌ای (20تایی) ----------
    if mentions:
        parts = build_mention_text(mentions)
        for p in parts:
            # از Markdown استفاده می‌کنیم تا لینک‌های tg:// کار کنند
            try:
                await context.bot.send_message(chat.id, p, parse_mode="Markdown")
            except Exception:
                # اگر parse_mode Markdown مشکل داشت سعی کن بدون parse_mode ارسال کنی
                await context.bot.send_message(chat.id, p)
            await asyncio.sleep(1)  # جلوگیری از محدودیت API
    else:
        # اگر هیچ mention ای نبود، اطلاع بده (و هیچ پیام اضافی نذار)
        try:
            await context.bot.send_message(chat.id, "⚠️ هیچ کاربری برای تگ یافت نشد.")
        except Exception:
            pass

# ===================== ثبت هندلرها (برای فراخوانی در main) =====================
def register_tag_handlers(application, group_number: int = 14):
    """
    ثبت هندلرها در اپلیکیشن:
    - دستور متنی "تگ" بازکننده پنل
    - هندلر کلیک روی دکمه‌ها
    - ذخیره فعالیت همه پیام‌ها
    - ذخیره ورود اعضا
    """
    application.add_handler(
        MessageHandler(filters.Regex(r"^(تگ)$") & filters.ChatType.GROUPS, open_tag_panel),
        group=group_number,
    )

    application.add_handler(
        CallbackQueryHandler(handle_tag_panel_click, pattern=r"^tg_"),
        group=group_number + 1,
    )

    # ثبت فعالیت هر پیام
    application.add_handler(
        MessageHandler(filters.ALL & filters.ChatType.GROUPS, record_user_activity),
        group=group_number + 2,
    )

    # ثبت ورود اعضا برای تشخیص کاربران جدید
    application.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, record_new_member),
        group=group_number + 3,
    )

# ===================== پایان فایل =====================
