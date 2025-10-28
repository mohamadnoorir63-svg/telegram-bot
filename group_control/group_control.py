# ======================= ⚙️ سیستم مدیریت گروه (نسخه نهایی کامل) =======================

import json, os, re
from datetime import datetime
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes

# 🔧 فایل‌های ذخیره
GROUP_CTRL_FILE = "group_control.json"
ALIASES_FILE = "aliases.json"
FILTER_FILE = "filters.json"

# 👑 سودوها (آی‌دی خودت و افراد مجاز)
SUDO_IDS = [1777319036 , 7089376754]  # 👈 آی‌دی خودت رو بذار

# ======================= ✅ alias پیش‌فرض (نسخه نهایی و کامل) =======================

ALIASES = {
    # 🚫 دستورات مدیریتی اصلی
    "ban": ["ban", "بن", "اخراج", "حذف کاربر"],
    "unban": ["unban", "آزاد", "رفع‌بن", "آزادکردن"],
    "warn": ["warn", "اخطار", "هشدار"],
    "unwarn": ["unwarn", "پاک‌اخطار", "حذف‌اخطار", "رفع‌اخطار"],
    "mute": ["mute", "سکوت", "خفه"],
    "unmute": ["unmute", "آزادسکوت", "رفع‌سکوت", "بازکردن سکوت"],
    "addadmin": ["addadmin", "افزودنمدیر", "مدیرکن", "ادمین"],
    "removeadmin": ["removeadmin", "حذفمدیر", "برکنار", "حذف ادمین"],
    "admins": ["admins", "مدیران", "ادمینها", "لیست مدیران"],

    # 🔒 قفل و باز کردن گروه
    "lockgroup": ["lockgroup", "قفل‌گروه", "قفل گروه", "ببند گروه"],
    "unlockgroup": ["unlockgroup", "بازگروه", "باز گروه", "باز کن گروه"],
    "lock": ["lock", "قفل"],
    "unlock": ["unlock", "باز"],

    # 🧹 پاکسازی
    "clean": ["clean", "پاکسازی", "پاک", "حذفعدد", "clear", "نظافت"],

    # 📌 پین و آن‌پین
    "pin": ["pin", "پین", "سنجاق", "پین کن"],
    "unpin": ["unpin", "بردارپین", "بردارسنجاق", "آن‌پین"],

    # 🧿 سیستم «اصل»
    "setorigin": ["setorigin", "set origin", "ثبت اصل", "اصل بده"],
    "showorigin": ["showorigin", "origin", "اصل", "اصل من", "اصلش", "اصل خودم"],

    # 🧩 alias
    "alias": ["alias", "تغییر", "تغییرنام", "نام مستعار"],

    # 🚫 فیلتر کلمات
    "addfilter": ["addfilter", "افزودن‌فیلتر", "فیلترکن"],
    "delfilter": ["delfilter", "حذف‌فیلتر", "پاک‌فیلتر"],
    "filters": ["filters", "فیلترها", "لیست‌فیلتر"],

    # 📣 تگ کاربران
    "tagall": ["tagall", "تگ‌همه", "منشن‌همگانی"],
    "tagactive": ["tagactive", "تگ‌فعال", "تگ‌آنلاین"],

    # 🧱 قفل رسانه‌ها و پیام‌ها
    "locklinks": ["lock links", "قفل لینک", "قفل‌لینک‌ها"],
    "unlocklinks": ["unlock links", "باز لینک", "باز‌لینک‌ها"],
    "lockmedia": ["lock media", "قفل مدیا", "قفل رسانه"],
    "unlockmedia": ["unlock media", "باز مدیا", "باز رسانه"]
}
# 📂 بارگذاری و ذخیره فایل‌ها + بک‌آپ خودکار
import os, json

BACKUP_DIR = "backups"
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

def load_json_file(path, default):
    """📥 لود فایل JSON با بازیابی خودکار از بک‌آپ"""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ خطا در لود {path}: {e} — تلاش برای بازیابی از بک‌آپ...")

    # اگر فایل اصلی وجود نداشت، از بک‌آپ بخوان
    backup_path = os.path.join(BACKUP_DIR, f"backup_{os.path.basename(path)}")
    if os.path.exists(backup_path):
        try:
            with open(backup_path, "r", encoding="utf-8") as b:
                print(f"♻️ {path} از بک‌آپ بازیابی شد ✅")
                return json.load(b)
        except Exception as e:
            print(f"⚠️ بک‌آپ {backup_path} نیز قابل استفاده نیست: {e}")

    return default


