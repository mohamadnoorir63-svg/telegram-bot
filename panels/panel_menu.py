# ====================== 🧭 پنل مدیریت گروه — نسخه پیشرفته با کنترل زنده قفل‌ها ======================
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

    # 🔒 بخش قفل‌ها
    if data == "Tastatur_locks":
        return await show_lock_menu(query, context)

    # 🧩 دسته‌بندی قفل‌ها
    if data == "lock_cat_media":
        locks_map = {k: LOCK_TYPES[k] for k in ["photos", "videos", "gifs", "files", "voices", "vmsgs"]}
        return await show_lock_category(query, context, "🖼 رسانه‌ها", locks_map)

    if data == "lock_cat_text":
        locks_map = {k: LOCK_TYPES[k] for k in ["text", "caption", "emoji", "english", "arabic"]}
        return await show_lock_category(query, context, "💬 پیام‌ها و متون", locks_map)

    if data == "lock_cat_members":
        locks_map = {k: LOCK_TYPES[k] for k in ["bots", "join", "joinmsg"]}
        return await show_lock_category(query, context, "👥 اعضا و ربات‌ها", locks_map)

    if data == "lock_cat_links":
        locks_map = {k: LOCK_TYPES[k] for k in ["links", "ads", "usernames", "mention"]}
        return await show_lock_category(query, context, "🌐 لینک‌ها و تبلیغ", locks_map)

    # ==================== سایر بخش‌ها ====================
    sections = {
        "Tastatur_users": "👮 <b>مدیریت کاربران</b>\n\n• بن / رفع‌بن\n• اخطار / حذف‌اخطار\n• سکوت / رفع‌سکوت\n• افزودن یا حذف مدیر\n• لیست مدیران",
        "Tastatur_settings": "⚙️ <b>تنظیمات گروه</b>\n\n• قفل یا بازکردن کل گروه\n• فعال‌سازی خوش‌آمدگویی\n• پاکسازی گروه\n• تنظیم حالت یادگیری",
        "Tastatur_stats": "📊 <b>آمار و گزارش</b>\n\n• آمار کاربران و پیام‌ها\n• فعالیت مدیران\n• اعضای فعال و غیرفعال",
        "Tastatur_fun": "🎮 <b>سرگرمی‌ها و ابزارها</b>\n\n🌤 آب‌وهوا | 🔮 فال | 😂 جوک | 🪪 ابزارها و فونت",
        "Tastatur_alias": "🧩 <b>دستورات شخصی (Alias)</b>\n\nمثلاً:\n<code>افزودن دستور \"گمشو\" → ban</code>",
        "Tastatur_welcome": "👋 <b>سیستم خوشامدگویی</b>\n\nارسال پیام خوش‌آمد خودکار به تازه‌واردها 💬"
    }
    if data in sections:
        return await _Tastatur_section(query, sections[data])


# ========================= 🔙 زیرمنوها و قفل‌ها =========================

async def _Tastatur_section(query, text):
    keyboard = [
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back"),
            InlineKeyboardButton("❌ بستن", callback_data="Tastatur_close")
        ]
    ]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


# ====================== 🔒 کنترل و نمایش قفل‌ها ======================

async def show_lock_menu(query, context):
    """صفحه‌ی دسته‌بندی قفل‌ها"""
    text = (
        "🔐 <b>مدیریت قفل‌های گروه</b>\n\n"
        "نوع قفلی که می‌خواهی تنظیم کنی را انتخاب کن 👇"
    )
    keyboard = [
        [InlineKeyboardButton("🖼 رسانه‌ها", callback_data="lock_cat_media")],
        [InlineKeyboardButton("💬 پیام‌ها و متون", callback_data="lock_cat_text")],
        [InlineKeyboardButton("👥 اعضا و ربات‌ها", callback_data="lock_cat_members")],
        [InlineKeyboardButton("🌐 لینک‌ها و تبلیغ", callback_data="lock_cat_links")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back")]
    ]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def show_lock_category(query, context, category, locks_map):
    """نمایش وضعیت هر قفل در دسته مربوطه"""
    chat_id = query.message.chat.id
    locks = _locks_get(chat_id)
    keyboard, row = [], []

    for key, label in locks_map.items():
        state = locks.get(key, False)
        icon = "🔒 فعال" if state else "🔓 غیرفعال"
        btn = InlineKeyboardButton(f"{label} | {icon}", callback_data=f"toggle_lock:{key}")
        row.append(btn)
        if len(row) == 1:  # یک‌ستونه زیباتر دیده می‌شود
            keyboard.append(row)
            row = []

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_locks")])
    text = f"⚙️ <b>تنظیمات قفل‌های {category}</b>\n\nروی هر مورد بزن تا روشن یا خاموش شود 👇"
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def toggle_lock_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """روشن / خاموش کردن قفل با دکمه"""
    query = update.callback_query
    await query.answer()
    data = query.data
    if not data.startswith("toggle_lock:"):
        return

    chat_id = query.message.chat.id
    lock_key = data.split(":", 1)[1]

    # وضعیت فعلی را برعکس کن
    locks = _locks_get(chat_id)
    current_state = locks.get(lock_key, False)
    _locks_set(chat_id, lock_key, not current_state)
    _save_json(GROUP_CTRL_FILE, group_data)

    # بازسازی صفحه فعلی
    categories = {
        "media": ["photos", "videos", "gifs", "files", "voices", "vmsgs"],
        "text": ["text", "caption", "emoji", "english", "arabic"],
        "members": ["bots", "join", "joinmsg"],
        "links": ["links", "ads", "usernames", "mention"]
    }

    for cat, keys in categories.items():
        if lock_key in keys:
            locks_map = {k: LOCK_TYPES[k] for k in keys}
            category_name = {
                "media": "🖼 رسانه‌ها",
                "text": "💬 پیام‌ها و متون",
                "members": "👥 اعضا و ربات‌ها",
                "links": "🌐 لینک‌ها و تبلیغ"
            }[cat]
            await show_lock_category(query, context, category_name, locks_map)
            return
