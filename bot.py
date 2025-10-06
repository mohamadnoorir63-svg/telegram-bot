# -*- coding: utf-8 -*-
import telebot, os, threading, time, random
from telebot import types
from datetime import datetime
import pytz

# ================== تنظیمات ==================
TOKEN   = os.environ.get("BOT_TOKEN")   # توکن ربات از Config Vars
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))  # آیدی سودو اصلی
SUPPORT_ID = "NOORI_NOOR"  # آیدی پشتیبانی
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
# ============================================

# ========= سودو / ادمین =========
sudo_ids = {SUDO_ID}
def is_sudo(uid): 
    return uid in sudo_ids

def is_admin(chat_id, user_id):
    if is_sudo(user_id): return True
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator","creator")
    except:
        return False

def cmd_text(m):
    return (getattr(m,"text",None) or getattr(m,"caption",None) or "").strip()

# ========= حذف خودکار پیام‌ها =========
def auto_del(chat_id,msg_id,delay=7):
    def _():
        time.sleep(delay)
        try: bot.delete_message(chat_id,msg_id)
        except: pass
    threading.Thread(target=_).start()

# ========= دستورات عمومی =========

# ⏰ ساعت
@bot.message_handler(func=lambda m: cmd_text(m)=="ساعت")
def time_cmd(m):
    now_utc=datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_teh=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    msg = bot.reply_to(m,f"⏰ ساعت UTC: {now_utc}\n⏰ ساعت تهران: {now_teh}")
    auto_del(m.chat.id,msg.message_id,delay=7)

# 🆔 ایدی
@bot.message_handler(func=lambda m: cmd_text(m)=="ایدی")
def id_cmd(m):
    try:
        photos=bot.get_user_profile_photos(m.from_user.id,limit=1)
        caption=f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>"
        if photos.total_count>0:
            msg = bot.send_photo(m.chat.id,photos.photos[0][-1].file_id,caption=caption)
        else:
            msg = bot.reply_to(m,caption)
    except:
        msg = bot.reply_to(m,f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>")
    auto_del(m.chat.id,msg.message_id,delay=7)

# ========= فونت‌ساز =========
FONTS = [
    # انگلیسی Bold
    lambda txt: "".join({"a":"𝗮","b":"𝗯","c":"𝗰","d":"𝗱","e":"𝗲","f":"𝗳","g":"𝗴","h":"𝗵",
                         "i":"𝗶","j":"𝗷","k":"𝗸","l":"𝗹","m":"𝗺","n":"𝗻","o":"𝗼","p":"𝗽",
                         "q":"𝗾","r":"𝗿","s":"𝘀","t":"𝘁","u":"𝘂","v":"𝘃","w":"𝘄","x":"𝘅",
                         "y":"𝘆","z":"𝘇"}.get(ch.lower(),ch) for ch in txt),

    # انگلیسی Italic
    lambda txt: "".join({"a":"𝑎","b":"𝑏","c":"𝑐","d":"𝑑","e":"𝑒","f":"𝑓","g":"𝑔","h":"ℎ",
                         "i":"𝑖","j":"𝑗","k":"𝑘","l":"𝑙","m":"𝑚","n":"𝑛","o":"𝑜","p":"𝑝",
                         "q":"𝑞","r":"𝑟","s":"𝑠","t":"𝑡","u":"𝑢","v":"𝑣","w":"𝑤","x":"𝑥",
                         "y":"𝑦","z":"𝑧"}.get(ch.lower(),ch) for ch in txt),

    # فارسی استایل ۱
    lambda txt: "".join({"ا":"ٱ","ب":"بٰ","ت":"تہ","ث":"ثٰ","ج":"جـ","ح":"حہ","خ":"خہ",
                         "د":"دٰ","ذ":"ذٰ","ر":"رٰ","ز":"زٰ","س":"سٰ","ش":"شٰ","ص":"صٰ",
                         "ض":"ضٰ","ط":"طٰ","ظ":"ظٰ","ع":"عہ","غ":"غہ","ف":"فہ","ق":"قٰ",
                         "ک":"ڪ","گ":"گٰ","ل":"لہ","م":"مہ","ن":"نٰ","ه":"ﮬ","و":"ۆ","ی":"ۍ"}.get(ch,ch) for ch in txt),

    # فارسی استایل ۲
    lambda txt: "".join({"ا":"آ","ب":"ب̍","ت":"تۛ","ث":"ثہ","ج":"ج͠","ح":"حٰٰ","خ":"خ̐",
                         "د":"دُ","ذ":"ذٰ","ر":"ر͜","ز":"زٰ","س":"سہ","ش":"شہ","ص":"صہ",
                         "ض":"ضہ","ط":"طہ","ظ":"ظہ","ع":"عہ","غ":"غہ","ف":"فہ","ق":"ق͠",
                         "ک":"ڪہ","گ":"گہ","ل":"لہ","م":"مہ","ن":"نہ","ه":"ﮬ","و":"و͠",
                         "ی":"يہ"}.get(ch,ch) for ch in txt),
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
        try: res += style(name) + "\n"
        except: continue
    msg = bot.reply_to(m,res)
    auto_del(m.chat.id,msg.message_id,delay=15)

# ========= سیستم اصل =========
origins={}  # chat_id -> { user_id: اصل }

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m).startswith("ثبت اصل "))
def set_origin(m):
    if not is_admin(m.chat.id,m.from_user.id): return
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
        auto_del(m.chat.id,msg.message_id)
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
        auto_del(m.chat.id,msg.message_id)
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
        txt = custom or f"• سلام {name} به گروه {m.chat.title} خوش آمدید 🌻\n\n📆 {date}\n⏰ {time_}"
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
        auto_del(m.chat.id,msg.message_id,delay=7)# ========= سیستم اصل =========
