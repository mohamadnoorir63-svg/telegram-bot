import os
import json
import re
import asyncio
from datetime import datetime
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
        data[chat_key] = {"filters": {}, "enabled": True}

    filters_for_chat = data[chat_key]["filters"]

    # بررسی دسترسی مدیر/سودو
    admin_cmds = ("فیلتر", "حذف فیلتر", "لیست فیلتر", "فیلتر روشن", "فیلتر خاموش")
    if any(text.startswith(cmd) or text == cmd for cmd in admin_cmds):
        if not await _has_access(context, chat.id, user.id):
            return await msg.reply_text("🚫 فقط مدیران یا سودوها مجاز به مدیریت فیلترها هستند!")

    # روشن/خاموش کردن فیلتر
    if text == "فیلتر خاموش":
        if not data[chat_key]["enabled"]:
            return await msg.reply_text("ℹ️ فیلتر کلمات از قبل خاموش بود.")
        data[chat_key]["enabled"] = False
        _save_filters(data)
        return await msg.reply_text("🔕 فیلتر کلمات غیرفعال شد.")

    if text == "فیلتر روشن":
        if data[chat_key]["enabled"]:
            return await msg.reply_text("ℹ️ فیلتر کلمات از قبل فعال بود.")
        data[chat_key]["enabled"] = True
        _save_filters(data)
        return await msg.reply_text("✅ فیلتر کلمات فعال شد.")

    # ================= ➕ افزودن فیلتر =================
    if text.startswith("فیلتر "):
        # استخراج متن بعد از دستور فیلتر
        remainder = text[len("فیلتر "):].strip()
        if not remainder:
            return await msg.reply_text(
                "⚠️ لطفاً بنویس چه کلمه‌ای باید فیلتر بشه.\nمثلاً:\n`فیلتر تست`\nیا\n`فیلتر تست 2 ساعت`",
                parse_mode="Markdown"
            )

        # تشخیص کلمه و مدت زمان (ساعت، دقیقه، ثانیه) اگر بود
        match = re.search(r"(.+?)\s*(\d+\s*(ساعت|دقیقه|ثانیه))?$", remainder)
        if match:
            word = match.group(1).strip()
            duration = 0
            if match.group(2):
                num, unit = re.match(r"(\d+)\s*(ساعت|دقیقه|ثانیه)", match.group(2)).groups()
                num = int(num)
                if unit == "ساعت":
                    duration = num * 3600
                elif unit == "دقیقه":
                    duration = num * 60
                elif unit == "ثانیه":
                    duration = num
            expire_time = datetime.utcnow().timestamp() + duration if duration > 0 else None
            filters_for_chat[word] = expire_time
            _save_filters(data)

            if duration > 0:
                await msg.reply_text(f"🚫 کلمه «{word}» برای {num} {unit} فیلتر شد.")
                async def auto_unfilter():
                    await asyncio.sleep(duration)
                    filters_data = _load_filters()
                    if chat_key in filters_data and word in filters_data[chat_key]["filters"]:
                        del filters_data[chat_key]["filters"][word]
                        _save_filters(filters_data)
                        try:
                            await context.bot.send_message(chat.id, f"⌛️ فیلتر «{word}» منقضی شد.")
                        except:
                            pass
                asyncio.create_task(auto_unfilter())
            else:
                await msg.reply_text(f"🚫 کلمه «{word}» به‌صورت دائمی فیلتر شد.")
        return

    # ================= ❌ حذف فیلتر =================
    elif text.startswith("حذف فیلتر"):
        word = text[len("حذف فیلتر"):].strip()
        if not word:
            return await msg.reply_text("⚠️ لطفاً بنویس کدوم کلمه از فیلتر حذف بشه.")
        if word in filters_for_chat:
            del filters_for_chat[word]
            _save_filters(data)
            await msg.reply_text(f"✅ فیلتر «{word}» حذف شد.")
        else:
            await msg.reply_text(f"ℹ️ کلمه «{word}» در لیست فیلتر نیست.")
        return

    # ================= 📋 لیست فیلترها =================
    elif text == "لیست فیلتر":
        filters_for_chat = data[chat_key]["filters"]
        status = "✅ فعال" if data[chat_key]["enabled"] else "🔕 غیرفعال"
        if not filters_for_chat:
            return await msg.reply_text(f"ℹ️ هیچ فیلتری در این گروه وجود ندارد.\n🔧 وضعیت فیلتر: {status}")
        lines = [f"🚫 فهرست فیلترهای فعال در گروه {chat.title or 'بدون‌نام'}:", f"🔧 وضعیت فیلتر: {status}\n"]
        for word, expire in filters_for_chat.items():
            lines.append(f"• <b>{word}</b> — {_time_left_str(expire)}")
        return await msg.reply_text("\n".join(lines), parse_mode="HTML")

    # ================= 🔍 بررسی پیام‌ها =================
    else:
        if not data[chat_key]["enabled"] or await _has_access(context, chat.id, user.id):
            return

        for word, expire_time in list(filters_for_chat.items()):
            # حذف خودکار فیلترهای منقضی‌شده
            if expire_time and datetime.utcnow().timestamp() > expire_time:
                del filters_for_chat[word]
                _save_filters(data)
                continue

            # بررسی وجود کلمه در پیام
            if word.lower() in text.lower():
                try:
                    await msg.delete()
                    warning_msg = await context.bot.send_message(
                        chat_id=chat.id,
                        text=(
                            f"🌙 پیام <b>{user.first_name}</b> پاک شد ⚡️\n"
                            f"🪄 دلیل: <tg-spoiler>{word}</tg-spoiler>\n"
                            f"🧩 رعایت قوانین = محیط بهتر ✨"
                        ),
                        parse_mode="HTML"
                    )
                    # حذف پیام هشدار بعد از 10 ثانیه
                    await asyncio.sleep(10)
                    await warning_msg.delete()
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
