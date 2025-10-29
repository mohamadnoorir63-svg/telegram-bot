# ====================== 🌟 پنل مدیریت ربات — یک‌فایلِ پنل ======================
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from group_control.group_control import (
    _locks_get, _locks_set, _save_json,
    group_data, GROUP_CTRL_FILE, LOCK_TYPES
)

# ───────────────────────────── عنوان اصلی ─────────────────────────────
MAIN_TITLE = (
    "🌟 <b>پنل مدیریت ربات</b>\n\n"
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
        ],
        [
            InlineKeyboardButton("✳️ افزودن دستور", callback_data="Tastatur_add_alias"),
            InlineKeyboardButton("💬 افزودن ریپلای", callback_data="Tastatur_add_reply"),
        ],
        [
            InlineKeyboardButton("💐 خوشامد", callback_data="Tastatur_welcome"),
        ],
        [InlineKeyboardButton("❌ بستن پنل", callback_data="Tastatur_close")],
    ]

    if update.message:
        return await update.message.reply_text(
            MAIN_TITLE, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    # اگر از کال‌بک برگشته‌ایم
    return await update.callback_query.edit_message_text(
        MAIN_TITLE, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ───────────────────────────── روترِ همه دکمه‌های «Tastatur_*» ─────────────────────────────
async def Tastatur_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    # بستن
    if data == "Tastatur_close":
        return await query.message.delete()

    # بازگشت به منوی اصلی
    if data == "Tastatur_back":
        return await Tastatur_menu(update, context)

    # تنظیمات
    if data == "Tastatur_settings":
        return await show_settings_menu(query)

    # قفل‌ها (صفحه ۱)
    if data == "Tastatur_locks":
        return await show_lock_page(query, 1)

    # سرگرمی‌ها
    if data == "Tastatur_fun":
        return await show_fun_menu(query)

    # مدیریت گروه (راهنما)
    if data == "Tastatur_admin":
        return await show_admin_menu(query)

    # افزودن دستور (راهنما)
    if data == "Tastatur_add_alias":
        return await show_add_alias_help(query)

    # افزودن ریپلای (راهنما)
    if data == "Tastatur_add_reply":
        return await show_add_reply_help(query)

    # خوشامد (راهنما/پنل توضیحی)
    if data == "Tastatur_welcome":
        return await show_welcome_menu(query)

    # زیرمنوهای مدیریت گروه (همه با پیشوند Tastatur_admin_)
    if data in ADMIN_TEXTS:
        title, desc = ADMIN_TEXTS[data]
        kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_admin")]]
        return await query.edit_message_text(
            f"<b>{title}</b>\n\n{desc}", parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    # پیش‌فرض
    return await query.answer("این دکمه هنوز پیکربندی نشده ⚙️", show_alert=False)

# ====================== ⚙️ «تنظیمات» و «قفل‌ها» (۳ صفحه، تک‌ستونه، زنده) ======================
async def show_settings_menu(query):
    text = (
        "⚙️ <b>تنظیمات گروه</b>\n\n"
        "از گزینه‌های زیر یکی را انتخاب کنید 👇"
    )
    keyboard = [
        [InlineKeyboardButton("🔒 قفل‌ها", callback_data="Tastatur_locks")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")],
    ]
    return await query.edit_message_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )

# تقسیم قفل‌ها به ۳ صفحه (تک‌ستونه برای خوانایی)
LOCK_PAGES = {
    1: [
        ("links", "ارسال لینک"),
        ("usernames", "یوزرنیم / تگ"),
        ("mention", "منشن با @"),
        ("ads", "تبلیغ / تبچی"),
        ("forward", "فوروارد پیام"),
        ("tgservices", "پیام‌های سیستمی تلگرام"),
        ("bots", "افزودن ربات"),
        ("join", "ورود عضو جدید"),
        ("joinmsg", "پیام خوش‌آمد"),
    ],
    2: [
        ("media", "تمام رسانه‌ها"),
        ("photos", "ارسال عکس"),
        ("videos", "ارسال ویدیو"),
        ("gifs", "ارسال گیف"),
        ("stickers", "ارسال استیکر"),
        ("files", "ارسال فایل"),
        ("audio", "موسیقی / آهنگ"),
        ("voices", "ارسال ویس"),
        ("vmsgs", "ویدیو مسیج"),
        ("caption", "ارسال کپشن"),
    ],
    3: [
        ("text", "ارسال پیام متنی"),
        ("emoji", "پیام فقط ایموجی"),
        ("english", "حروف انگلیسی"),
        ("arabic", "حروف عربی"),
        ("edit", "ویرایش پیام"),
        ("reply", "ریپلای / پاسخ"),
        ("all", "قفل کلی گروه"),
    ],
}

async def show_lock_page(query, page: int = 1):
    chat_id = query.message.chat.id
    locks = _locks_get(chat_id)
    if page not in LOCK_PAGES:
        page = 1

    # دکمه‌های تک‌ستونه
    keyboard = []
    for key, label in LOCK_PAGES[page]:
        # فقط اگر این کلید واقعاً در LOCK_TYPES تعریف شده باشد
        if key not in LOCK_TYPES:
            continue
        state = bool(locks.get(key, False))
        icon = "✅ فعال" if state else "❌ غیرفعال"
        keyboard.append([InlineKeyboardButton(f"{label} | {icon}", callback_data=f"toggle_lock:{key}")])

    # ناوبری صفحات
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⬅️ صفحه قبل", callback_data=f"lock_page:{page-1}"))
    if page < max(LOCK_PAGES.keys()):
        nav.append(InlineKeyboardButton("صفحه بعد ➡️", callback_data=f"lock_page:{page+1}"))
    if nav:
        keyboard.append(nav)

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_settings")])

    text = f"🔐 <b>مدیریت قفل‌ها — صفحه {page}/{len(LOCK_PAGES)}</b>\n\nروی هر مورد بزن تا آنی تغییر کند 👇"
    try:
        return await query.edit_message_text(
            text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception:
        # در صورت «Message not modified»
        return await query.answer("✅ به‌روز شد", show_alert=False)

# تغییر وضعیت آنی قفل‌ها
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

    # پیدا کردن صفحه‌ای که قفل در آن است
    page_to_show = 1
    for p, items in LOCK_PAGES.items():
        if any(k == lock_key for k, _ in items):
            page_to_show = p
            break

    name = LOCK_TYPES.get(lock_key, lock_key)
    await query.answer(f"{name} {'🔒 فعال شد' if new_state else '🔓 غیرفعال شد'}", show_alert=False)
    return await show_lock_page(query, page_to_show)

# جابه‌جایی صفحات قفل‌ها (الگوی ^lock_page:)
async def handle_lock_page_switch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    if not data.startswith("lock_page:"):
        return
    try:
        page = int(data.split(":")[1])
    except (IndexError, ValueError):
        return await query.answer("صفحه نامعتبر است ⚠️", show_alert=True)
    return await show_lock_page(query, page)

# ====================== 🎮 سرگرمی‌ها (راهنماهای متنی) ======================
async def show_fun_menu(query):
    text = (
        "🎮 <b>بخش سرگرمی‌ها و ابزارهای خنگول</b>\n\n"
        "یکی از گزینه‌های زیر را انتخاب کنید 👇"
    )
    keyboard = [
        [
            InlineKeyboardButton("🎯 فال", callback_data="fun_fal"),
            InlineKeyboardButton("🏷 لقب", callback_data="fun_laqab"),
        ],
        [
            InlineKeyboardButton("📜 اصل", callback_data="fun_asl"),
            InlineKeyboardButton("😂 جوک", callback_data="fun_jok"),
        ],
        [
            InlineKeyboardButton("💬 بیو تصادفی", callback_data="fun_bio"),
            InlineKeyboardButton("🧩 فونت‌ساز", callback_data="fun_font"),
        ],
        [
            InlineKeyboardButton("🕋 اذان", callback_data="fun_azan"),
            InlineKeyboardButton("☁️ آب‌وهوا", callback_data="fun_weather"),
        ],
        [
            InlineKeyboardButton("👤 آیدی من", callback_data="fun_id"),
            InlineKeyboardButton("🧠 دستورات شخصی", callback_data="fun_alias"),
        ],
        [
            InlineKeyboardButton("💬 سخنگوی خنگول", callback_data="fun_speaker"),
            InlineKeyboardButton("🤖 ChatGPT", callback_data="fun_ai"),
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")],
    ]
    return await query.edit_message_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )

FUN_TEXTS = {
    "fun_fal": ("🎯 فال", "با دستور <code>فال</code> می‌تونی فال روزانه بگیری 🌟"),
    "fun_laqab": ("🏷 لقب", "با <code>ثبت لقب [لقب]</code> یا «لقب من» کار کن 😎"),
    "fun_asl": ("📜 اصل", "با <code>ثبت اصل [متن]</code> یا «اصل / اصل من»"),
    "fun_jok": ("😂 جوک", "با <code>جوک</code> یه لطیفه‌ی جدید بگیر 🤣"),
    "fun_bio": ("💬 بیو تصادفی", "با <code>بیو</code> یک بیو خوشگل تصادفی بگیر 💫"),
    "fun_font": ("🧩 فونت‌ساز", "با <code>فونت [متن]</code> یا <code>فونت محمد</code>"),
    "fun_azan": ("🕋 اذان", "مثال: <code>اذان تهران</code> یا <code>اذان مشهد</code>"),
    "fun_weather": ("☁️ آب‌وهوا", "مثال: <code>آب‌وهوا تهران</code> 🌦"),
    "fun_id": ("👤 آیدی من", "با <code>آیدی</code> شناسه عددی خودت/دیگران رو بگیر 🔢"),
    "fun_alias": ("🧠 دستورات شخصی", "ساخت کلمهٔ میانبر برای فرمان‌ها (پایین توضیح کامل‌تر داریم)"),
    "fun_speaker": ("💬 سخنگوی خنگول", "هرچی بگی، با لحن فان جواب می‌ده 😄"),
    "fun_ai": ("🤖 ChatGPT", "در پیوی ربات پیام بده و گفتگو کن 🤖"),
}

async def show_fun_info(query, title, desc):
    kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_fun")]]
    return await query.edit_message_text(
        f"<b>{title}</b>\n\n{desc}", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb)
    )

# هندلر اختصاصی سرگرمی‌ها (الگوی ^fun_)
async def handle_fun_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()
    if data in FUN_TEXTS:
        title, desc = FUN_TEXTS[data]
        return await show_fun_info(query, title, desc)

# ====================== 👮 مدیریت گروه — فقط راهنمای متنی (دو ستونه) ======================
async def show_admin_menu(query):
    text = (
        "👮 <b>مدیریت گروه</b>\n\n"
        "یکی از موضوعات زیر را انتخاب کن تا دستورهای مربوط به آن نمایش داده شود 👇"
    )
    keyboard = [
        [
            InlineKeyboardButton("👑 مدیریت‌ها", callback_data="Tastatur_admin_manage"),
            InlineKeyboardButton("🚫 بن/رفع‌بن", callback_data="Tastatur_admin_ban"),
        ],
        [
            InlineKeyboardButton("🔇 سکوت/رفع‌سکوت", callback_data="Tastatur_admin_mute"),
            InlineKeyboardButton("⚠️ اخطارها", callback_data="Tastatur_admin_warn"),
        ],
        [
            InlineKeyboardButton("📌 پین/آن‌پین", callback_data="Tastatur_admin_pin"),
            InlineKeyboardButton("🧹 پاکسازی", callback_data="Tastatur_admin_clean"),
        ],
        [
            InlineKeyboardButton("🔐 قفل/باز گروه", callback_data="Tastatur_admin_lockgroup"),
            InlineKeyboardButton("🕒 قفل خودکار", callback_data="Tastatur_admin_autolock"),
        ],
        [
            InlineKeyboardButton("🧠 Aliasها", callback_data="Tastatur_admin_alias"),
            InlineKeyboardButton("👥 تگ + اصل/لقب", callback_data="Tastatur_admin_tags"),
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")],
    ]
    return await query.edit_message_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )

ADMIN_TEXTS = {
    "Tastatur_admin_manage": (
        "👑 مدیریت‌ها",
        "• افزودن مدیر: <code>افزودن مدیر</code> (ریپلای)\n"
        "• حذف مدیر: <code>حذف مدیر</code> (ریپلای)\n"
        "• لیست مدیران: <code>لیست مدیران</code>\n"
        "• پاکسازی مدیران: <code>پاکسازی مدیران</code>\n"
        "نکته: بعضی دستورات باید روی پیام کاربر هدف «ریپلای» شوند."
    ),
    "Tastatur_admin_ban": (
        "🚫 بن / رفع‌بن",
        "• بن کاربر: <code>بن</code> (ریپلای)\n"
        "• رفع بن: <code>رفع بن</code> (ریپلای)\n"
        "• لیست بن‌ها: <code>لیست بن</code>\n"
        "محافظت: مدیران/سودوها قابل بن نیستند."
    ),
    "Tastatur_admin_mute": (
        "🔇 سکوت / رفع‌سکوت",
        "• سکوت: <code>سکوت</code> (ریپلای)\n"
        "  ⤷ با زمان: <code>سکوت 3 دقیقه</code> / <code>سکوت 30 ثانیه</code>\n"
        "• رفع سکوت: <code>رفع سکوت</code> (ریپلای)\n"
        "• لیست سکوت‌ها: <code>لیست سکوت</code>\n"
        "اتومات: بعد از زمان، خودکار آزاد می‌شود."
    ),
    "Tastatur_admin_warn": (
        "⚠️ اخطارها",
        "• اخطار: <code>اخطار</code> (ریپلای)\n"
        "• حذف اخطار: <code>حذف اخطار</code> (ریپلای)\n"
        "• لیست: <code>لیست اخطار</code>\n"
        "قانون: با ۳ اخطار → بن خودکار."
    ),
    "Tastatur_admin_pin": (
        "📌 پین / آن‌پین",
        "• پین: ریپلای + <code>پین</code>\n"
        "  ⤷ مدت‌دار: <code>پین 10</code> (دقیقه)\n"
        "• حذف همه پین‌ها: <code>حذف پین</code>"
    ),
    "Tastatur_admin_clean": (
        "🧹 پاکسازی",
        "• پاکسازی عددی: <code>پاکسازی 50</code>\n"
        "• پاکسازی کامل: <code>پاکسازی کامل</code> / <code>همه</code>\n"
        "• پاکسازی پیام‌های یک کاربر: ریپلای + <code>پاکسازی</code>"
    ),
    "Tastatur_admin_lockgroup": (
        "🔐 قفل/باز گروه",
        "• قفل گروه: <code>قفل گروه</code>\n"
        "• باز گروه: <code>باز گروه</code>\n"
        "مدیران واقعی/ثبت‌شده و سودو همیشه مجازند."
    ),
    "Tastatur_admin_autolock": (
        "🕒 قفل خودکار",
        "• فعال‌سازی: <code>قفل خودکار گروه 23:00 07:00</code>\n"
        "• غیرفعال: <code>غیرفعال کردن قفل خودکار</code>"
    ),
    "Tastatur_admin_alias": (
        "🧠 Alias (دستورات شخصی)",
        "• ساخت: <code>افزودن دستور \"اخراج\" → ban</code>\n"
        "  (از → یا -> یا => یا = هم پشتیبانی می‌شود)\n"
        "بعد از ساخت، نوشتن «اخراج» همان ban را اجرا می‌کند."
    ),
    "Tastatur_admin_tags": (
        "👥 تگ + اصل/لقب",
        "• تگ همه/فعال/غیرفعال/مدیران: <code>تگ ...</code>\n"
        "• اصل: <code>ثبت اصل [متن]</code> / <code>اصل</code> / <code>اصل من</code>\n"
        "• لقب: <code>ثبت لقب [لقب]</code> / <code>لقب</code> / <code>لقب من</code>"
    ),
}

# ====================== ✳️ افزودن دستور (Alias) — راهنما ======================
async def show_add_alias_help(query):
    text = (
        "✳️ <b>افزودن دستور (Alias)</b>\n\n"
        "با این قابلیت می‌تونی برای هر فرمان یک اسم فارسی/کوتاه بسازی.\n\n"
        "نمونه‌ها:\n"
        "• <code>افزودن دستور \"اخراج\" → ban</code>\n"
        "• <code>افزودن دستور \"سکوتش\" -> mute</code>\n"
        "• <code>افزودن دستور \"بازگروه\" = unlockgroup</code>\n\n"
        "بعد از ساخت، همون کلمهٔ جدید مثل فرمان اصلی عمل می‌کنه ✅"
    )
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")]]
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# ====================== 💬 افزودن ریپلای — راهنما (Reply storage) ======================
async def show_add_reply_help(query):
    text = (
        "💬 <b>افزودن ریپلای</b>\n\n"
        "منظور از «ریپلای» اینه که روی یک پیام ریپلای می‌کنی و دستور ذخیره‌سازی می‌دی "
        "تا بعداً با یک کلمه، همون متن/پاسخ ارسال بشه.\n\n"
        "✅ الگوی پیشنهادی (بسته به پیاده‌سازی شما):\n"
        "• ریپلای روی پیام + <code>افزودن ریپلای [کلید]</code>\n"
        "  مثال: ریپلای روی یک متن + <code>افزودن ریپلای سلام</code>\n"
        "• از اون به بعد با نوشتن <code>سلام</code> ربات پاسخ ذخیره‌شده رو می‌فرسته.\n\n"
        "🔒 دسترسی‌ها و محل ذخیره (JSON/DB) به پیاده‌سازی شما در هسته بستگی دارد."
    )
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")]]
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# ====================== 💐 خوشامد — راهنما/پنل توضیحی ======================
async def show_welcome_menu(query):
    text = (
        "💐 <b>خوشامدگویی اعضای جدید</b>\n\n"
        "با دستور <code>خوشامد</code> در گروه، همین پنلِ راهنما نمایش داده می‌شود.\n\n"
        "امکانات پیشنهادی (بسته به هسته شما):\n"
        "• 🖼 عکس خوشامد (آپلود دلخواه)\n"
        "• 📝 متن خوشامد (قابل قالب‌بندی، متغیرها: <code>{name}</code>، <code>{id}</code>)\n"
        "• 🔗 لینک/قوانین زیر پیام\n"
        "• ⏱ حذف خودکار پیام خوشامد بعد از X ثانیه\n"
        "• 🔛 روشن/خاموش کردن سیستم خوشامد\n\n"
        "نمونه دستورها (راهنمایی):\n"
        "• <code>خوشامد فعال</code> / <code>خوشامد غیرفعال</code>\n"
        "• <code>تنظیم متن خوشامد ...</code>\n"
        "• <code>تنظیم زمان حذف خوشامد 10</code>  (ثانیه)\n"
        "• <code>تنظیم لینک قوانین https://t.me/...</code>\n\n"
        "پیاده‌سازی ذخیره/خواندن تنظیمات بسته به فایل/دیتابیس شماست."
    )
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")]]
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