def save_json_file(path, data):
    """💾 ذخیره فایل JSON به همراه بک‌آپ خودکار"""
    try:
        # ذخیره فایل اصلی
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # ذخیره بک‌آپ در پوشه backups
        backup_path = os.path.join(BACKUP_DIR, f"backup_{os.path.basename(path)}")
        with open(backup_path, "w", encoding="utf-8") as b:
            json.dump(data, b, ensure_ascii=False, indent=2)

        print(f"💾 فایل {os.path.basename(path)} و بک‌آپ آن ذخیره شد ✅")

    except Exception as e:
        print(f"⚠️ خطا در ذخیره {path}: {e}")


# ✅ بارگذاری داده‌ها
group_data = load_json_file(GROUP_CTRL_FILE, {})
ALIASES = load_json_file(ALIASES_FILE, ALIASES)

# 🧠 بررسی مجاز بودن (مدیران تلگرام + مدیران ثبت‌شده + سودوها)
async def is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    chat_id = str(chat.id)

    # 👑 سودوها همیشه مجازن
    if user.id in SUDO_IDS:
        return True

    # ✅ اگر در لیست مدیران ثبت‌شده باشد (مدیرانی که با دستور «افزودنمدیر» اضافه شدن)
    group = group_data.get(chat_id, {})
    admins = group.get("admins", [])
    if str(user.id) in admins:
        return True

    # 🔹 بررسی مدیران واقعی تلگرام
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status in ["administrator", "creator"]:
            return True
    except:
        pass

    # 🚫 در غیر اینصورت مجاز نیست
    return False


# 🧱 بررسی هدف
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
    if not update or not update.message or not update.effective_chat:
        return

    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید روی پیام کاربر ریپلای بزنی.")

    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)

    if not await can_act_on_target(update, context, target):
        return

    # ✅ اگر گروه یا ساختار اخطار وجود نداشت، بساز
    if chat_id not in group_data:
        group_data[chat_id] = {}
    if "warns" not in group_data[chat_id]:
        group_data[chat_id]["warns"] = {}
    if "admins" not in group_data[chat_id]:
        group_data[chat_id]["admins"] = []

    warns = group_data[chat_id]["warns"]
    warns[str(target.id)] = warns.get(str(target.id), 0) + 1
    count = warns[str(target.id)]
    save_json_file(GROUP_CTRL_FILE, group_data)

    # 🚫 اگر سه اخطار شد → بن شود
    if count >= 3:
        try:
            await context.bot.ban_chat_member(chat_id, target.id)
            await update.message.reply_text(
                f"🚫 <b>{target.first_name}</b> سه اخطار گرفت و بن شد!",
                parse_mode="HTML"
            )
            warns[str(target.id)] = 0
            save_json_file(GROUP_CTRL_FILE, group_data)
        except Exception as e:
            await update.message.reply_text(f"⚠️ خطا در بن:\n<code>{e}</code>", parse_mode="HTML")
    else:
        await update.message.reply_text(
            f"⚠️ <b>{target.first_name}</b> اخطار شماره <b>{count}</b> گرفت.",
            parse_mode="HTML"
    )



# 🤐 سکوت / رفع سکوت
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
        # 🔊 رفع سکوت کاربر