origins={}  # chat_id -> { user_id: اصل }

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m).startswith("ثبت اصل "))
def set_origin(m):
    if not is_admin(m.chat.id,m.from_user.id): return
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
        auto_del(m.chat.id,msg.message_id)
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
        auto_del(m.chat.id,msg.message_id)
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
        bot.send_photo(m.chat.id, fal["file"], caption=fal["caption"])


# ========= فونت‌ساز =========
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
    auto_del(m.chat.id,msg.message_id,delay=15)# ========= استارت در پیوی (پنل سودو) =========
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
    except: pass


# ========= راهنمای سودو =========
@bot.callback_query_handler(func=lambda call: call.data.startswith("sudo_help"))
def sudo_help(call):
    if not is_sudo(call.from_user.id):
        return
    txt = HELP_TEXT_SUDO
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
    bot.send_message(call.message.chat.id, status)


# ========= لینک گروه‌ها =========
@bot.callback_query_handler(func=lambda call: call.data=="sudo_links")
def sudo_links(call):
    if not is_sudo(call.from_user.id): return
    if not joined_groups:
        return bot.send_message(call.message.chat.id,"❗ ربات در هیچ گروهی نیست.")
    txt="🔗 لینک گروه‌ها:\n"
    for gid in list(joined_groups)[:20]: # فقط 20 گروه اول
        try:
            link=bot.export_chat_invite_link(gid)
            chat=bot.get_chat(gid)
            txt+=f"▪️ {chat.title} → {link}\n"
        except: continue
    bot.send_message(call.message.chat.id,txt)# ========= لیست مدیران گروه =========
@bot.message_handler(func=lambda m: cmd_text(m)=="لیست مدیران گروه")
def admins_list(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        members = bot.get_chat_administrators(m.chat.id)
        names = [f"▪️ {u.user.first_name} ({u.user.id})" for u in members]
        txt = "👑 لیست مدیران گروه:\n\n" + "\n".join(names)
    except:
        txt = "❗ نتوانستم لیست مدیران گروه را بگیرم."
    msg = bot.reply_to(m, txt)
    auto_del(m.chat.id,msg.message_id,delay=20)

# ========= لیست سودوهای ربات =========
@bot.message_handler(func=lambda m: cmd_text(m)=="لیست سودوها")
def sudo_list(m):
    if not is_sudo(m.from_user.id): return
    if not sudo_ids:
        txt = "ℹ️ هیچ سودویی ثبت نشده."
    else:
        txt = "👑 لیست سودوها:\n\n" + "\n".join([f"▪️ {uid}" for uid in sudo_ids])
    msg = bot.reply_to(m, txt)
    auto_del(m.chat.id,msg.message_id,delay=15)# ========= ارسال هماهنگی (Broadcast) =========
waiting_broadcast = {}

@bot.callback_query_handler(func=lambda call: call.data=="sudo_bc")
def sudo_bc(call):
    if not is_sudo(call.from_user.id): return
    waiting_broadcast[call.from_user.id] = True
    bot.send_message(call.message.chat.id,"📢 پیام بعدی که بفرستی به همه گروه‌ها ارسال میشه.")

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and waiting_broadcast.get(m.from_user.id), content_types=['text','photo'])
def do_broadcast(m):
    waiting_broadcast[m.from_user.id] = False
    s = 0
    for gid in list(joined_groups):
        try:
            if m.content_type == "text":
                bot.send_message(gid, m.text)
            elif m.content_type == "photo":
                bot.send_photo(gid, m.photo[-1].file_id, caption=(m.caption or ""))
            s += 1
        except:
            continue
    msg = bot.reply_to(m, f"✅ پیام به {s} گروه ارسال شد.")
    auto_del(m.chat.id,msg.message_id,delay=10)# ========= متن‌های راهنما =========
