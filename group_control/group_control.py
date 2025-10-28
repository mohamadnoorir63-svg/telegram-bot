# ======================= ⚙️ سیستم کنترل گروه (بخش پایه و فایل‌ها) =======================
import json, os, re
from datetime import datetime
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes

# ======================= 🔧 فایل‌ها و تنظیمات اصلی =======================

GROUP_CTRL_FILE = "group_control.json"   # 📂 فایل تنظیمات گروه‌ها
ALIASES_FILE = "aliases.json"            # 📂 فایل دستورهای جایگزین (alias)
FILTER_FILE = "filters.json"             # 📂 فایل فیلتر کلمات

# 👑 لیست سودوها (کاربران خاصی که همیشه مجازند)
SUDO_IDS = [1777319036, 7089376754]  # ← آیدی خودت و سودوهای دیگر

# 📁 پوشه بک‌آپ
BACKUP_DIR = "backups"
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

# ======================= 📥 توابع لود و ذخیره فایل‌ها =======================

def load_json_file(path, default):
    """📥 لود فایل JSON با بازیابی خودکار از بک‌آپ در صورت خرابی"""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                print(f"⚠️ فایل {path} معتبر نیست، از مقدار پیش‌فرض استفاده می‌شود.")
        except Exception as e:
            print(f"⚠️ خطا در لود {path}: {e} — تلاش برای بازیابی از بک‌آپ...")

    # 📦 اگر فایل اصلی خراب بود، از بک‌آپ بخوان
    backup_path = os.path.join(BACKUP_DIR, f"backup_{os.path.basename(path)}")
    if os.path.exists(backup_path):
        try:
            with open(backup_path, "r", encoding="utf-8") as b:
                data = json.load(b)
                if isinstance(data, dict):
                    print(f"♻️ {path} از بک‌آپ بازیابی شد ✅")
                    return data
        except Exception as e:
            print(f"⚠️ بک‌آپ {backup_path} نیز خراب است: {e}")

    # در نهایت مقدار پیش‌فرض برگردان
    return default if isinstance(default, dict) else {}

def save_json_file(path, data):
    """💾 ذخیره فایل JSON به همراه بک‌آپ خودکار"""
    try:
        # ذخیره فایل اصلی
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # بک‌آپ در پوشه backups
        backup_path = os.path.join(BACKUP_DIR, f"backup_{os.path.basename(path)}")
        with open(backup_path, "w", encoding="utf-8") as b:
            json.dump(data, b, ensure_ascii=False, indent=2)

        print(f"💾 فایل {os.path.basename(path)} و بک‌آپ آن ذخیره شد ✅")

    except Exception as e:
        print(f"⚠️ خطا در ذخیره {path}: {e}")

# 📂 لود داده‌های اولیه
group_data = load_json_file(GROUP_CTRL_FILE, {})
ALIASES = load_json_file(ALIASES_FILE, {})
filters_data = load_json_file(FILTER_FILE, {})

print("✅ [Group Control System Base] آماده است.")
# ======================= 🧩 تعریف دستورات (ALIASES) =======================

