# ====================== ⚙️ پنل تنظیمات + راهنما + قفل‌های زنده ======================
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from group_control.group_control import (
    _locks_get, _locks_set, _save_json,
    group_data, GROUP_CTRL_FILE, LOCK_TYPES
)

# 🌟 عنوان اصلی
MAIN_TITLE = "⚙️ <b>پنل تنظیمات ربات</b>\n\nاز منوی زیر گزینه مورد نظر را انتخاب کنید 👇"

# ====================== گروه‌بندی دقیق قفل‌ها ======================
ORDERED_KEYS = [
    "links", "usernames", "mention", "ads", "forward",
    "tgservices", "bots", "join", "joinmsg",
    "media", "photos", "videos", "gifs", "stickers",
    "files", "audio", "voices", "vmsgs", "caption",
    "text", "emoji", "english", "arabic", "edit", "reply", "all"
]

PAGES_BASE = {
    1: ORDERED_KEYS[0:9],
    2: ORDERED_KEYS[9:19],
    3: ORDERED_KEYS[19:]
}


def _build_pages_from_locktypes() -> dict:
    pages = {p: list(keys) for p, keys in PAGES_BASE.items()}
    all_defined = set(LOCK_TYPES.keys())
    already_listed = set(ORDERED_KEYS)
    extra = [k for k in all_defined if k not in already_listed]
    if extra:
        pages[3].extend(extra)
    return pages


