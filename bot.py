# -*- coding: utf-8 -*-
import telebot, os, threading, time
from datetime import datetime
import pytz
from telebot import types

# ================== تنظیمات اولیه ==================
TOKEN   = os.environ.get("BOT_TOKEN")   # توکن ربات از Config Vars
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))  # آیدی سودو اصلی
SUPPORT_ID = "NOORI_NOOR"  # آیدی پشتیبانی (می‌تونی تغییر بدی)

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ========= سودو / ادمین =========
sudo_ids = {SUDO_ID}

def is_sudo(uid):
    return uid in sudo_ids

def is_admin(chat_id, user_id):
    if is_sudo(user_id): 
        return True
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator","creator")
    except:
        return False

def cmd_text(m):
    """برگردوندن متن پیام یا کپشن"""
    return (getattr(m,"text",None) or getattr(m,"caption",None) or "").strip()

# ========= حذف خودکار پیام‌ها =========
def auto_del(chat_id, msg_id, delay=7):
    def _():
        time.sleep(delay)
        try: bot.delete_message(chat_id,msg_id)
        except: pass
    threading.Thread(target=_).start()

# ========= دستورات عمومی (شروع پایه) =========

# ⏰ ساعت
@bot.message_handler(func=lambda m: cmd_text(m)=="ساعت")
def time_cmd(m):
    now_utc = datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_teh = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    msg = bot.reply_to(m, f"⏰ ساعت UTC: {now_utc}\n⏰ ساعت تهران: {now_teh}")
    auto_del(m.chat.id,msg.message_id,delay=7)

