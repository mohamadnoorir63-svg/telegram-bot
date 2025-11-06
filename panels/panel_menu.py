# ====================== 🌟 پنل مدیریت ربات (نسخه راهنمای تنظیمات) ======================
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
        return await show_settings_help(query)
    if data == "Tastatur_fun":
        return await show_fun_menu(query)
    if data == "Tastatur_locks":
        return await show_lock_page(query, 1)
    if data == "Tastatur_admin":
        return await show_admin_menu(query)
    if data == "Tastatur_welcome":
        return await show_welcome_menu(query)
    if data.startswith("toggle_lock:"):
        return await toggle_lock_button(update, context)
    if data.startswith("lock_page:"):
        return await handle_lock_page_switch(update, context)
    if data.startswith("fun_"):
        return await handle_fun_buttons(update, context)

    return await query.answer("این دکمه هنوز پیکربندی نشده ⚙️", show_alert=False)

# ====================== ⚙️ راهنمای تنظیمات ======================
async def show_settings_help(query):
    text = (
        "⚙️ <b>راهنمای تنظیمات ربات</b>\n\n"
        "در این بخش می‌تونی با دستورات زیر تنظیمات گروهت رو تغییر بدی:\n\n"
        "🔒 <b>قفل‌ها</b> — کنترل محتوای مجاز:\n"
        "   قفل لینک، قفل عکس، قفل ویدیو، قفل ربات و ...\n"
        "   📝 مثال: <code>قفل لینک</code> یا <code>باز کردن استیکر</code>\n\n"
        "🚫 <b>فیلتر کلمات</b> — حذف پیام‌های دارای کلمه خاص:\n"
        "   <code>فیلتر [کلمه]</code> — <code>حذف فیلتر [کلمه]</code>\n"
        "   <code>لیست فیلتر</code>\n\n"
        "🕒 <b>قفل خودکار</b> — بستن گروه در ساعات مشخص:\n"
        "   <code>قفل خودکار 23:00 07:00</code>\n"
        "   <code>حذف قفل خودکار</code>\n\n"
        "💬 <b>خوشامدگویی</b> — فعالسازی خوشامد و تنظیم پیام:\n"
        "   <code>خوشامد فعال</code> / <code>خوشامد غیرفعال</code>\n"
        "   <code>تنظیم خوشامد سلام به {name}</code>\n\n"
        "👑 <b>مدیریت مدیران</b> — افزودن / حذف مدیر گروه:\n"
        "   <code>افزودن مدیر</code> / <code>حذف مدیر</code>\n\n"
        "⚠️ <b>تنبیهات</b> — بن، سکوت، اخطار و حذف اخطار:\n"
        "   <code>بن</code> / <code>سکوت 5 دقیقه</code> / <code>اخطار</code>\n\n"
        "🔙 برای بازگشت از دکمه زیر استفاده کن 👇"
    )
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")]]
    return await query.edit_message_text(
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
