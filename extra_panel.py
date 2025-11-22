# extra_panel.py
import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# ======================= ⚙️ تنظیمات اولیه =======================
ADMIN_ID = 8588347189  # <--- آیدی خودت

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
    admin_buttons = data.get("admin_buttons", [])
    if not admin_buttons:
        # اگر خالی بود دکمه‌های پیشفرض را قرار می‌دهیم
        admin_buttons = [
            {"text": "➕ افزودن دکمه", "action": "add"},
            {"text": "📝 ویرایش دکمه‌ها", "action": "edit"},
            {"text": "🗑 حذف دکمه", "action": "delete"},
        ]
        data["admin_buttons"] = admin_buttons
        save_panel_data(data)

    keyboard = [[InlineKeyboardButton(btn["text"], callback_data=f"admin_{btn['action']}")] for btn in admin_buttons]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ پنل مدیریت ربات:\nاز دکمه‌ها استفاده کنید:", reply_markup=markup)

# ======================= 🔹 هندلر دکمه‌ها =======================
async def extra_panel_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    panel_data = load_panel_data()

    # ---- دکمه‌های کاربران ----
    if data.startswith("user_"):
        index = int(data.replace("user_", ""))
        user_buttons = panel_data.get("user_buttons", [])
        if 0 <= index < len(user_buttons):
            await query.edit_message_text(f"✅ شما روی دکمه '{user_buttons[index]['text']}' کلیک کردید.")
        else:
            await query.edit_message_text("❗ دکمه نامعتبر است.")

    # ---- دکمه‌های ادمین ----
    elif data.startswith("admin_"):
        action = data.replace("admin_", "")
        if action == "add":
            context.user_data["awaiting_add"] = True
            await query.edit_message_text("➕ لطفاً متن دکمه جدید را ارسال کنید:")
        elif action == "edit":
            await query.edit_message_text("📝 برای ویرایش دکمه‌ها، دستور بعدی را بفرستید...")
        elif action == "delete":
            await query.edit_message_text("🗑 برای حذف دکمه‌ها، دستور بعدی را بفرستید...")
        else:
            await query.edit_message_text("❗ عملکرد نامشخص.")

# ======================= 🔹 دریافت پیام ادمین برای افزودن دکمه =======================
async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    data = load_panel_data()

    # ---- اضافه کردن دکمه ----
    if context.user_data.get("awaiting_add"):
        text = update.message.text.strip()
        if text:
            data["user_buttons"].append({"text": text})
            save_panel_data(data)
            await update.message.reply_text(f"✅ دکمه '{text}' اضافه شد.")
        context.user_data["awaiting_add"] = False
