# -*- coding: utf-8 -*-
import telebot, os, threading, time
from datetime import datetime
import pytz
from telebot import types

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
        msg=bot.reply_to(m,"❗ نتوانستم لینک بگیرم. (بات باید ادمین با مجوز دعوت باشد)")
    auto_del(m.chat.id,msg.message_id)

# ========= راهنما =========
HELP_TEXT = """
📖 لیست دستورات پایه:

⏰ ساعت | 🆔 ایدی 
📊 آمار | 📎 لینک 
🛠 وضعیت ربات
"""

@bot.message_handler(func=lambda m: cmd_text(m)=="راهنما")
def help_cmd(m):
    if m.chat.type!="private" and not is_admin(m.chat.id,m.from_user.id): return
    msg=bot.reply_to(m,HELP_TEXT)
    auto_del(m.chat.id,msg.message_id,delay=20)

# ========= وضعیت ربات =========
@bot.message_handler(func=lambda m: cmd_text(m)=="وضعیت ربات")
def status_cmd(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    now=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    msg=bot.reply_to(m,f"🤖 ربات فعال است.\n🕒 زمان: {now}")
    auto_del(m.chat.id,msg.message_id)

# ========= استارت پیوی =========
@bot.message_handler(commands=['start'])
def start_cmd(m):
    if m.chat.type=="private":
        kb=types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/{bot.get_me().username}?startgroup=new"),
            types.InlineKeyboardButton("📞 پشتیبانی", url=f"https://t.me/{SUPPORT_ID}")
        )
        bot.send_message(m.chat.id,"👋 سلام!\n\nمن ربات مدیریت گروه هستم 🤖",reply_markup=kb)# ========= خوشامد =========
welcome_enabled, welcome_texts, welcome_photos = {}, {}, {}
DEFAULT_WELCOME = "• سلام {name} به گروه {title} خوش آمدید 🌻\n📆 {date}\n⏰ {time}"

@bot.message_handler(content_types=['new_chat_members'])
def welcome(m):
    for u in m.new_chat_members:
        if not welcome_enabled.get(m.chat.id): 
            continue
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
        msg=bot.reply_to(m,"✅ خوشامد روشن شد.")
        auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="خوشامد خاموش")
def w_off(m):
    if is_admin(m.chat.id,m.from_user.id):
        welcome_enabled[m.chat.id]=False
        msg=bot.reply_to(m,"❌ خوشامد خاموش شد.")
        auto_del(m.chat.id,msg.message_id)

# تغییر متن
@bot.message_handler(func=lambda m: cmd_text(m).startswith("خوشامد متن "))
def w_txt(m):
    if is_admin(m.chat.id,m.from_user.id):
        welcome_texts[m.chat.id]=cmd_text(m).replace("خوشامد متن ","",1).strip()
        msg=bot.reply_to(m,"✍️ متن خوشامد ذخیره شد.")
        auto_del(m.chat.id,msg.message_id)

# ثبت عکس
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="ثبت عکس")
def w_photo(m):
    if is_admin(m.chat.id,m.from_user.id) and m.reply_to_message.photo:
        welcome_photos[m.chat.id]=m.reply_to_message.photo[-1].file_id
        msg=bot.reply_to(m,"🖼 عکس خوشامد ذخیره شد.")
        auto_del(m.chat.id,msg.message_id)

# حذف متن / عکس / ریست
@bot.message_handler(func=lambda m: cmd_text(m)=="حذف متن خوشامد")
def del_welcome_text(m):
    if is_admin(m.chat.id,m.from_user.id):
        welcome_texts.pop(m.chat.id, None)
        msg=bot.reply_to(m,"✍️ متن خوشامد حذف شد (بازگشت به پیش‌فرض).")
        auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="حذف عکس خوشامد")
def del_welcome_photo(m):
    if is_admin(m.chat.id,m.from_user.id):
        welcome_photos.pop(m.chat.id, None)
        msg=bot.reply_to(m,"🖼 عکس خوشامد حذف شد.")
        auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="ریست خوشامد")
def reset_welcome(m):
    if is_admin(m.chat.id,m.from_user.id):
        welcome_texts.pop(m.chat.id, None)
        welcome_photos.pop(m.chat.id, None)
        welcome_enabled[m.chat.id] = True
        msg=bot.reply_to(m,"🔄 خوشامد به حالت پیش‌فرض برگشت.")
        auto_del(m.chat.id,msg.message_id)

# لیست تنظیمات خوشامد
@bot.message_handler(func=lambda m: cmd_text(m)=="لیست خوشامد")
def list_welcome(m):
    if is_admin(m.chat.id,m.from_user.id):
        txt = "🎉 تنظیمات خوشامد:\n\n"
        txt += f"✍️ متن: {welcome_texts.get(m.chat.id,'پیش‌فرض')[:40]}\n"
        txt += f"🖼 عکس: {'ذخیره شده' if welcome_photos.get(m.chat.id) else 'ندارد'}\n"
        txt += f"🔘 وضعیت: {'✅ روشن' if welcome_enabled.get(m.chat.id) else '❌ خاموش'}"
        msg=bot.reply_to(m,txt)
        auto_del(m.chat.id,msg.message_id,delay=20)# ========= فونت‌ساز (۱۰ استایل) =========
