# ====================== 🌟 پنل مدیریت ربات — یک‌فایلِ پنل ======================
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from group_control.group_control import (
    _get_locks, _set_lock, _save_json, LOCK_TYPES
)

# ───────────────────────────── عنوان اصلی ─────────────────────────────
MAIN_TITLE = (
    "🌟 پنل مدیریت ربات\n\n"
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
            InlineKeyboardButton("🧭 راهنمای مدیریت", callback_data="Tastatur_help"),  # 🔹 دکمه جدید
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

    # 🔹 راهنمای مدیریت
    if data == "Tastatur_help":
        return await show_help_menu(query)

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
            f"**{title}**\n\n{desc}", parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    # پیش‌فرض
    return await query.answer("این دکمه هنوز پیکربندی نشده ⚙️", show_alert=False)

# ====================== ⚙️ تنظیمات و قفل‌ها ======================

async def show_settings_menu(query):
    text = (
        "⚙️ تنظیمات گروه\n\n"
        "از گزینه‌های زیر یکی را انتخاب کنید 👇"
    )
    keyboard = [
        [InlineKeyboardButton("🔒 قفل‌ها", callback_data="Tastatur_locks")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")],
    ]
    return await query.edit_message_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ───────────────────────────── تقسیم قفل‌ها به صفحات ─────────────────────────────
LOCK_PAGES = {
    1: [
        ("links", "ارسال لینک"), ("usernames", "یوزرنیم / تگ"),
        ("mention", "منشن با @"), ("ads", "تبلیغ / تبچی"),
        ("forward", "فوروارد پیام"), ("tgservices", "پیام‌های سیستمی تلگرام"),
        ("bots", "افزودن ربات"), ("join", "ورود عضو جدید"),
        ("joinmsg", "پیام خوش‌آمد"),
    ],
    2: [
        ("media", "تمام رسانه‌ها"), ("photos", "ارسال عکس"),
        ("videos", "ارسال ویدیو"), ("gifs", "ارسال گیف"),
        ("stickers", "ارسال استیکر"), ("files", "ارسال فایل"),
        ("audio", "موسیقی / آهنگ"), ("voices", "ارسال ویس"),
        ("vmsgs", "ویدیو مسیج"), ("caption", "ارسال کپشن"),
    ],
    3: [
        ("text", "ارسال پیام متنی"), ("emoji", "پیام فقط ایموجی"),
        ("english", "حروف انگلیسی"), ("arabic", "حروف عربی"),
        ("edit", "ویرایش پیام"), ("reply", "ریپلای / پاسخ"),
        ("all", "قفل کلی گروه"),
    ],
}
# ───────────────────────────── نمایش صفحه قفل‌ها ─────────────────────────────
async def show_lock_page(query, page: int = 1):
    chat_id = query.message.chat.id
    locks = _locks_get(chat_id)
    if page not in LOCK_PAGES:
        page = 1

    keyboard = []
    for key, label in LOCK_PAGES[page]:
        if key not in LOCK_TYPES:
            continue
        state = bool(locks.get(key, False))
        icon = "✅ فعال" if state else "❌ غیرفعال"
        keyboard.append([InlineKeyboardButton(f"{label} | {icon}", callback_data=f"toggle_lock:{key}")])

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⬅️ صفحه قبل", callback_data=f"lock_page:{page-1}"))
    if page < max(LOCK_PAGES.keys()):
        nav.append(InlineKeyboardButton("صفحه بعد ➡️", callback_data=f"lock_page:{page+1}"))
    if nav:
        keyboard.append(nav)

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_settings")])

    text = f"🔐 **مدیریت قفل‌ها — صفحه {page}/{len(LOCK_PAGES)}**\n\nروی هر مورد بزن تا آنی تغییر کند 👇"
    try:
        return await query.edit_message_text(
            text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception:
        return await query.answer("✅ به‌روز شد", show_alert=False)

# ───────────────────────────── تغییر وضعیت آنی قفل‌ها ─────────────────────────────
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

    page_to_show = 1
    for p, items in LOCK_PAGES.items():
        if any(k == lock_key for k, _ in items):
            page_to_show = p
            break

    name = LOCK_TYPES.get(lock_key, lock_key)
    await query.answer(f"{name} {'🔒 فعال شد' if new_state else '🔓 غیرفعال شد'}", show_alert=False)
    return await show_lock_page(query, page_to_show)

# ───────────────────────────── جابه‌جایی صفحات قفل‌ها ─────────────────────────────
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

# ====================== 🎮 سرگرمی‌ها ======================
async def show_fun_menu(query):
    text = (
        "🎮 بخش سرگرمی‌ها و ابزارهای خنگول\n\n"
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
    "fun_fal": ("🎯 فال", "با دستور فال می‌تونی فال روزانه بگیری 🌟"),
    "fun_laqab": ("🏷 لقب", "با ثبت لقب [لقب] یا «لقب من» کار کن 😎"),
    "fun_asl": ("📜 اصل", "با ثبت اصل [متن] یا «اصل / اصل من»"),
    "fun_jok": ("😂 جوک", "با جوک یه لطیفه‌ی جدید بگیر 🤣"),
    "fun_bio": ("💬 بیو تصادفی", "با بیو یک بیو خوشگل تصادفی بگیر 💫"),
    "fun_font": ("🧩 فونت‌ساز", "با فونت [متن] یا فونت محمد"),
    "fun_azan": ("🕋 اذان", "مثال: اذان تهران یا اذان مشهد"),
    "fun_weather": ("☁️ آب‌وهوا", "مثال: آب‌وهوا تهران 🌦"),
    "fun_id": ("👤 آیدی من", "با آیدی شناسه عددی خودت/دیگران رو بگیر 🔢"),
    "fun_alias": ("🧠 دستورات شخصی", "ساخت کلمهٔ میانبر برای فرمان‌ها (پایین توضیح کامل‌تر داریم)"),
    "fun_speaker": ("💬 سخنگوی خنگول", "هرچی بگی، با لحن فان جواب می‌ده 😄"),
    "fun_ai": ("🤖 ChatGPT", "در پیوی ربات پیام بده و گفتگو کن 🤖"),
}

async def show_fun_info(query, title, desc):
    kb = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_fun")]]
    return await query.edit_message_text(
        f"{title}\n\n{desc}", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb)
    )

async def handle_fun_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()
    if data in FUN_TEXTS:
        title, desc = FUN_TEXTS[data]
        return await show_fun_info(query, title, desc)

# ====================== 👮 مدیریت گروه ======================
async def show_admin_menu(query):
    text = (
        "👮 مدیریت گروه\n\n"
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

# ───────────────────────────── متون مدیریت ─────────────────────────────
ADMIN_TEXTS = {
    "Tastatur_admin_manage": (
        "👑 مدیریت‌ها",
        "• افزودن مدیر: افزودن مدیر (ریپلای)\n"
        "• حذف مدیر: حذف مدیر (ریپلای)\n"
        "• لیست مدیران: لیست مدیران\n"
        "• پاکسازی مدیران: پاکسازی مدیران"
    ),
    "Tastatur_admin_ban": (
        "🚫 بن / رفع‌بن",
        "• بن کاربر: بن (ریپلای)\n"
        "• رفع بن: رفع بن (ریپلای)\n"
        "• لیست بن‌ها: لیست بن"
    ),
    "Tastatur_admin_mute": (
        "🔇 سکوت / رفع‌سکوت",
        "• سکوت: سکوت (ریپلای)\n"
        "• رفع سکوت: رفع سکوت (ریپلای)"
    ),
    "Tastatur_admin_warn": (
        "⚠️ اخطارها",
        "• اخطار: اخطار (ریپلای)\n"
        "• حذف اخطار: حذف اخطار (ریپلای)\n"
        "• لیست: لیست اخطار"
    ),
    "Tastatur_admin_pin": (
        "📌 پین / آن‌پین",
        "• پین: ریپلای + پین\n• حذف همه پین‌ها: حذف پین"
    ),
    "Tastatur_admin_clean": (
        "🧹 پاکسازی",
        "• پاکسازی عددی: پاکسازی 50\n• پاکسازی کامل: پاکسازی کامل / همه"
    ),
    "Tastatur_admin_lockgroup": (
        "🔐 قفل/باز گروه",
        "• قفل گروه: قفل گروه\n• باز گروه: باز گروه"
    ),
    "Tastatur_admin_autolock": (
        "🕒 قفل خودکار",
        "• فعال‌سازی: قفل خودکار گروه 23:00 07:00\n• غیرفعال: غیرفعال کردن قفل خودکار"
    ),
    "Tastatur_admin_alias": (
        "🧠 Alias (دستورات شخصی)",
        "• ساخت: افزودن دستور 'اخراج' → ban"
    ),
    "Tastatur_admin_tags": (
        "👥 تگ + اصل/لقب",
        "• تگ همه / فعال / غیرفعال / مدیران"
    ),
}

# ====================== 🧭 راهنمای مدیریت — بخش جدید ======================
HELP_TEXT = (
    "🧭 <b>راهنمای کامل مدیریت گروه</b>\n\n"
    "🔒 <b>قفل‌ها:</b>\n"
    "قفل [نوع] / بازکردن [نوع]  |  locks / unlock [type]\n"
    "مثال: قفل لینک، بازکردن عکس\n"
    "وضعیت قفل‌ها  |  lock status / locks\n\n"
    "📦 <b>قفل گروه:</b>\n"
    "قفل گروه / بازکردن گروه  |  lock group / unlock group\n"
    "قفل خودکار گروه [شروع] [پایان]  |  auto lock group\n"
    "غیرفعال کردن قفل خودکار  |  disable auto lock\n\n"
    "🚫 <b>فیلتر کلمات:</b>\n"
    "افزودن فیلتر [کلمه]  |  addfilter\n"
    "حذف فیلتر [کلمه]  |  delfilter\n"
    "لیست فیلترها  |  filters\n\n"
    "👑 <b>مدیریت مدیران:</b>\n"
    "افزودن مدیر (ریپلای)  |  addadmin\n"
    "حذف مدیر (ریپلای)  |  removeadmin\n"
    "لیست مدیران  |  admins\n"
    "پاکسازی مدیران  |  clearadmins\n\n"
    "👮 <b>مدیریت کاربران:</b>\n"
    "بن (ریپلای)  |  ban\n"
    "رفع بن (ریپلای)  |  unban\n"
    "لیست بن‌شده‌ها  |  listbans\n"
    "سکوت (ریپلای) [مدت]  |  mute\n"
    "رفع سکوت (ریپلای)  |  unmute\n"
    "لیست ساکت‌ها  |  listmutes\n"
    "اخطار (ریپلای)  |  warn\n"
    "رفع اخطار (ریپلای)  |  unwarn\n"
    "لیست اخطارها  |  listwarns\n\n"
    "👑 <b>مدیریت سودو:</b>\n"
    "افزودن سودو (ریپلای)  |  addsudo\n"
    "حذف سودو (ریپلای)  |  delsudo\n"
    "لیست سودوها  |  listsudos\n\n"
    "🧹 <b>پاکسازی:</b>\n"
    "پاکسازی [عدد/همه] / clean / delete / clear\n"
    "مثال: پاکسازی 50 — یا ریپلای برای حذف پیام کاربر خاص\n\n"
    "📌 <b>پین و آن‌پین:</b>\n"
    "پین (ریپلای) [دقیقه]  |  pin\n"
    "حذف پین‌ها  |  unpin\n\n"
    "📜 <b>لقب و اصل:</b>\n"
    "ثبت لقب [متن] / set nick [text]\n"
    "لقب / لقب من / حذف لقب / delnick\n"
    "ثبت اصل [متن] / set origin [text]\n"
    "اصل / اصل من / حذف اصل / delorigin\n\n"
    "🏷 <b>تگ‌ها:</b>\n"
    "تگ همه / تگ فعال / تگ غیرفعال / تگ مدیران / تگ [@کاربر]\n\n"
    "⚙️ <b>افزودن دستور سفارشی:</b>\n"
    "افزودن دستور 'کلمه جدید' → دستور اصلی\n"
    "مثال: افزودن دستور 'اخراج' → ban\n\n"
    "💬 <b>خوشامدگویی:</b>\n"
    "تنظیم خوشامد، عکس، متن، قوانین و زمان حذف پیام خوشامد\n\n"
    "📁 <b>سایر:</b>\n"
    "راهنما — نمایش همین لیست\n"
    "پنل — ورود به تنظیمات ربات\n\n"
    "📢 <b>کانال راهنما:</b>\n"
    "<a href='https://t.me/Taktakkun'>t.me/Taktakkun</a>"
)

async def show_help_menu(query):
    keyboard = [
        [InlineKeyboardButton("📢 کانال راهنما", url="https://t.me/Taktakkun")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")],
    ]
    return await query.edit_message_text(
        HELP_TEXT,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True,
    )

# ====================== ✳️ افزودن دستور (Alias) ======================
async def show_add_alias_help(query):
    text = (
        "✳️ افزودن دستور (Alias)\n\n"
        "با این قابلیت می‌تونی برای هر فرمان یک اسم فارسی/کوتاه بسازی.\n\n"
        "نمونه‌ها:\n"
        "• افزودن دستور 'اخراج' → ban\n"
        "• افزودن دستور 'سکوتش' -> mute\n"
        "• افزودن دستور 'بازگروه' = unlockgroup\n\n"
        "بعد از ساخت، همون کلمهٔ جدید مثل فرمان اصلی عمل می‌کنه ✅"
    )
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")]]
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# ====================== 💬 افزودن ریپلای ======================
async def show_add_reply_help(query):
    text = (
        "💬 افزودن ریپلای\n\n"
        "منظور از «ریپلای» اینه که روی یک پیام ریپلای می‌کنی و دستور ذخیره‌سازی می‌دی "
        "تا بعداً با یک کلمه، همون متن/پاسخ ارسال بشه.\n\n"
        "✅ الگوی پیشنهادی:\n"
        "• ریپلای روی پیام + افزودن ریپلای [کلید]\n"
        "مثال: ریپلای روی متن + افزودن ریپلای سلام\n"
        "از اون به بعد با نوشتن سلام، ربات پاسخ ذخیره‌شده رو می‌فرسته.\n\n"
        "🔒 محل ذخیره و سطح دسترسی بستگی به پیاده‌سازی شما دارد."
    )
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")]]
    return await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_welcome_menu(query):
    text = (
        "💐 خوشامدگویی اعضای جدید\n\n"
        "با دستور خوشامد در گروه، همین پنلِ راهنما نمایش داده می‌شود.\n\n"
        "امکانات پیشنهادی (بسته به هسته شما):\n"
        "• 🖼 عکس خوشامد (آپلود دلخواه)\n"
        "• 📝 متن خوشامد (قابل قالب‌بندی، متغیرها: {name}، {id})\n"
        "• 🔗 لینک/قوانین زیر پیام\n"
        "• ⏱ حذف خودکار پیام خوشامد بعد از X ثانیه\n"
        "• 🔛 روشن/خاموش کردن سیستم خوشامد\n\n"
        "نمونه دستورها (راهنمایی):\n"
        "• خوشامد فعال / خوشامد غیرفعال\n"
        "• تنظیم متن خوشامد ...\n"
        "• تنظیم زمان حذف خوشامد 10  (ثانیه)\n"
        "• تنظیم لینک قوانین [https://t.me/](https://t.me/...)\n\n"
        "پیاده‌سازی ذخیره/خواندن تنظیمات بسته به فایل/دیتابیس شماست."
    )
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")]]
    return await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
