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
    msg=bot.reply_to(m,res); auto_del(m.chat.id,msg.message_id,delay=20)# ================== اصل ==================
origins = {}  # chat_id -> { user_id: text }

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m).startswith("ثبت اصل "))
def origin_set(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    val = cmd_text(m).replace("ثبت اصل ", "", 1).strip()
    origins.setdefault(m.chat.id, {})[uid] = val
    msg = bot.reply_to(m, f"✅ اصل برای {m.reply_to_message.from_user.first_name} ثبت شد: {val}")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m) == "اصل من")
def origin_me(m):
    val = origins.get(m.chat.id, {}).get(m.from_user.id)
    msg = bot.reply_to(m, f"🧾 اصل شما: {val}" if val else "ℹ️ اصل شما ثبت نشده.")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "اصل")
def origin_get(m):
    uid = m.reply_to_message.from_user.id
    val = origins.get(m.chat.id, {}).get(uid)
    msg = bot.reply_to(m, f"🧾 اصل: {val}" if val else "ℹ️ اصل ثبت نشده.")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف اصل")
def origin_del(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    ok = origins.get(m.chat.id, {}).pop(uid, None)
    msg = bot.reply_to(m, "🗑 اصل حذف شد." if ok else "ℹ️ اصلی ثبت نشده بود.")
    auto_del(m.chat.id, msg.message_id)


# ================== جوک ==================
jokes = []  # list of dicts

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "ثبت جوک")
def joke_add(m):
    if not m.reply_to_message:
        return
    if m.reply_to_message.text:
        jokes.append({"type":"text", "content":m.reply_to_message.text})
    elif m.reply_to_message.photo:
        jokes.append({"type":"photo", "file":m.reply_to_message.photo[-1].file_id, "caption":m.reply_to_message.caption or ""})
    msg = bot.reply_to(m, "😂 جوک ذخیره شد.")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def joke_send(m):
    if not jokes:
        return bot.reply_to(m, "ℹ️ هیچ جوکی ثبت نشده.")
    j = random.choice(jokes)
    if j["type"] == "text":
        bot.send_message(m.chat.id, j["content"])
    else:
        bot.send_photo(m.chat.id, j["file"], caption=j.get("caption") or "")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "لیست جوک‌ها")
def jokes_list(m):
    if not jokes:
        return bot.reply_to(m, "ℹ️ هیچ جوکی ثبت نشده.")
    start = max(0, len(jokes)-20)
    lines = []
    for i, j in enumerate(jokes[start:], start=1):
        if j["type"] == "text":
            prev = j["content"][:40] + ("…" if len(j["content"])>40 else "")
        else:
            prev = "[📸 عکس]" + (" — "+(j.get("caption")[:20]+"…") if j.get("caption") else "")
        lines.append(f"{i}. {prev}")
    msg = bot.reply_to(m, "😂 لیست جوک‌ها (۲۰ تای آخر):\n\n" + "\n".join(lines))
    auto_del(m.chat.id, msg.message_id, delay=30)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف جوک "))
def jokes_del(m):
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        start = max(0, len(jokes)-20)
        real = start + idx
        if 0 <= real < len(jokes):
            jokes.pop(real)
            msg = bot.reply_to(m, "✅ جوک حذف شد.")
        else:
            msg = bot.reply_to(m, "❗ شماره نامعتبر.")
    except:
        msg = bot.reply_to(m, "❗ فرمت صحیح: حذف جوک 3")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "پاکسازی جوک‌ها")
def jokes_clear(m):
    jokes.clear()
    msg = bot.reply_to(m, "🗑 همه جوک‌ها پاک شدند.")
    auto_del(m.chat.id, msg.message_id)


# ================== فال ==================
fortunes = []

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "ثبت فال")
def fal_add(m):
    if not m.reply_to_message:
        return
    if m.reply_to_message.text:
        fortunes.append({"type":"text", "content":m.reply_to_message.text})
    elif m.reply_to_message.photo:
        fortunes.append({"type":"photo", "file":m.reply_to_message.photo[-1].file_id, "caption":m.reply_to_message.caption or ""})
    msg = bot.reply_to(m, "🔮 فال ذخیره شد.")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def fal_send(m):
    if not fortunes:
        return bot.reply_to(m, "ℹ️ هیچ فالی ثبت نشده.")
    f = random.choice(fortunes)
    if f["type"] == "text":
        bot.send_message(m.chat.id, f["content"])
    else:
        bot.send_photo(m.chat.id, f["file"], caption=f.get("caption") or "")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "لیست فال‌ها")
def fal_list(m):
    if not fortunes:
        return bot.reply_to(m, "ℹ️ هیچ فالی ثبت نشده.")
    start = max(0, len(fortunes)-20)
    lines = []
    for i, f in enumerate(fortunes[start:], start=1):
        if f["type"] == "text":
            prev = f["content"][:40] + ("…" if len(f["content"])>40 else "")
        else:
            prev = "[📸 عکس]" + (" — "+(f.get("caption")[:20]+"…") if f.get("caption") else "")
        lines.append(f"{i}. {prev}")
    msg = bot.reply_to(m, "🔮 لیست فال‌ها (۲۰ تای آخر):\n\n" + "\n".join(lines))
    auto_del(m.chat.id, msg.message_id, delay=30)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف فال "))
def fal_del(m):
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        start = max(0, len(fortunes)-20)
        real = start + idx
        if 0 <= real < len(fortunes):
            fortunes.pop(real)
            msg = bot.reply_to(m, "✅ فال حذف شد.")
        else:
            msg = bot.reply_to(m, "❗ شماره نامعتبر.")
    except:
        msg = bot.reply_to(m, "❗ فرمت صحیح: حذف فال 2")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "پاکسازی فال‌ها")
