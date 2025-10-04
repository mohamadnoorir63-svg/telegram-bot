import telebot
from telebot import types
from datetime import datetime, timedelta
import re

# 🔑 توکن ربات
TOKEN = "7462131830:AAENzKipQzuxQ4UYkl9vcVgmmfDMKMUvZi8"
# 👑 آیدی سودو
SUDO_ID = 7089376754

bot = telebot.TeleBot(TOKEN)

# دیتابیس ساده
group_expiry = {}
welcome_settings = {}   # روشن/خاموش خوشامد
welcome_content = {}    # متن/عکس خوشامد
all_groups = set()

lock_links = {}
lock_stickers = {}
lock_group = {}

# ======================
# پنل سودو در پیوی
# ======================
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type == "private" and message.from_user.id == SUDO_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📊 آمار گروه‌ها", "📩 ارسال پیام")
        markup.add("⏳ شارژ گروه", "💬 تنظیم خوشامد")
        bot.send_message(message.chat.id, "👑 پنل مدیریت سودو", reply_markup=markup)
    else:
        bot.reply_to(message, "✅ ربات فعال است!")

@bot.message_handler(func=lambda m: m.chat.type == "private" and m.from_user.id == SUDO_ID)
def sudo_panel(message):
    text = message.text
    if text == "📊 آمار گروه‌ها":
        if not group_expiry:
            bot.send_message(message.chat.id, "❌ هیچ گروهی ثبت نشده")
        else:
            stats = "\n".join([f"{gid} : تا {exp.strftime('%Y-%m-%d')}" for gid, exp in group_expiry.items()])
            bot.send_message(message.chat.id, "📊 آمار گروه‌ها:\n" + stats)

    elif text == "📩 ارسال پیام":
        bot.send_message(message.chat.id, "✏️ پیام خود را بفرست تا به همه گروه‌ها ارسال شود.")
        bot.register_next_step_handler(message, broadcast)

    elif text == "⏳ شارژ گروه":
        bot.send_message(message.chat.id, "فرمت دستور:\n/charge group_id روز")

    elif text == "💬 تنظیم خوشامد":
        bot.send_message(message.chat.id, "فرمت دستور:\n/welcome group_id متن خوشامد")

def broadcast(message):
    for gid in all_groups:
        try:
            bot.send_message(gid, f"📢 پیام مدیر:\n{message.text}")
        except:
            pass
    bot.send_message(message.chat.id, "✅ پیام ارسال شد.")

# ======================
# شارژ گروه
# ======================
@bot.message_handler(commands=['charge'])
def charge_group(message):
    if message.from_user.id != SUDO_ID:
        return
    try:
        _, group_id, days = message.text.split()
        group_expiry[int(group_id)] = datetime.now() + timedelta(days=int(days))
        all_groups.add(int(group_id))
        bot.send_message(message.chat.id, f"✅ گروه {group_id} برای {days} روز شارژ شد.")
    except:
        bot.send_message(message.chat.id, "❌ فرمت درست:\n/charge group_id روز")

# ======================
# خوشامدگویی
# ======================
@bot.message_handler(content_types=['new_chat_members'])
def greet_new_member(message):
    cid = message.chat.id
    if cid in group_expiry and datetime.now() < group_expiry[cid]:
        if welcome_settings.get(cid, True):
            if cid in welcome_content:
                content = welcome_content[cid]
                if "photo" in content:
                    bot.send_photo(cid, content["photo"], caption=content.get("text", "👋 خوش آمدید!"))
                else:
                    bot.send_message(cid, content.get("text", "👋 خوش آمدید!"))
            else:
                bot.send_message(cid, "👋 خوش آمدید!")

@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"])
def welcome_commands(message):
    cid = message.chat.id
    text = message.text

    if text == "خوشامد روشن":
        welcome_settings[cid] = True
        bot.send_message(cid, "✅ خوشامدگویی فعال شد.")

    elif text == "خوشامد خاموش":
        welcome_settings[cid] = False
        bot.send_message(cid, "❌ خوشامدگویی خاموش شد.")

    elif text == "ویرایش خوشامد" and message.reply_to_message:
        if message.reply_to_message.photo:
            file_id = message.reply_to_message.photo[-1].file_id
            caption = message.reply_to_message.caption or ""
            welcome_content[cid] = {"photo": file_id, "text": caption}
            bot.send_message(cid, "✅ خوشامدگویی با عکس و متن ذخیره شد.")
        else:
            welcome_content[cid] = {"text": message.reply_to_message.text}
            bot.send_message(cid, "✅ خوشامدگویی متنی ذخیره شد.")

    elif text == "لینک":
        try:
            invite = bot.export_chat_invite_link(cid)
            bot.send_message(cid, f"🔗 لینک گروه:\n{invite}")
        except:
            bot.send_message(cid, "⚠️ ربات باید دسترسی ساخت لینک داشته باشد.")