ALIASES = {
    # 🚫 مدیریت اعضا
    "ban": ["ban", "بن", "اخراج", "بن کاربر"],
    "unban": ["unban", "آزاد", "حذف بن", "رفع بن"],
    "warn": ["warn", "اخطار", "هشدار"],
    "unwarn": ["unwarn", "حذف اخطار", "رفع اخطار", "پاک‌اخطار"],

    # 🤐 سکوت / رفع سکوت
    "mute": ["mute", "سکوت", "خفه", "بی‌صدا"],
    "unmute": ["unmute", "رفع سکوت", "بازکردن سکوت", "آزادسکوت"],

    # 👑 مدیریت مدیران
    "addadmin": ["addadmin", "افزودن مدیر", "ادمین کن", "مدیر کن"],
    "removeadmin": ["removeadmin", "حذف مدیر", "برکنار مدیر"],
    "admins": ["admins", "لیست مدیران", "مدیران", "ادمین‌ها"],

    # 🔒 قفل و بازکردن گروه (کلی)
    "lockgroup": ["lockgroup", "قفل گروه", "بستن گروه", "ببند گروه"],
    "unlockgroup": ["unlockgroup", "بازکردن گروه", "باز گروه", "بازکن گروه"],

    # 🔐 قفل‌های خاص رسانه‌ها
    "lock": ["lock", "قفل", "بستن", "مسدودکردن"],
    "unlock": ["unlock", "بازکردن", "آزادکردن"],

    # 🧱 قفل‌های رسانه‌ای و جزئیات (با فارسی مخصوص تو)
    "lock_links": ["قفل لینک‌ها", "قفل لینک"],
    "unlock_links": ["بازکردن لینک‌ها", "بازکردن لینک"],
    "lock_media": ["قفل رسانه", "قفل مدیا"],
    "unlock_media": ["بازکردن رسانه", "بازکردن مدیا"],
    "lock_photos": ["قفل عکس"],
    "unlock_photos": ["بازکردن عکس"],
    "lock_videos": ["قفل ویدیو"],
    "unlock_videos": ["بازکردن ویدیو"],
    "lock_files": ["قفل فایل"],
    "unlock_files": ["بازکردن فایل"],
    "lock_gifs": ["قفل گیف"],
    "unlock_gifs": ["بازکردن گیف"],
    "lock_stickers": ["قفل استیکر"],
    "unlock_stickers": ["بازکردن استیکر"],

    # 🧹 پاکسازی پیام‌ها
    "clean": ["clean", "پاکسازی", "پاک کردن", "حذف عددی", "پاک عددی", "نظافت"],

    # 📌 پین و حذف پین
    "pin": ["pin", "پین", "سنجاق", "پن"],
    "unpin": ["unpin", "حذف پین", "برداشتن پین", "پاک پین"],

    # 🧿 سیستم «اصل»
    "setorigin": ["setorigin", "ثبت اصل", "set origin"],
    "showorigin": ["showorigin", "اصل", "اصل من", "اصلش", "اصل خودم"],

    # 🧩 alias
    "alias": ["alias", "تغییر", "تغییرنام", "نام مستعار"],

    # 🚫 فیلتر کلمات
    "addfilter": ["addfilter", "افزودن فیلتر", "فیلتر کن"],
    "delfilter": ["delfilter", "حذف فیلتر", "پاک فیلتر"],
    "filters": ["filters", "لیست فیلترها", "فیلترها"],

    # 📣 تگ کاربران
    "tagall": ["tagall", "تگ همه", "منشن همه", "تگ کاربران"],
    "tagactive": ["tagactive", "تگ کاربران فعال", "تگ فعال"],
    "tagnonactive": ["tagnonactive", "تگ کاربران غیره فعال", "تگ غیرفعال"],
    "tagadmins": ["tagadmins", "تگ مدیران", "منشن مدیران"]
}
# ======================= 👑 بررسی مجوزها و هدف دستورات =======================

