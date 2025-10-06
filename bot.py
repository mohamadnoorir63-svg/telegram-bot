# -*- coding: utf-8 -*-
import os, time, threading, random
from datetime import datetime
import pytz
import telebot
from telebot import types

# ================== تنظیمات ==================
TOKEN     = os.environ.get("BOT_TOKEN")
SUDO_ID   = int(os.environ.get("SUDO_ID", "0"))

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
sudo_ids   = {SUDO_ID}
bot_admins = set()

# ================== کمکی‌ها ==================
def is_sudo(uid): return uid in sudo_ids
def is_bot_admin(uid): return uid in bot_admins or is_sudo(uid)
def is_admin(chat_id, user_id):
    if is_bot_admin(user_id): return True
    try: st = bot.get_chat_member(chat_id, user_id).status
    except: return False
    return st in ("administrator","creator")

def cmd_text(m): return (getattr(m,"text",None) or getattr(m,"caption",None) or "").strip()

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
    caption=f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>"
    try:
        photos=bot.get_user_profile_photos(m.from_user.id,limit=1)
        if photos.total_count>0:
            bot.send_photo(m.chat.id,photos.photos[0][-1].file_id,caption=caption)
        else: bot.reply_to(m,caption)
    except: bot.reply_to(m,caption)

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

# ================== خوشامد ==================
welcome_enabled, welcome_texts, welcome_photos = {}, {}, {}
DEFAULT_WELCOME="• سلام {name} به گروه {title} خوش آمدی 🌹\n📆 {date}\n⏰ {time}"

@bot.message_handler(content_types=['new_chat_members'])
def welcome(m):
    for u in m.new_chat_members:
        if not welcome_enabled.get(m.chat.id): continue
        txt=(welcome_texts.get(m.chat.id,DEFAULT_WELCOME)).format(
            name=u.first_name,title=m.chat.title,
            date=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y/%m/%d"),
            time=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%H:%M:%S")
        )
        if m.chat.id in welcome_photos:
            bot.send_photo(m.chat.id,welcome_photos[m.chat.id],caption=txt)
        else: bot.send_message(m.chat.id,txt)

@bot.message_handler(func=lambda m: cmd_text(m)=="خوشامد روشن")
def w_on(m): 
    if is_admin(m.chat.id,m.from_user.id):
        welcome_enabled[m.chat.id]=True
        bot.reply_to(m,"✅ خوشامد روشن شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="خوشامد خاموش")
def w_off(m): 
    if is_admin(m.chat.id,m.from_user.id):
        welcome_enabled[m.chat.id]=False
        bot.reply_to(m,"❌ خوشامد خاموش شد")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("خوشامد متن "))
def w_txt(m):
    if is_admin(m.chat.id,m.from_user.id):
        welcome_texts[m.chat.id]=cmd_text(m).replace("خوشامد متن ","",1)
        bot.reply_to(m,"✍️ متن خوشامد ذخیره شد")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="ثبت عکس")
def w_pic(m):
    if is_admin(m.chat.id,m.from_user.id) and m.reply_to_message.photo:
        welcome_photos[m.chat.id]=m.reply_to_message.photo[-1].file_id
        bot.reply_to(m,"🖼 عکس خوشامد ذخیره شد")

# ================== فونت‌ها (۱۰ استایل) ==================
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

# ================== اصل ==================
origins={}
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m).startswith("ثبت اصل "))
def origin_set(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid=m.reply_to_message.from_user.id
    val=cmd_text(m).replace("ثبت اصل ","",1).strip()
    origins.setdefault(m.chat.id,{})[uid]=val
    bot.reply_to(m,f"✅ اصل ثبت شد: {val}")

@bot.message_handler(func=lambda m: cmd_text(m)=="اصل من")
def origin_me(m):
    val=origins.get(m.chat.id,{}).get(m.from_user.id)
    bot.reply_to(m,f"🧾 اصل شما: {val}" if val else "ℹ️ ثبت نشده")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="اصل")
def origin_get(m):
    uid=m.reply_to_message.from_user.id
    val=origins.get(m.chat.id,{}).get(uid)
    bot.reply_to(m,f"🧾 اصل: {val}" if val else "ℹ️ ثبت نشده")

# ================== جوک و فال ==================
jokes=[]; fortunes=[]
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="ثبت جوک")
def joke_add(m):
    if m.reply_to_message:
        if m.reply_to_message.text: jokes.append({"type":"text","content":m.reply_to_message.text})
        elif m.reply_to_message.photo: jokes.append({"type":"photo","file":m.reply_to_message.photo[-1].file_id,"caption":m.reply_to_message.caption or ""})
        bot.reply_to(m,"😂 جوک ذخیره شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="جوک")
def joke_send(m):
    if not jokes: return bot.reply_to(m,"❗ جوکی ثبت نشده")
    j=random.choice(jokes)
    if j["type"]=="text": bot.send_message(m.chat.id,j["content"])
    else: bot.send_photo(m.chat.id,j["file"],caption=j["caption"])

@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="ثبت فال")
def fal_add(m):
    if m.reply_to_message:
        if m.reply_to_message.text: fortunes.append({"type":"text","content":m.reply_to_message.text})
        elif m.reply_to_message.photo: fortunes.append({"type":"photo","file":m.reply_to_message.photo[-1].file_id,"caption":m.reply_to_message.caption or ""})
        bot.reply_to(m,"🔮 فال ذخیره شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="فال")
def fal_send(m):
    if not fortunes: return bot.reply_to(m,"❗ فالی ثبت نشده")
    f=random.choice(fortunes)
    if f["type"]=="text": bot.send_message(m.chat.id,f["content"])
    else: bot.send_photo(m.chat.id,f["file"],caption=f["caption"])
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True,timeout=30)
