# tag_module.py
import os
import json
import asyncio
import random
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


async def _has_access(context, chat_id, user_id):
    """بررسی اینکه کاربر مجاز است یا نه"""
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False


# ================= 🧾 ثبت فعالیت =================
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

    # مجوز
    if not await _has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها مجاز به استفاده از این دستور هستند!")

    data = _load_activity()
    chat_key = str(chat.id)
    chat_data = data.get(chat_key, {})

    # ================= 📢 تگ همه =================
    if text == "تگ همه":
        await msg.reply_text("⏳ در حال تگ همه اعضا...")

        try:
            members = []
            async for m in context.bot.get_chat_administrators(chat.id):
                pass  # warmup to ensure permission

            # اگر دیتای اکتیویتی خالیه، از API کل اعضا رو بگیر
            if not chat_data:
                async for member in context.bot.get_chat_administrators(chat.id):
                    pass
                async for member in context.bot.get_chat_members(chat.id):
                    if not member.user.is_bot:
                        chat_data[str(member.user.id)] = datetime.utcnow().timestamp()
                _save_activity(data)

            user_ids = list(chat_data.keys())
            chunks = [user_ids[i:i + 20] for i in range(0, len(user_ids), 20)]

            count = 0
            for chunk in chunks:
                mentions = []
                for uid in chunk:
                    try:
                        member = await context.bot.get_chat_member(chat.id, int(uid))
                        if not member.user.is_bot:
                            name = member.user.first_name.replace("[", "").replace("]", "")
                            mentions.append(f"[{name}](tg://user?id={uid})")
                    except:
                        continue
                if mentions:
                    await msg.reply_text("👥 " + " ".join(mentions), parse_mode="Markdown")
                    count += len(mentions)
                await asyncio.sleep(1)

            await msg.reply_text(f"✅ تگ همه انجام شد.\n📊 تعداد تگ‌ها: {count}")
        except Exception as e:
            await msg.reply_text(f"⚠️ خطا در تگ همه: {e}")

    # ================= 👑 تگ مدیران =================
    elif text == "تگ مدیران":
        try:
            admins = await context.bot.get_chat_administrators(chat.id)
            mentions = [f"[{a.user.first_name}](tg://user?id={a.user.id})" for a in admins if not a.user.is_bot]
            for i in range(0, len(mentions), 20):
                await msg.reply_text("👑 " + " ".join(mentions[i:i+20]), parse_mode="Markdown")
                await asyncio.sleep(1)
        except Exception as e:
            await msg.reply_text(f"⚠️ خطا در تگ مدیران: {e}")

    # ================= 💬 تگ فعال =================
    elif text == "تگ فعال":
        now = datetime.utcnow().timestamp()
        active = [uid for uid, t in chat_data.items() if now - t <= 24 * 3600]
        if not active:
            return await msg.reply_text("ℹ️ هیچ کاربر فعالی در ۲۴ ساعت گذشته وجود ندارد.")
        for i in range(0, len(active), 20):
            mentions = []
            for uid in active[i:i+20]:
                try:
                    member = await context.bot.get_chat_member(chat.id, int(uid))
                    if not member.user.is_bot:
                        name = member.user.first_name.replace("[", "").replace("]", "")
                        mentions.append(f"[{name}](tg://user?id={uid})")
                except:
                    continue
            if mentions:
                await msg.reply_text("💬 " + " ".join(mentions), parse_mode="Markdown")
                await asyncio.sleep(1)

    # ================= 💤 تگ غیرفعال =================
    elif text == "تگ غیرفعال":
        now = datetime.utcnow().timestamp()
        inactive = [uid for uid, t in chat_data.items() if now - t > 24 * 3600]
        if not inactive:
            return await msg.reply_text("✅ همه کاربران در ۲۴ ساعت گذشته فعال بوده‌اند.")
        for i in range(0, len(inactive), 20):
            mentions = []
            for uid in inactive[i:i+20]:
                try:
                    member = await context.bot.get_chat_member(chat.id, int(uid))
                    if not member.user.is_bot:
                        name = member.user.first_name.replace("[", "").replace("]", "")
                        mentions.append(f"[{name}](tg://user?id={uid})")
                except:
                    continue
            if mentions:
                await msg.reply_text("😴 " + " ".join(mentions), parse_mode="Markdown")
                await asyncio.sleep(1)

    # ================= 🎲 تگ تصادفی =================
    elif text.startswith("تگ تصادفی"):
        try:
            count = 5
            parts = text.split()
            if len(parts) > 2 and parts[2].isdigit():
                count = int(parts[2])

            user_ids = list(chat_data.keys())
            if not user_ids:
                return await msg.reply_text("ℹ️ هیچ کاربری برای تگ تصادفی پیدا نشد.")

            sample = random.sample(user_ids, min(count, len(user_ids)))
            mentions = []
            for uid in sample:
                try:
                    member = await context.bot.get_chat_member(chat.id, int(uid))
                    if not member.user.is_bot:
                        name = member.user.first_name.replace("[", "").replace("]", "")
                        mentions.append(f"[{name}](tg://user?id={uid})")
                except:
                    continue

            await msg.reply_text("🎲 تگ تصادفی:\n" + " ".join(mentions), parse_mode="Markdown")
        except Exception as e:
            await msg.reply_text(f"⚠️ خطا در تگ تصادفی: {e}")


# ================= 🔧 ثبت هندلر =================
def register_tag_handlers(application, group_number: int = 14):
    """ثبت هندلر تگ کاربران"""
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