FONTS = [
    # ۱- Bold انگلیسی
    lambda txt: "".join({"a":"𝗮","b":"𝗯","c":"𝗰","d":"𝗱","e":"𝗲","f":"𝗳","g":"𝗴","h":"𝗵",
                         "i":"𝗶","j":"𝗷","k":"𝗸","l":"𝗹","m":"𝗺","n":"𝗻","o":"𝗼","p":"𝗽",
                         "q":"𝗾","r":"𝗿","s":"𝘀","t":"𝘁","u":"𝘂","v":"𝘃","w":"𝘄","x":"𝘅",
                         "y":"𝘆","z":"𝘇"}.get(ch.lower(),ch) for ch in txt),

    # ۲- Italic انگلیسی
    lambda txt: "".join({"a":"𝑎","b":"𝑏","c":"𝑐","d":"𝑑","e":"𝑒","f":"𝑓","g":"𝑔","h":"ℎ",
                         "i":"𝑖","j":"𝑗","k":"𝑘","l":"𝑙","m":"𝑚","n":"𝑛","o":"𝑜","p":"𝑝",
                         "q":"𝑞","r":"𝑟","s":"𝑠","t":"𝑡","u":"𝑢","v":"𝑣","w":"𝑤","x":"𝑥",
                         "y":"𝑦","z":"𝑧"}.get(ch.lower(),ch) for ch in txt),

    # ۳- Bubble انگلیسی
    lambda txt: "".join({"a":"ⓐ","b":"ⓑ","c":"ⓒ","d":"ⓓ","e":"ⓔ","f":"ⓕ","g":"ⓖ","h":"ⓗ",
                         "i":"ⓘ","j":"ⓙ","k":"ⓚ","l":"ⓛ","m":"ⓜ","n":"ⓝ","o":"ⓞ","p":"ⓟ",
                         "q":"ⓠ","r":"ⓡ","s":"ⓢ","t":"ⓣ","u":"ⓤ","v":"ⓥ","w":"ⓦ","x":"ⓧ",
                         "y":"ⓨ","z":"ⓩ"}.get(ch.lower(),ch) for ch in txt),

    # ۴- Small Caps انگلیسی
    lambda txt: "".join({"a":"ᴀ","b":"ʙ","c":"ᴄ","d":"ᴅ","e":"ᴇ","f":"ғ","g":"ɢ","h":"ʜ",
                         "i":"ɪ","j":"ᴊ","k":"ᴋ","l":"ʟ","m":"ᴍ","n":"ɴ","o":"ᴏ","p":"ᴘ",
                         "q":"ǫ","r":"ʀ","s":"s","t":"ᴛ","u":"ᴜ","v":"ᴠ","w":"ᴡ","x":"x",
                         "y":"ʏ","z":"ᴢ"}.get(ch.lower(),ch) for ch in txt),

    # ۵- Gothic انگلیسی
    lambda txt: "".join({"a":"𝔞","b":"𝔟","c":"𝔠","d":"𝔡","e":"𝔢","f":"𝔣","g":"𝔤","h":"𝔥",
                         "i":"𝔦","j":"𝔧","k":"𝔨","l":"𝔩","m":"𝔪","n":"𝔫","o":"𝔬","p":"𝔭",
                         "q":"𝔮","r":"𝔯","s":"𝔰","t":"𝔱","u":"𝔲","v":"𝔳","w":"𝔴","x":"𝔵",
                         "y":"𝔶","z":"𝔷"}.get(ch.lower(),ch) for ch in txt),

    # ۶- فارسی استایل فانتزی
    lambda txt: "".join({"ا":"ٱ","ب":"بٰ","ت":"تہ","ث":"ثٰ","ج":"جـ","ح":"حہ","خ":"خہ",
                         "د":"دٰ","ذ":"ذٰ","ر":"رٰ","ز":"زٰ","س":"سٰ","ش":"شٰ","ص":"صٰ",
                         "ض":"ضٰ","ط":"طٰ","ظ":"ظٰ","ع":"عہ","غ":"غہ","ف":"فہ","ق":"قٰ",
                         "ک":"ڪ","گ":"گٰ","ل":"لہ","م":"مہ","ن":"نٰ","ه":"ﮬ","و":"ۆ","ی":"ۍ"}.get(ch,ch) for ch in txt),

    # ۷- فارسی استایل عربی
    lambda txt: "".join({"ا":"آ","ب":"ب̍","ت":"تۛ","ث":"ثہ","ج":"ج͠","ح":"حٰٰ","خ":"خ̐",
                         "د":"دُ","ذ":"ذٰ","ر":"ر͜","ز":"زٰ","س":"سہ","ش":"شہ","ص":"صہ",
                         "ض":"ضہ","ط":"طہ","ظ":"ظہ","ع":"عہ","غ":"غہ","ف":"فہ","ق":"ق͠",
                         "ک":"ڪہ","گ":"گہ","ل":"لہ","م":"مہ","ن":"نہ","ه":"ﮬ","و":"و͠","ی":"يہ"}.get(ch,ch) for ch in txt),

    # ۸- فارسی کلاسیک
    lambda txt: "".join({"ا":"اٰ","ب":"بـ","ت":"تـ","ث":"ثـ","ج":"ﮔ","ح":"حـ","خ":"خـ",
                         "د":"دٰ","ذ":"ذٰ","ر":"رٰ","ز":"زٰ","س":"سـ","ش":"شـ","ص":"صـ",
                         "ض":"ضـ","ط":"طـ","ظ":"ظـ","ع":"عـ","غ":"غـ","ف":"فـ","ق":"قـ",
                         "ک":"ڪ","گ":"گـ","ل":"لـ","م":"مـ","ن":"نـ","ه":"هـ","و":"ۅ","ی":"ۍ"}.get(ch,ch) for ch in txt),

    # ۹- فارسی مدرن
    lambda txt: "".join({"ا":"ﺂ","ب":"ﺑ","ت":"ﺗ","ث":"ﺛ","ج":"ﺟ","ح":"ﺣ","خ":"ﺧ",
                         "د":"ﮄ","ذ":"ﮆ","ر":"ﺭ","ز":"ﺯ","س":"ﺳ","ش":"ﺷ","ص":"ﺻ",
                         "ض":"ﺿ","ط":"ﻁ","ظ":"ﻅ","ع":"ﻋ","غ":"ﻏ","ف":"ﻓ","ق":"ﻗ",
                         "ک":"ﮎ","گ":"ﮒ","ل":"ﻟ","م":"ﻣ","ن":"ﻧ","ه":"ﮬ","و":"ۆ","ی":"ﯼ"}.get(ch,ch) for ch in txt),

    # ۱۰- فارسی ترکیبی
    lambda txt: "".join({"ا":"آ","ب":"بہ","ت":"تـ","ث":"ثہ","ج":"جہ","ح":"حہ","خ":"خہ",
                         "د":"دٰ","ذ":"ذہ","ر":"رٰ","ز":"زہ","س":"سہ","ش":"شہ","ص":"صہ",
                         "ض":"ضہ","ط":"طہ","ظ":"ظہ","ع":"عہ","غ":"غہ","ف":"فہ","ق":"قہ",
                         "ک":"کہ","گ":"گہ","ل":"لہ","م":"مہ","ن":"نہ","ه":"ﮬ","و":"ۅ","ی":"یے"}.get(ch,ch) for ch in txt),
]

