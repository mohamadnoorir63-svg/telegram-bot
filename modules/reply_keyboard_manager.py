# modules/reply_keyboard_manager.py

import json
import os
from typing import Dict, Any

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

# -------------------- تنظیم مسیر فایل --------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

FILE = os.path.join(DATA_DIR, "reply_keyboard.json")

# -------------------- حالت مدیریت ------------------------
# کلید: user_id  / مقدار: اسم منوی فعلی
ADMIN_MODE: Dict[int, str] = {}


# -------------------- بارگذاری / ذخیره --------------------
def save_data(data: Dict[str, Any]):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_data() -> Dict[str, Any]:
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
        data = json.load(f)

    # 🔁 مهاجرت از نسخه قدیمی (فقط keyboard) به ساختار جدید
    if "menus" not in data:
        keyboard = data.get("keyboard", [
            ["🙂 یه جوک بگو", "🔮 فال بگیر"],
            ["❓ راهنما"]
        ])
        data = {
            "menus": {"main": keyboard},
            "links": {}
        }
        save_data(data)

    # اطمینان از وجود کلیدها
    data.setdefault("menus", {})
    data.setdefault("links", {})
    if "main" not in data["menus"]:
        data["menus"]["main"] = [
            ["🙂 یه جوک بگو", "🔮 فال بگیر"],
            ["❓ راهنما"]
        ]
        save_data(data)

    return data


# -------------------- نمایش منوی فعلی ---------------------
async def show_menu(update: Update,
                    context: ContextTypes.DEFAULT_TYPE,
                    menu: str = "main"):
    data = load_data()
    kb = data["menus"].get(menu, [])
    if not kb:
        kb = [["❌ منو خالی است"]]

    markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
    context.user_data["rk_current_menu"] = menu

    if update.message:
        await update.message.reply_text("👇 منوی فعلی:", reply_markup=markup)
    else:
        await update.callback_query.message.reply_text(
            "👇 منوی فعلی:", reply_markup=markup
        )


# -------------------- پنل مدیریت --------------------------
ADMIN_KEYBOARD = [
    ["➕ افزودن دکمه", "❌ حذف دکمه"],
    ["✏️ تغییر نام دکمه"],
    ["📂 ساخت زیرمنو"],
    ["🔙 بازگشت به منوی اصلی"]
]


async def open_admin_panel(update: Update,
                           context: ContextTypes.DEFAULT_TYPE):
    """فقط از /admin صدا زده می‌شود (چک سودو در bot.py)."""
    user_id = update.effective_user.id
    # شروع مدیریت از منوی اصلی
    ADMIN_MODE[user_id] = context.user_data.get("rk_current_menu", "main")

    # پاک کردن وضعیت‌های قبلی
    for key in ["rk_add_menu", "rk_remove_menu", "rk_rename_step",
                "rk_old_name", "rk_make_submenu"]:
        context.user_data.pop(key, None)

    markup = ReplyKeyboardMarkup(ADMIN_KEYBOARD, resize_keyboard=True)
    await update.message.reply_text("⚙️ پنل مدیریت:", reply_markup=markup)


