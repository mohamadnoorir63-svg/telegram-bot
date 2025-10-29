# ====================== ⚙️ پنل تنظیمات ساده با کنترل زنده قفل‌ها ======================
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from group_control.group_control import (
    _locks_get, _locks_set, _save_json,
    group_data, GROUP_CTRL_FILE, LOCK_TYPES
)

# 🌟 عنوان اصلی
MAIN_TITLE = "⚙️ <b>پنل تنظیمات ربات</b>\n\nاز منوی زیر گزینه مورد نظر را انتخاب کنید 👇"


# 🎨 صفحه اصلی پنل
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

    # ❌ بستن
    if data == "Tastatur_close":
        return await query.message.delete()

    # 🔙 بازگشت
    if data == "Tastatur_back":
        return await Tastatur_menu(update, context)

    # 🔒 قفل‌ها
    if data == "Tastatur_locks":
        return await show_lock_page(query, 1)


# ====================== 🔐 بخش قفل‌ها (سه صفحه‌ای) ======================

# 📘 دسته‌بندی قفل‌ها (هماهنگ با group_control)
PAGES = {
    1: ["links", "usernames", "mention", "ads", "forward", "tgservices", "bots", "join", "joinmsg"],
    2: ["media", "photos", "videos", "gifs", "files", "audio", "voices", "vmsgs", "caption"],
    3: ["text", "emoji", "english", "arabic", "edit", "reply", "all"],
}


async def show_lock_page(query, page: int = 1):
    """نمایش صفحه قفل‌ها"""
    chat_id = query.message.chat.id
    locks = _locks_get(chat_id)

    keyboard, row = [], []

    for k in PAGES.get(page, []):
        state = bool(locks.get(k, False))
        icon = "✅ فعال" if state else "❌ غیرفعال"
        label = LOCK_TYPES.get(k, k)
        row.append(InlineKeyboardButton(f"{label} | {icon}", callback_data=f"toggle_lock:{k}"))
        if len(row) == 1:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # ناوبری صفحات
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⬅️ صفحه قبل", callback_data=f"lock_page:{page-1}"))
    if page < max(PAGES.keys()):
        nav.append(InlineKeyboardButton("صفحه بعد ➡️", callback_data=f"lock_page:{page+1}"))
    if nav:
        keyboard.append(nav)

    # برگشت
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")])

    text = f"🔐 <b>مدیریت قفل‌های گروه — صفحه {page}</b>\n\nبرای فعال یا غیرفعال کردن، روی هر مورد بزن 👇"
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


# 🧭 جابه‌جایی بین صفحات
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

    locks = _locks_get(chat_id)
    new_state = not locks.get(lock_key, False)
    _locks_set(chat_id, lock_key, new_state)
    _save_json(GROUP_CTRL_FILE, group_data)

    # یافتن صفحه فعلی و بروزرسانی آنی
    page_to_show = 1
    for p, keys in PAGES.items():
        if lock_key in keys:
            page_to_show = p
            break
    await show_lock_page(query, page_to_show)