@bot.message_handler(func=lambda m: cmd_text(m).startswith("فونت "))
def make_fonts(m):
    name = cmd_text(m).replace("فونت ","",1).strip()
    if not name:
        msg = bot.reply_to(m,"❗ اسم رو هم بنویس")
        auto_del(m.chat.id,msg.message_id)
        return
    res = f"🎨 فونت‌های خوشگل برای {name}:\n\n"
    for style in FONTS:
        try: 
            res += style(name) + "\n"
        except: 
            continue
    msg = bot.reply_to(m,res)
    auto_del(m.chat.id,msg.message_id,delay=20)# ========= سیستم اصل =========
origins = {}  # chat_id -> { user_id: اصل }

# ثبت اصل (فقط مدیران/سودو) با ریپلای
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m).startswith("ثبت اصل "))
def set_origin(m):
    if not is_admin(m.chat.id, m.from_user.id): 
        return
    uid = m.reply_to_message.from_user.id
    val = cmd_text(m).replace("ثبت اصل ","",1).strip()
    if not val:
        msg = bot.reply_to(m,"❗ متنی وارد کن.")
    else:
        origins.setdefault(m.chat.id,{})[uid] = val
        msg = bot.reply_to(m,f"✅ اصل برای {m.reply_to_message.from_user.first_name} ثبت شد: {val}")
    auto_del(m.chat.id,msg.message_id,delay=7)

# نمایش اصل (ریپلای روی کاربر)
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="اصل")
def get_origin(m):
    uid = m.reply_to_message.from_user.id
    val = origins.get(m.chat.id,{}).get(uid)
    msg = bot.reply_to(m,f"🧾 اصل: {val}" if val else "ℹ️ اصل ثبت نشده.")
    auto_del(m.chat.id,msg.message_id,delay=7)

# نمایش اصل من (بدون ریپلای)
@bot.message_handler(func=lambda m: cmd_text(m)=="اصل من")
def my_origin(m):
    val = origins.get(m.chat.id,{}).get(m.from_user.id)
    msg = bot.reply_to(m,f"🧾 اصل شما: {val}" if val else "ℹ️ اصل شما ثبت نشده.")
    auto_del(m.chat.id,msg.message_id,delay=7)import random

# ========= جوک و فال =========
jokes = []
fortunes = []

# --- ثبت جوک ---
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m).startswith("ثبت جوک"))
def save_joke(m):
    if m.reply_to_message:
        if m.reply_to_message.text:
            jokes.append({"type":"text","content":m.reply_to_message.text})
        elif m.reply_to_message.photo:
            jokes.append({"type":"photo","file":m.reply_to_message.photo[-1].file_id,"caption":m.reply_to_message.caption or ""})
        msg = bot.reply_to(m,"😂 جوک ذخیره شد.")
    else:
        msg = bot.reply_to(m,"❗ روی پیام جوک ریپلای کن.")
    auto_del(m.chat.id,msg.message_id)

# --- ارسال جوک ---
@bot.message_handler(func=lambda m: cmd_text(m)=="جوک")
def send_joke(m):
    if not jokes:
        return bot.reply_to(m,"❗ هیچ جوکی ذخیره نشده.")
    joke = random.choice(jokes)
    if joke["type"]=="text":
        bot.send_message(m.chat.id, joke["content"])
    else:
        bot.send_photo(m.chat.id, joke["file"], caption=joke["caption"])

# --- ثبت فال ---
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m).startswith("ثبت فال"))
def save_fal(m):
    if m.reply_to_message:
        if m.reply_to_message.text:
            fortunes.append({"type":"text","content":m.reply_to_message.text})
        elif m.reply_to_message.photo:
            fortunes.append({"type":"photo","file":m.reply_to_message.photo[-1].file_id,"caption":m.reply_to_message.caption or ""})
        msg = bot.reply_to(m,"🔮 فال ذخیره شد.")
    else:
        msg = bot.reply_to(m,"❗ روی پیام فال ریپلای کن.")
    auto_del(m.chat.id,msg.message_id)

# --- ارسال فال ---
@bot.message_handler(func=lambda m: cmd_text(m)=="فال")
def send_fal(m):
    if not fortunes:
        return bot.reply_to(m,"❗ هیچ فالی ذخیره نشده.")
    fal = random.choice(fortunes)
    if fal["type"]=="text":
        bot.send_message(m.chat.id, fal["content"])
    else:
        bot.send_photo(m.chat.id, fal["file"], caption=fal["caption"])

# --- لیست جوک‌ها ---
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="لیست جوک‌ها")
def list_jokes(m):
    if not jokes:
        return bot.reply_to(m,"ℹ️ هیچ جوکی ذخیره نشده.")
    txt = "😂 لیست جوک‌ها:\n\n"
    for i,j in enumerate(jokes[-10:],1):
        if j["type"]=="text":
            txt += f"{i}. {j['content'][:30]}...\n"
        else:
            txt += f"{i}. [📸 عکس با کپشن]\n"
    msg = bot.reply_to(m,txt)
    auto_del(m.chat.id,msg.message_id,delay=25)

# --- حذف جوک n ---
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m).startswith("حذف جوک "))
def del_joke(m):
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        if 0 <= idx < len(jokes):
            jokes.pop(idx)
            msg = bot.reply_to(m,"✅ جوک حذف شد.")
        else:
            msg = bot.reply_to(m,"❗ شماره نامعتبر است.")
    except:
        msg = bot.reply_to(m,"❗ دستور درست نیست.")
    auto_del(m.chat.id,msg.message_id,delay=7)

