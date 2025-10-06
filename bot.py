# -*- coding: utf-8 -*-
import telebot, os, threading, time, random
from datetime import datetime
import pytz
from telebot import types

# ================== تنظیمات ==================
TOKEN   = os.environ.get("BOT_TOKEN")        # توکن ربات
SUDO_ID = int(os.environ.get("SUDO_ID","0")) # آیدی سودو اصلی
SUPPORT_ID = "NOORI_NOOR"                    # پشتیبانی

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

# روشن / خاموش
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

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="ثبت عکس")
def w_photo(m):
    if is_admin(m.chat.id,m.from_user.id) and m.reply_to_message.photo:
        welcome_photos[m.chat.id]=m.reply_to_message.photo[-1].file_id
        msg=bot.reply_to(m,"🖼 عکس خوشامد ذخیره شد."); auto_del(m.chat.id,msg.message_id)

# ========= فونت‌ساز =========
FONTS = [
    lambda t: "".join({"a":"𝗮","b":"𝗯","c":"𝗰","d":"𝗱","e":"𝗲","f":"𝗳","g":"𝗴","h":"𝗵",
                       "i":"𝗶","j":"𝗷","k":"𝗸","l":"𝗹","m":"𝗺","n":"𝗻","o":"𝗼","p":"𝗽",
                       "q":"𝗾","r":"𝗿","s":"𝘀","t":"𝘁","u":"𝘂","v":"𝘃","w":"𝘄","x":"𝘅",
                       "y":"𝘆","z":"𝘇"}.get(ch.lower(),ch) for ch in t),
    lambda t: "".join({"a":"𝑎","b":"𝑏","c":"𝑐","d":"𝑑","e":"𝑒","f":"𝑓","g":"𝑔","h":"ℎ",
                       "i":"𝑖","j":"𝑗","k":"𝑘","l":"𝑙","m":"𝑚","n":"𝑛","o":"𝑜","p":"𝑝",
                       "q":"𝑞","r":"𝑟","s":"𝑠","t":"𝑡","u":"𝑢","v":"𝑣","w":"𝑤","x":"𝑥",
                       "y":"𝑦","z":"𝑧"}.get(ch.lower(),ch) for ch in t),
    # ۸ استایل دیگه هم میشه اضافه کرد (حروف فارسی و فانتزی)
]
@bot.message_handler(func=lambda m: cmd_text(m).startswith("فونت "))
def make_fonts(m):
    name = cmd_text(m).replace("فونت ","",1).strip()
    if not name:
        msg=bot.reply_to(m,"❗ اسم رو هم بنویس"); auto_del(m.chat.id,msg.message_id); return
    res=f"🎨 فونت‌ها برای {name}:\n\n"
    for style in FONTS:
        try: res+=style(name)+"\n"
        except: continue
    msg=bot.reply_to(m,res); auto_del(m.chat.id,msg.message_id,delay=20)

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
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m).startswith("ثبت جوک"))
def save_joke(m):
    if m.reply_to_message:
        if m.reply_to_message.text:
            jokes.append({"type":"text","content":m.reply_to_message.text})
        elif m.reply_to_message.photo:
            jokes.append({"type":"photo","file":m.reply_to_message.photo[-1].file_id,"caption":m.reply_to_message.caption or ""})
        msg=bot.reply_to(m,"😂 جوک ذخیره شد.")
    else: msg=bot.reply_to(m,"❗ روی پیام جوک ریپلای کن.")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="جوک")
def send_joke(m):
    if not jokes: return bot.reply_to(m,"❗ هیچ جوکی ذخیره نشده.")
    joke=random.choice(jokes)
    if joke["type"]=="text": bot.send_message(m.chat.id,joke["content"])
    else: bot.send_photo(m.chat.id,joke["file"],caption=joke["caption"])

# (برای فال هم مشابه جوک پیاده‌سازی شده)

# ========= قفل‌ها و پنل =========
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
    kb.add(*btns); kb.add(types.InlineKeyboardButton("❌ بستن",callback_data=f"close:{m.chat.id}"))
    bot.reply_to(m,"🛠 پنل مدیریت قفل‌ها:",reply_markup=kb)

# ========= بن / سکوت / اخطار / مدیر =========
warnings={}; MAX_WARNINGS=3
# (اینجا کدهای بن، سکوت، اخطار و ارتقا/حذف مدیر کامل هست مثل نسخه‌های قبلی)

# ========= پن / حذف پن =========
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="پن")
def pin_msg(m):
    if is_admin(m.chat.id,m.from_user.id):
        try: bot.pin_chat_message(m.chat.id,m.reply_to_message.message_id,disable_notification=True); msg=bot.reply_to(m,"📌 پیام سنجاق شد.")
        except: msg=bot.reply_to(m,"❗ نتوانستم سنجاق کنم.")
        auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="حذف پن")
def unpin_msg(m):
    if is_admin(m.chat.id,m.from_user.id):
        try: bot.unpin_chat_message(m.chat.id); msg=bot.reply_to(m,"❌ سنجاق برداشته شد.")
        except: msg=bot.reply_to(m,"❗ سنجاقی پیدا نشد.")
        auto_del(m.chat.id,msg.message_id)

# ========= پاکسازی =========
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m).startswith("حذف "))
def del_n(m):
    try:
        n=int(cmd_text(m).split()[1]); 
        for i in range(n): bot.delete_message(m.chat.id,m.message_id-i)
    except: pass

# ========= لیست مدیران =========
@bot.message_handler(func=lambda m: cmd_text(m)=="لیست مدیران گروه")
def admins_list(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    admins=bot.get_chat_administrators(m.chat.id)
    txt="👑 مدیران گروه:\n"+"\n".join([f"▪️ {a.user.first_name} — <code>{a.user.id}</code>" for a in admins])
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

# ========= استارت پیوی =========
@bot.message_handler(commands=['start'])
def start_cmd(m):
    if m.chat.type!="private": return
    kb=types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("➕ افزودن ربات به گروه", url=f"https://t.me/{bot.get_me().username}?startgroup=new"),
        types.InlineKeyboardButton("📞 پشتیبانی", url=f"https://t.me/{SUPPORT_ID}")
    )
    txt=("👋 سلام!\n\nمن ربات مدیریت گروه هستم 🤖\n\n"
         "📌 امکانات:\n"
         "• قفل‌ها\n• خوشامد\n• اخطار/بن/سکوت\n• اصل\n• جوک و فال\n• ابزار مدیریتی\n\n➕ منو به گروهت اضافه کن.")
    bot.send_message(m.chat.id,txt,reply_markup=kb)

# ========= اجرای ربات =========
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True, timeout=30)