# -------------------- هندلر اصلی پنل مدیریت ----------------
async def admin_handler(update: Update,
                        context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_MODE:
        return  # خارج از مود مدیریت؛ کاری نکن

    text = (update.message.text or "").strip()

    if text == "➕ افزودن دکمه":
        await update.message.reply_text("✏️ متن دکمه جدید را بفرست:")
        # منویی که الان داخلش هستیم
        context.user_data["rk_add_menu"] = ADMIN_MODE[user_id]

    elif text == "❌ حذف دکمه":
        data = load_data()
        menu = ADMIN_MODE[user_id]
        rows = data["menus"].get(menu, [])
        msg = "📌 دکمه‌های این منو:\n"
        for row in rows:
            for b in row:
                msg += f"• {b}\n"
        await update.message.reply_text(
            msg + "\n✏️ نام دکمه‌ای که می‌خوای حذف کنی را بفرست:"
        )
        context.user_data["rk_remove_menu"] = menu

    elif text == "✏️ تغییر نام دکمه":
        await update.message.reply_text("✏️ نام فعلی دکمه را بفرست:")
        context.user_data["rk_rename_step"] = "old"

    elif text == "📂 ساخت زیرمنو":
        await update.message.reply_text(
            "📂 نام دکمه‌ای که تبدیل به زیرمنو شود را بفرست:"
        )
        context.user_data["rk_make_submenu"] = True

    elif text == "🔙 بازگشت به منوی اصلی":
        # خروج از مود مدیریت
        ADMIN_MODE.pop(user_id, None)
        await show_menu(update, context, "main")


# -------------------- افزودن دکمه -------------------------
async def handle_add_button(update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_MODE:
        return

    menu = context.user_data.get("rk_add_menu")
    if not menu:
        return  # الان در حالت افزودن نیستیم

    btn_text = (update.message.text or "").strip()
    if not btn_text:
        return

    data = load_data()
    data["menus"].setdefault(menu, [])
    data["menus"][menu].append([btn_text])
    save_data(data)

    context.user_data["rk_add_menu"] = None
    await update.message.reply_text("✅ دکمه اضافه شد.")
    await show_menu(update, context, menu)


# -------------------- حذف دکمه -----------------------------
async def handle_remove_button(update: Update,
                               context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_MODE:
        return

    menu = context.user_data.get("rk_remove_menu")
    if not menu:
        return

    btn = (update.message.text or "").strip()
    data = load_data()

    rows = data["menus"].get(menu, [])
    new_rows = []
    for row in rows:
        new_row = [b for b in row if b != btn]
        if new_row:
            new_rows.append(new_row)

    data["menus"][menu] = new_rows
    save_data(data)

    context.user_data["rk_remove_menu"] = None
    await update.message.reply_text("🗑 دکمه حذف شد.")
    await show_menu(update, context, menu)


# -------------------- تغییر نام دکمه -----------------------
async def handle_rename(update: Update,
                        context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_MODE:
        return

    step = context.user_data.get("rk_rename_step")
    if not step:
        return

    menu = ADMIN_MODE[user_id]

    if step == "old":
        context.user_data["rk_old_name"] = (update.message.text or "").strip()
        context.user_data["rk_rename_step"] = "new"
        await update.message.reply_text("✏️ نام جدید را بفرست:")
        return

    if step == "new":
        old = context.user_data.get("rk_old_name")
        new = (update.message.text or "").strip()
        if not old or not new:
            context.user_data["rk_rename_step"] = None
            return

        data = load_data()
        rows = data["menus"].get(menu, [])
        for r_idx, row in enumerate(rows):
            for i, b in enumerate(row):
                if b == old:
                    rows[r_idx][i] = new

        data["menus"][menu] = rows
        save_data(data)

        context.user_data["rk_rename_step"] = None
        context.user_data["rk_old_name"] = None

        await update.message.reply_text("✨ نام دکمه تغییر کرد.")
        await show_menu(update, context, menu)


# -------------------- ساخت زیرمنو --------------------------
async def handle_create_submenu(update: Update,
                                context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_MODE:
        return

    if not context.user_data.get("rk_make_submenu"):
        return

    btn = (update.message.text or "").strip()
    menu = ADMIN_MODE[user_id]

    data = load_data()

    submenu_id = f"{menu}:{btn}"
    # ایجاد زیرمنو با یک دکمه برگشت
    data["menus"][submenu_id] = [["🔙 بازگشت"]]
    data["links"][submenu_id] = menu
    save_data(data)

    context.user_data["rk_make_submenu"] = None
    ADMIN_MODE[user_id] = submenu_id

    await update.message.reply_text("📂 زیرمنو ساخته شد.")
    await show_menu(update, context, submenu_id)


# -------------------- ناوبری بین منوها ---------------------
async def handle_navigation(update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
    """برای زمانی که دکمه‌های خود منو را می‌زنیم (زیرمنو / بازگشت)."""
    text = (update.message.text or "").strip()
    data = load_data()

    # منوی فعلی را از user_data می‌گیریم
    menu = context.user_data.get("rk_current_menu", "main")

    # دکمه برگشت در زیرمنوها
    if text == "🔙 بازگشت":
        parent = data["links"].get(menu, "main")
        context.user_data["rk_current_menu"] = parent
        await show_menu(update, context, parent)
        # اگر در مود مدیریت هستیم، منوی مدیریت را هم آپدیت کنیم
        user_id = update.effective_user.id
        if user_id in ADMIN_MODE:
            ADMIN_MODE[user_id] = parent
        return

    # اگر دکمه‌ای اسم زیرمنو بود → برو داخلش
    submenu_id = f"{menu}:{text}"
    if submenu_id in data["menus"]:
        context.user_data["rk_current_menu"] = submenu_id
        user_id = update.effective_user.id
        if user_id in ADMIN_MODE:
            ADMIN_MODE[user_id] = submenu_id
        await show_menu(update, context, submenu_id)
