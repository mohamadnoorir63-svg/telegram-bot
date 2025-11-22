# extra_panel.py
import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# ======================= ⚙️ تنظیمات =======================
ADMIN_ID = 8588347189  # <-- آیدی خودت
DATA_FILE = "extra_panel_data.json"

# ======================= 📝 بارگذاری و ذخیره دکمه‌ها =======================
def load_panel_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"user_buttons": [], "admin_buttons": []}
    return {"user_buttons": [], "admin_buttons": []}

def save_panel_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================= 🔹 پنل کاربران =======================
async def show_user_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_panel_data()
    user_buttons = data.get("user_buttons", [])

    if not user_buttons:
        await update.message.reply_text("🌟 پنل شما خالی است. هیچ دکمه‌ای موجود نیست.")
        return

    keyboard = [[InlineKeyboardButton(btn["text"], callback_data=f"user_{i}")] for i, btn in enumerate(user_buttons)]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🌟 پنل پیوی شما:\nاز دکمه‌ها استفاده کنید:", reply_markup=markup)

# ======================= 🔹 پنل مدیریت =======================
async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط ادمین مجاز است!")

    data = load_panel_data()
    admin_buttons = [
        {"text": "➕ افزودن دکمه", "action": "add"},
        {"text": "📝 ویرایش دکمه‌ها", "action": "edit"},
        {"text": "🗑 حذف دکمه", "action": "delete"},
    ]

    keyboard = [[InlineKeyboardButton(btn["text"], callback_data=f"admin_{btn['action']}")] for btn in admin_buttons]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ پنل مدیریت ربات:\nاز دکمه‌ها استفاده کنید:", reply_markup=markup)

# ======================= 🔹 هندلر دکمه‌ها =======================
async def extra_panel_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data_str = query.data
    panel_data = load_panel_data()

    # ---- دکمه‌های کاربران ----
    if data_str.startswith("user_"):
        index = int(data_str.replace("user_", ""))
        user_buttons = panel_data.get("user_buttons", [])
        if 0 <= index < len(user_buttons):
            await query.edit_message_text(f"✅ شما روی دکمه '{user_buttons[index]['text']}' کلیک کردید.")
        else:
            await query.edit_message_text("❗ دکمه نامعتبر است.")

    # ---- دکمه‌های ادمین ----
    elif data_str.startswith("admin_"):
        action = data_str.replace("admin_", "")
        if action == "add":
            context.user_data["awaiting_add"] = True
            await query.edit_message_text("➕ لطفاً متن دکمه جدید را ارسال کنید:")
        elif action == "edit":
            user_buttons = panel_data.get("user_buttons", [])
            if not user_buttons:
                await query.edit_message_text("❗ هیچ دکمه‌ای برای ویرایش وجود ندارد.")
                return
            # ساخت لیست انتخاب دکمه برای ویرایش
            keyboard = [[InlineKeyboardButton(btn["text"], callback_data=f"edit_{i}")] for i, btn in enumerate(user_buttons)]
            markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("📝 روی دکمه‌ای که می‌خوای ویرایش کنی بزن:", reply_markup=markup)
        elif action == "delete":
            user_buttons = panel_data.get("user_buttons", [])
            if not user_buttons:
                await query.edit_message_text("❗ هیچ دکمه‌ای برای حذف وجود ندارد.")
                return
            keyboard = [[InlineKeyboardButton(btn["text"], callback_data=f"del_{i}")] for i, btn in enumerate(user_buttons)]
            markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("🗑 روی دکمه‌ای که می‌خوای حذف کنی بزن:", reply_markup=markup)
        else:
            await query.edit_message_text("❗ عملکرد نامشخص.")

    # ---- ویرایش یک دکمه ----
    elif data_str.startswith("edit_") and update.effective_user.id == ADMIN_ID:
        index = int(data_str.replace("edit_", ""))
        context.user_data["awaiting_edit"] = index
        await query.edit_message_text(f"📝 لطفاً متن جدید برای دکمه {index+1} را ارسال کنید:")

    # ---- حذف یک دکمه ----
    elif data_str.startswith("del_") and update.effective_user.id == ADMIN_ID:
        index = int(data_str.replace("del_", ""))
        user_buttons = panel_data.get("user_buttons", [])
        if 0 <= index < len(user_buttons):
            removed = user_buttons.pop(index)
            panel_data["user_buttons"] = user_buttons
            save_panel_data(panel_data)
            await query.edit_message_text(f"🗑 دکمه '{removed['text']}' حذف شد.")
        else:
            await query.edit_message_text("❗ دکمه نامعتبر است.")

# ======================= 🔹 هندلر پیام ادمین =======================
async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    panel_data = load_panel_data()

    # ---- اضافه کردن دکمه ----
    if context.user_data.get("awaiting_add"):
        text = update.message.text.strip()
        if text:
            panel_data["user_buttons"].append({"text": text})
            save_panel_data(panel_data)
            await update.message.reply_text(f"✅ دکمه '{text}' اضافه شد.")
        context.user_data["awaiting_add"] = False

    # ---- ویرایش دکمه ----
    elif "awaiting_edit" in context.user_data:
        index = context.user_data.pop("awaiting_edit")
        text = update.message.text.strip()
        user_buttons = panel_data.get("user_buttons", [])
        if 0 <= index < len(user_buttons):
            old_text = user_buttons[index]["text"]
            user_buttons[index]["text"] = text
            panel_data["user_buttons"] = user_buttons
            save_panel_data(panel_data)
            await update.message.reply_text(f"✏️ دکمه '{old_text}' به '{text}' تغییر یافت.")
