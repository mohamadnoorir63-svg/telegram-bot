import os
import json
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

# ================= ⚙️ تنظیمات اولیه =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "origin_title.json")

SUDO_IDS = [8588347189]  # آیدی سودوها (خودت + ادمین‌های ثابت)

# فایل ذخیره‌سازی
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

def _load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def _save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

USER_DATA = _load_data()

# ================= 🔐 بررسی ادمین / سودو =================
async def _has_access(context, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False

# ================= 🪪 مدیریت اصل و لقب =================
async def handle_origin_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not msg or chat.type not in ("group", "supergroup"):
        return

    text = (msg.text or "").strip()

    # --- ثبت اصل ---
    if msg.reply_to_message and text == "ثبت اصل":
        if not await _has_access(context, chat.id, user.id):
            return await msg.reply_text("🚫 فقط مدیران یا سودوها مجاز به ثبت اصل هستند.")
        target = msg.reply_to_message.from_user
        USER_DATA[str(target.id)] = USER_DATA.get(str(target.id), {})
        USER_DATA[str(target.id)]["origin"] = msg.reply_to_message.text or "—"
        _save_data(USER_DATA)
        return await msg.reply_text(f"✅ اصل {target.first_name} با موفقیت ثبت شد.")

    # --- ثبت لقب ---
    if msg.reply_to_message and text == "ثبت لقب":
        if not await _has_access(context, chat.id, user.id):
            return await msg.reply_text("🚫 فقط مدیران یا سودوها مجاز به ثبت لقب هستند.")
        target = msg.reply_to_message.from_user
        USER_DATA[str(target.id)] = USER_DATA.get(str(target.id), {})
        USER_DATA[str(target.id)]["title"] = msg.reply_to_message.text or "—"
        _save_data(USER_DATA)
        return await msg.reply_text(f"✅ لقب {target.first_name} با موفقیت ثبت شد.")

    # --- نمایش اصل ---
    if msg.reply_to_message and text == "اصل":
        target = msg.reply_to_message.from_user
        info = USER_DATA.get(str(target.id), {}).get("origin")
        if info:
            return await msg.reply_text(f"📜 اصل {target.first_name}:\n<code>{info}</code>", parse_mode="HTML")
        else:
            return  # هیچی نگه

    # --- نمایش لقب ---
    if msg.reply_to_message and text == "لقب":
        target = msg.reply_to_message.from_user
        info = USER_DATA.get(str(target.id), {}).get("title")
        if info:
            return await msg.reply_text(f"🏷️ لقب {target.first_name}:\n<code>{info}</code>", parse_mode="HTML")
        else:
            return  # هیچی نگه

    # --- نمایش اصل خود ---
    if text == "اصل من":
        info = USER_DATA.get(str(user.id), {}).get("origin")
        if info:
            return await msg.reply_text(f"📜 اصل شما:\n<code>{info}</code>", parse_mode="HTML")
        else:
            return await msg.reply_text("😅 هنوز اصل شما ثبت نشده است.")

    # --- نمایش لقب خود ---
    if text == "لقب من":
        info = USER_DATA.get(str(user.id), {}).get("title")
        if info:
            return await msg.reply_text(f"🏷️ لقب شما:\n<code>{info}</code>", parse_mode="HTML")
        else:
            return await msg.reply_text("😅 هنوز لقب شما ثبت نشده است.")

# ================= 🔧 ثبت هندلر =================
def register_origin_title_handlers(application):
    """افزودن هندلر اصل و لقب به برنامه اصلی"""
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_origin_title)
    )
