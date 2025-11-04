# ==========================================================
# 🧱 GROUP CONTROL SYSTEM — STEP 1
# پایه‌ها + فایل داده‌ها + قفل‌ها + سطح دسترسی مدیر / سودو
# ==========================================================

import os, json
from telegram import Update
from telegram.ext import ContextTypes

# ─────────────────────────────── مسیر فایل داده‌ها ───────────────────────────────
GROUP_CTRL_FILE = "group_control.json"

# اطمینان از وجود فایل داده
if not os.path.exists(GROUP_CTRL_FILE):
    with open(GROUP_CTRL_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

# ─────────────────────────────── توابع ذخیره / بارگذاری ───────────────────────────────
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
SUDO_IDS = [8588347189]  # 👈 آیدی خودت رو اینجا بگذار


# ─────────────────────────────── تعریف قفل‌ها (۲۵ مورد) ───────────────────────────────
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
    "ads": "تبچی/تبلیغ",
    "usernames": "یوزرنیم/تگ",
    "mention": "منشن با @",
    "bots": "افزودن ربات",
    "join": "ورود عضو جدید",
    "tgservices": "پیام سیستمی تلگرام",
    "joinmsg": "پیام خوش‌آمدگویی",
    "arabic": "حروف عربی",
    "english": "حروف انگلیسی",
    "text": "پیام متنی",
    "audio": "آهنگ/موزیک",
    "emoji": "ایموجی",
    "caption": "کپشن",
    "edit": "ویرایش پیام",
    "reply": "ریپلای/پاسخ",
}

