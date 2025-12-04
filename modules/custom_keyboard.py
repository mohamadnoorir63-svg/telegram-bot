import json
import os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes

DATA_FILE = "data/custom_keyboard.json"

# ------------------ 📌 بارگذاری و ذخیره ------------------

def load_keyboard():
    if not os.path.exists(DATA_FILE):
        return {"main": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_keyboard(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ------------------ 📌 نمایش منوی پویا ------------------

async def show_dynamic_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE, level="main"):
    kb = load_keyboard()

    # اگر سطح موجود نبود → ایجادش کن
    if level not in kb:
        kb[level] = []
        save_keyboard(kb)

    # ساخت دکمه‌ها
    keyboard = []
    for btn in kb[level]:
        keyboard.append([
            InlineKeyboardButton(btn["name"], callback_data=f"ck_open:{btn['id']}")
        ])

    # دکمه‌های مدیریتی
    keyboard.append([
        InlineKeyboardButton("➕ افزودن دکمه", callback_data=f"ck_add:{level}")
    ])

    if level != "main":
        keyboard.append([
            InlineKeyboardButton("⬅️ برگشت", callback_data="ck_open:main")
        ])

    markup = InlineKeyboardMarkup(keyboard)
    text = f"📂 <b>منوی پویا ({level})</b>"
    await update.message.reply_text(text, reply_markup=markup, parse_mode="HTML")


# ------------------ 📌 مدیریت دکمه‌ها ------------------

async def custom_keyboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    kb = load_keyboard()

    # باز کردن یک سطح جدید
    if data.startswith("ck_open:"):
        level = data.split(":")[1]

        keyboard = []
        for btn in kb[level]:
            keyboard.append([
                InlineKeyboardButton(btn["name"], callback_data=f"ck_open:{btn['id']}"),
                InlineKeyboardButton("✏️", callback_data=f"ck_rename:{btn['id']}"),
                InlineKeyboardButton("🗑", callback_data=f"ck_delete:{btn['id']}")
            ])

        keyboard.append([InlineKeyboardButton("➕ افزودن", callback_data=f"ck_add:{level}")])

        if level != "main":
            keyboard.append([InlineKeyboardButton("⬅️ برگشت", callback_data="ck_open:main")])

        await query.edit_message_text(
            f"📁 <b>مدیریت منو → {level}</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return

    # افزودن دکمه
    if data.startswith("ck_add:"):
        level = data.split(":")[1]
        context.user_data["ck_add_level"] = level
        await query.edit_message_text("✍️ نام دکمه جدید را ارسال کنید:")
        context.user_data["await_ck_add"] = True
        return

    # تغییر نام
    if data.startswith("ck_rename:"):
        btn_id = data.split(":")[1]
        context.user_data["ck_rename_id"] = btn_id
        context.user_data["await_ck_rename"] = True
        await query.edit_message_text("✏️ نام جدید را ارسال کنید:")
        return

    # حذف دکمه
    if data.startswith("ck_delete:"):
        btn_id = data.split(":")[1]

        # حذف از هر سطح
        for level in kb:
            kb[level] = [b for b in kb[level] if b["id"] != btn_id]

        save_keyboard(kb)
        await query.edit_message_text("🗑 دکمه حذف شد!")
        return


# ------------------ 📌 دریافت متن دکمه ------------------

async def custom_keyboard_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    kb = load_keyboard()

    # افزودن دکمه جدید
    if context.user_data.get("await_ck_add"):
        level = context.user_data["ck_add_level"]

        new_id = f"{level}_{len(kb[level])+1}"

        # ساخت سطح زیرمجموعه
        kb[new_id] = []

        kb[level].append({
            "id": new_id,
            "name": text
        })

        save_keyboard(kb)

        context.user_data["await_ck_add"] = False
        await update.message.reply_text(f"✔️ دکمه '{text}' اضافه شد!")
        return

    # تغییر نام دکمه
    if context.user_data.get("await_ck_rename"):
        btn_id = context.user_data["ck_rename_id"]

        for level in kb:
            for btn in kb[level]:
                if btn["id"] == btn_id:
                    btn["name"] = text

        save_keyboard(kb)
        context.user_data["await_ck_rename"] = False
        await update.message.reply_text("✔️ نام دکمه تغییر کرد!")
        return