# 🆔 ایدی
@bot.message_handler(func=lambda m: cmd_text(m)=="ایدی")
def id_cmd(m):
    try:
        photos = bot.get_user_profile_photos(m.from_user.id, limit=1)
        caption = f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>"
        if photos.total_count > 0:
            msg = bot.send_photo(m.chat.id, photos.photos[0][-1].file_id, caption=caption)
        else:
            msg = bot.reply_to(m, caption)
    except:
        msg = bot.reply_to(m, f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>")
    auto_del(m.chat.id, msg.message_id, delay=7)# ========= فونت‌ساز (۱۰ استایل) =========
FONTS = [
    # انگلیسی – Bold
    lambda txt: "".join({"a":"𝗮","b":"𝗯","c":"𝗰","d":"𝗱","e":"𝗲","f":"𝗳","g":"𝗴","h":"𝗵",
                         "i":"𝗶","j":"𝗷","k":"𝗸","l":"𝗹","m":"𝗺","n":"𝗻","o":"𝗼","p":"𝗽",
                         "q":"𝗾","r":"𝗿","s":"𝘀","t":"𝘁","u":"𝘂","v":"𝘃","w":"𝘄","x":"𝘅",
                         "y":"𝘆","z":"𝘇"}.get(ch.lower(),ch) for ch in txt),

    # انگلیسی – Italic
    lambda txt: "".join({"a":"𝑎","b":"𝑏","c":"𝑐","d":"𝑑","e":"𝑒","f":"𝑓","g":"𝑔","h":"ℎ",
                         "i":"𝑖","j":"𝑗","k":"𝑘","l":"𝑙","m":"𝑚","n":"𝑛","o":"𝑜","p":"𝑝",
                         "q":"𝑞","r":"𝑟","s":"𝑠","t":"𝑡","u":"𝑢","v":"𝑣","w":"𝑤","x":"𝑥",
                         "y":"𝑦","z":"𝑧"}.get(ch.lower(),ch) for ch in txt),

    # انگلیسی – Bubble
    lambda txt: "".join({"a":"ⓐ","b":"ⓑ","c":"ⓒ","d":"ⓓ","e":"ⓔ","f":"ⓕ","g":"ⓖ","h":"ⓗ",
                         "i":"ⓘ","j":"ⓙ","k":"ⓚ","l":"ⓛ","m":"ⓜ","n":"ⓝ","o":"ⓞ","p":"ⓟ",
                         "q":"ⓠ","r":"ⓡ","s":"ⓢ","t":"ⓣ","u":"ⓤ","v":"ⓥ","w":"ⓦ","x":"ⓧ",
                         "y":"ⓨ","z":"ⓩ"}.get(ch.lower(),ch) for ch in txt),

    # انگلیسی – Small Caps
    lambda txt: "".join({"a":"ᴀ","b":"ʙ","c":"ᴄ","d":"ᴅ","e":"ᴇ","f":"ғ","g":"ɢ","h":"ʜ",
                         "i":"ɪ","j":"ᴊ","k":"ᴋ","l":"ʟ","m":"ᴍ","n":"ɴ","o":"ᴏ","p":"ᴘ",
                         "q":"ǫ","r":"ʀ","s":"s","t":"ᴛ","u":"ᴜ","v":"ᴠ","w":"ᴡ","x":"x",
                         "y":"ʏ","z":"ᴢ"}.get(ch.lower(),ch) for ch in txt),

    # انگلیسی – Gothic
    lambda txt: "".join({"a":"𝔞","b":"𝔟","c":"𝔠","d":"𝔡","e":"𝔢","f":"𝔣","g":"𝔤","h":"𝔥",
                         "i":"𝔦","j":"𝔧","k":"𝔨","l":"𝔩","m":"𝔪","n":"𝔫","o":"𝔬","p":"𝔭",
                         "q":"𝔮","r":"𝔯","s":"𝔰","t":"𝔱","u":"𝔲","v":"𝔳","w":"𝔴","x":"𝔵",
                         "y":"𝔶","z":"𝔷"}.get(ch.lower(),ch) for ch in txt),

    # فارسی – استایل ۱
    lambda txt: "".join({"ا":"ٱ","ب":"بٰ","ت":"تہ","ث":"ثٰ","ج":"جـ","ح":"حہ","خ":"خہ",
                         "د":"دٰ","ذ":"ذٰ","ر":"رٰ","ز":"زٰ","س":"سٰ","ش":"شٰ","ص":"صٰ",
                         "ض":"ضٰ","ط":"طٰ","ظ":"ظٰ","ع":"عہ","غ":"غہ","ف":"فہ","ق":"قٰ",
                         "ک":"ڪ","گ":"گٰ","ل":"لہ","م":"مہ","ن":"نٰ","ه":"ﮬ","و":"ۆ","ی":"ۍ"}.get(ch,ch) for ch in txt),

    # فارسی – استایل ۲
    lambda txt: "".join({"ا":"آ","ب":"ب̍","ت":"تۛ","ث":"ثہ","ج":"ج͠","ح":"حٰٰ","خ":"خ̐",
                         "د":"دُ","ذ":"ذٰ","ر":"ر͜","ز":"زٰ","س":"سہ","ش":"شہ","ص":"صہ",
                         "ض":"ضہ","ط":"طہ","ظ":"ظہ","ع":"عہ","غ":"غہ","ف":"فہ","ق":"ق͠",
                         "ک":"ڪہ","گ":"گہ","ل":"لہ","م":"مہ","ن":"نہ","ه":"ﮬ","و":"و͠",
                         "ی":"يہ"}.get(ch,ch) for ch in txt),

    # فارسی – استایل ۳ (کلاسیک)
    lambda txt: "".join({"ا":"اٰ","ب":"بـ","ت":"تـ","ث":"ثـ","ج":"ﮔ","ح":"حـ","خ":"خـ",
                         "د":"دٰ","ذ":"ذٰ","ر":"رٰ","ز":"زٰ","س":"سـ","ش":"شـ","ص":"صـ",
                         "ض":"ضـ","ط":"طـ","ظ":"ظـ","ع":"عـ","غ":"غـ","ف":"فـ","ق":"قـ",
                         "ک":"ڪ","گ":"گـ","ل":"لـ","م":"مـ","ن":"نـ","ه":"هـ","و":"ۅ","ی":"ۍ"}.get(ch,ch) for ch in txt),

    # فارسی – استایل ۴ (فانتزی)
    lambda txt: "".join({"ا":"ﺂ","ب":"ﺑ","ت":"ﺗ","ث":"ﺛ","ج":"ﺟ","ح":"ﺣ","خ":"ﺧ",
                         "د":"ﮄ","ذ":"ﮆ","ر":"ﺭ","ز":"ﺯ","س":"ﺳ","ش":"ﺷ","ص":"ﺻ",
                         "ض":"ﺿ","ط":"ﻁ","ظ":"ﻅ","ع":"ﻋ","غ":"ﻏ","ف":"ﻓ","ق":"ﻗ",
                         "ک":"ﮎ","گ":"ﮒ","ل":"ﻟ","م":"ﻣ","ن":"ﻧ","ه":"ﮬ","و":"ۆ","ی":"ﯼ"}.get(ch,ch) for ch in txt),
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

# ========= جوک و فال =========
jokes = []
fortunes = []

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

@bot.message_handler(func=lambda m: cmd_text(m)=="جوک")
def send_joke(m):
    if not jokes:
        return bot.reply_to(m,"❗ هیچ جوکی ذخیره نشده.")
    joke = random.choice(jokes)
    if joke["type"]=="text":
        bot.send_message(m.chat.id, joke["content"])
    else:
        bot.send_photo(m.chat.id, joke["file"], caption=joke["caption"])

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

@bot.message_handler(func=lambda m: cmd_text(m)=="فال")
def send_fal(m):
    if not fortunes:
        return bot.reply_to(m,"❗ هیچ فالی ذخیره نشده.")
    fal = random.choice(fortunes)
    if fal["type"]=="text":
        bot.send_message(m.chat.id, fal["content"])
    else:
        bot.send_photo(m.chat.id, fal["file"], caption=fal["caption"])# ========= خوشامد =========
welcome_enabled, welcome_texts, welcome_photos = {}, {}, {}

@bot.message_handler(content_types=['new_chat_members'])
def welcome(m):
    for u in m.new_chat_members:
        if not welcome_enabled.get(m.chat.id): 
            continue
        name = u.first_name or ""
        date = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y/%m/%d")
        time_ = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%H:%M:%S")
        custom = welcome_texts.get(m.chat.id)
        txt = custom or f"• سلام {name} به گروه {m.chat.title} خوش آمدی 🌻\n\n📆 {date}\n⏰ {time_}"
        if m.chat.id in welcome_photos:
            bot.send_photo(m.chat.id,welcome_photos[m.chat.id],caption=txt)
        else:
            bot.send_message(m.chat.id,txt)

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

@bot.message_handler(func=lambda m: cmd_text(m).startswith("خوشامد متن"))
def w_txt(m):
    if is_admin(m.chat.id,m.from_user.id):
        welcome_texts[m.chat.id]=cmd_text(m).replace("خوشامد متن","",1).strip()
        msg = bot.reply_to(m,"✍️ متن خوشامد ذخیره شد.")
        auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="ثبت عکس")
def w_photo(m):
    if is_admin(m.chat.id,m.from_user.id) and m.reply_to_message.photo:
        welcome_photos[m.chat.id]=m.reply_to_message.photo[-1].file_id
        msg = bot.reply_to(m,"🖼 عکس خوشامد ذخیره شد.")
        auto_del(m.chat.id,msg.message_id)


# ========= قفل‌ها =========
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
    except: pass# ========= بن / سکوت =========
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
        auto_del(m.chat.id,msg.message_id,delay=7)# ========= مدیریت سودو =========
@bot.message_handler(func=lambda m: cmd_text(m).startswith("افزودن سودو "))
def add_sudo(m):
    if not is_sudo(m.from_user.id): return
    try:
        uid = int(cmd_text(m).split()[-1])
    except:
        msg = bot.reply_to(m,"❗ آیدی نامعتبر")
        auto_del(m.chat.id,msg.message_id,delay=7)
        return
    sudo_ids.add(uid)
    msg = bot.reply_to(m,f"✅ <code>{uid}</code> به سودوها اضافه شد.")
    auto_del(m.chat.id,msg.message_id,delay=7)


@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف سودو "))
def del_sudo(m):
    if not is_sudo(m.from_user.id): return
    try:
        uid = int(cmd_text(m).split()[-1])
    except:
        msg = bot.reply_to(m,"❗ آیدی نامعتبر")
        auto_del(m.chat.id,msg.message_id,delay=7)
        return
    if uid == SUDO_ID:
        msg = bot.reply_to(m,"❗ سودوی اصلی حذف نمی‌شود.")
    elif uid in sudo_ids:
        sudo_ids.remove(uid)
        msg = bot.reply_to(m,f"✅ <code>{uid}</code> حذف شد.")
    else:
        msg = bot.reply_to(m,"ℹ️ این آیدی در سودوها نیست.")
    auto_del(m.chat.id,msg.message_id,delay=7)


# ========= لیست سودوها =========
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="لیست سودوها")
def sudo_list(m):
    if not sudo_ids:
        txt = "ℹ️ هیچ سودویی ثبت نشده."
    else:
        txt = "👑 لیست سودوها:\n\n" + "\n".join([f"▪️ {uid}" for uid in sudo_ids])
    msg = bot.reply_to(m, txt)
    auto_del(m.chat.id,msg.message_id,delay=15)


# ========= ارسال همگانی (فقط سودو) =========
joined_groups=set()

@bot.my_chat_member_handler()
def track_groups(upd):
    try:
        chat = upd.chat
        if chat and chat.type in ("group","supergroup"):
            joined_groups.add(chat.id)
    except:
        pass

waiting_broadcast={}
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ارسال")
def ask_bc(m):
    waiting_broadcast[m.from_user.id]=True
    msg = bot.reply_to(m,"📢 پیام بعدی را بفرست.")
    auto_del(m.chat.id,msg.message_id,delay=10)

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and waiting_broadcast.get(m.from_user.id), content_types=['text','photo'])
def do_bc(m):
    waiting_broadcast[m.from_user.id]=False
    s=0
    for gid in list(joined_groups):
        try:
            if m.content_type=="text":
                bot.send_message(gid,m.text)
            elif m.content_type=="photo":
                bot.send_photo(gid,m.photo[-1].file_id,caption=(m.caption or ""))
            s+=1
        except:
            pass
    msg = bot.reply_to(m,f"✅ به {s} گروه ارسال شد.")
    auto_del(m.chat.id,msg.message_id,delay=10)# ========= استارت در پیوی (پنل سودو) =========
