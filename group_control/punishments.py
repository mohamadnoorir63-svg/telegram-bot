import os
import json
import re
from telegram import Update, ChatPermissions, MessageEntity
from telegram.ext import ContextTypes, MessageHandler, filters
from datetime import timedelta, datetime

# ================= ⚙️ تنظیمات اولیه =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WARN_FILE = os.path.join(BASE_DIR, "warnings.json")

SUDO_IDS = [8588347189]  # آیدی سودوها

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
    """آیا کاربر مجاز به اجرای دستور است؟ (سودو یا مدیر)"""
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False


# ================= 🔧 استخراج هدف امن (با امکان silent on missing) =================
async def _resolve_target(msg, context, chat_id):
    """
    برمی‌گرداند: (target_user_or_None, mention_failed_or_None)
    - اگر هدف واضح باشد => (User, None)
    - اگر @username نوشته شده ولی کاربر در گروه نباشد => (None, username)  (در این حالت ما ساکت می‌مانیم طبق خواست شما)
    - اگر هیچ هدفی نباشد => (None, None)
    """
    # 1) ریپلای
    if msg.reply_to_message:
        return msg.reply_to_message.from_user, None

    text = msg.text or ""
    entities = msg.entities or []

    # 2) entities: text_mention / mention
    for ent in entities:
        try:
            if ent.type == MessageEntity.TEXT_MENTION:
                return ent.user, None
            if ent.type == MessageEntity.MENTION:
                start = ent.offset
                length = ent.length
                mention_text = text[start:start + length]  # شامل @
                username = mention_text.lstrip("@")
                try:
                    cm = await context.bot.get_chat_member(chat_id, username)
                    return cm.user, None
                except:
                    # mention موجود است ولی عضو گروه نیست
                    return None, username
        except:
            continue

    # 3) plain @username (بدون entity) — بررسی می‌کنیم، اگر نبود ساکت می‌مانیم
    plain_mention = re.search(r"@([A-Za-z0-9_]{5,32})", text)
    if plain_mention:
        username = plain_mention.group(1)
        try:
            cm = await context.bot.get_chat_member(chat_id, username)
            return cm.user, None
        except:
            return None, username

    # 4) آیدی عددی دقیقاً بعد از دستور
    m = re.search(r"^(?:بن|حذف\s*بن|سکوت|حذف\s*سکوت|اخطار|حذف\s*اخطار)\s+(\d{6,15})\b", text)
    if m:
        try:
            target_id = int(m.group(1))
            cm = await context.bot.get_chat_member(chat_id, target_id)
            return cm.user, None
        except:
            return None, None

    return None, None


