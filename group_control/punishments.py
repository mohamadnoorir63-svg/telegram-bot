import os
import json
import re
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, MessageHandler, filters
from datetime import timedelta, datetime

# ================= ⚙️ تنظیمات اولیه =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WARN_FILE = os.path.join(BASE_DIR, "warnings.json")

SUDO_IDS = [8588347189]  # آیدی سودوها (خودت + هرکس خواستی)

if not os.path.exists(WARN_FILE):
    with open(WARN_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)


def _load_warnings():
    try:
        with open(WARN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def _save_warnings(data):
    with open(WARN_FILE, "w", encoding="utf-8") as f:
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


# ================= 🚫 بن / 🤐 سکوت / ⚠️ اخطار =================
async def handle_punishments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not msg or chat.type not in ("group", "supergroup"):
        return

    text = (msg.text or "").strip()

    # فقط روی پیام ریپلای اعمال میشن
    need_reply = ["بن", "حذف بن", "سکوت", "حذف سکوت", "اخطار", "حذف اخطار"]
    if text in need_reply and not msg.reply_to_message:
        return await msg.reply_text("⚠️ باید روی پیام کاربر ریپلای کنی.")

    # هدف
    target = msg.reply_to_message.from_user if msg.reply_to_message else None

    # 😅 شوخی اگر هدف خود ربات باشه
    if target and target.id == context.bot.id:
        if "بن" in text:
            return await msg.reply_text("😅 می‌خوای منو بن کنی؟ من خود گروه رو نگه می‌دارم!")
        if "سکوت" in text:
            return await msg.reply_text("🤐 خودم سکوت کنم؟ تو بامزه‌ای!")
        if "اخطار" in text:
            return await msg.reply_text("⚠️ من که همیشه مودبم، اخطار واسه من چرا؟")
        return

    # جلوگیری از تنبیه مدیر یا سودو
    if target:
        target_member = await context.bot.get_chat_member(chat.id, target.id)
        if target.id in SUDO_IDS:
            return await msg.reply_text("👑 این کاربر سودو است، نمی‌تونی بن یا سکوتش کنی.")
        if target_member.status == "creator":
            return await msg.reply_text("👑 این کاربر سازنده گروه است.")
        if target_member.status == "administrator":
            return await msg.reply_text("🛡 این کاربر مدیر گروه است.")

    # بررسی مجوز مجری
    if text in need_reply:
        if not await _has_access(context, chat.id, user.id):
            return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    # ========== 🚫 بن ==========
    if text == "بن":
        try:
            await context.bot.ban_chat_member(chat.id, target.id)
            return await msg.reply_text(f"🚫 {target.first_name} از گروه بن شد.")
        except Exception as e:
            return await msg.reply_text(f"⚠️ خطا در بن: {e}")

    # ========== 🔓 حذف بن ==========
    if text == "حذف بن":
        try:
            await context.bot.unban_chat_member(chat.id, target.id)
            return await msg.reply_text(f"✅ {target.first_name} از بن خارج شد.")
        except Exception as e:
            return await msg.reply_text(f"⚠️ خطا در حذف بن: {e}")

    # ========== 🤐 سکوت ==========
    if text.startswith("سکوت"):
        try:
            match = re.search(r"(\d+)\s*(ثانیه|دقیقه)?", text)
            duration = 0
            if match:
                num = int(match.group(1))
                unit = match.group(2)
                duration = num * 60 if unit == "دقیقه" else num

            until_date = datetime.utcnow() + timedelta(seconds=duration or 3600)
            await context.bot.restrict_chat_member(
                chat.id,
                target.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until_date
            )
            t = f"برای {duration} ثانیه" if duration else "به‌صورت نامحدود"
            return await msg.reply_text(f"🤐 {target.first_name} {t} در سکوت قرار گرفت.")
        except Exception as e:
            return await msg.reply_text(f"⚠️ خطا در سکوت: {e}")

    # ========== 🔊 حذف سکوت ==========
    if text == "حذف سکوت":
        try:
            await context.bot.restrict_chat_member(
                chat.id,
                target.id,
                permissions=ChatPermissions(can_send_messages=True)
            )
            return await msg.reply_text(f"🔊 {target.first_name} از سکوت خارج شد.")
        except Exception as e:
            return await msg.reply_text(f"⚠️ خطا در حذف سکوت: {e}")

    # ========== ⚠️ اخطار ==========
    if text == "اخطار":
        data = _load_warnings()
        key = f"{chat.id}:{target.id}"
        data[key] = data.get(key, 0) + 1
        _save_warnings(data)
        count = data[key]
        if count >= 3:
            try:
                await context.bot.ban_chat_member(chat.id, target.id)
                data[key] = 0
                _save_warnings(data)
                return await msg.reply_text(f"🚫 {target.first_name} به‌دلیل ۳ اخطار بن شد.")
            except:
                return await msg.reply_text("⚠️ اخطار سوم ثبت شد ولی نتونستم بن کنم.")
        else:
            return await msg.reply_text(f"⚠️ {target.first_name} اخطار {count}/3 گرفت.")

    # ========== 🗑 حذف اخطار ==========
    if text == "حذف اخطار":
        data = _load_warnings()
        key = f"{chat.id}:{target.id}"
        if key in data:
            del data[key]
            _save_warnings(data)
            return await msg.reply_text(f"✅ اخطارهای {target.first_name} حذف شد.")
        else:
            return await msg.reply_text("ℹ️ این کاربر اخطاری نداشت.")


# ================= 🔧 ثبت هندلر =================
def register_punishment_handlers(application, group_number: int = 11):
    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND
            & filters.ChatType.GROUPS,
            handle_punishments,
        ),
        group=group_number,
    )
