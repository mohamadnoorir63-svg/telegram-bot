# ====================== 🧭 پنل مدیریت گروه — نسخه پیشرفته با کنترل زنده و زیرمنوی تنظیمات ======================
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from group_control.group_control import _locks_get, _locks_set, _save_json, group_data, GROUP_CTRL_FILE, LOCK_TYPES


# 🌟 عنوان اصلی
MAIN_TITLE = "🌟 <b>پنل راهنمای ربات مدیریت گروه</b>\n\n🧭 یکی از بخش‌های زیر را انتخاب کنید 👇"


# 🎨 منوی اصلی
async def Tastatur_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text("❌ این پنل فقط در داخل گروه‌ها قابل استفاده است!", parse_mode="HTML")

    keyboard = [
        [
            InlineKeyboardButton("🔒 قفل‌ها", callback_data="Tastatur_locks"),
            InlineKeyboardButton("👮 کاربران", callback_data="Tastatur_users")
        ],
        [
            InlineKeyboardButton("⚙️ تنظیمات", callback_data="Tastatur_settings"),
            InlineKeyboardButton("📊 آمار و گزارش", callback_data="Tastatur_stats")
        ],
        [
            InlineKeyboardButton("🎮 سرگرمی‌ها", callback_data="Tastatur_fun"),
            InlineKeyboardButton("🧩 دستورات شخصی", callback_data="Tastatur_alias")
        ],
        [InlineKeyboardButton("👋 خوشامدگویی", callback_data="Tastatur_welcome")],
        [InlineKeyboardButton("❌ بستن پنل", callback_data="Tastatur_close")]
    ]

    if update.message:
        await update.message.reply_text(MAIN_TITLE, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.edit_message_text(MAIN_TITLE, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


# 🎛 هندلر دکمه‌ها
async def Tastatur_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    # ❌ بستن
    if data == "Tastatur_close":
        return await query.message.delete()

    # 🔙 بازگشت به منوی اصلی
    if data == "Tastatur_back":
        return await Tastatur_menu(update, context)

    # ================= 🔒 بخش قفل‌ها =================
    if data == "Tastatur_locks":
        return await show_lock_menu(query, context)

    # ================= ⚙️ زیرمنوی تنظیمات =================
    if data == "Tastatur_settings":
        return await show_settings_menu(query)

    # 🔧 زیرمنوی قفل‌ها در بخش تنظیمات
    if data == "settings_locks":
        return await show_settings_locks(query)

    # 📋 سایر زیرمنوهای تنظیمات
    if data == "settings_lists":
        return await show_text_section(query, "📜 لیست‌ها", "لیست فیلترها، اخطارها و مدیران فعال در گروه.")
    if data == "settings_help":
        return await show_text_section(query, "❓ راهنما", "در این بخش می‌تونی با نحوه‌ی کار دستورات آشنا بشی.")
    if data == "settings_advanced":
        return await show_text_section(query, "⚙️ تنظیمات پیشرفته", "تنظیمات خودکار، زمان‌بندی قفل‌ها و تنظیم خوشامد خودکار.")

    # 🎯 سایر بخش‌های اطلاعاتی (کاربران، آمار، سرگرمی و...)
    simple_sections = {
        "Tastatur_users": "👮 <b>مدیریت کاربران</b>\n\n• بن / رفع‌بن\n• سکوت / رفع‌سکوت\n• افزودن مدیر\n• لیست مدیران",
        "Tastatur_stats": "📊 <b>آمار گروه</b>\n\n• تعداد کاربران\n• تعداد پیام‌ها\n• اعضای فعال",
        "Tastatur_fun": "🎮 <b>سرگرمی‌ها</b>\n\nفال، جوک، آب‌وهوا، بیو، فونت و ابزارهای روزانه 😄",
        "Tastatur_alias": "🧩 <b>دستورات شخصی (Alias)</b>\n\nمثلاً:\n<code>افزودن دستور \"گمشو\" → ban</code>",
        "Tastatur_welcome": "👋 <b>سیستم خوشامدگویی</b>\n\nارسال پیام خوش‌آمد خودکار به تازه‌واردها 💬"
    }
    if data in simple_sections:
        return await show_text_section(query, "ℹ️ اطلاعات", simple_sections[data])
        # ====================== 🔧 زیرمنوهای تنظیمات و قفل‌ها ======================

async def show_settings_menu(query):
    """منوی اصلی تنظیمات"""
    text = "⚙️ <b>تنظیمات گروه</b>\n\nیکی از بخش‌های زیر را انتخاب کنید 👇"
    keyboard = [
        [InlineKeyboardButton("🔒 قفل‌ها", callback_data="settings_locks")],
        [InlineKeyboardButton("📜 لیست‌ها", callback_data="settings_lists")],
        [InlineKeyboardButton("❓ راهنما", callback_data="settings_help")],
        [InlineKeyboardButton("⚙️ تنظیمات پیشرفته", callback_data="settings_advanced")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")]
    ]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def show_text_section(query, title, text):
    """نمایش متن‌های ساده تنظیمات"""
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_settings")]]
    await query.edit_message_text(f"<b>{title}</b>\n\n{text}", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


# ====================== 🔐 کنترل و صفحه‌بندی قفل‌ها ======================

async def show_settings_locks(query):
    """اولین صفحه‌ی قفل‌ها"""
    await show_lock_page(query, page=1)


async def show_lock_page(query, page=1):
    """صفحه‌بندی قفل‌ها (۳ صفحه شامل ۲۵ قفل)"""
    chat_id = query.message.chat.id
    locks = _locks_get(chat_id)

    # دیکشنری همه قفل‌ها
    all_locks = {
        1: ["links", "hyperlinks", "hashtags", "usernames", "english", "persian", "text", "telegramservice", "emoji", "badwords",
            "forward", "inlinebtn", "games", "hidden", "addbots", "bots", "editmsg", "editmedia"],
        2: ["photos", "videos", "files", "stickers", "audios", "gifs", "location", "contact", "animations", "voice", "commands", "selfie"],
        3: ["pin", "commands2", "mention", "newmember", "story", "reply", "foreignreply", "poll"]
    }

    current = all_locks.get(page, [])
    keyboard = []
    row = []

    for lock_key in current:
        state = locks.get(lock_key, False)
        icon = "✅" if state else "❌"
        label = LOCK_TYPES.get(lock_key, lock_key)
        btn = InlineKeyboardButton(f"{icon} {label}", callback_data=f"toggle_lock:{lock_key}")
        row.append(btn)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # دکمه‌های صفحه‌بندی
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ صفحه قبل", callback_data=f"lock_page:{page-1}"))
    if page < 3:
        nav_buttons.append(InlineKeyboardButton("صفحه بعد ➡️", callback_data=f"lock_page:{page+1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_settings")])

    await query.edit_message_text(
        f"🔐 <b>پنل تنظیمات قفل‌ها — بخش {page}</b>\n\nبا لمس هر مورد می‌تونی فعال یا غیرفعال کنی 👇",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# 📌 هندلر تغییر صفحه
async def handle_lock_page_switch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data.startswith("lock_page:"):
        page = int(data.split(":")[1])
        await show_lock_page(query, page)
        return

# ⚙️ تغییر وضعیت هر قفل
async def toggle_lock_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if not data.startswith("toggle_lock:"):
        return

    chat_id = query.message.chat.id
    lock_key = data.split(":", 1)[1]
    locks = _locks_get(chat_id)
    new_state = not locks.get(lock_key, False)
    _locks_set(chat_id, lock_key, new_state)
    _save_json(GROUP_CTRL_FILE, group_data)

    await show_lock_page(query, 1)  # به همان صفحه برگردد
