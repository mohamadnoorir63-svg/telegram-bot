# ====================== 🌟 پنل مدیریت ربات (بروز شده) ======================
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from group_control.group_control import _get_locks, _set_lock, _save_json, LOCK_TYPES, LOCK_FILE, _load_json

# ───────────────────────────── عنوان اصلی ─────────────────────────────
MAIN_TITLE = (
    "🌟 <b>پنل مدیریت گروه</b>\n\n"
    "از منوی زیر یکی از بخش‌ها را انتخاب کنید 👇"
)

# ───────────────────────────── منوی اصلی ─────────────────────────────
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

# ───────────────────────────── روتر دکمه‌ها ─────────────────────────────
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

    if data == "Tastatur_locks":
        return await show_lock_page(query, 1)

    if data == "Tastatur_fun":
        return await show_fun_menu(query)

    if data == "Tastatur_admin":
        return await show_admin_menu(query)

    if data == "Tastatur_welcome":
        return await show_welcome_menu(query)

    # تغییر قفل
    if data.startswith("toggle_lock:"):
        return await toggle_lock_button(update, context)

    # جابجایی صفحات قفل
    if data.startswith("lock_page:"):
        return await handle_lock_page_switch(update, context)

    return await query.answer("این دکمه هنوز پیکربندی نشده ⚙️", show_alert=False)

# ====================== ⚙️ تنظیمات ======================
async def show_settings_menu(query):
    text = "⚙️ تنظیمات گروه\n\nاز گزینه‌های زیر یکی را انتخاب کنید 👇"
    keyboard = [
        [InlineKeyboardButton("🔒 قفل‌ها", callback_data="Tastatur_locks")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")],
    ]
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# ====================== 🔐 قفل‌ها ======================
LOCK_PAGE_SIZE = 8  # چند قفل در هر صفحه نمایش داده شود

async def show_lock_page(query, page: int = 1):
    chat_id = query.message.chat.id
    locks_data = _get_locks(chat_id)

    all_locks = list(LOCK_TYPES.items())
    total_pages = (len(all_locks) + LOCK_PAGE_SIZE - 1) // LOCK_PAGE_SIZE
    page = max(1, min(page, total_pages))
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

    text = f"🔐 <b>مدیریت قفل‌ها</b>\nصفحه {page}/{total_pages}\n\nبرای تغییر وضعیت هر قفل روی آن بزنید 👇"
    try:
        return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    except:
        return await query.answer("✅ به‌روز شد", show_alert=False)

async def toggle_lock_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat.id
    lock_key = data.split(":", 1)[1]

    locks_data = _get_locks(chat_id)
    new_state = not locks_data.get(lock_key, False)
    _set_lock(chat_id, lock_key, new_state)

    await query.answer(f"{LOCK_TYPES.get(lock_key)} {'🔒 فعال شد' if new_state else '🔓 غیرفعال شد'}", show_alert=False)

    # بروزرسانی صفحه
    locks_reload = _load_json(LOCK_FILE, {})
    page_to_show = 1
    index = list(LOCK_TYPES.keys()).index(lock_key)
    page_to_show = index // LOCK_PAGE_SIZE + 1
    return await show_lock_page(query, page_to_show)

async def handle_lock_page_switch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    page = int(query.data.split(":")[1])
    return await show_lock_page(query, page)

# ====================== 🎮 سرگرمی‌ها (بدون تغییر) ======================
async def show_fun_menu(query):
    text = (
        "🎮 بخش سرگرمی‌ها و ابزارهای خنگول\n\n"
        "یکی از گزینه‌های زیر را انتخاب کنید 👇"
    )
    keyboard = [
        [InlineKeyboardButton("😂 جوک", callback_data="fun_jok"),
         InlineKeyboardButton("🎯 فال", callback_data="fun_fal")],
        [InlineKeyboardButton("🏷 لقب", callback_data="fun_laqab"),
         InlineKeyboardButton("📜 اصل", callback_data="fun_asl")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")],
    ]
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# ====================== 👮 مدیریت گروه ======================
async def show_admin_menu(query):
    text = (
        "👮 بخش مدیریت گروه\n\n"
        "از گزینه‌های زیر استفاده کن برای کنترل گروه 👇"
    )
    keyboard = [
        [InlineKeyboardButton("🔒 قفل/باز گروه", callback_data="Tastatur_admin_lockgroup")],
        [InlineKeyboardButton("🚫 بن / سکوت / اخطار", callback_data="Tastatur_admin_punish")],
        [InlineKeyboardButton("📌 پین / حذف پین", callback_data="Tastatur_admin_pin")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")],
    ]
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# ====================== 💐 خوشامد ======================
async def show_welcome_menu(query):
    text = (
        "💐 بخش خوشامدگویی\n\n"
        "با دستور «خوشامد فعال» یا «خوشامد غیرفعال» سیستم خوشامد را کنترل کن 🌸"
    )
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")]]
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