@bot.message_handler(commands=['start'])
def start_cmd(m):
    if m.chat.type == "private":
        kb = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/{bot.get_me().username}?startgroup=new")
        btn2 = types.InlineKeyboardButton("📞 پشتیبانی", url=f"https://t.me/{SUPPORT_ID}")
        kb.add(btn1, btn2)

        if is_sudo(m.from_user.id):  
            btn3 = types.InlineKeyboardButton("🛠 پنل مدیریتی سودو", callback_data=f"sudo_panel:{m.chat.id}")
            btn4 = types.InlineKeyboardButton("📖 راهنمای سودو", callback_data=f"sudo_help:{m.chat.id}")
            kb.add(btn3, btn4)

        bot.send_message(
            m.chat.id,
            "👋 سلام!\n\n"
            "من ربات مدیریت گروه هستم 🤖\n"
            "میتونی منو به گروهت اضافه کنی یا برای راهنمایی بیشتر با پشتیبانی در تماس باشی.",
            reply_markup=kb
        )


# ========= پنل مدیریتی سودو =========
bot_active = True

@bot.callback_query_handler(func=lambda call: call.data.startswith("sudo_panel"))
def sudo_panel(call):
    if not is_sudo(call.from_user.id):
        return bot.answer_callback_query(call.id,"❌ فقط سودو می‌تونه این پنل رو ببینه",show_alert=True)

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📊 آمار گروه‌ها", callback_data="sudo_stats"),
        types.InlineKeyboardButton("🛠 وضعیت ربات", callback_data="sudo_status"),
        types.InlineKeyboardButton("📢 ارسال همگانی", callback_data="sudo_bc"),
        types.InlineKeyboardButton("➕ افزودن سودو", callback_data="sudo_add"),
        types.InlineKeyboardButton("➖ حذف سودو", callback_data="sudo_del"),
        types.InlineKeyboardButton("📎 لینک گروه‌ها", callback_data="sudo_links"),
        types.InlineKeyboardButton("🚫 خاموش/روشن کردن", callback_data="sudo_toggle"),
        types.InlineKeyboardButton("❌ بستن", callback_data="sudo_close")
    )
    bot.edit_message_text("🛠 پنل مدیریتی سودو:", call.message.chat.id, call.message.message_id, reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data=="sudo_close")
def sudo_close(call):
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except: 
        pass


# ========= راهنمای سودو =========
@bot.callback_query_handler(func=lambda call: call.data.startswith("sudo_help"))
def sudo_help(call):
    if not is_sudo(call.from_user.id):
        return
    txt = """
📖 راهنمای سودو:

🔹 افزودن/حذف سودو
🔹 ارسال همگانی
🔹 وضعیت ربات
🔹 آمار گروه‌ها
🔹 لینک گروه‌های فعال
🔹 خاموش/روشن کردن ربات
"""
    bot.send_message(call.message.chat.id, txt)


# ========= وضعیت ربات =========
@bot.callback_query_handler(func=lambda call: call.data=="sudo_status")
def sudo_status(call):
    if not is_sudo(call.from_user.id): return
    now = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    txt = f"🤖 وضعیت ربات:\n\n🟢 فعال: {bot_active}\n🕒 زمان: {now}\n📊 گروه‌ها: {len(joined_groups)}"
    bot.send_message(call.message.chat.id, txt)


# ========= خاموش/روشن کردن ربات =========
@bot.callback_query_handler(func=lambda call: call.data=="sudo_toggle")
def sudo_toggle(call):
    global bot_active
    if not is_sudo(call.from_user.id): return
    bot_active = not bot_active
    status = "🟢 ربات روشن شد." if bot_active else "🔴 ربات خاموش شد."
    bot.send_message(call.message.chat.id, status)# ========= آمار گروه‌ها =========
@bot.callback_query_handler(func=lambda call: call.data=="sudo_stats")
def sudo_stats(call):
    if not is_sudo(call.from_user.id): return
    txt = f"📊 ربات هم‌اکنون در {len(joined_groups)} گروه عضو است."
    bot.send_message(call.message.chat.id, txt)# ========= مدیریت سودوها از پنل =========
waiting_add_sudo = {}   # برای ذخیره وضعیت افزودن سودو

@bot.callback_query_handler(func=lambda call: call.data=="sudo_add")
def sudo_add(call):
    if not is_sudo(call.from_user.id): return
    waiting_add_sudo[call.from_user.id] = True
    bot.send_message(call.message.chat.id,"➕ آیدی عددی فردی که می‌خواهی سودو بشه رو بفرست.")

@bot.message_handler(func=lambda m: waiting_add_sudo.get(m.from_user.id))
def do_add_sudo(m):
    if not is_sudo(m.from_user.id): return
    try:
        uid = int(m.text.strip())
        sudo_ids.add(uid)
        msg = bot.reply_to(m,f"✅ کاربر <code>{uid}</code> به سودوها اضافه شد.")
    except:
        msg = bot.reply_to(m,"❗ لطفا فقط آیدی عددی وارد کن.")
    waiting_add_sudo[m.from_user.id] = False
    auto_del(m.chat.id,msg.message_id,delay=10)


# ========= حذف سودو =========
@bot.callback_query_handler(func=lambda call: call.data=="sudo_del")
def sudo_del(call):
    if not is_sudo(call.from_user.id): return
    if not sudo_ids:
        return bot.send_message(call.message.chat.id,"ℹ️ هیچ سودویی ثبت نشده.")
    kb = types.InlineKeyboardMarkup()
    for uid in sudo_ids:
        kb.add(types.InlineKeyboardButton(f"❌ {uid}", callback_data=f"del_sudo:{uid}"))
    bot.send_message(call.message.chat.id,"➖ یکی از سودوها رو انتخاب کن:",reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_sudo:"))
def do_del_sudo(call):
    if not is_sudo(call.from_user.id): return
    uid = int(call.data.split(":")[1])
    if uid in sudo_ids:
        sudo_ids.remove(uid)
        bot.answer_callback_query(call.id,f"❌ سودو {uid} حذف شد.",show_alert=True)
    else:
        bot.answer_callback_query(call.id,"❗ پیدا نشد.",show_alert=True)


# ========= لیست سودوها =========
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="لیست سودوها")
def sudo_list(m):
    if not sudo_ids:
        txt = "ℹ️ هیچ سودویی ثبت نشده."
    else:
        txt = "👑 لیست سودوها:\n\n" + "\n".join([f"▪️ {uid}" for uid in sudo_ids])
    msg = bot.reply_to(m, txt)
    auto_del(m.chat.id,msg.message_id,delay=15)# ========= پنل مدیریتی سودو چندصفحه‌ای =========

