from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

# ============================
# 🎛 دکمه‌های ثابت
# ============================
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["فال", "جوک"],
        ["راز موفقیت", "بیو"],
        ["عکس پروفایل دختر 👧", "عکس پروفایل پسر 👦"],
        ["موزیک غمگین 🎧", "موزیک شاد 🎵"],
        ["/start"]
    ],
    resize_keyboard=True
)

# ============================
# 📌 هندلر اصلی → فقط متن دکمه را برگرداند
# ============================
async def fixed_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    await update.message.reply_text(text)
