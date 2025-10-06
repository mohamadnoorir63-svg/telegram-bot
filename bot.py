# -*- coding: utf-8 -*-
import telebot, os, threading, time, random
from telebot import types
from datetime import datetime
import pytz

# ================== تنظیمات ==================
TOKEN   = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID","0"))
SUPPORT_ID = "NOORI_NOOR"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
sudo_ids = {SUDO_ID}

# ========= چک سودو / ادمین =========
def is_sudo(uid): return uid in sudo_ids
def is_admin(chat_id, user_id):
    if is_sudo(user_id): return True
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
        msg=bot.reply_to(m,"❗ نتوانستم لینک بگیرم. (ربات باید ادمین با مجوز دعوت باشد)")
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
        txt = (welcome_texts.get(m.chat.id) or DEFAULT_WELCOME).format(name=name,title=m.chat.title)
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

# ========= فونت‌ساز (۱۰ استایل) =========
FONTS = [
    lambda t: "".join({"a":"𝗮","b":"𝗯","c":"𝗰","d":"𝗱","e":"𝗲","f":"𝗳","g":"𝗴","h":"𝗵",
                       "i":"𝗶","j":"𝗷","k":"𝗸","l":"𝗹","m":"𝗺","n":"𝗻","o":"𝗼","p":"𝗽",
                       "q":"𝗾","r":"𝗿","s":"𝘀","t":"𝘁","u":"𝘂","v":"𝘃","w":"𝘄","x":"𝘅",
                       "y":"𝘆","z":"𝘇"}.get(ch.lower(),ch) for ch in t),
    lambda t: "".join({"a":"𝑎","b":"𝑏","c":"𝑐","d":"𝑑","e":"𝑒","f":"𝑓","g":"𝑔","h":"ℎ",
                       "i":"𝑖","j":"𝑗","k":"𝑘","l":"𝑙","m":"𝑚","n":"𝑛","o":"𝑜","p":"𝑝",
                       "q":"𝑞","r":"𝑟","s":"𝑠","t":"𝑡","u":"𝑢","v":"𝑣","w":"𝑤","x":"𝑥",
                       "y":"𝑦","z":"𝑧"}.get(ch.lower(),ch) for ch in t),
    lambda t: "".join({"a":"ⓐ","b":"ⓑ","c":"ⓒ","d":"ⓓ","e":"ⓔ","f":"ⓕ","g":"ⓖ","h":"ⓗ",
                       "i":"ⓘ","j":"ⓙ","k":"ⓚ","l":"ⓛ","m":"ⓜ","n":"ⓝ","o":"ⓞ","p":"ⓟ",
                       "q":"ⓠ","r":"ⓡ","s":"ⓢ","t":"ⓣ","u":"ⓤ","v":"ⓥ","w":"ⓦ","x":"ⓧ",
                       "y":"ⓨ","z":"ⓩ"}.get(ch.lower(),ch) for ch in t),
    lambda t: "".join({"ا":"ٱ","ب":"بٰ","ت":"تہ","ج":"جـ","س":"سٰ","ش":"شٰ","م":"مہ",
                       "ن":"نٰ","ه":"ﮬ","و":"ۆ","ی":"ۍ"}.get(ch,ch) for ch in t),
    lambda t: "".join({"ا":"آ","ب":"ب̍","ت":"تۛ","ج":"ج͠","س":"سہ","ش":"شہ","م":"مہ",
                       "ن":"نہ","ه":"ﮬ","و":"و͠","ی":"يہ"}.get(ch,ch) for ch in t),
]
@bot.message_handler(func=lambda m: cmd_text(m).startswith("فونت "))
def make_fonts(m):
    name = cmd_text(m).replace("فونت ","",1).strip()
    if not name:
        msg=bot.reply_to(m,"❗ اسم رو هم بنویس"); auto_del(m.chat.id,msg.message_id); return
    res=f"🎨 فونت‌های خوشگل برای {name}:\n\n"
    for s in FONTS: 
        try: res+=s(name)+"\n"
        except: continue
    msg=bot.reply_to(m,res); auto_del(m.chat.id,msg.message_id,delay=20)