HELP_TEXT_PUBLIC = """
📖 دستورات عمومی:

⏰ ساعت  
🆔 ایدی  
🎭 اصل من  
🎭 اصل (ریپلای)  
😂 جوک  
🔮 فال  
فونت [اسم]
"""

HELP_TEXT_ADMIN = """
📖 دستورات مدیران:

📊 آمار  
📎 لینک  
🎉 خوشامد روشن / خاموش  
✍️ خوشامد متن [متن]  
🖼 ثبت عکس (ریپلای روی عکس)  
🔒 قفل‌ها (با دستور یا پنل)  
🚫 بن / ✅ حذف بن   (ریپلای)  
🔕 سکوت / 🔊 حذف سکوت (ریپلای)  
⚠️ اخطار / حذف اخطار (ریپلای)  
👑 مدیر / ❌ حذف مدیر (ریپلای)  
📌 پن  
"""

HELP_TEXT_SUDO = """
📖 دستورات سودو:

🛠 وضعیت ربات  
📢 ارسال هماهنگی (Broadcast)  
➕ افزودن سودو [آیدی]  
➖ حذف سودو [آیدی]  
🚪 لفت بده  
📋 لیست مدیران ربات  
📊 آمار گروه‌ها  
🔗 لینک گروه‌ها  
🔴 خاموش / 🟢 روشن کردن ربات
"""

# ========= دستور راهنما =========
@bot.message_handler(func=lambda m: cmd_text(m)=="راهنما")
def show_help(m):
    if m.chat.type == "private" and is_sudo(m.from_user.id):
        bot.send_message(m.chat.id, HELP_TEXT_SUDO)
    elif is_admin(m.chat.id, m.from_user.id):
        bot.send_message(m.chat.id, HELP_TEXT_PUBLIC + "\n" + HELP_TEXT_ADMIN)
    else:
        bot.send_message(m.chat.id, HELP_TEXT_PUBLIC)# ========= ذخیره گروه‌هایی که ربات عضو میشه =========
joined_groups = set()

@bot.my_chat_member_handler()
def track_groups(upd):
    try:
        chat = upd.chat
        if chat and chat.type in ("group", "supergroup"):
            if upd.new_chat_member and upd.new_chat_member.status in ("member", "administrator"):
                joined_groups.add(chat.id)
            elif upd.new_chat_member and upd.new_chat_member.status == "left":
                joined_groups.discard(chat.id)
    except:
        pass


# ========= آمار گروه‌ها =========
@bot.callback_query_handler(func=lambda call: call.data=="sudo_stats")
def sudo_stats(call):
    if not is_sudo(call.from_user.id): return
    txt = f"📊 ربات هم‌اکنون در {len(joined_groups)} گروه عضو است."
    bot.send_message(call.message.chat.id, txt)


# ========= لینک گروه‌ها =========
@bot.callback_query_handler(func=lambda call: call.data=="sudo_links")
def sudo_links(call):
    if not is_sudo(call.from_user.id): return
    if not joined_groups:
        return bot.send_message(call.message.chat.id,"❗ ربات در هیچ گروهی عضو نیست.")
    
    txt="🔗 لینک گروه‌ها:\n"
    for gid in list(joined_groups)[:20]:  # فقط ۲۰ گروه اول
        try:
            link = bot.export_chat_invite_link(gid)
            chat = bot.get_chat(gid)
            txt += f"▪️ {chat.title} → {link}\n"
        except:
            continue
    bot.send_message(call.message.chat.id, txt)# ========= لیست مدیران ربات =========
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="لیست مدیران ربات")
def sudo_admins(m):
    if not sudo_ids:
        return bot.reply_to(m,"ℹ️ هیچ سودویی ثبت نشده.")
    txt = "👑 لیست مدیران ربات:\n\n"
    for i, uid in enumerate(sudo_ids, 1):
        txt += f"{i}. <code>{uid}</code>\n"
    bot.send_message(m.chat.id, txt)