# لیست صفحات پنل
SUDO_PAGES = {
    1: [
        ("➕ افزودن سودو", "sudo_add"),
        ("➖ حذف سودو", "sudo_del"),
        ("📋 لیست سودوها", "sudo_list"),
    ],
    2: [
        ("🛠 وضعیت ربات", "sudo_status"),
        ("📊 آمار گروه‌ها", "sudo_stats"),
        ("🔗 لینک گروه‌ها", "sudo_links"),
    ],
    3: [
        ("📢 ارسال همگانی", "sudo_bc"),
        ("🚪 لفت بده", "sudo_leave"),
        ("👥 لیست مدیران ربات", "sudo_admins"),
    ],
    4: [
        ("🔴 خاموش/🟢 روشن", "sudo_toggle"),
        ("⚙️ ریست قفل‌ها", "sudo_reset_locks"),
        ("📖 راهنمای سودو", "sudo_help"),
    ]
}

TOTAL_SUDO_PAGES = len(SUDO_PAGES)

def sudo_panel_markup(page:int=1):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for text, cb in SUDO_PAGES.get(page, []):
        kb.add(types.InlineKeyboardButton(text, callback_data=cb))
    
    nav_btns = []
    if page > 1:
        nav_btns.append(types.InlineKeyboardButton("◀️ قبلی", callback_data=f"sudo_page:{page-1}"))
    if page < TOTAL_SUDO_PAGES:
        nav_btns.append(types.InlineKeyboardButton("▶️ بعدی", callback_data=f"sudo_page:{page+1}"))
    if nav_btns:
        kb.add(*nav_btns)
    
    kb.add(types.InlineKeyboardButton("❌ بستن", callback_data="sudo_close"))
    return kb

@bot.message_handler(commands=['sudo'])
def open_sudo_panel(m):
    if not is_sudo(m.from_user.id): return
    kb = sudo_panel_markup(1)
    bot.send_message(m.chat.id, "🛠 پنل مدیریتی سودو (صفحه ۱ از ۴):", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("sudo_page:"))
def sudo_page_nav(call):
    if not is_sudo(call.from_user.id): 
        return bot.answer_callback_query(call.id,"❌ فقط سودو می‌تواند ببیند",show_alert=True)
    page = int(call.data.split(":")[1])
    kb = sudo_panel_markup(page)
    try:
        bot.edit_message_text(
            f"🛠 پنل مدیریتی سودو (صفحه {page} از {TOTAL_SUDO_PAGES}):",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb
        )
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data=="sudo_close")
def sudo_close(call):
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass# ========= تنظیمات حذف خودکار =========
delete_delay = 7  # پیش‌فرض

def auto_del(chat_id,msg_id,delay=None):
    d = delay if delay is not None else delete_delay
    if d <= 0: return  # اگر خاموش بود
    def _():
        time.sleep(d)
        try: bot.delete_message(chat_id,msg_id)
        except: pass
    threading.Thread(target=_).start()

# ========= پنل سودو (بخش تنظیمات اضافه شد) =========
@bot.callback_query_handler(func=lambda call: call.data.startswith("sudo_panel"))
def sudo_panel(call):
    if not is_sudo(call.from_user.id):
        return bot.answer_callback_query(call.id,"❌ فقط سودو می‌تونه این پنل رو ببینه",show_alert=True)

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📊 آمار گروه‌ها", callback_data="sudo_stats"),
        types.InlineKeyboardButton("🛠 وضعیت ربات", callback_data="sudo_status"),
        types.InlineKeyboardButton("📢 ارسال همگانی", callback_data="sudo_bc"),
        types.InlineKeyboardButton("➕ افزودن سودو", callback_data="sudo_add"),
        types.InlineKeyboardButton("➖ حذف سودو", callback_data="sudo_del"),
        types.InlineKeyboardButton("📎 لینک گروه‌ها", callback_data="sudo_links"),
        types.InlineKeyboardButton("🚫 خاموش/روشن کردن", callback_data="sudo_toggle"),
        types.InlineKeyboardButton("⚙️ تنظیم زمان حذف پیام", callback_data="sudo_delay"),
        types.InlineKeyboardButton("❌ بستن", callback_data="sudo_close")
    )
    bot.edit_message_text("🛠 پنل مدیریتی سودو:", call.message.chat.id, call.message.message_id, reply_markup=kb)

# ========= تنظیم زمان حذف پیام =========
@bot.callback_query_handler(func=lambda call: call.data=="sudo_delay")
def sudo_delay(call):
    if not is_sudo(call.from_user.id): return
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("۵ ثانیه", callback_data="set_delay:5"),
        types.InlineKeyboardButton("۱۰ ثانیه", callback_data="set_delay:10"),
        types.InlineKeyboardButton("۱۵ ثانیه", callback_data="set_delay:15"),
        types.InlineKeyboardButton("۳۰ ثانیه", callback_data="set_delay:30"),
        types.InlineKeyboardButton("خاموش ❌", callback_data="set_delay:0")
    )
    bot.edit_message_text(f"⚙️ زمان فعلی حذف پیام: {delete_delay if delete_delay>0 else 'خاموش'} ثانیه\n\n⏳ یکی رو انتخاب کن:", 
                          call.message.chat.id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_delay:"))
def set_delay(call):
    global delete_delay
    if not is_sudo(call.from_user.id): return
    val = int(call.data.split(":")[1])
    delete_delay = val
    status = f"⏳ زمان حذف پیام روی {val} ثانیه تنظیم شد." if val>0 else "❌ حذف خودکار پیام خاموش شد."
    bot.edit_message_text(status, call.message.chat.id, call.message.message_id)import json

# ========= فایل ذخیره =========
DATA_FILE = "bot_data.json"

data = {
    "delete_delay": 7,
    "jokes": [],
    "fortunes": [],
    "welcome_texts": {},
    "welcome_photos": {},
    "welcome_enabled": {},
    "origins": {}
}

# ========= بارگذاری از فایل =========
def load_data():
    global data, delete_delay, jokes, fortunes, welcome_texts, welcome_photos, welcome_enabled, origins
    try:
        with open(DATA_FILE,"r",encoding="utf-8") as f:
            data.update(json.load(f))
    except: pass
    delete_delay = data.get("delete_delay",7)
    jokes = data.get("jokes",[])
    fortunes = data.get("fortunes",[])
    welcome_texts = data.get("welcome_texts",{})
    welcome_photos = data.get("welcome_photos",{})
    welcome_enabled = data.get("welcome_enabled",{})
    origins = data.get("origins",{})

# ========= ذخیره در فایل =========
def save_data():
    data.update({
        "delete_delay": delete_delay,
        "jokes": jokes,
        "fortunes": fortunes,
        "welcome_texts": welcome_texts,
        "welcome_photos": welcome_photos,
        "welcome_enabled": welcome_enabled,
        "origins": origins
    })
    with open(DATA_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)

# بارگذاری اول
load_data()# وقتی سودو زمان حذف پیام رو تغییر میده
delete_delay = val
save_data()

# وقتی جوک یا فال ذخیره میشه
jokes.append({...})
save_data()

# وقتی اصل ثبت میشه
origins.setdefault(m.chat.id,{})[uid] = val
save_data()

# وقتی متن یا عکس خوشامد تغییر کنه
welcome_texts[m.chat.id] = ...
save_data()# ========= مدیریت جوک‌ها =========
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="لیست جوک‌ها")
def list_jokes(m):
    if not jokes:
        return bot.reply_to(m,"ℹ️ هیچ جوکی ذخیره نشده.")
    txt = "😂 لیست جوک‌ها:\n\n"
    for i,j in enumerate(jokes[-10:],1):
        if j["type"]=="text":
            txt += f"{i}. {j['content'][:30]}...\n"
        else:
            txt += f"{i}. [عکس با کپشن: {j['caption'][:20]}]\n"
    msg = bot.reply_to(m,txt)
    auto_del(m.chat.id,msg.message_id,delay=25)

