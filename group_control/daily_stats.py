import os
import json
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

STATS_FILE = "stats.json"
SUDO_ID = 8588347189


# ================= فایل =================

def load_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}


def save_stats():
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False)


stats = load_stats()


# ================= ایجاد روز =================

def init_day(chat_id):
    today = datetime.now().strftime("%Y-%m-%d")

    if chat_id not in stats:
        stats[chat_id] = {}

    if today not in stats[chat_id]:
        stats[chat_id][today] = {
            "messages": {},
            "joins": 0,
            "lefts": 0
        }

    return today


# ================= ثبت پیام =================

async def record_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    if update.effective_chat.type not in ["group", "supergroup"]:
        return

    chat_id = str(update.effective_chat.id)
    user_id = str(update.effective_user.id)

    today = init_day(chat_id)

    data = stats[chat_id][today]

    data["messages"][user_id] = (
        data["messages"].get(user_id, 0) + 1
    )

    save_stats()


# ================= ثبت ورود =================

async def record_join(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    if not update.message.new_chat_members:
        return

    chat_id = str(update.effective_chat.id)

    today = init_day(chat_id)

    stats[chat_id][today]["joins"] += len(
        update.message.new_chat_members
    )

    save_stats()


# ================= ثبت خروج =================

async def record_left(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    if not update.message.left_chat_member:
        return

    chat_id = str(update.effective_chat.id)

    today = init_day(chat_id)

    stats[chat_id][today]["lefts"] += 1

    save_stats()


# ================= آمار گروه =================

async def show_group_stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user
    chat = update.effective_chat

    try:
        member = await context.bot.get_chat_member(
            chat.id,
            user.id
        )

        if (
            user.id != SUDO_ID
            and member.status
            not in ["creator", "administrator"]
        ):
            return

    except:
        return

    chat_id = str(chat.id)
    today = datetime.now().strftime("%Y-%m-%d")

    if (
        chat_id not in stats
        or today not in stats[chat_id]
    ):
        await update.message.reply_text(
            "ℹ️ هنوز آماری ثبت نشده است."
        )
        return

    data = stats[chat_id][today]

    total_messages = sum(
        data["messages"].values()
    )

    top_users = sorted(
        data["messages"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    text = (
        "📊 آمار امروز گروه\n\n"
        f"💬 کل پیام‌ها: {total_messages}\n"
        f"👥 ورود اعضا: {data['joins']}\n"
        f"🚪 خروج اعضا: {data['lefts']}\n\n"
        "🏆 5 کاربر فعال:\n"
    )

    rank = 1

    for uid, count in top_users:

        try:
            member = await context.bot.get_chat_member(
                chat.id,
                int(uid)
            )

            name = member.user.first_name

        except:
            name = "کاربر"

        text += (
            f"{rank}. {name} ➜ {count} پیام\n"
        )

        rank += 1

    await update.message.reply_text(text)
