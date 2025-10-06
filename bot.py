# -*- coding: utf-8 -*-
import os, re, time, threading, random
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
    def _(): time.sleep(delay); 
    threading.Thread(target=lambda: (time.sleep(delay), bot.delete_message(chat_id,msg_id)), daemon=True).start()

# ================== دستورات عمومی ==================
@bot.message_handler(func=lambda m: cmd_text(m)=="ساعت")
def cmd_time(m):
    now_utc=datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_teh=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    msg=bot.reply_to(m,f"⏰ UTC: {now_utc}\n⏰ تهران: {now_teh}")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="ایدی")
def cmd_id(m):
    msg=bot.reply_to(m,f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="آمار")
def cmd_stats(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try: count=bot.get_chat_member_count(m.chat.id)
    except: count="نامشخص"
    msg=bot.reply_to(m,f"📊 اعضای گروه: {count}")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="لینک")
def cmd_link(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try: link=bot.export_chat_invite_link(m.chat.id)
    except: link="❗ خطا در گرفتن لینک."
    msg=bot.reply_to(m,f"📎 {link}")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="وضعیت ربات")
def cmd_status(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    now=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    msg=bot.reply_to(m,f"🤖 فعال هستم\n🕒 {now}")
    auto_del(m.chat.id,msg.message_id)

# جواب سودو «ربات»
SUDO_RESPONSES=["جونم قربان 😎","در خدمتم ✌️","ربات آماده‌ست 🚀","چه خبر رئیس؟ 🤖"]
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ربات")
def cmd_sudo(m):
    msg=bot.reply_to(m,random.choice(SUDO_RESPONSES))
    auto_del(m.chat.id,msg.message_id)

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
        msg=bot.reply_to(m,"✅ خوشامد روشن شد"); auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="خوشامد خاموش")
def w_off(m): 
    if is_admin(m.chat.id,m.from_user.id):
        welcome_enabled[m.chat.id]=False
        msg=bot.reply_to(m,"❌ خوشامد خاموش شد"); auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m).startswith("خوشامد متن "))
def w_txt(m):
    if is_admin(m.chat.id,m.from_user.id):
        welcome_texts[m.chat.id]=cmd_text(m).replace("خوشامد متن ","",1)
        msg=bot.reply_to(m,"✍️ متن خوشامد ذخیره شد"); auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="ثبت عکس")
def w_pic(m):
    if is_admin(m.chat.id,m.from_user.id) and m.reply_to_message.photo:
        welcome_photos[m.chat.id]=m.reply_to_message.photo[-1].file_id
        msg=bot.reply_to(m,"🖼 عکس خوشامد ذخیره شد"); auto_del(m.chat.id,msg.message_id)