@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m).startswith("حذف جوک "))
def del_joke(m):
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        if 0 <= idx < len(jokes):
            jokes.pop(idx)
            save_data()
            msg = bot.reply_to(m,"✅ جوک حذف شد.")
        else:
            msg = bot.reply_to(m,"❗ شماره نامعتبر است.")
    except:
        msg = bot.reply_to(m,"❗ دستور درست نیست.")
    auto_del(m.chat.id,msg.message_id,delay=7)

@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="پاکسازی جوک‌ها")
def clear_jokes(m):
    jokes.clear()
    save_data()
    msg = bot.reply_to(m,"🗑 همه جوک‌ها پاک شدند.")
    auto_del(m.chat.id,msg.message_id,delay=7)# ========= مدیریت فال‌ها =========
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="لیست فال‌ها")
def list_fals(m):
    if not fortunes:
        return bot.reply_to(m,"ℹ️ هیچ فالی ذخیره نشده.")
    txt = "🔮 لیست فال‌ها:\n\n"
    for i,f in enumerate(fortunes[-10:],1):
        if f["type"]=="text":
            txt += f"{i}. {f['content'][:30]}...\n"
        else:
            txt += f"{i}. [عکس با کپشن: {f['caption'][:20]}]\n"
    msg = bot.reply_to(m,txt)
    auto_del(m.chat.id,msg.message_id,delay=25)

@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m).startswith("حذف فال "))
def del_fal(m):
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        if 0 <= idx < len(fortunes):
            fortunes.pop(idx)
            save_data()
            msg = bot.reply_to(m,"✅ فال حذف شد.")
        else:
            msg = bot.reply_to(m,"❗ شماره نامعتبر است.")
    except:
        msg = bot.reply_to(m,"❗ دستور درست نیست.")
    auto_del(m.chat.id,msg.message_id,delay=7)

@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="پاکسازی فال‌ها")
def clear_fals(m):
    fortunes.clear()
    save_data()
    msg = bot.reply_to(m,"🗑 همه فال‌ها پاک شدند.")
    auto_del(m.chat.id,msg.message_id,delay=7)# ========= مدیریت خوشامد =========
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
    auto_del(m.chat.id, msg.message_id, delay=15)@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="حذف متن خوشامد")
def del_welcome_text(m):
    welcome_texts.pop(m.chat.id, None)
    msg = bot.reply_to(m,"✍️ متن خوشامد حذف شد (بازگشت به پیش‌فرض).")
    auto_del(m.chat.id,msg.message_id,delay=7)

@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="حذف عکس خوشامد")
def del_welcome_photo(m):
    welcome_photos.pop(m.chat.id, None)
    msg = bot.reply_to(m,"🖼 عکس خوشامد حذف شد.")
    auto_del(m.chat.id,msg.message_id,delay=7)

@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="ریست خوشامد")
def reset_welcome(m):
    welcome_texts.pop(m.chat.id, None)
    welcome_photos.pop(m.chat.id, None)
    welcome_enabled[m.chat.id] = True
    msg = bot.reply_to(m,"🔄 خوشامد به حالت پیش‌فرض برگشت.")
    auto_del(m.chat.id,msg.message_id,delay=7)# ====== تنظیمات حذف خودکار ======
DEFAULT_DELETE = int(os.environ.get("DELETE_DELAY", "7"))           # پیش‌فرض گروه‌ها
PRIVATE_DELETE_DEFAULT = int(os.environ.get("PRIVATE_DELETE_DELAY", "0"))  # پیش‌فرض پی‌وی

# نگه‌داری زمان حذف به‌ازای هر چت
chat_delete_delay = {}  # chat_id -> seconds (0 یعنی خاموش)

def get_chat_delete_delay(chat_id):
    """بر اساس نوع چت (گروه/پی‌وی) و تنظیم اختصاصی مقدار را برمی‌گرداند."""
    try:
        ch = bot.get_chat(chat_id)
        is_private = (ch.type == "private")
    except:
        is_private = False
    base = PRIVATE_DELETE_DEFAULT if is_private else DEFAULT_DELETE
    return chat_delete_delay.get(chat_id, base)

def auto_del(chat_id, msg_id, delay=None):
    """
    حذف پیام با تاخیر تنظیم‌شده.
    نکته مهم: هر پارامتر delay پاس‌داده‌شده نادیده گرفته می‌شود
    تا همه‌چیز از تنظیمات واحد پیروی کند.
    """
    d = get_chat_delete_delay(chat_id)
    if d <= 0:
        return
    def _worker():
        time.sleep(d)
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
    threading.Thread(target=_worker, daemon=True).start()# ====== نمایش زمان حذف در این چت ======
@bot.message_handler(func=lambda m: cmd_text(m) == "زمان حذف")
def show_delete_time(m):
    d = get_chat_delete_delay(m.chat.id)
    status = "خاموش" if d <= 0 else f"{d} ثانیه"
    msg = bot.reply_to(m, f"⏳ زمان حذف خودکار پیام‌های ربات در این چت: {status}\n(۰ = خاموش)")
    auto_del(m.chat.id, msg.message_id)

# ====== تنظیم زمان حذف در این چت ======
@bot.message_handler(func=lambda m: cmd_text(m).startswith("زمان حذف "))
def set_delete_time(m):
    # محدودسازی دسترسی
    if m.chat.type == "private":
        if not is_sudo(m.from_user.id):
            return
    else:
        if not is_admin(m.chat.id, m.from_user.id):
            return

    # خواندن عدد
    parts = cmd_text(m).split()
    if len(parts) < 3:
        msg = bot.reply_to(m, "❗ فرمت درست: «زمان حذف 10» (برحسب ثانیه). ۰ = خاموش")
        return auto_del(m.chat.id, msg.message_id)

    try:
        sec = int(parts[-1])
        if sec < 0:
            raise ValueError
        # سقف منطقی (مثلاً 600 ثانیه = 10 دقیقه)
        if sec > 600:
            sec = 600
    except:
        msg = bot.reply_to(m, "❗ فقط عدد صحیح بنویس. مثال: «زمان حذف 15»")
        return auto_del(m.chat.id, msg.message_id)

    chat_delete_delay[m.chat.id] = sec
    human = "خاموش" if sec == 0 else f"{sec} ثانیه"
    msg = bot.reply_to(m, f"✅ زمان حذف خودکار برای این چت تنظیم شد: {human}")
    auto_del(m.chat.id, msg.message_id)

