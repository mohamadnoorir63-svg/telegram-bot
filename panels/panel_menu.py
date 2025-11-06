# ====================== 🌟 پنل مدیریت ربات (کامل و بدون باگ) ======================
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from group_control.group_control import (
    _get_locks, _set_lock, _load_json, LOCK_TYPES, LOCK_FILE
)

# ───────────────────────────── عنوان اصلی ─────────────────────────────
MAIN_TITLE = (
    "🌟 <b>پنل مدیریت گروه</b>\n\n"
    "از منوی زیر یکی از بخش‌ها را انتخاب کنید 👇"
)

# ====================== 🏠 منوی اصلی ======================
async def Tastatur_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text(
            "❌ این پنل فقط در داخل گروه‌ها قابل استفاده است!",
            parse_mode="HTML"
        )

    keyboard = [
        [
            InlineKeyboardButton("⚙️ تنظیمات", callback_data="Tastatur_settings"),
            InlineKeyboardButton("🎮 سرگرمی‌ها", callback_data="Tastatur_fun"),
        ],
        [
            InlineKeyboardButton("👮 مدیریت گروه", callback_data="Tastatur_admin"),
            InlineKeyboardButton("💐 خوشامد", callback_data="Tastatur_welcome"),
        ],
        [InlineKeyboardButton("❌ بستن پنل", callback_data="Tastatur_close")],
    ]

    if update.message:
        return await update.message.reply_text(
            MAIN_TITLE, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    return await update.callback_query.edit_message_text(
        MAIN_TITLE, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ====================== 🔁 روتر دکمه‌ها ======================
async def Tastatur_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "Tastatur_close":
        return await query.message.delete()
    if data == "Tastatur_back":
        return await Tastatur_menu(update, context)
    if data == "Tastatur_settings":
        return await show_settings_menu(query)
    if data.startswith("help_"):
        return await show_help_info(query)
    if data == "Tastatur_fun":
        return await show_fun_menu(query)
    if data == "Tastatur_admin":
        return await show_admin_menu(query)
    if data == "Tastatur_welcome":
        return await show_welcome_menu(query)
    if data == "Tastatur_locks":
        return await show_lock_page(query, 1)
    if data.startswith("toggle_lock:"):
        return await toggle_lock_button(update, context)
    if data.startswith("lock_page:"):
        return await handle_lock_page_switch(update, context)
    if data.startswith("fun_"):
        return await handle_fun_buttons(update, context)

# ====================== ⚙️ زیرمنوی تنظیمات ======================
async def show_settings_menu(query):
    text = (
        "⚙️ <b>بخش تنظیمات و ابزارها</b>\n\n"
        "یکی از گزینه‌های زیر را برای مشاهده راهنما انتخاب کنید 👇"
    )
    keyboard = [
        [
            InlineKeyboardButton("👑 افزودن مدیر", callback_data="help_addadmin"),
            InlineKeyboardButton("📌 پن پیام", callback_data="help_pin"),
        ],
        [
            InlineKeyboardButton("🚫 فیلتر کلمات", callback_data="help_filter"),
            InlineKeyboardButton("🧹 پاکسازی", callback_data="help_clean"),
        ],
        [
            InlineKeyboardButton("📜 اصل", callback_data="help_asl"),
            InlineKeyboardButton("🏷 لقب", callback_data="help_laqab"),
        ],
        [InlineKeyboardButton("🔔 تگ کاربران", callback_data="help_tag")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")],
    ]
    return await query.edit_message_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ====================== 📘 توضیحات کامل ابزارها ======================
HELP_TEXTS = {
    "help_addadmin": (
        "👑 <b>افزودن یا حذف مدیر گروه</b>\n\n"
        "➕ افزودن مدیر:\n"
        "<code>افزودن مدیر</code> (روی پیام فرد ریپلای کن)\n\n"
        "➖ حذف مدیر:\n"
        "<code>حذف مدیر</code>\n\n"
        "📋 نمایش مدیران:\n"
        "<code>لیست مدیران</code>"
    ),
    "help_pin": (
        "📌 <b>پن یا حذف پن پیام</b>\n\n"
        "📍 پن پیام:\n"
        "<code>پن</code> (ریپلای روی پیام)\n\n"
        "❌ حذف پن:\n"
        "<code>حذف پن</code>\n\n"
        "⏰ پن موقت:\n"
        "<code>پن 2 دقیقه</code> / <code>پن 10 ثانیه</code>"
    ),
    "help_filter": (
        "🚫 <b>فیلتر کلمات</b>\n\n"
        "➕ افزودن:\n"
        "<code>فیلتر تست</code>\n"
        "⏰ موقت:\n"
        "<code>فیلتر تست 2 ساعت</code>\n\n"
        "➖ حذف:\n"
        "<code>حذف فیلتر تست</code>\n\n"
        "📋 لیست:\n"
        "<code>لیست فیلتر</code>"
    ),
    "help_clean": (
        "🧹 <b>پاکسازی پیام‌ها</b>\n\n"
        "🧾 دستور:\n"
        "<code>پاکسازی 50</code>\n"
        "→ ۵۰ پیام آخر حذف می‌شوند.\n\n"
        "⚠️ فقط برای مدیران یا سودوها مجاز است."
    ),
    "help_asl": (
        "📜 <b>ثبت اصل</b>\n\n"
        "➕ ثبت:\n"
        "<code>ثبت اصل من اهل صداقتم</code>\n\n"
        "👀 نمایش:\n"
        "<code>اصل من</code>\n\n"
        "❌ حذف:\n"
        "<code>حذف اصل</code>"
    ),
    "help_laqab": (
        "🏷 <b>ثبت لقب</b>\n\n"
        "➕ ثبت:\n"
        "<code>ثبت لقب قهرمان</code>\n\n"
        "👀 نمایش:\n"
        "<code>لقب من</code>\n\n"
        "❌ حذف:\n"
        "<code>حذف لقب</code>"
    ),
    "help_tag": (
        "🔔 <b>تگ کاربران گروه</b>\n\n"
        "👥 تگ همه:\n"
        "<code>تگ همه</code>\n\n"
        "👮 تگ مدیران:\n"
        "<code>تگ مدیران</code>\n\n"
        "💤 تگ غیرفعال‌ها:\n"
        "<code>تگ غیره فعال</code>\n\n"
        "🔥 تگ فعال‌ها:\n"
        "<code>تگ فعال</code>"
    ),
}
async def show_help_info(query):
    data = query.data  # مثلاً help_addadmin یا help_filter
    key = data.strip()

    if key not in HELP_TEXTS:
        return await query.answer("❌ هنوز برای این گزینه راهنما تعریف نشده", show_alert=True)

    text = HELP_TEXTS[key]
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_settings")]]
    return await query.edit_message_text(  # ⬅️ حتماً return داشته باشه
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ====================== 🔒 قفل‌ها ======================
LOCK_PAGE_SIZE = 8

async def show_lock_page(query, page: int = 1):
    chat_id = query.message.chat.id
    locks_data = _get_locks(chat_id)
    all_locks = list(LOCK_TYPES.items())
    total_pages = (len(all_locks) + LOCK_PAGE_SIZE - 1) // LOCK_PAGE_SIZE
    start = (page - 1) * LOCK_PAGE_SIZE
    end = start + LOCK_PAGE_SIZE

    current_page_locks = all_locks[start:end]
    keyboard = []
    for key, label in current_page_locks:
        state = locks_data.get(key, False)
        icon = "✅ فعال" if state else "❌ غیرفعال"
        keyboard.append([InlineKeyboardButton(f"{label} | {icon}", callback_data=f"toggle_lock:{key}")])

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⬅️ قبل", callback_data=f"lock_page:{page-1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton("بعد ➡️", callback_data=f"lock_page:{page+1}"))
    if nav:
        keyboard.append(nav)

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_admin")])

    text = f"🔐 <b>مدیریت قفل‌ها</b>\nصفحه {page}/{total_pages}\n\nبرای تغییر وضعیت هر قفل روی آن بزنید 👇"
    return await query.edit_message_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def toggle_lock_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat.id
    lock_key = data.split(":", 1)[1]

    locks_data = _get_locks(chat_id)
    new_state = not locks_data.get(lock_key, False)
    _set_lock(chat_id, lock_key, new_state)
    await query.answer(f"{LOCK_TYPES.get(lock_key)} {'🔒 فعال شد' if new_state else '🔓 غیرفعال شد'}", show_alert=False)

    index = list(LOCK_TYPES.keys()).index(lock_key)
    page_to_show = index // LOCK_PAGE_SIZE + 1
    return await show_lock_page(query, page_to_show)

async def handle_lock_page_switch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    page = int(query.data.split(":", 1)[1])
    return await show_lock_page(query, page)

# ====================== 🎮 سرگرمی‌ها ======================
FUN_TEXTS = {
    "fun_jok": ("😂 جوک", "با دستور «جوک» یه لطیفه‌ی جدید بگیر 🤣"),
    "fun_fal": ("🎯 فال", "با دستور «فال» فال روزانه دریافت کن 🌟"),
    "fun_font": ("🧩 فونت‌ساز", "با دستور «فونت [متن]» متن خودت رو زیبا کن 🎨"),
    "fun_azan": ("🕋 اذان", "با دستور «اذان تهران» یا «اذان مشهد» زمان اذان رو ببین 🕌"),
    "fun_weather": ("☁️ آب‌وهوا", "با دستور «آب‌وهوا [شهر]» وضعیت آب‌وهوا رو بگیر 🌦"),
}

async def show_fun_menu(query):
    text = "🎮 <b>بخش سرگرمی‌ها و ابزارها</b>\n\nیکی از گزینه‌های زیر را انتخاب کنید 👇"
    keyboard = [
        [InlineKeyboardButton("😂 جوک", callback_data="fun_jok"), InlineKeyboardButton("🎯 فال", callback_data="fun_fal")],
        [InlineKeyboardButton("🧩 فونت", callback_data="fun_font"), InlineKeyboardButton("☁️ آب‌وهوا", callback_data="fun_weather")],
        [InlineKeyboardButton("🕋 اذان", callback_data="fun_azan")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")],
    ]
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_fun_info(query, title, desc):
    kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_fun")]]
    return await query.edit_message_text(
        f"{title}\n\n{desc}", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb)
    )

async def handle_fun_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    key = query.data
    await query.answer()
    if key in FUN_TEXTS:
        title, desc = FUN_TEXTS[key]
        return await show_fun_info(query, title, desc)
    return await query.answer("❌ گزینه نامعتبر است.", show_alert=False)

# ====================== 👮 مدیریت گروه ======================
async def show_admin_menu(query):
    text = (
        "👮 <b>بخش مدیریت گروه</b>\n\n"
        "• بن / رفع‌بن\n"
        "• سکوت / رفع‌سکوت\n"
        "• اخطارها و حذف اخطار\n"
        "• پاکسازی پیام‌ها\n\n"
        "🔒 برای دیدن لیست قفل‌های فعال، از دکمه زیر استفاده کن 👇"
    )
    keyboard = [
        [InlineKeyboardButton("🔒 قفل‌ها", callback_data="Tastatur_locks")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")],
    ]
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# ====================== 💐 خوشامد ======================
async def show_welcome_menu(query):
    text = (
        "💐 <b>سیستم خوشامدگویی</b>\n\n"
        "برای باز کردن پنل تنظیمات خوشامد، دستور زیر را در گروه ارسال کنید:\n"
        "<code>خوشامد</code>\n\n"
        "📋 در آن پنل می‌توانید خوشامد را فعال/غیرفعال کنید، متن و زمان حذف پیام را تنظیم کنید."
    )
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")]]
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
