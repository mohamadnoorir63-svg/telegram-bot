import os
import json
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, MessageHandler, filters

# ================= ⚙️ تنظیمات اولیه =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WARN_FILE = os.path.join(BASE_DIR, "warnings.json")

SUDO_IDS = [8588347189]  # آیدی سودوها (خودت + هرکس خواستی)

# فایل اخطارها
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

    # فقط روی پیام ریپلای اعمال میشن (به جز "اخطار من")
    need_reply = ["بن", "سکوت", "رفع سکوت", "اخطار", "حذف اخطار"]
    if text in need_reply and not msg.reply_to_message:
        return await msg.reply_text("⚠️ باید روی پیام کاربر ریپلای کنی.")

    # دسترسی مدیر یا سودو
    if text in need_reply:
        if not await _has_access(context, chat.id, user.id):
            return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    # ========== 🚫 بن ==========
    if msg.reply_to_message and text in ("بن", "بن کن"):
        target = msg.reply_to_message.from_user
        try:
            await context.bot.ban_chat_member(chat.id, target.id)
            return await msg.reply_text(f"🚫 {target.first_name} از گروه بن شد.")
        except Exception as e:
            return await msg.reply_text(f"⚠️ خطا در بن: {e}")

    # ========== 🤐 سکوت ==========
    if msg.reply_to_message and text in ("سکوت", "میوت", "mute"):
        target = msg.reply_to_message.from_user
        try:
            await context.bot.restrict_chat_member(
                chat.id,
                target.id,
                permissions=ChatPermissions(can_send_messages=False)
            )
            return await msg.reply_text(f"🤐 {target.first_name} در سکوت قرار گرفت.")
        except Exception as e:
            return await msg.reply_text(f"⚠️ خطا در سکوت: {e}")

    # ========== 🔊 رفع سکوت ==========
    if msg.reply_to_message and text in ("رفع سکوت", "آن‌میوت", "unmute"):
        target = msg.reply_to_message.from_user
        try:
            await context.bot.restrict_chat_member(
                chat.id,
                target.id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True
                )
            )
            return await msg.reply_text(f"🔊 {target.first_name} از سکوت خارج شد.")
        except Exception as e:
            return await msg.reply_text(f"⚠️ خطا در رفع سکوت: {e}")

    # ========== ⚠️ اخطار ==========
    if msg.reply_to_message and text in ("اخطار",):
        target = msg.reply_to_message.from_user
        data = _load_warnings()
        key = f"{chat.id}:{target.id}"
        data[key] = data.get(key, 0) + 1
        _save_warnings(data)
        count = data[key]

        if count >= 3:
            try:
                await context.bot.ban_chat_member(chat.id, target.id)
                data[key] = 0  # ریست بعد از بن
                _save_warnings(data)
                return await msg.reply_text(f"🚫 {target.first_name} به‌دلیل ۳ اخطار بن شد.")
            except Exception as e:
                return await msg.reply_text(f"⚠️ اخطار سوم ثبت شد ولی بن نشد: {e}")
        else:
            return await msg.reply_text(f"⚠️ {target.first_name} اخطار {count}/3 گرفت.")

    # ========== 🗑 حذف اخطار ==========
    if msg.reply_to_message and text in ("حذف اخطار", "ریست اخطار"):
        target = msg.reply_to_message.from_user
        data = _load_warnings()
        key = f"{chat.id}:{target.id}"
        if key in data:
            del data[key]
            _save_warnings(data)
            return await msg.reply_text(f"✅ اخطارهای {target.first_name} پاک شد.")
        else:
            return await msg.reply_text("ℹ️ این کاربر اخطاری نداشت.")

    # ========== 👤 اخطار من ==========
    if text == "اخطار من":
        data = _load_warnings()
        key = f"{chat.id}:{user.id}"
        cnt = data.get(key, 0)
        return await msg.reply_text(f"📌 اخطار شما: {cnt}/3")


# ================= 🔧 ثبت هندلر =================
def register_punishment_handlers(application, group_number: int = 11):
    """
    افزودن هندلر تنبیهات به برنامه اصلی.
    group_number را بر اساس نظم بقیه هندلرها تنظیم کن.
    """
    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND
            & filters.ChatType.GROUPS,  # ✅ اصلاح‌شده برای گروه‌ها
            handle_punishments,
        ),
        group=group_number,
    )
