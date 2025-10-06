# -*- coding: utf-8 -*-
import telebot, os, threading, time, random
from datetime import datetime
import pytz
from telebot import types

# ================== تنظیمات ==================
TOKEN   = os.environ.get("BOT_TOKEN")        # توکن ربات
SUDO_ID = int(os.environ.get("SUDO_ID","0")) # آیدی سودو اصلی
SUPPORT_ID = "NOORI_NOOR"                    # آیدی پشتیبانی

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

sudo_ids = {SUDO_ID}    # لیست سودوها
bot_admins = set()      # لیست مدیران ربات

# ========= چک سودو / مدیر ربات / مدیر گروه =========
def is_sudo(uid): return uid in sudo_ids
def is_bot_admin(uid): return uid in bot_admins or is_sudo(uid)
def is_admin(chat_id, user_id):
    if is_bot_admin(user_id): return True
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
        msg=bot.reply_to(m,"❗ نتوانستم لینک بگیرم. (بات باید ادمین با مجوز دعوت باشد)")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="وضعیت ربات")
def status_cmd(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    now=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    msg=bot.reply_to(m,f"🤖 ربات فعال است.\n🕒 زمان: {now}")
    auto_del(m.chat.id,msg.message_id)

# ========= جواب به سودو وقتی بگه «ربات» =========
SUDO_RESPONSES = [
    "جونم قربان 😎",
    "در خدمتم ✌️",
    "ربات آماده‌ست قربان 🚀",
    "چه خبر رئیس؟ 🤖"
]
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ربات")
def sudo_reply(m):
    msg=bot.reply_to(m,random.choice(SUDO_RESPONSES))
    auto_del(m.chat.id,msg.message_id)

# ========= خوشامد =========
welcome_enabled, welcome_texts, welcome_photos = {}, {}, {}
DEFAULT_WELCOME = "• سلام {name} به گروه {title} خوش آمدید 🌻\n📆 {date}\n⏰ {time}"

@bot.message_handler(content_types=['new_chat_members'])
def welcome(m):
    for u in m.new_chat_members:
        if not welcome_enabled.get(m.chat.id): continue
        name = u.first_name or ""
        date = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y/%m/%d")
        time_ = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%H:%M:%S")
        template = welcome_texts.get(m.chat.id, DEFAULT_WELCOME)
        txt = template.format(name=name, title=m.chat.title, date=date, time=time_)
        if m.chat.id in welcome_photos:
            bot.send_photo(m.chat.id, welcome_photos[m.chat.id], caption=txt)
        else:
            bot.send_message(m.chat.id, txt)

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

@bot.message_handler(func=lambda m: cmd_text(m).startswith("خوشامد متن "))
def w_txt(m):
    if is_admin(m.chat.id,m.from_user.id):
        welcome_texts[m.chat.id]=cmd_text(m).replace("خوشامد متن ","",1).strip()
        msg=bot.reply_to(m,"✍️ متن خوشامد ذخیره شد."); auto_del(m.chat.id,msg.message_id)

# ========= سیستم اصل =========
origins={}
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m).startswith("ثبت اصل "))
def set_origin(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid=m.reply_to_message.from_user.id
    val=cmd_text(m).replace("ثبت اصل ","",1).strip()
    if not val: msg=bot.reply_to(m,"❗ متنی وارد کن.")
    else:
        origins.setdefault(m.chat.id,{})[uid]=val
        msg=bot.reply_to(m,f"✅ اصل برای {m.reply_to_message.from_user.first_name} ثبت شد: {val}")
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
    joke=random.choice(jokes)
    if joke["type"]=="text": bot.send_message(m.chat.id,joke["content"])
    else: bot.send_photo(m.chat.id,joke["file"],caption=joke["caption"])

@bot.message_handler(func=lambda m: cmd_text(m)=="فال")
def send_fal(m):
    if not fortunes: return bot.reply_to(m,"❗ هیچ فالی ذخیره نشده.")
    fal=random.choice(fortunes)
    if fal["type"]=="text": bot.send_message(m.chat.id,fal["content"])
    else: bot.send_photo(m.chat.id,fal["file"],caption=fal["caption"])# ========= قفل‌ها و پنل =========
locks={k:{} for k in ["links","stickers","bots","tabchi","group","photo","video","gif","file","music","voice","forward"]}
LOCK_MAP={"لینک":"links","استیکر":"stickers","ربات":"bots","تبچی":"tabchi","گروه":"group",
          "عکس":"photo","ویدیو":"video","گیف":"gif","فایل":"file","موزیک":"music","ویس":"voice","فوروارد":"forward"}

@bot.message_handler(func=lambda m: cmd_text(m)=="پنل")
def locks_panel(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    kb=types.InlineKeyboardMarkup(row_width=2)
    btns=[]
    for name,key in LOCK_MAP.items():
        st="🔒" if locks[key].get(m.chat.id) else "🔓"
        btns.append(types.InlineKeyboardButton(f"{st} {name}",callback_data=f"toggle:{key}:{m.chat.id}"))
    kb.add(*btns)
    kb.add(types.InlineKeyboardButton("❌ بستن",callback_data=f"close:{m.chat.id}"))
    bot.reply_to(m,"🛠 پنل مدیریت قفل‌ها:",reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle:"))
def cb_toggle(call):
    _,key,chat_id=call.data.split(":")
    chat_id=int(chat_id)
    if not is_admin(chat_id,call.from_user.id):
        return bot.answer_callback_query(call.id,"❌ فقط مدیران",show_alert=True)
    cur=locks[key].get(chat_id,False)
    locks[key][chat_id]=not cur
    bot.answer_callback_query(call.id,("✅ فعال شد" if locks[key][chat_id] else "❌ غیرفعال شد"))

    kb=types.InlineKeyboardMarkup(row_width=2)
    btns=[]
    for name,k in LOCK_MAP.items():
        st="🔒" if locks[k].get(chat_id) else "🔓"
        btns.append(types.InlineKeyboardButton(f"{st} {name}",callback_data=f"toggle:{k}:{chat_id}"))
    kb.add(*btns)
    kb.add(types.InlineKeyboardButton("❌ بستن",callback_data=f"close:{chat_id}"))
    bot.edit_message_reply_markup(chat_id,call.message.message_id,reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("close:"))
def cb_close(call):
    try: bot.delete_message(call.message.chat.id,call.message.message_id)
    except: pass

# ========= بن / سکوت / اخطار =========
warnings={}; MAX_WARNINGS=3

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="بن")
def ban_user(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        bot.ban_chat_member(m.chat.id,m.reply_to_message.from_user.id)
        msg=bot.reply_to(m,"🚫 کاربر بن شد.")
    except: msg=bot.reply_to(m,"❗ خطا در بن.")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف بن")
def unban_user(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        bot.unban_chat_member(m.chat.id,m.reply_to_message.from_user.id)
        msg=bot.reply_to(m,"✅ بن حذف شد.")
    except: msg=bot.reply_to(m,"❗ خطا در حذف بن.")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="سکوت")
def mute_user(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        bot.restrict_chat_member(m.chat.id,m.reply_to_message.from_user.id,can_send_messages=False)
        msg=bot.reply_to(m,"🔕 کاربر در حالت سکوت قرار گرفت.")
    except: msg=bot.reply_to(m,"❗ خطا در سکوت.")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف سکوت")
def unmute_user(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        bot.restrict_chat_member(
            m.chat.id,m.reply_to_message.from_user.id,
            can_send_messages=True,can_send_media_messages=True,
            can_send_other_messages=True,can_add_web_page_previews=True
        )
        msg=bot.reply_to(m,"🔊 سکوت برداشته شد.")
    except: msg=bot.reply_to(m,"❗ خطا در حذف سکوت.")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="اخطار")
def warn_user(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid=m.reply_to_message.from_user.id
    warnings.setdefault(m.chat.id,{})
    warnings[m.chat.id][uid]=warnings[m.chat.id].get(uid,0)+1
    c=warnings[m.chat.id][uid]
    if c>=MAX_WARNINGS:
        try:
            bot.ban_chat_member(m.chat.id,uid)
            msg=bot.reply_to(m,"🚫 کاربر با ۳ اخطار بن شد.")
            warnings[m.chat.id][uid]=0
        except: msg=bot.reply_to(m,"❗ خطا در بن.")
    else: msg=bot.reply_to(m,f"⚠️ اخطار {c}/{MAX_WARNINGS}")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف اخطار")
def reset_warn(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid=m.reply_to_message.from_user.id
    warnings.get(m.chat.id,{}).pop(uid,None)
    msg=bot.reply_to(m,"✅ اخطارها حذف شد.")
    auto_del(m.chat.id,msg.message_id)

# ========= مدیر / حذف مدیر =========
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="مدیر")
def promote(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        bot.promote_chat_member(
            m.chat.id,m.reply_to_message.from_user.id,
            can_manage_chat=True,can_delete_messages=True,
            can_restrict_members=True,can_pin_messages=True,
            can_invite_users=True,can_manage_video_chats=True
        )
        msg=bot.reply_to(m,"👑 کاربر مدیر شد.")
    except: msg=bot.reply_to(m,"❗ خطا در ارتقا.")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف مدیر")
def demote(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        bot.promote_chat_member(
            m.chat.id,m.reply_to_message.from_user.id,
            can_manage_chat=False,can_delete_messages=False,
            can_restrict_members=False,can_pin_messages=False,
            can_invite_users=False,can_manage_video_chats=False
        )
        msg=bot.reply_to(m,"❌ مدیر حذف شد.")
    except: msg=bot.reply_to(m,"❗ خطا در حذف مدیر.")
    auto_del(m.chat.id,msg.message_id)

# ========= پن / حذف پن =========
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="پن")
def pin_msg(m):
    if is_admin(m.chat.id,m.from_user.id):
        try:
            bot.pin_chat_message(m.chat.id,m.reply_to_message.message_id,disable_notification=True)
            msg=bot.reply_to(m,"📌 پیام سنجاق شد.")
        except: msg=bot.reply_to(m,"❗ خطا در سنجاق.")
        auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="حذف پن")
def unpin_msg(m):
    if is_admin(m.chat.id,m.from_user.id):
        try: bot.unpin_chat_message(m.chat.id); msg=bot.reply_to(m,"❌ سنجاق برداشته شد.")
        except: msg=bot.reply_to(m,"❗ سنجاقی نبود.")
        auto_del(m.chat.id,msg.message_id)

# ========= پاکسازی =========
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m).startswith("حذف "))
def del_n(m):
    try:
        n=int(cmd_text(m).split()[1])
        for i in range(n):
            bot.delete_message(m.chat.id,m.message_id-i)
    except: pass

# ========= لیست مدیران =========
@bot.message_handler(func=lambda m: cmd_text(m)=="لیست مدیران گروه")
def admins_list(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        admins=bot.get_chat_administrators(m.chat.id)
        names=[f"▪️ {a.user.first_name} — <code>{a.user.id}</code>" for a in admins]
        txt="👑 لیست مدیران گروه:\n\n"+"\n".join(names)
    except: txt="❗ نتوانستم لیست مدیران را بگیرم."
    bot.reply_to(m,txt)

@bot.message_handler(func=lambda m: cmd_text(m)=="لیست مدیران ربات")
def bot_admins_list(m):
    if not is_sudo(m.from_user.id): return
    txt="👑 مدیران ربات:\n"+"\n".join([str(x) for x in bot_admins])
    bot.reply_to(m,txt)

@bot.message_handler(func=lambda m: cmd_text(m)=="لیست سودو")
def sudo_list(m):
    if not is_sudo(m.from_user.id): return
    txt="⚡ سودوها:\n"+"\n".join([str(x) for x in sudo_ids])
    bot.reply_to(m,txt)

# ========= راهنما =========
HELP_TEXT_ADMIN = """
📖 دستورات مدیران:

⏰ ساعت | 🆔 ایدی | 📊 آمار | 📎 لینک
🎉 خوشامد روشن/خاموش | ✍️ خوشامد متن | 🖼 ثبت عکس
🔒 قفل/بازکردن (لینک، استیکر، ربات، تبچی، عکس، ویدیو، ...)
🚫 بن / ✅ حذف بن | 🔕 سکوت / 🔊 حذف سکوت
⚠️ اخطار / حذف اخطار
👑 مدیر / ❌ حذف مدیر
📌 پن / ❌ حذف پن
🏷 اصل / اصل من / ثبت اصل
😂 جوک | 🔮 فال
🧹 پاکسازی / حذف [عدد]
📋 لیست مدیران گروه / لیست مدیران ربات
"""
@bot.message_handler(func=lambda m: cmd_text(m)=="راهنما")
def help_cmd(m):
    if m.chat.type!="private" and not is_admin(m.chat.id,m.from_user.id): return
    bot.reply_to(m,HELP_TEXT_ADMIN)

# ========= استارت پیوی =========
@bot.message_handler(commands=['start'])
def start_cmd(m):
    if m.chat.type!="private": return
    kb=types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("➕ افزودن ربات به گروه",url=f"https://t.me/{bot.get_me().username}?startgroup=new"),
        types.InlineKeyboardButton("📞 پشتیبانی",url=f"https://t.me/{SUPPORT_ID}")
    )
    txt=("👋 سلام!\n\nمن ربات مدیریت گروه هستم 🤖\n\n"
         "📌 امکانات:\n"
         "• قفل‌ها\n• خوشامد\n• اخطار/بن/سکوت\n• اصل\n• جوک و فال\n• ابزار مدیریتی\n\n➕ منو به گروهت اضافه کن.")
    bot.send_message(m.chat.id,txt,reply_markup=kb)

# ========= اجرای ربات =========
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True, timeout=30)
