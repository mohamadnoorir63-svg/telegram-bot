from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

# ============================
# 🎛 دکمه‌های صفحه اول
# ============================
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🎭 سرگرمی", "📸 پروفایل"],
        ["🎵 موزیک‌ها", "📝 متن‌ها"],
    ],
    resize_keyboard=True
)

# ============================
# 🎛 زیرمنوها
# ============================

ENTERTAINMENT_MENU = ReplyKeyboardMarkup(
    [
        ["فال", "جوک"],
        ["🔙 بازگشت"]
    ],
    resize_keyboard=True
)

PROFILE_MENU = ReplyKeyboardMarkup(
    [
        ["عکس پروفایل دختر 👧", "عکس پروفایل پسر 👦"],
        ["🔙 بازگشت"]
    ],
    resize_keyboard=True
)

MUSIC_MENU = ReplyKeyboardMarkup(
    [
        ["موزیک غمگین 🎧", "موزیک شاد 🎵"],
        ["🔙 بازگشت"]
    ],
    resize_keyboard=True
)

TEXT_MENU = ReplyKeyboardMarkup(
    [
        ["🍁دیپ تاک آلمانی🍁", "🍁دیپ تاک فارسی🍁"],
        ["راز موفقیت", "بیو"],
        ["🔙 بازگشت"]
    ],
    resize_keyboard=True
)


# ============================
# 📌 /start → نمایش منو اصلی
# ============================
async def start_fixed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["menu"] = "main"
    await update.message.reply_text("👇 یکی از منوها رو انتخاب کن:", reply_markup=MAIN_KEYBOARD)


# ============================
# 📌 هندلر → مدیریت زیرمنوها
# ============================
async def fixed_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    current = context.user_data.get("menu", "main")

    # ======================
    # 📌 بازگشت
    # ======================
    if text == "🔙 بازگشت":
        context.user_data["menu"] = "main"
        return await update.message.reply_text("🔙 برگشتی به منوی اصلی:", reply_markup=MAIN_KEYBOARD)

    # ======================
    # 📌 ورود به زیرمنوها
    # ======================
    if text == "🎭 سرگرمی":
        context.user_data["menu"] = "ent"
        return await update.message.reply_text("🎭 منوی سرگرمی:", reply_markup=ENTERTAINMENT_MENU)

    if text == "📸 پروفایل":
        context.user_data["menu"] = "profile"
        return await update.message.reply_text("📸 انتخاب کن:", reply_markup=PROFILE_MENU)

    if text == "🎵 موزیک‌ها":
        context.user_data["menu"] = "music"
        return await update.message.reply_text("🎵 موزیک مورد نظرت؟", reply_markup=MUSIC_MENU)

    if text == "📝 متن‌ها":
        context.user_data["menu"] = "texts"
        return await update.message.reply_text("📝 متن‌ها:", reply_markup=TEXT_MENU)

    # ======================
    # 📌 داخل زیرمنو → فقط متن را بفرست
    # ======================
    await update.message.reply_text(text)