# ─────────────────────────────── نگاشت فارسی → کلید ───────────────────────────────
PERSIAN_TO_KEY = {
    "گروه": "group",
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


# ─────────────────────────────── توابع قفل‌ها ───────────────────────────────
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


# ─────────────────────────────── بررسی سطح دسترسی ───────────────────────────────
async def _is_admin_or_sudo_uid(context, chat_id: int, user_id: int) -> bool:
    """بررسی اینکه کاربر مدیر یا سودو است"""
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except:
        return False


async def is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """بررسی مجاز بودن فرستنده پیام"""
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


# ─────────────────────────────── پیام خطا برای قفل نامعتبر ───────────────────────────────
async def _unknown_lock_error(update: Update, name: str):
    """نمایش پیام خطای قفل ناشناخته"""
    return await update.message.reply_text(
        f"⚠️ نام قفل «<b>{name}</b>» ناشناخته است.\n"
        "لطفاً نام قفل را به‌درستی وارد کنید یا از دستور «وضعیت قفل‌ها» استفاده کنید.",
        parse_mode="HTML"
    )
    # ==========================================================
# 🧱 GROUP CONTROL SYSTEM — STEP 2
# فعال / غیرفعال کردن قفل‌ها + قفل گروه با طراحی بنری زیبا
# ==========================================================

# ─────────────────────────────── فعال کردن قفل تکی ───────────────────────────────
async def handle_lock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    """فعال‌سازی قفل مورد نظر"""
    if key not in LOCK_TYPES:
        return await _unknown_lock_error(update, key)

    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجاز به اجرای این دستور هستند.")

    chat = update.effective_chat
    locks = _locks_get(chat.id)

    if locks.get(key):
        return await update.message.reply_text(
            f"⚠️ قفل <b>{LOCK_TYPES[key]}</b> از قبل فعال بوده است.",
            parse_mode="HTML"
        )

    _locks_set(chat.id, key, True)
    await update.message.reply_text(
        f"✅ قفل <b>{LOCK_TYPES[key]}</b> با موفقیت فعال شد.",
        parse_mode="HTML"
    )


# ─────────────────────────────── غیرفعال کردن قفل تکی ───────────────────────────────
async def handle_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    """غیرفعال‌سازی قفل"""
    if key not in LOCK_TYPES:
        return await _unknown_lock_error(update, key)

    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجاز به اجرای این دستور هستند.")

    chat = update.effective_chat
    locks = _locks_get(chat.id)

    if not locks.get(key):
        return await update.message.reply_text(
            f"⚠️ قفل <b>{LOCK_TYPES[key]}</b> از قبل غیرفعال بوده است.",
            parse_mode="HTML"
        )

    _locks_set(chat.id, key, False)
    await update.message.reply_text(
        f"🔓 قفل <b>{LOCK_TYPES[key]}</b> با موفقیت باز شد.",
        parse_mode="HTML"
    )

from telegram import ChatPermissions

# ─────────────────────────────── قفل کامل گروه ───────────────────────────────
async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE, cmd_text: str = "قفل گروه"):
    """بستن کامل گروه با بررسی وضعیت قبلی و طراحی زیبا"""
    chat = update.effective_chat
    user = update.effective_user

    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند گروه را ببندند.")

    locks = _locks_get(chat.id)
    if locks.get("group"):
        return await update.message.reply_text("🔒 گروه از قبل بسته بوده است.", parse_mode="HTML")

    try:
        await context.bot.set_chat_permissions(
            chat_id=chat.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        _locks_set(chat.id, "group", True)

        text = (
            "━━━━━━━━━━━━━━━\n"
            "🔒 <b>گروه بسته شد</b>\n"
            f"📌 <b>دستور:</b> <code>{cmd_text}</code>\n"
            f"👮 <b>مدیر:</b> <a href='tg://user?id={user.id}'>{user.first_name}</a>\n"
            "🚫 <b>تا اطلاع ثانوی بسته است</b>\n"
            "━━━━━━━━━━━━━━━"
        )

        await update.message.reply_text(text, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بستن گروه:\n<code>{e}</code>", parse_mode="HTML")

# ─────────────────────────────── باز کردن گروه ───────────────────────────────
async def unlock_group(update: Update, context: ContextTypes.DEFAULT_TYPE, cmd_text: str = "باز کردن گروه"):
    """باز کردن کامل گروه با بررسی وضعیت قبلی و طراحی زیبا"""
    chat = update.effective_chat
    user = update.effective_user

    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند گروه را باز کنند.")

    locks = _locks_get(chat.id)
    if not locks.get("group"):
        return await update.message.reply_text("✅ گروه از قبل باز بوده است.", parse_mode="HTML")

    try:
        await context.bot.set_chat_permissions(
            chat_id=chat.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_voice_notes=True,
                can_invite_users=True,
                can_send_polls=True,
                can_pin_messages=False
            )
        )
        _locks_set(chat.id, "group", False)

        text = (
            "━━━━━━━━━━━━━━━\n"
            "✅ <b>گروه باز شد</b>\n"
            f"📌 <b>دستور:</b> <code>{cmd_text}</code>\n"
            f"👮 <b>مدیر:</b> <a href='tg://user?id={user.id}'>{user.first_name}</a>\n"
            "💬 <b>اکنون همه کاربران می‌توانند پیام ارسال کنند</b>\n"
            "━━━━━━━━━━━━━━━"
        )

        await update.message.reply_text(text, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در باز کردن گروه:\n<code>{e}</code>", parse_mode="HTML")
# ─────────────────────────────── نمایش وضعیت قفل‌ها ───────────────────────────────
async def handle_locks_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش وضعیت تمام قفل‌ها در گروه"""
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
# aliasها + فرمان هوشمند قفل‌ها + پنل وضعیت با ⛔ / ✅
# ==========================================================

ALIASES_FILE = "aliases.json"
ALIASES = _load_json(ALIASES_FILE, {})

def _save_aliases():
    _save_json(ALIASES_FILE, ALIASES)


# ─────────────────────────────── نگاشت فارسی / alias به کلید ───────────────────────────────
def _map_to_key(name: str) -> str | None:
    """تبدیل متن فارسی، انگلیسی یا alias به کلید قفل"""
    name = name.strip().lower()

    # aliasهای ثبت‌شده
    for k, v in ALIASES.items():
        if name in v:
            return k

    # فارسی‌ها
    for fa, key in PERSIAN_TO_KEY.items():
        if fa in name:
            return key

    # انگلیسی‌ها (مثل links, photos, videos)
    for key in LOCK_TYPES:
        if key in name:
            return key

    return None


# ─────────────────────────────── فرمان هوشمند قفل / بازکردن ───────────────────────────────
import re
_lock_cmd_regex = re.compile(r"^(قفل|باز ?کردن|lock|unlock)\s+(.+)$")

async def handle_locks_with_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشخیص خودکار قفل / بازکردن (با alias یا بدون واژه قفل)"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip().lower()

    # 🔹 روش ۱: اگر پیام با «قفل» یا «باز کردن» شروع شده باشد
    match = _lock_cmd_regex.match(text)
    if match:
        action, rest = match.groups()
        key = _map_to_key(rest)

        if not key:
            return await _unknown_lock_error(update, rest)

        # اگر قفل گروه بود
        if key == "group":
            if action in ["قفل", "lock"]:
                return await lock_group(update, context, text)
            else:
                return await unlock_group(update, context, text)

        # بقیه قفل‌ها
        if action in ["قفل", "lock"]:
            return await handle_lock(update, context, key)
        else:
            return await handle_unlock(update, context, key)

    # 🔹 روش ۲: اگر فقط alias یا نام قفل نوشته شده باشد (مثلاً «ببند» یا «بازکن»)
    key = _map_to_key(text)
    if key:
        if any(w in text for w in ["باز", "آزاد", "open", "unlock"]):
            if key == "group":
                return await unlock_group(update, context, text)
            return await handle_unlock(update, context, key)
        else:
            if key == "group":
                return await lock_group(update, context, text)
            return await handle_lock(update, context, key)


# ─────────────────────────────── افزودن alias جدید ───────────────────────────────
async def handle_add_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """افزودن دستور جدید برای یک قفل"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند دستور جدید بسازند.")

    text = update.message.text.strip()

    # حذف عبارت آغازین
    if text.startswith("افزودن دستور"):
        text = text.replace("افزودن دستور", "", 1).strip()
    elif text.startswith("/addalias"):
        text = text.replace("/addalias", "", 1).strip()

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
        return await _unknown_lock_error(update, lock_name)

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


# ─────────────────────────────── لیست alias‌ها ───────────────────────────────
async def handle_list_aliases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش تمام aliasهای ثبت‌شده"""
    if not ALIASES:
        return await update.message.reply_text("ℹ️ هنوز هیچ دستور سفارشی ثبت نشده است.")

    text = "<b>🧩 دستورات سفارشی (Alias):</b>\n\n"
    for k, v in ALIASES.items():
        text += f"🔹 <b>{LOCK_TYPES.get(k, k)}</b> → {', '.join(v)}\n"

    await update.message.reply_text(text, parse_mode="HTML")


# ─────────────────────────────── ساخت پنل قفل‌ها با ⛔ / ✅ ───────────────────────────────
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

def _generate_lock_panel(chat_id: int) -> InlineKeyboardMarkup:
    """ساخت دکمه‌های وضعیت قفل‌ها با ⛔ / ✅"""
    locks = _locks_get(chat_id)
    keyboard, row = [], []
    for i, (key, title) in enumerate(LOCK_TYPES.items()):
        icon = "⛔" if locks.get(key, False) else "✅"
        row.append(InlineKeyboardButton(f"{icon} {title}", callback_data=f"locktoggle|{key}"))
        if i % 2 == 1:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ بستن پنل", callback_data="lockclose")])
    return InlineKeyboardMarkup(keyboard)


# ─────────────────────────────── کنترل کلیک پنل ───────────────────────────────
async def handle_lock_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت دکمه‌های پنل قفل‌ها"""
    query = update.callback_query
    user = query.from_user
    chat = query.message.chat

    if not await _is_admin_or_sudo_uid(context, chat.id, user.id):
        return await query.answer("🚫 فقط مدیران مجازند.", show_alert=True)

    data = query.data

    # بستن پنل
    if data == "lockclose":
        try:
            await query.message.delete()
        except:
            try:
                await query.edit_message_text("✅ پنل بسته شد.")
            except:
                pass
        return await query.answer("❌ پنل بسته شد.", show_alert=False)

    # تغییر وضعیت قفل
    if data.startswith("locktoggle|"):
        key = data.split("|")[1]
        current = _locks_get(chat.id).get(key, False)
        _locks_set(chat.id, key, not current)

        status_msg = "⛔ فعال شد" if not current else "✅ غیرفعال شد"
        await query.answer(f"{LOCK_TYPES[key]} {status_msg}", show_alert=False)

        try:
            await query.edit_message_reply_markup(reply_markup=_generate_lock_panel(chat.id))
        except BadRequest as e:
            if "Message is not modified" in str(e):
                pass


# ─────────────────────────────── نمایش پنل قفل‌ها ───────────────────────────────
async def handle_lock_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش پنل وضعیت قفل‌ها"""
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    chat = update.effective_chat
    locks = _locks_get(chat.id)
    active = [LOCK_TYPES[k] for k, v in locks.items() if v]

    text = "<b>📋 وضعیت قفل‌های گروه</b>\n\n"
    if active:
        text += "🔒 قفل‌های فعال:\n" + "\n".join([f"• {x}" for x in active]) + "\n\n"
    else:
        text += "✅ هیچ قفلی فعال نیست.\n\n"

    text += "برای فعال یا غیرفعال کردن، روی دکمه‌های زیر بزنید 👇"

    await update.message.reply_text(
        text,
        reply_markup=_generate_lock_panel(chat.id),
        parse_mode="HTML"
)