# ========= سیستم اصل =========
origins={}
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m).startswith("ثبت اصل "))
def set_origin(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid=m.reply_to_message.from_user.id
    val=cmd_text(m).replace("ثبت اصل ","",1).strip()
    origins.setdefault(m.chat.id,{})[uid]=val
    msg=bot.reply_to(m,f"✅ اصل ثبت شد: {val}"); auto_del(m.chat.id,msg.message_id,delay=7)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="اصل")
def get_origin(m):
    uid=m.reply_to_message.from_user.id
    val=origins.get(m.chat.id,{}).get(uid)
    msg=bot.reply_to(m,f"🧾 اصل: {val}" if val else "ℹ️ اصل ثبت نشده."); auto_del(m.chat.id,msg.message_id,delay=7)

@bot.message_handler(func=lambda m: cmd_text(m)=="اصل من")
def my_origin(m):
    val=origins.get(m.chat.id,{}).get(m.from_user.id)
    msg=bot.reply_to(m,f"🧾 اصل شما: {val}" if val else "ℹ️ اصل شما ثبت نشده."); auto_del(m.chat.id,msg.message_id,delay=7)

# ========= جوک و فال =========
jokes, fortunes=[],[]
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m).startswith("ثبت جوک"))
def save_joke(m):
    if m.reply_to_message:
        if m.reply_to_message.text:
            jokes.append({"type":"text","content":m.reply_to_message.text})
        elif m.reply_to_message.photo:
            jokes.append({"type":"photo","file":m.reply_to_message.photo[-1].file_id,"caption":m.reply_to_message.caption or ""})
        msg=bot.reply_to(m,"😂 جوک ذخیره شد."); auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="جوک")
def send_joke(m):
    if not jokes: return bot.reply_to(m,"❗ هیچ جوکی ذخیره نشده.")
    j=random.choice(jokes)
    bot.send_message(m.chat.id,j["content"]) if j["type"]=="text" else bot.send_photo(m.chat.id,j["file"],caption=j["caption"])

@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m).startswith("ثبت فال"))
def save_fal(m):
    if m.reply_to_message:
        if m.reply_to_message.text:
            fortunes.append({"type":"text","content":m.reply_to_message.text})
        elif m.reply_to_message.photo:
            fortunes.append({"type":"photo","file":m.reply_to_message.photo[-1].file_id,"caption":m.reply_to_message.caption or ""})
        msg=bot.reply_to(m,"🔮 فال ذخیره شد."); auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="فال")
def send_fal(m):
    if not fortunes: return bot.reply_to(m,"❗ هیچ فالی ذخیره نشده.")
    f=random.choice(fortunes)
    bot.send_message(m.chat.id,f["content"]) if f["type"]=="text" else bot.send_photo(m.chat.id,f["file"],caption=f["caption"])

# ========= راهنما مدیر =========
HELP_TEXT_ADMIN = """
📖 دستورات مدیران:

⏰ ساعت | 🆔 ایدی | 📊 آمار | 📎 لینک
🎉 خوشامد روشن/خاموش | ✍️ خوشامد متن | 🖼 ثبت عکس
🏷 اصل | اصل من | ثبت اصل (ریپلای)
😂 جوک | 🔮 فال | ثبت جوک/فال (ریپلای)
...
"""
@bot.message_handler(func=lambda m: cmd_text(m)=="راهنما")
def help_cmd(m):
    if m.chat.type in ("group","supergroup") and is_admin(m.chat.id,m.from_user.id):
        msg=bot.reply_to(m,HELP_TEXT_ADMIN); auto_del(m.chat.id,msg.message_id,delay=25)

# ========= استارت پیوی (پنل ممبر) =========
@bot.message_handler(commands=['start'])
def start_cmd(m):
    if m.chat.type=="private":
        kb=types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("➕ افزودن ربات به گروه", url=f"https://t.me/{bot.get_me().username}?startgroup=new"),
               types.InlineKeyboardButton("📞 پشتیبانی", url=f"https://t.me/{SUPPORT_ID}"))
        bot.send_message(m.chat.id,"👋 سلام!\n\nمن یک ربات مدیریت گروه هستم 🤖\n➕ منو به گروه اضافه کن و مدیرم کن تا شروع کنم.",reply_markup=kb)

# ========= اجرای ربات =========
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True,timeout=30)
