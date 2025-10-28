# ======================= 🔒 سیستم قفل‌های گروه (نسخه حرفه‌ای با alias) =======================

import os, json
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

# 📂 مسیر فایل داده‌ها
GROUP_CTRL_FILE = "group_control.json"

# 👑 سودوها (لیست افراد ارشد)
SUDO_IDS = [7089376754, 1777319036]

# ======================= 📦 توابع ذخیره و لود داده‌ها =======================

def load_json_file(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ خطا در لود {path}: {e}")
    return default


def save_json_file(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ خطا در ذخیره {path}: {e}")


group_data = load_json_file(GROUP_CTRL_FILE, {})

# ======================= 👑 بررسی سطح دسترسی =======================

async def is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return False

    # سودو همیشه مجاز
    if user.id in SUDO_IDS:
        return True

    chat_id = chat.id
    try:
        member = await context.bot.get_chat_member(chat_id, user.id)
        return member.status in ["administrator", "creator"]
    except:
        return False


# ======================= 🧱 تعریف قفل‌ها =======================

LOCK_TYPES = {
    "links": "ارسال لینک",
    "photos": "ارسال عکس",
    "videos": "ارسال ویدیو",
    "files": "ارسال فایل",
    "voices": "ارسال ویس",
    "vmsgs": "ارسال ویدیو مسیج",
    "stickers": "ارسال استیکر",
    "gifs": "ارسال گیف",
    "media": "ارسال رسانه‌ها",
    "forward": "ارسال فوروارد",
    "ads": "ارسال تبلیغ",
    "usernames": "ارسال یوزرنیم / تگ",
    "bots": "افزودن ربات",
    "join": "ورود اعضای جدید",
    "tgservices": "پیام‌های سیستمی تلگرام",
    "arabic": "نوشتن حروف عربی",
    "english": "نوشتن حروف انگلیسی",
    "text": "ارسال پیام متنی",
    "audio": "ارسال آهنگ / موزیک",
    "emoji": "ارسال ایموجی",
    "mention": "تگ کردن کاربران",
    "all": "قفل کلی (سکوت همه)",
    "joinmsg": "پیام ورود",
    "caption": "کپشن زیر مدیا",
    "edit": "ویرایش پیام‌ها",
    "reply": "پاسخ به پیام‌ها"
}

# ======================= ⚙️ ذخیره وضعیت قفل =======================

def set_lock(chat_id, lock_name, status):
    chat_id = str(chat_id)
    group = group_data.get(chat_id, {"locks": {}})
    locks = group.get("locks", {})
    locks[lock_name] = status
    group["locks"] = locks
    group_data[chat_id] = group
    save_json_file(GROUP_CTRL_FILE, group_data)

def get_lock(chat_id, lock_name):
    chat_id = str(chat_id)
    group = group_data.get(chat_id, {"locks": {}})
    locks = group.get("locks", {})
    return locks.get(lock_name, False)

# ======================= 🔒 فعال‌سازی قفل =======================

async def handle_lock(update, context, lock_name):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند قفل کنند!")

    chat_id = str(update.effective_chat.id)
    user = update.effective_user

    if get_lock(chat_id, lock_name):
        return await update.message.reply_text(f"⚠️ قفل <b>{LOCK_TYPES[lock_name]}</b> از قبل فعال است.", parse_mode="HTML")

    set_lock(chat_id, lock_name, True)
    time_str = datetime.now().strftime("%H:%M - %d/%m/%Y")

    await update.message.reply_text(
        f"🔒 <b>{LOCK_TYPES[lock_name]}</b> فعال شد.\n\n"
        f"👤 مدیر: <b>{user.first_name}</b>\n"
        f"🕒 {time_str}",
        parse_mode="HTML"
    )


# ======================= 🔓 بازکردن قفل =======================

async def handle_unlock(update, context, lock_name):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند باز کنند!")

    chat_id = str(update.effective_chat.id)
    user = update.effective_user

    if not get_lock(chat_id, lock_name):
        return await update.message.reply_text(f"⚠️ قفل <b>{LOCK_TYPES[lock_name]}</b> از قبل باز است.", parse_mode="HTML")

    set_lock(chat_id, lock_name, False)
    time_str = datetime.now().strftime("%H:%M - %d/%m/%Y")

    await update.message.reply_text(
        f"🔓 <b>{LOCK_TYPES[lock_name]}</b> باز شد.\n\n"
        f"👤 مدیر: <b>{user.first_name}</b>\n"
        f"🕒 {time_str}",
        parse_mode="HTML"
    )

# ======================= 🧾 نمایش وضعیت قفل‌ها =======================

async def handle_locks_status(update, context):
    chat_id = str(update.effective_chat.id)
    locks = group_data.get(chat_id, {}).get("locks", {})

    if not locks:
        return await update.message.reply_text("🔓 هیچ قفلی فعال نیست.", parse_mode="HTML")

    text = "🧱 <b>وضعیت قفل‌های فعال در این گروه:</b>\n\n"
    for lock, desc in LOCK_TYPES.items():
        status = "🔒 فعال" if locks.get(lock, False) else "🔓 غیرفعال"
        text += f"▫️ <b>{desc}:</b> {status}\n"

    await update.message.reply_text(text, parse_mode="HTML")

# ======================= 🧩 اتصال به alias =======================

async def handle_locks_with_alias(update, context):
    """شناسایی دستورات فارسی مثل 'قفل لینک' یا 'باز کردن لینک'"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip().lower()

    for lock, desc in LOCK_TYPES.items():
        if text in [f"قفل {lock}", f"قفل {desc}", f"فعال {desc}"]:
            return await handle_lock(update, context, lock)
        elif text in [f"باز {lock}", f"باز کردن {lock}", f"باز کردن {desc}", f"باز {desc}"]:
            return await handle_unlock(update, context, lock)

    # وضعیت قفل‌ها
    if text in ["وضعیت قفل", "قفل‌ها", "locks", "lock status"]:
        return await handle_locks_status(update, context)
        # ======================= 🔍 بررسی و حذف پیام‌ها بر اساس قفل‌ها =======================

from telegram.error import BadRequest

async def check_message_locks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بررسی تمام پیام‌ها و حذف موارد نقض قفل‌ها"""
    if not update.message:
        return

    chat = update.effective_chat
    user = update.effective_user
    chat_id = str(chat.id)
    message = update.message

    # ✅ اگر کاربر مدیر یا سودو است → نادیده بگیر
    if user and user.id in SUDO_IDS:
        return
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status in ["administrator", "creator"]:
            return
    except:
        pass

    # 🔒 بررسی قفل‌های فعال این گروه
    locks = group_data.get(chat_id, {}).get("locks", {})
    if not locks:
        return

    delete_reason = None
    text = (message.text or "").lower()

    # لینک
    if locks.get("links") and ("http" in text or "t.me/" in text or "telegram.me/" in text):
        delete_reason = "ارسال لینک"
    # عکس
    elif locks.get("photos") and message.photo:
        delete_reason = "ارسال عکس"
    # ویدیو
    elif locks.get("videos") and message.video:
        delete_reason = "ارسال ویدیو"
    # فایل
    elif locks.get("files") and message.document:
        delete_reason = "ارسال فایل"
    # ویس
    elif locks.get("voices") and message.voice:
        delete_reason = "ارسال ویس"
    # ویدیو مسیج
    elif locks.get("vmsgs") and message.video_note:
        delete_reason = "ارسال ویدیو مسیج"
    # استیکر
    elif locks.get("stickers") and message.sticker:
        delete_reason = "ارسال استیکر"
    # گیف
    elif locks.get("gifs") and message.animation:
        delete_reason = "ارسال گیف"
    # رسانه‌ها
    elif locks.get("media") and (message.photo or message.video or message.animation or message.document):
        delete_reason = "ارسال رسانه (مدیا)"
    # فوروارد
    elif locks.get("forward") and message.forward_from:
        delete_reason = "ارسال پیام فورواردی"
    # تبلیغات / تبچی
    elif locks.get("ads") and any(word in text for word in ["join", "channel", "تبچی", "ربات تبلیغ"]):
        delete_reason = "ارسال تبلیغ"
    # یوزرنیم / تگ
    elif locks.get("usernames") and "@" in text:
        delete_reason = "ارسال یوزرنیم / تگ"
    # پیام متنی
    elif locks.get("text") and message.text:
        delete_reason = "ارسال پیام متنی"
    # عربی
    elif locks.get("arabic") and any("\u0600" <= ch <= "\u06FF" for ch in text):
        delete_reason = "استفاده از حروف عربی"
    # انگلیسی
    elif locks.get("english") and any("a" <= ch <= "z" for ch in text):
        delete_reason = "استفاده از حروف انگلیسی"
    # ایموجی
    elif locks.get("emoji") and any(ord(ch) > 10000 for ch in text):
        delete_reason = "ارسال ایموجی"
    # منشن
    elif locks.get("mention") and "@" in text:
        delete_reason = "منشن دیگران"
    # آهنگ / صوت
    elif locks.get("audio") and message.audio:
        delete_reason = "ارسال آهنگ / فایل صوتی"
    # ویرایش پیام
    elif locks.get("edit") and message.edit_date:
        delete_reason = "ویرایش پیام"
    # ریپلای
    elif locks.get("reply") and message.reply_to_message:
        delete_reason = "پاسخ به پیام"
    # قفل کلی
    elif locks.get("all"):
        delete_reason = "قفل کلی گروه"

    # 🗑 اگر تخلفی یافت شد → حذف و هشدار
    if delete_reason:
        try:
            await message.delete()
            await context.bot.send_message(
                chat.id,
                f"🚫 پیام <b>{user.first_name}</b> حذف شد.\n🎯 دلیل: <b>{delete_reason}</b>",
                parse_mode="HTML"
            )
        except BadRequest:
            pass
           # ======================= 👑 مدیریت مدیران گروه =======================

async def handle_addadmin(update, context):
    """➕ افزودن مدیر جدید"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند مدیر اضافه کنند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید روی پیام فردی ریپلای بزنی تا مدیرش کنم.")

    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)

    # داده‌های گروه
    group = group_data.get(chat_id, {})
    admins = group.get("admins", [])

    if str(target.id) in admins:
        return await update.message.reply_text("⚠️ این کاربر قبلاً مدیر بوده.")

    admins.append(str(target.id))
    group["admins"] = admins
    group_data[chat_id] = group
    save_json_file(GROUP_CTRL_FILE, group_data)

    await update.message.reply_text(
        f"👑 <b>{target.first_name}</b> به لیست مدیران افزوده شد ✅",
        parse_mode="HTML"
    )


async def handle_removeadmin(update, context):
    """❌ حذف مدیر از لیست"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید روی پیام مدیر ریپلای بزنی تا حذف بشه.")

    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)

    group = group_data.get(chat_id, {})
    admins = group.get("admins", [])

    if str(target.id) not in admins:
        return await update.message.reply_text("⚠️ این کاربر در لیست مدیران نیست.")

    admins.remove(str(target.id))
    group["admins"] = admins
    group_data[chat_id] = group
    save_json_file(GROUP_CTRL_FILE, group_data)

    await update.message.reply_text(
        f"❌ <b>{target.first_name}</b> از لیست مدیران حذف شد.",
        parse_mode="HTML"
    )


