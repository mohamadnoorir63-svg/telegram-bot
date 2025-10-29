# ====================== ⚙️ پنل تنظیمات ساده با کنترل زنده قفل‌ها ======================
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from group_control.group_control import (
    _locks_get, _locks_set, _save_json,
    group_data, GROUP_CTRL_FILE, LOCK_TYPES
)

# 🌟 عنوان اصلی
MAIN_TITLE = "⚙️ <b>پنل تنظیمات ربات</b>\n\nاز منوی زیر گزینه مورد نظر را انتخاب کنید 👇"

# ====================== 👇 گروه‌بندی دقیق ۲۵ قفل واقعی (طبق group_control) ======================
# ترتیب و دسته‌بندی دلخواه ولی فقط از کلیدهای واقعی استفاده شده
ORDERED_KEYS = [
    # صفحه 1 — لینک و عضویت و سرویس‌ها
    "links", "usernames", "mention", "ads", "forward",
    "tgservices", "bots", "join", "joinmsg",
    # صفحه 2 — رسانه و فایل‌ها
    "media", "photos", "videos", "gifs", "stickers",
    "files", "audio", "voices", "vmsgs", "caption",
    # صفحه 3 — متن و زبان و رفتار
    "text", "emoji", "english", "arabic", "edit", "reply", "all"
]
# از روی ترتیب بالا، ۳ صفحه می‌سازیم
PAGES_BASE = {
    1: ORDERED_KEYS[0:9],
    2: ORDERED_KEYS[9:19],
    3: ORDERED_KEYS[19:]
}

def _build_pages_from_locktypes() -> dict:
    """اگر در LOCK_TYPES چیزی وجود داشت که در ORDERED_KEYS نبود،
    خودکار به صفحه 3 اضافه می‌کنیم تا هیچ قفلی بی‌دکمه نماند."""
    pages = {p: list(keys) for p, keys in PAGES_BASE.items()}

    all_defined = set(LOCK_TYPES.keys())
    already_listed = set(ORDERED_KEYS)
    extra = [k for k in all_defined if k not in already_listed]
    if extra:
        pages[3].extend(extra)
    return pages

# ================ UI =================

async def Tastatur_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text(
            "❌ این پنل فقط در داخل گروه‌ها قابل استفاده است!",
            parse_mode="HTML"
        )

    keyboard = [
        [InlineKeyboardButton("🔒 قفل‌ها", callback_data="Tastatur_locks")],
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


# 🎛 مدیریت دکمه‌ها
async def Tastatur_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "Tastatur_close":
        return await query.message.delete()

    if data == "Tastatur_back":
        return await Tastatur_menu(update, context)

    if data == "Tastatur_locks":
        return await show_lock_page(query, 1)


# ====================== 🔐 بخش قفل‌ها (سه‌صفحه‌ای) ======================

async def show_lock_page(query, page: int = 1):
    """نمایش صفحه قفل‌ها با وضعیت زنده"""
    chat_id = query.message.chat.id
    locks = _locks_get(chat_id)
    PAGES = _build_pages_from_locktypes()

    # اگر صفحه در بازه نبود، بیار صفحه 1
    page = page if page in PAGES else 1

    keyboard = []
    for key in PAGES[page]:
        # فقط کلیدهایی را نشان می‌دهیم که در LOCK_TYPES تعریف شده باشند (برچسب فارسی داشته باشند)
        if key not in LOCK_TYPES:
            continue
        state = bool(locks.get(key, False))
        label = LOCK_TYPES[key]          # فارسی
        icon  = "✅ فعال" if state else "❌ غیرفعال"
        # یک‌ستونه (خواناتر با متن فارسی)
        keyboard.append([InlineKeyboardButton(f"{label} | {icon}", callback_data=f"toggle_lock:{key}")])

    # ناوبری صفحات
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⬅️ صفحه قبل", callback_data=f"lock_page:{page-1}"))
    if page < max(PAGES.keys()):
        nav.append(InlineKeyboardButton("صفحه بعد ➡️", callback_data=f"lock_page:{page+1}"))
    if nav:
        keyboard.append(nav)

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")])

    text = f"🔐 <b>مدیریت قفل‌های گروه — صفحه {page}</b>\n\nبرای فعال/غیرفعال کردن، روی هر مورد بزن 👇"
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


# 🧭 جابه‌جایی صفحات
async def handle_lock_page_switch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()
    if data.startswith("lock_page:"):
        page = int(data.split(":")[1])
        await show_lock_page(query, page)


# 🔄 تغییر وضعیت قفل‌ها (زنده)
async def toggle_lock_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if not data.startswith("toggle_lock:"):
        return

    chat_id = query.message.chat.id
    lock_key = data.split(":", 1)[1]

    # فقط کلیدهای معتبر
    if lock_key not in LOCK_TYPES:
        return

    # تغییر وضعیت
    locks = _locks_get(chat_id)
    new_state = not locks.get(lock_key, False)
    _locks_set(chat_id, lock_key, new_state)
    _save_json(GROUP_CTRL_FILE, group_data)

    # تشخیص اینکه این کلید در کدام صفحه است
    PAGES = _build_pages_from_locktypes()
    page_to_show = 1
    for p, keys in PAGES.items():
        if lock_key in keys:
            page_to_show = p
            break

    # رفرش همان صفحه
    await show_lock_page(query, page_to_show)
