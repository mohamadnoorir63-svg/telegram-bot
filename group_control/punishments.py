import os
import json
import re
import asyncio
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, MessageHandler, filters

# ================= ⚙️ تنظیمات اولیه =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WARN_FILE = os.path.join(BASE_DIR, "warnings.json")
DATA_DIR = os.path.join(BASE_DIR, "group_data")
os.makedirs(DATA_DIR, exist_ok=True)

SUDO_IDS = [8588347189]  # آیدی سودوها

if not os.path.exists(WARN_FILE):
    with open(WARN_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

# ---------- یوزربات ----------
try:
    from userbot_module.userbot import client as userbot_client  # مسیر سشن یوزربات
    from userbot_module.userbot import punish_via_userbot
except ImportError:
    userbot_client = None
    async def punish_via_userbot(*args, **kwargs):
        pass  # اگر یوزربات فعال نبود، خطا نده

# ================= 📁 توابع کمکی =================
def _load_json(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _group_file(chat_id, name):
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, f"{chat_id}_{name}.json")

def _load_group_list(chat_id, name):
    return _load_json(_group_file(chat_id, name)) or []

def _save_group_list(chat_id, name, data):
    _save_json(_group_file(chat_id, name), data)

# ================= 🔐 بررسی ادمین / سودو =================
async def _has_access(context, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except Exception:
        return False

# ================= 🎯 استخراج هدف مقاوم =================
async def _resolve_target(msg, context, chat_id, explicit_arg: str = None):
    text = (msg.text or "").strip()

    if msg.reply_to_message and getattr(msg.reply_to_message, "from_user", None):
        return msg.reply_to_message.from_user

    m_id = None
    if explicit_arg and explicit_arg.isdigit():
        m_id = explicit_arg
    else:
        m_id = re.search(r"\b(\d{6,15})\b", text)
        m_id = m_id.group(1) if m_id else None

    if m_id:
        try:
            cm = await context.bot.get_chat_member(chat_id, int(m_id))
            return cm.user
        except Exception as e:
            print(f"⚠️ خطا در گرفتن آیدی عددی: {e}")

    m_username = re.search(r"@([A-Za-z0-9_]{3,32})", text)
    if m_username:
        username = m_username.group(1)
        try:
            user_obj = await context.bot.get_chat(f"@{username}")
            if user_obj:
                return user_obj
        except Exception as e:
            print(f"⚠️ ربات نتونست @{username} رو resolve کنه: {e}")

        if userbot_client:
            try:
                user_entity = await userbot_client.get_entity(f"@{username}")
                class DummyUser:
                    def __init__(self, id, first_name, username=None):
                        self.id = id
                        self.first_name = first_name
                        self.username = username
                return DummyUser(user_entity.id, getattr(user_entity, "first_name", username), username)
            except Exception as e2:
                print(f"⚠️ یوزربات هم نتونست @{username} رو resolve کنه: {e2}")

    return None

# ================= ⚙️ حذف خودکار پیام =================
async def auto_delete(message, delay=10):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

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

    PATTERNS = {
        "ban": re.compile(r"^بن(?:\s+(\S+))?$"),
        "unban": re.compile(r"^حذف\s*بن(?:\s+(\S+))?$"),
        "mute": re.compile(r"^سکوت(?:\s+(\S+))?(?:\s+(\d+)\s*(ثانیه|دقیقه|ساعت)?)?$"),
        "unmute": re.compile(r"^حذف\s*سکوت(?:\s+(\S+))?$"),
        "warn": re.compile(r"^اخطار(?:\s+(\S+))?$"),
        "delwarn": re.compile(r"^حذف\s*اخطار(?:\s+(\S+))?$"),
        "list_ban": re.compile(r"^لیست\s*بن$"),
        "list_mute": re.compile(r"^لیست\s*سکوت$")
    }

    matched = None
    cmd_type = None
    for k, pat in PATTERNS.items():
        m = pat.match(text)
        if m:
            cmd_type = k
            matched = m
            break

    if not cmd_type:
        return

    if not await _has_access(context, chat.id, user.id):
        resp = await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
        await auto_delete(resp)
        return

    explicit_arg = None
    extra_time = None
    if matched:
        explicit_arg = matched.group(1)
        if cmd_type == "mute" and matched.lastindex and matched.lastindex >= 3:
            num = matched.group(2)
            unit = matched.group(3)
            if num:
                extra_time = (int(num), unit)

    target_user = None
    if cmd_type not in ["list_ban", "list_mute"]:
        target_user = await _resolve_target(msg, context, chat.id, explicit_arg)
        if not target_user:
            resp = await msg.reply_text("⚠️ هدف مشخص نیست.\n• ریپلای روی پیام کاربر\n• یا آیدی عددی/یوزرنیم")
            await auto_delete(resp)
            return

        bot_user = await context.bot.get_me()
        if target_user.id == bot_user.id:
            resp = await msg.reply_text("😅 نمی‌تونم خودم رو تنبیه کنم.")
            await auto_delete(resp)
            return
        if target_user.id in SUDO_IDS:
            resp = await msg.reply_text("🚫 این کاربر در لیست سودو است.")
            await auto_delete(resp)
            return
        try:
            tm = await context.bot.get_chat_member(chat.id, target_user.id)
            if tm.status in ("creator", "administrator"):
                resp = await msg.reply_text("🛡 امکان اجرای دستور روی ادمین وجود ندارد.")
                await auto_delete(resp)
                return
        except Exception:
            pass

    try:
        if cmd_type == "ban":
            await context.bot.ban_chat_member(chat.id, target_user.id)
            banned_list = _load_group_list(chat.id, "banned")
            if target_user.id not in banned_list:
                banned_list.append(target_user.id)
                _save_group_list(chat.id, "banned", banned_list)
            resp = await msg.reply_text(f"🚫 {target_user.first_name} از گروه بن شد.")
            await auto_delete(resp)

        elif cmd_type == "unban":
            await context.bot.unban_chat_member(chat.id, target_user.id)
            banned_list = _load_group_list(chat.id, "banned")
            if target_user.id in banned_list:
                banned_list.remove(target_user.id)
                _save_group_list(chat.id, "banned", banned_list)
            resp = await msg.reply_text(f"✅ {target_user.first_name} از بن خارج شد.")
            await auto_delete(resp)

        elif cmd_type == "mute":
            seconds = 3600
            if extra_time:
                num, unit = extra_time
                if unit == "ساعت":
                    seconds = num * 3600
                elif unit == "دقیقه":
                    seconds = num * 60
                else:
                    seconds = num
            until = datetime.utcnow() + timedelta(seconds=seconds)
            await context.bot.restrict_chat_member(
                chat.id, target_user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until
            )
            muted_list = _load_group_list(chat.id, "muted")
            if target_user.id not in muted_list:
                muted_list.append(target_user.id)
                _save_group_list(chat.id, "muted", muted_list)
            resp = await msg.reply_text(f"🤐 {target_user.first_name} برای {seconds} ثانیه سکوت شد.")
            await auto_delete(resp)

        elif cmd_type == "unmute":
            await context.bot.restrict_chat_member(
                chat.id, target_user.id,
                permissions=ChatPermissions(can_send_messages=True)
            )
            muted_list = _load_group_list(chat.id, "muted")
            if target_user.id in muted_list:
                muted_list.remove(target_user.id)
                _save_group_list(chat.id, "muted", muted_list)
            resp = await msg.reply_text(f"🔊 {target_user.first_name} از سکوت خارج شد.")
            await auto_delete(resp)

        elif cmd_type == "warn":
            warns = _load_json(WARN_FILE)
            key = f"{chat.id}:{target_user.id}"
            warns[key] = warns.get(key, 0) + 1
            _save_json(WARN_FILE, warns)
            if warns[key] >= 3:
                await context.bot.ban_chat_member(chat.id, target_user.id)
                warns[key] = 0
                _save_json(WARN_FILE, warns)
                resp = await msg.reply_text(f"🚫 {target_user.first_name} به‌دلیل ۳ اخطار بن شد.")
            else:
                resp = await msg.reply_text(f"⚠️ {target_user.first_name} اخطار {warns[key]}/3 گرفت.")
            await auto_delete(resp)

        elif cmd_type == "delwarn":
            warns = _load_json(WARN_FILE)
            key = f"{chat.id}:{target_user.id}"
            if key in warns:
                del warns[key]
                _save_json(WARN_FILE, warns)
                resp = await msg.reply_text(f"✅ اخطارهای {target_user.first_name} حذف شد.")
            else:
                resp = await msg.reply_text("ℹ️ این کاربر اخطاری نداشت.")
            await auto_delete(resp)

        elif cmd_type == "list_ban":
            banned_list = _load_group_list(chat.id, "banned")
            resp = await msg.reply_text(f"لیست کاربران بن‌شده:\n{banned_list}")
            await auto_delete(resp)

        elif cmd_type == "list_mute":
            muted_list = _load_group_list(chat.id, "muted")
            resp = await msg.reply_text(f"لیست کاربران سکوت‌شده:\n{muted_list}")
            await auto_delete(resp)

    except Exception as e:
        print("handle_punishments execution exception:", e)
        resp = await msg.reply_text(f"⚠️ خطا در اجرای دستور: {e}")
        await auto_delete(resp)

# ================= 🧩 ثبت هندلر =================
def register_punishment_handlers(application, group_number: int = 12):
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_punishments,
        ),
        group=group_number,
    )
