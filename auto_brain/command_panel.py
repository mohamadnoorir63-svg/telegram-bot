# ==================== ⚙️ command_panel.py (ورژن لوکال بدون MongoDB) ====================
import json, os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes

DATA_FILE = "data/commands.json"
ADMIN_ID = 7089376754
os.makedirs("data", exist_ok=True)

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==================== 📋 نمایش پنل تنظیمات ====================

async def show_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجازه!")

    if not context.args:
        return await update.message.reply_text("❗ فرمت درست: /panel <نام دستور>")

    name = " ".join(context.args).strip().lower()
    data = load_data()
    cmd = data.get(name)

    if not cmd:
        return await update.message.reply_text("⚠️ این دستور هنوز وجود ندارد.")

    s = cmd.get("settings", {"access": ["everyone"], "mode": "all", "creator_only": False})
    await update.message.reply_text(
        f"در حال تنظیم دستور <b>{name}</b> ⚙️\n\n"
        "- انتخاب کنید چه کسانی بتوانند اجرا کنند.\n"
        "- مشخص کنید حالت اجرا تصادفی باشد یا همه.\n"
        "- در صورت فعال بودن 🔒 فقط‌سازنده، فقط سازنده می‌تواند از آن استفاده کند.\n\n"
        "✅ = فعال | ☑️ = غیرفعال",
        parse_mode="HTML",
        reply_markup=_panel_keyboard(name, s)
    )

# ==================== 🎛 ساخت دکمه‌ها ====================

def _panel_keyboard(name, s):
    def check(o): return "✅" if o in s.get("access", []) else "☑️"
    def mode(o): return "✅" if o == s.get("mode") else "☑️"
    c = "✅" if s.get("creator_only") else "☑️"
    kb = [
        [
            InlineKeyboardButton(f"{check('everyone')} همه", callback_data=f"toggle:{name}:everyone"),
            InlineKeyboardButton(f"{check('admins')} ادمین", callback_data=f"toggle:{name}:admins")
        ],
        [
            InlineKeyboardButton(f"{check('groups')} گروه", callback_data=f"toggle:{name}:groups"),
            InlineKeyboardButton(f"{check('private')} شخصی", callback_data=f"toggle:{name}:private")
        ],
        [
            InlineKeyboardButton(f"{mode('all')} ارسال برای همه", callback_data=f"mode:{name}:all"),
            InlineKeyboardButton(f"{mode('random')} تصادفی", callback_data=f"mode:{name}:random")
        ],
        [
            InlineKeyboardButton(f"{c} فقط‌سازنده", callback_data=f"creator:{name}")
        ],
        [
            InlineKeyboardButton("💾 ذخیره", callback_data=f"save:{name}"),
            InlineKeyboardButton("🗑 حذف", callback_data=f"del:{name}")
        ]
    ]
    return InlineKeyboardMarkup(kb)

# ==================== 🔄 مدیریت کلیک دکمه‌ها ====================

async def panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    if len(parts) < 2:
        return

    action, name = parts[0], parts[1]
    data = load_data()
    cmd = data.get(name)
    if not cmd:
        return await query.edit_message_text("⚠️ دستور وجود ندارد.")

    s = cmd.get("settings", {"access": ["everyone"], "mode": "all", "creator_only": False})

    if action == "toggle":
        t = parts[2]
        if t in s["access"]:
            s["access"].remove(t)
        else:
            s["access"].append(t)

    elif action == "mode":
        s["mode"] = parts[2]

    elif action == "creator":
        s["creator_only"] = not s.get("creator_only", False)

    elif action == "save":
        cmd["settings"] = s
        data[name] = cmd
        save_data(data)
        return await query.edit_message_text(f"✅ تنظیمات برای '{name}' ذخیره شد!")

    elif action == "del":
        del data[name]
        save_data(data)
        return await query.edit_message_text(f"🗑 دستور '{name}' حذف شد!")

    cmd["settings"] = s
    data[name] = cmd
    save_data(data)
    await query.edit_message_reply_markup(reply_markup=_panel_keyboard(name, s))
