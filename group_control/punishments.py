import os
import json
import re
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, MessageHandler, filters
from datetime import timedelta, datetime

# ================= ⚙️ تنظیمات اولیه =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WARN_FILE = os.path.join(BASE_DIR, "warnings.json")

SUDO_IDS = [8588347189]  # آیدی سودوها

# ساخت فایل در صورت نبود
if not os.path.exists(WARN_FILE):
    with open(WARN_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)


def _load_json(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def _save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ================= 🔐 بررسی ادمین / سودو =================
async def _has_access(context, chat_id: int, user_id: int) -> bool:
    """بررسی دسترسی مجری دستور"""
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False


# ================= ⚙️ مدیریت دستورات تنبیه =================
async def handle_punishments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not msg or chat.type not in ("group", "supergroup"):
        return

    text = (msg.text or "").strip()
    if not text:
        return

    # لیست دستورات پایه
    base_cmds = ["بن", "حذف بن", "سکوت", "حذف سکوت", "اخطار", "حذف اخطار"]

    if not any(text.startswith(c) for c in base_cmds):
        return

    # ---- استخراج هدف (از ریپلای، @، یا آیدی عددی) ----
    target = None
    mentioned_username = re.search(r"@([A-Za-z0-9_]{5,32})", text)
    user_id_match = re.search(r"\b(\d{6,15})\b", text)

    if msg.reply_to_message:
        target = msg.reply_to_message.from_user
    elif user_id_match:
        try:
            target_id = int(user_id_match.group(1))
            chat_member = await context.bot.get_chat_member(chat.id, target_id)
            target = chat_member.user
        except Exception:
            target = None
    elif mentioned_username:
        username = mentioned_username.group(1)
        try:
            user_obj = await context.bot.get_chat(username)
            target = user_obj
        except Exception:
            target = None

    if not target:
        return await msg.reply_text(
            "⚠️ کاربر یافت نشد.\n"
            "برای استفاده:\n"
            "📎 روی پیام فرد ریپلای کن یا آیدی عددی او را بنویس.\n"
            "(@username فقط اگر فرد در گروه فعال باشد کار می‌کند.)"
        )

    # ---- بررسی سطح دسترسی ----
    if not await _has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    # ---- محافظت از خود ربات، سودوها و مدیران ----
    if target.id == context.bot.id:
        return await msg.reply_text("😅 نمی‌تونم خودم رو تنبیه کنم.")

    # بررسی فقط در صورت وجود واقعی target در گروه
    try:
        t_member = await context.bot.get_chat_member(chat.id, target.id)
        if t_member.status in ("creator", "administrator"):
            return await msg.reply_text("🛡 این کاربر مدیر گروهه، نمی‌تونی تنبیهش کنی!")
    except:
        pass

    if target.id in SUDO_IDS:
        return await msg.reply_text("👑 این کاربر جزو سودوهاست و مصون از تنبیهه!")

    # ---- اجرای دستور ----
    try:
        if text.startswith("بن"):
            await context.bot.ban_chat_member(chat.id, target.id)
            return await msg.reply_text(f"🚫 {target.first_name} از گروه بن شد.")

        elif text.startswith("حذف بن"):
            await context.bot.unban_chat_member(chat.id, target.id)
            return await msg.reply_text(f"✅ {target.first_name} از بن خارج شد.")

        elif text.startswith("سکوت"):
            m = re.search(r"سکوت\s*(\d+)?\s*(ثانیه|دقیقه|ساعت)?", text)
            if m and m.group(1):
                num = int(m.group(1))
                unit = m.group(2)
                seconds = num * 3600 if unit == "ساعت" else (num * 60 if unit == "دقیقه" else num)
            else:
                seconds = 3600  # پیش‌فرض ۱ ساعت
            until_date = datetime.utcnow() + timedelta(seconds=seconds)
            await context.bot.restrict_chat_member(
                chat.id, target.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until_date
            )
            return await msg.reply_text(f"🤐 {target.first_name} برای {seconds} ثانیه در سکوت است.")

        elif text.startswith("حذف سکوت"):
            await context.bot.restrict_chat_member(
                chat.id, target.id,
                permissions=ChatPermissions(can_send_messages=True)
            )
            return await msg.reply_text(f"🔊 {target.first_name} از سکوت خارج شد.")

        elif text.startswith("اخطار"):
            warns = _load_json(WARN_FILE)
            key = f"{chat.id}:{target.id}"
            warns[key] = warns.get(key, 0) + 1
            _save_json(WARN_FILE, warns)
            if warns[key] >= 3:
                await context.bot.ban_chat_member(chat.id, target.id)
                warns[key] = 0
                _save_json(WARN_FILE, warns)
                return await msg.reply_text(f"🚫 {target.first_name} به‌دلیل ۳ اخطار بن شد.")
            else:
                return await msg.reply_text(f"⚠️ {target.first_name} اخطار {warns[key]}/3 گرفت.")

        elif text.startswith("حذف اخطار"):
            warns = _load_json(WARN_FILE)
            key = f"{chat.id}:{target.id}"
            if key in warns:
                del warns[key]
                _save_json(WARN_FILE, warns)
                return await msg.reply_text(f"✅ اخطارهای {target.first_name} حذف شد.")
            return await msg.reply_text("ℹ️ این کاربر اخطاری نداشت.")

    except Exception as e:
        return await msg.reply_text(f"⚠️ خطا در اجرای دستور: {e}")


# ================= 🔧 ثبت هندلر =================
def register_punishment_handlers(application, group_number: int = 12):
    """ثبت هندلر دستورات تنبیهی در گروه"""
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_punishments,
        ),
        group=group_number,
    )