# ================== فونت‌ها (۱۰ استایل) ==================
FONTS=[
    lambda t:"".join({"a":"𝗮","b":"𝗯","c":"𝗰","d":"𝗱","e":"𝗲","f":"𝗳","g":"𝗴","h":"𝗵","i":"𝗶","j":"𝗷","k":"𝗸","l":"𝗹","m":"𝗺","n":"𝗻","o":"𝗼","p":"𝗽","q":"𝗾","r":"𝗿","s":"𝘀","t":"𝘁","u":"𝘂","v":"𝘃","w":"𝘄","x":"𝘅","y":"𝘆","z":"𝘇"}.get(ch.lower(),ch) for ch in t),
    lambda t:"".join({"a":"𝑎","b":"𝑏","c":"𝑐","d":"𝑑","e":"𝑒","f":"𝑓","g":"𝑔","h":"ℎ","i":"𝑖","j":"𝑗","k":"𝑘","l":"𝑙","m":"𝑚","n":"𝑛","o":"𝑜","p":"𝑝","q":"𝑞","r":"𝑟","s":"𝑠","t":"𝑡","u":"𝑢","v":"𝑣","w":"𝑤","x":"𝑥","y":"𝑦","z":"𝑧"}.get(ch.lower(),ch) for ch in t),
    lambda t:"".join({"a":"ⓐ","b":"ⓑ","c":"ⓒ","d":"ⓓ","e":"ⓔ","f":"ⓕ","g":"ⓖ","h":"ⓗ","i":"ⓘ","j":"ⓙ","k":"ⓚ","l":"ⓛ","m":"ⓜ","n":"ⓝ","o":"ⓞ","p":"ⓟ","q":"ⓠ","r":"ⓡ","s":"ⓢ","t":"ⓣ","u":"ⓤ","v":"ⓥ","w":"ⓦ","x":"ⓧ","y":"ⓨ","z":"ⓩ"}.get(ch.lower(),ch) for ch in t),
    lambda t:"".join({"a":"ᴀ","b":"ʙ","c":"ᴄ","d":"ᴅ","e":"ᴇ","f":"ғ","g":"ɢ","h":"ʜ","i":"ɪ","j":"ᴊ","k":"ᴋ","l":"ʟ","m":"ᴍ","n":"ɴ","o":"ᴏ","p":"ᴘ","q":"ǫ","r":"ʀ","s":"s","t":"ᴛ","u":"ᴜ","v":"ᴠ","w":"ᴡ","x":"x","y":"ʏ","z":"ᴢ"}.get(ch.lower(),ch) for ch in t),
    lambda t:"".join({"a":"𝔞","b":"𝔟","c":"𝔠","d":"𝔡","e":"𝔢","f":"𝔣","g":"𝔤","h":"𝔥","i":"𝔦","j":"𝔧","k":"𝔨","l":"𝔩","m":"𝔪","n":"𝔫","o":"𝔬","p":"𝔭","q":"𝔮","r":"𝔯","s":"𝔰","t":"𝔱","u":"𝔲","v":"𝔳","w":"𝔴","x":"𝔵","y":"𝔶","z":"𝔷"}.get(ch.lower(),ch) for ch in t),
    lambda t:"".join({"ا":"ٱ","ب":"بٰ","ت":"تہ","ث":"ثٰ","ج":"جـ","ح":"حہ","خ":"خہ","د":"دٰ","ر":"رٰ","س":"سٰ","ش":"شٰ","ع":"عہ","غ":"غہ","ف":"فہ","ق":"قٰ","ک":"ڪ","ل":"لہ","م":"مہ","ن":"نٰ","ه":"ﮬ","و":"ۆ","ی":"ۍ"}.get(ch,ch) for ch in t),
    lambda t:"".join({"ا":"آ","ب":"ب̍","ت":"تۛ","ث":"ثہ","ج":"ج͠","ح":"حٰ","خ":"خ̐","د":"دُ","ذ":"ذٰ","ر":"ر͜","ز":"زٰ","س":"سہ","ش":"شہ","ع":"عہ","غ":"غہ","ف":"فہ","ق":"ق͠","ک":"ڪہ","ل":"لہ","م":"مہ","ن":"نہ","ه":"ﮬ","و":"و͠","ی":"يہ"}.get(ch,ch) for ch in t),
    lambda t:"".join({"ا":"اٰ","ب":"بـ","ت":"تـ","ث":"ثـ","ج":"ﮔ","ح":"حـ","خ":"خـ","د":"دٰ","ر":"رٰ","س":"سـ","ش":"شـ","ع":"عـ","غ":"غـ","ف":"فـ","ق":"قـ","ک":"ڪ","گ":"گـ","ل":"لـ","م":"مـ","ن":"نـ","ه":"هـ","و":"ۅ","ی":"ۍ"}.get(ch,ch) for ch in t),
    lambda t:"".join({"ا":"ﺂ","ب":"ﺑ","ت":"ﺗ","ث":"ﺛ","ج":"ﺟ","ح":"ﺣ","خ":"ﺧ","د":"ﮄ","ر":"ﺭ","ز":"ﺯ","س":"ﺳ","ش":"ﺷ","ع":"ﻋ","غ":"ﻏ","ف":"ﻓ","ق":"ﻗ","ک":"ﮎ","ل":"ﻟ","م":"ﻣ","ن":"ﻧ","ه":"ﮬ","و":"ۆ","ی":"ﯼ"}.get(ch,ch) for ch in t),
    lambda t:"".join({"ا":"آ","ب":"بہ","ت":"تـ","ث":"ثہ","ج":"جہ","ح":"حہ","خ":"خہ","د":"دٰ","ر":"رٰ","س":"سہ","ش":"شہ","ع":"عہ","غ":"غہ","ف":"فہ","ق":"قہ","ک":"کہ","ل":"لہ","م":"مہ","ن":"نہ","ه":"ﮬ","و":"ۅ","ی":"یے"}.get(ch,ch) for ch in t),
]