# ========= ارسال همگانی =========
waiting_broadcast = {}

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ارسال")
def ask_bc(m):
    waiting_broadcast[m.from_user.id] = True
    msg = bot.reply_to(m,"📢 پیام بعدی که میفرستی به همه گروه‌ها ارسال میشه.")
    auto_del(m.chat.id,msg.message_id,delay=10)

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and waiting_broadcast.get(m.from_user.id), content_types=['text','photo'])
def do_bc(m):
    waiting_broadcast[m.from_user.id] = False
    s = 0
    for gid in list(joined_groups):
        try:
            if m.content_type == "text":
                bot.send_message(gid, m.text)
            elif m.content_type == "photo":
                bot.send_photo(gid, m.photo[-1].file_id, caption=(m.caption or ""))
            s += 1
        except:
            continue
    msg = bot.reply_to(m,f"✅ پیام به {s} گروه ارسال شد.")
    auto_del(m.chat.id,msg.message_id,delay=10)# ========= راهنما =========
HELP_TEXT_PUBLIC = """
📖 دستورات عمومی:

⏰ ساعت  
🆔 ایدی  
🎭 اصل من  
🎭 اصل (ریپلای)  
😂 جوک  
🔮 فال  
فونت [اسم]
"""

HELP_TEXT_ADMIN = """
📖 دستورات مدیران:

📊 آمار  
📎 لینک  
🎉 خوشامد روشن / خاموش  
✍️ خوشامد متن [متن]  
🖼 ثبت عکس (ریپلای روی عکس)  
🔒 قفل‌ها (با دستور یا پنل)  
🚫 بن / ✅ حذف بن   (ریپلای)  
🔕 سکوت / 🔊 حذف سکوت (ریپلای)  
⚠️ اخطار / حذف اخطار (ریپلای)  
👑 مدیر / ❌ حذف مدیر (ریپلای)  
📌 پنل قفل‌ها
"""

@bot.message_handler(func=lambda m: cmd_text(m)=="راهنما")
def help_cmd(m):
    if is_sudo(m.from_user.id):
        txt = HELP_TEXT_SUDO
    elif is_admin(m.chat.id,m.from_user.id):
        txt = HELP_TEXT_ADMIN
    else:
        txt = HELP_TEXT_PUBLIC
    msg = bot.reply_to(m, txt)
    auto_del(m.chat.id, msg.message_id, delay=25)

# ========= آمار (فقط مدیران) =========
@bot.message_handler(func=lambda m: cmd_text(m)=="آمار")
def group_stats(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        count = bot.get_chat_member_count(m.chat.id)
    except:
        count = "نامشخص"
    msg = bot.reply_to(m,f"📊 تعداد اعضای گروه: {count}")
    auto_del(m.chat.id,msg.message_id,delay=7)

# ========= لینک (فقط مدیران) =========
@bot.message_handler(func=lambda m: cmd_text(m)=="لینک")
def group_link(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        msg = bot.reply_to(m,f"📎 لینک گروه:\n{link}")
    except:
        msg = bot.reply_to(m,"❗ نتوانستم لینک بگیرم (بات باید ادمین با مجوز دعوت باشد).")
    auto_del(m.chat.id,msg.message_id,delay=10)# ========= جواب سودو (تست سریع) =========
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ربات")
def sudo_reply(m):
    msg = bot.reply_to(m,"جانم سودو 👑")
    auto_del(m.chat.id,msg.message_id,delay=7)


# ========= فیلتر وقتی ربات خاموش است =========
@bot.message_handler(func=lambda m: not bot_active)
def inactive_block(m):
    if is_sudo(m.from_user.id):
        bot.reply_to(m,"🔴 ربات در حالت خاموش است، فقط سودو می‌تواند روشن کند.")
    # پیام‌های دیگر را نادیده می‌گیرد


# ========= RUN =========
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True, timeout=30)
