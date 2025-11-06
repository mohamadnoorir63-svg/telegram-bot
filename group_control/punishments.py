import os
import json
import re
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, MessageHandler, filters
from datetime import timedelta, datetime

# ================= ⚙️ تنظیمات اولیه =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WARN_FILE = os.path.join(BASE_DIR, "warnings.json")
ALIAS_FILE = os.path.join(BASE_DIR, "custom_cmds.json")

SUDO_IDS = [8588347189]  # آیدی سودوها

# ساخت فایل‌ها در صورت نبود
for f in (WARN_FILE, ALIAS_FILE):
    if not os.path.exists(f):
        with open(f, "w", encoding="utf-8") as x:
            json.dump({}, x, ensure_ascii=False, indent=2)


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


# ================= 🚫 بن / 🤐 سکوت / ⚠️ اخطار =================
async def handle_punishments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not msg or chat.type not in ("group", "supergroup"):
        return

    text = (msg.text or "").strip()
    if not text:
        return

    # ---- اضافه کردن دستور سفارشی ----
    if text.startswith("افزودن دستور"):
        if not await _has_access(context, chat.id, user.id):
            return await msg.reply_text("🚫 فقط مدیران یا سودوها می‌تونن دستور اضافه کنن.")

        parts = text.split(" ", 2)
        if len(parts) < 3:
            return await msg.reply_text("📘 فرمت درست:\n<code>افزودن دستور [نام] [متن پاسخ]</code>", parse_mode="HTML")

        name = parts[1].strip()
        response = parts[2].strip()

        if name in ("بن", "سکوت", "اخطار", "حذف بن", "حذف سکوت", "حذف اخطار"):
            return await msg.reply_text("⚠️ نمی‌تونی دستورهای اصلی رو بازنویسی کنی.")

        data = _load_json(ALIAS_FILE)
        data[name] = response
        _save_json(ALIAS_FILE, data)
        return await msg.reply_text(f"✅ دستور جدید با نام <b>{name}</b> اضافه شد.", parse_mode="HTML")

    # ---- اگر دستور جزو aliasها بود ----
    aliases = _load_json(ALIAS_FILE)
    if text in aliases:
        # فقط روی ریپلای مجازه
        if not msg.reply_to_message:
            return await msg.reply_text("⚠️ باید روی پیام فرد ریپلای کنی.")

        target = msg.reply_to_message.from_user

        # اگر هدف خود ربات بود
        if target.id == context.bot.id:
            return await msg.reply_text("😅 با خودم شوخی داری؟ من که خودم خنگولم!")

        # بررسی مجوز
        if not await _has_access(context, chat.id, user.id):
            return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

        # عمل پیش‌فرض: حذف کاربر از گروه (kick)
        try:
            await context.bot.ban_chat_member(chat.id, target.id)
            await context.bot.unban_chat_member(chat.id, target.id)
            txt = aliases[text].replace("{name}", target.first_name)
            return await msg.reply_text(txt)
        except Exception as e:
            return await msg.reply_text(f"⚠️ خطا در اجرای دستور سفارشی: {e}")

    # ---- دستورات پیش‌فرض ----
    need_reply = ["بن", "حذف بن", "سکوت", "حذف سکوت", "اخطار", "حذف اخطار"]
    if text in need_reply and not msg.reply_to_message:
        return await msg.reply_text("⚠️ باید روی پیام کاربر ریپلای کنی.")

    target = msg.reply_to_message.from_user if msg.reply_to_message else None

    if target and target.id == context.bot.id:
        if "بن" in text:
            return await msg.reply_text("😅 منو بن کنی کل گروه می‌پره!")
        if "سکوت" in text:
            return await msg.reply_text("🤐 خودم سکوت کنم؟ تو بامزه‌ای!")
        if "اخطار" in text:
            return await msg.reply_text("⚠️ من که همیشه مودبم، اخطار واسه من چرا؟")
        return

    if text in need_reply:
        if not await _has_access(context, chat.id, user.id):
            return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    # 🚫 بن
    if text == "بن":
        try:
            await context.bot.ban_chat_member(chat.id, target.id)
            return await msg.reply_text(f"🚫 {target.first_name} از گروه بن شد.")
        except Exception as e:
            return await msg.reply_text(f"⚠️ خطا در بن: {e}")

    # 🔓 حذف بن
    if text == "حذف بن":
        try:
            await context.bot.unban_chat_member(chat.id, target.id)
            return await msg.reply_text(f"✅ {target.first_name} از بن خارج شد.")
        except Exception as e:
            return await msg.reply_text(f"⚠️ خطا در حذف بن: {e}")

    # 🤐 سکوت
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

    # 🔊 حذف سکوت
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

    # ⚠️ اخطار
    if text == "اخطار":
        data = _load_json(WARN_FILE)
        key = f"{chat.id}:{target.id}"
        data[key] = data.get(key, 0) + 1
        _save_json(WARN_FILE, data)
        count = data[key]

        if count >= 3:
            try:
                await context.bot.ban_chat_member(chat.id, target.id)
                data[key] = 0
                _save_json(WARN_FILE, data)
                return await msg.reply_text(f"🚫 {target.first_name} به‌دلیل ۳ اخطار بن شد.")
            except:
                return await msg.reply_text("⚠️ اخطار سوم ثبت شد ولی نتونستم بن کنم.")
        else:
            return await msg.reply_text(f"⚠️ {target.first_name} اخطار {count}/3 گرفت.")

    # 🗑 حذف اخطار
    if text == "حذف اخطار":
        data = _load_json(WARN_FILE)
        key = f"{chat.id}:{target.id}"
        if key in data:
            del data[key]
            _save_json(WARN_FILE, data)
            return await msg.reply_text(f"✅ اخطارهای {target.first_name} حذف شد.")
        else:
            return await msg.reply_text("ℹ️ این کاربر اخطاری نداشت.")


# ================= 🔧 ثبت هندلر =================
def register_punishment_handlers(application, group_number: int = 12):
    """ثبت هندلر دستورات تنبیه و سفارشی"""
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_punishments,
        ),
        group=group_number,
    )
