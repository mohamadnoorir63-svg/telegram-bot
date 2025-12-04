import json
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from bot import SUDO_IDS   # لیست سودوها از فایل اصلی

FILE = "data/reply_keyboard.json"


# ---------------------------------------------------
# 📁 بارگذاری / ذخیره
# ---------------------------------------------------
def load_data():
    if not os.path.exists(FILE):
        base = {
            "menus": {
                "main": [
                    ["🙂 یه جوک بگو", "🔮 فال بگیر"],
                    ["❓ راهنما"]
                ]
            },
            "links": {}
        }
        save_data(base)
        return base

    with open(FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------
# 📌 نمایش یک منو
# ---------------------------------------------------
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, menu="main"):
    data = load_data()
    kb = data["menus"].get(menu, [])

    # ✨ اگر سودو است → Admin panel را اضافه کن
    user_id = update.effective_user.id
    kb = [row[:] for row in kb]

    if user_id in SUDO_IDS:
        if ["⚙️ Admin"] not in kb:
            kb.append(["⚙️ Admin"])

    markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
    context.user_data["current_menu"] = menu

    if update.message:
        await update.message.reply_text("👇 منوت:", reply_markup=markup)
    else:
        await update.callback_query.message.reply_text("👇 منوت:", reply_markup=markup)


# ---------------------------------------------------
# 🎛 پنل مدیریت سودو
# ---------------------------------------------------
ADMIN_MENU = [
    ["➕ افزودن دکمه", "❌ حذف دکمه"],
    ["✏️ تغییر نام دکمه"],
    ["📂 ساخت زیرمنو"],
    ["🔙 بازگشت"]
]


async def open_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in SUDO_IDS:
        return await update.message.reply_text("⛔ فقط سودو!")

    markup = ReplyKeyboardMarkup(ADMIN_MENU, resize_keyboard=True)
    context.user_data["admin_mode"] = True

    await update.message.reply_text("⚙️ پنل مدیریت:", reply_markup=markup)


# ---------------------------------------------------
# 🎚 کنترل دکمه‌های پنل مدیریت
# ---------------------------------------------------
async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("admin_mode"):
        return

    text = update.message.text

    if text == "➕ افزودن دکمه":
        return await add_button(update, context)

    elif text == "❌ حذف دکمه":
        return await remove_button(update, context)

    elif text == "✏️ تغییر نام دکمه":
        return await rename_button(update, context)

    elif text == "📂 ساخت زیرمنو":
        return await create_submenu(update, context)

    elif text == "🔙 بازگشت":
        context.user_data["admin_mode"] = False
        return await show_menu(update, context)


# ---------------------------------------------------
# ➕ افزودن دکمه
# ---------------------------------------------------
async def add_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu = context.user_data.get("current_menu", "main")
    await update.message.reply_text("✏️ متن دکمه جدید را بفرست:")
    context.user_data["add_btn"] = menu


async def handle_add_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu = context.user_data.get("add_btn")
    if not menu:
        return

    text = update.message.text.strip()
    data = load_data()

    data["menus"][menu].append([text])
    save_data(data)

    context.user_data["add_btn"] = None
    await update.message.reply_text("✅ دکمه اضافه شد.")
    await show_menu(update, context, menu)


# ---------------------------------------------------
# ❌ حذف دکمه
# ---------------------------------------------------
async def remove_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu = context.user_data.get("current_menu", "main")
    kb = load_data()["menus"].get(menu, [])

    msg = "📌 دکمه‌های موجود:\n"
    for row in kb:
        for b in row:
            msg += f"• {b}\n"

    await update.message.reply_text(msg + "\n✏️ نام دکمه‌ای که می‌خوای حذف کنی را بفرست:")
    context.user_data["remove_btn"] = menu


async def handle_remove_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu = context.user_data.get("remove_btn")
    if not menu:
        return

    btn = update.message.text.strip()
    data = load_data()

    new_rows = []
    for row in data["menus"][menu]:
        if btn not in row:
            new_rows.append(row)

    data["menus"][menu] = new_rows
    save_data(data)

    context.user_data["remove_btn"] = None
    await update.message.reply_text("🗑 دکمه حذف شد.")
    await show_menu(update, context, menu)


# ---------------------------------------------------
# ✏️ تغییر نام دکمه
# ---------------------------------------------------
async def rename_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✏️ نام فعلی دکمه را بفرست:")
    context.user_data["rename_step"] = "old"


async def handle_rename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("rename_step")
    menu = context.user_data.get("current_menu", "main")

    if not step:
        return

    if step == "old":
        context.user_data["old_name"] = update.message.text.strip()
        context.user_data["rename_step"] = "new"
        return await update.message.reply_text("✏️ نام جدید را بفرست:")

    if step == "new":
        old = context.user_data["old_name"]
        new = update.message.text.strip()

        data = load_data()

        for row in data["menus"][menu]:
            for i, b in enumerate(row):
                if b == old:
                    row[i] = new

        save_data(data)

        context.user_data["rename_step"] = None
        await update.message.reply_text("✨ نام دکمه تغییر کرد.")
        await show_menu(update, context, menu)


# ---------------------------------------------------
# 📂 ساخت زیرمنو
# ---------------------------------------------------
async def create_submenu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📁 نام دکمه‌ای که تبدیل به زیرمنو می‌شود را بفرست:")
    context.user_data["make_submenu"] = True


async def handle_create_submenu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("make_submenu"):
        return

    btn = update.message.text.strip()
    menu = context.user_data.get("current_menu", "main")

    submenu_id = f"{menu}_{btn}_submenu"

    data = load_data()

    data["menus"][submenu_id] = [["🔙 بازگشت"]]
    data["links"][submenu_id] = menu

    save_data(data)

    context.user_data["make_submenu"] = None
    await update.message.reply_text("📂 زیرمنو ساخته شد.")
    await show_menu(update, context, submenu_id)


# ---------------------------------------------------
# 🔙 بازگشت و حرکت بین منوها
# ---------------------------------------------------
async def handle_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    menu = context.user_data.get("current_menu", "main")
    data = load_data()

    # برگشت
    if text == "🔙 بازگشت":
        parent = data["links"].get(menu, "main")
        return await show_menu(update, context, parent)

    # حرکت به زیرمنو
    submenu = f"{menu}_{text}_submenu"
    if submenu in data["menus"]:
        return await show_menu(update, context, submenu)