# --- پاکسازی جوک‌ها ---
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="پاکسازی جوک‌ها")
def clear_jokes(m):
    jokes.clear()
    msg = bot.reply_to(m,"🗑 همه جوک‌ها پاک شدند.")
    auto_del(m.chat.id,msg.message_id,delay=7)

# --- لیست فال‌ها ---
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="لیست فال‌ها")
def list_fals(m):
    if not fortunes:
        return bot.reply_to(m,"ℹ️ هیچ فالی ذخیره نشده.")
    txt = "🔮 لیست فال‌ها:\n\n"
    for i,f in enumerate(fortunes[-10:],1):
        if f["type"]=="text":
            txt += f"{i}. {f['content'][:30]}...\n"
        else:
            txt += f"{i}. [📸 عکس با کپشن]\n"
    msg = bot.reply_to(m,txt)
    auto_del(m.chat.id,msg.message_id,delay=25)

# --- حذف فال n ---
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m).startswith("حذف فال "))
def del_fal(m):
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        if 0 <= idx < len(fortunes):
            fortunes.pop(idx)
            msg = bot.reply_to(m,"✅ فال حذف شد.")
        else:
            msg = bot.reply_to(m,"❗ شماره نامعتبر است.")
    except:
        msg = bot.reply_to(m,"❗ دستور درست نیست.")
    auto_del(m.chat.id,msg.message_id,delay=7)

# --- پاکسازی فال‌ها ---
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="پاکسازی فال‌ها")
def clear_fals(m):
    fortunes.clear()
    msg = bot.reply_to(m,"🗑 همه فال‌ها پاک شدند.")
    auto_del(m.chat.id,msg.message_id,delay=7)# ========= خوشامد =========
welcome_enabled, welcome_texts, welcome_photos = {}, {}, {}
DEFAULT_WELCOME = "• سلام {name} به گروه {title} خوش آمدید 🌻"

@bot.message_handler(content_types=['new_chat_members'])
def welcome(m):
    for u in m.new_chat_members:
        if not welcome_enabled.get(m.chat.id): 
            continue
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

# --- روشن/خاموش ---
@bot.message_handler(func=lambda m: cmd_text(m)=="خوشامد روشن")
def w_on(m):
    if is_admin(m.chat.id,m.from_user.id):
        welcome_enabled[m.chat.id]=True
        msg = bot.reply_to(m,"✅ خوشامد روشن شد.")
        auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="خوشامد خاموش")
def w_off(m):
    if is_admin(m.chat.id,m.from_user.id):
        welcome_enabled[m.chat.id]=False
        msg = bot.reply_to(m,"❌ خوشامد خاموش شد.")
        auto_del(m.chat.id,msg.message_id)

# --- تغییر متن ---
@bot.message_handler(func=lambda m: cmd_text(m).startswith("خوشامد متن"))
def w_txt(m):
    if is_admin(m.chat.id,m.from_user.id):
        welcome_texts[m.chat.id]=cmd_text(m).replace("خوشامد متن","",1).strip()
        msg = bot.reply_to(m,"✍️ متن خوشامد ذخیره شد.")
        auto_del(m.chat.id,msg.message_id)

# --- ثبت عکس (ریپلای) ---
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="ثبت عکس")
def w_photo(m):
    if is_admin(m.chat.id,m.from_user.id) and m.reply_to_message.photo:
        welcome_photos[m.chat.id]=m.reply_to_message.photo[-1].file_id
        msg = bot.reply_to(m,"🖼 عکس خوشامد ذخیره شد.")
        auto_del(m.chat.id,msg.message_id)

# --- حذف متن خوشامد ---
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="حذف متن خوشامد")
def del_welcome_text(m):
    welcome_texts.pop(m.chat.id, None)
    msg = bot.reply_to(m,"✍️ متن خوشامد حذف شد (بازگشت به پیش‌فرض).")
    auto_del(m.chat.id,msg.message_id)

# --- حذف عکس خوشامد ---
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="حذف عکس خوشامد")
def del_welcome_photo(m):
    welcome_photos.pop(m.chat.id, None)
    msg = bot.reply_to(m,"🖼 عکس خوشامد حذف شد.")
    auto_del(m.chat.id,msg.message_id)

# --- ریست خوشامد ---
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="ریست خوشامد")
def reset_welcome(m):
    welcome_texts.pop(m.chat.id, None)
    welcome_photos.pop(m.chat.id, None)
    welcome_enabled[m.chat.id] = True
    msg = bot.reply_to(m,"🔄 خوشامد به حالت پیش‌فرض برگشت.")
    auto_del(m.chat.id,msg.message_id)

# --- لیست خوشامد ---
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="لیست خوشامد")
def list_welcome(m):
    txt = "🎉 تنظیمات خوشامدگویی:\n\n"
    if welcome_texts.get(m.chat.id):
        txt += f"✍️ متن: {welcome_texts[m.chat.id][:50]}...\n"
    else:
        txt += "✍️ متن: پیش‌فرض\n"

    if welcome_photos.get(m.chat.id):
        txt += "🖼 عکس: ذخیره شده\n"
    else:
        txt += "🖼 عکس: پیش‌فرض (ندارد)\n"

    status = "✅ روشن" if welcome_enabled.get(m.chat.id) else "❌ خاموش"
    txt += f"\n🔘 وضعیت: {status}"
    msg = bot.reply_to(m, txt)
    auto_del(m.chat.id, msg.message_id, delay=15)# ========= قفل‌ها =========
locks={k:{} for k in [
    "links","stickers","bots","tabchi","group","photo","video","gif","file","music","voice","forward"
]}
LOCK_MAP={
    "لینک":"links","استیکر":"stickers","ربات":"bots","تبچی":"tabchi","گروه":"group",
    "عکس":"photo","ویدیو":"video","گیف":"gif","فایل":"file","موزیک":"music","ویس":"voice","فوروارد":"forward"
}

