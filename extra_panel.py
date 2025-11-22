import json, os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

DATA_FILE = "extra_panel_data.json"
ADMIN_IDS = [123456789]  # آیدی خودت و مدیران

# ------------------ بارگذاری و ذخیره داده‌ها ------------------
def load_panel_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # داده اولیه
    default_data = {
        "user_panel": [],
        "admin_panel": ["اضافه کردن دکمه", "ویرایش دکمه", "حذف دکمه"]
    }
    save_panel_data(default_data)
    return default_data

def save_panel_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ------------------ نمایش پنل ------------------
async def show_extra_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    user_id = update.effective_user.id
    data = load_panel_data()

    if user_id in ADMIN_IDS:
        # پنل مدیریت
        buttons = [InlineKeyboardButton(b, callback_data=f"admin_{i}") for i, b in enumerate(data["admin_panel"])]
        text = "👑 پنل مدیریت: یک گزینه انتخاب کنید"
    else:
        # پنل کاربران
        buttons = [InlineKeyboardButton(b["title"], callback_data=f"user_{i}") for i, b in enumerate(data["user_panel"])]
        text = "🌟 پنل شما: یک گزینه را انتخاب کنید"

    buttons.append(InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_main"))
    keyboard = [[b] for b in buttons]
    markup = InlineKeyboardMarkup(keyboard)

    if edit:
        await update.callback_query.edit_message_text(text, reply_markup=markup)
    else:
        await update.message.reply_text(text, reply_markup=markup)

# ------------------ هندلر دکمه‌ها ------------------
async def extra_panel_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = load_panel_data()
    d = query.data

    # ------------------ پنل مدیریت ------------------
    if d.startswith("admin_") and user_id in ADMIN_IDS:
        idx = int(d.replace("admin_", ""))
        action = data["admin_panel"][idx]

        if action == "اضافه کردن دکمه":
            context.user_data["action"] = "add_button"
            await query.edit_message_text("📌 نام دکمه جدید را وارد کنید:")
        elif action == "ویرایش دکمه":
            if not data["user_panel"]:
                await query.edit_message_text("⚠️ هیچ دکمه‌ای برای ویرایش وجود ندارد.")
                return
            buttons = [InlineKeyboardButton(b["title"], callback_data=f"editbtn_{i}") 
                       for i, b in enumerate(data["user_panel"])]
            markup = InlineKeyboardMarkup([[b] for b in buttons])
            await query.edit_message_text("✏️ دکمه‌ای برای ویرایش انتخاب کنید:", reply_markup=markup)
        elif action == "حذف دکمه":
            if not data["user_panel"]:
                await query.edit_message_text("⚠️ هیچ دکمه‌ای برای حذف وجود ندارد.")
                return
            buttons = [InlineKeyboardButton(b["title"], callback_data=f"delbtn_{i}") 
                       for i, b in enumerate(data["user_panel"])]
            markup = InlineKeyboardMarkup([[b] for b in buttons])
            await query.edit_message_text("❌ دکمه‌ای برای حذف انتخاب کنید:", reply_markup=markup)

    # ------------------ ویرایش و حذف دکمه‌ها ------------------
    elif d.startswith("editbtn_") and user_id in ADMIN_IDS:
        idx = int(d.replace("editbtn_", ""))
        context.user_data["action"] = "edit_button"
        context.user_data["edit_idx"] = idx
        await query.edit_message_text("✏️ متن جدید برای دکمه وارد کنید:")

    elif d.startswith("delbtn_") and user_id in ADMIN_IDS:
        idx = int(d.replace("delbtn_", ""))
        button_title = data["user_panel"][idx]["title"]
        data["user_panel"].pop(idx)
        save_panel_data(data)
        await query.edit_message_text(f"✅ دکمه '{button_title}' حذف شد.")
        # بازگرداندن پنل مدیریت
        await show_extra_panel(update, context, edit=True)

    # ------------------ پنل کاربران ------------------
    elif d.startswith("user_"):
        idx = int(d.replace("user_", ""))
        button_info = data["user_panel"][idx]
        text = button_info["text"]
        await query.edit_message_text(text)

    # ------------------ بازگشت ------------------
    elif d == "back_main":
        from main import show_main_panel
        await show_main_panel(update, context, edit=True)

# ------------------ هندلر پیام‌ها برای اضافه/ویرایش ------------------
async def handle_extra_panel_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_panel_data()
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if "action" not in context.user_data:
        return  # هیچ عملی در حال انجام نیست

    action = context.user_data.pop("action")

    if action == "add_button" and user_id in ADMIN_IDS:
        # ساخت دکمه جدید
        data["user_panel"].append({"title": text, "text": "📝 متن این دکمه بعدا ویرایش می‌شود."})
        save_panel_data(data)
        await update.message.reply_text(f"✅ دکمه '{text}' اضافه شد. حالا می‌توانید متن آن را ویرایش کنید.")
    elif action == "edit_button" and user_id in ADMIN_IDS:
        idx = context.user_data.pop("edit_idx")
        data["user_panel"][idx]["text"] = text
        save_panel_data(data)
        await update.message.reply_text(f"✅ متن دکمه '{data['user_panel'][idx]['title']}' بروزرسانی شد.")