async def is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    🔐 بررسی اینکه آیا کاربر مجاز است (مدیر، سودو یا مالک)
    """
    user = update.effective_user
    chat = update.effective_chat
    chat_id = str(chat.id)

    # 👑 اگر سودو باشد همیشه مجاز است
    if user.id in SUDO_IDS:
        return True

    # 🧩 بررسی مدیران ذخیره‌شده در فایل
    group = group_data.get(chat_id, {})
    admins = group.get("admins", [])
    if str(user.id) in admins:
        return True

    # 📡 بررسی مدیران واقعی تلگرام
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status in ["administrator", "creator"]:
            return True
    except:
        pass

    # 🚫 در غیر این صورت مجاز نیست
    return False


async def can_act_on_target(update: Update, context: ContextTypes.DEFAULT_TYPE, target):
    """
    🧱 بررسی اینکه آیا ربات می‌تواند روی هدف (کاربر) عملی انجام دهد یا نه
    مثل بن یا سکوت — جلوی بن مدیر و سودو را می‌گیرد
    """
    bot = await context.bot.get_me()
    chat = update.effective_chat

    # 🚫 جلوگیری از اعمال روی خود ربات
    if target.id == bot.id:
        replies = [
            "😏 می‌خوای منو بن کنی؟ من خودم اینجارو می‌گردونم!",
            "😂 شوخی می‌کنی؟ منو بن می‌کنی؟",
            "😎 اول خودتو بن کن بعد منو!"
        ]
        await update.message.reply_text(replies[hash(target.id) % len(replies)])
        return False

    # 🚫 جلوگیری از اعمال روی سودو یا مدیر اصلی
    if target.id in SUDO_IDS or target.id == int(os.getenv("ADMIN_ID", "7089376754")):
        await update.message.reply_text("⚠️ این کاربر از مدیران ارشد است — نمی‌تونی کاریش کنی!")
        return False

    # 🚫 جلوگیری از اعمال روی مدیر واقعی گروه
    try:
        member = await context.bot.get_chat_member(chat.id, target.id)
        if member.status in ["administrator", "creator"]:
            await update.message.reply_text("⚠️ نمی‌تونی روی مدیر گروه کاری انجام بدی!")
            return False
    except:
        pass

    return True
    # ======================= 🚫 دستورات مدیریتی اصلی =======================

# 🚷 بن کاربر
async def handle_ban(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید روی پیام کاربر ریپلای بزنی تا بن بشه.")

    target = update.message.reply_to_message.from_user
    chat = update.effective_chat

    if not await can_act_on_target(update, context, target):
        return

    try:
        await context.bot.ban_chat_member(chat.id, target.id)
        await update.message.reply_text(
            f"🚫 <b>{target.first_name}</b> از گروه بن شد.",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بن:\n<code>{e}</code>", parse_mode="HTML")


# ✅ رفع بن
async def handle_unban(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران یا سودوها مجازند!")

    chat = update.effective_chat

    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
    elif context.args:
        user_id = int(context.args[0])
    else:
        return await update.message.reply_text("🔹 باید روی پیام فرد ریپلای بزنی یا آیدی بدی.")

    try:
        await context.bot.unban_chat_member(chat.id, user_id)
        await update.message.reply_text("✅ کاربر از بن خارج شد.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در رفع‌بن:\n<code>{e}</code>", parse_mode="HTML")


# ⚠️ اخطار — (۳ اخطار = بن خودکار)
async def handle_warn(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید روی پیام کاربر ریپلای بزنی.")

    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)

    if not await can_act_on_target(update, context, target):
        return

    # 🧠 ذخیره اخطار
    if chat_id not in group_data:
        group_data[chat_id] = {}
    if "warns" not in group_data[chat_id]:
        group_data[chat_id]["warns"] = {}

    warns = group_data[chat_id]["warns"]
    warns[str(target.id)] = warns.get(str(target.id), 0) + 1
    count = warns[str(target.id)]
    save_json_file(GROUP_CTRL_FILE, group_data)

    # 🚫 اگر سه اخطار → بن خودکار
    if count >= 3:
        try:
            await context.bot.ban_chat_member(chat_id, target.id)
            await update.message.reply_text(
                f"🚫 <b>{target.first_name}</b> سه اخطار گرفت و بن شد!",
                parse_mode="HTML"
            )
            warns[str(target.id)] = 0  # ریست اخطار
            save_json_file(GROUP_CTRL_FILE, group_data)
        except Exception as e:
            await update.message.reply_text(f"⚠️ خطا در بن:\n<code>{e}</code>", parse_mode="HTML")
    else:
        await update.message.reply_text(
            f"⚠️ <b>{target.first_name}</b> اخطار شماره <b>{count}</b> گرفت.",
            parse_mode="HTML"
        )


# 🧹 پاک‌اخطار (رفع اخطار)
async def handle_unwarn(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید روی پیام فرد ریپلای بزنی.")

    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)

    if chat_id in group_data and "warns" in group_data[chat_id]:
        warns = group_data[chat_id]["warns"]
        warns[str(target.id)] = 0
        save_json_file(GROUP_CTRL_FILE, group_data)
        await update.message.reply_text(
            f"✅ اخطارهای <b>{target.first_name}</b> پاک شد.",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text("ℹ️ این کاربر هیچ اخطاری نداشت.", parse_mode="HTML")


# 🤐 سکوت کاربر
async def handle_mute(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

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
            f"🤐 <b>{target.first_name}</b> در سکوت قرار گرفت.\n"
            f"👤 توسط: {user.first_name}\n🕒 {time_str}",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در سکوت:\n<code>{e}</code>", parse_mode="HTML")


# 🔊 رفع سکوت
async def handle_unmute(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید روی پیام فرد ریپلای بزنی.")

    target = update.message.reply_to_message.from_user
    chat = update.effective_chat
    user = update.effective_user

    try:
        await context.bot.restrict_chat_member(
            chat.id,
            target.id,
            permissions=ChatPermissions(can_send_messages=True)
        )
        await update.message.reply_text(
            f"🔊 <b>{target.first_name}</b> از حالت سکوت خارج شد.\n"
            f"👤 توسط: {user.first_name}",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")
        # ======================= 🧹 پاکسازی پیام‌ها =======================

import asyncio
from telegram.error import BadRequest, RetryAfter

async def handle_clean(update, context):
    """🧹 پاکسازی هوشمند و بی‌صدا — با تشخیص نوع حذف"""
    user = update.effective_user
    chat = update.effective_chat
    message = update.message
    args = context.args if context.args else []

    # مجوز
    if not await is_authorized(update, context):
        return await message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    limit = 100  # پیش‌فرض
    mode = "all"

    if args and args[0].isdigit():
        limit = min(int(args[0]), 1000)
        mode = "number"

    last_id = message.message_id
    deleted = 0
    tasks = []

    async def safe_delete(msg_id):
        try:
            await context.bot.delete_message(chat.id, msg_id)
            return 1
        except (BadRequest, RetryAfter):
            return 0
        except Exception:
            return 0

    # 🚀 حذف دسته‌ای
    for _ in range(limit):
        last_id -= 1
        if last_id <= 0:
            break
        tasks.append(asyncio.create_task(safe_delete(last_id)))

        if len(tasks) >= 30:
            results = await asyncio.gather(*tasks)
            deleted += sum(results)
            tasks = []
            await asyncio.sleep(0.3)

    if tasks:
        results = await asyncio.gather(*tasks)
        deleted += sum(results)

    try:
        await context.bot.delete_message(chat.id, message.message_id)
    except:
        pass

    await context.bot.send_message(
        chat.id,
        f"🧹 <b>پاکسازی انجام شد!</b>\n🗑 حذف‌شده: {deleted} پیام",
        parse_mode="HTML"
    )


# ======================= 📌 پین و حذف پین =======================

async def handle_pin(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("📌 باید روی پیام ریپلای بزنی تا پین بشه.")

    try:
        await context.bot.pin_chat_message(update.effective_chat.id, update.message.reply_to_message.id)
        await update.message.reply_text("📍 پیام با موفقیت پین شد.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در پین:\n<code>{e}</code>", parse_mode="HTML")


async def handle_unpin(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    try:
        await context.bot.unpin_all_chat_messages(update.effective_chat.id)
        await update.message.reply_text("📍 همه‌ی پین‌ها حذف شدند.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در حذف پین:\n<code>{e}</code>", parse_mode="HTML")


# ======================= 🔒 قفل و بازگروه =======================

async def handle_lockgroup(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند گروه را قفل کنند!")

    chat = update.effective_chat
    try:
        await context.bot.set_chat_permissions(chat.id, ChatPermissions(can_send_messages=False))
        await update.message.reply_text("🔒 گروه قفل شد! فقط مدیران می‌توانند پیام بدهند.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در قفل گروه:\n<code>{e}</code>", parse_mode="HTML")


async def handle_unlockgroup(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند گروه را باز کنند!")

    chat = update.effective_chat
    try:
        await context.bot.set_chat_permissions(chat.id, ChatPermissions(can_send_messages=True))
        await update.message.reply_text("🔓 گروه باز شد! همه می‌توانند پیام بدهند.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بازگروه:\n<code>{e}</code>", parse_mode="HTML")
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
    "media": "ارسال تمام مدیاها",
    "chat": "ارسال پیام متنی"
}


# 💾 ذخیره و واکشی وضعیت قفل‌ها
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


# 🔐 فعال کردن قفل خاص
async def handle_lock_generic(update, context, lock_name):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    chat = update.effective_chat
    user = update.effective_user

    if get_lock_status(chat.id, lock_name):
        return await update.message.reply_text(f"🔒 {LOCK_TYPES[lock_name]} از قبل قفل است!")

    set_lock_status(chat.id, lock_name, True)
    await update.message.reply_text(
        f"🔒 <b>{LOCK_TYPES[lock_name]}</b> قفل شد.\n👤 توسط: {user.first_name}",
        parse_mode="HTML"
    )


# 🔓 غیرفعال کردن قفل خاص
async def handle_unlock_generic(update, context, lock_name):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    chat = update.effective_chat
    user = update.effective_user

    if not get_lock_status(chat.id, lock_name):
        return await update.message.reply_text(f"🔓 {LOCK_TYPES[lock_name]} از قبل باز است!")

    set_lock_status(chat.id, lock_name, False)
    await update.message.reply_text(
        f"🔓 <b>{LOCK_TYPES[lock_name]}</b> باز شد.\n👤 توسط: {user.first_name}",
        parse_mode="HTML"
    )


# 🚨 بررسی پیام‌های جدید و حذف در صورت نقض قفل‌ها
async def check_message_locks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = str(update.effective_chat.id)
    user = update.effective_user
    message = update.message
    locks = group_data.get(chat_id, {}).get("locks", {})

    if not locks:
        return

    # ✅ مدیرها و سودوها از قفل‌ها مستثنا هستند
    if await is_authorized(update, context):
        return

    delete_reason = None
    text = (message.text or "").lower()

    if locks.get("links") and ("http" in text or "t.me/" in text):
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
        delete_reason = "ارسال تبلیغ"
    elif locks.get("usernames") and "@" in text:
        delete_reason = "ارسال یوزرنیم"
    elif locks.get("media") and (message.photo or message.video or message.animation):
        delete_reason = "ارسال مدیا (قفل کلی)"
    elif locks.get("chat") and message.text:
        delete_reason = "ارسال پیام متنی"

    if delete_reason:
        try:
            await message.delete()
            await context.bot.send_message(
                chat_id,
                f"🚫 پیام <b>{user.first_name}</b> حذف شد.\n🎯 دلیل: {delete_reason}",
                parse_mode="HTML"
            )
        except:
            pass


# 📋 نمایش وضعیت فعلی قفل‌ها
async def handle_locks_status(update, context):
    chat_id = str(update.effective_chat.id)
    locks = group_data.get(chat_id, {}).get("locks", {})

    if not locks:
        return await update.message.reply_text("🔓 هیچ قفلی فعال نیست.", parse_mode="HTML")

    text = "🧱 <b>وضعیت قفل‌های گروه:</b>\n\n"
    for lock, desc in LOCK_TYPES.items():
        status = "🔒 فعال" if locks.get(lock, False) else "🔓 غیرفعال"
        text += f"▫️ <b>{desc}:</b> {status}\n"
    await update.message.reply_text(text, parse_mode="HTML")
    # ======================= 👑 مدیریت مدیران گروه =======================

async def handle_addadmin(update, context):
    """افزودن مدیر جدید به سیستم داخلی ربات"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط سودو یا مدیران ارشد می‌تونن مدیر اضافه کنن!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید روی پیام کاربر ریپلای بزنی تا مدیر بشه.")

    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)
    group = group_data.get(chat_id, {"admins": []})

    if str(target.id) in group["admins"]:
        return await update.message.reply_text("⚠️ این کاربر قبلاً مدیر بوده.")

    group["admins"].append(str(target.id))
    group_data[chat_id] = group
    save_json_file(GROUP_CTRL_FILE, group_data)

    await update.message.reply_text(
        f"👑 <b>{target.first_name}</b> به‌عنوان مدیر اضافه شد.",
        parse_mode="HTML"
    )


