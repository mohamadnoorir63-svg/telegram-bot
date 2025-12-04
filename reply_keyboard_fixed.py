from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

# ============================
# 🎛 دکمه‌های ثابت
# ============================
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["فال 🔮", "جوک 🙂"],
        ["راز موفقیت 💡", "بیو ✨"],
        ["عکس پروفایل دختر 👧", "عکس پروفایل پسر 👦"],
        ["موزیک غمگین 🎧", "موزیک شاد 🎵"]
    ],
    resize_keyboard=True
)

# ============================
# 📌 /start → نمایش کیبورد
# ============================
async def start_fixed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👇 یکی از گزینه‌ها رو انتخاب کن:", reply_markup=MAIN_KEYBOARD)

# ============================
# 📌 هندلر اصلی → فقط متن دکمه را برگرداند
# ============================
async def fixed_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    await update.message.reply_text(text)
