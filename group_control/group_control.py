    # ==========================================================
# 🧱 GROUP CONTROL SYSTEM — STEP 1 (NEW & CLEAN)
# نسخه بازنویسی‌شده و بهینه‌شده قفل‌ها بدون هیچ تداخل با سایر Stepها
# ==========================================================

import os, json, asyncio, re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ContextTypes
from telegram.error import BadRequest

# ─────────────────────────────── مسیر فایل ───────────────────────────────
LOCK_FILE = "group_locks.json"
if not os.path.exists(LOCK_FILE):
    with open(LOCK_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

# ─────────────────────────────── سودوها ───────────────────────────────
SUDO_IDS = [8588347189]  # 👈 آیدی خودت رو اینجا بذار

# ─────────────────────────────── تعریف قفل‌ها ───────────────────────────────
LOCK_TYPES = {
    "group": "گروه",
    "links": "ارسال لینک",
    "photos": "ارسال عکس",
    "videos": "ارسال ویدیو",
    "files": "ارسال فایل",
    "voices": "ارسال ویس",
    "vmsgs": "ویدیو مسیج",
    "stickers": "استیکر",
    "gifs": "گیف",
    "media": "رسانه‌ها",
    "forward": "فوروارد",
    "ads": "تبچی / تبلیغ",
    "usernames": "یوزرنیم / تگ",
    "mention": "منشن با @",
    "bots": "افزودن ربات",
    "join": "ورود عضو جدید",
    "tgservices": "پیام سیستمی تلگرام",
    "joinmsg": "پیام خوش‌آمد",
    "arabic": "حروف عربی",
    "english": "حروف انگلیسی",
    "text": "پیام متنی",
    "audio": "آهنگ / موزیک",
    "emoji": "فقط ایموجی",
    "caption": "کپشن",
    "edit": "ویرایش پیام",
    "reply": "ریپلای / پاسخ",
}

# ─────────────────────────────── مدیریت فایل ───────────────────────────────
def _load_json(path, default=None):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ خطا در لود {path}: {e}")
    return default or {}

def _save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ خطا در ذخیره {path}: {e}")

# ─────────────────────────────── بارگذاری قفل‌ها ───────────────────────────────
LOCKS = _load_json(LOCK_FILE, {})

def _get_locks(chat_id: int):
    return LOCKS.get(str(chat_id), {})

def _set_lock(chat_id: int, key: str, status: bool):
    cid = str(chat_id)
    locks = LOCKS.get(cid, {})
    locks[key] = bool(status)
    LOCKS[cid] = locks
    _save_json(LOCK_FILE, LOCKS)

# ─────────────────────────────── بررسی مجوز مدیر یا سودو ───────────────────────────────
async def _is_admin_or_sudo(context, chat_id: int, user_id: int):
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except:
        return False

# ─────────────────────────────── فعال‌سازی قفل ───────────────────────────────
async def handle_lock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    chat = update.effective_chat
    user = update.effective_user

    if not await _is_admin_or_sudo(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
    if key not in LOCK_TYPES:
        return await update.message.reply_text("⚠️ نام قفل معتبر نیست.")

    locks = _get_locks(chat.id)
    if locks.get(key):
        return await update.message.reply_text(f"🔒 قفل <b>{LOCK_TYPES[key]}</b> از قبل فعال است.", parse_mode="HTML")

    _set_lock(chat.id, key, True)
    await update.message.reply_text(f"✅ قفل <b>{LOCK_TYPES[key]}</b> فعال شد.", parse_mode="HTML")

# ─────────────────────────────── غیرفعال‌سازی قفل ───────────────────────────────
async def handle_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    chat = update.effective_chat
    user = update.effective_user

    if not await _is_admin_or_sudo(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
    if key not in LOCK_TYPES:
        return await update.message.reply_text("⚠️ نام قفل معتبر نیست.")

    locks = _get_locks(chat.id)
    if not locks.get(key):
        return await update.message.reply_text(f"🔓 قفل <b>{LOCK_TYPES[key]}</b> از قبل باز است.", parse_mode="HTML")

    _set_lock(chat.id, key, False)
    await update.message.reply_text(f"🔓 قفل <b>{LOCK_TYPES[key]}</b> باز شد.", parse_mode="HTML")

# ─────────────────────────────── نمایش وضعیت قفل‌ها ───────────────────────────────
async def handle_locks_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    locks = _get_locks(chat.id)
    active = [LOCK_TYPES[k] for k, v in locks.items() if v]

    text = "<b>📋 وضعیت قفل‌های گروه</b>\n\n"
    if active:
        text += "🔒 قفل‌های فعال:\n" + "\n".join(f"• {x}" for x in active)
    else:
        text += "✅ هیچ قفلی فعال نیست."
    await update.message.reply_text(text, parse_mode="HTML")

# ─────────────────────────────── پنل دکمه‌ای قفل‌ها ───────────────────────────────
def _generate_lock_panel(chat_id: int):
    locks = _get_locks(chat_id)
    keyboard = []
    row = []
    for i, (key, title) in enumerate(LOCK_TYPES.items()):
        icon = "⛔" if locks.get(key, False) else "✅"
        row.append(InlineKeyboardButton(f"{icon} {title}", callback_data=f"locktoggle|{key}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ بستن پنل", callback_data="lockclose")])
    return InlineKeyboardMarkup(keyboard)

# ─────────────────────────────── واکنش به دکمه‌های پنل ───────────────────────────────
async def handle_lock_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    chat = query.message.chat

    if not await _is_admin_or_sudo(context, chat.id, user.id):
        return await query.answer("🚫 فقط مدیران مجازند.", show_alert=True)

    data = query.data
    if data == "lockclose":
        try:
            await query.message.delete()
        except:
            pass
        return await query.answer("❌ پنل بسته شد.")

    if data.startswith("locktoggle|"):
        key = data.split("|")[1]
        locks = _get_locks(chat.id)
        new_status = not locks.get(key, False)
        _set_lock(chat.id, key, new_status)
        state = "⛔ فعال شد" if new_status else "✅ غیرفعال شد"
        await query.answer(f"{LOCK_TYPES[key]} {state}")
        try:
            await query.edit_message_reply_markup(reply_markup=_generate_lock_panel(chat.id))
        except BadRequest:
            pass

# ─────────────────────────────── نمایش پنل قفل‌ها ───────────────────────────────
async def handle_lock_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if not await _is_admin_or_sudo(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    locks = _get_locks(chat.id)
    active = [LOCK_TYPES[k] for k, v in locks.items() if v]

    text = "<b>📋 وضعیت قفل‌های گروه</b>\n\n"
    if active:
        text += "🔒 قفل‌های فعال:\n" + "\n".join(f"• {x}" for x in active) + "\n\n"
    else:
        text += "✅ هیچ قفلی فعال نیست.\n\n"
    text += "برای فعال یا غیرفعال کردن روی دکمه‌های زیر کلیک کنید 👇"

    await update.message.reply_text(
        text, reply_markup=_generate_lock_panel(chat.id), parse_mode="HTML"
    )

    # ==========================================================
# 🧱 GROUP CONTROL SYSTEM — STEP 2
# قفل گروه، بازکردن گروه، و قفل خودکار زمان‌بندی‌شده
# ==========================================================
from telegram import ChatPermissions

# ─────────────────────────────── قفل گروه ───────────────────────────────
async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قفل کردن گروه (ممنوعیت ارسال پیام برای اعضا)"""
    chat = update.effective_chat
    user = update.effective_user

    if not await _is_admin_or_sudo(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    try:
        await context.bot.set_chat_permissions(
            chat.id,
            ChatPermissions(can_send_messages=False)
        )
        await update.message.reply_text(
            f"🔒 گروه توسط <b>{user.first_name}</b> قفل شد.\n"
            f"📴 ارسال پیام تا اطلاع ثانوی غیرفعال است.",
            parse_mode="HTML"
        )
    except Exception as e:
        if "chat_not_modified" in str(e).lower():
            await update.message.reply_text("ℹ️ گروه از قبل بسته بود.")
        else:
            await update.message.reply_text(f"⚠️ خطا در بستن گروه:\n<code>{e}</code>", parse_mode="HTML")


# ─────────────────────────────── باز کردن گروه ───────────────────────────────
async def unlock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """باز کردن گروه (فعال‌سازی ارسال پیام‌ها)"""
    chat = update.effective_chat
    user = update.effective_user

    if not await _is_admin_or_sudo(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    try:
        await context.bot.set_chat_permissions(
            chat.id,
            ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_polls=True,
                can_invite_users=True,
                can_pin_messages=True
            )
        )
        await update.message.reply_text(
            f"✅ گروه توسط <b>{user.first_name}</b> باز شد.\n"
            f"💬 کاربران دوباره می‌توانند پیام بفرستند.",
            parse_mode="HTML"
        )
    except Exception as e:
        if "chat_not_modified" in str(e).lower():
            await update.message.reply_text("ℹ️ گروه از قبل باز بود.")
        else:
            await update.message.reply_text(f"⚠️ خطا در باز کردن گروه:\n<code>{e}</code>", parse_mode="HTML")
# ─────────────────────────────── تنظیم ساعت قفل خودکار ───────────────────────────────
AUTOLOCK_FILE = "autolock.json"

# اطمینان از وجود فایل
if not os.path.exists(AUTOLOCK_FILE):
    with open(AUTOLOCK_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

# لود داده از فایل (با تابع جدید)
AUTOLOCKS = _load_json(AUTOLOCK_FILE, {})

# ذخیره داده در فایل
def _save_autolocks():
    _save_json(AUTOLOCK_FILE, AUTOLOCKS)


# ─────────────────────────────── دستور تنظیم خودکار ───────────────────────────────
async def set_auto_lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    تنظیم قفل خودکار گروه.
    مثال:
    تنظیم قفل خودکار 23:00 06:00
    (بستن در ۲۳ و باز کردن در ۶ صبح)
    """
    if not await _is_admin_or_sudo(context, update.effective_chat.id, update.effective_user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌تونن تنظیم کنن.")

    text = update.message.text.strip().split()
    if len(text) != 3:
        return await update.message.reply_text("📘 مثال:\n<code>تنظیم قفل خودکار 23:00 06:00</code>", parse_mode="HTML")

    start, end = text[1], text[2]
    try:
        datetime.strptime(start, "%H:%M")
        datetime.strptime(end, "%H:%M")
    except:
        return await update.message.reply_text("⚠️ فرمت ساعت اشتباه است. از 24 ساعته استفاده کن مثل 23:00", parse_mode="HTML")

    chat_id = str(update.effective_chat.id)
    AUTOLOCKS[chat_id] = {"start": start, "end": end}
    _save_autolocks()

    await update.message.reply_text(
        f"⏰ قفل خودکار تنظیم شد!\n"
        f"🔒 بستن در: <b>{start}</b>\n"
        f"🔓 باز کردن در: <b>{end}</b>",
        parse_mode="HTML"
    )


# ─────────────────────────────── اجرای خودکار قفل / بازکردن ───────────────────────────────
async def auto_lock_checker(context: ContextTypes.DEFAULT_TYPE):
    """بررسی خودکار قفل گروه بر اساس ساعت تنظیم‌شده"""
    now = datetime.now().strftime("%H:%M")
    for chat_id, times in AUTOLOCKS.items():
        start, end = times["start"], times["end"]
        locks = _get_locks(int(chat_id))

        # زمان بین بستن و باز کردن
        if start <= now or now < end:
            # قفل باید فعال باشد
            if not locks.get("group", False):
                try:
                    await context.bot.set_chat_permissions(
                        chat_id=int(chat_id),
                        permissions=ChatPermissions(can_send_messages=False)
                    )
                    _set_lock(int(chat_id), "group", True)
                    print(f"[AUTOLOCK] Group {chat_id} closed at {now}")
                except Exception as e:
                    print(f"[AUTOLOCK ERROR] {e}")
        else:
            # قفل باید باز باشد
            if locks.get("group", False):
                try:
                    await context.bot.set_chat_permissions(
                        chat_id=int(chat_id),
                        permissions=ChatPermissions(
                            can_send_messages=True,
                            can_send_audios=True,
                            can_send_documents=True,
                            can_send_photos=True,
                            can_send_videos=True,
                            can_send_voice_notes=True,
                            can_invite_users=True,
                            can_send_polls=True
                        )
                    )
                    _set_lock(int(chat_id), "group", False)
                    print(f"[AUTOLOCK] Group {chat_id} opened at {now}")
                except Exception as e:
                    print(f"[AUTOLOCK ERROR] {e}")
                    # ==========================================================
# 🧱 GROUP CONTROL SYSTEM — STEP 3
# فیلتر کلمات + حذف خودکار پیام‌های شامل فیلتر
# ==========================================================

FILTER_FILE = "filters.json"

# اطمینان از وجود فایل فیلترها
if not os.path.exists(FILTER_FILE):
    with open(FILTER_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

def _load_filters():
    try:
        with open(FILTER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def _save_filters(data):
    with open(FILTER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

FILTERS = _load_filters()

# ─────────────────────────────── افزودن فیلتر ───────────────────────────────
async def add_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """افزودن یک کلمه به لیست فیلتر"""
    if not await _is_admin_or_sudo(context, update.effective_chat.id, update.effective_user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌تونن فیلتر اضافه کنن.")

    text = update.message.text.strip().split(maxsplit=1)
    if len(text) < 2:
        return await update.message.reply_text("📘 مثال:\n<code>فیلتر کلمه</code>", parse_mode="HTML")

    word = text[1].lower()
    chat_id = str(update.effective_chat.id)

    FILTERS.setdefault(chat_id, [])
    if word in FILTERS[chat_id]:
        return await update.message.reply_text("⚠️ این کلمه از قبل در لیست فیلتر است.")

    FILTERS[chat_id].append(word)
    _save_filters(FILTERS)
    await update.message.reply_text(f"🚫 کلمه <b>{word}</b> به فیلتر اضافه شد.", parse_mode="HTML")

# ─────────────────────────────── حذف فیلتر ───────────────────────────────
async def remove_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف یک کلمه از فیلتر"""
    if not await _is_admin_or_sudo(context, update.effective_chat.id, update.effective_user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌تونن فیلتر حذف کنن.")

    text = update.message.text.strip().split(maxsplit=2)
    if len(text) < 3:
        return await update.message.reply_text("📘 مثال:\n<code>حذف فیلتر کلمه</code>", parse_mode="HTML")

    word = text[2].lower()
    chat_id = str(update.effective_chat.id)

    if chat_id not in FILTERS or word not in FILTERS[chat_id]:
        return await update.message.reply_text("⚠️ این کلمه در فیلتر وجود ندارد.")

    FILTERS[chat_id].remove(word)
    _save_filters(FILTERS)
    await update.message.reply_text(f"✅ کلمه <b>{word}</b> از فیلتر حذف شد.", parse_mode="HTML")

# ─────────────────────────────── لیست فیلترها ───────────────────────────────
async def list_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش تمام کلمات فیلترشده"""
    chat_id = str(update.effective_chat.id)
    words = FILTERS.get(chat_id, [])
    if not words:
        return await update.message.reply_text("✅ هیچ کلمه‌ای فیلتر نشده است.")
    text = "<b>🚫 لیست کلمات فیلتر شده:</b>\n\n" + "\n".join([f"• {w}" for w in words])
    await update.message.reply_text(text, parse_mode="HTML")

# ─────────────────────────────── بررسی و حذف پیام فیلتر ───────────────────────────────
async def check_filtered_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بررسی پیام و حذف در صورت وجود کلمه فیلتر"""
    if not update.message or not update.message.text:
        return

    chat_id = str(update.effective_chat.id)
    if chat_id not in FILTERS or not FILTERS[chat_id]:
        return

    text = update.message.text.lower()
    for word in FILTERS[chat_id]:
        if word in text:
            try:
                msg = await update.message.reply_text(
                    f"⚠️ پیام شما به دلیل استفاده از کلمه ممنوعه <b>{word}</b> حذف شد.",
                    parse_mode="HTML"
                )
                await asyncio.sleep(10)
                await update.message.delete()
                await msg.delete()
            except Exception as e:
                print(f"[Filter Error] {e}")
            break
            # ==========================================================
# 🧱 GROUP CONTROL SYSTEM — STEP 4
# ثبت اصل و لقب (پروفایل کاربران در گروه)
# ==========================================================

ORIGIN_FILE = "origins.json"

# اطمینان از وجود فایل داده
if not os.path.exists(ORIGIN_FILE):
    with open(ORIGIN_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

def _load_origins():
    try:
        with open(ORIGIN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def _save_origins(data):
    with open(ORIGIN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

ORIGINS = _load_origins()

# ─────────────────────────────── ثبت اصل ───────────────────────────────
async def set_origin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ثبت اصل برای کاربر (فقط مدیر یا سودو)"""
    if not await _is_admin_or_sudo(context, update.effective_chat.id, update.effective_user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌تونن اصل ثبت کنن.")

    target = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not target:
        return await update.message.reply_text("📎 روی پیام کاربر مورد نظر ریپلای بزن و بنویس: ثبت اصل")

    chat_id = str(update.effective_chat.id)
    ORIGINS.setdefault(chat_id, {})

    ORIGINS[chat_id].setdefault(str(target.id), {})
    ORIGINS[chat_id][str(target.id)]["origin"] = update.message.text.replace("ثبت اصل", "").strip() or "نامشخص"

    _save_origins(ORIGINS)

    await update.message.reply_text(
        f"🪪 برای <b>{target.first_name}</b>\nاصل ثبت شد: <b>{ORIGINS[chat_id][str(target.id)]['origin']}</b>",
        parse_mode="HTML"
    )

# ─────────────────────────────── ثبت لقب ───────────────────────────────
async def set_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ثبت لقب برای کاربر (فقط مدیر یا سودو)"""
    if not await _is_admin_or_sudo(context, update.effective_chat.id, update.effective_user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌تونن لقب ثبت کنن.")

    target = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not target:
        return await update.message.reply_text("📎 روی پیام کاربر مورد نظر ریپلای بزن و بنویس: ثبت لقب")

    chat_id = str(update.effective_chat.id)
    ORIGINS.setdefault(chat_id, {})

    ORIGINS[chat_id].setdefault(str(target.id), {})
    ORIGINS[chat_id][str(target.id)]["nickname"] = update.message.text.replace("ثبت لقب", "").strip() or "نامشخص"

    _save_origins(ORIGINS)

    await update.message.reply_text(
        f"🏷️ برای <b>{target.first_name}</b>\nلقب ثبت شد: <b>{ORIGINS[chat_id][str(target.id)]['nickname']}</b>",
        parse_mode="HTML"
    )

# ─────────────────────────────── نمایش اصل ───────────────────────────────
async def show_origin(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id=None):
    """نمایش اصل فرد"""
    chat_id = str(update.effective_chat.id)
    target_id = target_id or str(update.effective_user.id)
    if chat_id not in ORIGINS or target_id not in ORIGINS[chat_id] or "origin" not in ORIGINS[chat_id][target_id]:
        return await update.message.reply_text("ℹ️ برای این کاربر اصل ثبت نشده است.")

    origin = ORIGINS[chat_id][target_id]["origin"]
    await update.message.reply_text(f"🪪 اصل کاربر: <b>{origin}</b>", parse_mode="HTML")

# ─────────────────────────────── نمایش لقب ───────────────────────────────
async def show_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id=None):
    """نمایش لقب فرد"""
    chat_id = str(update.effective_chat.id)
    target_id = target_id or str(update.effective_user.id)
    if chat_id not in ORIGINS or target_id not in ORIGINS[chat_id] or "nickname" not in ORIGINS[chat_id][target_id]:
        return await update.message.reply_text("ℹ️ برای این کاربر لقب ثبت نشده است.")

    nickname = ORIGINS[chat_id][target_id]["nickname"]
    await update.message.reply_text(f"🏷️ لقب کاربر: <b>{nickname}</b>", parse_mode="HTML")
    # ==========================================================
# 🧱 GROUP CONTROL SYSTEM — STEP 5
# امتیازدهی (XP) و رتبه کاربران
# ==========================================================

from datetime import datetime

XP_FILE = "xp.json"

# ─────────────────────────────── اطمینان از وجود فایل ───────────────────────────────
if not os.path.exists(XP_FILE):
    with open(XP_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

def _load_xp():
    try:
        with open(XP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def _save_xp(data):
    with open(XP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

XP_DATA = _load_xp()

# ─────────────────────────────── افزودن امتیاز ───────────────────────────────
async def add_xp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """افزودن امتیاز به کاربر با هر پیام"""
    if not update.message or not update.effective_user or update.effective_user.is_bot:
        return

    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    user_id = str(user.id)

    XP_DATA.setdefault(chat_id, {})
    XP_DATA[chat_id].setdefault(user_id, {"xp": 0, "last": None})

    # ضد اسپم: فقط هر 30 ثانیه یک بار امتیاز بده
    now = datetime.now()
    last = XP_DATA[chat_id][user_id].get("last")
    if last and (now.timestamp() - last) < 30:
        return

    XP_DATA[chat_id][user_id]["xp"] += 1
    XP_DATA[chat_id][user_id]["last"] = now.timestamp()

    _save_xp(XP_DATA)

# ─────────────────────────────── نمایش رتبه من ───────────────────────────────
async def show_my_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش رتبه کاربر در گروه"""
    chat_id = str(update.effective_chat.id)
    user_id = str(update.effective_user.id)

    if chat_id not in XP_DATA or user_id not in XP_DATA[chat_id]:
        return await update.message.reply_text("ℹ️ هنوز امتیازی برایت ثبت نشده است.")

    user_xp = XP_DATA[chat_id][user_id]["xp"]
    # رتبه‌ی کاربر در بین بقیه
    sorted_users = sorted(XP_DATA[chat_id].items(), key=lambda x: x[1]["xp"], reverse=True)
    rank = next((i + 1 for i, (uid, _) in enumerate(sorted_users) if uid == user_id), None)

    await update.message.reply_text(
        f"🏅 <b>رتبه شما در گروه</b>\n\n"
        f"🎯 امتیاز: <b>{user_xp}</b>\n"
        f"📊 جایگاه: <b>{rank}</b> از <b>{len(sorted_users)}</b>",
        parse_mode="HTML"
    )

# ─────────────────────────────── نمایش لیست رتبه‌ها ───────────────────────────────
async def show_rank_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش 10 کاربر برتر گروه"""
    chat_id = str(update.effective_chat.id)
    if chat_id not in XP_DATA or not XP_DATA[chat_id]:
        return await update.message.reply_text("ℹ️ هنوز امتیازی برای هیچ‌کس ثبت نشده است.")

    sorted_users = sorted(XP_DATA[chat_id].items(), key=lambda x: x[1]["xp"], reverse=True)
    text = "<b>🏆 10 کاربر برتر گروه:</b>\n\n"

    for i, (uid, data) in enumerate(sorted_users[:10], start=1):
        text += f"{i}. <a href='tg://user?id={uid}'>کاربر {uid}</a> — <b>{data['xp']}</b> امتیاز\n"

    await update.message.reply_text(text, parse_mode="HTML")

# ─────────────────────────────── ریست رتبه‌ها ───────────────────────────────
async def reset_ranks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فقط مدیر یا سودو می‌تونه امتیازها رو ریست کنه"""
    if not await _is_admin_or_sudo(context, update.effective_chat.id, update.effective_user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌تونن رتبه‌ها رو ریست کنن.")

    chat_id = str(update.effective_chat.id)
    if chat_id in XP_DATA:
        XP_DATA[chat_id] = {}
        _save_xp(XP_DATA)
        await update.message.reply_text("♻️ تمام امتیازها و رتبه‌ها ریست شد.")
    else:
        await update.message.reply_text("ℹ️ هیچ داده‌ای برای این گروه وجود ندارد.")
        # ==========================================================
# 🧱 GROUP CONTROL SYSTEM — STEP 6
# تگ گروهی (همه / فعال / غیرفعال / مدیران)
# ==========================================================

import asyncio

# ─────────────────────────────── تابع اصلی تگ ───────────────────────────────
async def tag_users(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str):
    """تگ کاربران بر اساس حالت (همه، فعال، غیرفعال، مدیران)"""
    chat = update.effective_chat
    user = update.effective_user

    if not await _is_admin_or_sudo(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران و سودوها می‌توانند از این دستور استفاده کنند.")

    try:
        members = await context.bot.get_chat_administrators(chat.id)
        admins = [m.user.id for m in members]

        if mode == "admins":
            users_to_tag = admins
        else:
            # اگر داده امتیاز موجود باشد از آن برای تشخیص فعال‌ها استفاده می‌کنیم
            chat_id = str(chat.id)
            all_users = XP_DATA.get(chat_id, {})

            if not all_users:
                return await update.message.reply_text("ℹ️ هنوز داده‌ای از کاربران وجود ندارد.")

            # مرتب‌سازی بر اساس آخرین فعالیت
            sorted_users = sorted(all_users.items(), key=lambda x: x[1].get("last", 0), reverse=True)

            if mode == "active":
                users_to_tag = [int(uid) for uid, data in sorted_users[:10]]  # ۱۰ کاربر فعال
            elif mode == "inactive":
                users_to_tag = [int(uid) for uid, data in sorted_users[-10:]]  # ۱۰ کاربر غیرفعال
            else:
                users_to_tag = [int(uid) for uid in all_users.keys()]

        # جلوگیری از تگ خود ربات
        me = await context.bot.get_me()
        users_to_tag = [uid for uid in users_to_tag if uid != me.id]

        if not users_to_tag:
            return await update.message.reply_text("ℹ️ کاربری برای تگ یافت نشد.")

        await update.message.reply_text("📢 در حال تگ کردن کاربران...")

        batch_size = 5  # تعداد کاربران در هر پیام
        for i in range(0, len(users_to_tag), batch_size):
            batch = users_to_tag[i:i + batch_size]
            mentions = " ".join([f"<a href='tg://user?id={uid}'>👤</a>" for uid in batch])
            try:
                await context.bot.send_message(chat.id, mentions, parse_mode="HTML")
                await asyncio.sleep(2)  # تأخیر بین پیام‌ها برای جلوگیری از Flood
            except Exception as e:
                print(f"[Tag Error] {e}")

        await update.message.reply_text("✅ تگ کاربران انجام شد.", parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در دریافت کاربران:\n<code>{e}</code>", parse_mode="HTML")
        # ==========================================================

            # ==========================================================
# 🧹 STEP 13 — سیستم پاکسازی نهایی (Purge System v4)
# کاملاً سازگار با PTB v20+ و بدون متد get_history
# ==========================================================
import asyncio
from datetime import datetime
from telegram.error import BadRequest, RetryAfter

# ─────────────────────────────── ابزار حذف امن ───────────────────────────────
async def _safe_delete(context, chat_id, msg_id):
    try:
        await context.bot.delete_message(chat_id, msg_id)
        await asyncio.sleep(0.05)
        return True
    except RetryAfter as r:
        await asyncio.sleep(r.retry_after + 1)
        return await _safe_delete(context, chat_id, msg_id)
    except BadRequest as e:
        if "message can't be deleted" in str(e).lower():
            return False
        return False
    except:
        return False


# ─────────────────────────────── پاکسازی عددی ───────────────────────────────
async def purge_count(update: Update, context: ContextTypes.DEFAULT_TYPE, count: int):
    """🧹 حذف تعداد مشخصی از پیام‌ها"""
    chat = update.effective_chat
    user = update.effective_user
    msg_id = update.message.message_id

    if not await _is_admin_or_sudo(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران و سودوها مجازند.")

    deleted = 0
    await update.message.reply_text(f"🧹 در حال حذف {count} پیام اخیر...")

    # از آخر به عقب
    for mid in range(msg_id, msg_id - count, -1):
        if mid <= 0:
            break
        if await _safe_delete(context, chat.id, mid):
            deleted += 1

    now = datetime.now().strftime("%Y-%m-%d | %H:%M:%S")
    await context.bot.send_message(
        chat.id,
        f"✅ {deleted} پیام حذف شد.\n🕒 {now}\n👤 مدیر: <a href='tg://user?id={user.id}'>{user.first_name}</a>",
        parse_mode="HTML"
    )


# ─────────────────────────────── حذف پیام‌های یک کاربر ───────────────────────────────
async def purge_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧹 حذف پیام‌های اخیر یک کاربر خاص"""
    chat = update.effective_chat
    user = update.effective_user
    reply = update.message.reply_to_message

    if not await _is_admin_or_sudo(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
    if not reply:
        return await update.message.reply_text("📎 روی پیام کاربر ریپلای کن و بنویس: حذف")

    target = reply.from_user
    deleted = 0

    await update.message.reply_text(f"🧹 در حال حذف پیام‌های {target.first_name}...")

    # فقط ۵۰۰ پیام اخیر چک می‌کنیم (محدودیت API)
    for mid in range(update.message.message_id, update.message.message_id - 500, -1):
        try:
            msg = await context.bot.get_message(chat.id, mid)
            if msg and msg.from_user and msg.from_user.id == target.id:
                if await _safe_delete(context, chat.id, mid):
                    deleted += 1
        except:
            continue

    now = datetime.now().strftime("%Y-%m-%d | %H:%M:%S")
    await context.bot.send_message(
        chat.id,
        f"✅ {deleted} پیام از {target.first_name} حذف شد.\n🕒 {now}",
        parse_mode="HTML"
    )


# ─────────────────────────────── پاکسازی بین دو پیام ───────────────────────────────
async def purge_between(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧹 پاکسازی بین دو پیام (از ریپلای تا دستور فعلی)"""
    chat = update.effective_chat
    user = update.effective_user
    reply = update.message.reply_to_message

    if not await _is_admin_or_sudo(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
    if not reply:
        return await update.message.reply_text("📎 روی پیام قدیمی ریپلای کن و بنویس: تا اینجا حذف")

    start_id = reply.message_id
    end_id = update.message.message_id
    deleted = 0

    for mid in range(end_id, start_id - 1, -1):
        if await _safe_delete(context, chat.id, mid):
            deleted += 1

    now = datetime.now().strftime("%Y-%m-%d | %H:%M:%S")
    await context.bot.send_message(
        chat.id,
        f"✅ {deleted} پیام بین دو نقطه حذف شد.\n🕒 {now}\n👤 مدیر: <a href='tg://user?id={user.id}'>{user.first_name}</a>",
        parse_mode="HTML"
    )


# ─────────────────────────────── پاکسازی کل گروه (تا حد API) ───────────────────────────────
async def purge_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧹 حذف کل پیام‌ها (حداکثر 10000 مورد)"""
    chat = update.effective_chat
    user = update.effective_user
    msg_id = update.message.message_id

    if not await _is_admin_or_sudo(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    await update.message.reply_text("🧹 در حال پاکسازی کل گروه...\nلطفاً صبر کنید.")

    deleted = 0
    for mid in range(msg_id, msg_id - 10000, -1):
        if mid <= 0:
            break
        if await _safe_delete(context, chat.id, mid):
            deleted += 1
        if mid % 200 == 0:
            await asyncio.sleep(1)  # ضد flood

    now = datetime.now().strftime("%Y-%m-%d | %H:%M:%S")
    await context.bot.send_message(
        chat.id,
        f"✅ گروه تا حد مجاز پاکسازی شد.\n🧾 {deleted} پیام حذف شد.\n🕒 {now}",
        parse_mode="HTML"
                             )
 
        # ==========================================================
# 🧱 GROUP CONTROL SYSTEM — STEP 8
# بن / سکوت / اخطار با alias
# ==========================================================

import json, os, asyncio
from telegram import ChatPermissions

PUNISH_FILE = "punishments.json"
if not os.path.exists(PUNISH_FILE):
    with open(PUNISH_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

PUNISH_DATA = _load_json(PUNISH_FILE, {})

def _save_punish():
    _save_json(PUNISH_FILE, PUNISH_DATA)

# ─────────────── اعمال‌ها ───────────────
async def _do_ban(update, context, target):
    chat = update.effective_chat
    await context.bot.ban_chat_member(chat.id, target.id)
    await update.message.reply_text(f"🚫 <b>{target.first_name}</b> بن شد.", parse_mode="HTML")

async def _do_mute(update, context, target):
    chat = update.effective_chat
    await context.bot.restrict_chat_member(chat.id, target.id, permissions=ChatPermissions(can_send_messages=False))
    await update.message.reply_text(f"🤐 <b>{target.first_name}</b> ساکت شد.", parse_mode="HTML")

async def _do_warn(update, context, target):
    chat = update.effective_chat
    cid, uid = str(chat.id), str(target.id)
    PUNISH_DATA.setdefault(cid, {}).setdefault("warns", {})
    warns = PUNISH_DATA[cid]["warns"]
    warns[uid] = warns.get(uid, 0) + 1
    _save_punish()

    if warns[uid] >= 3:
        await _do_ban(update, context, target)
        del warns[uid]
        _save_punish()
        return await update.message.reply_text(f"🚨 <b>{target.first_name}</b> با ۳ اخطار بن شد.", parse_mode="HTML")
    await update.message.reply_text(f"⚠️ به <b>{target.first_name}</b> اخطار داده شد ({warns[uid]}/3)", parse_mode="HTML")

# ─────────────── لیست اخطارها ───────────────
async def list_warns(update, context):
    cid = str(update.effective_chat.id)
    warns = PUNISH_DATA.get(cid, {}).get("warns", {})
    if not warns:
        return await update.message.reply_text("✅ هیچ اخطاری وجود ندارد.")
    text = "<b>⚠️ لیست اخطارها:</b>\n"
    for uid, count in warns.items():
        text += f"• <a href='tg://user?id={uid}'>کاربر {uid}</a> — {count}/3\n"
    await update.message.reply_text(text, parse_mode="HTML")
    # ==========================================================
# 🧱 STEP 9 — مدیریت مدیران هر گروه (Local Admins)
# ==========================================================

ADMINS_FILE = "group_admins.json"
ADMINS = _load_json(ADMINS_FILE, {})

def _save_admins():
    _save_json(ADMINS_FILE, ADMINS)

async def add_admin(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران اصلی می‌تونن مدیر جدید اضافه کنن.")
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("📎 روی پیام فردی ریپلای کن تا مدیرش کنم.")
    cid, uid = str(update.effective_chat.id), str(reply.from_user.id)
    ADMINS.setdefault(cid, [])
    if uid not in ADMINS[cid]:
        ADMINS[cid].append(uid)
        _save_admins()
        await update.message.reply_text(f"👮 <b>{reply.from_user.first_name}</b> مدیر گروه شد.", parse_mode="HTML")

async def del_admin(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران اصلی می‌تونن حذف کنن.")
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("📎 روی پیام مدیر ریپلای کن تا حذفش کنم.")
    cid, uid = str(update.effective_chat.id), str(reply.from_user.id)
    if uid in ADMINS.get(cid, []):
        ADMINS[cid].remove(uid)
        _save_admins()
        await update.message.reply_text(f"🧹 <b>{reply.from_user.first_name}</b> از مدیران حذف شد.", parse_mode="HTML")

async def list_admins(update, context):
    cid = str(update.effective_chat.id)
    admins = ADMINS.get(cid, [])
    if not admins:
        return await update.message.reply_text("ℹ️ هنوز هیچ مدیر محلی ثبت نشده.")
    text = "<b>👮 مدیران ثبت‌شده:</b>\n"
    for uid in admins:
        text += f"• <a href='tg://user?id={uid}'>کاربر {uid}</a>\n"
    await update.message.reply_text(text, parse_mode="HTML")
    # ==========================================================
# 🧱 STEP 10 — مدیریت سودوهای ربات (Global Sudo)
# ==========================================================

SUDO_FILE = "sudos.json"
SUDOS = _load_json(SUDO_FILE, {})

def _save_sudos():
    _save_json(SUDO_FILE, SUDOS)

async def add_sudo(update, context):
    if update.effective_user.id not in SUDO_IDS:
        return await update.message.reply_text("🚫 فقط سودوی اصلی ربات می‌تونه سودو جدید اضافه کنه.")
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("📎 روی پیام کاربر ریپلای کن تا سودو بشه.")
    uid = str(reply.from_user.id)
    if uid not in SUDO_IDS:
        SUDO_IDS.append(int(uid))
        _save_sudos()
        await update.message.reply_text(f"👑 <b>{reply.from_user.first_name}</b> به سودوهای جهانی افزوده شد.", parse_mode="HTML")

async def del_sudo(update, context):
    if update.effective_user.id not in SUDO_IDS:
        return await update.message.reply_text("🚫 فقط سودوی اصلی می‌تونه حذف کنه.")
    reply = update.message.reply_to_message
    if not reply:
        return await update.message.reply_text("📎 روی پیام سودو ریپلای کن تا حذفش کنم.")
    uid = str(reply.from_user.id)
    if int(uid) in SUDO_IDS:
        SUDO_IDS.remove(int(uid))
        _save_sudos()
        await update.message.reply_text(f"🧹 <b>{reply.from_user.first_name}</b> از سودوها حذف شد.", parse_mode="HTML")

async def list_sudos(update, context):
    if not SUDO_IDS:
        return await update.message.reply_text("ℹ️ هیچ سودویی ثبت نشده.")
    text = "<b>👑 سودوهای ربات:</b>\n"
    for uid in SUDO_IDS:
        text += f"• <a href='tg://user?id={uid}'>کاربر {uid}</a>\n"
    await update.message.reply_text(text, parse_mode="HTML")

    # ==========================================================
# 🧱 GROUP CONTROL SYSTEM — STEP 11
# گزارش کامل وضعیت گروه (Group Report System)
# ==========================================================
from datetime import datetime

async def handle_group_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📊 نمایش گزارش کامل وضعیت گروه (فقط برای مدیران و سودوها)"""
    chat = update.effective_chat
    user = update.effective_user

    # بررسی مجوز
    if not await _is_admin_or_sudo(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجاز به دریافت گزارش هستند.")

    try:
        # 📈 آمار زنده از تلگرام
        members = await context.bot.get_chat_members_count(chat.id)
        admins = await context.bot.get_chat_administrators(chat.id)
        admin_count = len(admins)

        # 🔒 قفل‌های فعال
        locks = _get_locks(chat.id)
        active_locks = [LOCK_TYPES[k] for k, v in locks.items() if v]

        # 🚫 کاربران محدودشده
        mutes = MUTES.get(str(chat.id), [])
        bans = BANS.get(str(chat.id), [])
        warns = WARNS.get(str(chat.id), {})

        # 👮 مدیران محلی
        local_admins = ADMINS.get(str(chat.id), [])

        # 👑 سودوها
        sudo_count = len(SUDO_IDS)

        # 🕒 زمان فعلی
        now = datetime.now().strftime("%Y-%m-%d | %H:%M:%S")

        # 📋 ساخت متن گزارش
        text = (
            "━━━━━━━━━━━━━━━\n"
            f"📊 <b>گزارش وضعیت گروه</b>\n"
            f"🕒 <i>{now}</i>\n"
            "━━━━━━━━━━━━━━━\n"
            f"🏷️ <b>نام گروه:</b> {chat.title}\n"
            f"👥 <b>تعداد اعضا:</b> {members}\n"
            f"👮 <b>مدیران تلگرام:</b> {admin_count}\n"
            f"🔧 <b>مدیران محلی:</b> {len(local_admins)}\n"
            f"👑 <b>سودوها:</b> {sudo_count}\n"
            "━━━━━━━━━━━━━━━\n"
        )

        # 🔒 قفل‌های فعال
        if active_locks:
            text += "🔒 <b>قفل‌های فعال:</b>\n" + "، ".join(active_locks) + "\n"
        else:
            text += "✅ هیچ قفلی فعال نیست.\n"

        # 🚫 وضعیت کاربران محدودشده
        text += (
            "\n━━━━━━━━━━━━━━━\n"
            f"🤐 <b>در سکوت:</b> {len(mutes)} نفر\n"
            f"🚫 <b>بن‌شده:</b> {len(bans)} نفر\n"
            f"⚠️ <b>دارای اخطار:</b> {len(warns)} نفر\n"
            "━━━━━━━━━━━━━━━\n"
            f"👤 <b>درخواست توسط:</b> <a href='tg://user?id={user.id}'>{user.first_name}</a>\n"
            "━━━━━━━━━━━━━━━"
        )

        await update.message.reply_text(text, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ خطا در ایجاد گزارش:\n<code>{e}</code>",
            parse_mode="HTML"
        )
        # ==========================================================
# 🧱 STEP 12 — سیستم دستورهای سفارشی (Alias System)
# ==========================================================

ALIAS_FILE = "aliases.json"

# ─────────────────────────────── اطمینان از وجود فایل ───────────────────────────────
if not os.path.exists(ALIAS_FILE):
    with open(ALIAS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

ALIASES = _load_json(ALIAS_FILE, {})

def _save_aliases():
    _save_json(ALIAS_FILE, ALIASES)

# ─────────────────────────────── افزودن دستور ───────────────────────────────
async def handle_add_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """افزودن یک دستور سفارشی (Alias)"""
    chat = update.effective_chat
    user = update.effective_user
    text = update.message.text.strip()

    if not await _is_admin_or_sudo(context, chat.id, user.id):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌تونن دستور جدید اضافه کنن.")

    # قالب: افزودن دستور جدید = دستور اصلی
    if "=" not in text:
        return await update.message.reply_text("📘 مثال:\n<code>افزودن دستور بنش = بن</code>", parse_mode="HTML")

    parts = text.split("دستور", 1)[1].strip().split("=")
    if len(parts) != 2:
        return await update.message.reply_text("⚠️ فرمت دستور اشتباه است.", parse_mode="HTML")

    alias = parts[0].strip()
    real = parts[1].strip()

    if not alias or not real:
        return await update.message.reply_text("⚠️ لطفاً نام دستور و عمل اصلی را مشخص کن.")

    chat_id = str(chat.id)
    ALIASES.setdefault(chat_id, {})
    ALIASES[chat_id][alias] = real
    _save_aliases()

    await update.message.reply_text(f"✅ دستور <b>{alias}</b> به عنوان معادل <b>{real}</b> ثبت شد.", parse_mode="HTML")

# ─────────────────────────────── لیست دستورهای سفارشی ───────────────────────────────
async def handle_list_aliases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست aliasها"""
    chat_id = str(update.effective_chat.id)
    data = ALIASES.get(chat_id, {})
    if not data:
        return await update.message.reply_text("ℹ️ هیچ دستوری ثبت نشده است.")
    text = "<b>📜 لیست دستورهای سفارشی:</b>\n\n"
    for k, v in data.items():
        text += f"• {k} → {v}\n"
    await update.message.reply_text(text, parse_mode="HTML")

# ─────────────────────────────── تشخیص aliasها ───────────────────────────────
async def handle_locks_with_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بررسی و اجرای aliasهای ثبت‌شده"""
    chat = update.effective_chat
    text = update.message.text.strip().lower()
    chat_id = str(chat.id)

    if chat_id not in ALIASES:
        return

    if text in ALIASES[chat_id]:
        new_cmd = ALIASES[chat_id][text]
        update.message.text = new_cmd
        print(f"[ALIAS] {text} → {new_cmd}")
        return await handle_group_message(update, context)
        # ─────────────────────────────── ابزار حذف و اخطار ───────────────────────────────
import asyncio

async def _del_msg(update: Update, warn_text: str = None):
    """حذف پیام کاربر و نمایش هشدار موقت"""
    try:
        chat_id = update.effective_chat.id
        msg_id = update.message.message_id
        user = update.effective_user

        # حذف پیام اصلی
        await update.message.delete()

        # اگر متن هشدار تعریف شده، بفرست و بعد از چند ثانیه پاک کن
        if warn_text:
            warn = await update.effective_chat.send_message(
                f"{warn_text}\n👤 <a href='tg://user?id={user.id}'>{user.first_name}</a>",
                parse_mode="HTML"
            )
            await asyncio.sleep(5)
            await warn.delete()
    except Exception as e:
        print(f"[Lock Delete Error] {e}")
        
# ==========================================================
# 🧱 تابع مرکزی گروه (نسخه اصلاح‌شده نهایی)
# ==========================================================

import asyncio, re
from telegram import Update
from telegram.ext import ContextTypes

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستگاه مرکزی کنترل گروه — نسخه پایدار و نهایی"""
    if not update.message:
        return

    # متن پیام (برای متن و کپشن)
    text = (update.message.text or update.message.caption or "").strip().lower()
    chat = update.effective_chat
    user = update.effective_user

    # ─────────────────────────────── دستورات قفل / بازکردن / وضعیت / پنل ───────────────────────────────
    if text in ["قفل گروه", "بستن گروه", "بستن"]:
        return await lock_group(update, context)

    if text in ["باز کردن گروه", "باز کردن", "گروه باز"]:
        return await unlock_group(update, context)

    if text in ["وضعیت قفل‌ها", "وضعیت قفل", "locks"]:
        return await handle_locks_status(update, context)

    if text in ["پنل قفل", "پنل قفل‌ها", "lock panel"]:
        return await handle_lock_panel(update, context)

    # ─────────────── بررسی قفل‌های فعال ───────────────
    locks = _get_locks(chat.id)
    if any(locks.values()):
        is_admin = await _is_admin_or_sudo(context, chat.id, user.id)

        # 🚫 قفل گروه
        if locks.get("group") and not is_admin:
            try:
                await update.message.delete()
            except:
                pass
            return

        # 🚫 قفل لینک
        if locks.get("links") and any(x in text for x in ["http", "t.me", "telegram.me"]):
            await _del_msg(update, "🚫 ارسال لینک ممنوع است.")
            return

        # 🚫 قفل رسانه‌ها
        if locks.get("photos") and update.message.photo:
            await _del_msg(update, "🚫 ارسال عکس ممنوع است.")
            return
        if locks.get("videos") and update.message.video:
            await _del_msg(update, "🚫 ارسال ویدیو ممنوع است.")
            return
        if locks.get("files") and update.message.document:
            await _del_msg(update, "🚫 ارسال فایل ممنوع است.")
            return
        if locks.get("voices") and update.message.voice:
            await _del_msg(update, "🚫 ارسال ویس ممنوع است.")
            return
        if locks.get("stickers") and update.message.sticker:
            await _del_msg(update, "🚫 ارسال استیکر ممنوع است.")
            return
        if locks.get("gifs") and update.message.animation:
            await _del_msg(update, "🚫 ارسال گیف ممنوع است.")
            return
        if locks.get("forward") and update.message.forward_date:
            await _del_msg(update, "🚫 فوروارد پیام ممنوع است.")
            return
        if locks.get("media") and (update.message.photo or update.message.video or update.message.document or update.message.animation):
            await _del_msg(update, "🚫 ارسال رسانه ممنوع است.")
            return

        # 🚫 منشن / تگ
        if (locks.get("usernames") or locks.get("mention")) and "@" in text:
            await _del_msg(update, "🚫 استفاده از @ یا منشن ممنوع است.")
            return

        # 🚫 تبلیغ
        if locks.get("ads") and any(x in text for x in ["t.me/", "joinchat", "promo"]):
            await _del_msg(update, "🚫 تبلیغات ممنوع است.")
            return

        # 🚫 عربی / انگلیسی
        if locks.get("arabic") and any("\u0600" <= c <= "\u06FF" for c in text):
            await _del_msg(update, "🚫 استفاده از حروف عربی ممنوع است.")
            return
        if locks.get("english") and any("a" <= c <= "z" or "A" <= c <= "Z" for c in text):
            await _del_msg(update, "🚫 استفاده از حروف انگلیسی ممنوع است.")
            return

        # 🚫 کپشن
        if locks.get("caption") and update.message.caption:
            await _del_msg(update, "🚫 کپشن‌گذاری ممنوع است.")
            return

        # 🚫 ریپلای
        if locks.get("reply") and update.message.reply_to_message:
            await _del_msg(update, "🚫 پاسخ دادن (ریپلای) ممنوع است.")
            return

        # 🚫 فقط ایموجی
        if locks.get("emoji"):
            emoji_pattern = re.compile("[\U00010000-\U0010ffff]", flags=re.UNICODE)
            if all(emoji_pattern.match(c) for c in text if not c.isspace()):
                await _del_msg(update, "🚫 ارسال فقط ایموجی مجاز نیست.")
                return

        # 🚫 پیام متنی
        if locks.get("text") and not (update.message.photo or update.message.video):
            await _del_msg(update, "🚫 ارسال پیام متنی ممنوع است.")
            return

    # ─────────────────────────────── فیلتر کلمات ───────────────────────────────
    if text.startswith("فیلتر "):
        return await add_filter(update, context)
    if text.startswith("حذف فیلتر "):
        return await remove_filter(update, context)
    if text in ["لیست فیلتر", "لیست فیلترها"]:
        return await list_filters(update, context)

    # ─────────────────────────────── بن / سکوت / اخطار ───────────────────────────────
    if text in ["بن", "ban"]:
        if not update.message.reply_to_message:
            return await update.message.reply_text("📎 روی پیام فرد ریپلای کن تا بن شود.")
        return await _do_ban(update, context, update.message.reply_to_message.from_user)

    if text in ["سکوت", "mute"]:
        if not update.message.reply_to_message:
            return await update.message.reply_text("📎 روی پیام فرد ریپلای کن تا ساکت شود.")
        return await _do_mute(update, context, update.message.reply_to_message.from_user)

    if text in ["اخطار", "warn"]:
        if not update.message.reply_to_message:
            return await update.message.reply_text("📎 روی پیام فرد ریپلای کن تا اخطار بگیرد.")
        return await _do_warn(update, context, update.message.reply_to_message.from_user)

    if text in ["لیست اخطار", "warns"]:
        return await list_warns(update, context)

    # ─────────────────────────────── مدیریت مدیران و سودوها ───────────────────────────────
    if text in ["افزودن مدیر", "add admin"]:
        return await add_admin(update, context)
    if text in ["حذف مدیر", "remove admin"]:
        return await del_admin(update, context)
    if text in ["لیست مدیران", "admins list"]:
        return await list_admins(update, context)
    if text in ["افزودن سودو", "add sudo"]:
        return await add_sudo(update, context)
    if text in ["حذف سودو", "remove sudo"]:
        return await del_sudo(update, context)
    if text in ["لیست سودو", "sudo list"]:
        return await list_sudos(update, context)

    # ─────────────────────────────── اصل / لقب ───────────────────────────────
    if text == "ثبت اصل":
        return await set_origin(update, context)
    if text == "ثبت لقب":
        return await set_nickname(update, context)
    if text == "اصل":
        return await show_origin(update, context)
    if text == "اصل من":
        return await show_my_original(update, context)
    if text == "لقب":
        return await show_nickname(update, context)
    if text == "لقب من":
        return await show_my_nickname(update, context)

    # ─────────────────────────────── تگ کاربران ───────────────────────────────
    if text == "تگ همه":
        return await tag_users(update, context, "all")
    if text == "تگ فعال":
        return await tag_users(update, context, "active")
    if text == "تگ غیرفعال":
        return await tag_users(update, context, "inactive")
    if text == "تگ مدیران":
        return await tag_users(update, context, "admins")

    # ─────────────────────────────── پاکسازی پیام‌ها ───────────────────────────────
    if text == "پاکسازی":
        return await purge_all(update, context)
    if text.startswith("حذف "):
        try:
            number = int(text.split(" ")[1])
            return await purge_count(update, context, number)
        except:
            return await update.message.reply_text("⚠️ مثال: حذف 50")
    if text == "حذف" and update.message.reply_to_message:
        return await purge_user(update, context)
    if text in ["تا اینجا حذف", "پاکسازی بین"]:
        return await purge_between(update, context)

    # ─────────────────────────────── گزارش کامل ───────────────────────────────
    if text in ["گزارش گروه", "وضعیت گروه", "report"]:
        return await handle_group_report(update, context)

    # ─────────────────────────────── aliasها ───────────────────────────────
    if text.startswith("افزودن دستور"):
        return await handle_add_alias(update, context)
    if text in ["لیست دستورها", "لیست alias"]:
        return await handle_list_aliases(update, context)

    # ✅ در پایان — aliasها فقط بررسی می‌شن، نه return
    await handle_locks_with_alias(update, context)