async def handle_admins(update, context):
    """📋 نمایش لیست مدیران گروه"""
    chat_id = str(update.effective_chat.id)
    group = group_data.get(chat_id, {})
    admins = group.get("admins", [])

    if not admins:
        return await update.message.reply_text("ℹ️ هنوز هیچ مدیری ثبت نشده است.", parse_mode="HTML")

    text = "👑 <b>لیست مدیران گروه:</b>\n\n"
    for i, admin_id in enumerate(admins, 1):
        text += f"{i}. <a href='tg://user?id={admin_id}'>مدیر {i}</a>\n"

    await update.message.reply_text(text, parse_mode="HTML")


async def handle_clearadmins(update, context):
    """🧹 پاکسازی کامل لیست مدیران (فقط سودو)"""
    user = update.effective_user
    if user.id not in SUDO_IDS:
        return await update.message.reply_text("🚫 فقط سودوها می‌توانند لیست مدیران را پاکسازی کنند!")

    chat_id = str(update.effective_chat.id)
    if chat_id not in group_data or "admins" not in group_data[chat_id]:
        return await update.message.reply_text("⚠️ این گروه هیچ مدیری ثبت نکرده است!")

    group_data[chat_id]["admins"] = []
    save_json_file(GROUP_CTRL_FILE, group_data)

    await update.message.reply_text("🧹 تمام مدیران گروه حذف شدند ✅", parse_mode="HTML")
