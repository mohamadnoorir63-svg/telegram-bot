# ====================== ⚙️ پنل مدیریت گروه + قفل‌های زنده + سرگرمی‌ها ======================
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from group_control.group_control import (
    _locks_get, _locks_set, _save_json,
    group_data, GROUP_CTRL_FILE, LOCK_TYPES
)

# 🌟 عنوان اصلی
MAIN_TITLE = (
    "🌟 <b>پنل مدیریت ربات</b>\n\n"
    "از منوی زیر یکی از بخش‌ها را انتخاب کنید 👇"
)


# 🎛 منوی اصلی
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
            InlineKeyboardButton("🎮 سرگرمی‌ها", callback_data="Tastatur_fun")
        ],
        [
            InlineKeyboardButton("👮 مدیریت گروه", callback_data="Tastatur_admin")
        ],
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


# 🎛 مدیریت کلی دکمه‌ها
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

    # ⚙️ تنظیمات
    if data == "Tastatur_settings":
        return await show_settings_menu(query)

    # 🎮 سرگرمی‌ها
    if data == "Tastatur_fun":
        return await show_fun_menu(query)

    # 👮 مدیریت گروه
    if data == "Tastatur_admin":
        return await show_admin_menu(query)

    # 🧩 بخش قفل‌ها
    if data == "Tastatur_locks":
        return await show_lock_page(query, 1)

    # 🔄 تغییر صفحه در قفل‌ها
    if data.startswith("lock_page:"):
        page = int(data.split(":")[1])
        return await show_lock_page(query, page)
        # ====================== ⚙️ زیرمنوی تنظیمات ======================