@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل ") or cmd_text(m).startswith("باز کردن "))
def toggle_lock(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    t=cmd_text(m); enable=t.startswith("قفل ")
    name=t.replace("قفل ","",1).replace("باز کردن ","",1).strip()
    key=LOCK_MAP.get(name)
    if not key: return
    if key=="group":
        try:
            bot.set_chat_permissions(m.chat.id,types.ChatPermissions(can_send_messages=not enable))
        except:
            msg = bot.reply_to(m,"❗ نیاز به دسترسی محدودسازی")
            auto_del(m.chat.id,msg.message_id)
            return
    locks[key][m.chat.id]=enable
    msg = bot.reply_to(m,f"{'🔒' if enable else '🔓'} {name} {'فعال شد' if enable else 'آزاد شد'}")
    auto_del(m.chat.id,msg.message_id)

# ========= پنل قفل‌ها =========
@bot.message_handler(func=lambda m: cmd_text(m)=="پنل")
def locks_panel(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for name,key in LOCK_MAP.items():
        status = "🔒" if locks[key].get(m.chat.id) else "🔓"
        btns.append(types.InlineKeyboardButton(f"{status} {name}",callback_data=f"toggle:{key}:{m.chat.id}"))
    kb.add(*btns)
    kb.add(types.InlineKeyboardButton("❌ بستن", callback_data=f"close:{m.chat.id}"))
    msg = bot.reply_to(m,"🛠 پنل مدیریت قفل‌ها:",reply_markup=kb)
    auto_del(m.chat.id,msg.message_id,delay=30)

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle:"))
def cb_toggle(call):
    _,key,chat_id = call.data.split(":")
    chat_id=int(chat_id)
    uid=call.from_user.id
    if not is_admin(chat_id,uid): 
        return bot.answer_callback_query(call.id,"❌ فقط مدیران می‌توانند تغییر دهند.",show_alert=True)
    current=locks[key].get(chat_id,False)
    locks[key][chat_id]=not current
    bot.answer_callback_query(call.id,f"{'فعال' if locks[key][chat_id] else 'غیرفعال'} شد ✅")

    kb = types.InlineKeyboardMarkup(row_width=2)
    btns=[]
    for name,k in LOCK_MAP.items():
        st="🔒" if locks[k].get(chat_id) else "🔓"
        btns.append(types.InlineKeyboardButton(f"{st} {name}",callback_data=f"toggle:{k}:{chat_id}"))
    kb.add(*btns)
    kb.add(types.InlineKeyboardButton("❌ بستن", callback_data=f"close:{chat_id}"))
    bot.edit_message_reply_markup(chat_id,call.message.message_id,reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("close:"))
def cb_close(call):
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass# ========= بن / حذف بن =========
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="بن")
def ban_user(m):
    if is_admin(m.chat.id,m.from_user.id):
        try:
            bot.ban_chat_member(m.chat.id,m.reply_to_message.from_user.id)
            msg = bot.reply_to(m,"🚫 کاربر بن شد.")
        except:
            msg = bot.reply_to(m,"❗ خطا در بن.")
        auto_del(m.chat.id,msg.message_id,delay=7)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف بن")
def unban_user(m):
    if is_admin(m.chat.id,m.from_user.id):
        try:
            bot.unban_chat_member(m.chat.id,m.reply_to_message.from_user.id)
            msg = bot.reply_to(m,"✅ بن حذف شد.")
        except:
            msg = bot.reply_to(m,"❗ خطا در حذف بن.")
        auto_del(m.chat.id,msg.message_id,delay=7)


# ========= سکوت / حذف سکوت =========
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="سکوت")
def mute_user(m):
    if is_admin(m.chat.id,m.from_user.id):
        try:
            bot.restrict_chat_member(m.chat.id,m.reply_to_message.from_user.id,can_send_messages=False)
            msg = bot.reply_to(m,"🔕 کاربر در حالت سکوت قرار گرفت.")
        except:
            msg = bot.reply_to(m,"❗ خطا در سکوت.")
        auto_del(m.chat.id,msg.message_id,delay=7)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف سکوت")
def unmute_user(m):
    if is_admin(m.chat.id,m.from_user.id):
        try:
            bot.restrict_chat_member(
                m.chat.id,m.reply_to_message.from_user.id,
                can_send_messages=True,can_send_media_messages=True,
                can_send_other_messages=True,can_add_web_page_previews=True
            )
            msg = bot.reply_to(m,"🔊 سکوت برداشته شد.")
        except:
            msg = bot.reply_to(m,"❗ خطا در حذف سکوت.")
        auto_del(m.chat.id,msg.message_id,delay=7)


# ========= اخطار =========
warnings={}; MAX_WARNINGS=3

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="اخطار")
def warn_user(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    warnings.setdefault(m.chat.id,{})
    warnings[m.chat.id][uid] = warnings[m.chat.id].get(uid,0)+1
    c = warnings[m.chat.id][uid]
    if c >= MAX_WARNINGS:
        try:
            bot.ban_chat_member(m.chat.id,uid)
            msg = bot.reply_to(m,"🚫 کاربر با ۳ اخطار بن شد.")
            warnings[m.chat.id][uid] = 0
        except:
            msg = bot.reply_to(m,"❗ خطا در بن.")
    else:
        msg = bot.reply_to(m,f"⚠️ اخطار {c}/{MAX_WARNINGS}")
    auto_del(m.chat.id,msg.message_id,delay=7)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف اخطار")
def reset_warn(m):
    if is_admin(m.chat.id,m.from_user.id):
        uid = m.reply_to_message.from_user.id
        warnings.get(m.chat.id,{}).pop(uid,None)
        msg = bot.reply_to(m,"✅ اخطارها حذف شد.")
        auto_del(m.chat.id,msg.message_id,delay=7)


# ========= مدیر / حذف مدیر =========
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="مدیر")
def promote(m):
    if is_admin(m.chat.id,m.from_user.id):
        try:
            bot.promote_chat_member(
                m.chat.id,m.reply_to_message.from_user.id,
                can_manage_chat=True,can_delete_messages=True,
                can_restrict_members=True,can_pin_messages=True,
                can_invite_users=True,can_manage_video_chats=True
            )
            msg = bot.reply_to(m,"👑 کاربر مدیر شد.")
        except:
            msg = bot.reply_to(m,"❗ خطا در ارتقا.")
        auto_del(m.chat.id,msg.message_id,delay=7)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف مدیر")