@bot.message_handler(func=lambda m: cmd_text(m).startswith("فونت "))
def cmd_fonts(m):
    name=cmd_text(m).replace("فونت ","",1)
    if not name: return
    res=f"🎨 فونت‌ها برای {name}:\n\n"
    for s in FONTS:
        try: res+=s(name)+"\n"
        except: pass
    msg=bot.reply_to(m,res); auto_del(m.chat.id,msg.message_id,delay=20)

# ================== اصل ==================
origins={}
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m).startswith("ثبت اصل "))
def origin_set(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid=m.reply_to_message.from_user.id
    val=cmd_text(m).replace("ثبت اصل ","",1)
    origins.setdefault(m.chat.id,{})[uid]=val
    msg=bot.reply_to(m,f"✅ اصل ثبت شد: {val}"); auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="اصل من")
def origin_me(m):
    val=origins.get(m.chat.id,{}).get(m.from_user.id)
    msg=bot.reply_to(m,f"🧾 اصل شما: {val}" if val else "❗ ثبت نشده")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="اصل")
def origin_get(m):
    uid=m.reply_to_message.from_user.id
    val=origins.get(m.chat.id,{}).get(uid)
    msg=bot.reply_to(m,f"🧾 اصل: {val}" if val else "❗ ثبت نشده")
    auto_del(m.chat.id,msg.message_id)

# ================== جوک/فال ==================
jokes, fortunes=[],[]
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="ثبت جوک")
def joke_add(m):
    if m.reply_to_message:
        if m.reply_to_message.text: jokes.append({"type":"text","content":m.reply_to_message.text})
        elif m.reply_to_message.photo: jokes.append({"type":"photo","file":m.reply_to_message.photo[-1].file_id,"caption":m.reply_to_message.caption or ""})
        msg=bot.reply_to(m,"😂 ذخیره شد"); auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="جوک")
def joke_send(m):
    if not jokes: return
    j=random.choice(jokes)
    if j["type"]=="text": bot.send_message(m.chat.id,j["content"])
    else: bot.send_photo(m.chat.id,j["file"],caption=j.get("caption",""))

@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="ثبت فال")
def fal_add(m):
    if m.reply_to_message:
        if m.reply_to_message.text: fortunes.append({"type":"text","content":m.reply_to_message.text})
        elif m.reply_to_message.photo: fortunes.append({"type":"photo","file":m.reply_to_message.photo[-1].file_id,"caption":m.reply_to_message.caption or ""})
        msg=bot.reply_to(m,"🔮 ذخیره شد"); auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="فال")
def fal_send(m):
    if not fortunes: return
    f=random.choice(fortunes)
    if f["type"]=="text": bot.send_message(m.chat.id,f["content"])
    else: bot.send_photo(m.chat.id,f["file"],caption=f.get("caption",""))# ================== قفل‌ها ==================
locks={k:{} for k in ["links","stickers","bots","tabchi","group","photo","video","gif","file","music","voice","forward"]}
LOCK_MAP={"لینک":"links","استیکر":"stickers","ربات":"bots","تبچی":"tabchi","گروه":"group",
          "عکس":"photo","ویدیو":"video","گیف":"gif","فایل":"file","موزیک":"music","ویس":"voice","فوروارد":"forward"}

