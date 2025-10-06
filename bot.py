# -*- coding: utf-8 -*-
import os, json, time, threading, random
from datetime import datetime
import pytz
import telebot
from telebot import types

# ================== تنظیمات ==================
TOKEN     = os.environ.get("BOT_TOKEN")
SUDO_ID   = int(os.environ.get("SUDO_ID", "0"))
SUPPORT_ID = "NOORI_NOOR"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

sudo_ids   = {SUDO_ID}
bot_admins = set()

# ================== توابع کمکی ==================
def is_sudo(uid): return uid in sudo_ids
def is_bot_admin(uid): return uid in bot_admins or is_sudo(uid)
def is_admin(chat_id, user_id):
    if is_bot_admin(user_id): return True
    try: st = bot.get_chat_member(chat_id, user_id).status
    except: return False
    return st in ("administrator","creator")

def cmd_text(m): 
    return (getattr(m,"text",None) or getattr(m,"caption",None) or "").strip()

def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file,"r",encoding="utf-8") as f: return json.load(f)
        except: return default
    return default

def save_json(file,data):
    try:
        with open(file,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
    except: pass

DELETE_DELAY = 7
def auto_del(chat_id, msg_id, delay=DELETE_DELAY):
    def _():
        time.sleep(delay)
        try: bot.delete_message(chat_id,msg_id)
        except: pass
    threading.Thread(target=_, daemon=True).start()

# ================== دستورات عمومی ==================
@bot.message_handler(func=lambda m: cmd_text(m)=="ساعت")
def cmd_time(m):
    now_utc=datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_teh=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    bot.reply_to(m,f"⏰ UTC: {now_utc}\n⏰ تهران: {now_teh}")

@bot.message_handler(func=lambda m: cmd_text(m)=="ایدی")
def cmd_id(m):
    bot.reply_to(m,f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>")

@bot.message_handler(func=lambda m: cmd_text(m)=="آمار")
def cmd_stats(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try: count=bot.get_chat_member_count(m.chat.id)
    except: count="نامشخص"
    bot.reply_to(m,f"📊 اعضای گروه: {count}")

@bot.message_handler(func=lambda m: cmd_text(m)=="لینک")
def cmd_link(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try: link=bot.export_chat_invite_link(m.chat.id)
    except: link="❗ خطا در گرفتن لینک."
    bot.reply_to(m,f"📎 {link}")

@bot.message_handler(func=lambda m: cmd_text(m)=="وضعیت ربات")
def cmd_status(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    now=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    bot.reply_to(m,f"🤖 فعال هستم\n🕒 {now}")

# جواب سودو «ربات»
SUDO_RESPONSES=["جونم قربان 😎","در خدمتم ✌️","ربات آماده‌ست 🚀","چه خبر رئیس؟ 🤖"]
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ربات")
def cmd_sudo(m):
    bot.reply_to(m,random.choice(SUDO_RESPONSES))

# ================== خوشامد (welcome.json) ==================
WELCOME_FILE="welcome.json"
welcome_data=load_json(WELCOME_FILE,{})

DEFAULT_WELCOME="• سلام {name} به گروه {title} خوش آمدی 🌹\n📆 {date}\n⏰ {time}"

@bot.message_handler(content_types=['new_chat_members'])
def welcome(m):
    for u in m.new_chat_members:
        w=welcome_data.get(str(m.chat.id),{})
        if not w.get("enabled"): continue
        txt=(w.get("text",DEFAULT_WELCOME)).format(
            name=u.first_name,title=m.chat.title,
            date=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y/%m/%d"),
            time=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%H:%M:%S")
        )
        if "photo" in w: bot.send_photo(m.chat.id,w["photo"],caption=txt)
        else: bot.send_message(m.chat.id,txt)

@bot.message_handler(func=lambda m: cmd_text(m)=="خوشامد روشن")
def w_on(m): 
    if is_admin(m.chat.id,m.from_user.id):
        welcome_data[str(m.chat.id)] = welcome_data.get(str(m.chat.id),{})
        welcome_data[str(m.chat.id)]["enabled"]=True
        save_json(WELCOME_FILE,welcome_data)
        bot.reply_to(m,"✅ خوشامد روشن شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="خوشامد خاموش")
def w_off(m): 
    if is_admin(m.chat.id,m.from_user.id):
        welcome_data[str(m.chat.id)] = welcome_data.get(str(m.chat.id),{})
        welcome_data[str(m.chat.id)]["enabled"]=False
        save_json(WELCOME_FILE,welcome_data)
        bot.reply_to(m,"❌ خوشامد خاموش شد")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("خوشامد متن "))
def w_txt(m):
    if is_admin(m.chat.id,m.from_user.id):
        txt=cmd_text(m).replace("خوشامد متن ","",1)
        welcome_data[str(m.chat.id)]=welcome_data.get(str(m.chat.id),{})
        welcome_data[str(m.chat.id)]["text"]=txt
        save_json(WELCOME_FILE,welcome_data)
        bot.reply_to(m,"✍️ متن خوشامد ذخیره شد")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="ثبت عکس")
def w_pic(m):
    if is_admin(m.chat.id,m.from_user.id) and m.reply_to_message.photo:
        welcome_data[str(m.chat.id)]=welcome_data.get(str(m.chat.id),{})
        welcome_data[str(m.chat.id)]["photo"]=m.reply_to_message.photo[-1].file_id
        save_json(WELCOME_FILE,welcome_data)
        bot.reply_to(m,"🖼 عکس خوشامد ذخیره شد")

# ================== فونت‌ها ==================
FONTS=[
    lambda t:"".join({"a":"𝗮","b":"𝗯","c":"𝗰","d":"𝗱","e":"𝗲","f":"𝗳","g":"𝗴","h":"𝗵","i":"𝗶","j":"𝗷","k":"𝗸","l":"𝗹","m":"𝗺","n":"𝗻","o":"𝗼","p":"𝗽","q":"𝗾","r":"𝗿","s":"𝘀","t":"𝘁","u":"𝘂","v":"𝘃","w":"𝘄","x":"𝘅","y":"𝘆","z":"𝘇"}.get(ch.lower(),ch) for ch in t),
    lambda t:"".join({"a":"𝑎","b":"𝑏","c":"𝑐","d":"𝑑","e":"𝑒","f":"𝑓","g":"𝑔","h":"ℎ","i":"𝑖","j":"𝑗","k":"𝑘","l":"𝑙","m":"𝑚","n":"𝑛","o":"𝑜","p":"𝑝","q":"𝑞","r":"𝑟","s":"𝑠","t":"𝑡","u":"𝑢","v":"𝑣","w":"𝑤","x":"𝑥","y":"𝑦","z":"𝑧"}.get(ch.lower(),ch) for ch in t),
    lambda t:"".join({"a":"ⓐ","b":"ⓑ","c":"ⓒ","d":"ⓓ","e":"ⓔ","f":"ⓕ","g":"ⓖ","h":"ⓗ","i":"ⓘ","j":"ⓙ","k":"ⓚ","l":"ⓛ","m":"ⓜ","n":"ⓝ","o":"ⓞ","p":"ⓟ","q":"ⓠ","r":"ⓡ","s":"ⓢ","t":"ⓣ","u":"ⓤ","v":"ⓥ","w":"ⓦ","x":"ⓧ","y":"ⓨ","z":"ⓩ"}.get(ch.lower(),ch) for ch in t),
    lambda t:"".join({"ا":"ٱ","ب":"بٰ","ت":"تہ","ث":"ثٰ","ج":"جـ","ح":"حہ","خ":"خہ","د":"دٰ","ر":"رٰ","س":"سٰ","ش":"شٰ","ع":"عہ","غ":"غہ","ف":"فہ","ق":"قٰ","ک":"ڪ","ل":"لہ","م":"مہ","ن":"نٰ","ه":"ﮬ","و":"ۆ","ی":"ۍ"}.get(ch,ch) for ch in t),
]
@bot.message_handler(func=lambda m: cmd_text(m).startswith("فونت "))
def cmd_fonts(m):
    name=cmd_text(m).replace("فونت ","",1)
    if not name: return
    res=f"🎨 فونت‌ها برای {name}:\n\n"
    for s in FONTS: 
        try: res+=s(name)+"\n"
        except: pass
    bot.reply_to(m,res)

# ================== اصل (origins.json) ==================
ORIG_FILE="origins.json"
origins=load_json(ORIG_FILE,{})

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m).startswith("ثبت اصل "))
def origin_set(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid=str(m.reply_to_message.from_user.id)
    val=cmd_text(m).replace("ثبت اصل ","",1)
    origins.setdefault(str(m.chat.id),{})[uid]=val
    save_json(ORIG_FILE,origins)
    bot.reply_to(m,f"✅ اصل برای {m.reply_to_message.from_user.first_name} ذخیره شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="اصل من")
def origin_me(m):
    val=origins.get(str(m.chat.id),{}).get(str(m.from_user.id))
    bot.reply_to(m,f"🧾 اصل شما: {val}" if val else "ℹ️ اصل شما ثبت نشده.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="اصل")
def origin_get(m):
    uid=str(m.reply_to_message.from_user.id)
    val=origins.get(str(m.chat.id),{}).get(uid)
    bot.reply_to(m,f"🧾 اصل: {val}" if val else "ℹ️ اصل ثبت نشده.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف اصل")
def origin_del(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid=str(m.reply_to_message.from_user.id)
    origins.get(str(m.chat.id),{}).pop(uid,None)
    save_json(ORIG_FILE,origins)
    bot.reply_to(m,"🗑 اصل حذف شد")

# ================== اجرا ==================
print("🤖 Bot Stage 1 Running...")
bot.infinity_polling(skip_pending=True,timeout=30)
