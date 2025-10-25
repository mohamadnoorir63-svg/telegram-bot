# ======================= ⚙️ سیستم مدیریت گروه (نسخه نهایی) =======================

import json, os
from datetime import datetime
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes

# 🔧 فایل‌های ذخیره
GROUP_CTRL_FILE = "group_control.json"
ALIASES_FILE = "aliases.json"

# 👑 سودوها (آی‌دی خودت و افراد مجاز)
SUDO_IDS = [123456789, 7089376754]  # 👈 آی‌دی‌هات رو اینجا بذار

# ✅ alias پیش‌فرض (قابل تغییر توسط سودوها)
ALIASES = {
    "ban": ["ban", "بن", "اخراج"],
    "unban": ["unban", "آزاد", "رفع‌بن"],
    "warn": ["warn", "اخطار", "هشدار"],
    "unwarn": ["unwarn", "پاک‌اخطار", "حذف‌اخطار"],
    "mute": ["mute", "سکوت", "خفه"],
    "unmute": ["unmute", "آزادسکوت", "رفع‌سکوت"],
    "addadmin": ["addadmin", "افزودنمدیر", "ادمین"],
    "removeadmin": ["removeadmin", "حذفمدیر", "برکنار"],
    "admins": ["admins", "مدیران", "ادمینها"],
    "lock": ["lock", "قفل"],
    "unlock": ["unlock", "باز"],
    "alias": ["alias", "تغییر"]
}

