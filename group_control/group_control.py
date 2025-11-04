# ==========================================================
# 🧱 GROUP CONTROL SYSTEM — STEP 1
# پایه‌ها + ۲۵ نوع قفل + فایل ذخیره‌سازی
# ==========================================================

import os, json
from telegram import Update
from telegram.ext import ContextTypes

# ─────────────────────────────── مسیر فایل‌ها ───────────────────────────────

GROUP_CTRL_FILE = "group_control.json"

# اطمینان از وجود فایل
if not os.path.exists(GROUP_CTRL_FILE):
    with open(GROUP_CTRL_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

# ─────────────────────────────── توابع ذخیره و بارگذاری ───────────────────────────────

def _load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ خطا در بارگذاری {path}: {e}")
    return default

def _save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ خطا در ذخیره {path}: {e}")

# ─────────────────────────────── داده اصلی ───────────────────────────────

group_data = _load_json(GROUP_CTRL_FILE, {})

# ─────────────────────────────── سودوها (مدیران کل) ───────────────────────────────

SUDO_IDS = [8588347189]  # 👈 آیدی خودت رو اینجا بذار

# ─────────────────────────────── قفل‌ها (۲۵ نوع کامل) ───────────────────────────────

LOCK_TYPES = {
    "links": "ارسال لینک",
    "photos": "ارسال عکس",
    "videos": "ارسال ویدیو",
    "files": "ارسال فایل",
    "voices": "ارسال ویس",
    "vmsgs": "ارسال ویدیو مسیج",
    "stickers": "ارسال استیکر",
    "gifs": "ارسال گیف",
    "media": "ارسال همه رسانه‌ها",
    "forward": "ارسال فوروارد",
    "ads": "ارسال تبلیغ/تبچی",
    "usernames": "ارسال یوزرنیم/تگ",
    "mention": "منشن با @",
    "bots": "افزودن ربات",
    "join": "ورود عضو جدید",
    "tgservices": "پیام‌های سیستمی تلگرام",
    "joinmsg": "پیام خوش‌آمدگویی",
    "arabic": "حروف عربی (غیرفارسی)",
    "english": "حروف انگلیسی",
    "text": "ارسال پیام متنی",
    "audio": "ارسال آهنگ/موزیک",
    "emoji": "ارسال فقط ایموجی",
    "caption": "ارسال کپشن",
    "edit": "ویرایش پیام",
    "reply": "ریپلای/پاسخ به پیام",
}

# ─────────────────────────────── نگاشت فارسی → کلید ───────────────────────────────

PERSIAN_TO_KEY = {
    "لینک": "links",
    "عکس": "photos", "تصویر": "photos",
    "ویدیو": "videos", "فیلم": "videos",
    "فایل": "files",
    "ویس": "voices",
    "ویدیو مسیج": "vmsgs",
    "استیکر": "stickers",
    "گیف": "gifs",
    "رسانه": "media",
    "فوروارد": "forward",
    "تبچی": "ads", "تبلیغ": "ads",
    "یوزرنیم": "usernames", "تگ": "usernames",
    "منشن": "mention",
    "ربات": "bots",
    "ورود": "join",
    "سرویس": "tgservices",
    "پیام ورود": "joinmsg",
    "عربی": "arabic",
    "انگلیسی": "english",
    "متن": "text",
    "آهنگ": "audio", "موزیک": "audio",
    "ایموجی": "emoji",
    "کپشن": "caption",
    "ویرایش": "edit",
    "ریپلای": "reply",
}

# ─────────────────────────────── توابع دسترسی قفل‌ها ───────────────────────────────

def _locks_get(chat_id: int) -> dict:
    """دریافت قفل‌های فعال برای گروه"""
    g = group_data.get(str(chat_id), {})
    return g.get("locks", {})

def _locks_set(chat_id: int, key: str, status: bool):
    """تنظیم وضعیت یک قفل"""
    cid = str(chat_id)
    g = group_data.get(cid, {})
    locks = g.get("locks", {})
    locks[key] = bool(status)
    g["locks"] = locks
    group_data[cid] = g
    _save_json(GROUP_CTRL_FILE, group_data)
    # ==========================================================
# 🧱 GROUP CONTROL SYSTEM — STEP 2
# فعال / غیرفعال کردن قفل‌ها + وضعیت قفل‌ها
# ==========================================================

from telegram import Update
from telegram.ext import ContextTypes

# ─────────────────────────────── بررسی سطح دسترسی ───────────────────────────────

async def _is_admin_or_sudo_uid(context, chat_id: int, user_id: int) -> bool:
    """بررسی اینکه آیا کاربر مدیر یا سودو است"""
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except:
        return False

async def is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """بررسی اینکه آیا فرستنده پیام مجاز است"""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return False
    if user.id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ("administrator", "creator")
    except:
        return False

# ─────────────────────────────── فعال کردن قفل ───────────────────────────────

async def handle_lock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    """فعال‌سازی قفل مورد نظر"""
    if key not in LOCK_TYPES:
        return await update.message.reply_text("⚠️ همچین قفلی وجود ندارد.")
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران و سودوها مجاز به اجرای این دستور هستند.")

    chat = update.effective_chat
    locks = _locks_get(chat.id)
    if locks.get(key):
        return await update.message.reply_text(
            f"🔒 قفل <b>{LOCK_TYPES[key]}</b> از قبل فعال بوده است.",
            parse_mode="HTML"
        )

    _locks_set(chat.id, key, True)
    await update.message.reply_text(
        f"✅ قفل <b>{LOCK_TYPES[key]}</b> با موفقیت فعال شد.",
        parse_mode="HTML"
    )

# ─────────────────────────────── غیرفعال کردن قفل ───────────────────────────────

async def handle_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    """غیرفعال‌سازی قفل"""
    if key not in LOCK_TYPES:
        return await update.message.reply_text("⚠️ همچین قفلی وجود ندارد.")
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران و سودوها مجاز به اجرای این دستور هستند.")

    chat = update.effective_chat
    locks = _locks_get(chat.id)
    if not locks.get(key):
        return await update.message.reply_text(
            f"🔓 قفل <b>{LOCK_TYPES[key]}</b> از قبل غیرفعال بوده است.",
            parse_mode="HTML"
        )

    _locks_set(chat.id, key, False)
    await update.message.reply_text(
        f"🔓 قفل <b>{LOCK_TYPES[key]}</b> با موفقیت باز شد.",
        parse_mode="HTML"
    )

# ─────────────────────────────── نمایش وضعیت قفل‌ها ───────────────────────────────

async def handle_locks_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش وضعیت تمام قفل‌ها"""
    chat = update.effective_chat
    locks = _locks_get(chat.id)

    text = "<b>📋 وضعیت قفل‌های گروه:</b>\n\n"
    active_count = 0

    for key, title in LOCK_TYPES.items():
        status = locks.get(key, False)
        if status:
            text += f"🔒 <b>{title}</b>\n"
            active_count += 1
        else:
            text += f"🔓 {title}\n"

    if active_count == 0:
        text += "\nℹ️ در حال حاضر هیچ قفلی فعال نیست."

    await update.message.reply_text(text, parse_mode="HTML")
    # ==========================================================
# 🧱 GROUP CONTROL SYSTEM — STEP 3
# دستورات فارسی / انگلیسی + پشتیبانی از Alias
# ==========================================================

import re

ALIASES_FILE = "aliases.json"

# ─────────────────────────────── بارگذاری و ذخیره alias ───────────────────────────────

ALIASES = _load_json(ALIASES_FILE, {})

def _save_aliases():
    _save_json(ALIASES_FILE, ALIASES)

# ─────────────────────────────── تابع نگاشت فارسی و Alias ───────────────────────────────

def _map_to_key(name: str) -> str | None:
    """تبدیل نام فارسی، انگلیسی یا alias به کلید قفل"""
    name = name.strip().lower()

    # اول بررسی alias سفارشی
    for k, v in ALIASES.items():
        if name in v:
            return k

    # فارسی‌ها
    for fa, key in PERSIAN_TO_KEY.items():
        if fa in name:
            return key

    # انگلیسی‌ها (مثلاً links, photos, videos)
    for key in LOCK_TYPES:
        if key in name:
            return key

    return None

# ─────────────────────────────── فرمان اصلی قفل / بازکردن ───────────────────────────────

_lock_cmd_regex = re.compile(r"^(قفل|باز ?کردن|lock|unlock)\s+(.+)$")

async def handle_locks_with_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشخیص خودکار قفل یا بازکردن (با alias یا بدون قید 'قفل')"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip().lower()

    # 1️⃣ اگر جمله با "قفل" یا "بازکردن" شروع بشه → روش قبلی
    match = _lock_cmd_regex.match(text)
    if match:
        action, rest = match.groups()
        key = _map_to_key(rest)
        if not key:
            return await update.message.reply_text("⚠️ نام قفل ناشناخته است.")
        if action in ["قفل", "lock"]:
            return await handle_lock(update, context, key)
        else:
            return await handle_unlock(update, context, key)

    # 2️⃣ اگر فقط alias نوشته شده باشه (مثلاً "ببند" یا "بازکن")
    key = _map_to_key(text)
    if key:
        # بررسی می‌کنیم آیا alias شامل واژه‌هایی مثل "باز" یا "آزاد" هست → یعنی بازکردن
        if any(w in text for w in ["باز", "آزاد", "آنلاک", "open", "unlock"]):
            return await handle_unlock(update, context, key)
        else:
            return await handle_lock(update, context, key)

# ─────────────────────────────── افزودن دستور جدید (Alias) ───────────────────────────────


async def handle_add_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """افزودن دستور جدید برای یک قفل (با یا بدون /)"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران و سودوها می‌توانند دستور جدید بسازند.")

    text = update.message.text.strip()

    # حذف بخش اول «افزودن دستور» یا «/addalias»
    if text.startswith("افزودن دستور"):
        text = text.replace("افزودن دستور", "", 1).strip()
    elif text.startswith("/addalias"):
        text = text.replace("/addalias", "", 1).strip()

    # حالا متن باقی‌مانده مثلاً میشه: "لینک لینک‌بند"
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return await update.message.reply_text(
            "📘 مثال:\n<code>افزودن دستور لینک لینک‌بند</code>",
            parse_mode="HTML"
        )

    lock_name = parts[0].lower()
    alias_word = parts[1].lower()

    key = _map_to_key(lock_name)
    if not key:
        return await update.message.reply_text("⚠️ قفل مورد نظر یافت نشد.")

    aliases_for_lock = ALIASES.get(key, [])
    if alias_word in aliases_for_lock:
        return await update.message.reply_text("⚠️ این دستور از قبل ثبت شده است.")

    aliases_for_lock.append(alias_word)
    ALIASES[key] = aliases_for_lock
    _save_aliases()

    await update.message.reply_text(
        f"🧩 <b>Alias جدید ثبت شد!</b>\n"
        f"🔒 قفل: <b>{LOCK_TYPES[key]}</b>\n"
        f"🆕 دستور جدید: <code>{alias_word}</code>",
        parse_mode="HTML"
    )