# ================= 🔧 هندلر دستورات =================
async def handle_punishments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not msg or chat.type not in ("group", "supergroup"):
        return

    text = (msg.text or "").strip()
    if not text:
        return

    # الگوهای دستورات سالم — فقط ابتدای پیام
    COMMAND_PATTERNS = {
        "ban": r"^بن(?:\s+|$)",
        "unban": r"^حذف\s*بن(?:\s+|$)",
        "mute": r"^سکوت(?:\s+|$)",
        "unmute": r"^حذف\s*سکوت(?:\s+|$)",
        "warn": r"^اخطار(?:\s+|$)",
        "delwarn": r"^حذف\s*اخطار(?:\s+|$)",
    }

    cmd_type = None
    for cmd, pattern in COMMAND_PATTERNS.items():
        if re.match(pattern, text):
            cmd_type = cmd
            break

    if not cmd_type:
        return  # پیام دستور واقعی نیست

    # بررسی اینکه اجراکننده مجاز است — اگر مجاز نیست، ساکت بمان
    if not await _has_access(context, chat.id, user.id):
        return

    # استخراج هدف امن (و پرچم mention_failed)
    target, mention_failed = await _resolve_target(msg, context, chat.id)

    # اگر mention وجود داشت ولی کاربر در گروه نبود => طبق خواست شما ساکت بمونه (هیچ پیامی)
    if mention_failed:
        return

    # اگر هدف نبود => ساکت بمونه
    if not target:
        return

    # محافظت‌ها — اینجا می‌خواهیم در صورت هدف بودن ربات/سودو/مدیر، پیام اطلاع‌رسان بدهیم
    # خود ربات
    if target.id == context.bot.id:
        try:
            await msg.reply_text("😅 من ربات هستم — نمی‌توانم تنبیه شوم.")
        except:
            pass
        return

    # سودوها (افشای آیدی امن است چون فقط کوتاه اطلاع می‌دهیم)
    if target.id in SUDO_IDS:
        try:
            await msg.reply_text("🚫 امکان اجرای دستور روی این کاربر وجود ندارد.")
        except:
            pass
        return

    # مدیر/creator/administrator
    try:
        t_member = await context.bot.get_chat_member(chat.id, target.id)
        if t_member.status in ("creator", "administrator"):
            try:
                await msg.reply_text("🛡 امکان اجرای دستور روی این کاربر وجود ندارد.")
            except:
                pass
            return
    except:
        # اگر نتوانستیم وضعیت را بگیریم، ادامه می‌دهیم (ولی معمولاً این حالت رخ نمیده)
        pass

    # ---- اگر تا اینجا رسیدیم: هدف مشخص و قابل تنبیه است ----
    try:
        if cmd_type == "ban":
            await context.bot.ban_chat_member(chat.id, target.id)
            await msg.reply_text(f"🚫 {target.first_name} از گروه بن شد.")

        elif cmd_type == "unban":
            await context.bot.unban_chat_member(chat.id, target.id)
            await msg.reply_text(f"✅ {target.first_name} از بن خارج شد.")

        elif cmd_type == "mute":
            m = re.search(r"سکوت\s*(\d+)?\s*(ثانیه|دقیقه|ساعت)?", text)
            if m and m.group(1):
                num = int(m.group(1))
                unit = m.group(2)
                if unit == "ساعت":
                    seconds = num * 3600
                elif unit == "دقیقه":
                    seconds = num * 60
                elif unit == "ثانیه":
                    seconds = num
                else:
                    seconds = num * 60
            else:
                seconds = 3600
            until_date = datetime.utcnow() + timedelta(seconds=seconds)
            await context.bot.restrict_chat_member(
                chat.id, target.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until_date
            )
            await msg.reply_text(f"🤐 {target.first_name} برای {seconds} ثانیه سکوت شد.")

        elif cmd_type == "unmute":
            await context.bot.restrict_chat_member(
                chat.id, target.id,
                permissions=ChatPermissions(can_send_messages=True)
            )
            await msg.reply_text(f"🔊 {target.first_name} از سکوت خارج شد.")

        elif cmd_type == "warn":
            warns = _load_json(WARN_FILE)
            key = f"{chat.id}:{target.id}"
            warns[key] = warns.get(key, 0) + 1
            _save_json(WARN_FILE, warns)
            if warns[key] >= 3:
                await context.bot.ban_chat_member(chat.id, target.id)
                warns[key] = 0
                _save_json(WARN_FILE, warns)
                await msg.reply_text(f"🚫 {target.first_name} به‌دلیل ۳ اخطار بن شد.")
            else:
                await msg.reply_text(f"⚠️ {target.first_name} اخطار {warns[key]}/3 گرفت.")

        elif cmd_type == "delwarn":
            warns = _load_json(WARN_FILE)
            key = f"{chat.id}:{target.id}"
            if key in warns:
                del warns[key]
                _save_json(WARN_FILE, warns)
                await msg.reply_text(f"✅ اخطارهای {target.first_name} حذف شد.")

    except Exception:
        # در صورت بروز هر خطا (محدودیت دسترسی ها یا خطای API) ساکت بمان
        return


# ================= 🔧 ثبت هندلر =================
def register_punishment_handlers(application, group_number: int = 12):
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_punishments,
        ),
        group=group_number,
    )
