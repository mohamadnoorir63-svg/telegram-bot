import os
import json
import re
import asyncio
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, MessageHandler, filters
from datetime import timedelta, datetime

# ================= ⚙️ Grundeinstellungen =================
BASIS_VERZEICHNIS = os.path.dirname(os.path.abspath(__file__))
WARN_DATEI = os.path.join(BASIS_VERZEICHNIS, "warnings.json")
SUDO_IDS = [8588347189]  # Admin-IDs

# فایل‌ها را بساز اگر موجود نیست
if not os.path.exists(WARN_DATEI):
    with open(WARN_DATEI, "w", encoding="utf-8") as x:
        json.dump({}, x, ensure_ascii=False, indent=2)

# ================= 🔧 JSON Helfer =================
def lade_json(datei):
    try:
        with open(datei, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def speichere_json(datei, daten):
    with open(datei, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)

# ================= 🔐 Zugriffsprüfung =================
async def hat_zugriff(context, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_IDS:
        return True
    try:
        mitglied = await context.bot.get_chat_member(chat_id, user_id)
        return mitglied.status in ("creator", "administrator")
    except:
        return False

# ================= 🔧 Zielbenutzer دقیق =================
async def loese_ziel(msg, context, chat_id):
    """
    پیدا کردن دقیق کاربر:
    1. ریپلای
    2. @username یا user_id بعد از دستور
    """
    if msg.reply_to_message:
        return msg.reply_to_message.from_user, None

    text = (msg.text or "").strip()
    # بررسی دقیق: فقط دستور + یک کاربر معتبر
    m = re.search(r"^\S+\s+(@[A-Za-z0-9_]{5,32}|\d+)$", text)
    if m:
        target_str = m.group(1)
        if target_str.startswith("@"):
            username = target_str[1:]
            try:
                cm = await context.bot.get_chat_member(chat_id, username)
                return cm.user, None
            except:
                return None, username
        else:
            try:
                target_id = int(target_str)
                cm = await context.bot.get_chat_member(chat_id, target_id)
                return cm.user, None
            except:
                return None, None
    return None, None

# ================= 📦 پیام موقت =================
async def sende_temp(msg, text, context, loeschen_nach=10):
    gesendet = await msg.reply_text(text)
    asyncio.create_task(loesche_nach(gesendet, loeschen_nach, context))

async def loesche_nach(message, verzogerung, context):
    await asyncio.sleep(verzogerung)
    try:
        await context.bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

# ================= 🔧 Haupt-Handler =================
async def registriere_bestrafen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not msg or chat.type not in ("group", "supergroup"):
        return

    text = (msg.text or "").strip()
    if not text:
        return

    # بررسی دسترسی
    if not await hat_zugriff(context, chat.id, user.id):
        return

    # پیدا کردن هدف
    target, mention_failed = await loese_ziel(msg, context, chat.id)
    if not target:
        if mention_failed:
            await sende_temp(msg, f"⚠️ کاربر @{mention_failed} پیدا نشد.", context)
        return

    # بررسی بات
    if target.id == context.bot.id:
        await sende_temp(msg, "😅 من ربات هستم — نمی‌توانم تنبیه شوم.", context)
        return

    # بررسی سودو
    if target.id in SUDO_IDS:
        await sende_temp(msg, "🚫 امکان اجرای دستور روی این کاربر سودو وجود ندارد.", context)
        return

    # بررسی مدیر یا سازنده گروه
    try:
        t_member = await context.bot.get_chat_member(chat.id, target.id)
        if t_member.status in ("creator", "administrator"):
            await sende_temp(msg, "🛡 امکان اجرای دستور روی این کاربر مدیر یا سازنده گروه وجود ندارد.", context)
            return
    except:
        await sende_temp(msg, "⚠️ کاربر موردنظر در گروه نیست.", context)
        return

    # دستورات دقیق فارسی
    BEFEHLE = {
        "ban": r"^بن\s+(@[A-Za-z0-9_]{5,32}|\d+)$",
        "unban": r"^حذف\s*بن\s+(@[A-Za-z0-9_]{5,32}|\d+)$",
        "mute": r"^سکوت\s+(@[A-Za-z0-9_]{5,32}|\d+)(?:\s+(\d+)\s*(ثانیه|دقیقه|ساعت)?)?$",
        "unmute": r"^حذف\s*سکوت\s+(@[A-Za-z0-9_]{5,32}|\d+)$",
        "warn": r"^اخطار\s+(@[A-Za-z0-9_]{5,32}|\d+)$",
        "delwarn": r"^حذف\s*اخطار\s+(@[A-Za-z0-9_]{5,32}|\d+)$"
    }

    cmd_type = None
    for cmd, pattern in BEFEHLE.items():
        if re.match(pattern, text):
            cmd_type = cmd
            break

    if not cmd_type:
        return  # هیچ متن اضافی اجرا نمی‌شود

    # ================= اجرای دستور =================
    try:
        if cmd_type == "ban":
            await context.bot.ban_chat_member(chat.id, target.id)
            await sende_temp(msg, f"🚫 {target.first_name} از گروه بن شد.", context)

        elif cmd_type == "unban":
            await context.bot.unban_chat_member(chat.id, target.id)
            await sende_temp(msg, f"✅ {target.first_name} از بن خارج شد.", context)

        elif cmd_type == "mute":
            m = re.match(BEFEHLE["mute"], text)
            seconds = 3600  # پیشفرض 1 ساعت
            if m and m.group(2):
                num = int(m.group(2))
                unit = m.group(3)
                if unit == "ساعت":
                    seconds = num * 3600
                elif unit == "دقیقه":
                    seconds = num * 60
                elif unit == "ثانیه":
                    seconds = num
            until_date = datetime.utcnow() + timedelta(seconds=seconds)
            await context.bot.restrict_chat_member(
                chat.id, target.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until_date
            )
            await sende_temp(msg, f"🤐 {target.first_name} برای {seconds} ثانیه سکوت شد.", context)

        elif cmd_type == "unmute":
            await context.bot.restrict_chat_member(
                chat.id, target.id,
                permissions=ChatPermissions(can_send_messages=True)
            )
            await sende_temp(msg, f"🔊 {target.first_name} از سکوت خارج شد.", context)

        elif cmd_type == "warn":
            warns = lade_json(WARN_DATEI)
            key = f"{chat.id}:{target.id}"
            warns[key] = warns.get(key, 0) + 1
            speichere_json(WARN_DATEI, warns)
            if warns[key] >= 3:
                await context.bot.ban_chat_member(chat.id, target.id)
                warns[key] = 0
                speichere_json(WARN_DATEI, warns)
                await sende_temp(msg, f"🚫 {target.first_name} به‌دلیل ۳ اخطار بن شد.", context)
            else:
                await sende_temp(msg, f"⚠️ {target.first_name} اخطار {warns[key]}/3 گرفت.", context)

        elif cmd_type == "delwarn":
            warns = lade_json(WARN_DATEI)
            key = f"{chat.id}:{target.id}"
            if key in warns:
                del warns[key]
                speichere_json(WARN_DATEI, warns)
                await sende_temp(msg, f"✅ اخطارهای {target.first_name} حذف شد.", context)

    except Exception as e:
        await sende_temp(msg, f"❌ خطا در اجرای دستور: {e}", context)

# ================= 🔧 Handler Registrierung =================
def register_punishment_handlers(application, group_number: int = 12):
    """ثبت handler با امکان مشخص کردن group_number"""
    application.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), registriere_bestrafen_handler),
        group=group_number
    )
