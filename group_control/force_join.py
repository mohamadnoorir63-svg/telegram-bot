import os
import json
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters

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


def add_channel(chat_id, channel):
    data = load_db()

    chat_id = str(chat_id)

    if chat_id not in data:
        data[chat_id] = []

    if channel not in data[chat_id]:
        data[chat_id].append(channel)

    save_db(data)


def remove_channel(chat_id, channel):
    data = load_db()

    chat_id = str(chat_id)

    if chat_id in data and channel in data[chat_id]:
        data[chat_id].remove(channel)

    save_db(data)


# ================= CHECK USER =================

async def check_force_join(bot, chat_id, user_id):
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

async def force_join_middleware(update, context):

    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not msg or not chat or not user:
        return True

    if chat.type not in ["group", "supergroup"]:
        return True

    not_joined = await check_force_join(
        context.bot,
        chat.id,
        user.id
    )

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
        InlineKeyboardButton(
            "🔄 بررسی عضویت",
            callback_data="force_check"
        )
    ])

    await msg.reply_text(
        "❌ برای استفاده از ربات باید عضو کانال‌های زیر شوید:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

    return False


# ================= CALLBACK =================

async def force_check_callback(update, context):

    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat.id

    not_joined = await check_force_join(
        context.bot,
        chat_id,
        user_id
    )

    if not not_joined:
        await query.message.edit_text("✅ عضویت تایید شد.")
    else:
        await query.answer("❌ هنوز عضو کامل نشدی", show_alert=True)


# ================= REGISTER =================

def register_force_join(application, group_number=15):

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            force_join_middleware
        ),
        group=group_number
    )
