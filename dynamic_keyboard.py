import json
import os
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

FILE = "dynamic_buttons.json"

# -----------------------------
# اگر فایل وجود نداشت → ایجادش کن
# -----------------------------
if not os.path.exists(FILE):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(["فال", "جوک"], f, ensure_ascii=False, indent=2)


# -----------------------------
# گرفتن لیست دکمه‌ها
# -----------------------------
def load_buttons():
    with open(FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------------
# ذخیره دکمه‌ها
# -----------------------------
def save_buttons(buttons):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(buttons, f, ensure_ascii=False, indent=2)


# -----------------------------
# ساخت کیبورد داینامیک
# -----------------------------
def build_keyboard():
    buttons = load_buttons()
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


# ===============================
#  /start → نمایش کیبورد
# ===============================
async def start_fixed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👇 یکی از گزینه‌ها رو انتخاب کن:", 
                                    reply_markup=build_keyboard())


# ===============================
#  اضافه کردن دکمه
# ===============================
async def add_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("❗ استفاده: /addbtn متن_دکمه")

    new_button = " ".join(context.args)

    buttons = load_buttons()
    if new_button in buttons:
        return await update.message.reply_text("⚠️ این دکمه از قبل وجود دارد!")

    buttons.append(new_button)
    save_buttons(buttons)

    await update.message.reply_text("✅ دکمه اضافه شد!", reply_markup=build_keyboard())


# ===============================
#  حذف دکمه
# ===============================
async def remove_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("❗ استفاده: /delbtn متن_دکمه")

    btn = " ".join(context.args)

    buttons = load_buttons()

    if btn not in buttons:
        return await update.message.reply_text("❌ همچین دکمه‌ای وجود ندارد!")

    buttons.remove(btn)
    save_buttons(buttons)

    await update.message.reply_text("🗑 دکمه حذف شد!", reply_markup=build_keyboard())


# ===============================
#  لیست دکمه‌ها
# ===============================
async def list_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = load_buttons()
    txt = "📌 دکمه‌های فعلی:\n\n" + "\n".join([f"— {b}" for b in buttons])
    await update.message.reply_text(txt)


# ===============================
#  وقتی کاربر روی دکمه کلیک میکند
# ===============================
async def fixed_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    buttons = load_buttons()

    if text in buttons:
        return await update.message.reply_text(text)
        MAIN_KEYBOARD = build_keyboard()

    # اگر دکمه نباشد → هیچ کاری نکن