# ====== میانبرها: خاموش/روشن ======
@bot.message_handler(func=lambda m: cmd_text(m) == "حذف خودکار خاموش")
def disable_autodel(m):
    if m.chat.type == "private":
        if not is_sudo(m.from_user.id): return
    else:
        if not is_admin(m.chat.id, m.from_user.id): return
    chat_delete_delay[m.chat.id] = 0
    msg = bot.reply_to(m, "🔴 حذف خودکار پیام‌های ربات در این چت خاموش شد.")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف خودکار روشن"))
def enable_autodel(m):
    if m.chat.type == "private":
        if not is_sudo(m.from_user.id): return
    else:
        if not is_admin(m.chat.id, m.from_user.id): return

    # اجازه بده «حذف خودکار روشن 12» هم کار کند
    parts = cmd_text(m).split()
    sec = None
    if len(parts) >= 3:
        try:
            sec = int(parts[-1])
        except:
            sec = None

    if sec is None:
        # اگر عدد ندادند از پیش‌فرض‌های پایه استفاده کن
        d = get_chat_delete_delay(m.chat.id)
        sec = d if d > 0 else (DEFAULT_DELETE if m.chat.type != "private" else PRIVATE_DELETE_DEFAULT)

    if sec < 0: sec = 0
    if sec > 600: sec = 600

    chat_delete_delay[m.chat.id] = sec
    msg = bot.reply_to(m, f"🟢 حذف خودکار روشن شد: {sec} ثانیه")
    auto_del(m.chat.id, msg.message_id)@bot.callback_query_handler(func=lambda call: call.data.startswith("sudo_panel"))
def sudo_panel(call):
    if not is_sudo(call.from_user.id):
        return bot.answer_callback_query(call.id,"❌ فقط سودو می‌تونه این پنل رو ببینه",show_alert=True)

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📊 آمار گروه‌ها", callback_data="sudo_stats"),
        types.InlineKeyboardButton("🛠 وضعیت ربات", callback_data="sudo_status"),
        types.InlineKeyboardButton("📢 ارسال همگانی", callback_data="sudo_bc"),
        types.InlineKeyboardButton("➕ افزودن سودو", callback_data="sudo_add"),
        types.InlineKeyboardButton("➖ حذف سودو", callback_data="sudo_del"),
        types.InlineKeyboardButton("📎 لینک گروه‌ها", callback_data="sudo_links"),
        types.InlineKeyboardButton("⏳ زمان حذف", callback_data="sudo_delete_time"),  # 👈 اینو اضافه کردیم
        types.InlineKeyboardButton("🚫 خاموش/روشن کردن", callback_data="sudo_toggle"),
        types.InlineKeyboardButton("❌ بستن", callback_data="sudo_close")
    )
    bot.edit_message_text("🛠 پنل مدیریتی سودو:", call.message.chat.id, call.message.message_id, reply_markup=kb)@bot.callback_query_handler(func=lambda call: call.data=="sudo_delete_time")
def sudo_delete_time(call):
    if not is_sudo(call.from_user.id): return
    kb = types.InlineKeyboardMarkup(row_width=2)
    for sec in [5,10,15,30]:
        kb.add(types.InlineKeyboardButton(f"⏳ {sec} ثانیه", callback_data=f"sudo_setdelay:{sec}"))
    kb.add(types.InlineKeyboardButton("🔴 خاموش", callback_data="sudo_setdelay:0"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="sudo_panel_back"))
    bot.edit_message_text("⏳ انتخاب زمان حذف خودکار برای پی‌وی سودو:", call.message.chat.id, call.message.message_id, reply_markup=kb)@bot.callback_query_handler(func=lambda call: call.data.startswith("sudo_setdelay:"))
def sudo_setdelay(call):
    if not is_sudo(call.from_user.id): return
    sec = int(call.data.split(":")[1])
    chat_delete_delay[call.message.chat.id] = sec
    status = "خاموش" if sec == 0 else f"{sec} ثانیه"
    bot.answer_callback_query(call.id, f"✅ زمان حذف روی {status} تنظیم شد.", show_alert=True)
    # برگردوندن دوباره به پنل اصلی
    sudo_panel(call)@bot.callback_query_handler(func=lambda call: call.data=="sudo_panel_back")
def sudo_panel_back(call):
    sudo_panel(call)global_delete_delay = 7  # پیش‌فرض برای گروه‌ها ۷ ثانیه@bot.callback_query_handler(func=lambda call: call.data=="sudo_delete_time")
def sudo_delete_time(call):
    if not is_sudo(call.from_user.id): return
    kb = types.InlineKeyboardMarkup(row_width=2)
    
    # زمان برای پی‌وی سودو
    for sec in [5,10,15,30]:
        kb.add(types.InlineKeyboardButton(f"⏳ {sec} ثانیه (پی‌وی)", callback_data=f"sudo_setdelay_pm:{sec}"))
    kb.add(types.InlineKeyboardButton("🔴 خاموش (پی‌وی)", callback_data="sudo_setdelay_pm:0"))

    # زمان برای گروه‌ها
    for sec in [5,10,15,30]:
        kb.add(types.InlineKeyboardButton(f"⏳ {sec} ثانیه (گروه‌ها)", callback_data=f"sudo_setdelay_grp:{sec}"))
    kb.add(types.InlineKeyboardButton("🔴 خاموش (گروه‌ها)", callback_data="sudo_setdelay_grp:0"))
    
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="sudo_panel_back"))
    bot.edit_message_text("⏳ انتخاب زمان حذف خودکار:", call.message.chat.id, call.message.message_id, reply_markup=kb)@bot.callback_query_handler(func=lambda call: call.data.startswith("sudo_setdelay_pm:"))
def sudo_setdelay_pm(call):
    if not is_sudo(call.from_user.id): return
    sec = int(call.data.split(":")[1])
    chat_delete_delay[call.message.chat.id] = sec
    status = "خاموش" if sec == 0 else f"{sec} ثانیه"
    bot.answer_callback_query(call.id, f"✅ زمان حذف پی‌وی روی {status} تنظیم شد.", show_alert=True)
    sudo_panel(call)@bot.callback_query_handler(func=lambda call: call.data.startswith("sudo_setdelay_grp:"))
def sudo_setdelay_grp(call):
    global global_delete_delay
    if not is_sudo(call.from_user.id): return
    sec = int(call.data.split(":")[1])
    global_delete_delay = sec
    status = "خاموش" if sec == 0 else f"{sec} ثانیه"
    bot.answer_callback_query(call.id, f"✅ زمان حذف گروه‌ها روی {status} تنظیم شد.", show_alert=True)
    sudo_panel(call)def auto_del(chat_id,msg_id,delay=None):
    def _():
        time.sleep(delay or global_delete_delay)
        try: bot.delete_message(chat_id,msg_id)
        except: pass
    threading.Thread(target=_).start()kb.add(
    types.InlineKeyboardButton("📝 مدیریت جوک/فال", callback_data="sudo_jokes_fal")
)@bot.callback_query_handler(func=lambda call: call.data=="sudo_jokes_fal")
def sudo_jokes_fal(call):
    if not is_sudo(call.from_user.id): return
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("😂 لیست جوک‌ها", callback_data="sudo_list_jokes"),
        types.InlineKeyboardButton("🔮 لیست فال‌ها", callback_data="sudo_list_fal"),
    )
    kb.add(
        types.InlineKeyboardButton("➕ ثبت جوک", callback_data="sudo_add_joke"),
        types.InlineKeyboardButton("➕ ثبت فال", callback_data="sudo_add_fal"),
    )
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="sudo_panel_back"))
    
    bot.edit_message_text("📝 مدیریت جوک و فال:", call.message.chat.id, call.message.message_id, reply_markup=kb)@bot.callback_query_handler(func=lambda call: call.data=="sudo_list_jokes")
