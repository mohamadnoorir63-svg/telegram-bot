import json, os
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

# مسیر ذخیره داده‌ها
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ORIGIN_FILE = os.path.join(BASE_DIR, "origins.json")
TITLE_FILE = os.path.join(BASE_DIR, "titles.json")

# ایجاد فایل‌ها در صورت نبود
for path in (ORIGIN_FILE, TITLE_FILE):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

# لود و ذخیره
def _load(path): 
    try: 
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}
def _save(path, data): 
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

# حافظه
origins = _load(ORIGIN_FILE)
titles = _load(TITLE_FILE)

# 🔐 دسترسی
SUDO_IDS = [8588347189]
async def _is_admin_or_sudo(context, chat_id, user_id):
    if user_id in SUDO_IDS:
        return True
    try:
        m = await context.bot.get_chat_member(chat_id, user_id)
        return m.status in ("administrator", "creator")
    except:
        return False

# 🧠 هندلر اصلی
async def handle_origin_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    text = (msg.text or "").strip().lower()

    # فقط در گروه
    if chat.type not in ("group", "supergroup"):
        return

    # ثبت اصل
    if text == "ثبت اصل" and msg.reply_to_message:
        if not await _is_admin_or_sudo(context, chat.id, user.id):
            return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
        target = msg.reply_to_message.from_user
        origins[str(target.id)] = msg.reply_to_message.text or ""
        _save(ORIGIN_FILE, origins)
        return await msg.reply_text(f"✅ اصل برای {target.first_name} ثبت شد.")

    # ثبت لقب
    if text == "ثبت لقب" and msg.reply_to_message:
        if not await _is_admin_or_sudo(context, chat.id, user.id):
            return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
        target = msg.reply_to_message.from_user
        titles[str(target.id)] = msg.reply_to_message.text or ""
        _save(TITLE_FILE, titles)
        return await msg.reply_text(f"🏷️ لقب برای {target.first_name} ثبت شد.")

    # نمایش اصل
    if text == "اصل من":
        if str(user.id) in origins:
            return await msg.reply_text(f"📜 اصل شما:\n<code>{origins[str(user.id)]}</code>", parse_mode="HTML")
        else:
            return await msg.reply_text("❌ اصل ثبت‌نشده‌ای برای شما وجود ندارد.")

    # نمایش لقب
    if text == "لقب من":
        if str(user.id) in titles:
            return await msg.reply_text(f"🏷️ لقب شما:\n<code>{titles[str(user.id)]}</code>", parse_mode="HTML")
        else:
            return await msg.reply_text("❌ لقبی برای شما ثبت نشده است.")

    # ریپلای → نمایش اصل/لقب کاربر
    if msg.reply_to_message and text in ("اصل", "لقب"):
        target = msg.reply_to_message.from_user
        if text == "اصل" and str(target.id) in origins:
            return await msg.reply_text(f"📜 اصل {target.first_name}:\n<code>{origins[str(target.id)]}</code>", parse_mode="HTML")
        if text == "لقب" and str(target.id) in titles:
            return await msg.reply_text(f"🏷️ لقب {target.first_name}:\n<code>{titles[str(target.id)]}</code>", parse_mode="HTML")

# ✨ رجیستر هندلر
def register_origin_title_handlers(application):
    """اتصال ماژول اصل و لقب به ربات"""
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_origin_title)
    )    