# ======================= 🧹 سیستم پاکسازی هوشمند (Clean System Pro) =======================
import asyncio
from datetime import datetime
from telegram.error import BadRequest, RetryAfter

async def handle_clean(update, context):
    """🧹 پاکسازی هوشمند بر اساس ریپلای، عدد، یا دستور کامل"""

    user = update.effective_user
    chat = update.effective_chat
    message = update.message
    args = context.args if context.args else []

    # بررسی مجوز
    if not await is_authorized(update, context):
        return await message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند از دستور پاکسازی استفاده کنند!")

    # 🔍 حالت‌های مختلف
    limit = 100  # پیش‌فرض
    mode = "range"
    target_id = None

    # 1️⃣ ریپلای → پاکسازی پیام‌های کاربر خاص
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        mode = "user"

    # 2️⃣ عدد → پاکسازی تعدادی از پیام‌ها
    elif args and args[0].isdigit():
        limit = min(int(args[0]), 1000)
        mode = "count"

    # 3️⃣ دستور "کامل" یا "همه"
    elif any(word in " ".join(args) for word in ["all", "همه", "کامل", "full"]):
        limit = 1000
        mode = "full"

    # 4️⃣ بدون عدد → پاکسازی عادی
    else:
        limit = 100

    deleted = 0
    last_id = message.message_id
    batch = []

    async def safe_delete(msg_id):
        try:
            await context.bot.delete_message(chat.id, msg_id)
            return 1
        except (BadRequest, RetryAfter):
            return 0
        except:
            return 0

    # 🚀 عملیات پاکسازی
    for _ in range(limit):
        last_id -= 1
        if last_id <= 0:
            break

        try:
            msg = await context.bot.forward_message(chat.id, chat.id, last_id)
            sender_id = msg.forward_from.id if msg.forward_from else None
            await context.bot.delete_message(chat.id, msg.message_id)

            if mode == "user" and sender_id != target_id:
                continue

            batch.append(asyncio.create_task(safe_delete(last_id)))
            if len(batch) >= 50:
                results = await asyncio.gather(*batch)
                deleted += sum(results)
                batch = []
                await asyncio.sleep(0.4)

        except Exception:
            continue

    if batch:
        results = await asyncio.gather(*batch)
        deleted += sum(results)

    # حذف دستور اصلی
    try:
        await context.bot.delete_message(chat.id, message.message_id)
    except:
        pass

    # ✉️ گزارش نهایی (در پیام خصوصی مدیر یا همانجا)
    mode_label = {
        "user": "پاکسازی پیام‌های کاربر خاص",
        "count": f"پاکسازی عددی ({limit} پیام)",
        "full": "پاکسازی کامل گروه",
        "range": "پاکسازی عمومی"
    }[mode]

    report = (
        f"🧹 <b>گزارش پاکسازی</b>\n\n"
        f"🏷 <b>حالت:</b> {mode_label}\n"
        f"👤 <b>توسط:</b> {user.first_name}\n"
        f"🗑 <b>تعداد حذف‌شده:</b> {deleted}\n"
        f"🕒 {datetime.now().strftime('%H:%M:%S - %Y/%m/%d')}"
    )

    # سعی کن گزارش رو در چت خصوصی بفرستی
    try:
        await context.bot.send_message(user.id, report, parse_mode="HTML")
    except:
        await message.reply_text(report, parse_mode="HTML")
        # ======================= 📌 سیستم پین (Pin System Pro - فارسی و زمانی) =======================
