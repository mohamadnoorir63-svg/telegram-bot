import os
import json
import re
import unicodedata
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions, MessageEntity
from telegram.ext import ContextTypes, MessageHandler, filters

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
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except Exception:
        return False


# ================== کمکی: پاک‌سازی username ==================
def _clean_username(u: str) -> str:
    """
    Remove zero-width / control characters and normalize the username.
    Return lowercase username without leading '@'.
    """
    if not u:
        return u
    # حذف @ اگر هست
    if u.startswith("@"):
        u = u[1:]
    # normalize unicode (NFKC)
    u = unicodedata.normalize("NFKC", u)
    # حذف کاراکترهای کنترل و zero-width
    u = re.sub(r"[\u200B\u200C\u200D\uFEFF]", "", u)
    # حذف فاصله‌ها و کاراکترهای عجیب اطراف
    u = u.strip()
    return u


# ================= 🎯 استخراج هدف امن (نسخهٔ دیباگ و مقاوم) =================
async def _resolve_target(msg, context, chat_id):
    # 1) ریپلای
    if msg.reply_to_message:
        # لاگ کوچک برای دیباگ
        print("resolve_target: using reply_to_message.from_user")
        return msg.reply_to_message.from_user

    text = (msg.text or "")
    entities = msg.entities or []

    # لاگ برای دیباگ: متن کامل و entities دریافت‌شده
    try:
        print("resolve_target: text:", repr(text))
        ents_info = []
        for e in entities:
            ents_info.append({"type": e.type, "offset": e.offset, "length": e.length})
        print("resolve_target: entities:", ents_info)
    except Exception as ex:
        print("resolve_target: failed to print entities:", ex)

    # 2) بررسی entityها (text_mention و mention)
    for ent in entities:
        try:
            if ent.type == MessageEntity.TEXT_MENTION:
                print("resolve_target: found TEXT_MENTION ->", ent.user.id)
                return ent.user

            if ent.type == MessageEntity.MENTION:
                # استخراج username از اسیپت / طول
                start = ent.offset
                length = ent.length
                raw_mention = text[start:start + length]
                username = _clean_username(raw_mention)
                print("resolve_target: found MENTION raw:", repr(raw_mention), "clean:", username)
                if not username:
                    continue
                # تلاش برای resolve با get_chat
                try:
                    user_obj = await context.bot.get_chat(username)
                    print("resolve_target: get_chat success for", username, "->", getattr(user_obj, "id", None))
                    return user_obj
                except Exception as e:
                    print("resolve_target: get_chat failed for", username, "err:", e)
                    # ادامه بده تا fallbackها چک شوند
                    continue
        except Exception as ex:
            print("resolve_target: entity loop exception:", ex)
            continue

    # 3) تلاش دستی برای پیدا کردن @username در متن حتی بدون entity
    # الگوی username: حداقل 5 کاراکتر (تلگرام حداقل 5) — اگر usernameهای کوتاه‌تر مدنظر است، عدد را تغییر بده
    m_user = re.search(r"@([A-Za-z0-9_]{3,})", text)
    if m_user:
        raw_username = m_user.group(0)
        username = _clean_username(m_user.group(1))
        print("resolve_target: manual mention found raw:", raw_username, "clean:", username)
        if username:
            try:
                user_obj = await context.bot.get_chat(username)
                print("resolve_target: manual get_chat success for", username, "->", getattr(user_obj, "id", None))
                return user_obj
            except Exception as e:
                print("resolve_target: manual get_chat failed for", username, "err:", e)

    # 4) آیدی عددی در متن
    m_id = re.search(r"\b(\d{6,15})\b", text)
    if m_id:
        try:
            target_id = int(m_id.group(1))
            print("resolve_target: found numeric id:", target_id)
            cm = await context.bot.get_chat_member(chat_id, target_id)
            return cm.user
        except Exception as e:
            print("resolve_target: get_chat_member by id failed:", e)

    # اگر به اینجا رسیدیم، هیچ کدام کار نکرد
    print("resolve_target: NO TARGET FOUND")
    return None


