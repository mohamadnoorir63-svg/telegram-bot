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

    # ---- استخراج هدف (ریپلای، @username، یا آیدی) ----
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

    # ---- بررسی سطح دسترسی ----
    if not await _has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    # ---- محافظت از خود ربات و سودو و مدیران ----
    if target:
        if target.id == context.bot.id:
            return await msg.reply_text("😅 نمی‌تونم خودم رو تنبیه کنم.")
        try:
            t_member = await context.bot.get_chat_member(chat.id, target.id)
            if t_member.status in ("creator", "administrator"):
                return await msg.reply_text("🛡 این کاربر مدیر گروهه، نمی‌تونی تنبیهش کنی!")
        except:
            pass
        if target.id in SUDO_IDS:
            return await msg.reply_text("👑 این کاربر جزو سودوهاست و مصون از تنبیهه!")

    # ---- اجرای دستورات ----

    # ---- بن ----
    if "بن" in text:
        if not target:
            return await msg.reply_text("⚠️ برای بن، باید روی پیام ریپلای کنید یا آیدی/یوزرنیم وارد کنید.")
        await context.bot.ban_chat_member(chat.id, target.id)
        return await msg.reply_text(f"🚫 {target.first_name} از گروه بن شد.")

    # ---- حذف بن ----
    if "حذف بن" in text:
        if not target:
            return await msg.reply_text("⚠️ برای حذف بن، باید روی پیام ریپلای کنید یا آیدی/یوزرنیم وارد کنید.")
        await context.bot.unban_chat_member(chat.id, target.id)
        return await msg.reply_text(f"✅ {target.first_name} از بن خارج شد.")

    # ---- سکوت ----
    if "سکوت" in text:
        if not target:
            return await msg.reply_text("⚠️ برای سکوت، باید روی پیام ریپلای کنید یا آیدی/یوزرنیم وارد کنید.")
        m = re.search(r"سکوت\s*(\d+)?\s*(ثانیه|دقیقه|ساعت)?", text)
        if m and m.group(1):
            num = int(m.group(1))
            unit = m.group(2)
            seconds = num * 3600 if unit == "ساعت" else (num * 60 if unit == "دقیقه" else num)
        else:
            seconds = 3600
        until_date = datetime.utcnow() + timedelta(seconds=seconds)
        await context.bot.restrict_chat_member(
            chat.id, target.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        return await msg.reply_text(f"🤐 {target.first_name} برای {seconds} ثانیه در سکوت است.")

    # ---- حذف سکوت ----
    if "حذف سکوت" in text:
        if not target:
            return await msg.reply_text("⚠️ برای حذف سکوت، باید روی پیام ریپلای کنید یا آیدی/یوزرنیم وارد کنید.")
        await context.bot.restrict_chat_member(
            chat.id, target.id,
            permissions=ChatPermissions(can_send_messages=True)
        )
        return await msg.reply_text(f"🔊 {target.first_name} از سکوت خارج شد.")

    # ---- اخطار ----
    if "اخطار" in text:
        if not target:
            return await msg.reply_text("⚠️ برای اخطار، باید روی پیام ریپلای کنید یا آیدی/یوزرنیم وارد کنید.")
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

    # ---- حذف اخطار ----
    if "حذف اخطار" in text:
        if not target:
            return await msg.reply_text("⚠️ برای حذف اخطار، باید روی پیام ریپلای کنید یا آیدی/یوزرنیم وارد کنید.")
        warns = _load_json(WARN_FILE)
        key = f"{chat.id}:{target.id}"
        if key in warns:
            del warns[key]
            _save_json(WARN_FILE, warns)
            return await msg.reply_text(f"✅ اخطارهای {target.first_name} حذف شد.")
        return await msg.reply_text("ℹ️ این کاربر اخطاری نداشت.")


# ================= 🔧 ثبت هندلر =================
def register_punishment_handlers(application, group_number: int = 12):
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_punishments,
        ),
        group=group_number,
    )
