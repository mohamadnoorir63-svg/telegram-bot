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
BAN_FILE = os.path.join(BASE_DIR, "ban_list.json")
MUTE_FILE = os.path.join(BASE_DIR, "mute_list.json")  # اکنون شامل until timestamps است
ALIAS_FILE = os.path.join(BASE_DIR, "alias_cmds.json")

SUDO_IDS = [8588347189]  # آیدی سودوها

# ایجاد فایل‌ها در صورت نبود
for file in [WARN_FILE, BAN_FILE, MUTE_FILE, ALIAS_FILE]:
    if not os.path.exists(file):
        with open(file, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

# ---------- یوزربات ----------
try:
    from userbot_module.userbot import client as userbot_client
    from userbot_module.userbot import punish_via_userbot
except ImportError:
    userbot_client = None
    async def punish_via_userbot(*args, **kwargs):
        pass

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

async def _has_access(context, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except Exception:
        return False

async def _resolve_target(msg, context, chat_id, explicit_arg: str = None):
    if msg.reply_to_message and getattr(msg.reply_to_message, "from_user", None):
        return msg.reply_to_message.from_user

    text = (msg.text or "").strip()
    user_id = explicit_arg if explicit_arg and explicit_arg.isdigit() else None

    if not user_id:
        m_id = re.search(r"\b(\d{6,15})\b", text)
        if m_id:
            user_id = m_id.group(1)

    if user_id:
        try:
            cm = await context.bot.get_chat_member(chat_id, int(user_id))
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

def add_to_list(file, chat_id, user):
    data = _load_json(file)
    chat_key = str(chat_id)
    if chat_key not in data:
        data[chat_key] = {}
    data[chat_key][str(user.id)] = user.username or ""
    _save_json(file, data)

def remove_from_list(file, chat_id, user):
    data = _load_json(file)
    chat_key = str(chat_id)
    if chat_key in data and str(user.id) in data[chat_key]:
        del data[chat_key][str(user.id)]
    _save_json(file, data)

def list_from_file(file, chat_id):
    data = _load_json(file)
    chat_key = str(chat_id)
    if chat_key in data:
        return [f"{uid} ({uname})" if uname else str(uid) for uid, uname in data[chat_key].items()]
    return []

# ---- توابع مخصوص MUTE FILE (ساختار متفاوت) ----
def save_mute_entry(chat_id: int, user, until_ts: float):
    data = _load_json(MUTE_FILE)
    cid = str(chat_id)
    if cid not in data:
        data[cid] = {}
    data[cid][str(user.id)] = {"username": getattr(user, "username", ""), "until": until_ts}
    _save_json(MUTE_FILE, data)

def remove_mute_entry(chat_id: int, user_id: int):
    data = _load_json(MUTE_FILE)
    cid = str(chat_id)
    uid = str(user_id)
    if cid in data and uid in data[cid]:
        del data[cid][uid]
        if not data[cid]:
            del data[cid]
        _save_json(MUTE_FILE, data)

def load_all_mutes():
    return _load_json(MUTE_FILE)

# ================= 🔐 هندلر تنبیه و alias =================

async def handle_punishments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not msg or chat.type not in ("group", "supergroup"):
        return

    text = (msg.text or "").strip()

    # ---------- ساخت alias داخل گروه ----------
    match_alias = re.match(r"افزودن دستور (.+?)\s+(.+)", text)
    if match_alias:
        if not await _has_access(context, chat.id, user.id):
            return  # فقط متوقف کن بدون ارسال پیام
        alias_name = match_alias.group(1).strip()
        original_cmd = match_alias.group(2).strip()
        data = _load_json(ALIAS_FILE)
        chat_key = str(chat.id)
        if chat_key not in data:
            data[chat_key] = {}
        data[chat_key][alias_name] = original_cmd
        _save_json(ALIAS_FILE, data)
        reply = await msg.reply_text(f"✅ دستور alias ساخته شد:\n`{alias_name}`→`{original_cmd}`", parse_mode="Markdown")
        await asyncio.sleep(10)
        await reply.delete()
        return

    # ---------- لیست‌ها ----------
    if text == "لیست بن":
        items = list_from_file(BAN_FILE, chat.id)
        reply = await msg.reply_text("🚫 لیست بن شده‌ها:\n" + ("\n".join(items) if items else "هیچ کس"))
        await asyncio.sleep(10)
        await reply.delete()
        return

    if text == "لیست سکوت":
        # نمایش لیست سکوت‌ها با زمان باقی‌مانده
        mutes = _load_json(MUTE_FILE).get(str(chat.id), {})
        if not mutes:
            reply = await msg.reply_text("🤐 هیچ کسی در لیست سکوت نیست.")
            await asyncio.sleep(8)
            await reply.delete()
            return
        text_lines = ["🤐 لیست سکوت شده‌ها:"]
        now_ts = datetime.utcnow().timestamp()
        for i, (uid, info) in enumerate(mutes.items(), 1):
            remain = int(info.get("until", 0) - now_ts)
            if remain > 0:
                text_lines.append(f"{i}. {uid} — تا {remain} ثانیه")
            else:
                text_lines.append(f"{i}. {uid} — در حال انتظار آزادسازی")
        reply = await msg.reply_text("\n".join(text_lines))
        await asyncio.sleep(10)
        await reply.delete()
        return

    # ---------- aliasها ----------
    aliases_all = _load_json(ALIAS_FILE)
    chat_aliases = aliases_all.get(str(chat.id), {})

    for alias_text, alias_cmd in chat_aliases.items():
        if text.startswith(alias_text):
            text = alias_cmd
            break

    # ---------- regex دستورات ----------
    PATTERNS = {
        "ban": re.compile(r"^بن(?:\s+(@?[A-Za-z0-9_]{3,32}|\d{6,15}))?$"),
        "unban": re.compile(r"^حذف\s+بن(?:\s+(@?[A-Za-z0-9_]{3,32}|\d{6,15}))?$"),
        "mute": re.compile(r"^سکوت(?:\s+(@?[A-Za-z0-9_]{3,32}|\d{6,15}))?(?:\s+(\d+)\s*(ثانیه|دقیقه|ساعت))?$"),
        "unmute": re.compile(r"^حذف\s+سکوت(?:\s+(@?[A-Za-z0-9_]{3,32}|\d{6,15}))?$"),
        "warn": re.compile(r"^اخطار(?:\s+(@?[A-Za-z0-9_]{3,32}|\d{6,15}))?$"),
        "delwarn": re.compile(r"^حذف\s+اخطار(?:\s+(@?[A-Za-z0-9_]{3,32}|\d{6,15}))?$"),
    }

    matched = None
    cmd_type = None
    for k, pat in PATTERNS.items():
        m = pat.fullmatch(text)
        if m:
            cmd_type = k
            matched = m
            break

    if not cmd_type:
        return

    if not await _has_access(context, chat.id, user.id):
        return  # فقط متوقف کن بدون ارسال پیام

    explicit_arg = matched.group(1) if matched else None
    extra_time = None
    if cmd_type == "mute" and matched.lastindex and matched.lastindex >= 3:
        num = matched.group(2)
        unit = matched.group(3)
        if num:
            extra_time = (int(num), unit)

    target_user = await _resolve_target(msg, context, chat.id, explicit_arg)
    if not target_user:
        reply = await msg.reply_text("⚠️ هدف مشخص نیست.\n• ریپلای روی پیام کاربر\n• یا آیدی عددی/یوزرنیم")
        await asyncio.sleep(10)
        await reply.delete()
        return

    bot_user = await context.bot.get_me()
    if target_user.id == bot_user.id or target_user.id in SUDO_IDS:
        reply = await msg.reply_text("🚫 نمی‌توان روی این کاربر اقدام کرد.")
        await asyncio.sleep(10)
        await reply.delete()
        return

    try:
        tm = await context.bot.get_chat_member(chat.id, target_user.id)
        if tm.status in ("creator", "administrator"):
            reply = await msg.reply_text("🛡 امکان اجرای دستور روی ادمین وجود ندارد.")
            await asyncio.sleep(10)
            await reply.delete()
            return
    except Exception:
        pass

    target_ref = f"@{target_user.username}" if getattr(target_user, "username", None) else str(target_user.id)

    try:
        if cmd_type == "ban":
            await context.bot.ban_chat_member(chat.id, target_user.id)
            add_to_list(BAN_FILE, chat.id, target_user)
            await punish_via_userbot(chat.id, target_ref, action="ban")
            reply = await msg.reply_text(f"🚫 {target_user.first_name} از گروه بن شد.")

        elif cmd_type == "unban":
            await context.bot.unban_chat_member(chat.id, target_user.id)
            remove_from_list(BAN_FILE, chat.id, target_user)
            await punish_via_userbot(chat.id, target_ref, action="unban")
            reply = await msg.reply_text(f"✅ {target_user.first_name} از بن خارج شد.")

        elif cmd_type == "mute":
            # محاسبه مدت زمان سکوت به ثانیه
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

            # اعمال سکوت (تا زمان مشخص)
            await context.bot.restrict_chat_member(
                chat.id,
                target_user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until
            )

            # ذخیره اطلاعات در فایل mute_list.json
            save_mute_entry(chat.id, target_user, until.timestamp())

            await punish_via_userbot(chat.id, target_ref, action="mute", seconds=seconds)
            reply = await msg.reply_text(f"🤐 {target_user.first_name} برای {seconds} ثانیه سکوت شد.")

        elif cmd_type == "unmute":
            # باز کردن کامل دسترسی‌ها (رفع سکوت دستی)
            full_perms = ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=False
            )

            await context.bot.restrict_chat_member(
                chat.id,
                target_user.id,
                permissions=full_perms,
                until_date=0
            )

            # حذف از فایل mute_list
            remove_mute_entry(chat.id, target_user.id)

            await punish_via_userbot(chat.id, target_ref, action="unmute")
            reply = await msg.reply_text(f"🔊 {target_user.first_name} از سکوت خارج شد.")

        elif cmd_type == "warn":
            warns = _load_json(WARN_FILE)
            key = f"{chat.id}:{target_user.id}"
            warns[key] = warns.get(key, 0) + 1
            _save_json(WARN_FILE, warns)
            if warns[key] >= 3:
                await context.bot.ban_chat_member(chat.id, target_user.id)
                add_to_list(BAN_FILE, chat.id, target_user)
                await punish_via_userbot(chat.id, target_ref, action="ban")
                warns[key] = 0
                _save_json(WARN_FILE, warns)
                reply = await msg.reply_text(f"🚫 {target_user.first_name} به‌دلیل ۳ اخطار بن شد.")
            else:
                reply = await msg.reply_text(f"⚠️ {target_user.first_name} اخطار {warns[key]}/3 گرفت.")

        elif cmd_type == "delwarn":
            warns = _load_json(WARN_FILE)
            key = f"{chat.id}:{target_user.id}"
            if key in warns:
                del warns[key]
                _save_json(WARN_FILE, warns)
                reply = await msg.reply_text(f"✅ اخطارهای {target_user.first_name} حذف شد.")
            else:
                reply = await msg.reply_text("ℹ️ این کاربر اخطاری نداشت.")

        await asyncio.sleep(10)
        await reply.delete()
    except Exception as e:
        print("handle_punishments execution exception:", e)
        reply = await msg.reply_text(f"⚠️ خطا در اجرای دستور: {e}")
        await asyncio.sleep(10)
        await reply.delete()

# ================= اتوماتیک آزادسازی سکوت (Job) =================

async def _auto_unmute_job(context: ContextTypes.DEFAULT_TYPE):
    """
    این تابع یک بار اجرا می‌شود (job تکرارشونده).
    اگر زمان until برای هر سکوت گذشته باشد، کاربر آزاد می‌شود و در فایل پاک می‌شود.
    """
    try:
        bot = context.bot
        mute_data = _load_json(MUTE_FILE)
        now_ts = datetime.utcnow().timestamp()
        changed = False

        for chat_id, users in list(mute_data.items()):
            for user_id, info in list(users.items()):
                until = info.get("until", 0)
                try:
                    if now_ts >= until:
                        # سعی می‌کنیم سکوت را برداریم
                        try:
                            full_perms = ChatPermissions(
                                can_send_messages=True,
                                can_send_media_messages=True,
                                can_send_polls=True,
                                can_send_other_messages=True,
                                can_add_web_page_previews=True,
                                can_change_info=False,
                                can_invite_users=True,
                                can_pin_messages=False
                            )
                            await bot.restrict_chat_member(int(chat_id), int(user_id), permissions=full_perms, until_date=0)
                        except Exception as e:
                            # اگر نشد، لاگ کن اما باز هم سعی کن رکورد را حذف کنی
                            print(f"[auto_unmute] failed to unrestrict {user_id} in {chat_id}: {e}")

                        # اطلاع‌رسانی در گروه
                        try:
                            await bot.send_message(int(chat_id), f"🔊 کاربر <a href='tg://user?id={user_id}'>کاربر</a> از سکوت خارج شد.", parse_mode="HTML")
                        except Exception as e:
                            print(f"[auto_unmute] notify failed for {user_id} in {chat_id}: {e}")

                        # حذف رکورد
                        del mute_data[chat_id][user_id]
                        changed = True

            if chat_id in mute_data and not mute_data[chat_id]:
                del mute_data[chat_id]
                changed = True

        if changed:
            _save_json(MUTE_FILE, mute_data)

    except Exception as e:
        print("[auto_unmute_job] error:", e)

# ================= 🧩 ثبت هندلر و job =================

def register_punishment_handlers(application, group_number: int = 12):
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_punishments,
        ),
        group=group_number,
    )

    # ثبت job خودکار آزادسازی سکوت (هر 10 ثانیه)
    try:
        application.job_queue.run_repeating(_auto_unmute_job, interval=10, first=10)
    except Exception as e:
        print("Failed to register auto unmute job:", e)