async def show_settings_menu(query):
    """صفحه تنظیمات کلی گروه"""
    text = (
        "⚙️ <b>تنظیمات گروه</b>\n\n"
        "از گزینه‌های زیر یکی را انتخاب کنید 👇"
    )
    keyboard = [
        [InlineKeyboardButton("🔒 قفل‌ها", callback_data="Tastatur_locks")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")]
    ]
    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ====================== 🎮 زیرمنوی سرگرمی‌ها ======================
async def show_fun_menu(query):
    """نمایش بخش سرگرمی‌ها و ابزارها"""
    text = (
        "🎮 <b>بخش سرگرمی‌ها و ابزارهای خنگول</b>\n\n"
        "یکی از گزینه‌های زیر را انتخاب کنید 👇"
    )

    keyboard = [
        [
            InlineKeyboardButton("🎯 فال", callback_data="fun_fal"),
            InlineKeyboardButton("🏷 لقب", callback_data="fun_laqab")
        ],
        [
            InlineKeyboardButton("📜 اصل", callback_data="fun_asl"),
            InlineKeyboardButton("😂 جوک", callback_data="fun_jok")
        ],
        [
            InlineKeyboardButton("💬 بیو تصادفی", callback_data="fun_bio"),
            InlineKeyboardButton("🧩 فونت‌ساز", callback_data="fun_font")
        ],
        [
            InlineKeyboardButton("🕋 اذان", callback_data="fun_azan"),
            InlineKeyboardButton("☁️ آب‌وهوا", callback_data="fun_weather")
        ],
        [
            InlineKeyboardButton("👤 آیدی من", callback_data="fun_id"),
            InlineKeyboardButton("🧠 دستورات شخصی", callback_data="fun_alias")
        ],
        [
            InlineKeyboardButton("🤖 ChatGPT", callback_data="fun_ai"),
            InlineKeyboardButton("💬 سخنگوی خنگول", callback_data="fun_speaker")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")]
    ]

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ====================== 📚 نمایش توضیحات هر سرگرمی ======================
async def show_fun_info(query, title, desc):
    """نمایش راهنمای هر ابزار سرگرمی"""
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_fun")]]
    await query.edit_message_text(
        f"<b>{title}</b>\n\n{desc}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ⚙️ پاسخ به دکمه‌های سرگرمی
async def handle_fun_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت انتخاب گزینه‌های سرگرمی"""
    query = update.callback_query
    data = query.data
    await query.answer()

    FUN_TEXTS = {
        "fun_fal": ("🎯 فال", "با دستور <code>فال</code> می‌تونی فال روزانه بگیری 🌟"),
        "fun_laqab": ("🏷 لقب", "با دستور <code>لقب [نام]</code> یه لقب باحال بساز 😎"),
        "fun_asl": ("📜 اصل", "با <code>اصل</code> یه جمله‌ی فان از خنگول بگیر 😂"),
        "fun_jok": ("😂 جوک", "با <code>جوک</code> یه لطیفه‌ی جدید بگیر 🤣"),
        "fun_bio": ("💬 بیو تصادفی", "با <code>بیو</code> یه بیو تصادفی از ربات بگیر 💫"),
        "fun_font": ("🧩 فونت‌ساز", "با <code>فونت محمد</code> یا هر اسم دیگه‌ای فونت مخصوص بگیر ✍️"),
        "fun_azan": ("🕋 اذان", "با <code>اذان تهران</code> یا شهر دلخواهت، زمان اذان رو بگیر 🕌"),
        "fun_weather": ("☁️ آب‌وهوا", "با <code>آب‌وهوا تهران</code> یا شهر دلخواهت دما و شرایط رو ببین 🌦"),
        "fun_id": ("👤 آیدی من", "با دستور <code>آیدی</code> آیدی عددی خودت یا دیگران رو بگیر 🔢"),
        "fun_alias": ("🧠 دستورات شخصی", "با دستور <code>افزودن دستور</code> یه اسم خاص برای دستور بساز 😎"),
        "fun_ai": ("🤖 ChatGPT", "با ارسال پیام در پیوی ربات، با ChatGPT حرف بزن 🤖"),
        "fun_speaker": ("💬 سخنگوی خنگول", "با نوشتن جمله، خنگول باهات حرف می‌زنه 😂"),
    }

    if data in FUN_TEXTS:
        title, desc = FUN_TEXTS[data]
        return await show_fun_info(query, title, desc)
        # ====================== 👮 زیرمنوی مدیریت گروه ======================
async def show_admin_menu(query):
    """منوی مدیریت گروه و راهنمای دستورات مدیریتی"""
    text = (
        "👮 <b>مدیریت گروه</b>\n\n"
        "از گزینه‌های زیر برای مشاهده راهنمای هر بخش استفاده کن 👇"
    )

    keyboard = [
        [
            InlineKeyboardButton("👑 مدیریت‌ها", callback_data="admin_manage"),
            InlineKeyboardButton("🚫 بن / رفع‌بن", callback_data="admin_ban")
        ],
        [
            InlineKeyboardButton("🔇 سکوت / رفع‌سکوت", callback_data="admin_mute"),
            InlineKeyboardButton("⚠️ اخطار / حذف اخطار", callback_data="admin_warn")
        ],
        [
            InlineKeyboardButton("🧹 پاکسازی‌ها", callback_data="admin_clean"),
            InlineKeyboardButton("📊 آمار گروه", callback_data="admin_stats")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")]
    ]

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# 🧭 راهنمای دستورات مدیریتی
async def show_admin_info(query, title, desc):
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_admin")]]
    await query.edit_message_text(
        f"<b>{title}</b>\n\n{desc}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ⚙️ پاسخ به دکمه‌های مدیریت
async def handle_admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    ADMIN_TEXTS = {
        "admin_manage": ("👑 مدیریت‌ها", "• افزودن مدیر: <code>افزودن مدیر (ریپلای)</code>\n• حذف مدیر: <code>حذف مدیر (ریپلای)</code>\n• لیست مدیران: <code>لیست مدیران</code>\n• پاکسازی مدیران: <code>پاکسازی مدیران</code>"),
        "admin_ban": ("🚫 بن / رفع‌بن", "• بن کاربر: <code>بن (ریپلای)</code>\n• رفع بن: <code>رفع بن (ریپلای)</code>\n• لیست بن شده‌ها: <code>لیست بن</code>"),
        "admin_mute": ("🔇 سکوت / رفع‌سکوت", "• سکوت کاربر: <code>سکوت (ریپلای)</code>\n• رفع سکوت: <code>رفع سکوت (ریپلای)</code>\n• لیست افراد ساکت: <code>لیست سکوت</code>"),
        "admin_warn": ("⚠️ اخطار / حذف اخطار", "• افزودن اخطار: <code>اخطار (ریپلای)</code>\n• حذف اخطار: <code>حذف اخطار (ریپلای)</code>\n• لیست اخطارها: <code>لیست اخطار</code>"),
        "admin_clean": ("🧹 پاکسازی‌ها", "• پاکسازی پیام‌ها: <code>پاکسازی [عدد]</code>\n• پاکسازی لیست بن: <code>پاکسازی بن</code>\n• پاکسازی اخطارها: <code>پاکسازی اخطار</code>"),
        "admin_stats": ("📊 آمار گروه", "• مشاهده آمار روزانه: <code>آمار روز</code>\n• آمار اعضا: <code>آمار اعضا</code>\n• فعالیت کاربران: <code>فعال‌ترین اعضا</code>"),
    }

    if data in ADMIN_TEXTS:
        title, desc = ADMIN_TEXTS[data]
        return await show_admin_info(query, title, desc)


# ====================== 🔐 سیستم قفل‌ها با عملکرد زنده ======================

# 📄 تقسیم قفل‌ها در چهار صفحه کامل
PAGES = {
    1: {
        "links": "ارسال لینک",
        "usernames": "ارسال یوزرنیم / تگ",
        "mention": "منشن با @",
        "ads": "ارسال تبلیغ / تبچی",
        "forward": "فوروارد پیام",
        "joinmsg": "پیام خوش‌آمد",
        "tgservices": "پیام‌های سیستمی تلگرام",
    },
    2: {
        "photos": "ارسال عکس",
        "videos": "ارسال ویدیو",
        "gifs": "ارسال گیف",
        "files": "ارسال فایل",
        "audio": "ارسال موسیقی / آهنگ",
        "voices": "ارسال ویس",
        "vmsgs": "ارسال ویدیو مسیج",
        "media": "تمام رسانه‌ها",
        "caption": "ارسال کپشن",
    },
    3: {
        "text": "ارسال پیام متنی",
        "emoji": "پیام فقط ایموجی",
        "english": "حروف انگلیسی",
        "arabic": "حروف عربی (غیرفارسی)",
        "edit": "ویرایش پیام",
        "reply": "ریپلای / پاسخ به پیام",
    },
    4: {
        "bots": "افزودن ربات",
        "join": "ورود عضو جدید",
        "all": "قفل کلی گروه",
    }
}


# ⚙️ نمایش صفحه قفل‌ها
async def show_lock_page(query, page: int = 1):
    """نمایش صفحه قفل‌ها با وضعیت فعال یا غیرفعال"""
    chat_id = query.message.chat.id
    locks = _locks_get(chat_id)
    locks_page = PAGES.get(page, {})
    keyboard = []

    # ساخت دکمه‌ها به صورت دو ستونه
    row = []
    for key, label in locks_page.items():
        state = locks.get(key, False)
        icon = "✅ فعال" if state else "❌ غیرفعال"
        row.append(
            InlineKeyboardButton(
                f"{label} | {icon}",
                callback_data=f"toggle_lock:{key}"
            )
        )
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # ناوبری صفحات
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⬅️ صفحه قبل", callback_data=f"lock_page:{page-1}"))
    if page < len(PAGES):
        nav.append(InlineKeyboardButton("صفحه بعد ➡️", callback_data=f"lock_page:{page+1}"))
    if nav:
        keyboard.append(nav)

    # بازگشت
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_settings")])

    # متن نمایش
    text = (
        f"🔐 <b>مدیریت قفل‌های گروه — صفحه {page}/{len(PAGES)}</b>\n\n"
        "برای فعال یا غیرفعال کردن هر مورد روی آن بزن 👇"
    )
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


# 🔄 تغییر وضعیت قفل‌ها
async def toggle_lock_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فعال یا غیرفعال کردن قفل‌ها درجا با ذخیره در فایل"""
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

    # پیدا کردن صفحه‌ای که قفل داخلشه
    page_to_show = 1
    for p, keys in PAGES.items():
        if lock_key in keys:
            page_to_show = p
            break

    # فیدبک برای کاربر
    state_txt = "🔒 فعال شد" if new_state else "🔓 غیرفعال شد"
    name = PAGES[page_to_show][lock_key]
    await query.answer(f"{name} {state_txt}", show_alert=False)

    # بروزرسانی صفحه جاری
    await show_lock_page(query, page_to_show)
    # ====================== 🧭 کنترل تغییر صفحه قفل‌ها ======================
async def handle_lock_page_switch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت جابه‌جایی بین صفحات قفل‌ها (رزرو برای گسترش آینده)"""
    query = update.callback_query
    data = query.data
    await query.answer()

    # بررسی اینکه کاربر روی دکمه صفحه زده
    if not data.startswith("lock_page:"):
        return

    # استخراج شماره صفحه
    try:
        page = int(data.split(":")[1])
    except (IndexError, ValueError):
        return await query.answer("صفحه نامعتبر است ⚠️", show_alert=True)

    # نمایش صفحه مورد نظر
    await show_lock_page(query, page)