import asyncio
from datetime import datetime, timedelta

async def handle_pin(update, context):
    """📌 پین کردن پیام (عادی یا زمانی)"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند پیام پین کنند!")

    message = update.message
    chat = update.effective_chat

    if not message.reply_to_message:
        return await message.reply_text("🔹 باید روی پیام مورد نظر ریپلای بزنی تا پین بشه.")

    # بررسی اگر عدد داده شده (مثلاً پن 10)
    text = message.text.strip().lower()
    duration = None
    for word in text.split():
        if word.isdigit():
            duration = int(word)
            break

    # پین کردن پیام
    try:
        await context.bot.pin_chat_message(chat.id, message.reply_to_message.message_id)
        time_str = datetime.now().strftime("%H:%M - %d/%m/%Y")

        if duration:
            await message.reply_text(
                f"📌 پیام پین شد و بعد از <b>{duration} دقیقه</b> به‌صورت خودکار برداشته می‌شود.\n"
                f"🕒 <b>توسط:</b> {update.effective_user.first_name}\n"
                f"📅 <b>زمان:</b> {time_str}",
                parse_mode="HTML"
            )

            # بعد از زمان مشخص، آن‌پین خودکار
            await asyncio.sleep(duration * 60)
            try:
                await context.bot.unpin_chat_message(chat.id, message.reply_to_message.message_id)
                await context.bot.send_message(
                    chat.id,
                    f"⌛ پین خودکار حذف شد (مدت {duration} دقیقه به پایان رسید).",
                    parse_mode="HTML"
                )
            except:
                pass

        else:
            await message.reply_text(
                f"📍 پیام با موفقیت پین شد.\n"
                f"🕒 <b>توسط:</b> {update.effective_user.first_name}\n"
                f"📅 {time_str}",
                parse_mode="HTML"
            )

    except Exception as e:
        await message.reply_text(f"⚠️ خطا در پین کردن پیام:\n<code>{e}</code>", parse_mode="HTML")


async def handle_unpin(update, context):
    """📍 حذف پین فعلی"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    chat = update.effective_chat
    try:
        await context.bot.unpin_all_chat_messages(chat.id)
        await update.message.reply_text("📍 تمام پین‌ها با موفقیت حذف شدند.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در حذف پین:\n<code>{e}</code>", parse_mode="HTML")
        # ======================= 🚫 سیستم فیلتر کلمات (Filter System Pro) =======================
import json, os

FILTER_FILE = "filters.json"

# 📂 لود و ذخیره‌سازی داده‌ها
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

# 👑 بررسی سطح دسترسی
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
        return await update.message.reply_text("📝 استفاده: افزودن فیلتر [کلمه]\nمثلاً: افزودن فیلتر تبلیغ")

    word = " ".join(context.args).strip().lower()
    chat_id = str(update.effective_chat.id)
    chat_filters = filters_data.get(chat_id, [])

    if word in chat_filters:
        return await update.message.reply_text("⚠️ این کلمه از قبل فیلتر شده است!")

    chat_filters.append(word)
    filters_data[chat_id] = chat_filters
    save_filters(filters_data)

    await update.message.reply_text(f"✅ کلمه <b>{word}</b> به لیست فیلتر اضافه شد.", parse_mode="HTML")


# ❌ حذف فیلتر
async def handle_delfilter(update, context):
    if not await can_manage(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if len(context.args) < 1:
        return await update.message.reply_text("📝 استفاده: حذف فیلتر [کلمه]\nمثلاً: حذف فیلتر تبلیغ")

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


# 🚫 بررسی پیام‌ها و حذف خودکار
async def check_filtered_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = str(update.effective_chat.id)
    user = update.effective_user
    text = update.message.text.lower()

    # مدیران و سودوها مستثنی هستند
    if user.id in SUDO_IDS:
        return
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, user.id)
        if member.status in ["administrator", "creator"]:
            return
    except:
        pass

    chat_filters = filters_data.get(chat_id, [])
    for word in chat_filters:
        if word in text:
            try:
                await update.message.delete()
                await update.message.chat.send_message(
                    f"🚫 پیام <b>{user.first_name}</b> حذف شد!\n🎯 شامل کلمه فیلترشده: <b>{word}</b>",
                    parse_mode="HTML"
                )
            except:
                pass
            return
            # ======================= 🧩 سیستم تگ کاربران (Tag System Pro) =======================
import json, os, asyncio
from datetime import datetime, timedelta

ORIGINS_FILE = "origins.json"

