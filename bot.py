# -*- coding: utf-8 -*-
import telebot, os, threading, time, random
from datetime import datetime
import pytz
from telebot import types

# ================== تنظیمات ==================
TOKEN   = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID","0"))
SUPPORT_ID = "NOORI_NOOR"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
sudo_ids = {SUDO_ID}
bot_admins = set()   # مدیران ربات (اضافه/حذف توسط سودو)

# ========= چک سودو / ادمین / مدیر ربات =========
def is_sudo(uid): return uid in sudo_ids
def is_bot_admin(uid): return uid in bot_admins or is_sudo(uid)
def is_admin(chat_id, user_id):
    if is_sudo(user_id) or is_bot_admin(user_id): return True
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator","creator")
    except: return False

def cmd_text(m): return (getattr(m,"text",None) or getattr(m,"caption",None) or "").strip()

# ========= حذف خودکار پیام =========
DELETE_DELAY = 7
def auto_del(chat_id,msg_id,delay=DELETE_DELAY):
    def _():
        time.sleep(delay)
        try: bot.delete_message(chat_id,msg_id)
        except: pass
    threading.Thread(target=_).start()

# ========= دستورات عمومی =========
@bot.message_handler(func=lambda m: cmd_text(m)=="ساعت")
def time_cmd(m):
    now_utc=datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_teh=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    msg=bot.reply_to(m,f"⏰ ساعت UTC: {now_utc}\n⏰ ساعت تهران: {now_teh}")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="ایدی")
def id_cmd(m):
    caption=f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>"
    try:
        photos=bot.get_user_profile_photos(m.from_user.id,limit=1)
        if photos.total_count>0:
            msg=bot.send_photo(m.chat.id,photos.photos[0][-1].file_id,caption=caption)
        else:
            msg=bot.reply_to(m,caption)
    except:
        msg=bot.reply_to(m,caption)
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="آمار")
def stats(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try: count=bot.get_chat_member_count(m.chat.id)
    except: count="نامشخص"
    msg=bot.reply_to(m,f"📊 اعضای گروه: {count}")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="لینک")
def group_link(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        link=bot.export_chat_invite_link(m.chat.id)
        msg=bot.reply_to(m,f"📎 لینک گروه:\n{link}")
    except:
        msg=bot.reply_to(m,"❗ نتوانستم لینک بگیرم.")
    auto_del(m.chat.id,msg.message_id)

# ========= وضعیت ربات =========
@bot.message_handler(func=lambda m: cmd_text(m)=="وضعیت ربات")
def status_cmd(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    now=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    msg=bot.reply_to(m,f"🤖 ربات فعال است.\n🕒 زمان: {now}")
    auto_del(m.chat.id,msg.message_id)

# ========= خوشامد =========
welcome_enabled, welcome_texts, welcome_photos = {}, {}, {}
DEFAULT_WELCOME = "• سلام {name} به گروه {title} خوش آمدید 🌻"

@bot.message_handler(content_types=['new_chat_members'])
def welcome(m):
    for u in m.new_chat_members:
        if not welcome_enabled.get(m.chat.id): continue
        name = u.first_name or ""
        date = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y/%m/%d")
        time_ = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%H:%M:%S")
        custom = welcome_texts.get(m.chat.id)
        txt = (custom or DEFAULT_WELCOME).format(name=name, title=m.chat.title)
        txt += f"\n\n📆 {date}\n⏰ {time_}"
        if m.chat.id in welcome_photos:
            bot.send_photo(m.chat.id,welcome_photos[m.chat.id],caption=txt)
        else:
            bot.send_message(m.chat.id,txt)

@bot.message_handler(func=lambda m: cmd_text(m)=="خوشامد روشن")
def w_on(m):
    if is_admin(m.chat.id,m.from_user.id):
        welcome_enabled[m.chat.id]=True
        msg=bot.reply_to(m,"✅ خوشامد روشن شد."); auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="خوشامد خاموش")
def w_off(m):
    if is_admin(m.chat.id,m.from_user.id):
        welcome_enabled[m.chat.id]=False
        msg=bot.reply_to(m,"❌ خوشامد خاموش شد."); auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m).startswith("خوشامد متن"))
def w_txt(m):
    if is_admin(m.chat.id,m.from_user.id):
        welcome_texts[m.chat.id]=cmd_text(m).replace("خوشامد متن","",1).strip()
        msg=bot.reply_to(m,"✍️ متن خوشامد ذخیره شد."); auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="ثبت عکس")
def w_photo(m):
    if is_admin(m.chat.id,m.from_user.id) and m.reply_to_message.photo:
        welcome_photos[m.chat.id]=m.reply_to_message.photo[-1].file_id
        msg=bot.reply_to(m,"🖼 عکس خوشامد ذخیره شد."); auto_del(m.chat.id,msg.message_id)

