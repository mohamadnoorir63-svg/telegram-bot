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

# ---------- یوزربات ----------
try:
    from userbot_module.userbot import client as userbot_client  # مسیر سشن یوزربات
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

# ================= 👥 ارسال تگ با یوزربات (حتی اگه داخل گروه نباشه) =================
async def send_tag_via_userbot(mentions, chat_id):
    if not userbot_client:
        return
    try:
        chunk_size = 20
        for i in range(0, len(mentions), chunk_size):
            chunk = mentions[i:i + chunk_size]
            try:
                await userbot_client.send_message(chat_id, "👥 " + " ".join(chunk), parse_mode="md")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"⚠️ خطا در ارسال تگ توسط یوزربات: {e}")
    except Exception as e:
        print(f"⚠️ خطای کلی یوزربات در تگ: {e}")

# ================= 👥 تگ کاربران (حالت ترکیبی) =================
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

    data = _load_activity()
    chat_data = data.get(str(chat.id), {})

    mentions = []

    # ---------- تگ همه ----------
    if text == "تگ همه":
        participants = []
        if userbot_client:
            try:
                # 🔹 تلاش برای دریافت اعضا از یوزربات
                participants = await userbot_client.get_participants(chat.id)
            except Exception as e:
                print(f"⚠️ یوزربات نتونست اعضا رو بگیره: {e}")

        # اگر یوزربات عضو گروه نبود → از activity.json استفاده کن
        if not participants and chat_data:
            print("ℹ️ استفاده از داده‌های ذخیره‌شده activity.json برای تگ همه")
            for uid_str in chat_data.keys():
                try:
                    member = await context.bot.get_chat_member(chat.id, int(uid_str))
                    if not member.user.is_bot:
                        participants.append(member.user)
                except:
                    continue

        # ساخت منشن‌ها
        mentions = [f"[{getattr(m, 'first_name', 'ناشناس')}](tg://user?id={m.id})" for m in participants if not getattr(m, "bot", False)]

    # ---------- تگ مدیران ----------
    elif text == "تگ مدیران":
        try:
            admins = await context.bot.get_chat_administrators(chat.id)
            mentions = [f"[{a.user.first_name}](tg://user?id={a.user.id})" for a in admins if not a.user.is_bot]
        except:
            await msg.reply_text("⚠️ خطا در دریافت مدیران گروه")

    # ---------- تگ فعال ----------
    elif text == "تگ فعال":
        now = datetime.utcnow().timestamp()
        active_users = [uid for uid, t in chat_data.items() if now - t <= 24 * 3600]
        for uid in active_users:
            try:
                member = await context.bot.get_chat_member(chat.id, int(uid))
                if not member.user.is_bot:
                    mentions.append(f"[{member.user.first_name}](tg://user?id={member.user.id})")
            except:
                continue

    # ---------- تگ غیرفعال ----------
    elif text == "تگ غیرفعال":
        now = datetime.utcnow().timestamp()
        inactive_users = [uid for uid, t in chat_data.items() if now - t > 24 * 3600]
        for uid in inactive_users:
            try:
                member = await context.bot.get_chat_member(chat.id, int(uid))
                if not member.user.is_bot:
                    mentions.append(f"[{member.user.first_name}](tg://user?id={member.user.id})")
            except:
                continue

    # ---------- تگ تصادفی ----------
    elif text.startswith("تگ تصادفی"):
        parts = text.split()
        count = 5
        if len(parts) > 2 and parts[2].isdigit():
            count = int(parts[2])

        sample_users = []
        if userbot_client:
            try:
                participants = await userbot_client.get_participants(chat.id)
                non_bots = [m for m in participants if not m.bot]
                sample_users = random.sample(non_bots, min(count, len(non_bots)))
            except:
                pass

        if not sample_users and chat_data:
            uid_list = list(chat_data.keys())
            chosen = random.sample(uid_list, min(count, len(uid_list)))
            for uid in chosen:
                try:
                    member = await context.bot.get_chat_member(chat.id, int(uid))
                    if not member.user.is_bot:
                        sample_users.append(member.user)
                except:
                    continue

        mentions = [f"[{m.first_name}](tg://user?id={m.id})" for m in sample_users]

    # ---------- ارسال تگ‌ها ----------
    if mentions:
        # ارسال با ربات اصلی
        chunk_size = 20
        for i in range(0, len(mentions), chunk_size):
            chunk = mentions[i:i + chunk_size]
            await msg.reply_text("👥 " + " ".join(chunk), parse_mode="Markdown")
            await asyncio.sleep(1)

        # ارسال همزمان با یوزربات
        await send_tag_via_userbot(mentions, chat.id)
    else:
        await msg.reply_text("⚠️ هیچ کاربری برای تگ یافت نشد.")

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
