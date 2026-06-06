import os
import json
import asyncio

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, MessageHandler, filters, CallbackQueryHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "force_db.json")

SUDO_IDS = [8588347189]


# ================= DB =================

def load_db():
    if not os.path.exists(DB_FILE):
        return {}

    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_channels(chat_id):
    data = load_db()
    return data.get(str(chat_id), [])


# ================= CHECK JOIN =================

async def check_join(bot, chat_id, user_id):
    channels = get_channels(chat_id)

    not_joined = []

    for ch in channels:
        try:
            member = await bot.get_chat_member(ch, user_id)

            if member.status in ["left", "kicked"]:
                not_joined.append(ch)

        except:
            not_joined.append(ch)

    return not_joined


# ================= MIDDLEWARE =================

async def force_join_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not msg or not chat or not user:
        return True

    if chat.type not in ["group", "supergroup"]:
        return True

    not_joined = await check_join(context.bot, chat.id, user.id)

    if not not_joined:
        return True

    buttons = []

    for ch in not_joined:
        buttons.append([
            InlineKeyboardButton(
                "📢 عضویت در کانال",
                url=f"https://t.me/{ch.replace('@','')}"
            )
        ])

    buttons.append([
        InlineKeyboardButton("🔄 بررسی عضویت", callback_data="force_check")
    ])

    await msg.reply_text(
        "❌ برای استفاده از ربات باید عضو کانال‌ها شوید:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

    return False


# ================= CALLBACK =================

async def force_check_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    chat_id = query.message.chat.id

    not_joined = await check_join(context.bot, chat_id, user_id)

    if not not_joined:
        await query.message.edit_text("✅ عضویت تایید شد، می‌تونی استفاده کنی.")
    else:
        await query.answer("❌ هنوز عضو کامل نشدی", show_alert=True)


# ================= REGISTER =================

def register_force_join(application, group_number=0):

    application.add_handler(
        MessageHandler(
            filters.ALL,
            force_join_middleware
        ),
        group=group_number
    )

    application.add_handler(
        CallbackQueryHandler(
            force_check_callback,
            pattern="force_check"
        ),
        group=group_number
    )