# ========= قفل‌ها =========
locks={k:{} for k in ["links","stickers","bots","tabchi","group","photo","video","gif","file","music","voice","forward"]}
LOCK_MAP={"لینک":"links","استیکر":"stickers","ربات":"bots","تبچی":"tabchi","گروه":"group",
"عکس":"photo","ویدیو":"video","گیف":"gif","فایل":"file","موزیک":"music","ویس":"voice","فوروارد":"forward"}

@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل ") or cmd_text(m).startswith("باز کردن "))
def toggle_lock(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    t=cmd_text(m); enable=t.startswith("قفل ")
    name=t.replace("قفل ","",1).replace("باز کردن ","",1).strip()
    key=LOCK_MAP.get(name)
    if not key: return
    locks[key][m.chat.id]=enable
    msg=bot.reply_to(m,f"{'🔒' if enable else '🔓'} {name} {'فعال شد' if enable else 'آزاد شد'}")
    auto_del(m.chat.id,msg.message_id)

# ========= بن / سکوت =========
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="بن")
def ban_user(m):
    if is_admin(m.chat.id,m.from_user.id):
        try: bot.ban_chat_member(m.chat.id,m.reply_to_message.from_user.id); txt="🚫 کاربر بن شد."
        except: txt="❗ خطا در بن."
        msg=bot.reply_to(m,txt); auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف بن")
def unban_user(m):
    if is_admin(m.chat.id,m.from_user.id):
        try: bot.unban_chat_member(m.chat.id,m.reply_to_message.from_user.id); txt="✅ بن حذف شد."
        except: txt="❗ خطا در حذف بن."
        msg=bot.reply_to(m,txt); auto_del(m.chat.id,msg.message_id)

# سکوت
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="سکوت")
def mute_user(m):
    if is_admin(m.chat.id,m.from_user.id):
        try: bot.restrict_chat_member(m.chat.id,m.reply_to_message.from_user.id,can_send_messages=False); txt="🔕 کاربر سکوت شد."
        except: txt="❗ خطا در سکوت."
        msg=bot.reply_to(m,txt); auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف سکوت")
def unmute_user(m):
    if is_admin(m.chat.id,m.from_user.id):
        try:
            bot.restrict_chat_member(m.chat.id,m.reply_to_message.from_user.id,
                can_send_messages=True,can_send_media_messages=True,
                can_send_other_messages=True,can_add_web_page_previews=True)
            txt="🔊 سکوت برداشته شد."
        except: txt="❗ خطا در حذف سکوت."
        msg=bot.reply_to(m,txt); auto_del(m.chat.id,msg.message_id)

# ========= اخطار =========
warnings={}; MAX_WARNINGS=3
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="اخطار")
def warn_user(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid=m.reply_to_message.from_user.id
    warnings.setdefault(m.chat.id,{})
    warnings[m.chat.id][uid]=warnings[m.chat.id].get(uid,0)+1
    c=warnings[m.chat.id][uid]
    if c>=MAX_WARNINGS:
        try: bot.ban_chat_member(m.chat.id,uid); txt="🚫 کاربر با ۳ اخطار بن شد."; warnings[m.chat.id][uid]=0
        except: txt="❗ خطا در بن."
    else: txt=f"⚠️ اخطار {c}/{MAX_WARNINGS}"
    msg=bot.reply_to(m,txt); auto_del(m.chat.id,msg.message_id)

# ========= اصل =========
origins={}
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m).startswith("ثبت اصل "))
def set_origin(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid=m.reply_to_message.from_user.id
    val=cmd_text(m).replace("ثبت اصل ","",1).strip()
    if not val: msg=bot.reply_to(m,"❗ متنی وارد کن.")
    else: origins.setdefault(m.chat.id,{})[uid]=val; msg=bot.reply_to(m,f"✅ اصل ثبت شد: {val}")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="اصل")
def get_origin(m):
    uid=m.reply_to_message.from_user.id
    val=origins.get(m.chat.id,{}).get(uid)
    msg=bot.reply_to(m,f"🧾 اصل: {val}" if val else "ℹ️ اصل ثبت نشده."); auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="اصل من")
def my_origin(m):
    val=origins.get(m.chat.id,{}).get(m.from_user.id)
    msg=bot.reply_to(m,f"🧾 اصل شما: {val}" if val else "ℹ️ اصل شما ثبت نشده."); auto_del(m.chat.id,msg.message_id)