# ================= ⚙️ هندلر دستورات تنبیهی =================
async def handle_punishments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not msg or chat.type not in ("group", "supergroup"):
        return

    text = (msg.text or "").strip()
    if not text:
        return

    COMMAND_PATTERNS = {
        "ban": r"^بن(?:\s|$)",
        "unban": r"^حذف\s*بن(?:\s|$)",
        "mute": r"^سکوت(?:\s|$)",
        "unmute": r"^حذف\s*سکوت(?:\s|$)",
        "warn": r"^اخطار(?:\s|$)",
        "delwarn": r"^حذف\s*اخطار(?:\s|$)",
    }

    cmd_type = None
    for cmd, pattern in COMMAND_PATTERNS.items():
        if re.match(pattern, text):
            cmd_type = cmd
            break

    if not cmd_type:
        return

    # بررسی دسترسی
    if not await _has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    # استخراج هدف (با لاگ)
    target = await _resolve_target(msg, context, chat.id)
    if not target:
        # لاگ مفصل برای debug
        try:
            print("handle_punishments: could not resolve target. message text:", repr(text))
            for e in (msg.entities or []):
                print("handle_punishments: entity:", e.type, e.offset, e.length)
        except Exception:
            pass

        return await msg.reply_text(
            "⚠️ هدف مشخص نیست.\n"
            "• ریپلای روی پیام کاربر\n"
            "• @username (عضو گروه)\n"
            "• آیدی عددی\n\n"
            "🔍 اگر کاربر عضو گروه است و ربات ادمین است، لطفاً لاگ‌ها را بررسی کنید یا یک پیام تست بفرستید."
        )

    # محافظت‌ها
    if target.id == context.bot.id:
        return await msg.reply_text("😅 نمی‌تونم خودم رو تنبیه کنم.")
    if target.id in SUDO_IDS:
        return await msg.reply_text("🚫 امکان اجرای دستور روی این کاربر وجود ندارد.")
    try:
        t_member = await context.bot.get_chat_member(chat.id, target.id)
        if t_member.status in ("creator", "administrator"):
            return await msg.reply_text("🛡 امکان اجرای دستور روی این کاربر وجود ندارد.")
    except Exception:
        pass

    # اجرای دستورات
    try:
        if cmd_type == "ban":
            await context.bot.ban_chat_member(chat.id, target.id)
            return await msg.reply_text(f"🚫 {target.first_name} از گروه بن شد.")

        if cmd_type == "unban":
            await context.bot.unban_chat_member(chat.id, target.id)
            return await msg.reply_text(f"✅ {target.first_name} از بن خارج شد.")

        if cmd_type == "mute":
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
            return await msg.reply_text(f"🤐 {target.first_name} برای {seconds} ثانیه سکوت شد.")

        if cmd_type == "unmute":
            await context.bot.restrict_chat_member(
                chat.id, target.id,
                permissions=ChatPermissions(can_send_messages=True)
            )
            return await msg.reply_text(f"🔊 {target.first_name} از سکوت خارج شد.")

        if cmd_type == "warn":
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

        if cmd_type == "delwarn":
            warns = _load_json(WARN_FILE)
            key = f"{chat.id}:{target.id}"
            if key in warns:
                del warns[key]
                _save_json(WARN_FILE, warns)
                return await msg.reply_text(f"✅ اخطارهای {target.first_name} حذف شد.")
            return await msg.reply_text("ℹ️ این کاربر اخطاری نداشت.")

    except Exception as e:
        print("handle_punishments: execution exception:", e)
        return await msg.reply_text(f"⚠️ خطا در اجرای دستور: {e}")


# ================= 🧩 ثبت هندلر =================
def register_punishment_handlers(application, group_number: int = 12):
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_punishments,
        ),
        group=group_number,
    )
