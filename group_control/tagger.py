import asyncio
import random
from datetime import datetime, timedelta
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update
)
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

SUDO_IDS = [8588347189]


# ========== پنل ==========

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
        [InlineKeyboardButton("لیست سفارشی", callback_data="tg_custom")],

        [InlineKeyboardButton("لغو عملیات", callback_data="tg_close")],
    ]

    return InlineKeyboardMarkup(keyboard)


# ========== مجوز ==========

async def _has_access(context, chat_id, uid):
    if uid in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, uid)
        return member.status in ("creator", "administrator")
    except:
        return False


# ========== پنل باز کردن ==========

async def open_tag_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    if not await _has_access(context, chat.id, user.id):
        return await update.message.reply_text("🚫 این پنل فقط برای مدیران است!")

    await update.message.reply_text(
        "• لطفاً نوع کاربران را برای تگ شدن انتخاب نمایید:",
        reply_markup=build_tag_panel()
    )


# ========== تابع ارسال تگ ==========

async def send_mentions(context, chat_id, users):
    if not users:
        return

    chunk = 20
    for i in range(0, len(users), chunk):
        batch = users[i:i + chunk]
        text = " ".join(batch)
        await context.bot.send_message(chat_id, text, parse_mode="Markdown")
        await asyncio.sleep(1)


# ========== هندلر کلیک روی دکمه‌ها ==========

async def handle_tag_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    chat = query.message.chat
    user = query.from_user

    await query.answer()

    if not await _has_access(context, chat.id, user.id):
        return await query.answer("⛔ فقط مدیران!", show_alert=True)

    # بستن پنل
    if data == "tg_close":
        await query.message.delete()
        return

    # جمع‌آوری کاربران
    mentions = []

    # گرفتن اطلاعات گروه
    members = await context.bot.get_chat_administrators(chat.id)
    last_active_time = datetime.utcnow() - timedelta(hours=24)

    # تگ همه کاربران گروه
    if data == "tg_all":
        chat_members = await context.bot.get_chat(chat.id)
        members_list = await context.bot.get_chat_members_count(chat.id)

    # ادمین‌های فعال
    if data == "tg_admin_active":
        for admin in members:
            if not admin.user.is_bot:
                mentions.append(f"[{admin.user.first_name}](tg://user?id={admin.user.id})")

    # ادمین‌های غیرفعال
    if data == "tg_admin_inactive":
        for admin in members:
            if not admin.user.is_bot:
                mentions.append(f"[{admin.user.first_name}](tg://user?id={admin.user.id})")

    # کاربران فعال (بر اساس پیام‌های ۲۴ ساعت گذشته)
    if data == "tg_users_active":
        activity = context.chat_data.get("activity", {})
        for uid, ts in activity.items():
            if datetime.utcfromtimestamp(ts) > last_active_time:
                mentions.append(f"[کاربر](tg://user?id={uid})")

    # کاربران غیرفعال
    if data == "tg_users_inactive":
        activity = context.chat_data.get("activity", {})
        for uid in activity.keys():
            mentions.append(f"[کاربر](tg://user?id={uid})")

    # کاربران جدید (۷۲ ساعت)
    if data == "tg_new":
        activity = context.chat_data.get("joined", {})
        for uid, ts in activity.items():
            if datetime.utcfromtimestamp(ts) > datetime.utcnow() - timedelta(hours=72):
                mentions.append(f"[کاربر جدید](tg://user?id={uid})")

    # لیست سفارشی — ساده: فقط ریپلای شده را تگ می‌کنیم
    if data == "tg_custom":
        if query.message.reply_to_message:
            uid = query.message.reply_to_message.from_user.id
            mentions.append(f"[کاربر](tg://user?id={uid})")
        else:
            return await query.answer("باید روی پیام کاربر ریپلای کنید!", show_alert=True)

    # پاک کردن پنل قبل از ارسال
    await query.message.delete()

    # ارسال
    await send_mentions(context, chat.id, mentions)


# ========== ذخیره فعالیت برای فعال/غیرفعال ==========

async def record_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or update.effective_user.is_bot:
        return

    uid = str(update.effective_user.id)
    ts = datetime.utcnow().timestamp()

    if "activity" not in context.chat_data:
        context.chat_data["activity"] = {}
    context.chat_data["activity"][uid] = ts


# ========== ثبت هندلرها ==========

def register_tag_handlers(application, group_number=14):
    application.add_handler(
        MessageHandler(filters.Regex(r"^(تگ)$"), open_tag_panel),
        group=group_number
    )

    application.add_handler(
        CallbackQueryHandler(handle_tag_click, pattern=r"^tg_"),
        group=group_number + 1
    )

    application.add_handler(
        MessageHandler(filters.ALL, record_activity),
        group=group_number + 2
    )
