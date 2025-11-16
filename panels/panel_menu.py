# panels/admin_panel.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from group_control.group_control import _get_locks, _set_lock, LOCK_TYPES
from datetime import datetime, timedelta

SUDO_IDS = [8588347189]  # آیدی سودو اصلی
LOCK_PAGE_SIZE = 8

# ───────────────────────────── عنوان اصلی ─────────────────────────────
MAIN_TITLE = "🌟 <b>پنل مدیریت گروه</b>\n\nاز منوی زیر یکی از بخش‌ها را انتخاب کنید 👇"

# ====================== 🏠 منوی اصلی ======================
async def Tastatur_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text(
            "❌ این پنل فقط در داخل گروه‌ها قابل استفاده است!", parse_mode="HTML"
        )

    if not await _has_access(context, chat.id, user.id):
        return await update.message.reply_text(
            "🚫 فقط مدیران یا سودو می‌توانند این پنل را باز کنند.", parse_mode="HTML"
        )

    keyboard = [
        [InlineKeyboardButton("⚙️ تنظیمات", callback_data="Tastatur_settings"),
         InlineKeyboardButton("🎮 سرگرمی‌ها", callback_data="Tastatur_fun")],
        [InlineKeyboardButton("👮 مدیریت گروه", callback_data="Tastatur_admin"),
         InlineKeyboardButton("💐 خوشامد", callback_data="Tastatur_welcome")],
        [InlineKeyboardButton("🗣️ سخنگوی خنگول", callback_data="Tastatur_speaker")],
        [InlineKeyboardButton("❌ بستن پنل", callback_data="Tastatur_close")]
    ]

    if update.message:
        return await update.message.reply_text(
            MAIN_TITLE, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    return await update.callback_query.edit_message_text(
        MAIN_TITLE, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ====================== دسترسی مدیر و سودو ======================
async def _has_access(context, chat_id, user_id):
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False

# ====================== 🔁 روتر دکمه‌ها ======================
async def Tastatur_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = query.from_user
    chat = query.message.chat

    if not await _has_access(context, chat.id, user.id):
        return await query.answer("🚫 فقط مدیران یا سودو می‌توانند این بخش را استفاده کنند.", show_alert=True)

    await query.answer()  # جلوگیری از چرخش دکمه‌ها

    if data == "Tastatur_close":
        try:
            await query.message.delete()
        except:
            pass
        return
    if data == "Tastatur_back":
        return await Tastatur_menu(update, context)
    if data == "Tastatur_settings":
        return await show_settings_menu(query)
    if data == "Tastatur_fun":
        return await show_fun_menu(query)
    if data == "Tastatur_admin":
        return await show_admin_menu(query)
    if data == "Tastatur_welcome":
        return await show_welcome_menu(query)
    if data == "Tastatur_speaker":
        return await show_speaker_menu(query)
    if data.startswith("help_"):
        return await show_help_info(query)
    if data == "Tastatur_locks":
        return await show_lock_page(query, 1)
    if data.startswith("toggle_lock:"):
        return await toggle_lock_button(update, context)
    if data.startswith("lock_page:"):
        return await handle_lock_page_switch(update, context)
    if data.startswith("fun_"):
        return await handle_fun_buttons(update, context)

# ====================== 🔧 زیرمنوی تنظیمات ======================
async def show_settings_menu(query):
    text = "⚙️ <b>بخش تنظیمات و ابزارها</b>\n\nیکی از گزینه‌ها را برای مشاهده راهنما انتخاب کنید 👇"
    keyboard = [
        [InlineKeyboardButton("👑 افزودن مدیر", callback_data="help_addadmin"),
         InlineKeyboardButton("📌 پن پیام", callback_data="help_pin")],
        [InlineKeyboardButton("🚫 فیلتر کلمات", callback_data="help_filter"),
         InlineKeyboardButton("🧹 پاکسازی", callback_data="help_clean")],
        [InlineKeyboardButton("📜 اصل", callback_data="help_asl"),
         InlineKeyboardButton("🏷 لقب", callback_data="help_laqab")],
        [InlineKeyboardButton("🔒 قفل گروه", callback_data="help_grouplock"),
         InlineKeyboardButton("🔔 تگ کاربران", callback_data="help_tag")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")]
    ]
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# ====================== 📘 توضیحات ابزارها ======================
HELP_TEXTS = {
    "help_addadmin": "👑 <b>افزودن یا حذف مدیر گروه</b>\n\n➕ افزودن مدیر: <code>افزودن مدیر</code>\n➖ حذف مدیر: <code>حذف مدیر</code>\n📋 نمایش مدیران: <code>لیست مدیران</code>",
    "help_pin": "📌 <b>پن یا حذف پن پیام</b>\n📍 پن پیام: <code>پن</code>\n❌ حذف پن: <code>حذف پن</code>\n⏰ پن موقت: <code>پن 2 دقیقه</code>",
    "help_filter": "🚫 <b>فیلتر کلمات</b>\n➕ افزودن: <code>فیلتر تست</code>\n⏰ موقت: <code>فیلتر تست 2 ساعت</code>\n➖ حذف: <code>حذف فیلتر تست</code>\n📋 لیست: <code>لیست فیلتر</code>",
    "help_clean": (
        "🧹 <b>پاکسازی پیام‌ها</b>\n\n"
        "• پاکسازی کامل: پاکسازی از اول تا آخر\n"
        "• حذف عددی: پاکسازی تعداد مشخص\n"
        "• پاک روی پیام فرد: روی پیام ریپلی شده آن فرد\n"
        "• تمام پیام‌های فرد: تمام پیام‌های کاربر پاک می‌شوند"
    ),
    "help_asl": "📜 <b>ثبت اصل</b>\n➕ ثبت: <code>ثبت اصل من اهل صداقتم</code>\n👀 نمایش: <code>اصل من</code>\n❌ حذف: <code>حذف اصل</code>",
    "help_laqab": "🏷 <b>ثبت لقب</b>\n➕ ثبت: <code>ثبت لقب قهرمان</code>\n👀 نمایش: <code>لقب من</code>\n❌ حذف: <code>حذف لقب</code>",
    "help_grouplock": "🔒 <b>قفل گروه</b>\n📌 با این ویژگی می‌توان گروه را قفل یا باز کرد.\n🕐 حالت خودکار: <code>قفل خودکار روشن</code>\n🔓 خاموش: <code>قفل خودکار خاموش</code>",
    "help_tag": (
        "🔔 <b>تگ کاربران</b>\n\n"
        "با ارسال دکمه تگ در گروه، پنل تک برای ارسال ایجاد می‌شود.\n"
        "کاربر می‌تواند انتخاب کند:\n"
        "• تگ همه مدیران\n"
        "• تگ ۵۰ کاربر\n"
        "• تگ ۳۰۰ کاربر\n"
        "• تگ ۵۰ کاربران دیگر"
    )
}

async def show_help_info(query):
    data = query.data.strip()
    if data not in HELP_TEXTS:
        return await query.answer("❌ هنوز برای این گزینه راهنما تعریف نشده", show_alert=True)
    text = HELP_TEXTS[data]
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_settings")]]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# ====================== 🔒 قفل‌ها ======================
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
    if page > 1: nav.append(InlineKeyboardButton("⬅️ قبل", callback_data=f"lock_page:{page-1}"))
    if page < total_pages: nav.append(InlineKeyboardButton("بعد ➡️", callback_data=f"lock_page:{page+1}"))
    if nav: keyboard.append(nav)

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_admin")])
    text = f"🔐 <b>مدیریت قفل‌ها</b>\nصفحه {page}/{total_pages}\n\nبرای تغییر وضعیت قفل‌ها کلیک کنید 👇"
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def toggle_lock_button(update, context):
    query = update.callback_query
    chat_id = query.message.chat.id
    lock_key = query.data.split(":", 1)[1]
    locks_data = _get_locks(chat_id)
    new_state = not locks_data.get(lock_key, False)
    _set_lock(chat_id, lock_key, new_state)
    await query.answer(f"{LOCK_TYPES.get(lock_key)} {'🔒 فعال شد' if new_state else '🔓 غیرفعال شد'}", show_alert=False)
    index = list(LOCK_TYPES.keys()).index(lock_key)
    page_to_show = index // LOCK_PAGE_SIZE + 1
    return await show_lock_page(query, page_to_show)

async def handle_lock_page_switch(update, context):
    query = update.callback_query
    page = int(query.data.split(":", 1)[1])
    return await show_lock_page(query, page)

# ====================== 🎮 سرگرمی‌ها ======================
FUN_TEXTS = {
    "fun_jok": ("😂 جوک", "با دستور «جوک» یه لطیفه‌ی جدید بگیر 🤣"),
    "fun_fal": ("🎯 فال", "با دستور «فال» فال روزانه دریافت کن 🌟"),
    "fun_font": ("🧩 فونت‌ساز", "با دستور «فونت [متن]» متن خودت رو زیبا کن 🎨"),
    "fun_azan": ("🕋 اذان", "با دستور «اذان تهران» یا «اذان مشهد» زمان اذان را ببین 🕌"),
    "fun_weather": ("☁️ آب‌وهوا", "با دستور «آب‌وهوا [شهر]» وضعیت آب‌وهوا را بگیر 🌦"),
    "fun_ramadan": ("🌙 رمضان", "با دستور «رمضان» تاریخ رمضان و روز فعلی ماه را ببین 🌙"),
    "fun_reply": ("💾 ساخت ریپلای", "روی پیام ریپلای کن و بنویس: <code>/save متن</code>\nبعدا با نوشتن <code>متن</code> پیام ارسال می‌شود 💬"),
}

async def show_fun_menu(query):
    text = "🎮 <b>بخش سرگرمی‌ها و ابزارها</b>\n\nیکی از گزینه‌ها را انتخاب کنید 👇"
    keyboard = [
        [InlineKeyboardButton("😂 جوک", callback_data="fun_jok"),
         InlineKeyboardButton("🎯 فال", callback_data="fun_fal")],
        [InlineKeyboardButton("🧩 فونت", callback_data="fun_font"),
         InlineKeyboardButton("☁️ آب‌وهوا", callback_data="fun_weather")],
        [InlineKeyboardButton("🌙 رمضان", callback_data="fun_ramadan"),
         InlineKeyboardButton("💾 ساخت ریپلای", callback_data="fun_reply")],
        [InlineKeyboardButton("🕋 اذان", callback_data="fun_azan")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")]
    ]
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_fun_info(query, title, desc):
    kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_fun")]]
    return await query.edit_message_text(f"{title}\n\n{desc}", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

async def handle_fun_buttons(update, context):
    query = update.callback_query
    key = query.data
    await query.answer()
    if key in FUN_TEXTS:
        title, desc = FUN_TEXTS[key]
        return await show_fun_info(query, title, desc)
    return await query.answer("❌ گزینه نامعتبر است.", show_alert=False)

# ====================== 🗣️ سخنگوی خنگول ======================
async def show_speaker_menu(query):
    text = (
        "🗣️ <b>بخش سخنگوی خنگول</b>\n\nبرای روشن/خاموش کردن: <code>/reply</code>\n"
        "خنگول فقط به پیام‌های ریپلای شده پاسخ می‌دهد."
    )
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")]]
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# ====================== 👮 مدیریت گروه ======================
async def show_admin_menu(query):
    text = "👮 <b>بخش مدیریت گروه</b>\n\n🔒 برای دیدن لیست قفل‌های فعال، از دکمه زیر استفاده کنید 👇"
    keyboard = [[InlineKeyboardButton("🔒 قفل‌ها", callback_data="Tastatur_locks")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")]]
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# ====================== 💐 خوشامد ======================
async def show_welcome_menu(query):
    text = (
        "💐 <b>سیستم خوشامدگویی</b>\n\n"
        "برای باز کردن پنل خوشامد، دستور <code>خوشامد</code> را ارسال کنید."
    )
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")]]
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