# ─────────────────────────────── لیست Alias‌ها ───────────────────────────────

async def handle_list_aliases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش تمام alias های ثبت‌شده"""
    if not ALIASES:
        return await update.message.reply_text("ℹ️ هیچ دستور سفارشی ثبت نشده است.")
    
    text = "<b>🧩 دستورات سفارشی (Alias):</b>\n\n"
    for k, v in ALIASES.items():
        text += f"🔹 <b>{LOCK_TYPES.get(k, k)}</b> → {', '.join(v)}\n"
    
    await update.message.reply_text(text, parse_mode="HTML")

# ─────────────────────────────── ساخت پنل با ⛔ / ✅ ───────────────────────────────

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest


def _generate_lock_panel(chat_id: int) -> InlineKeyboardMarkup:
    """ساخت دکمه‌های وضعیت قفل‌ها با ⛔ / ✅ فقط با دکمه بستن"""
    locks = _locks_get(chat_id)
    keyboard = []
    row = []
    i = 0

    for key, title in LOCK_TYPES.items():
        status = locks.get(key, False)
        icon = "⛔" if status else "✅"
        button = InlineKeyboardButton(
            f"{icon} {title}",
            callback_data=f"locktoggle|{key}"
        )
        row.append(button)
        i += 1
        if i % 2 == 0:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    # فقط دکمه بستن در پایین پنل
    keyboard.append([InlineKeyboardButton("❌ بستن پنل", callback_data="lockclose")])

    return InlineKeyboardMarkup(keyboard)


# ─────────────────────────────── کنترل دکمه‌های پنل ───────────────────────────────

async def handle_lock_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت دکمه‌های پنل قفل‌ها با آیکون ⛔ / ✅ و بستن"""
    query = update.callback_query
    user = query.from_user
    chat = query.message.chat

    # بررسی سطح دسترسی مدیر
    if not await _is_admin_or_sudo_uid(context, chat.id, user.id):
        return await query.answer("🚫 فقط مدیران مجازند.", show_alert=True)

    data = query.data

    # ✅ دکمه بستن
    if data == "lockclose":
        try:
            await query.message.delete()
        except:
            try:
                await query.edit_message_text("✅ پنل بسته شد.")
            except:
                pass
        return await query.answer("❌ پنل بسته شد.", show_alert=False)

    # ⛔ / ✅ تغییر وضعیت قفل
    if data.startswith("locktoggle|"):
        key = data.split("|")[1]
        locks = _locks_get(chat.id)
        current = locks.get(key, False)
        _locks_set(chat.id, key, not current)

        new_status = "⛔ فعال شد" if not current else "✅ غیرفعال شد"
        await query.answer(f"{LOCK_TYPES[key]} {new_status}", show_alert=False)

        # بروزرسانی دکمه‌ها
        try:
            await query.edit_message_reply_markup(reply_markup=_generate_lock_panel(chat.id))
        except BadRequest as e:
            if "Message is not modified" in str(e):
                pass
            else:
                print(f"⚠️ خطا در تغییر وضعیت قفل: {e}")


# ─────────────────────────────── نمایش پنل وضعیت قفل‌ها ───────────────────────────────

async def handle_lock_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش پنل وضعیت قفل‌ها با دکمه‌های ⛔ / ✅"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    chat = update.effective_chat
    locks = _locks_get(chat.id)
    active = [LOCK_TYPES[k] for k, v in locks.items() if v]

    text = "<b>📋 وضعیت قفل‌های گروه</b>\n\n"
    if active:
        text += "🔒 قفل‌های فعال:\n" + "\n".join([f"• {x}" for x in active]) + "\n\n"
    else:
        text += "✅ در حال حاضر هیچ قفلی فعال نیست.\n\n"

    text += "برای فعال یا غیرفعال کردن، روی دکمه‌های زیر کلیک کنید 👇"

    await update.message.reply_text(
        text,
        reply_markup=_generate_lock_panel(chat.id),
        parse_mode="HTML"
    )