@bot.message_handler(func=lambda m: cmd_text(m)=="پنل")
def locks_panel(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    kb=types.InlineKeyboardMarkup(row_width=2)
    for name,key in LOCK_MAP.items():
        st="🔒" if locks[key].get(m.chat.id) else "🔓"
        kb.add(types.InlineKeyboardButton(f"{st} {name}",callback_data=f"toggle:{key}:{m.chat.id}"))
    kb.add(types.InlineKeyboardButton("❌ بستن",callback_data=f"close:{m.chat.id}"))
    bot.reply_to(m,"🛠 پنل مدیریت قفل‌ها:",reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("toggle:"))
def cb_toggle(c):
    _,key,chat_id=c.data.split(":"); chat_id=int(chat_id)
    if not is_admin(chat_id,c.from_user.id):
        return bot.answer_callback_query(c.id,"❌ فقط مدیران")
    locks[key][chat_id]=not locks[key].get(chat_id,False)
    bot.answer_callback_query(c.id,"✅ تغییر شد")
    # بازسازی
    kb=types.InlineKeyboardMarkup(row_width=2)
    for name,k in LOCK_MAP.items():
        st="🔒" if locks[k].get(chat_id) else "🔓"
        kb.add(types.InlineKeyboardButton(f"{st} {name}",callback_data=f"toggle:{k}:{chat_id}"))
    kb.add(types.InlineKeyboardButton("❌ بستن",callback_data=f"close:{chat_id}"))
    bot.edit_message_reply_markup(chat_id,c.message.message_id,reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("close:"))
def cb_close(c):
    try: bot.delete_message(c.message.chat.id,c.message.message_id)
    except: pass

# enforce locks
@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation'])
def enforce(m):
    if is_admin(m.chat.id,m.from_user.id): return
    txt=m.text or ""
    if locks["links"].get(m.chat.id) and any(x in txt for x in ["http://","https://","t.me"]): bot.delete_message(m.chat.id,m.message_id)
    if locks["stickers"].get(m.chat.id) and m.sticker: bot.delete_message(m.chat.id,m.message_id)
    if locks["photo"].get(m.chat.id) and m.photo: bot.delete_message(m.chat.id,m.message_id)
    if locks["video"].get(m.chat.id) and m.video: bot.delete_message(m.chat.id,m.message_id)
    if locks["gif"].get(m.chat.id) and m.animation: bot.delete_message(m.chat.id,m.message_id)
    if locks["file"].get(m.chat.id) and m.document: bot.delete_message(m.chat.id,m.message_id)
    if locks["music"].get(m.chat.id) and m.audio: bot.delete_message(m.chat.id,m.message_id)
    if locks["voice"].get(m.chat.id) and m.voice: bot.delete_message(m.chat.id,m.message_id)

# قفل ربات‌ها
@bot.message_handler(content_types=['new_chat_members'])
def block_bots(m):
    for u in m.new_chat_members:
        if u.is_bot and locks["bots"].get(m.chat.id):
            try: bot.kick_chat_member(m.chat.id,u.id)
            except: pass
        if "tabchi" in (u.username or "").lower() and locks["tabchi"].get(m.chat.id):
            try: bot.kick_chat_member(m.chat.id,u.id)
            except: pass

# ================== بن / سکوت / اخطار ==================
warnings={}; MAX_WARNINGS=3

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="بن")
def ban(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try: bot.ban_chat_member(m.chat.id,m.reply_to_message.from_user.id); bot.reply_to(m,"🚫 بن شد")
    except: bot.reply_to(m,"❗ خطا")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف بن")
def unban(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try: bot.unban_chat_member(m.chat.id,m.reply_to_message.from_user.id); bot.reply_to(m,"✅ آزاد شد")
    except: bot.reply_to(m,"❗ خطا")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="سکوت")
def mute(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try: bot.restrict_chat_member(m.chat.id,m.reply_to_message.from_user.id,can_send_messages=False); bot.reply_to(m,"🔕 سکوت شد")
    except: bot.reply_to(m,"❗ خطا")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف سکوت")
def unmute(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try: bot.restrict_chat_member(m.chat.id,m.reply_to_message.from_user.id,can_send_messages=True,can_send_media_messages=True,can_send_other_messages=True,can_add_web_page_previews=True)
    except: pass
    bot.reply_to(m,"🔊 سکوت برداشته شد")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="اخطار")
def warn(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid=m.reply_to_message.from_user.id
    warnings.setdefault(m.chat.id,{})
    warnings[m.chat.id][uid]=warnings[m.chat.id].get(uid,0)+1
    c=warnings[m.chat.id][uid]
    if c>=MAX_WARNINGS:
        try: bot.ban_chat_member(m.chat.id,uid); bot.reply_to(m,"🚫 کاربر با ۳ اخطار بن شد")
        except: bot.reply_to(m,"❗ خطا")
        warnings[m.chat.id][uid]=0
    else: bot.reply_to(m,f"⚠️ اخطار {c}/{MAX_WARNINGS}")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف اخطار")
def reset_warn(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    warnings.get(m.chat.id,{}).pop(m.reply_to_message.from_user.id,None)
    bot.reply_to(m,"✅ اخطارها حذف شد")

# ================== مدیر / پن / پاکسازی ==================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="مدیر")
def promote(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try: bot.promote_chat_member(m.chat.id,m.reply_to_message.from_user.id,
        can_manage_chat=True,can_delete_messages=True,
        can_restrict_members=True,can_pin_messages=True,can_invite_users=True)
    except: pass
    bot.reply_to(m,"👑 مدیر شد")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف مدیر")
def demote(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try: bot.promote_chat_member(m.chat.id,m.reply_to_message.from_user.id,
        can_manage_chat=False,can_delete_messages=False,
        can_restrict_members=False,can_pin_messages=False,can_invite_users=False)
    except: pass
    bot.reply_to(m,"❌ مدیر حذف شد")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="پن")
def pin(m):
    if is_admin(m.chat.id,m.from_user.id):
        try: bot.pin_chat_message(m.chat.id,m.reply_to_message.message_id)
        except: pass
        bot.reply_to(m,"📌 سنجاق شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="حذف پن")
def unpin(m):
    if is_admin(m.chat.id,m.from_user.id):
        try: bot.unpin_chat_message(m.chat.id)
        except: pass
        bot.reply_to(m,"❌ سنجاق برداشته شد")

@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m).startswith("حذف "))
def del_n(m):
    try:
        n=int(cmd_text(m).split()[1])
        for i in range(n):
            bot.delete_message(m.chat.id,m.message_id-i)
        bot.reply_to(m,f"🗑 {n} پیام پاک شد")
    except: pass# ================== دستورات سودو ==================

# افزودن سودو
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("افزودن سودو "))
def add_sudo(m):
    try:
        uid = int(cmd_text(m).split()[2])
        sudo_ids.add(uid)
        msg = bot.reply_to(m, f"✅ کاربر {uid} به سودوها اضافه شد.")
    except:
        msg = bot.reply_to(m, "❗ فرمت صحیح: افزودن سودو 123456")
    auto_del(m.chat.id, msg.message_id)

# حذف سودو
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("حذف سودو "))
def del_sudo(m):
    try:
        uid = int(cmd_text(m).split()[2])
        if uid in sudo_ids and uid != SUDO_ID:
            sudo_ids.remove(uid)
            msg = bot.reply_to(m, f"❌ کاربر {uid} از سودوها حذف شد.")
        else:
            msg = bot.reply_to(m, "❗ این آیدی در سودوها نیست یا سودوی اصلی است.")
    except:
        msg = bot.reply_to(m, "❗ فرمت صحیح: حذف سودو 123456")
    auto_del(m.chat.id, msg.message_id)

# ارسال همگانی (فقط سودو)
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("ارسال "))
def broadcast(m):
    text = cmd_text(m).replace("ارسال ","",1)
    if not text: return
    # برای سادگی فقط توی همین گروه می‌فرسته (برای واقعی باید گروه‌ها ذخیره بشه)
    try:
        bot.send_message(m.chat.id, f"📢 ارسال همگانی:\n\n{text}")
        msg = bot.reply_to(m, "✅ پیام ارسال شد.")
    except:
        msg = bot.reply_to(m, "❗ خطا در ارسال.")
    auto_del(m.chat.id, msg.message_id)

# پنل سودو در پیوی
@bot.message_handler(func=lambda m: m.chat.type=="private" and is_sudo(m.from_user.id) and cmd_text(m)=="پنل سودو")
def sudo_panel(m):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("➕ افزودن سودو", callback_data="sudo:add"),
        types.InlineKeyboardButton("➖ حذف سودو", callback_data="sudo:del"),
        types.InlineKeyboardButton("📋 لیست سودوها", callback_data="sudo:list"),
        types.InlineKeyboardButton("👑 لیست مدیران ربات", callback_data="sudo:admins"),
        types.InlineKeyboardButton("📢 ارسال همگانی", callback_data="sudo:broadcast")
    )
    bot.send_message(m.chat.id, "⚙️ پنل مدیریت سودو:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("sudo:"))
def cb_sudo_panel(c):
    if not is_sudo(c.from_user.id):
        return bot.answer_callback_query(c.id,"❌ فقط برای سودوها",show_alert=True)

    if c.data=="
