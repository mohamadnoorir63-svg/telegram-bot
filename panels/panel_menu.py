# ====================== 🧭 پنل راهنمای فارسی پیشرفته و رنگی (چندمرحله‌ای دو ستونه) ======================
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# 🌈 رنگ‌بندی و طراحی زیبا
MAIN_TITLE = "🌟 <b>پنل راهنمای ربات مدیریت گروه</b>\n\n🧭 از منوی زیر یکی از بخش‌ها را انتخاب کنید 👇"

# 🎨 صفحه‌ی اصلی پنل
async def Tastatur_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    # 🚫 بررسی: فقط در گروه‌ها مجاز باشد
    if chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text(
            "❌ این پنل فقط در داخل گروه‌ها قابل استفاده است!",
            parse_mode="HTML"
        )

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
        [
            InlineKeyboardButton("👋 خوشامدگویی", callback_data="Tastatur_welcome")
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


# 🎛 هندلر دکمه‌ها
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

    # ==================== 🔒 بخش قفل‌ها ====================
    if data == "Tastatur_locks":
        text = (
            "🔐 <b>مدیریت قفل‌ها</b>\n\n"
            "🔸 <b>دستورات فارسی:</b>\n"
            "• قفل لینک / باز لینک\n"
            "• قفل مدیا / باز مدیا\n"
            "• قفل عکس، ویدیو، فایل، استیکر\n\n"
            "🔹 <b>دستورات انگلیسی:</b>\n"
            "<code>lock links</code> / <code>unlock links</code>\n"
            "<code>lock media</code> / <code>unlock media</code>"
        )
        return await _Tastatur_section(query, text)

    # ==================== 👮 مدیریت کاربران ====================
    if data == "Tastatur_users":
        text = (
            "👮 <b>مدیریت کاربران</b>\n\n"
            "• بن / رفع‌بن\n"
            "• اخطار / حذف‌اخطار\n"
            "• سکوت / رفع‌سکوت\n"
            "• افزودن یا حذف مدیر\n"
            "• مشاهده لیست مدیران"
        )
        return await _Tastatur_section(query, text)

    # ==================== ⚙️ تنظیمات ====================
    if data == "Tastatur_settings":
        text = (
            "⚙️ <b>تنظیمات گروه</b>\n\n"
            "• قفل کل گروه یا باز کردن گروه\n"
            "• فعال یا غیرفعال کردن خوش‌آمدگویی\n"
            "• پاکسازی گروه با دستور پاکسازی عددی\n"
            "• تغییر حالت یادگیری ربات"
        )
        return await _Tastatur_section(query, text)

    # ==================== 📊 آمار ====================
    if data == "Tastatur_stats":
        text = (
            "📊 <b>آمار و وضعیت گروه</b>\n\n"
            "• نمایش تعداد کاربران\n"
            "• تعداد پیام‌های امروز و هفته\n"
            "• اعضای فعال و غیرفعال\n"
            "• مدیران برتر بر اساس فعالیت"
        )
        return await _Tastatur_section(query, text)

    # ==================== 🎮 سرگرمی ====================
    if data == "Tastatur_fun":
        text = (
            "🎮 <b>سرگرمی و ابزارها</b>\n\n"
            "• فال روزانه / جملات انگیزشی\n"
            "• جوک و لطیفه تصادفی\n"
            "• منشن کاربران (تگ‌همه / تگ‌فعال)\n"
            "• ابزارهای کوچک و جالب دیگر 😄"
        )
        return await _Tastatur_section(query, text)

    # ==================== 🧩 دستورات شخصی ====================
    if data == "Tastatur_alias":
        text = (
            "🧩 <b>دستورات شخصی (Alias)</b>\n\n"
            "با این قابلیت می‌تونی برای دستورات، نام جدید بسازی 👇\n\n"
            "🔹 <b>افزودن alias جدید:</b>\n"
            "<code>alias [دستور اصلی] [نام جدید]</code>\n"
            "مثلاً:\n"
            "<code>alias ban محروم</code>\n\n"
            "🔹 <b>لیست aliasها:</b>\n"
            "<code>listsudo</code> یا دستور مخصوص نمایش"
        )
        return await _Tastatur_section(query, text)

    # ==================== 👋 خوشامدگویی ====================
    if data == "Tastatur_welcome":
        text = (
            "👋 <b>سیستم خوشامدگویی</b>\n\n"
            "با فعال کردن خوشامد، وقتی عضو جدید وارد گروه میشه، ربات به‌صورت خودکار پیام خوشامد ارسال می‌کنه 💬\n\n"
            "🔸 می‌تونی پیام خوشامد رو تغییر بدی یا غیرفعالش کنی.\n"
            "🔹 پیام خوشامد می‌تونه شامل نام کاربر یا لینک گروه هم باشه 🌐"
        )
        return await _Tastatur_section(query, text)


# 🔙 ساخت زیرمنو با بازگشت و بستن
async def _Tastatur_section(query, text):
    keyboard = [
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data="Tastatur_back"),
            InlineKeyboardButton("❌ بستن", callback_data="Tastatur_close")
        ]
    ]
    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
