from telebot import TeleBot, types
from datetime import datetime, timedelta

TOKEN = "اینجا_توکن_ربات_خودتو_بزار"
bot = TeleBot(TOKEN)

# دیتابیس ساده در حافظه (برای تست)
locks = {}
group_expire = {}

def is_admin(user_id):
    # اینجا می‌تونی آیدی خودتو بزاری
    return str(user_id) in ["123456789"]

@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "✅ ربات مدیریت گروه روشن است.\n/add برای افزودن به گروه استفاده کنید.")

@bot.message_handler(commands=['panel'])
def panel(msg):
    if not is_admin(msg.from_user.id):
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔒 قفل‌ها", callback_data="locks"))
    markup.add(types.InlineKeyboardButton("⏳ شارژ گروه", callback_data="charge"))
    bot.send_message(msg.chat.id, "پنل مدیریت:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    if call.data == "locks":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("قفل متن", callback_data="lock_text"))
        markup.add(types.InlineKeyboardButton("قفل عکس", callback_data="lock_photo"))
        markup.add(types.InlineKeyboardButton("قفل لینک", callback_data="lock_link"))
        bot.edit_message_text("🔒 قفل‌ها:", cid, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("lock_"):
        lock_type = call.data.split("_")[1]
        locks.setdefault(cid, {})[lock_type] = not locks[cid].get(lock_type, False)
        status = "فعال ✅" if locks[cid][lock_type] else "غیرفعال ❌"
        bot.answer_callback_query(call.id, f"قفل {lock_type} {status} شد.")

    elif call.data == "charge":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("7 روز", callback_data="ch_7"))
        markup.add(types.InlineKeyboardButton("30 روز", callback_data="ch_30"))
        bot.edit_message_text("⏳ مدت شارژ:", cid, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("ch_"):
        days = int(call.data.split("_")[1])
        group_expire[cid] = datetime.now() + timedelta(days=days)
        bot.answer_callback_query(call.id, f"گروه برای {days} روز شارژ شد ✅")

@bot.message_handler(content_types=['text', 'photo'])
def filter_msg(msg):
    cid = msg.chat.id
    if cid in group_expire and datetime.now() > group_expire[cid]:
        bot.send_message(cid, "⛔️ شارژ گروه تمام شده است. برای تمدید با مدیر تماس بگیرید.")
        return
    if cid in locks:
        if locks[cid].get("text") and msg.content_type == "text":
            bot.delete_message(cid, msg.message_id)
        if locks[cid].get("photo") and msg.content_type == "photo":
            bot