def demote(m):
    if is_admin(m.chat.id,m.from_user.id):
        try:
            bot.promote_chat_member(
                m.chat.id,m.reply_to_message.from_user.id,
                can_manage_chat=False,can_delete_messages=False,
                can_restrict_members=False,can_pin_messages=False,
                can_invite_users=False,can_manage_video_chats=False
            )
            msg = bot.reply_to(m,"❌ مدیر حذف شد.")
        except:
            msg = bot.reply_to(m,"❗ خطا در حذف مدیر.")
        auto_del(m.chat.id,msg.message_id,delay=7)# ========= سیستم اصل =========
origins = {}  # chat_id -> { user_id: اصل }

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m).startswith("ثبت اصل "))
def set_origin(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    val = cmd_text(m).replace("ثبت اصل ","",1).strip()
    if not val:
        msg = bot.reply_to(m,"❗ متنی وارد کن.")
    else:
        origins.setdefault(m.chat.id,{})[uid] = val
        msg = bot.reply_to(m,f"✅ اصل ثبت شد: {val}")
    auto_del(m.chat.id,msg.message_id,delay=7)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="اصل")
def get_origin(m):
    uid = m.reply_to_message.from_user.id
    val = origins.get(m.chat.id,{}).get(uid)
    msg = bot.reply_to(m,f"🧾 اصل: {val}" if val else "ℹ️ اصل ثبت نشده.")
    auto_del(m.chat.id,msg.message_id,delay=7)

@bot.message_handler(func=lambda m: cmd_text(m)=="اصل من")
def my_origin(m):
    val = origins.get(m.chat.id,{}).get(m.from_user.id)
    msg = bot.reply_to(m,f"🧾 اصل شما: {val}" if val else "ℹ️ اصل شما ثبت نشده.")
    auto_del(m.chat.id,msg.message_id,delay=7)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف اصل")
def del_origin(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    if uid in origins.get(m.chat.id,{}):
        origins[m.chat.id].pop(uid)
        msg = bot.reply_to(m,"🗑 اصل حذف شد.")
    else:
        msg = bot.reply_to(m,"ℹ️ اصل ثبت نشده بود.")
    auto_del(m.chat.id,msg.message_id,delay=7)# ========= جوک و فال =========
import random

jokes = []       # [{"type":"text","content":"..."}, {"type":"photo","file":"id","caption":"..."}]
fortunes = []    # مشابه بالا برای فال

# --- ثبت جوک ---
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="ثبت جوک", content_types=['text','photo'])
def save_joke(m):
    if m.reply_to_message:
        if m.reply_to_message.text:
            jokes.append({"type":"text","content":m.reply_to_message.text})
        elif m.reply_to_message.photo:
            jokes.append({"type":"photo","file":m.reply_to_message.photo[-1].file_id,"caption":m.reply_to_message.caption or ""})
        msg = bot.reply_to(m,"😂 جوک ذخیره شد.")
    else:
        msg = bot.reply_to(m,"❗ روی پیام جوک ریپلای کن.")
    auto_del(m.chat.id,msg.message_id)

# --- ارسال جوک ---
@bot.message_handler(func=lambda m: cmd_text(m)=="جوک")
def send_joke(m):
    if not jokes:
        return bot.reply_to(m,"❗ هیچ جوکی ذخیره نشده.")
    joke = random.choice(jokes)
    if joke["type"]=="text":
        bot.send_message(m.chat.id, joke["content"])
    else:
        bot.send_photo(m.chat.id, joke["file"], caption=joke["caption"])

# --- حذف جوک ---
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and m.reply_to_message and cmd_text(m)=="حذف جوک")
def del_joke(m):
    txt = m.reply_to_message.text or m.reply_to_message.caption
    for i,j in enumerate(jokes):
        if j["type"]=="text" and j["content"]==txt:
            jokes.pop(i); msg = bot.reply_to(m,"🗑 جوک حذف شد."); break
        elif j["type"]=="photo" and j.get("caption")==txt:
            jokes.pop(i); msg = bot.reply_to(m,"🗑 جوک حذف شد."); break
    else:
        msg = bot.reply_to(m,"❗ این جوک پیدا نشد.")
    auto_del(m.chat.id,msg.message_id)

# --- لیست جوک‌ها ---
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="لیست جوک‌ها")
def list_jokes(m):
    if not jokes: return bot.reply_to(m,"ℹ️ هیچ جوکی ذخیره نشده.")
    txt="😂 لیست جوک‌ها:\n\n"
    for i,j in enumerate(jokes[-10:],1):
        txt+=f"{i}. {(j['content'][:25]+'...') if j['type']=='text' else '[📸 عکس]'}\n"
    msg=bot.reply_to(m,txt); auto_del(m.chat.id,msg.message_id,delay=20)

# --- پاکسازی جوک‌ها ---
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="پاکسازی جوک‌ها")
def clear_jokes(m):
    jokes.clear()
    msg=bot.reply_to(m,"🧹 همه جوک‌ها پاک شدند.")
    auto_del(m.chat.id,msg.message_id)


# --- ثبت فال ---
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="ثبت فال", content_types=['text','photo'])
def save_fal(m):
    if m.reply_to_message:
        if m.reply_to_message.text:
            fortunes.append({"type":"text","content":m.reply_to_message.text})
        elif m.reply_to_message.photo:
            fortunes.append({"type":"photo","file":m.reply_to_message.photo[-1].file_id,"caption":m.reply_to_message.caption or ""})
        msg = bot.reply_to(m,"🔮 فال ذخیره شد.")
    else:
        msg = bot.reply_to(m,"❗ روی پیام فال ریپلای کن.")
    auto_del(m.chat.id,msg.message_id)

