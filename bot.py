# -*- coding: utf-8 -*-
import os, random, threading, time
from datetime import datetime
import pytz
import telebot

# ================== تنظیمات ==================
TOKEN   = os.environ.get("BOT_TOKEN") or "توکن_اینجا"
SUDO_ID = int(os.environ.get("SUDO_ID", "123456789"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
sudo_ids = {SUDO_ID}

# ================== توابع کمکی ==================
def is_sudo(uid): 
    return uid in sudo_ids

def is_admin(chat_id, user_id):
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator","creator")
    except: 
        return False

def cmd_text(m): 
    return (getattr(m,"text",None) or "").strip()

# ================== خوشامد ==================
WELCOME_MSG = "🎉 خوش اومدی {name} به گروه {title}"

@bot.message_handler(content_types=["new_chat_members"])
def welcome(m):
    for user in m.new_chat_members:
        text = WELCOME_MSG.format(name=user.first_name, title=m.chat.title)
        bot.send_message(m.chat.id, text)

# ================== سیستم اخطار ==================
warns = {}  # {chat_id:{user_id:count}}

def add_warn(chat_id, user_id, m_id):
    count = warns.setdefault(chat_id, {}).get(user_id, 0) + 1
    warns[chat_id][user_id] = count
    if count == 1:
        bot.reply_to(m_id, "⚠️ اخطار اول! ارسال لینک ممنوعه.")
    elif count == 2:
        bot.restrict_chat_member(chat_id, user_id, until_date=time.time()+3600, can_send_messages=False)
        bot.reply_to(m_id, "⏳ کاربر برای ۱ ساعت سکوت شد (اخطار دوم).")
    elif count >= 3:
        bot.ban_chat_member(chat_id, user_id)
        bot.reply_to(m_id, "🚫 کاربر به دلیل ۳ اخطار بن شد.")

# ================== فان (جوک و فال) ==================
jokes=[]; fortunes=[]
def save_item(arr,m):
    if m.reply_to_message:
        if m.reply_to_message.text:
            arr.append({"type":"text","content":m.reply_to_message.text})
        elif m.reply_to_message.photo:
            arr.append({"type":"photo","file":m.reply_to_message.photo[-1].file_id,"caption":m.reply_to_message.caption or ""})

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ثبت جوک")
def add_joke(m): save_item(jokes,m); bot.reply_to(m,"😂 جوک ذخیره شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="جوک")
def send_joke(m):
    if not jokes: return bot.reply_to(m,"❗ جوکی ثبت نشده")
    j=random.choice(jokes)
    if j["type"]=="text": bot.send_message(m.chat.id,j["content"])
    else: bot.send_photo(m.chat.id,j["file"],caption=j["caption"])

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ثبت فال")
def add_fal(m): save_item(fortunes,m); bot.reply_to(m,"🔮 فال ذخیره شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="فال")
def send_fal(m):
    if not fortunes: return bot.reply_to(m,"❗ فالی ثبت نشده")
    f=random.choice(fortunes)
    if f["type"]=="text": bot.send_message(m.chat.id,f["content"])
    else: bot.send_photo(m.chat.id,f["file"],caption=f["caption"])

# ================== قفل‌ها ==================
locks={k:{} for k in ["links","stickers","photo","video","gif","file","music","voice","forward","group"]}
LOCK_MAP={
    "لینک":"links","استیکر":"stickers","عکس":"photo","ویدیو":"video",
    "گیف":"gif","فایل":"file","موزیک":"music","ویس":"voice","فوروارد":"forward","گروه":"group"
}

@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل "))
def lock(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    key=LOCK_MAP.get(cmd_text(m).replace("قفل ","",1))
    if key: locks[key][m.chat.id]=True; bot.reply_to(m,"🔒 قفل فعال شد")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("باز کردن "))
def unlock(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    key=LOCK_MAP.get(cmd_text(m).replace("باز کردن ","",1))
    if key: locks[key][m.chat.id]=False; bot.reply_to(m,"🔓 قفل باز شد")

# enforce قفل‌ها
@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation'])
def enforce(m):
    if is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id): return
    txt=m.text or ""
    if locks["group"].get(m.chat.id): return bot.delete_message(m.chat.id,m.message_id)
    if locks["links"].get(m.chat.id) and any(x in txt for x in ["http://","https://","t.me"]): 
        bot.delete_message(m.chat.id,m.message_id); add_warn(m.chat.id,m.from_user.id,m)
    if locks["stickers"].get(m.chat.id) and m.sticker: bot.delete_message(m.chat.id,m.message_id)
    if locks["photo"].get(m.chat.id) and m.photo: bot.delete_message(m.chat.id,m.message_id)
    if locks["video"].get(m.chat.id) and m.video: bot.delete_message(m.chat.id,m.message_id)
    if locks["gif"].get(m.chat.id) and m.animation: bot.delete_message(m.chat.id,m.message_id)
    if locks["file"].get(m.chat.id) and m.document: bot.delete_message(m.chat.id,m.message_id)
    if locks["music"].get(m.chat.id) and m.audio: bot.delete_message(m.chat.id,m.message_id)
    if locks["voice"].get(m.chat.id) and m.voice: bot.delete_message(m.chat.id,m.message_id)
    if locks["forward"].get(m.chat.id) and (m.forward_from or m.forward_from_chat): bot.delete_message(m.chat.id,m.message_id)

# ================== قفل خودکار ==================
auto_lock={}
@bot.message_handler(func=lambda m: cmd_text(m).startswith("تنظیم قفل خودکار "))
def set_auto_lock(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    try:
        _,_,s,e = cmd_text(m).split()
        start,end=int(s),int(e)
        auto_lock[m.chat.id]={"start":start,"end":end,"enabled":True}
        bot.reply_to(m,f"⏰ قفل خودکار تنظیم شد از {start}:00 تا {end}:00")
    except: bot.reply_to(m,"❗ فرمت: تنظیم قفل خودکار 23 07")

def auto_lock_checker():
    while True:
        now=datetime.now(pytz.timezone("Asia/Tehran")).hour
        for chat_id,conf in list(auto_lock.items()):
            if not conf.get("enabled"): continue
            start,end=conf["start"],conf["end"]
            inside=(start<=now<end) if start<end else (now>=start or now<end)
            locks["group"][chat_id]=inside
        time.sleep(60)

threading.Thread(target=auto_lock_checker,daemon=True).start()

# ================== دستورات عمومی ==================
@bot.message_handler(func=lambda m: cmd_text(m)=="ساعت")
def cmd_time(m):
    now_teh=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    bot.reply_to(m,f"⏰ زمان تهران: {now_teh}")

@bot.message_handler(func=lambda m: cmd_text(m)=="آمار")
def cmd_stats(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    try: count=bot.get_chat_member_count(m.chat.id)
    except: count="نامشخص"
    bot.reply_to(m,f"📊 اعضای گروه: {count}")

@bot.message_handler(func=lambda m: cmd_text(m)=="ایدی")
def cmd_id(m):
    bot.reply_to(m,f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>")

# ================== اجرای ربات ==================
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True,timeout=30)