async def handle_unmute(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید روی پیام کاربر ریپلای بزنی.")

    target = update.message.reply_to_message.from_user
    chat = update.effective_chat
    user = update.effective_user

    try:
        await context.bot.restrict_chat_member(
            chat.id, 
            target.id,
            permissions=ChatPermissions(can_send_messages=True)
        )
        time_str = datetime.now().strftime("%H:%M - %d/%m/%Y")
        await update.message.reply_text(
            f"🔊 <b>{target.first_name}</b> از حالت سکوت خارج شد و می‌تواند پیام بفرستد.\n\n"
            f"👤 <b>توسط:</b> {user.first_name}\n"
            f"🕒 <b>زمان:</b> {time_str}",
            parse_mode="HTML"
        )
    except:
        await update.message.reply_text("⚠️ نمی‌توان سکوت این کاربر را برداشت (احتمالاً مدیر یا صاحب گروه است).", parse_mode="HTML")

# ======================= 🧹 Stealth Clean Pro+ (نسخه هوشمند و بی‌صدا) =======================
import asyncio
from datetime import datetime
from telegram.error import BadRequest, RetryAfter

async def handle_clean(update, context):
    """🧹 پاکسازی هوشمند و بی‌صدا — با تشخیص خودکار نوع پاکسازی"""
    try:
        user = update.effective_user
        chat = update.effective_chat
        message = update.message
        args = context.args if context.args else []

        # بررسی مجوز
        if not await is_authorized(update, context):
            return await message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

        # 🔍 تعیین حالت
        limit = 1000  # پیش‌فرض پاکسازی کامل
        mode = "all"
        if args and args[0].isdigit():
            limit = min(int(args[0]), 1000)
            mode = "number"
        elif message.reply_to_message:
            target_id = message.reply_to_message.from_user.id
            mode = "user"
        else:
            target_id = None

        last_id = message.message_id
        deleted = 0
        tasks = []

        async def safe_delete(msg_id):
            """حذف امن پیام با هندل خطاها"""
            try:
                # در حالت پاکسازی کاربر خاص
                if mode == "user":
                    fwd = await context.bot.forward_message(chat.id, chat.id, msg_id)
                    sender_id = fwd.forward_from.id if fwd.forward_from else None
                    await context.bot.delete_message(chat.id, fwd.message_id)
                    if sender_id != target_id:
                        return 0
                await context.bot.delete_message(chat.id, msg_id)
                return 1
            except (BadRequest, RetryAfter):
                return 0
            except Exception:
                return 0

        # 🚀 اجرای پاکسازی
        for _ in range(limit):
            last_id -= 1
            if last_id <= 0:
                break
            tasks.append(asyncio.create_task(safe_delete(last_id)))

            if len(tasks) >= 50:
                results = await asyncio.gather(*tasks)
                deleted += sum(results)
                tasks = []
                await asyncio.sleep(0.5)

        if tasks:
            results = await asyncio.gather(*tasks)
            deleted += sum(results)

        # حذف پیام دستور
        try:
            await context.bot.delete_message(chat.id, message.message_id)
        except:
            pass

        # 📩 ارسال گزارش خصوصی فقط به مدیر
        mode_label = {
            "all": "پاکسازی کامل گروه",
            "number": f"پاکسازی عددی ({limit})",
            "user": "پاکسازی پیام‌های کاربر خاص"
        }[mode]

        report = (
            f"✅ <b>گزارش پاکسازی</b>\n\n"
            f"🏷 <b>حالت:</b> {mode_label}\n"
            f"🧹 <b>گروه:</b> {chat.title}\n"
            f"👤 <b>توسط:</b> {user.first_name}\n"
            f"🗑 <b>تعداد حذف‌شده:</b> {deleted}\n"
            f"📆 <b>زمان:</b> {datetime.now().strftime('%H:%M:%S - %Y/%m/%d')}"
        )
        try:
            await context.bot.send_message(user.id, report, parse_mode="HTML")
        except:
            pass

    except Exception:
        pass
    
# 📌 پین کردن پیام (با ریپلای)
async def handle_pin(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("📌 باید روی پیام ریپلای بزنی تا سنجاق بشه.")

    try:
        await context.bot.pin_chat_message(update.effective_chat.id, update.message.reply_to_message.id)
        await update.message.reply_text("📍 پیام با موفقیت سنجاق شد.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در سنجاق پیام:\n<code>{e}</code>", parse_mode="HTML")


# 📍 برداشتن تمام پین‌ها
async def handle_unpin(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران یا سودوها مجازند!")

    try:
        await context.bot.unpin_all_chat_messages(update.effective_chat.id)
        await update.message.reply_text("📍 تمام پیام‌های سنجاق‌شده برداشته شدند.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در برداشتن پین:\n<code>{e}</code>", parse_mode="HTML")


# 🔒 قفل و باز کردن کل گروه (Mute All / Unmute All)
async def handle_lockgroup(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند گروه را قفل کنند!")

    chat = update.effective_chat
    try:
        await context.bot.set_chat_permissions(
            chat.id,
            ChatPermissions(can_send_messages=False)
        )
        await update.message.reply_text("🔒 گروه برای همه اعضا قفل شد! فقط مدیران می‌توانند پیام بدهند.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در قفل‌کردن گروه:\n<code>{e}</code>", parse_mode="HTML")


async def handle_unlockgroup(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند گروه را باز کنند!")

    chat = update.effective_chat
    try:
        await context.bot.set_chat_permissions(
            chat.id,
            ChatPermissions(can_send_messages=True)
        )
        await update.message.reply_text("🔓 گروه باز شد! همه می‌توانند پیام بفرستند.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بازکردن گروه:\n<code>{e}</code>", parse_mode="HTML")

    # ======================= 🔒 سیستم قفل‌های پیشرفته گروه =======================

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

for lock in LOCK_TYPES:
    ALIASES[f"lock_{lock}"] = [f"lock {lock}", f"قفل {lock}"]
    ALIASES[f"unlock_{lock}"] = [f"unlock {lock}", f"باز {lock}"]

save_json_file(ALIASES_FILE, ALIASES)


def set_lock_status(chat_id, lock_name, status):
    chat_id = str(chat_id)
    group = group_data.get(chat_id, {"locks": {}})
    locks = group.get("locks", {})
    locks[lock_name] = status
    group["locks"] = locks
    group_data[chat_id] = group
    save_json_file(GROUP_CTRL_FILE, group_data)


def get_lock_status(chat_id, lock_name):
    chat_id = str(chat_id)
    group = group_data.get(chat_id, {"locks": {}})
    locks = group.get("locks", {})
    return locks.get(lock_name, False)


# 🔐 قفل و باز کردن جزئیات
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


async def check_message_locks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = str(update.effective_chat.id)
    user = update.effective_user
    message = update.message

    # ✅ اگر کاربر مدیر یا سودو است، پیامش حذف نشود
    if user.id in SUDO_IDS:
        return
    group = group_data.get(chat_id, {})
    admins = group.get("admins", [])
    if str(user.id) in admins:
        return
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, user.id)
        if member.status in ["administrator", "creator"]:
            return
    except:
        pass

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
        await message.chat.send_message(
            f"🚫 پیام <b>{user.first_name}</b> حذف شد!\n🎯 دلیل: <b>{delete_reason}</b>",
            parse_mode="HTML"
        )


# 🧾 وضعیت قفل‌ها
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

# ======================= 👑 مدیریت مدیران =======================

async def handle_addadmin(update, context):
    # فقط مدیران مجاز
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط سودو یا مدیران ارشد می‌تونن مدیر اضافه کنن!")

    # باید روی پیام کسی ریپلای زده باشه
    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید روی پیام کسی ریپلای بزنی تا مدیرش کنم.")

    # ✋ جلوگیری از پاسخ خودکار ربات (مثلاً خوش‌آمد یا سخنگو)
    context.user_data["skip_autoresponse"] = True

    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)
    group = group_data.get(chat_id, {"admins": []})

    # بررسی تکرار
    if str(target.id) in group["admins"]:
        return await update.message.reply_text("⚠️ این کاربر قبلاً مدیر شده.")

    # افزودن مدیر
    group["admins"].append(str(target.id))
    group_data[chat_id] = group
    save_json_file(GROUP_CTRL_FILE, group_data)

    # پاسخ تأیید
    await update.message.reply_text(
        f"👑 <b>{target.first_name}</b> به عنوان مدیر افزوده شد.",
        parse_mode="HTML"
    )


async def handle_removeadmin(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط سودو یا مدیران ارشد می‌تونن مدیر حذف کنن!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید روی پیام مدیر ریپلای بزنی.")

    # ✋ جلوگیری از پاسخ خودکار ربات
    context.user_data["skip_autoresponse"] = True

    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)
    group = group_data.get(chat_id, {"admins": []})

    if str(target.id) not in group["admins"]:
        return await update.message.reply_text("⚠️ این کاربر مدیر نیست!")

    # حذف مدیر
    group["admins"].remove(str(target.id))
    group_data[chat_id] = group
    save_json_file(GROUP_CTRL_FILE, group_data)

    await update.message.reply_text(
        f"❌ <b>{target.first_name}</b> از مدیران حذف شد.",
        parse_mode="HTML"
    )


async def handle_admins(update, context):
    # ✋ جلوگیری از پاسخ خودکار در این دستور هم
    context.user_data["skip_autoresponse"] = True

    chat_id = str(update.effective_chat.id)
    group = group_data.get(chat_id, {"admins": []})
    admins = group.get("admins", [])

    if not admins:
        return await update.message.reply_text("ℹ️ هنوز هیچ مدیری ثبت نشده است.", parse_mode="HTML")

    text = "👑 <b>لیست مدیران گروه:</b>\n\n"
    for idx, admin_id in enumerate(admins, 1):
        text += f"{idx}. <a href='tg://user?id={admin_id}'>مدیر {idx}</a>\n"

    await update.message.reply_text(text, parse_mode="HTML")
# ======================= 💎 سیستم «اصل» پیشرفته مخصوص هر گروه =======================
import json, os, asyncio
from telegram import Update
from telegram.ext import ContextTypes

ORIGIN_FILE = "origins.json"
SUDO_IDS = [7089376754]  # 👑 آی‌دی سودوها

# 📂 بارگذاری و ذخیره‌سازی
def load_origins():
    if os.path.exists(ORIGIN_FILE):
        try:
            with open(ORIGIN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_origins(data):
    with open(ORIGIN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

origins = load_origins()

# 👑 بررسی مدیر یا سودو بودن
async def is_admin_or_sudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    if user.id in SUDO_IDS:
        return True

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ["administrator", "creator"]
    except:
        return False


# 🧹 پاکسازی داده‌های گروه وقتی ربات حذف شد
async def handle_bot_removed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id in origins:
        del origins[chat_id]
        save_origins(origins)
        print(f"🧹 داده‌های گروه {chat_id} پاک شد (ربات از گروه حذف شد).")


# ➕ ثبت اصل (فقط مدیرها و سودوها)
async def handle_set_origin(update, context):
    message = update.message
    user = update.effective_user
    chat_id = str(update.effective_chat.id)

    # فقط مدیران یا سودوها مجازند
    if not await is_admin_or_sudo(update, context):
        return await message.reply_text("🚫 فقط مدیران گروه یا سودوها می‌توانند اصل ثبت کنند!")

    raw_text = message.text.strip()
    origin_text = ""

    # حذف عبارت‌های شروع دستور
    for key in ["ثبت اصل", "set origin", "setorigin"]:
        if raw_text.lower().startswith(key):
            origin_text = raw_text[len(key):].strip()
            break

    # 🎯 اگر فقط نوشته "ثبت اصل" و ریپلای کرده → متن پیام اون فرد بشه اصل
    if not origin_text and message.reply_to_message:
        origin_text = message.reply_to_message.text or ""

    # ⚠️ اگر باز هم خالی بود
    if not origin_text:
        msg = await message.reply_text("⚠️ لطفاً متن اصل را بنویس یا روی پیام فردی ریپلای بزن.")
        await asyncio.sleep(10)
        try:
            await msg.delete()
            await message.delete()
        except:
            pass
        return

    # 🎯 هدف: ریپلای → اون کاربر / بدون ریپلای → خودش
    target = message.reply_to_message.from_user if message.reply_to_message else user

    # ساخت فضای مخصوص گروه
    if chat_id not in origins:
        origins[chat_id] = {}

    # ذخیره‌سازی اصل
    origins[chat_id][str(target.id)] = origin_text
    save_origins(origins)

    # ✨ پیام نهایی زیبا
    if target.id == user.id:
        msg_text = (
            f"💫 اصل شخصی شما با موفقیت ثبت شد ❤️\n\n"
            f"🧿 <b>{origin_text}</b>"
        )
    else:
        msg_text = (
            f"✅ اصل جدید برای <a href='tg://user?id={target.id}'>{target.first_name}</a> ثبت شد 💠\n\n"
            f"🧿 <b>{origin_text}</b>"
        )

    # ارسال پیام و حذف بعد از ۱۰ ثانیه
    msg_sent = await message.reply_text(msg_text, parse_mode="HTML")
    await asyncio.sleep(10)
    try:
        await msg_sent.delete()
        await message.delete()
    except:
        pass


# 🔍 نمایش اصل (برای همه)
async def handle_show_origin(update, context):
    message = update.message
    text = message.text.strip().lower()
    user = update.effective_user
    chat_id = str(update.effective_chat.id)

    target = None

    # اگر ریپلای کرده → اصل اون فرد رو نشون بده
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    # اگر نوشته "اصل من" → خودش
    elif text in ["اصل من", "اصل خودم", "my origin"]:
        target = user
    # اگر فقط نوشت "اصل" بدون ریپلای → هیچی نگو
    elif text in ["اصل", "اصلش", "origin"]:
        return

    if not target:
        return

    group_origins = origins.get(chat_id, {})
    origin_text = group_origins.get(str(target.id))

    # اگر اصل داشت نشون بده، نداشت سکوت کن
    if origin_text:
        if target.id == user.id:
            await message.reply_text(
                f"🌿 <b>اصل شما:</b>\n{origin_text}",
                parse_mode="HTML"
            )
        else:
            await message.reply_text(
                f"🧿 <b>اصل {target.first_name}:</b>\n{origin_text}",
                parse_mode="HTML"
)

import asyncio
from datetime import datetime, timedelta

# 🧹 پاکسازی خودکار داده‌های گروه‌های غیرفعال (هر ۷ روز یک‌بار)
async def auto_clean_old_origins(context):
    """بررسی خودکار گروه‌ها و حذف داده‌ی گروه‌هایی که ربات ازشون خارج شده"""
    print("🧭 شروع بررسی خودکار داده‌های قدیمی...")

    removed_groups = []
    to_delete = []

    # بررسی وضعیت هر گروه در فایل origins
    for chat_id in list(origins.keys()):
        try:
            chat = await context.bot.get_chat(chat_id)
            if chat.type not in ["group", "supergroup"]:
                to_delete.append(chat_id)
        except:
            # یعنی ربات از گروه رفته یا گروه وجود نداره
            to_delete.append(chat_id)

    # حذف داده‌های مربوط به گروه‌های نامعتبر
    for gid in to_delete:
        del origins[gid]
        removed_groups.append(gid)

    if removed_groups:
        save_origins(origins)
        print(f"🧹 {len(removed_groups)} گروه حذف شدند: {', '.join(removed_groups)}")
    else:
        print("✅ همه‌چیز تمیز است، هیچ گروهی برای حذف وجود ندارد.")

    print(f"⏰ بررسی بعدی در: {datetime.now() + timedelta(days=7)}")
# ======================= 🎮 هندلر اصلی دستورات گروه (نسخه نهایی کامل) =======================

async def group_command_handler(update, context):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip().lower()

    # 🧩 تغییر یا افزودن alias جدید (فقط سودو)
    if text.startswith("alias "):
        return await handle_alias(update, context)

    # 📋 نمایش وضعیت قفل‌ها
    if text in ["locks", "lock status", "وضعیت قفل"]:
        return await handle_locks_status(update, context)

    # 🧿 دستورات مربوط به سیستم "اصل"
    if text.startswith("ثبت اصل") or text.startswith("set origin") or text.startswith("setorigin"):
        return await handle_set_origin(update, context)
    elif text in ["اصل", "اصلش", "origin", "اصل من", "اصل خودم", "my origin"]:
        return await handle_show_origin(update, context)

    # 🚫 فیلترها و تگ‌ها
    for cmd, aliases in ALIASES.items():
        if text.startswith(tuple(aliases)):
            if cmd in ["addfilter", "delfilter", "filters"]:
                return await {
                    "addfilter": handle_addfilter,
                    "delfilter": handle_delfilter,
                    "filters": handle_filters
                }[cmd](update, context)


    # 🔄 بررسی تمام alias‌های مدیریتی و کنترلی
    for cmd, aliases in ALIASES.items():
        if text in aliases:
            # 🧱 بررسی قفل‌های خاص
            for lock in LOCK_TYPES:
                if cmd == f"lock_{lock}":
                    return await handle_lock_generic(update, context, lock)
                elif cmd == f"unlock_{lock}":
                    return await handle_unlock_generic(update, context, lock)

            # ⚙️ لیست تمام هندلرهای شناخته‌شده
            handlers = {
                "ban": handle_ban,
                "unban": handle_unban,
                "warn": handle_warn,
                "unwarn": handle_warn,
                "mute": handle_mute,
                "unmute": handle_unmute,
                "clean": handle_clean,
                "pin": handle_pin,
                "unpin": handle_unpin,
                "lockgroup": handle_lockgroup,
                "unlockgroup": handle_unlockgroup,
                "addadmin": handle_addadmin,
                "removeadmin": handle_removeadmin,
                "admins": handle_admins
            }

            # 🔍 اجرای تابع مرتبط با دستور
            if cmd in handlers:
                try:
                    return await handlers[cmd](update, context)
                except Exception as e:
                    try:
                        await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")
                    except:
                        pass
                    return

    # 💤 اگر هیچ دستوری تشخیص داده نشد
    return

# ======================= 🧠 فیلتر کلمات + تگ کاربران =======================

TAG_LIMIT = 5  # چند نفر در هر پیام تگ شوند

ALIASES_ADV = {
    "addfilter": ["addfilter", "افزودن‌فیلتر", "فیلترکن"],
    "delfilter": ["delfilter", "حذف‌فیلتر", "پاک‌فیلتر"],
    "filters": ["filters", "فیلترها", "لیست‌فیلتر"],
    "tagall": ["tagall", "تگ‌همه", "منشن‌همگانی"],
    "tagactive": ["tagactive", "تگ‌فعال", "تگ‌آنلاین"]
}


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


# ❌ حذف فیلتر
async def handle_delfilter(update, context):
    if not await can_manage(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if len(context.args) < 1:
        return await update.message.reply_text("📝 استفاده: delfilter [کلمه]\nمثلاً: delfilter تبلیغ")

    word = " ".join(context.args).strip().lower()
    chat_id = str(update.effective_chat.id)
    chat_filters = filters_data.get(chat_id, [])

    if word not in chat_filters:
        return await update.message.reply_text("⚠️ این کلمه در فیلتر وجود ندارد!")

    chat_filters.remove(word)
    filters_data[chat_id] = chat_filters
    save_filters(filters_data)
    await update.message.reply_text(f"🗑️ کلمه <b>{word}</b> از فیلتر حذف شد.", parse_mode="HTML")


# 📋 لیست فیلترها
async def handle_filters(update, context):
    chat_id = str(update.effective_chat.id)
    chat_filters = filters_data.get(chat_id, [])
    if not chat_filters:
        return await update.message.reply_text("ℹ️ هنوز هیچ کلمه‌ای فیلتر نشده است.")
    text = "🚫 <b>لیست کلمات فیلتر شده:</b>\n\n" + "\n".join([f"{i+1}. {w}" for i, w in enumerate(chat_filters)])
    await update.message.reply_text(text, parse_mode="HTML")


# 📣 تگ همه کاربران
async def handle_tagall(update, context):
    if not await can_manage(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    chat = update.effective_chat
    args_text = " ".join(context.args) if context.args else ""
    await update.message.reply_text("📣 درحال منشن همه کاربران...\n⏳ لطفاً صبر کنید.", parse_mode="HTML")

    members = []
    try:
        for member in await context.bot.get_chat_administrators(chat.id):
            if not member.user.is_bot:
                members.append(member.user)
    except Exception as e:
        return await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")

    text_group = ""
    counter = 0
    for user in members:
        text_group += f"[{user.first_name}](tg://user?id={user.id}) "
        counter += 1
        if counter % TAG_LIMIT == 0:
            try:
                await context.bot.send_message(chat.id, f"{text_group}\n\n{args_text}", parse_mode="Markdown")
            except:
                pass
            text_group = ""
    if text_group:
        await context.bot.send_message(chat.id, f"{text_group}\n\n{args_text}", parse_mode="Markdown")

    await update.message.reply_text("✅ تگ همه کاربران انجام شد.", parse_mode="HTML")


# 👥 تگ کاربران فعال
async def handle_tagactive(update, context):
    if not await can_manage(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    chat = update.effective_chat
    args_text = " ".join(context.args) if context.args else ""
    await update.message.reply_text("👥 درحال منشن کاربران فعال...", parse_mode="HTML")

    members = []
    try:
        for member in await context.bot.get_chat_administrators(chat.id):
            if not member.user.is_bot and member.user.is_premium:
                members.append(member.user)
    except Exception as e:
        return await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")

    if not members:
        return await update.message.reply_text("ℹ️ کاربر فعالی یافت نشد.")

    text_group = ""
    counter = 0
    for user in members:
        text_group += f"[{user.first_name}](tg://user?id={user.id}) "
        counter += 1
        if counter % TAG_LIMIT == 0:
            try:
                await context.bot.send_message(chat.id, f"{text_group}\n\n{args_text}", parse_mode="Markdown")
            except:
                pass
            text_group = ""
    if text_group:
        await context.bot.send_message(chat.id, f"{text_group}\n\n{args_text}", parse_mode="Markdown")

    await update.message.reply_text("✅ تگ کاربران فعال انجام شد.", parse_mode="HTML")

# ======================= 🧠 هندلر کلی alias پیشرفته =======================

async def group_text_handler_adv(update, context):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip().lower()


    # ⚙️ aliasهای پیشرفته (فیلترها و تگ‌ها)
    for cmd, aliases in ALIASES_ADV.items():
        for alias in aliases:
            if text.startswith(alias):
                args = text.replace(alias, "", 1).strip().split()
                context.args = args
                handlers = {
                    "addfilter": handle_addfilter,
                    "delfilter": handle_delfilter,
                    "filters": handle_filters,
                    "tagall": handle_tagall,
                    "tagactive": handle_tagactive
                }
                if cmd in handlers:
                    return await handlers[cmd](update, context)
    return


# ======================= 🧩 سیستم alias برای شخصی‌سازی دستورات =======================

async def handle_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    🧩 افزودن یا تغییر alias جدید برای دستورات گروهی
    فقط مدیران یا سودوها مجازند
    """

    # بررسی سطح دسترسی
    if not await is_authorized(update, context):
        return await update.message.reply_text(
            "🚫 فقط مدیران یا سودوها می‌توانند alias جدید بسازند!"
        )

    # گرفتن آرگومان‌ها
    parts = update.message.text.strip().split(" ", 2)
    if len(parts) < 3:
        return await update.message.reply_text(
            "🧩 استفاده‌ی درست از دستور:\n"
            "<code>alias [دستور اصلی] [نام جدید]</code>\n\n"
            "مثلاً:\n<code>alias ban محروم</code>",
            parse_mode="HTML"
        )

    base_cmd, new_alias = parts[1].lower(), parts[2].strip().lower()

    # بررسی وجود دستور اصلی
    if base_cmd not in ALIASES:
        return await update.message.reply_text(
            f"⚠️ همچین دستوری وجود ندارد!\n"
            f"دستورات معتبر:\n<b>{', '.join(ALIASES.keys())}</b>",
            parse_mode="HTML"
        )

    # بررسی تکراری بودن alias
    all_aliases = [a for aliases in ALIASES.values() for a in aliases]
    if new_alias in all_aliases:
        return await update.message.reply_text(
            "⚠️ این alias قبلاً برای دستور دیگری استفاده شده است!",
            parse_mode="HTML"
        )

    # افزودن alias جدید
    ALIASES[base_cmd].append(new_alias)
    save_json_file(ALIASES_FILE, ALIASES)

    await update.message.reply_text(
        f"✅ alias جدید با موفقیت ثبت شد!\n\n"
        f"🔹 دستور اصلی: <b>{base_cmd}</b>\n"
        f"🔸 alias جدید: <b>{new_alias}</b>",
        parse_mode="HTML"
    )


# ======================= ✅ اعلان راه‌اندازی سیستم =======================

print("✅ [Group Control System] با موفقیت بارگذاری شد.")