# ======================
# دستورات گروه
# ======================
@bot.message_handler(func=lambda m: m.chat.type in ["group", "supergroup"])
def group_handler(message):
    cid = message.chat.id
    text = message.text
    all_groups.add(cid)

    if cid not in group_expiry or datetime.now() > group_expiry[cid]:
        bot.send_message(cid, "⛔️ شارژ گروه تمام شد. ربات لفت می‌دهد.")
        try:
            bot.leave_chat(cid)
        except:
            pass
        return

    # عمومی
    if text == "ساعت":
        bot.send_message(cid, datetime.now().strftime("⏰ %H:%M:%S"))

    elif text == "تاریخ":
        bot.send_message(cid, datetime.now().strftime("📅 %Y-%m-%d"))

    elif text == "آمار":
        members = bot.get_chat_members_count(cid)
        bot.send_message(cid, f"👥 تعداد اعضا: {members}")

    elif text == "ایدی":
        bot.send_message(cid, f"🆔 آیدی شما: {message.from_user.id}\n🆔 آیدی گروه: {cid}")

    elif text == "راهنما":
        bot.send_message(cid, """
📖 لیست دستورات:
ساعت | تاریخ | آمار | ایدی
قفل لینک / باز کردن لینک
قفل استیکر / باز کردن استیکر
قفل گروه / باز کردن گروه
سکوت (ریپلای) / حذف سکوت (ریپلای)
بن (ریپلای)
مدیر (ریپلای) / حذف مدیر (ریپلای)
پاکسازی (۵۰ پیام)
لفت بده (فقط سودو)
""")

    elif text == "لفت بده" and message.from_user.id == SUDO_ID:
        bot.send_message(cid, "👋 خداحافظ")
        bot.leave_chat(cid)

    # قفل‌ها
    elif text == "قفل لینک":
        lock_links[cid] = True
        bot.send_message(cid, "🔒 لینک‌ها قفل شدند.")
    elif text == "باز کردن لینک":
        lock_links[cid] = False
        bot.send_message(cid, "🔓 لینک‌ها آزاد شدند.")
    elif text == "قفل استیکر":
        lock_stickers[cid] = True
        bot.send_message(cid, "🔒 استیکرها قفل شدند.")
    elif text == "باز کردن استیکر":
        lock_stickers[cid] = False
        bot.send_message(cid, "🔓 استیکرها آزاد شدند.")
    elif text == "قفل گروه":
        bot.set_chat_permissions(cid, types.ChatPermissions(can_send_messages=False))
        lock_group[cid] = True
        bot.send_message(cid, "🔒 گروه قفل شد.")
    elif text == "باز کردن گروه":
        bot.set_chat_permissions(cid, types.ChatPermissions(can_send_messages=True))
        lock_group[cid] = False
        bot.send_message(cid, "🔓 گروه باز شد.")

    # پاکسازی
    elif text == "پاکسازی" and message.from_user.id == SUDO_ID:
        deleted = 0
        for i in range(1, 51):
            try:
                bot.delete_message(cid, message.message_id - i)
                deleted += 1
            except:
                pass
        bot.send_message(cid, f"🧹 {deleted} پیام پاک شد.")

# ======================
# اکشن‌ها (ریپلای روی پیام کاربر)
# ======================
@bot.message_handler(func=lambda m: m.reply_to_message and m.text in ["سکوت","حذف سکوت","بن","مدیر","حذف مدیر"])
def reply_actions(message):
    cid = message.chat.id
    user_id = message.reply_to_message.from_user.id
    text = message.text

    if cid not in group_expiry or datetime.now() > group_expiry[cid]:
        return

    if text == "سکوت":
        bot.restrict_chat_member(cid, user_id, until_date=0, permissions=types.ChatPermissions(can_send_messages=False))
        bot.send_message(cid, f"🔇 کاربر {user_id} در سکوت قرار گرفت.")
    elif text == "حذف سکوت":
        bot.restrict_chat_member(cid, user_id, permissions=types.ChatPermissions(can_send_messages=True))
        bot.send_message(cid, f"🔊 سکوت کاربر {user_id} برداشته شد.")
    elif text == "بن":
        bot.ban_chat_member(cid, user_id)
        bot.send_message(cid, f"⛔️ کاربر {user_id} بن شد.")
    elif text == "مدیر" and message.from_user.id == SUDO_ID:
        bot.promote_chat_member(cid, user_id, can_manage_chat=True, can_delete_messages=True,
                                can_restrict_members=True, can_promote_members=False, can_invite_users=True)
        bot.send_message(cid, f"👑 کاربر {user_id} مدیر شد.")
    elif text == "حذف مدیر" and message.from_user.id == SUDO_ID:
        bot.promote_chat_member(cid, user_id, can_manage_chat=False, can_delete_messages=False,
                                can_restrict_members=False, can_invite_users=False)
        bot.send_message(cid, f"❌ کاربر {user_id} از مدیریت حذف شد.")

# ======================
# فیلتر لینک/استیکر
# ======================
@bot.message_handler(func=lambda m: True, content_types=['text', 'sticker'])
def filters(message):
    cid = message.chat.id
    if cid in lock_links and lock_links[cid]:
        if message.text and re.search(r"(https?://|t\.me/)", message.text):
            try: bot.delete_message(cid, message.message_id)
            except: pass
    if cid in lock_stickers and lock_stickers[cid]:
        if message.content_type == 'sticker':
            try: bot.delete_message(cid, message.message_id)
            except: pass

print("🤖 Bot is running...")
bot.infinity_polling()
