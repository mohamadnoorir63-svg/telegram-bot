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
    """بررسی دسترسی مجری دستور"""
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False


# ================= ⚙️ مدیریت دستورات و تنبیه‌ها =================
async def handle_punishments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not msg or chat.type not in ("group", "supergroup"):
        return

    text = (msg.text or "").strip()
    if not text:
        return

    # بارگذاری alias برای این گروه (dict of name -> {type, text})
    aliases_all = _load_json(ALIAS_FILE)
    aliases = aliases_all.get(str(chat.id), {})

    # لیست دستورات پایه
    base_cmds = ["بن", "حذف بن", "سکوت", "حذف سکوت", "اخطار", "حذف اخطار"]
    # دستورات مدیریتی خاص
    special_cmds_prefixes = ("افزودن دستور", "حذف دستور", "لیست دستورها", "لیست دستور ها")

    # ---- تشخیص اینکه آیا پیام دستور هست یا نه ----
    is_command = False
    if any(text.startswith(p) for p in special_cmds_prefixes):
        is_command = True
    if text in ("لیست دستورها", "لیست دستور ها"):
        is_command = True
    if any(text.startswith(c) for c in base_cmds):
        is_command = True
    for alias_name in aliases.keys():
        if text.startswith(alias_name):
            is_command = True
            break

    if not is_command:
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

    # ---- افزودن دستور جدید ----
    if text.startswith("افزودن دستور"):
        if not await _has_access(context, chat.id, user.id):
            return await msg.reply_text("🚫 فقط مدیران یا سودوها مجاز به افزودن دستور هستند.")

        match = re.match(r"^افزودن دستور\s+(\S+)\s+(بن|سکوت|اخطار)\s+(.+)$", text)
        if not match:
            return await msg.reply_text(
                "📘 فرمت درست:\n"
                "<code>افزودن دستور [نام] [نوع دستور] [متن پاسخ]</code>\n\n"
                "مثال:\n"
                "<code>افزودن دستور بپر بن 🚀 {name} از گروه پرت شد بیرون!</code>",
                parse_mode="HTML"
            )

        name, base_cmd, response = match.groups()
        if name in aliases:
            return await msg.reply_text("⚠️ این نام قبلاً تعریف شده.")

        aliases[name] = {"type": base_cmd, "text": response}
        aliases_all[str(chat.id)] = aliases
        _save_json(ALIAS_FILE, aliases_all)

        return await msg.reply_text(f"✅ دستور جدید با نام <b>{name}</b> برای این گروه ثبت شد.", parse_mode="HTML")

    # ---- حذف دستور ----
    if text.startswith("حذف دستور"):
        if not await _has_access(context, chat.id, user.id):
            return await msg.reply_text("🚫 فقط مدیران یا سودوها مجاز به حذف دستور هستند.")
        parts = text.split(" ", 2)
        if len(parts) < 3:
            return await msg.reply_text("📘 فرمت: <code>حذف دستور [نام]</code>", parse_mode="HTML")
        name = parts[2].strip()
        if name not in aliases:
            return await msg.reply_text("❌ چنین دستوری وجود ندارد.")
        del aliases[name]
        aliases_all[str(chat.id)] = aliases
        _save_json(ALIAS_FILE, aliases_all)
        return await msg.reply_text(f"🗑 دستور <b>{name}</b> حذف شد.", parse_mode="HTML")

    # ---- لیست دستورها ----
    if text in ("لیست دستورها", "لیست دستور ها"):
        if not aliases:
            return await msg.reply_text("ℹ️ هنوز هیچ دستوری در این گروه ساخته نشده.")
        lines = [f"🔹 <b>{n}</b> → {d['type']}" for n, d in aliases.items()]
        return await msg.reply_text("📜 <b>دستورات سفارشی این گروه:</b>\n\n" + "\n".join(lines), parse_mode="HTML")

    # ---- اجرای alias ----
    for alias_name, alias_info in aliases.items():
        if text.startswith(alias_name):
            cmd_type = alias_info["type"]
            response_text = alias_info["text"]

            if not target:
                return await msg.reply_text("⚠️ باید ریپلای کنی یا @/آیدی فرد را بنویسی.")
            if not await _has_access(context, chat.id, user.id):
                return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

            # محافظت از ربات و مدیران
            if target.id == context.bot.id:
                return await msg.reply_text("😅 نمی‌تونم خودم رو تنبیه کنم.")
            if target.id in SUDO_IDS:
                return await msg.reply_text("👑 این کاربر جزو سودوهاست و مصون از تنبیهه!")
            try:
                t_member = await context.bot.get_chat_member(chat.id, target.id)
                if t_member.status in ("creator", "administrator"):
                    return await msg.reply_text("🛡 این کاربر مدیر گروهه، نمی‌تونی تنبیهش کنی!")
            except:
                pass

            try:
                await execute_punishment(context, chat, target, cmd_type)
                return await msg.reply_text(response_text.replace("{name}", target.first_name))
            except Exception as e:
                return await msg.reply_text(f"⚠️ خطا در اجرای دستور سفارشی: {e}")

    # ---- دستورات اصلی ----
    if any(text.startswith(c) for c in base_cmds):
        if not target:
            return await msg.reply_text("⚠️ باید ریپلای کنی یا @/آیدی فرد را بنویسی.")
        if not await _has_access(context, chat.id, user.id):
            return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

        if target.id == context.bot.id:
            return await msg.reply_text("😅 نمی‌تونم خودم رو تنبیه کنم.")
        if target.id in SUDO_IDS:
            return await msg.reply_text("👑 این کاربر جزو سودوهاست و مصون از تنبیهه!")
        try:
            t_member = await context.bot.get_chat_member(chat.id, target.id)
            if t_member.status in ("creator", "administrator"):
                return await msg.reply_text("🛡 این کاربر مدیر گروهه، نمی‌تونی تنبیهش کنی!")
        except:
            pass

        try:
            if text.startswith("بن"):
                await context.bot.ban_chat_member(chat.id, target.id)
                return await msg.reply_text(f"🚫 {target.first_name} از گروه بن شد.")
            elif text.startswith("حذف بن"):
                await context.bot.unban_chat_member(chat.id, target.id)
                return await msg.reply_text(f"✅ {target.first_name} از بن خارج شد.")
            elif text.startswith("سکوت"):
                m = re.search(r"سکوت\s*(\d+)\s*(ثانیه|دقیقه|ساعت)?", text)
                if m:
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

    return


# ================= ⚙️ تابع مشترک اجرای مجازات =================
async def execute_punishment(context, chat, target, cmd_type):
    if cmd_type == "بن":
        await context.bot.ban_chat_member(chat.id, target.id)
        await context.bot.unban_chat_member(chat.id, target.id)
    elif cmd_type == "سکوت":
        until_date = datetime.utcnow() + timedelta(hours=1)
        await context.bot.restrict_chat_member(
            chat.id, target.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
    elif cmd_type == "اخطار":
        warns = _load_json(WARN_FILE)
        key = f"{chat.id}:{target.id}"
        warns[key] = warns.get(key, 0) + 1
        _save_json(WARN_FILE, warns)
        if warns[key] >= 3:
            await context.bot.ban_chat_member(chat.id, target.id)
            warns[key] = 0
            _save_json(WARN_FILE, warns)


# ================= 🔧 ثبت هندلر =================
def register_punishment_handlers(application, group_number: int = 12):
    """ثبت هندلر دستورات تنبیه و سفارشی (با پشتیبانی @ و آیدی و تشخیص نقش‌ها)"""
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_punishments,
        ),
        group=group_number,
    )
