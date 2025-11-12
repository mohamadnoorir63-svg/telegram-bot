import os
import json
import random
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

# ================= ⚙️ تنظیمات اولیه =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACTIVITY_FILE = os.path.join(BASE_DIR, "activity.json")

SUDO_IDS = [8588347189]  # آیدی سودوها

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

# ================= 👥 تگ کاربران =================
async def handle_tag_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    text = (msg.text or "").strip()

    if chat.type not in ("group", "supergroup"):
        return

    tag_commands = ["تگ همه", "تگ مدیران", "تگ فعال", "تگ غیرفعال", "تگ تصادفی"]
    if not any(text.startswith(cmd) for cmd in tag_commands):
        return

    if not await _has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها مجاز به استفاده از این دستور هستند!")

    # -------------------- تگ همه --------------------
    if text == "تگ همه":
        try:
            all_users = []
            async for member in context.bot.get_chat_members(chat.id):
                if not member.user.is_bot:
                    all_users.append(f"[{member.user.first_name}](tg://user?id={member.user.id})")
            
            if not all_users:
                return await msg.reply_text("ℹ️ هیچ کاربر مناسبی برای تگ پیدا نشد.")

            chunks = [all_users[i:i + 20] for i in range(0, len(all_users), 20)]
            for chunk in chunks:
                await msg.reply_text("👥 " + " ".join(chunk), parse_mode="Markdown")
                await asyncio.sleep(1)

        except Exception as e:
            await msg.reply_text(f"⚠️ خطا در تگ همه: {e}")

    # -------------------- تگ مدیران --------------------
    elif text == "تگ مدیران":
        try:
            admins = await context.bot.get_chat_administrators(chat.id)
            mentions = [f"[{a.user.first_name}](tg://user?id={a.user.id})" for a in admins if not a.user.is_bot]
            if not mentions:
                return await msg.reply_text("ℹ️ هیچ مدیر فعالی در گروه وجود ندارد.")
            chunks = [mentions[i:i + 20] for i in range(0, len(mentions), 20)]
            for chunk in chunks:
                await msg.reply_text("👑 " + " ".join(chunk), parse_mode="Markdown")
                await asyncio.sleep(1)
        except Exception as e:
            await msg.reply_text(f"⚠️ خطا در تگ مدیران: {e}")

    # -------------------- تگ فعال --------------------
    elif text == "تگ فعال":
        data = _load_activity()
        chat_data = data.get(str(chat.id), {})
        now = datetime.utcnow().timestamp()
        active_users = [uid for uid, t in chat_data.items() if now - t <= 24 * 3600]
        if not active_users:
            return await msg.reply_text("ℹ️ هیچ کاربر فعالی در ۲۴ ساعت گذشته وجود ندارد.")
        mentions = []
        for uid in active_users:
            try:
                member = await context.bot.get_chat_member(chat.id, int(uid))
                if not member.user.is_bot:
                    mentions.append(f"[{member.user.first_name}](tg://user?id={member.user.id})")
            except:
                continue
        chunks = [mentions[i:i + 20] for i in range(0, len(mentions), 20)]
        for chunk in chunks:
            await msg.reply_text("💬 " + " ".join(chunk), parse_mode="Markdown")
            await asyncio.sleep(1)

    # -------------------- تگ غیرفعال --------------------
    elif text == "تگ غیرفعال":
        data = _load_activity()
        chat_data = data.get(str(chat.id), {})
        now = datetime.utcnow().timestamp()
        inactive_users = [uid for uid, t in chat_data.items() if now - t > 24 * 3600]
        if not inactive_users:
            return await msg.reply_text("ℹ️ همه کاربران در ۲۴ ساعت گذشته فعال بوده‌اند.")
        mentions = []
        for uid in inactive_users:
            try:
                member = await context.bot.get_chat_member(chat.id, int(uid))
                if not member.user.is_bot:
                    mentions.append(f"[{member.user.first_name}](tg://user?id={member.user.id})")
            except:
                continue
        chunks = [mentions[i:i + 20] for i in range(0, len(mentions), 20)]
        for chunk in chunks:
            await msg.reply_text("😴 " + " ".join(chunk), parse_mode="Markdown")
            await asyncio.sleep(1)

    # -------------------- تگ تصادفی --------------------
    elif text.startswith("تگ تصادفی"):
        parts = text.split()
        count = 5
        if len(parts) > 2 and parts[2].isdigit():
            count = int(parts[2])
        try:
            all_users = []
            async for member in context.bot.get_chat_members(chat.id):
                if not member.user.is_bot:
                    all_users.append(f"[{member.user.first_name}](tg://user?id={member.user.id})")
            if not all_users:
                return await msg.reply_text("ℹ️ هیچ کاربر مناسبی برای تگ تصادفی وجود ندارد.")
            sample = random.sample(all_users, min(count, len(all_users)))
            await msg.reply_text("🎲 تگ تصادفی:\n" + " ".join(sample), parse_mode="Markdown")
        except Exception as e:
            await msg.reply_text(f"⚠️ خطا در تگ تصادفی: {e}")

# ================= 🔧 ثبت هندلر =================
def register_tag_handlers(application, group_number: int = 14):
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_tag_requests,
        ),
        group=group_number,
    )
    application.add_handler(
        MessageHandler(
            filters.ALL & filters.ChatType.GROUPS,
            record_user_activity,
        ),
        group=group_number + 1,
    )
