# ==========================================================
# 🧱 GROUP CONTROL SYSTEM — STEP 1
# پایه‌ها + فایل ذخیره + قفل‌ها
# ==========================================================

import os, json
from telegram import Update
from telegram.ext import ContextTypes

# ─────────────────────────────── مسیر فایل‌ها ───────────────────────────────
GROUP_CTRL_FILE = "group_control.json"
ALIASES_FILE = "aliases.json"

# ─────────────────────────────── تابع بارگذاری / ذخیره ───────────────────────────────

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

# ─────────────────────────────── داده‌ها ───────────────────────────────

group_data = _load_json(GROUP_CTRL_FILE, {})
ALIASES = _load_json(ALIASES_FILE, {})

SUDO_IDS = [8588347189]  # 👈 آیدی خودت

# ─────────────────────────────── قفل‌ها ───────────────────────────────

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
    "media": "همه رسانه‌ها",
    "forward": "فوروارد",
    "ads": "تبچی/تبلیغ",
    "usernames": "یوزرنیم/تگ",
    "mention": "منشن",
    "bots": "افزودن ربات",
    "join": "ورود کاربر",
    "tgservices": "پیام سیستمی تلگرام",
    "joinmsg": "پیام خوش‌آمد",
    "arabic": "حروف عربی",
    "english": "حروف انگلیسی",
    "text": "متن",
    "audio": "آهنگ",
    "emoji": "ایموجی",
    "caption": "کپشن",
    "edit": "ویرایش پیام",
    "reply": "ریپلای",
}

# ─────────────────────────────── نگاشت فارسی به کلید ───────────────────────────────

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
    g = group_data.get(str(chat_id), {})
    return g.get("locks", {})

def _locks_set(chat_id: int, key: str, status: bool):
    cid = str(chat_id)
    g = group_data.get(cid, {})
    locks = g.get("locks", {})
    locks[key] = bool(status)
    g["locks"] = locks
    group_data[cid] = g
    _save_json(GROUP_CTRL_FILE, group_data)

def _save_aliases():
    _save_json(ALIASES_FILE, ALIASES)
    # ==========================================================
# 🧱 GROUP CONTROL SYSTEM — STEP 2
# فعال/غیرفعال کردن قفل‌ها + قفل گروه + alias هوشمند
# ==========================================================

import re
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes

# ─────────────────────────────── بررسی سطح دسترسی ───────────────────────────────
async def _is_admin_or_sudo_uid(context, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except:
        return False

async def is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
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


# ─────────────────────────────── فعال/غیرفعال کردن قفل تکی ───────────────────────────────
async def handle_lock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    if key not in LOCK_TYPES:
        return await update.message.reply_text("⚠️ قفل مورد نظر یافت نشد.")
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران و سودوها می‌توانند از این دستور استفاده کنند.")

    chat = update.effective_chat
    locks = _locks_get(chat.id)
    if locks.get(key):
        return await update.message.reply_text(f"🔒 قفل <b>{LOCK_TYPES[key]}</b> از قبل فعال بوده است.", parse_mode="HTML")

    _locks_set(chat.id, key, True)
    await update.message.reply_text(f"✅ قفل <b>{LOCK_TYPES[key]}</b> با موفقیت فعال شد.", parse_mode="HTML")


async def handle_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    if key not in LOCK_TYPES:
        return await update.message.reply_text("⚠️ قفل مورد نظر یافت نشد.")
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران و سودوها می‌توانند از این دستور استفاده کنند.")

    chat = update.effective_chat
    locks = _locks_get(chat.id)
    if not locks.get(key):
        return await update.message.reply_text(f"🔓 قفل <b>{LOCK_TYPES[key]}</b> از قبل باز بوده است.", parse_mode="HTML")

    _locks_set(chat.id, key, False)
    await update.message.reply_text(f"🔓 قفل <b>{LOCK_TYPES[key]}</b> با موفقیت باز شد.", parse_mode="HTML")


# ─────────────────────────────── قفل و باز کردن کل گروه ───────────────────────────────

async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE, cmd_text="قفل گروه"):
    """بستن کامل گروه با طراحی زیبا"""
    chat = update.effective_chat
    user = update.effective_user

    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران می‌توانند گروه را ببندند.")

    try:
        await context.bot.set_chat_permissions(chat.id, ChatPermissions(can_send_messages=False))
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