async def handle_removeadmin(update, context):
    """حذف مدیر از لیست مدیران ثبت‌شده"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط سودو یا مدیران ارشد می‌تونن مدیر حذف کنن!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید روی پیام مدیر ریپلای بزنی.")

    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)
    group = group_data.get(chat_id, {"admins": []})

    if str(target.id) not in group["admins"]:
        return await update.message.reply_text("⚠️ این کاربر مدیر نیست!")

    group["admins"].remove(str(target.id))
    group_data[chat_id] = group
    save_json_file(GROUP_CTRL_FILE, group_data)

    await update.message.reply_text(
        f"❌ <b>{target.first_name}</b> از مدیران حذف شد.",
        parse_mode="HTML"
    )


async def handle_admins(update, context):
    """نمایش لیست تمام مدیران ثبت‌شده در گروه"""
    chat_id = str(update.effective_chat.id)
    group = group_data.get(chat_id, {"admins": []})
    admins = group.get("admins", [])

    if not admins:
        return await update.message.reply_text("ℹ️ هنوز هیچ مدیری ثبت نشده.", parse_mode="HTML")

    text = "👑 <b>لیست مدیران گروه:</b>\n\n"
    for idx, admin_id in enumerate(admins, 1):
        text += f"{idx}. <a href='tg://user?id={admin_id}'>مدیر {idx}</a>\n"

    await update.message.reply_text(text, parse_mode="HTML")
    # ======================= 💎 سیستم «اصل» مخصوص هر گروه =======================
import json, os, asyncio
from telegram import Update
from telegram.ext import ContextTypes

ORIGIN_FILE = "origins.json"

# 📂 بارگذاری داده‌ها
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


# 👑 بررسی اینکه آیا کاربر مدیر یا سودو است
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


# 🧩 ثبت اصل
async def handle_set_origin(update, context):
    message = update.message
    user = update.effective_user
    chat_id = str(update.effective_chat.id)

    # فقط مدیران و سودوها مجازند
    if not await is_admin_or_sudo(update, context):
        return await message.reply_text("🚫 فقط مدیران یا سودوها می‌تونن اصل ثبت کنن!")

    raw_text = message.text.strip()
    origin_text = ""

    # حذف دستور از ابتدای جمله
    for key in ["ثبت اصل", "setorigin", "set origin"]:
        if raw_text.startswith(key):
            origin_text = raw_text[len(key):].strip()
            break

    # اگر ریپلای کرده باشه و متن ننوشته باشه → متن اون پیام میشه اصل
    if not origin_text and message.reply_to_message:
        origin_text = message.reply_to_message.text or ""

    if not origin_text:
        return await message.reply_text("⚠️ لطفاً متن اصل را بنویس یا روی پیام فردی ریپلای بزن.")

    target = message.reply_to_message.from_user if message.reply_to_message else user

    if chat_id not in origins:
        origins[chat_id] = {}

    origins[chat_id][str(target.id)] = origin_text
    save_origins(origins)

    if target.id == user.id:
        msg_text = f"💫 اصل شخصی شما با موفقیت ثبت شد.\n🧿 <b>{origin_text}</b>"
    else:
        msg_text = (
            f"✅ اصل جدید برای <a href='tg://user?id={target.id}'>{target.first_name}</a> ثبت شد.\n"
            f"🧿 <b>{origin_text}</b>"
        )

    await message.reply_text(msg_text, parse_mode="HTML")


# 🔍 نمایش اصل
async def handle_show_origin(update, context):
    message = update.message
    text = message.text.strip().lower()
    user = update.effective_user
    chat_id = str(update.effective_chat.id)

    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif text in ["اصل من", "اصل خودم", "my origin"]:
        target = user
    else:
        return  # اگر فقط نوشت "اصل" بدون ریپلای، هیچی نگو

    group_origins = origins.get(chat_id, {})
    origin_text = group_origins.get(str(target.id))

    if origin_text:
        if target.id == user.id:
            await message.reply_text(f"🌿 <b>اصل شما:</b>\n{origin_text}", parse_mode="HTML")
        else:
            await message.reply_text(
                f"🧿 <b>اصل {target.first_name}:</b>\n{origin_text}", parse_mode="HTML"
            )
    else:
        await message.reply_text("❗ این کاربر هنوز اصلی ندارد.", parse_mode="HTML")
        # ======================= 🚫 سیستم فیلتر کلمات =======================

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

# 🧩 افزودن فیلتر
async def handle_addfilter(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

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
    await update.message.reply_text(f"✅ کلمه <b>{word}</b> فیلتر شد.", parse_mode="HTML")


# ❌ حذف فیلتر
async def handle_delfilter(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if len(context.args) < 1:
        return await update.message.reply_text("📝 استفاده: delfilter [کلمه]\nمثلاً: delfilter تبلیغ")

    word = " ".join(context.args).strip().lower()
    chat_id = str(update.effective_chat.id)
    chat_filters = filters_data.get(chat_id, [])

    if word not in chat_filters:
        return await update.message.reply_text("⚠️ این کلمه در فیلتر نیست!")

    chat_filters.remove(word)
    filters_data[chat_id] = chat_filters
    save_filters(filters_data)
    await update.message.reply_text(f"🗑️ کلمه <b>{word}</b> از فیلتر حذف شد.", parse_mode="HTML")


# 📋 نمایش لیست فیلترها
async def handle_filters(update, context):
    chat_id = str(update.effective_chat.id)
    chat_filters = filters_data.get(chat_id, [])
    if not chat_filters:
        return await update.message.reply_text("ℹ️ هیچ کلمه‌ای فیلتر نشده.", parse_mode="HTML")

    text = "🚫 <b>کلمات فیلتر شده:</b>\n\n" + "\n".join([f"• {w}" for w in chat_filters])
    await update.message.reply_text(text, parse_mode="HTML")


# 🚨 بررسی و حذف پیام‌های حاوی کلمات فیلتر
async def check_message_filters(update, context):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    chat_id = str(update.effective_chat.id)
    filters = filters_data.get(chat_id, [])

    for word in filters:
        if word in text:
            try:
                await update.message.delete()
                await context.bot.send_message(
                    chat_id,
                    f"🚫 پیام <b>{update.effective_user.first_name}</b> به دلیل استفاده از کلمه‌ی <b>{word}</b> حذف شد.",
                    parse_mode="HTML"
                )
            except:
                pass
            break
            # ======================= 📣 تگ کاربران =======================

TAG_LIMIT = 5  # چند نفر در هر پیام تگ شوند

async def handle_tagall(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    chat = update.effective_chat
    args_text = " ".join(context.args) if context.args else ""
    await update.message.reply_text("📣 درحال منشن همه کاربران...", parse_mode="HTML")

    members = []
    try:
        async for member in context.bot.get_chat_administrators(chat.id):
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
            await context.bot.send_message(chat.id, f"{text_group}\n\n{args_text}", parse_mode="Markdown")
            text_group = ""

    if text_group:
        await context.bot.send_message(chat.id, f"{text_group}\n\n{args_text}", parse_mode="Markdown")

    await update.message.reply_text("✅ تگ همه کاربران انجام شد.", parse_mode="HTML")


async def handle_tagadmins(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    chat = update.effective_chat
    args_text = " ".join(context.args) if context.args else ""
    await update.message.reply_text("👑 درحال تگ مدیران...", parse_mode="HTML")

    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        admin_list = [f"[{a.user.first_name}](tg://user?id={a.user.id})" for a in admins if not a.user.is_bot]
        admin_text = " ".join(admin_list)
        await context.bot.send_message(chat.id, f"{admin_text}\n\n{args_text}", parse_mode="Markdown")
        await update.message.reply_text("✅ مدیران تگ شدند.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")
        # ======================= 🎮 هندلر اصلی دستورات گروه =======================

async def group_command_handler(update, context):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip().lower()

    # 🧩 alias جدید (تغییر یا افزودن دستور مستعار)
    if text.startswith("alias "):
        return await handle_alias(update, context)

    # 📋 وضعیت قفل‌ها
    if text in ["locks", "lock status", "وضعیت قفل"]:
        return await handle_locks_status(update, context)

    # 🧿 سیستم "اصل"
    if text.startswith(("ثبت اصل", "set origin", "setorigin")):
        return await handle_set_origin(update, context)
    elif text in ["اصل", "اصلش", "origin", "اصل من", "اصل خودم", "my origin"]:
        return await handle_show_origin(update, context)

    # 🚫 فیلترها
    if text.startswith("افزودن فیلتر") or text.startswith("addfilter"):
        return await handle_addfilter(update, context)
    if text.startswith("حذف فیلتر") or text.startswith("delfilter"):
        return await handle_delfilter(update, context)
    if text in ["فیلترها", "filters", "لیست فیلتر"]:
        return await handle_filters(update, context)

    # 📣 تگ‌ها
    if text in ["تگ همه", "tagall"]:
        return await handle_tagall(update, context)
    if text in ["تگ مدیران", "tagadmins"]:
        return await handle_tagadmins(update, context)
    if text in ["تگ فعال", "تگ کاربران فعال", "tagactive"]:
        return await handle_tagactive(update, context)

    # 🔒 قفل گروه
    if text in ["قفل گروه", "lockgroup", "ببند گروه"]:
        return await handle_lockgroup(update, context)
    if text in ["باز گروه", "بازکردن گروه", "unlockgroup"]:
        return await handle_unlockgroup(update, context)

    # ⚙️ قفل‌های جزئی (مدیا، لینک، و غیره)
    for lock in LOCK_TYPES:
        if text.startswith(f"قفل {lock}") or text.startswith(f"lock {lock}"):
            return await handle_lock_generic(update, context, lock)
        if text.startswith(f"باز {lock}") or text.startswith(f"unlock {lock}"):
            return await handle_unlock_generic(update, context, lock)

    # 👑 مدیریت مدیران
    if text in ["افزودن مدیر", "addadmin"]:
        return await handle_addadmin(update, context)
    if text in ["حذف مدیر", "removeadmin"]:
        return await handle_removeadmin(update, context)
    if text in ["مدیران", "لیست مدیران", "admins"]:
        return await handle_admins(update, context)

    # 🚫 دستورات اصلی مدیریت کاربران
    if text in ["بن", "اخراج", "ban"]:
        return await handle_ban(update, context)
    if text in ["رفع بن", "آزاد", "unban"]:
        return await handle_unban(update, context)
    if text in ["اخطار", "warn"]:
        return await handle_warn(update, context)
    if text in ["حذف اخطار", "رفع اخطار", "unwarn"]:
        return await handle_unwarn(update, context)
    if text in ["سکوت", "خفه", "mute"]:
        return await handle_mute(update, context)
    if text in ["رفع سکوت", "بازکردن سکوت", "unmute"]:
        return await handle_unmute(update, context)

    # 🧹 پاکسازی
    if text in ["پاکسازی", "پاک", "حذف عددی", "clean"]:
        return await handle_clean(update, context)

    # 📌 پین / حذف پین
    if text in ["پین", "سنجاق", "pin"]:
        return await handle_pin(update, context)
    if text in ["حذف پین", "بردار پین", "unpin"]:
        return await handle_unpin(update, context)

    # اگر چیزی تشخیص داده نشد:
    return
    # ======================= ⚙️ گروه هندلر پیشرفته سازگار با ساختار اصلی =======================

async def group_text_handler_adv(update, context):
    """
    🎯 هندلر عمومی پیام‌های متنی گروه‌ها
    این تابع فقط نقش رابط را دارد تا با سیستم اصلی در bot.py هماهنگ باشد.
    """
    if not update.message or not update.message.text:
        return

    # اگر پیام شامل دستور مدیریتی یا تگ/فیلتر است
    text = update.message.text.strip().lower()

    # اول بررسی قفل‌ها و فیلترها
    await check_message_locks(update, context)

    # بعد بررسی دستورات اصلی گروه
    await group_command_handler(update, context)