def sudo_list_jokes(call):
    if not is_sudo(call.from_user.id): return
    if not jokes:
        return bot.send_message(call.message.chat.id,"❗ هیچ جوکی ذخیره نشده.")
    
    txt = "😂 لیست جوک‌ها (۱۰ تای آخر):\n\n"
    kb = types.InlineKeyboardMarkup(row_width=1)
    for i, joke in enumerate(jokes[-10:], 1):
        preview = joke["content"][:20] if joke["type"]=="text" else "[📸 عکس]"
        txt += f"{i}. {preview}\n"
        kb.add(types.InlineKeyboardButton(f"❌ حذف {i}", callback_data=f"sudo_del_joke:{len(jokes)-10+i-1}"))
    
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="sudo_jokes_fal"))
    bot.send_message(call.message.chat.id, txt, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("sudo_del_joke:"))
def sudo_del_joke(call):
    if not is_sudo(call.from_user.id): return
    idx = int(call.data.split(":")[1])
    try:
        jokes.pop(idx)
        bot.answer_callback_query(call.id,"✅ جوک حذف شد.",show_alert=True)
    except:
        bot.answer_callback_query(call.id,"❗ خطا در حذف جوک.",show_alert=True)
    sudo_jokes_fal(call)@bot.callback_query_handler(func=lambda call: call.data=="sudo_list_fal")
def sudo_list_fal(call):
    if not is_sudo(call.from_user.id): return
    if not fortunes:
        return bot.send_message(call.message.chat.id,"❗ هیچ فالی ذخیره نشده.")
    
    txt = "🔮 لیست فال‌ها (۱۰ تای آخر):\n\n"
    kb = types.InlineKeyboardMarkup(row_width=1)
    for i, fal in enumerate(fortunes[-10:], 1):
        preview = fal["content"][:20] if fal["type"]=="text" else "[📸 عکس]"
        txt += f"{i}. {preview}\n"
        kb.add(types.InlineKeyboardButton(f"❌ حذف {i}", callback_data=f"sudo_del_fal:{len(fortunes)-10+i-1}"))
    
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="sudo_jokes_fal"))
    bot.send_message(call.message.chat.id, txt, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("sudo_del_fal:"))
def sudo_del_fal(call):
    if not is_sudo(call.from_user.id): return
    idx = int(call.data.split(":")[1])
    try:
        fortunes.pop(idx)
        bot.answer_callback_query(call.id,"✅ فال حذف شد.",show_alert=True)
    except:
        bot.answer_callback_query(call.id,"❗ خطا در حذف فال.",show_alert=True)
    sudo_jokes_fal(call)waiting_joke = {}
waiting_fal = {}

@bot.callback_query_handler(func=lambda call: call.data=="sudo_add_joke")
def sudo_add_joke(call):
    if not is_sudo(call.from_user.id): return
    waiting_joke[call.from_user.id] = True
    bot.send_message(call.message.chat.id,"😂 جوک بعدی که می‌فرستی ذخیره میشه.")

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and waiting_joke.get(m.from_user.id), content_types=['text','photo'])
def do_add_joke(m):
    waiting_joke[m.from_user.id] = False
    if m.content_type == "text":
        jokes.append({"type":"text","content":m.text})
    elif m.content_type == "photo":
        jokes.append({"type":"photo","file":m.photo[-1].file_id,"caption":m.caption or ""})
    bot.reply_to(m,"✅ جوک ذخیره شد.")

@bot.callback_query_handler(func=lambda call: call.data=="sudo_add_fal")
def sudo_add_fal(call):
    if not is_sudo(call.from_user.id): return
    waiting_fal[call.from_user.id] = True
    bot.send_message(call.message.chat.id,"🔮 فال بعدی که می‌فرستی ذخیره میشه.")

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and waiting_fal.get(m.from_user.id), content_types=['text','photo'])
def do_add_fal(m):
    waiting_fal[m.from_user.id] = False
    if m.content_type == "text":
        fortunes.append({"type":"text","content":m.text})
    elif m.content_type == "photo":
        fortunes.append({"type":"photo","file":m.photo[-1].file_id,"caption":m.caption or ""})
    bot.reply_to(m,"✅ فال ذخیره شد.")# ========= خوشامد در پنل سودو =========

DEFAULT_WELCOME = "• سلام {name} به گروه {title} خوش آمدید 🌻"

@bot.callback_query_handler(func=lambda call: call.data == "sudo_welcome")
def sudo_welcome_panel(call):
    if not is_sudo(call.from_user.id):
        return
    chat_id = call.message.chat.id

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✅ روشن", callback_data="welcome_on"),
        types.InlineKeyboardButton("❌ خاموش", callback_data="welcome_off"),
        types.InlineKeyboardButton("✍️ تغییر متن", callback_data="welcome_text"),
        types.InlineKeyboardButton("🖼 حذف عکس", callback_data="welcome_delphoto"),
        types.InlineKeyboardButton("♻️ متن پیش‌فرض", callback_data="welcome_reset")
    )
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="sudo_panel_back"))
    bot.edit_message_text("🎉 مدیریت خوشامد:", chat_id, call.message.message_id, reply_markup=kb)


# روشن
@bot.callback_query_handler(func=lambda call: call.data == "welcome_on")
def welcome_on(call):
    welcome_enabled[call.message.chat.id] = True
    bot.answer_callback_query(call.id, "✅ خوشامد روشن شد", show_alert=True)

# خاموش
@bot.callback_query_handler(func=lambda call: call.data == "welcome_off")
def welcome_off(call):
    welcome_enabled[call.message.chat.id] = False
    bot.answer_callback_query(call.id, "❌ خوشامد خاموش شد", show_alert=True)

# تغییر متن
waiting_welcome_text = {}

@bot.callback_query_handler(func=lambda call: call.data == "welcome_text")
def welcome_text_wait(call):
    waiting_welcome_text[call.from_user.id] = call.message.chat.id
    bot.send_message(call.message.chat.id, "✍️ متن جدید خوشامد را ارسال کنید...")

@bot.message_handler(func=lambda m: waiting_welcome_text.get(m.from_user.id))
def welcome_text_set(m):
    chat_id = waiting_welcome_text.pop(m.from_user.id)
    welcome_texts[chat_id] = m.text
    bot.send_message(chat_id, "✅ متن خوشامد تغییر کرد.")