# --- ارسال فال ---
@bot.message_handler(func=lambda m: cmd_text(m)=="فال")
def send_fal(m):
    if not fortunes:
        return bot.reply_to(m,"❗ هیچ فالی ذخیره نشده.")
    fal = random.choice(fortunes)
    if fal["type"]=="text":
        bot.send_message(m.chat.id, fal["content"])
    else:
        bot.send_photo(m.chat.id, fal["file"], caption=fal["caption"])

# --- حذف فال ---
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and m.reply_to_message and cmd_text(m)=="حذف فال")
def del_fal(m):
    txt = m.reply_to_message.text or m.reply_to_message.caption
    for i,f in enumerate(fortunes):
        if f["type"]=="text" and f["content"]==txt:
            fortunes.pop(i); msg = bot.reply_to(m,"🗑 فال حذف شد."); break
        elif f["type"]=="photo" and f.get("caption")==txt:
            fortunes.pop(i); msg = bot.reply_to(m,"🗑 فال حذف شد."); break
    else:
        msg = bot.reply_to(m,"❗ این فال پیدا نشد.")
    auto_del(m.chat.id,msg.message_id)

# --- لیست فال‌ها ---
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="لیست فال‌ها")
def list_fals(m):
    if not fortunes: return bot.reply_to(m,"ℹ️ هیچ فالی ذخیره نشده.")
    txt="🔮 لیست فال‌ها:\n\n"
    for i,f in enumerate(fortunes[-10:],1):
        txt+=f"{i}. {(f['content'][:25]+'...') if f['type']=='text' else '[📸 عکس]'}\n"
    msg=bot.reply_to(m,txt); auto_del(m.chat.id,msg.message_id,delay=20)

# --- پاکسازی فال‌ها ---
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="پاکسازی فال‌ها")
def clear_fals(m):
    fortunes.clear()
    msg=bot.reply_to(m,"🧹 همه فال‌ها پاک شدند.")
    auto_del(m.chat.id,msg.message_id)# 📋 لیست مدیران گروه
@bot.message_handler(func=lambda m: cmd_text(m)=="لیست مدیران گروه")
def admins_list(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        admins = bot.get_chat_administrators(m.chat.id)
        names = [f"▪️ {a.user.first_name} — <code>{a.user.id}</code>" for a in admins]
        txt = "👑 لیست مدیران گروه:\n\n" + "\n".join(names)
    except:
        txt = "❗ نتوانستم لیست مدیران را بگیرم."
    msg = bot.reply_to(m, txt)
    auto_del(m.chat.id, msg.message_id, delay=20)# 📌 پن (سنجاق پیامِ ریپلای‌شده)
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="پن")
def pin_msg(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.pin_chat_message(m.chat.id, m.reply_to_message.message_id, disable_notification=True)
        msg = bot.reply_to(m, "📌 پیام سنجاق شد.")
    except:
        msg = bot.reply_to(m, "❗ نتوانستم سنجاق کنم. (ربات باید ادمین باشد)")
    auto_del(m.chat.id, msg.message_id)

# ❌ حذف پن (برداشتن سنجاق فعلی)
@bot.message_handler(func=lambda m: cmd_text(m)=="حذف پن")
def unpin_msg(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.unpin_chat_message(m.chat.id)
        msg = bot.reply_to(m, "❌ سنجاق برداشته شد.")
    except:
        msg = bot.reply_to(m, "❗ سنجاقی برای برداشتن پیدا نشد.")
    auto_del(m.chat.id, msg.message_id)HELP_TEXT_ADMIN = """
📖 دستورات مدیران:

⏰ ساعت | 🆔 ایدی | 📊 آمار | 📎 لینک
🎉 خوشامد روشن / خاموش
✍️ خوشامد متن [متن]  |  🖼 ثبت عکس (ریپلای روی عکس)
🔒 قفل/بازکردن: لینک، استیکر، ربات، تبچی، گروه، عکس، ویدیو، گیف، فایل، موزیک، ویس، فوروارد
🚫 بن / ✅ حذف بن   (ریپلای)
🔕 سکوت / 🔊 حذف سکوت (ریپلای)
⚠️ اخطار / حذف اخطار (ریپلای)
👑 مدیر / ❌ حذف مدیر (ریپلای)
📌 پن / ❌ حذف پن
🏷 اصل / اصل من / ثبت اصل (ریپلای)
😂 جوک / 🔮 فال / ثبت جوک (ریپلای) / ثبت فال (ریپلای)
🧹 پاکسازی  |  🧹 حذف [عدد]
📋 لیست مدیران گروه
"""

@bot.message_handler(func=lambda m: cmd_text(m)=="راهنما")
def show_help_for_admins(m):
    # فقط مدیران گروه‌ها؛ در پی‌وی یا برای کاربر عادی پاسخی نده
    if m.chat.type in ("group","supergroup") and is_admin(m.chat.id, m.from_user.id):
        msg = bot.reply_to(m, HELP_TEXT_ADMIN)
        auto_del(m.chat.id, msg.message_id, delay=25)# 🧾 حذف اصل (با ریپلای روی کاربر)
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف اصل")
def del_origin(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    ok = origins.get(m.chat.id, {}).pop(uid, None)
    msg = bot.reply_to(m, "🗑 اصل حذف شد." if ok is not None else "ℹ️ اصلی ثبت نشده بود.")
    auto_del(m.chat.id, msg.message_id)# ========== لیست جوک‌ها ==========
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="لیست جوک‌ها")
def list_jokes(m):
    if not jokes:
        return bot.reply_to(m,"ℹ️ هیچ جوکی ذخیره نشده.")
    txt = "😂 لیست جوک‌ها (حداکثر ۲۰ مورد آخر):\n\n"
    start = max(0, len(jokes)-20)
    for i, j in enumerate(jokes[start:], start=1):
        if j["type"]=="text":
            preview = (j["content"][:40] + "…") if len(j["content"])>40 else j["content"]
        else:
            preview = "[📸 عکس]" + (f" — {j['caption'][:30]}…" if j.get("caption") else "")
        txt += f"{i}. {preview}\n"
    msg = bot.reply_to(m, txt)
    auto_del(m.chat.id, msg.message_id, delay=30)

# ========== حذف جوک با شماره ==========
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m).startswith("حذف جوک "))
def del_joke_by_index(m):
    parts = cmd_text(m).split()
    if len(parts) < 3:
        msg = bot.reply_to(m, "❗ فرمت درست: «حذف جوک 3»")
        return auto_del(m.chat.id, msg.message_id)
    try:
        idx = int(parts[2])
        start = max(0, len(jokes)-20)
        real_idx = start + idx - 1
        if 0 <= real_idx < len(jokes):
            jokes.pop(real_idx)
            msg = bot.reply_to(m, "✅ جوک حذف شد.")
        else:
            msg = bot.reply_to(m, "❗ شماره نامعتبر است.")
    except:
        msg = bot.reply_to(m, "❗ فقط عدد بزن. مثال: حذف جوک 2")
    auto_del(m.chat.id, msg.message_id)