# 📂 بارگذاری و ذخیره فایل فعالیت کاربران
def load_origins():
    if os.path.exists(ORIGINS_FILE):
        try:
            with open(ORIGINS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_origins(data):
    with open(ORIGINS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

origins_data = load_origins()

# ======================= 🕒 ثبت فعالیت کاربران =======================
async def auto_clean_old_origins(update, context):
    """هر بار که کسی پیام می‌فرسته، زمان فعالیتش ثبت بشه"""
    if not update.message or not update.effective_user:
        return

    chat_id = str(update.effective_chat.id)
    user_id = str(update.effective_user.id)

    chat_data = origins_data.get(chat_id, {"users": {}})
    users = chat_data.get("users", {})
    users[user_id] = datetime.now().isoformat()
    chat_data["users"] = users
    origins_data[chat_id] = chat_data
    save_origins(origins_data)

# ======================= 🔖 تابع اصلی تگ‌ها =======================

async def handle_tag(update, context):
    """مدیریت تمام حالت‌های تگ"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    text = update.message.text.lower().strip()
    chat = update.effective_chat
    chat_id = str(chat.id)
    now = datetime.now()

    # 📅 دریافت داده‌ها
    chat_data = origins_data.get(chat_id, {"users": {}})
    users = chat_data.get("users", {})

    # هیچ کاربر ثبت نشده
    if not users:
        return await update.message.reply_text("⚠️ هنوز هیچ فعالیتی ثبت نشده است!")

    target_users = []
    title = "کاربران"

    # ======================= حالت‌های مختلف =======================
    if "همه" in text:
        target_users = list(users.keys())
        title = "همه کاربران"

    elif "فعال" in text:
        active_threshold = now - timedelta(days=3)
        target_users = [
            uid for uid, t in users.items()
            if datetime.fromisoformat(t) >= active_threshold
        ]
        title = "کاربران فعال (۳ روز اخیر)"

    elif "غیرفعال" in text:
        inactive_threshold = now - timedelta(days=3)
        target_users = [
            uid for uid, t in users.items()
            if datetime.fromisoformat(t) < inactive_threshold
        ]
        title = "کاربران غیرفعال (بیش از ۳ روز بی‌فعالیت)"

    elif "مدیر" in text:
        try:
            admins = await context.bot.get_chat_administrators(chat.id)
            target_users = [str(a.user.id) for a in admins]
            title = "مدیران گروه"
        except:
            return await update.message.reply_text("⚠️ خطا در دریافت لیست مدیران")

    elif "@" in text or any(ch.isdigit() for ch in text.split()):
        # مثل "تگ @username" یا "تگ 7548154581"
        target = text.replace("تگ", "").strip()
        target_users = [target.replace("@", "")]
        title = f"تگ کاربر خاص ({target})"

    else:
        return await update.message.reply_text(
            "📌 دستور نامعتبر است!\n"
            "نمونه دستورات:\n"
            "▫️ تگ همه\n"
            "▫️ تگ فعال\n"
            "▫️ تگ غیرفعال\n"
            "▫️ تگ مدیران\n"
            "▫️ تگ @username",
            parse_mode="HTML"
        )

    # ======================= ارسال تگ‌ها =======================
    if not target_users:
        return await update.message.reply_text("⚠️ کاربری برای تگ یافت نشد!")

    batch_size = 5
    mentions = []
    sent = 0

    await update.message.reply_text(f"📢 شروع {title} ...", parse_mode="HTML")

    for i, uid in enumerate(target_users, 1):
        mentions.append(f"<a href='tg://user?id={uid}'>🟢</a>")
        if len(mentions) >= batch_size or i == len(target_users):
            try:
                await context.bot.send_message(
                    chat.id,
                    f"{' '.join(mentions)}",
                    parse_mode="HTML"
                )
                sent += len(mentions)
                mentions = []
                await asyncio.sleep(1)
            except:
                pass

    await update.message.reply_text(
        f"✅ {sent} کاربر {title} تگ شدند.",
        parse_mode="HTML"
    )
    # ======================= 💎 سیستم اصل پیشرفته (Origin System Pro) =======================
import json, os, asyncio
from telegram import Update
from telegram.ext import ContextTypes

ORIGIN_FILE = "origins.json"

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

# 👑 بررسی مجاز بودن
async def can_manage_origin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if user.id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ["administrator", "creator"]
    except:
        return False


# ➕ ثبت اصل
async def handle_set_origin(update, context):
    message = update.message
    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    raw_text = message.text.strip()

    # فقط مدیران یا خود کاربر مجازند
    if not (await can_manage_origin(update, context) or message.reply_to_message):
        return await message.reply_text("🚫 فقط مدیران یا خود کاربران مجاز به ثبت اصل هستند!")

    # استخراج متن اصل
    origin_text = ""
    for phrase in ["ثبت اصل", "setorigin", "set origin"]:
        if raw_text.lower().startswith(phrase):
            origin_text = raw_text[len(phrase):].strip()
            break

    # اگر با ریپلای بود ولی متنی وارد نشده بود → از پیام ریپلای‌شده استفاده کن
    if not origin_text and message.reply_to_message:
        origin_text = message.reply_to_message.text or ""

    if not origin_text:
        msg = await message.reply_text("⚠️ لطفاً متن اصل را بنویس یا روی پیام شخصی ریپلای کن.")
        await asyncio.sleep(6)
        await msg.delete()
        return

    target = message.reply_to_message.from_user if message.reply_to_message else user
    if chat_id not in origins:
        origins[chat_id] = {}

    origins[chat_id][str(target.id)] = origin_text
    save_origins(origins)

    text = (
        f"✅ <b>اصل برای {target.first_name}</b> ثبت شد.\n"
        f"🧿 <b>{origin_text}</b>"
    )
    sent = await message.reply_text(text, parse_mode="HTML")
    await asyncio.sleep(10)
    try:
        await sent.delete()
        await message.delete()
    except:
        pass


# 🔍 نمایش اصل
async def handle_show_origin(update, context):
    message = update.message
    text = message.text.lower().strip()
    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    target = None

    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif "من" in text:
        target = user
    elif "@" in text:
        return await message.reply_text("⚠️ فعلاً فقط با ریپلای یا 'اصل من' قابل نمایش است.")

    if not target:
        return await message.reply_text("📘 برای دیدن اصل، بنویس:\n▪️ اصل من\nیا روی پیام کسی ریپلای کن و بنویس «اصل»")

    group_data = origins.get(chat_id, {})
    origin_text = group_data.get(str(target.id))

    if not origin_text:
        return await message.reply_text("ℹ️ هنوز اصلی برای این کاربر ثبت نشده است.")

    await message.reply_text(
        f"🌿 <b>اصل {target.first_name}:</b>\n{origin_text}",
        parse_mode="HTML"
    )


# 🗑️ حذف اصل
async def handle_del_origin(update, context):
    if not await can_manage_origin(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    chat_id = str(update.effective_chat.id)
    message = update.message
    user = update.effective_user

    target = message.reply_to_message.from_user if message.reply_to_message else user
    if chat_id not in origins or str(target.id) not in origins[chat_id]:
        return await message.reply_text("⚠️ هیچ اصلی برای این کاربر ثبت نشده!")

    del origins[chat_id][str(target.id)]
    save_origins(origins)
    await message.reply_text(f"🗑️ اصل {target.first_name} حذف شد.")


# 📋 لیست تمام اصل‌ها
async def handle_list_origins(update, context):
    chat_id = str(update.effective_chat.id)
    data = origins.get(chat_id, {})
    if not data:
        return await update.message.reply_text("ℹ️ هنوز هیچ اصلی ثبت نشده است.")

    text = "💎 <b>لیست اصل‌های ثبت‌شده در گروه:</b>\n\n"
    for uid, origin in data.items():
        text += f"👤 <a href='tg://user?id={uid}'>کاربر</a>:\n🧿 {origin}\n\n"
    await update.message.reply_text(text, parse_mode="HTML")
    # ======================= 🔒 سیستم قفل گروه پیشرفته (Smart Group Lock Pro) =======================
import asyncio
from datetime import datetime, time

# 🔐 قفل دستی گروه
async def handle_lockgroup(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند گروه را قفل کنند!")

    chat = update.effective_chat
    try:
        await context.bot.set_chat_permissions(chat.id, ChatPermissions(can_send_messages=False))
        time_str = datetime.now().strftime("%H:%M - %d/%m/%Y")
        await update.message.reply_text(
            f"🔒 <b>گروه قفل شد!</b>\n\n"
            f"📅 <b>زمان:</b> {time_str}\n"
            f"👑 <b>توسط:</b> {update.effective_user.first_name}",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در قفل‌کردن گروه:\n<code>{e}</code>", parse_mode="HTML")


# 🔓 بازکردن دستی گروه
async def handle_unlockgroup(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند گروه را باز کنند!")

    chat = update.effective_chat
    try:
        await context.bot.set_chat_permissions(chat.id, ChatPermissions(can_send_messages=True))
        time_str = datetime.now().strftime("%H:%M - %d/%m/%Y")
        await update.message.reply_text(
            f"🔓 <b>گروه باز شد!</b>\n\n"
            f"📅 <b>زمان:</b> {time_str}\n"
            f"👑 <b>توسط:</b> {update.effective_user.first_name}",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بازکردن گروه:\n<code>{e}</code>", parse_mode="HTML")


# ======================= ⏰ تنظیم قفل خودکار =======================
async def handle_auto_lockgroup(update, context):
    """تنظیم قفل خودکار گروه در بازه‌ی زمانی خاص"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند قفل خودکار تنظیم کنند!")

    chat_id = str(update.effective_chat.id)
    args = context.args

    if len(args) != 2:
        return await update.message.reply_text(
            "🕒 استفاده درست:\n<code>قفل خودکار گروه 23:00 07:00</code>\n\n"
            "🔹 مثال: قفل از ۲۳ تا ۷ صبح هر روز",
            parse_mode="HTML"
        )

    start, end = args
    if chat_id not in group_data:
        group_data[chat_id] = {}

    group_data[chat_id]["auto_lock"] = {"enabled": True, "start": start, "end": end}
    save_json_file(GROUP_CTRL_FILE, group_data)

    await update.message.reply_text(
        f"✅ <b>قفل خودکار گروه فعال شد!</b>\n\n"
        f"🕐 <b>ساعت قفل:</b> {start}\n"
        f"🕔 <b>ساعت باز:</b> {end}\n"
        f"🔁 <b>تکرار:</b> هر روز\n\n"
        f"👑 تنظیم توسط: <b>{update.effective_user.first_name}</b>",
        parse_mode="HTML"
    )


# 📴 غیرفعال‌سازی قفل خودکار
async def handle_disable_auto_lock(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    chat_id = str(update.effective_chat.id)
    group = group_data.get(chat_id, {})
    if "auto_lock" not in group or not group["auto_lock"].get("enabled", False):
        return await update.message.reply_text("ℹ️ قفل خودکار در این گروه فعال نیست.")

    group["auto_lock"]["enabled"] = False
    save_json_file(GROUP_CTRL_FILE, group_data)
    await update.message.reply_text("❌ قفل خودکار گروه غیرفعال شد.")


# ======================= ⏱ بررسی زمان‌بندی و اجرای خودکار =======================
async def auto_group_lock_scheduler(context):
    """اجرای زمان‌بندی قفل/باز گروه‌ها (هر دقیقه)"""
    now = datetime.now().time()
    for chat_id, data in group_data.items():
        auto = data.get("auto_lock", {})
        if not auto.get("enabled"):
            continue

        start_str = auto.get("start")
        end_str = auto.get("end")

        try:
            start = datetime.strptime(start_str, "%H:%M").time()
            end = datetime.strptime(end_str, "%H:%M").time()
        except:
            continue

        try:
            # حالت شب تا صبح (مثلاً 23 تا 07)
            if start > end:
                in_lock = now >= start or now <= end
            else:
                in_lock = start <= now <= end

            chat_id_int = int(chat_id)
            if in_lock:
                await context.bot.set_chat_permissions(chat_id_int, ChatPermissions(can_send_messages=False))
            else:
                await context.bot.set_chat_permissions(chat_id_int, ChatPermissions(can_send_messages=True))
        except Exception as e:
            print(f"⚠️ خطا در زمان‌بندی قفل گروه {chat_id}: {e}")
            # ======================= 👑 سیستم لقب پیشرفته (Nickname System Pro) =======================
import json, os, asyncio
from telegram import Update
from telegram.ext import ContextTypes

NICK_FILE = "nicknames.json"

# 📂 بارگذاری و ذخیره‌سازی
def load_nicks():
    if os.path.exists(NICK_FILE):
        try:
            with open(NICK_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_nicks(data):
    with open(NICK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

nicknames = load_nicks()

# 👑 بررسی مجاز بودن برای تنظیم لقب دیگران
async def can_manage_nick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if user.id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ["administrator", "creator"]
    except:
        return False


# ➕ ثبت لقب
async def handle_set_nick(update, context):
    message = update.message
    chat_id = str(update.effective_chat.id)
    user = update.effective_user
    text = message.text.strip()
    args = text.split(" ", 1)

    # استخراج لقب از متن
    nick_text = ""
    for phrase in ["ثبت لقب", "set nick", "setnickname", "setnick"]:
        if text.lower().startswith(phrase):
            nick_text = text[len(phrase):].strip()
            break

    if not nick_text and len(args) > 1:
        nick_text = args[1]

    # اگر ریپلای شده → مدیر می‌تواند برای دیگران لقب بگذارد
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        if not await can_manage_nick(update, context):
            return await message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند برای دیگران لقب تعیین کنند!")
    else:
        target = user

    if not nick_text:
        return await message.reply_text("📝 لطفاً لقب مورد نظر را بنویس.\nمثلاً: <code>ثبت لقب فرمانده</code>", parse_mode="HTML")

    # ذخیره در فایل
    if chat_id not in nicknames:
        nicknames[chat_id] = {}
    nicknames[chat_id][str(target.id)] = nick_text
    save_nicks(nicknames)

    await message.reply_text(
        f"✅ لقب جدید برای <b>{target.first_name}</b> ثبت شد:\n"
        f"👑 <b>{nick_text}</b>",
        parse_mode="HTML"
    )


# 🔍 نمایش لقب
async def handle_show_nick(update, context):
    message = update.message
    chat_id = str(update.effective_chat.id)
    text = message.text.strip().lower()
    user = update.effective_user
    target = None

    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif "من" in text:
        target = user
    else:
        return await message.reply_text("📘 برای دیدن لقب، بنویس:\n▪️ لقب من\nیا روی پیام کسی ریپلای کن و بنویس «لقب»")

    group_nicks = nicknames.get(chat_id, {})
    nick = group_nicks.get(str(target.id))

    if not nick:
        return await message.reply_text("ℹ️ هیچ لقبی برای این کاربر ثبت نشده است.")

    await message.reply_text(f"👑 <b>لقب {target.first_name}:</b>\n{nick}", parse_mode="HTML")


# ❌ حذف لقب
async def handle_del_nick(update, context):
    message = update.message
    chat_id = str(update.effective_chat.id)

    target = message.reply_to_message.from_user if message.reply_to_message else update.effective_user
    if message.reply_to_message and not await can_manage_nick(update, context):
        return await message.reply_text("🚫 فقط مدیران یا سودوها مجازند لقب دیگران را حذف کنند!")

    if chat_id not in nicknames or str(target.id) not in nicknames[chat_id]:
        return await message.reply_text("⚠️ هیچ لقبی برای این کاربر ثبت نشده است.")

    del nicknames[chat_id][str(target.id)]
    save_nicks(nicknames)
    await message.reply_text(f"🗑️ لقب <b>{target.first_name}</b> حذف شد.", parse_mode="HTML")


# 📋 لیست همه لقب‌ها
async def handle_list_nicks(update, context):
    chat_id = str(update.effective_chat.id)
    group_nicks = nicknames.get(chat_id, {})
    if not group_nicks:
        return await update.message.reply_text("ℹ️ هنوز هیچ لقبی ثبت نشده است.")

    text = "👑 <b>لیست لقب‌های گروه:</b>\n\n"
    for uid, nick in group_nicks.items():
        text += f"👤 <a href='tg://user?id={uid}'>کاربر</a> → {nick}\n"
    await update.message.reply_text(text, parse_mode="HTML")
    # ======================= ⚙️ سیستم Alias + Command Handler مرکزی =======================
import json, os
from telegram import Update
from telegram.ext import ContextTypes

ALIASES_FILE = "aliases.json"

# 📂 بارگذاری aliasها
def load_aliases():
    if os.path.exists(ALIASES_FILE):
        try:
            with open(ALIASES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_aliases(data):
    with open(ALIASES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

ALIASES = load_aliases()

# 🧠 alias پیش‌فرض (درصورت نبود فایل)
DEFAULT_ALIASES = {
    # مدیریت گروه
    "lockgroup": ["قفل گروه", "ببند گروه", "lock group"],
    "unlockgroup": ["بازکردن گروه", "باز گروه", "unlock group"],
    "autolockgroup": ["قفل خودکار گروه", "تنظیم قفل خودکار", "auto lock group"],
    "disableautolock": ["لغو قفل خودکار", "غیرفعال کردن قفل خودکار"],
    
    # فیلترها
    "addfilter": ["افزودن فیلتر", "فیلترکن", "addfilter"],
    "delfilter": ["حذف فیلتر", "پاک فیلتر", "delfilter"],
    "filters": ["لیست فیلترها", "فیلترها", "filters"],

    # تگ‌ها
    "tagall": ["تگ همه", "منشن همگانی", "tagall"],
    "tagactive": ["تگ فعال", "tagactive"],
    "taginactive": ["تگ غیرفعال", "taginactive"],
    "tagadmins": ["تگ مدیران", "tagadmins"],

    # لقب‌ها
    "setnick": ["ثبت لقب", "set nick", "setnickname", "setnick"],
    "shownick": ["لقب", "لقب من", "mynick"],
    "delnick": ["حذف لقب", "پاک لقب", "delnick"],
    "listnicks": ["لیست لقب‌ها", "نمایش لقب‌ها", "nicknames"],

    # اصل‌ها
    "setorigin": ["ثبت اصل", "set origin", "setorigin"],
    "showorigin": ["اصل", "اصل من", "origin"],
    "delorigin": ["حذف اصل", "پاک اصل", "delorigin"],
    "listorigins": ["لیست اصل‌ها", "origins"],

    # پین‌ها
    "pin": ["پن", "پین", "سنجاق", "pin"],
    "unpin": ["حذف پن", "بردار پین", "unpin"],

    # پاکسازی
    "clean": ["پاکسازی", "پاک کن", "پاک", "clear", "delete", "clean"]
}

# اگر فایل خالی بود، مقدار پیش‌فرض ذخیره شود
if not ALIASES:
    ALIASES = DEFAULT_ALIASES
    save_aliases(ALIASES)

# ======================= 🎯 مرکز تشخیص و اجرا =======================
async def group_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت دستورات فارسی و اجرای تابع مناسب"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip().lower()

    # بررسی alias‌ها و اجرای تابع مربوطه
    for cmd, aliases in ALIASES.items():
        for alias in aliases:
            if text.startswith(alias):
                context.args = text.replace(alias, "", 1).strip().split()
                return await execute_command(cmd, update, context)
    return


# ======================= ⚡️ نگاشت دستور به تابع =======================
async def execute_command(cmd, update, context):
    """اجرای تابع مرتبط با دستور"""
    try:
        mapping = {
            # گروه و قفل‌ها
            "lockgroup": handle_lockgroup,
            "unlockgroup": handle_unlockgroup,
            "autolockgroup": handle_auto_lockgroup,
            "disableautolock": handle_disable_auto_lock,

            # فیلترها
            "addfilter": handle_addfilter,
            "delfilter": handle_delfilter,
            "filters": handle_filters,

            # تگ‌ها
            "tagall": handle_tag,
            "tagactive": handle_tag,
            "taginactive": handle_tag,
            "tagadmins": handle_tag,

            # لقب‌ها
            "setnick": handle_set_nick,
            "shownick": handle_show_nick,
            "delnick": handle_del_nick,
            "listnicks": handle_list_nicks,

            # اصل‌ها
            "setorigin": handle_set_origin,
            "showorigin": handle_show_origin,
            "delorigin": handle_del_origin,
            "listorigins": handle_list_origins,

            # پین‌ها
            "pin": handle_pin,
            "unpin": handle_unpin,

            # پاکسازی
            "clean": handle_clean,
        }

        if cmd in mapping:
            await mapping[cmd](update, context)
        else:
            await update.message.reply_text("⚠️ دستور ناشناخته است.", parse_mode="HTML")

    except Exception as e:
        try:
            await update.message.reply_text(f"⚠️ خطا:\n<code>{e}</code>", parse_mode="HTML")
        except:
            pass