async def unlock_group(update: Update, context: ContextTypes.DEFAULT_TYPE, cmd_text="باز کردن گروه"):
    """باز کردن گروه با طراحی زیبا"""
    chat = update.effective_chat
    user = update.effective_user

    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران می‌توانند گروه را باز کنند.")

    try:
        await context.bot.set_chat_permissions(
            chat.id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
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


# ─────────────────────────────── alias و دستورات هوشمند ───────────────────────────────

def _map_to_key(name: str) -> str | None:
    """تبدیل متن (فارسی، انگلیسی یا alias) به کلید قفل"""
    name = name.strip().lower()

    for k, v in ALIASES.items():
        if name in v:
            return k
    for fa, key in PERSIAN_TO_KEY.items():
        if fa in name:
            return key
    for key in LOCK_TYPES:
        if key in name:
            return key
    return None


_lock_cmd_regex = re.compile(r"^(قفل|باز ?کردن|lock|unlock)\s+(.+)$")

async def handle_locks_with_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشخیص خودکار دستور قفل / باز کردن / alias"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip().lower()

    # ۱️⃣ اگر جمله با "قفل" یا "باز کردن" شروع شود
    match = _lock_cmd_regex.match(text)
    if match:
        action, rest = match.groups()
        key = _map_to_key(rest)
        if not key:
            return await update.message.reply_text("⚠️ قفل ناشناخته است.")
        if key == "group":
            if action in ["قفل", "lock"]:
                return await lock_group(update, context, text)
            else:
                return await unlock_group(update, context, text)
        if action in ["قفل", "lock"]:
            return await handle_lock(update, context, key)
        else:
            return await handle_unlock(update, context, key)

    # ۲️⃣ اگر فقط alias باشد
    key = _map_to_key(text)
    if key:
        if any(w in text for w in ["باز", "آزاد", "آنلاک", "unlock", "open"]):
            if key == "group":
                return await unlock_group(update, context, text)
            return await handle_unlock(update, context, key)
        else:
            if key == "group":
                return await lock_group(update, context, text)
            return await handle_lock(update, context, key)
            # ==========================================================
# 🧱 GROUP CONTROL SYSTEM — STEP 3
# پنل گرافیکی قفل‌ها + کنترل دکمه‌ها
# ==========================================================

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

# ─────────────────────────────── ساخت پنل قفل‌ها ───────────────────────────────
def _generate_lock_panel(chat_id: int) -> InlineKeyboardMarkup:
    """ساخت دکمه‌های وضعیت قفل‌ها با ⛔ / ✅ و دکمه بستن"""
    locks = _locks_get(chat_id)
    keyboard, row = [], []
    i = 0

    for key, title in LOCK_TYPES.items():
        status = locks.get(key, False)
        icon = "⛔" if status else "✅"
        button = InlineKeyboardButton(f"{icon} {title}", callback_data=f"locktoggle|{key}")
        row.append(button)
        i += 1
        if i % 2 == 0:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("❌ بستن پنل", callback_data="lockclose")])
    return InlineKeyboardMarkup(keyboard)


# ─────────────────────────────── مدیریت کلیک روی دکمه‌ها ───────────────────────────────
async def handle_lock_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت دکمه‌های پنل قفل‌ها"""
    query = update.callback_query
    user = query.from_user
    chat = query.message.chat

    if not await _is_admin_or_sudo_uid(context, chat.id, user.id):
        return await query.answer("🚫 فقط مدیران مجازند.", show_alert=True)

    data = query.data

    # ❌ بستن پنل
    if data == "lockclose":
        try:
            await query.message.delete()
        except:
            try:
                await query.edit_message_text("✅ پنل بسته شد.")
            except:
                pass
        return await query.answer("پنل بسته شد.", show_alert=False)

    # ⛔ / ✅ تغییر وضعیت قفل
    if data.startswith("locktoggle|"):
        key = data.split("|")[1]
        locks = _locks_get(chat.id)
        current = locks.get(key, False)
        _locks_set(chat.id, key, not current)

        new_status = "⛔ فعال شد" if not current else "✅ غیرفعال شد"
        await query.answer(f"{LOCK_TYPES[key]} {new_status}", show_alert=False)

        try:
            await query.edit_message_reply_markup(reply_markup=_generate_lock_panel(chat.id))
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                print(f"⚠️ خطا در تغییر وضعیت قفل: {e}")


# ─────────────────────────────── نمایش پنل ───────────────────────────────
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

    text += "برای فعال یا غیرفعال کردن روی دکمه‌های زیر کلیک کنید 👇"

    await update.message.reply_text(
        text,
        reply_markup=_generate_lock_panel(chat.id),
        parse_mode="HTML"
                      )