# ====================== 🎨 منوی اصلی ======================
async def Tastatur_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text(
            "❌ این پنل فقط در داخل گروه‌ها قابل استفاده است!",
            parse_mode="HTML"
        )

    keyboard = [
        [InlineKeyboardButton("⚙️ تنظیمات", callback_data="Tastatur_settings")],
        [InlineKeyboardButton("📘 راهنما", callback_data="Tastatur_help")],
        [InlineKeyboardButton("❌ بستن پنل", callback_data="Tastatur_close")]
    ]

    if update.message:
        await update.message.reply_text(
            MAIN_TITLE,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.callback_query.edit_message_text(
            MAIN_TITLE,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# ====================== 🎛 مدیریت دکمه‌ها ======================
async def Tastatur_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "Tastatur_close":
        return await query.message.delete()

    if data == "Tastatur_back":
        return await Tastatur_menu(update, context)

    # تنظیمات ← قفل‌ها
    if data == "Tastatur_settings":
        return await show_settings_menu(query)

    if data == "Tastatur_locks":
        return await show_lock_page(query, 1)

    # راهنما
    if data == "Tastatur_help":
        return await show_help_menu(query)

    if data.startswith("help_section:"):
        section = data.split(":", 1)[1]
        return await show_help_section(query, section)


# ====================== ⚙️ تنظیمات ======================
async def show_settings_menu(query):
    text = "⚙️ <b>تنظیمات گروه</b>\n\nیکی از گزینه‌های زیر را انتخاب کنید 👇"
    keyboard = [
        [InlineKeyboardButton("🔒 قفل‌ها", callback_data="Tastatur_locks")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")]
    ]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


# ====================== 📘 راهنما ======================
async def show_help_menu(query):
    """منوی اصلی راهنما"""
    text = "📘 <b>راهنمای کامل ربات مدیریت گروه</b>\n\nبخش مورد نظر را انتخاب کنید 👇"
    keyboard = [
        [InlineKeyboardButton("🔐 قفل‌ها", callback_data="help_section:locks")],
        [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="help_section:users")],
        [InlineKeyboardButton("🧹 پاکسازی و پین", callback_data="help_section:cleanpin")],
        [InlineKeyboardButton("📛 فیلترها و اخطارها", callback_data="help_section:filters")],
        [InlineKeyboardButton("🧩 سایر تنظیمات", callback_data="help_section:other")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")]
    ]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def show_help_section(query, section):
    """نمایش محتوای هر بخش راهنما"""
    help_texts = {
        "locks": (
            "🔐 <b>مدیریت قفل‌ها</b>\n\n"
            "برای فعال یا غیرفعال کردن هر قفل، بنویس:\n"
            "• <code>قفل لینک</code>\n• <code>باز کردن لینک</code>\n\n"
            "برخی قفل‌ها:\n"
            "▫️ لینک‌ها\n▫️ عکس‌ها\n▫️ ویدیو\n▫️ فایل\n▫️ فوروارد\n▫️ تبلیغ (تبچی)\n▫️ کپشن\n▫️ ریپلای\n▫️ متن\n\n"
            "همچنین می‌تونی از طریق پنل قفل‌ها به‌صورت زنده مدیریت کنی."
        ),
        "users": (
            "👥 <b>مدیریت کاربران</b>\n\n"
            "• بن کاربر → <code>بن</code> + ریپلای\n"
            "• رفع‌بن → <code>حذف بن</code>\n"
            "• سکوت → <code>سکوت</code> (اختیاری: 5 دقیقه)\n"
            "• حذف سکوت → <code>حذف سکوت</code>\n"
            "• اخطار → <code>اخطار</code> (سه اخطار = بن)\n"
            "• لیست‌ها: <code>لیست بن</code> | <code>لیست سکوت</code> | <code>لیست اخطار</code>"
        ),
        "cleanpin": (
            "🧹 <b>پاکسازی و پین</b>\n\n"
            "• پاکسازی 100 پیام آخر → <code>پاکسازی 100</code>\n"
            "• پاکسازی کامل → <code>پاکسازی کامل</code>\n"
            "• پاکسازی پیام‌های یک کاربر → ریپلای بزن و بنویس <code>پاکسازی</code>\n\n"
            "📌 پین پیام:\n"
            "• پین موقت: ریپلای + <code>پین 10</code> (۱۰ دقیقه)\n"
            "• حذف پین: <code>حذف پین</code>"
        ),
        "filters": (
            "📛 <b>فیلتر کلمات</b>\n\n"
            "• افزودن فیلتر: <code>افزودن فیلتر کلمه</code>\n"
            "• حذف فیلتر: <code>حذف فیلتر کلمه</code>\n"
            "• مشاهده لیست: <code>فیلترها</code>\n\n"
            "⚠️ پیام‌هایی که شامل کلمات فیلترشده باشند، خودکار حذف می‌شوند."
        ),
        "other": (
            "🧩 <b>سایر تنظیمات</b>\n\n"
            "• افزودن مدیر: ریپلای + <code>افزودن مدیر</code>\n"
            "• حذف مدیر: ریپلای + <code>حذف مدیر</code>\n"
            "• قفل گروه کامل: <code>قفل گروه</code>\n"
            "• باز کردن گروه: <code>بازکردن گروه</code>\n"
            "• فعال کردن قفل خودکار: <code>قفل خودکار گروه 23:00 07:00</code>\n"
            "• لغو قفل خودکار: <code>غیرفعال کردن قفل خودکار</code>"
        )
    }

    text = help_texts.get(section, "❌ بخش یافت نشد.")
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_help")]]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


# ====================== 🔐 بخش قفل‌ها (زنده + صفحه‌بندی) ======================
async def show_lock_page(query, page: int = 1):
    chat_id = query.message.chat.id
    locks = _locks_get(chat_id)
    PAGES = _build_pages_from_locktypes()
    page = page if page in PAGES else 1

    keyboard = []
    for key in PAGES[page]:
        if key not in LOCK_TYPES:
            continue
        state = bool(locks.get(key, False))
        label = LOCK_TYPES[key]
        icon = "✅ فعال" if state else "❌ غیرفعال"
        keyboard.append([InlineKeyboardButton(f"{label} | {icon}", callback_data=f"toggle_lock:{key}")])

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⬅️ صفحه قبل", callback_data=f"lock_page:{page-1}"))
    if page < max(PAGES.keys()):
        nav.append(InlineKeyboardButton("صفحه بعد ➡️", callback_data=f"lock_page:{page+1}"))
    if nav:
        keyboard.append(nav)

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_settings")])

    text = f"🔐 <b>مدیریت قفل‌های گروه — صفحه {page}</b>\n\nبرای فعال/غیرفعال کردن روی هر مورد بزن 👇"
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


# 🧭 جابه‌جایی صفحات
async def handle_lock_page_switch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()
    if data.startswith("lock_page:"):
        page = int(data.split(":")[1])
        await show_lock_page(query, page)


# 🔄 تغییر وضعیت قفل‌ها
async def toggle_lock_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()
    if not data.startswith("toggle_lock:"):
        return

    chat_id = query.message.chat.id
    lock_key = data.split(":", 1)[1]
    if lock_key not in LOCK_TYPES:
        return

    locks = _locks_get(chat_id)
    new_state = not locks.get(lock_key, False)
    _locks_set(chat_id, lock_key, new_state)
    _save_json(GROUP_CTRL_FILE, group_data)

    PAGES = _build_pages_from_locktypes()
    page_to_show = 1
    for p, keys in PAGES.items():
        if lock_key in keys:
            page_to_show = p
            break

    await show_lock_page(query, page_to_show)
