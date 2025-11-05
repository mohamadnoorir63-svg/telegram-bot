import json, os
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "titles.json")

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

def _load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------------

async def handle_origin_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت اصل و لقب"""
    msg = update.message
    if not msg or not msg.text:
        return
    chat_id = str(msg.chat_id)
    user = msg.from_user
    text = msg.text.strip().lower()
    data = _load_data()

    if chat_id not in data:
        data[chat_id] = {}

    # ثبت اصل
    if msg.reply_to_message and text == "ثبت اصل":
        origin_user = msg.reply_to_message.from_user
        data[chat_id][str(origin_user.id)] = {"origin": msg.reply_to_message.text, "title": None}
        _save_data(data)
        return await msg.reply_text(f"✅ اصل {origin_user.first_name} ثبت شد.")

    # ثبت لقب
    if msg.reply_to_message and text == "ثبت لقب":
        origin_user = msg.reply_to_message.from_user
        data[chat_id].setdefault(str(origin_user.id), {})["title"] = msg.reply_to_message.text
        _save_data(data)
        return await msg.reply_text(f"✅ لقب {origin_user.first_name} ثبت شد.")

    # نمایش اصل من
    if text == "اصل من":
        udata = data.get(chat_id, {}).get(str(user.id))
        if udata and udata.get("origin"):
            return await msg.reply_text(f"🧾 اصل شما:\n{udata['origin']}")
        else:
            return await msg.reply_text("❌ اصل شما ثبت نشده است.")

    # نمایش لقب من
    if text == "لقب من":
        udata = data.get(chat_id, {}).get(str(user.id))
        if udata and udata.get("title"):
            return await msg.reply_text(f"🏷️ لقب شما:\n{udata['title']}")
        else:
            return await msg.reply_text("❌ لقبی برای شما ثبت نشده است.")

    # وقتی روی پیام کسی ریپلای بزنی و بنویسی "اصل" یا "لقب"
    if msg.reply_to_message:
        target = msg.reply_to_message.from_user
        tdata = data.get(chat_id, {}).get(str(target.id))
        if not tdata:
            return
        if text == "اصل" and tdata.get("origin"):
            return await msg.reply_text(f"🧾 اصل {target.first_name}:\n{tdata['origin']}")
        if text == "لقب" and tdata.get("title"):
            return await msg.reply_text(f"🏷️ لقب {target.first_name}:\n{tdata['title']}")

# ---------------------------------------------------------------------

def register_origin_title_handlers(application):
    """ثبت هندلرها در اپ اصلی"""
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_origin_title))