# ========== حذف جوک با ریپلای (بر اساس تطبیق محتوا) ==========
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and m.reply_to_message and cmd_text(m)=="حذف جوک")
def del_joke_by_reply(m):
    target = m.reply_to_message
    removed = False
    if target.text:
        # حذف اولین جوکی که متنش دقیقاً همین باشد
        for i,j in enumerate(jokes):
            if j["type"]=="text" and j["content"]==target.text:
                jokes.pop(i); removed=True; break
    elif target.photo:
        fid = target.photo[-1].file_id
        for i,j in enumerate(jokes):
            if j["type"]=="photo" and j.get("file")==fid:
                jokes.pop(i); removed=True; break
    msg = bot.reply_to(m, "✅ جوک حذف شد." if removed else "ℹ️ جوک مطابق پیدا نشد.")
    auto_del(m.chat.id, msg.message_id)

# ========== لیست فال‌ها ==========
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="لیست فال‌ها")
def list_fals(m):
    if not fortunes:
        return bot.reply_to(m,"ℹ️ هیچ فالی ذخیره نشده.")
    txt = "🔮 لیست فال‌ها (حداکثر ۲۰ مورد آخر):\n\n"
    start = max(0, len(fortunes)-20)
    for i, f in enumerate(fortunes[start:], start=1):
        if f["type"]=="text":
            preview = (f["content"][:40] + "…") if len(f["content"])>40 else f["content"]
        else:
            preview = "[📸 عکس]" + (f" — {f['caption'][:30]}…" if f.get("caption") else "")
        txt += f"{i}. {preview}\n"
    msg = bot.reply_to(m, txt)
    auto_del(m.chat.id, msg.message_id, delay=30)

# ========== حذف فال با شماره ==========
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m).startswith("حذف فال "))
def del_fal_by_index(m):
    parts = cmd_text(m).split()
    if len(parts) < 3:
        msg = bot.reply_to(m, "❗ فرمت درست: «حذف فال 3»")
        return auto_del(m.chat.id, msg.message_id)
    try:
        idx = int(parts[2])
        start = max(0, len(fortunes)-20)
        real_idx = start + idx - 1
        if 0 <= real_idx < len(fortunes):
            fortunes.pop(real_idx)
            msg = bot.reply_to(m, "✅ فال حذف شد.")
        else:
            msg = bot.reply_to(m, "❗ شماره نامعتبر است.")
    except:
        msg = bot.reply_to(m, "❗ فقط عدد بزن. مثال: حذف فال 2")
    auto_del(m.chat.id, msg.message_id)

# ========== حذف فال با ریپلای (بر اساس تطبیق محتوا) ==========
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and m.reply_to_message and cmd_text(m)=="حذف فال")
def del_fal_by_reply(m):
    target = m.reply_to_message
    removed = False
    if target.text:
        for i,f in enumerate(fortunes):
            if f["type"]=="text" and f["content"]==target.text:
                fortunes.pop(i); removed=True; break
    elif target.photo:
        fid = target.photo[-1].file_id
        for i,f in enumerate(fortunes):
            if f["type"]=="photo" and f.get("file")==fid:
                fortunes.pop(i); removed=True; break
    msg = bot.reply_to(m, "✅ فال حذف شد." if removed else "ℹ️ فال مطابق پیدا نشد.")
    auto_del(m.chat.id, msg.message_id)# -*- coding: utf-8 -*-
import telebot
from telebot import types
import os

# ================== تنظیمات ==================
TOKEN = os.environ.get("BOT_TOKEN")  # توکن ربات از Config Vars یا مستقیم بذار
SUPPORT_ID = "NOORI_NOOR"            # آیدی پشتیبانی

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ========= استارت برای ممبر (پنل ساده) =========
@bot.message_handler(commands=['start'])
def start_cmd(m):
    if m.chat.type != "private":
        return  # فقط توی پیوی جواب بده

    kb = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("➕ افزودن ربات به گروه", url=f"https://t.me/{bot.get_me().username}?startgroup=new")
    btn2 = types.InlineKeyboardButton("📞 پشتیبانی", url=f"https://t.me/{SUPPORT_ID}")
    kb.add(btn1, btn2)

    txt = (
        "👋 سلام!\n\n"
        "من یک ربات مدیریت گروه هستم 🤖\n\n"
        "📌 کارهایی که می‌کنم:\n"
        "• مدیریت قفل‌ها (لینک، استیکر، فایل و ...)\n"
        "• خوشامدگویی خودکار و تنظیم متن/عکس\n"
        "• اخطار، سکوت و بن اعضا\n"
        "• ثبت و نمایش اصل اعضا\n"
        "• ارسال و مدیریت جوک و فال\n"
        "• ابزارهای مدیران مثل لیست مدیران، پن، پاکسازی و ...\n\n"
        "➕ برای استفاده من رو به گروهت اضافه کن.\n"
        "📞 در صورت نیاز با پشتیبانی در تماس باش."
    )

    bot.send_message(m.chat.id, txt, reply_markup=kb)

# ========= اجرای ربات =========
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True, timeout=30)
