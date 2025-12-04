import json
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes

FILE = "data/reply_keyboard.json"

def load_keyboard():
    if not os.path.exists(FILE):
        return {"keyboard": []}
    with open(FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_keyboard(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------
# 📌 نمایش کیبورد
# ---------------------------------------------------
async def show_reply_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_keyboard()
    kb = data.get("keyboard", [])
    markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
    await update.message.reply_text("👇 منوی اصلی:", reply_markup=markup)

# ---------------------------------------------------
# ➕ افزودن دکمه
# ---------------------------------------------------
async def add_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != 8588347189:
        return await update.message.reply_text("⛔ فقط مدیر اصلی!")

    await update.message.reply_text("✏️ متن دکمه جدید را ارسال کن:")
    context.user_data["await_add_btn"] = True

async def handle_add_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("await_add_btn"):
        return

    text = update.message.text
    data = load_keyboard()

    # اضافه به ردیف جدید
    data["keyboard"].append([text])

    save_keyboard(data)
    context.user_data["await_add_btn"] = False
    await update.message.reply_text("✅ دکمه اضافه شد.")
    await show_reply_keyboard(update, context)

# ---------------------------------------------------
# ❌ حذف دکمه
# ---------------------------------------------------
async def remove_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != 8588347189:
        return await update.message.reply_text("⛔ فقط مدیر اصلی!")

    kb = load_keyboard()["keyboard"]

    text = "📌 دکمه‌های موجود:\n"
    for row in kb:
        for btn in row:
            text += f"• {btn}\n"

    await update.message.reply_text(text + "\n✏️ نام دکمه‌ای که می‌خوای حذف کنی را بفرست:")
    context.user_data["await_remove_btn"] = True

async def handle_remove_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("await_remove_btn"):
        return

    btn = update.message.text
    data = load_keyboard()

    for row in data["keyboard"]:
        if btn in row:
            row.remove(btn)

    # حذف ردیف‌های خالی
    data["keyboard"] = [r for r in data["keyboard"] if r]

    save_keyboard(data)
    context.user_data["await_remove_btn"] = False
    await update.message.reply_text("🗑 دکمه حذف شد.")
    await show_reply_keyboard(update, context)
