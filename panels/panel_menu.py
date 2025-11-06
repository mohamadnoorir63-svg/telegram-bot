# ====================== 🌟 پنل مدیریت ربات (نسخه حرفه‌ای) ======================
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
        return await update.message.reply_text("❌ این پنل فقط در داخل گروه‌ها قابل استفاده است!", parse_mode="HTML")

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
        return await update.message.reply_text(MAIN_TITLE, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        return await update.callback_query.edit_message_text(MAIN_TITLE, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# ====================== 🎮 سرگرمی‌ها ======================
FUN_TEXTS = {
    "fun_jok": ("😂 جوک", "با دستور «جوک» یه لطیفه‌ی جدید بگیر 🤣"),
    "fun_fal": ("🎯 فال", "با دستور «فال» فال روزانه دریافت کن 🌟"),
    "fun_bio": ("💬 بیو تصادفی", "با دستور «بیو» یه بیوی تصادفی بگیر ✨"),
    "fun_font": ("🧩 فونت‌ساز", "با دستور «فونت [متن]» متن خودت رو زیبا کن 🎨"),
    "fun_azan": ("🕋 اذان", "با دستور «اذان تهران» یا «اذان مشهد» زمان اذان رو ببین 🕌"),
    "fun_weather": ("☁️ آب‌وهوا", "با دستور «آب‌وهوا [شهر]» وضعیت آب‌وهوا رو بگیر 🌦"),
    "fun_laqab": ("🏷 لقب", "با «ثبت لقب [متن]» یا «لقب من» کار کن 😎"),
    "fun_asl": ("📜 اصل", "با «ثبت اصل [متن]» یا «اصل من» اصل خودتو بنویس 📜"),
    "fun_ai": ("🤖 ChatGPT", "در پیوی با ربات گفتگو کن 🤖"),
}

async def show_fun_menu(query):
    text = "🎮 <b>بخش سرگرمی‌ها و ابزارها</b>\n\nیکی از گزینه‌های زیر را انتخاب کنید 👇"
    keyboard = [
        [InlineKeyboardButton("😂 جوک", callback_data="fun_jok"), InlineKeyboardButton("🎯 فال", callback_data="fun_fal")],
        [InlineKeyboardButton("🏷 لقب", callback_data="fun_laqab"), InlineKeyboardButton("📜 اصل", callback_data="fun_asl")],
        [InlineKeyboardButton("💬 بیو", callback_data="fun_bio"), InlineKeyboardButton("🧩 فونت", callback_data="fun_font")],
        [InlineKeyboardButton("☁️ آب‌وهوا", callback_data="fun_weather"), InlineKeyboardButton("🕋 اذان", callback_data="fun_azan")],
        [InlineKeyboardButton("🤖 ChatGPT", callback_data="fun_ai")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")],
    ]
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_fun_info(query, title, desc):
    kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_fun")]]
    return await query.edit_message_text(f"{title}\n\n{desc}", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

async def handle_fun_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    key = query.data
    await query.answer()
    if key in FUN_TEXTS:
        title, desc = FUN_TEXTS[key]
        return await show_fun_info(query, title, desc)
    return await query.answer("❌ گزینه نامعتبر است.", show_alert=False)

# ====================== ⚙️ تنظیمات ======================
async def show_settings_menu(query):
    text = (
        "⚙️ <b>بخش تنظیمات</b>\n\n"
        "از گزینه‌های زیر یکی را انتخاب کنید 👇\n\n"
        "هر بخش شامل دستورهای مرتبط خودش است ✅"
    )
    keyboard = [
        [InlineKeyboardButton("🔒 قفل‌ها", callback_data="Tastatur_locks")],
        [InlineKeyboardButton("🚫 فیلتر کلمات", callback_data="Tastatur_filters")],
        [InlineKeyboardButton("🕒 قفل خودکار", callback_data="Tastatur_autolock")],
        [InlineKeyboardButton("💬 خوشامدگویی", callback_data="Tastatur_welcome")],
        [InlineKeyboardButton("👑 مدیریت مدیران", callback_data="Tastatur_admins")],
        [InlineKeyboardButton("⚠️ تنبیهات", callback_data="Tastatur_punish")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")],
    ]
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

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

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_settings")])
    text = f"🔐 <b>مدیریت قفل‌ها</b>\nصفحه {page}/{total_pages}\n\nبرای فعال/غیرفعال‌سازی هر قفل روی آن بزنید 👇"
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def toggle_lock_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat.id
    lock_key = data.split(":", 1)[1]

    locks_data = _get_locks(chat_id)
    new_state = not locks_data.get(lock_key, False)
    _set_lock(chat_id, lock_key, new_state)
    await query.answer(f"{LOCK_TYPES.get(lock_key)} {'🔒 فعال شد' if new_state else '🔓 غیرفعال شد'}", show_alert=False)

    # تعیین صفحه فعلی
    index = list(LOCK_TYPES.keys()).index(lock_key)
    page_to_show = index // LOCK_PAGE_SIZE + 1
    return await show_lock_page(query, page_to_show)

async def handle_lock_page_switch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    page = int(query.data.split(":", 1)[1])
    return await show_lock_page(query, page)

# ====================== 👮 مدیریت گروه ======================
async def show_admin_menu(query):
    text = (
        "👮 <b>بخش مدیریت گروه</b>\n\n"
        "• بن / رفع‌بن\n"
        "• سکوت / رفع‌سکوت\n"
        "• اخطارها\n"
        "• پاکسازی\n"
        "• قفل / بازگروه"
    )
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")]]
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# ====================== 💐 خوشامد ======================
async def show_welcome_menu(query):
    text = (
        "💐 <b>سیستم خوشامدگویی</b>\n\n"
        "• خوشامد فعال / خوشامد غیرفعال\n"
        "• تنظیم متن خوشامد [متن دلخواه]\n"
        "• تنظیم زمان حذف خوشامد [ثانیه]\n"
        "• تنظیم لینک قوانین [لینک]\n\n"
        "✅ پیام خوشامد می‌تونه شامل متغیرهای زیر باشه:\n"
        "{name} → نام کاربر\n{id} → آیدی عددی"
    )
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_settings")]]
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