def fal_clear(m):
    fortunes.clear()
    msg = bot.reply_to(m, "🗑 همه فال‌ها پاک شدند.")
    auto_del(m.chat.id, msg.message_id)# ================== پاکسازی کلی ==================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "پاکسازی")
def clear_all(m):
    try:
        for i in range(1, 9999):
            bot.delete_message(m.chat.id, m.message_id - i)
    except:
        pass
    bot.reply_to(m, "🧹 پاکسازی انجام شد")

# ================== لیست جوک‌ها ==================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "لیست جوک‌ها")
def list_jokes(m):
    if not jokes:
        return bot.reply_to(m, "ℹ️ هیچ جوکی ثبت نشده")
    start = max(0, len(jokes) - 20)
    lines = []
    for i, j in enumerate(jokes[start:], start=1):
        if j["type"] == "text":
            prev = (j["content"][:40] + "…") if len(j["content"]) > 40 else j["content"]
        else:
            prev = "[📸 عکس]" + (f" — {j.get('caption')[:30]}…" if j.get("caption") else "")
        lines.append(f"{i}. {prev}")
    bot.reply_to(m, "😂 لیست جوک‌ها (۲۰ تای آخر):\n\n" + "\n".join(lines))

# ================== لیست فال‌ها ==================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "لیست فال‌ها")
def list_fortunes(m):
    if not fortunes:
        return bot.reply_to(m, "ℹ️ هیچ فالی ثبت نشده")
    start = max(0, len(fortunes) - 20)
    lines = []
    for i, f in enumerate(fortunes[start:], start=1):
        if f["type"] == "text":
            prev = (f["content"][:40] + "…") if len(f["content"]) > 40 else f["content"]
        else:
            prev = "[📸 عکس]" + (f" — {f.get('caption')[:30]}…" if f.get("caption") else "")
        lines.append(f"{i}. {prev}")
    bot.reply_to(m, "🔮 لیست فال‌ها (۲۰ تای آخر):\n\n" + "\n".join(lines))

# ================== حذف جوک / فال با شماره ==================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف جوک "))
def del_joke_num(m):
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        if 0 <= idx < len(jokes):
            jokes.pop(idx)
            bot.reply_to(m, "✅ جوک حذف شد")
        else:
            bot.reply_to(m, "❗ شماره نامعتبر")
    except:
        bot.reply_to(m, "❗ فرمت: حذف جوک [عدد]")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف فال "))
def del_fal_num(m):
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        if 0 <= idx < len(fortunes):
            fortunes.pop(idx)
            bot.reply_to(m, "✅ فال حذف شد")
        else:
            bot.reply_to(m, "❗ شماره نامعتبر")
    except:
        bot.reply_to(m, "❗ فرمت: حذف فال [عدد]")

# ================== حذف جوک / فال با ریپلای ==================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "حذف جوک")
def del_joke_reply(m):
    t = m.reply_to_message
    removed = False
    if t.text:
        for i, j in enumerate(jokes):
            if j["type"] == "text" and j["content"] == t.text:
                jokes.pop(i); removed = True; break
    elif t.photo:
        fid = t.photo[-1].file_id
        for i, j in enumerate(jokes):
            if j["type"] == "photo" and j.get("file") == fid:
                jokes.pop(i); removed = True; break
    bot.reply_to(m, "✅ جوک حذف شد" if removed else "ℹ️ جوک مطابق پیدا نشد")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "حذف فال")
def del_fal_reply(m):
    t = m.reply_to_message
    removed = False
    if t.text:
        for i, f in enumerate(fortunes):
            if f["type"] == "text" and f["content"] == t.text:
                fortunes.pop(i); removed = True; break
    elif t.photo:
        fid = t.photo[-1].file_id
        for i, f in enumerate(fortunes):
            if f["type"] == "photo" and f.get("file") == fid:
                fortunes.pop(i); removed = True; break
    bot.reply_to(m, "✅ فال حذف شد" if removed else "ℹ️ فال مطابق پیدا نشد")

# ================== پاکسازی لیست‌ها ==================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "پاکسازی جوک‌ها")
def clear_jokes(m):
    jokes.clear()
    bot.reply_to(m, "🗑 همه جوک‌ها پاک شدند")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "پاکسازی فال‌ها")
def clear_fals(m):
    fortunes.clear()
    bot.reply_to(m, "🗑 همه فال‌ها پاک شدند")

# ================== پاکسازی با عدد (با پیام تأیید) ==================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف "))
def delete_n_messages(m):
    parts = cmd_text(m).split()
    if len(parts) < 2: return
    try:
        n = int(parts[1])
        for i in range(n):
            bot.delete_message(m.chat.id, m.message_id - i)
        bot.reply_to(m, f"🗑 {n} پیام پاک شد")
    except:
        bot.reply_to(m, "❗ خطا در حذف پیام‌ها")# ================== ذخیره گروه‌ها ==================
GROUPS_FILE = "groups.txt"

def save_group(chat_id):
    try:
        groups = set()
        if os.path.exists(GROUPS_FILE):
            with open(GROUPS_FILE,"r") as f:
                groups = set([int(x.strip()) for x in f if x.strip()])
        groups.add(chat_id)
        with open(GROUPS_FILE,"w") as f:
            f.write("\n".join(str(x) for x in groups))
    except: pass

@bot.message_handler(content_types=['new_chat_members','text'])
def save_groups_handler(m):
    if m.chat.type in ["supergroup","group"]:
        save_group(m.chat.id)

# ================== ارسال همگانی ==================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("ارسال "))
def broadcast(m):
    text = cmd_text(m).replace("ارسال ","",1).strip()
    if not text:
        return bot.reply_to(m,"❗ متن خالی است.")

    sent, failed = 