# حذف عکس
@bot.callback_query_handler(func=lambda call: call.data == "welcome_delphoto")
def welcome_delphoto(call):
    welcome_photos.pop(call.message.chat.id, None)
    bot.answer_callback_query(call.id, "🖼 عکس خوشامد حذف شد", show_alert=True)

# ریست متن
@bot.callback_query_handler(func=lambda call: call.data == "welcome_reset")
def welcome_reset(call):
    welcome_texts[call.message.chat.id] = DEFAULT_WELCOME
    bot.answer_callback_query(call.id, "♻️ متن خوشامد به حالت پیش‌فرض برگشت", show_alert=True)# ========= مدیریت جوک و فال در پنل سودو =========

jokes = []
fortunes = []

@bot.callback_query_handler(func=lambda call: call.data == "sudo_jokes")
def sudo_jokes_panel(call):
    if not is_sudo(call.from_user.id): return
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📥 ثبت جوک", callback_data="joke_add"),
        types.InlineKeyboardButton("📤 جوک تصادفی", callback_data="joke_random"),
        types.InlineKeyboardButton("🗑 حذف همه جوک‌ها", callback_data="joke_clear"),
        types.InlineKeyboardButton("🔙 بازگشت", callback_data="sudo_panel_back")
    )
    bot.edit_message_text("😂 مدیریت جوک:", call.message.chat.id, call.message.message_id, reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data == "sudo_fal")
def sudo_fal_panel(call):
    if not is_sudo(call.from_user.id): return
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📥 ثبت فال", callback_data="fal_add"),
        types.InlineKeyboardButton("📤 فال تصادفی", callback_data="fal_random"),
        types.InlineKeyboardButton("🗑 حذف همه فال‌ها", callback_data="fal_clear"),
        types.InlineKeyboardButton("🔙 بازگشت", callback_data="sudo_panel_back")
    )
    bot.edit_message_text("🔮 مدیریت فال:", call.message.chat.id, call.message.message_id, reply_markup=kb)


# ========== ثبت جوک ==========
waiting_joke = {}

@bot.callback_query_handler(func=lambda call: call.data == "joke_add")
def joke_add_wait(call):
    waiting_joke[call.from_user.id] = True
    bot.send_message(call.message.chat.id, "✍️ متن یا عکس جوک رو بفرست...")

@bot.message_handler(func=lambda m: waiting_joke.get(m.from_user.id))
def joke_add_set(m):
    waiting_joke.pop(m.from_user.id)
    if m.text:
        jokes.append({"type":"text","content":m.text})
    elif m.photo:
        jokes.append({"type":"photo","file":m.photo[-1].file_id,"caption":m.caption or ""})
    bot.reply_to(m,"✅ جوک ثبت شد.")


# ========== جوک تصادفی ==========
@bot.callback_query_handler(func=lambda call: call.data == "joke_random")
def joke_random(call):
    if not jokes:
        return bot.answer_callback_query(call.id,"❗ هیچ جوکی ثبت نشده.",show_alert=True)
    joke = random.choice(jokes)
    if joke["type"]=="text":
        bot.send_message(call.message.chat.id, joke["content"])
    else:
        bot.send_photo(call.message.chat.id, joke["file"], caption=joke["caption"])


# ========== حذف همه جوک‌ها ==========
@bot.callback_query_handler(func=lambda call: call.data == "joke_clear")
def joke_clear(call):
    jokes.clear()
    bot.answer_callback_query(call.id,"🗑 همه جوک‌ها حذف شدند.",show_alert=True)


# ========== ثبت فال ==========
waiting_fal = {}

@bot.callback_query_handler(func=lambda call: call.data == "fal_add")
def fal_add_wait(call):
    waiting_fal[call.from_user.id] = True
    bot.send_message(call.message.chat.id, "✍️ متن یا عکس فال رو بفرست...")

@bot.message_handler(func=lambda m: waiting_fal.get(m.from_user.id))
def fal_add_set(m):
    waiting_fal.pop(m.from_user.id)
    if m.text:
        fortunes.append({"type":"text","content":m.text})
    elif m.photo:
        fortunes.append({"type":"photo","file":m.photo[-1].file_id,"caption":m.caption or ""})
    bot.reply_to(m,"✅ فال ثبت شد.")


# ========== فال تصادفی ==========
@bot.callback_query_handler(func=lambda call: call.data == "fal_random")
def fal_random(call):
    if not fortunes:
        return bot.answer_callback_query(call.id,"❗ هیچ فالی ثبت نشده.",show_alert=True)
    fal = random.choice(fortunes)
    if fal["type"]=="text":
        bot.send_message(call.message.chat.id, fal["content"])
    else:
        bot.send_photo(call.message.chat.id, fal["file"], caption=fal["caption"])


# ========== حذف همه فال‌ها ==========
@bot.callback_query_handler(func=lambda call: call.data == "fal_clear")
def fal_clear(call):
    fortunes.clear()
    bot.answer_callback_query(call.id,"🗑 همه فال‌ها حذف شدند.",show_alert=True)auto_del_time = 7  # مقدار پیش‌فرضdef auto_del(chat_id,msg_id,delay=None):
    def _():
        time.sleep(delay or auto_del_time)
        try: bot.delete_message(chat_id,msg_id)
        except: pass
    threading.Thread(target=_).start()@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("تنظیم زمان "))
def set_autodel(m):
    global auto_del_time
    try:
        sec = int(cmd_text(m).split()[-1])
        if 5 <= sec <= 60:
            auto_del_time = sec
            msg = bot.reply_to(m,f"✅ زمان حذف خودکار روی {sec} ثانیه تنظیم شد.")
        else:
            msg = bot.reply_to(m,"❗ فقط عددی بین ۵ تا ۶۰ وارد کن.")
    except:
        msg = bot.reply_to(m,"❗ فرمت درست: تنظیم زمان [عدد ثانیه]")
    auto_del(m.chat.id,msg.message_id,delay=10)types.InlineKeyboardButton("⏱ زمان حذف پیام‌ها", callback_data="sudo_autodel")@bot.callback_query_handler(func=lambda call: call.data=="sudo_autodel")
def sudo_autodel(call):
    if not is_sudo(call.from_user.id): return
    bot.send_message(call.message.chat.id,"⏱ با دستور:\n\nتنظیم زمان [عدد ثانیه]\n\nمثال: تنظیم زمان 15")@bot.message_handler(func=lambda m: m.from_user.id == SUDO_ID and cmd_text(m).startswith("تنظیم زمان "))
def set_autodel(m):
    global auto_del_time
    try:
        sec = int(cmd_text(m).split()[-1])
        if 5 <= sec <= 60:
            auto_del_time = sec
            msg = bot.reply_to(m,f"✅ زمان حذف خودکار روی {sec} ثانیه تنظیم شد.")
        else:
            msg = bot.reply_to(m,"❗ فقط عددی بین ۵ تا ۶۰ وارد کن.")
    except:
        msg = bot.reply_to(m,"❗ فرمت درست: تنظیم زمان [عدد ثانیه]")
    auto_del(m.chat.id,msg.message_id,delay=10)print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True, timeout=30)