# 📂 بارگذاری و ذخیره فایل‌ها
def load_json_file(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return default

def save_json_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

group_data = load_json_file(GROUP_CTRL_FILE, {})
ALIASES = load_json_file(ALIASES_FILE, ALIASES)

# 🧠 بررسی مجاز بودن
async def is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if user.id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ["administrator", "creator"]
    except:
        return False

# 🧱 بررسی هدف (تا روی مدیر / سودو / ربات اجرا نشه)
async def can_act_on_target(update, context, target):
    bot = await context.bot.get_me()
    chat = update.effective_chat

    if target.id == bot.id:
        replies = [
            "😏 می‌خوای منو بن کنی؟ من اینجارو ساختم!",
            "😂 جدی؟ منو سکوت می‌کنی؟ خودت خفه شو بهتره.",
            "😎 منو اخطار می‌دی؟ خودتو جمع کن رفیق."
        ]
        await update.message.reply_text(replies[hash(target.id) % len(replies)])
        return False

    if target.id in SUDO_IDS or target.id == int(os.getenv("ADMIN_ID", "7089376754")):
        await update.message.reply_text("⚠️ این کاربر از مدیران ارشد یا سازنده است — نمی‌تونی کاریش کنی!")
        return False

    try:
        member = await context.bot.get_chat_member(chat.id, target.id)
        if member.status in ["administrator", "creator"]:
            await update.message.reply_text("⚠️ نمی‌تونی روی مدیر گروه کاری انجام بدی!")
            return False
    except:
        pass
    return True

# 🚫 بن و رفع‌بن
async def handle_ban(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران یا سودوها می‌توانند بن کنند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید روی پیام کاربر ریپلای بزنی.")

    target = update.message.reply_to_message.from_user
    chat = update.effective_chat

    if not await can_act_on_target(update, context, target):
        return

    try:
        await context.bot.ban_chat_member(chat.id, target.id)
        await update.message.reply_text(f"🚫 <b>{target.first_name}</b> بن شد.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")

async def handle_unban(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران یا سودوها مجازند!")

    chat = update.effective_chat
    user_id = None

    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
    elif context.args:
        user_id = int(context.args[0])
    else:
        return await update.message.reply_text("🔹 باید روی پیام فرد ریپلای بزنی یا آیدی وارد کنی.")

    try:
        await context.bot.unban_chat_member(chat.id, user_id)
        await update.message.reply_text("✅ کاربر از بن خارج شد.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در رفع بن:\n<code>{e}</code>", parse_mode="HTML")

# ⚠️ اخطار (۳ اخطار = بن)
async def handle_warn(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید روی پیام کاربر ریپلای بزنی.")

    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)

    if not await can_act_on_target(update, context, target):
        return

    group = group_data.get(chat_id, {"warns": {}, "admins": []})
    warns = group["warns"]
    warns[str(target.id)] = warns.get(str(target.id), 0) + 1
    count = warns[str(target.id)]
    group["warns"] = warns
    group_data[chat_id] = group
    save_json_file(GROUP_CTRL_FILE, group_data)

    if count >= 3:
        try:
            await context.bot.ban_chat_member(chat_id, target.id)
            await update.message.reply_text(f"🚫 <b>{target.first_name}</b> سه اخطار گرفت و بن شد!", parse_mode="HTML")
            warns[str(target.id)] = 0
        except:
            pass
    else:
        await update.message.reply_text(f"⚠️ <b>{target.first_name}</b> اخطار شماره <b>{count}</b> گرفت.", parse_mode="HTML")

# 🤐 سکوت / رفع سکوت (بهبود یافته)
async def handle_mute(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید روی پیام کاربر ریپلای بزنی.")

    target = update.message.reply_to_message.from_user
    chat = update.effective_chat
    user = update.effective_user

    if not await can_act_on_target(update, context, target):
        return

    try:
        await context.bot.restrict_chat_member(chat.id, target.id, permissions=ChatPermissions(can_send_messages=False))
        time_str = datetime.now().strftime("%H:%M - %d/%m/%Y")
        await update.message.reply_text(
            f"🤐 <b>{target.first_name}</b> ساکت شد و دیگر نمی‌تواند پیام بفرستد.\n\n"
            f"👤 <b>توسط:</b> {user.first_name}\n"
            f"🕒 <b>زمان:</b> {time_str}",
            parse_mode="HTML"
        )
    except:
        await update.message.reply_text("⚠️ نمی‌توان این کاربر را ساکت کرد (احتمالاً مدیر یا مالک است).", parse_mode="HTML")

async def handle_unmute(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید روی پیام کاربر ریپلای بزنی.")

    target = update.message.reply_to_message.from_user
    chat = update.effective_chat
    user = update.effective_user

    try:
        await context.bot.restrict_chat_member(chat.id, target.id, permissions=ChatPermissions(can_send_messages=True))
        time_str = datetime.now().strftime("%H:%M - %d/%m/%Y")
        await update.message.reply_text(
            f"🔊 <b>{target.first_name}</b> از حالت سکوت خارج شد و اکنون می‌تواند صحبت کند.\n\n"
            f"👤 <b>توسط:</b> {user.first_name}\n"
            f"🕒 <b>زمان:</b> {time_str}",
            parse_mode="HTML"
        )
    except:
        await update.message.reply_text("⚠️ نمی‌توان سکوت این کاربر را برداشت (احتمالاً مدیر یا صاحب گروه است).", parse_mode="HTML")
      
# ======================= 🔒 سیستم قفل‌های پیشرفته گروه =======================

from telegram import ChatPermissions
from datetime import datetime

# ✅ لیست قفل‌های پشتیبانی‌شده
LOCK_TYPES = {
    "links": "ارسال لینک‌ها",
    "photos": "ارسال عکس",
    "videos": "ارسال ویدیو",
    "files": "ارسال فایل",
    "gifs": "ارسال گیف",
    "voices": "ارسال ویس",
    "vmsgs": "ارسال ویدیو مسیج",
    "stickers": "ارسال استیکر",
    "forward": "ارسال فوروارد",
    "ads": "ارسال تبلیغ / تبچی",
    "usernames": "ارسال یوزرنیم / تگ",
    "bots": "افزودن ربات",
    "join": "ورود عضو جدید",
    "chat": "ارسال پیام در چت",
    "media": "ارسال تمام مدیاها"
}

# ✅ alias پیش‌فرض برای هر قفل
for lock in LOCK_TYPES:
    ALIASES[f"lock_{lock}"] = [f"lock {lock}"]
    ALIASES[f"unlock_{lock}"] = [f"unlock {lock}"]

save_json_file(ALIASES_FILE, ALIASES)

# ⚙️ تابع کمکی: بروزرسانی وضعیت قفل
def set_lock_status(chat_id, lock_name, status):
    chat_id = str(chat_id)
    group = group_data.get(chat_id, {"locks": {}})
    locks = group.get("locks", {})
    locks[lock_name] = status
    group["locks"] = locks
    group_data[chat_id] = group
    save_json_file(GROUP_CTRL_FILE, group_data)

# 📊 گرفتن وضعیت قفل‌ها
def get_lock_status(chat_id, lock_name):
    chat_id = str(chat_id)
    group = group_data.get(chat_id, {"locks": {}})
    locks = group.get("locks", {})
    return locks.get(lock_name, False)

# 🔐 قفل یک بخش
async def handle_lock_generic(update, context, lock_name):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند قفل کنند!")

    chat = update.effective_chat
    chat_id = str(chat.id)
    user = update.effective_user

    if get_lock_status(chat_id, lock_name):
        return await update.message.reply_text(f"🔒 {LOCK_TYPES[lock_name]} از قبل قفل بوده است!")

    set_lock_status(chat_id, lock_name, True)
    time_str = datetime.now().strftime("%H:%M - %d/%m/%Y")

    await update.message.reply_text(
        f"🔒 <b>{LOCK_TYPES[lock_name]} قفل شد!</b>\n"
        f"📵 اعضا اجازه انجام آن را ندارند.\n\n"
        f"👤 توسط: <b>{user.first_name}</b>\n🕒 {time_str}",
        parse_mode="HTML"
    )

# 🔓 باز کردن قفل
async def handle_unlock_generic(update, context, lock_name):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند باز کنند!")

    chat = update.effective_chat
    chat_id = str(chat.id)
    user = update.effective_user

    if not get_lock_status(chat_id, lock_name):
        return await update.message.reply_text(f"🔓 {LOCK_TYPES[lock_name]} از قبل باز بوده است!")

    set_lock_status(chat_id, lock_name, False)
    time_str = datetime.now().strftime("%H:%M - %d/%m/%Y")

    await update.message.reply_text(
        f"🔓 <b>{LOCK_TYPES[lock_name]} باز شد!</b>\n"
        f"💬 اعضا اکنون می‌توانند از آن استفاده کنند.\n\n"
        f"👤 توسط: <b>{user.first_name}</b>\n🕒 {time_str}",
        parse_mode="HTML"
    )

# 🧹 بررسی و حذف پیام‌های خلاف قفل‌ها
async def check_message_locks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = str(update.effective_chat.id)
    user = update.effective_user
    message = update.message
    locks = group_data.get(chat_id, {}).get("locks", {})
    if not locks:
        return

    delete_reason = None
    text = message.text.lower() if message.text else ""

    if locks.get("links") and ("t.me/" in text or "http" in text):
        delete_reason = "ارسال لینک"
    elif locks.get("photos") and message.photo:
        delete_reason = "ارسال عکس"
    elif locks.get("videos") and message.video:
        delete_reason = "ارسال ویدیو"
    elif locks.get("files") and message.document:
        delete_reason = "ارسال فایل"
    elif locks.get("gifs") and message.animation:
        delete_reason = "ارسال گیف"
    elif locks.get("voices") and message.voice:
        delete_reason = "ارسال ویس"
    elif locks.get("vmsgs") and message.video_note:
        delete_reason = "ارسال ویدیو مسیج"
    elif locks.get("stickers") and message.sticker:
        delete_reason = "ارسال استیکر"
    elif locks.get("forward") and message.forward_from:
        delete_reason = "ارسال فوروارد"
    elif locks.get("ads") and ("join" in text or "channel" in text):
        delete_reason = "ارسال تبلیغ / تبچی"
    elif locks.get("usernames") and "@" in text:
        delete_reason = "ارسال یوزرنیم یا تگ"
    elif locks.get("media") and (message.photo or message.video or message.animation):
        delete_reason = "ارسال مدیا (قفل کلی)"
    elif locks.get("chat") and message.text:
        delete_reason = "ارسال پیام متنی"

    if delete_reason:
        try:
            await message.delete()
        except:
            return
        warn_msg = await message.chat.send_message(
            f"🚫 پیام <b>{user.first_name}</b> حذف شد!\n🎯 دلیل: <b>{delete_reason}</b>",
            parse_mode="HTML"
        )
        try:
            await context.application.create_task(
                context.bot.delete_message(chat_id, warn_msg.message_id)
            )
        except:
            pass

# 🧾 وضعیت همه قفل‌ها
async def handle_locks_status(update, context):
    chat_id = str(update.effective_chat.id)
    locks = group_data.get(chat_id, {}).get("locks", {})

    if not locks:
        return await update.message.reply_text("🔓 هیچ قفلی فعال نیست!", parse_mode="HTML")

    text = "🧱 <b>وضعیت قفل‌های گروه:</b>\n\n"
    for lock, desc in LOCK_TYPES.items():
        status = "🔒 فعال" if locks.get(lock, False) else "🔓 غیرفعال"
        text += f"▫️ <b>{desc}:</b> {status}\n"

    await update.message.reply_text(text, parse_mode="HTML")

# 🎮 اضافه کردن همه هندلرها به group_command_handler
async def group_command_handler(update, context):
    text = update.message.text.strip().lower()

    if text.startswith("alias "):
        return await handle_alias(update, context)

    if text in ["locks", "lock status", "وضعیت قفل"]:
        return await handle_locks_status(update, context)

    for cmd, aliases in ALIASES.items():
        if text in aliases:
            for lock in LOCK_TYPES:
                if cmd == f"lock_{lock}":
                    return await handle_lock_generic(update, context, lock)
                elif cmd == f"unlock_{lock}":
                    return await handle_unlock_generic(update, context, lock)

            handlers = {
                "ban": handle_ban, "unban": handle_unban,
                "warn": handle_warn, "unwarn": handle_warn,
                "mute": handle_mute, "unmute": handle_unmute,
                "addadmin": handle_addadmin, "removeadmin": handle_removeadmin,
                "admins": handle_admins
            }
            if cmd in handlers:
                return await handlers[cmd](update, context)
    return

# ======================= 🧠 فیلتر کلمات + تگ کاربران =======================

import json, os, re, asyncio
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

FILTER_FILE = "filters.json"
TAG_LIMIT = 5  # چند نفر در هر پیام تگ شوند

ALIASES_ADV = {
    "addfilter": ["addfilter", "addfilterword", "افزودن‌فیلتر", "فیلترکن"],
    "delfilter": ["delfilter", "removefilter", "حذف‌فیلتر", "پاک‌فیلتر"],
    "filters": ["filters", "filterlist", "لیست‌فیلتر", "فیلترها"],
    "tagall": ["tagall", "تگ‌کاربران", "تگ‌همه", "منشن‌همگانی"],
    "tagactive": ["tagactive", "تگ‌فعال", "تگ‌آنلاین"]
}

# 📁 فایل فیلترها
def load_filters():
    if os.path.exists(FILTER_FILE):
        try:
            with open(FILTER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_filters(data):
    with open(FILTER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

filters_data = load_filters()

# 🧩 بررسی مجاز بودن
async def can_manage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if user.id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ["administrator", "creator"]
    except:
        return False

# ➕ افزودن فیلتر
async def handle_addfilter(update, context):
    if not await can_manage(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند فیلتر اضافه کنند!")

    if len(context.args) < 1:
        return await update.message.reply_text("📝 استفاده: addfilter [کلمه]\nمثلاً: addfilter تبلیغ")

    word = " ".join(context.args).strip().lower()
    chat_id = str(update.effective_chat.id)
    chat_filters = filters_data.get(chat_id, [])

    if word in chat_filters:
        return await update.message.reply_text("⚠️ این کلمه از قبل در فیلتر است!")

    chat_filters.append(word)
    filters_data[chat_id] = chat_filters
    save_filters(filters_data)
    await update.message.reply_text(f"✅ کلمه <b>{word}</b> به لیست فیلتر اضافه شد.", parse_mode="HTML")