# ========= جوک و فال =========
jokes=[]; fortunes=[]
@bot.message_handler(func=lambda m: cmd_text(m)=="جوک")
def send_joke(m):
    if not jokes: return bot.reply_to(m,"❗ هیچ جوکی ذخیره نشده.")
    j=random.choice(jokes); 
    (bot.send_message if j["type"]=="text" else bot.send_photo)(m.chat.id, j.get("content",j.get("file")), caption=j.get("caption",""))

@bot.message_handler(func=lambda m: cmd_text(m)=="فال")
def send_fal(m):
    if not fortunes: return bot.reply_to(m,"❗ هیچ فالی ذخیره نشده.")
    f=random.choice(fortunes)
    (bot.send_message if f["type"]=="text" else bot.send_photo)(m.chat.id, f.get("content",f.get("file")), caption=f.get("caption",""))

# ========= لیست مدیران =========
@bot.message_handler(func=lambda m: cmd_text(m)=="لیست مدیران گروه")
def admins_list(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        admins=bot.get_chat_administrators(m.chat.id)
        names=[f"▪️ {a.user.first_name} — <code>{a.user.id}</code>" for a in admins]
        txt="👑 لیست مدیران گروه:\n\n"+"\n".join(names)
    except: txt="❗ نتوانستم لیست مدیران را بگیرم."
    msg=bot.reply_to(m,txt); auto_del(m.chat.id,msg.message_id,delay=20)

@bot.message_handler(func=lambda m: cmd_text(m)=="لیست مدیران ربات")
def bot_admin_list(m):
    if not is_sudo(m.from_user.id): return
    if not bot_admins: txt="ℹ️ مدیری برای ربات ثبت نشده."
    else: txt="👑 مدیران ربات:\n"+"\n".join([str(i) for i in bot_admins])
    bot.reply_to(m,txt)

# ========= پاسخ ربات به سودو =========
SUDO_REPLIES=["در خدمتم سودو 😎","بله قربان 👑","ربات آماده‌ست 🔥","گوش به فرمانم 🤖"]
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ربات")
def sudo_reply(m):
    msg=bot.reply_to(m,random.choice(SUDO_REPLIES))
    auto_del(m.chat.id,msg.message_id)

# ========= راهنما =========
HELP_TEXT_ADMIN = """
📖 دستورات مدیران:

⏰ ساعت | 🆔 ایدی | 📊 آمار | 📎 لینک
🎉 خوشامد روشن / خاموش / متن / ثبت عکس
🔒 قفل‌ها | پنل قفل‌ها
🚫 بن / ✅ حذف بن
🔕 سکوت / 🔊 حذف سکوت
⚠️ اخطار / حذف اخطار
👑 مدیر / ❌ حذف مدیر
📌 پن / ❌ حذف پن
🏷 اصل / اصل من
😂 جوک / 🔮 فال
📋 لیست مدیران گروه
🧹 پاکسازی / حذف [عدد]
"""

HELP_TEXT_SUDO = """
👑 دستورات سودو:
➕ افزودن سودو [آیدی]
➖ حذف سودو [آیدی]
➕ افزودن مدیرربات [آیدی]
➖ حذف مدیرربات [آیدی]
📋 لیست مدیران ربات
📢 ارسال
🚪 لفت بده (ریپلای)
"""

@bot.message_handler(func=lambda m: cmd_text(m)=="راهنما")
def help_cmd(m):
    if is_sudo(m.from_user.id): txt=HELP_TEXT_ADMIN+HELP_TEXT_SUDO
    elif is_bot_admin(m.from_user.id): txt=HELP_TEXT_ADMIN
    elif is_admin(m.chat.id,m.from_user.id): txt=HELP_TEXT_ADMIN
    else: return
    kb=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("❌ بستن",callback_data="close_help"))
    msg=bot.reply_to(m,txt,reply_markup=kb); auto_del(m.chat.id,msg.message_id,delay=25)

@bot.callback_query_handler(func=lambda call: call.data=="close_help")
def close_help(call):
    try: bot.delete_message(call.message.chat.id,call.message.message_id)
    except: pass

# ========= استارت پیوی =========
@bot.message_handler(commands=['start'])
def start_cmd(m):
    if m.chat.type=="private":
        kb=types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/{bot.get_me().username}?startgroup=new"),
            types.InlineKeyboardButton("📞 پشتیبانی", url=f"https://t.me/{SUPPORT_ID}")
        )
        txt="👋 سلام!\nمن ربات مدیریت گروه هستم 🤖\n\nبرای استفاده من رو به گروهت اضافه کن."
        bot.send_message(m.chat.id,txt,reply_markup=kb)

# ========= اجرای ربات =========
print("🤖 Bot v2000 is running...")
bot.infinity_polling(skip_pending=True, timeout=30)
