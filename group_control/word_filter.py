import os
import json
import re
import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

# ================= ⚙️ تنظیمات اولیه =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILTER_FILE = os.path.join(BASE_DIR, "filtered_words.json")

SUDO_IDS = [8588347189]  # آیدی سودوها (خودت + هرکس خواستی)

if not os.path.exists(FILTER_FILE):
    with open(FILTER_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)


# ================= 📁 توابع کمکی =================
def _load_filters():
    try:
        with open(FILTER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def _save_filters(data):
    with open(FILTER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _time_left_str(expire_timestamp):
    """تبدیل timestamp به مدت باقیمانده"""
    if not expire_timestamp:
        return "دائمی"
    remain = expire_timestamp - datetime.utcnow().timestamp()
    if remain <= 0:
        return "منقضی‌شده"
    m, s = divmod(int(remain), 60)
    h, m = divmod(m, 60)
    parts = []
    if h:
        parts.append(f"{h} ساعت")
    if m:
        parts.append(f"{m} دقیقه")
    if s and not h:
        parts.append(f"{s} ثانیه")
    return "، ".join(parts) + " باقی‌مانده"


# ================= 🔐 بررسی ادمین / سودو =================
async def _has_access(context, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False


# ================= 🚫 مدیریت فیلتر کلمات =================
async def handle_word_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    text = (msg.text or "").strip()

    if chat.type not in ("group", "supergroup"):
        return

    data = _load_filters()
    chat_key = str(chat.id)
    if chat_key not in data:
        data[chat_key] = {}

    # فقط مدیران یا سودوها
    if text.startswith("فیلتر") or text.startswith("حذف فیلتر") or text == "لیست فیلترها":
        if not await _has_access(context, chat.id, user.id):
            return await msg.reply_text("🚫 فقط مدیران یا سودوها مجاز به مدیریت فیلترها هستند!")

    # ========== ➕ افزودن فیلتر ==========
    if text.startswith("فیلتر"):
        parts = text.split(maxsplit=2)
        if len(parts) < 2:
            return await msg.reply_text("⚠️ لطفاً کلمه‌ای که باید فیلتر شود را بنویس. مثال:\n`فیلتر تست`", parse_mode="Markdown")

        word = parts[1].strip()
        duration = 0

        match = re.search(r"(\d+)\s*(ساعت|دقیقه|ثانیه)", text)
        if match:
            num = int(match.group(1))
            unit = match.group(2)
            if unit == "ساعت":
                duration = num * 3600
            elif unit == "دقیقه":
                duration = num * 60
            elif unit == "ثانیه":
                duration = num

        expire_time = datetime.utcnow().timestamp() + duration if duration > 0 else None
        data[chat_key][word] = expire_time
        _save_filters(data)

        if duration > 0:
            await msg.reply_text(f"🚫 کلمه «{word}» برای {num} {unit} فیلتر شد.")
            async def auto_unfilter():
                await asyncio.sleep(duration)
                filters_data = _load_filters()
                if chat_key in filters_data and word in filters_data[chat_key]:
                    del filters_data[chat_key][word]
                    _save_filters(filters_data)
                    try:
                        await context.bot.send_message(chat.id, f"⌛️ فیلتر «{word}» منقضی شد.")
                    except:
                        pass
            asyncio.create_task(auto_unfilter())
        else:
            await msg.reply_text(f"🚫 کلمه «{word}» به‌صورت دائمی فیلتر شد.")

    # ========== ❌ حذف فیلتر ==========
    elif text.startswith("حذف فیلتر"):
        parts = text.split(maxsplit=2)
        if len(parts) < 2:
            return await msg.reply_text("⚠️ لطفاً کلمه‌ای که باید از فیلتر حذف شود را بنویس.")
        word = parts[1].strip()
        if word in data[chat_key]:
            del data[chat_key][word]
            _save_filters(data)
            await msg.reply_text(f"✅ فیلتر «{word}» حذف شد.")
        else:
            await msg.reply_text(f"ℹ️ کلمه «{word}» در فهرست فیلتر نیست.")

    # ========== 📋 لیست فیلترها ==========
    elif text == "لیست فیلترها":
        filters_for_chat = data.get(chat_key, {})
        if not filters_for_chat:
            return await msg.reply_text("ℹ️ هیچ فیلتری فعال نیست.")
        lines = ["🚫 فهرست کلمات فیلترشده:"]
        now = datetime.utcnow().timestamp()
        for word, expire in filters_for_chat.items():
            lines.append(f"• <b>{word}</b> — {_time_left_str(expire)}")
        return await msg.reply_text("\n".join(lines), parse_mode="HTML")

    # ========== 🔍 بررسی پیام‌های کاربران ==========
    else:
        if await _has_access(context, chat.id, user.id):
            return  # مدیرها بررسی نمی‌شن

        for word, expire_time in list(data.get(chat_key, {}).items()):
            # حذف خودکار فیلتر منقضی‌شده
            if expire_time and datetime.utcnow().timestamp() > expire_time:
                del data[chat_key][word]
                _save_filters(data)
                continue

            # بررسی وجود کلمه
            if re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE):
                try:
                    await msg.delete()
                    await msg.reply_text(f"🚫 پیام حذف شد چون شامل کلمه فیلترشده «{word}» بود.", quote=True)
                except:
                    pass
                break


# ================= 🔧 ثبت هندلر =================
def register_filter_handlers(application, group_number: int = 13):
    """ثبت هندلر فیلتر کلمات"""
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_word_filter,
        ),
        group=group_number,
    )
