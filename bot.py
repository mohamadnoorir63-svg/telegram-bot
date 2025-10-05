# -*- coding: utf-8 -*-
import telebot, os, re, threading, time
from telebot import types
from datetime import datetime
import pytz

# ================== تنظیمات ==================
TOKEN   = os.environ.get("BOT_TOKEN")   # توکن ربات از Config Vars
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))  # آیدی سودو اصلی
SUPPORT_ID = "NOORI_NOOR"  # آیدی پشتیبانی

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
# ============================================

HELP_TEXT = """
📖 لیست دستورات:

⏰ ساعت | 🆔 ایدی | 📊 آمار | 📎 لینک
🛠 وضعیت ربات
🎉 خوشامد روشن / خاموش
✍️ خوشامد متن [متن]
🖼 ثبت عکس (روی عکس ریپلای کن)
🔒 قفل لینک / باز کردن لینک
🧷 قفل استیکر / باز کردن استیکر
🤖 قفل ربات / باز کردن ربات
🚫 قفل تبچی / باز کردن تبچی
🔐 قفل گروه / باز کردن گروه
🖼 قفل عکس / باز کردن عکس
🎥 قفل ویدیو / باز کردن ویدیو
🎭 قفل گیف / باز کردن گیف
📎 قفل فایل / باز کردن فایل
🎶 قفل موزیک / باز کردن موزیک
🎙 قفل ویس / باز کردن ویس
🔄 قفل فوروارد / باز کردن فوروارد
🚫 بن / ✅ حذف بن   (ریپلای)
🔕 سکوت / 🔊 حذف سکوت (ریپلای)
⚠️ اخطار / حذف اخطار (ریپلای)
👑 مدیر / ❌ حذف مدیر (ریپلای)
📌 پن / ❌ حذف پن    (ریپلای)
📋 لیست مدیران گروه | 📋 لیست مدیران ربات
🧹 پاکسازی              (تا ۹۹۹۹ پیام)
🧹 حذف [عدد]           (پاکسازی تعداد مشخص)
📢 ارسال                (فقط سودو)
➕ افزودن سودو [آیدی]
➖ حذف سودو [آیدی]
🚪 لفت بده              (فقط سودو)
🧑‍🤝‍🧑 من کیم
🧾 این کیه (ریپلای)
🏷 لقب [متن] (ریپلای) | لقب
فونت [اسم] (برای نوشتن خوشگل)

برای باز کردن پنل قفل‌ها: «پنل» در گروه
"""

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
    """حذف پیام ربات بعد از delay ثانیه"""
    def _():
        time.sleep(delay)
        try: bot.delete_message(chat_id,msg_id)
        except: pass
    threading.Thread(target=_).start()# ========= فونت‌ساز =========
FONTS = [
    # انگلیسی — حالت Bold
    lambda txt: "".join({"a":"ᗩ","b":"ᗷ","c":"ᑕ","d":"ᗪ","e":"E","f":"ᖴ","g":"G","h":"ᕼ",
                         "i":"I","j":"ᒍ","k":"K","l":"ᒪ","m":"ᗰ","n":"ᑎ","o":"O","p":"ᑭ",
                         "q":"ᑫ","r":"ᖇ","s":"ᔕ","t":"T","u":"ᑌ","v":"ᐯ","w":"ᗯ","x":"᙭",
                         "y":"Y","z":"ᘔ"}.get(ch.lower(),ch) for ch in txt),
    # انگلیسی — حالت Fancy
    lambda txt: "".join({"a":"𝒜","b":"𝒝","c":"𝒞","d":"𝒟","e":"𝓔","f":"𝓕","g":"𝒢","h":"𝒽",
                         "i":"𝒾","j":"𝒥","k":"𝒦","l":"𝓁","m":"𝓂","n":"𝓃","o":"𝑜","p":"𝓅",
                         "q":"𝓆","r":"𝓇","s":"𝓈","t":"𝓉","u":"𝓊","v":"𝓋","w":"𝓌","x":"𝓍",
                         "y":"𝓎","z":"𝓏"}.get(ch.lower(),ch) for ch in txt),
    # فارسی — تزئینی
    lambda txt: "".join({"ا":"آ","ب":"ب̍","ت":"تۛ","ث":"ثہ","ج":"ج͠","ح":"حٰٰ","خ":"خ̐",
                         "د":"دُ","ذ":"ذٰ","ر":"ر͜","ز":"زٰ","س":"سہ","ش":"شہ","ص":"صہ",
                         "ض":"ضہ","ط":"طہ","ظ":"ظہ","ع":"عہ","غ":"غہ","ف":"فہ","ق":"ق͠",
                         "ك":"ڪہ","ل":"لہ","م":"مہ","ن":"نہ","ه":"ﮬ","و":"و͠","ي":"يہ"}.get(ch, ch) for ch in txt),
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
    auto_del(m.chat.id,msg.message_id,delay=15)# ========= خوشامد =========
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
        auto_del(m.chat.id,msg.message_id,delay=7)

@bot.message_handler(func=lambda m: cmd_text(m)=="خوشامد خاموش")
def w_off(m):
    if is_admin(m.chat.id,m.from_user.id):
        welcome_enabled[m.chat.id]=False
        msg = bot.reply_to(m,"❌ خوشامد خاموش شد.")
        auto_del(m.chat.id,msg.message_id,delay=7)

@bot.message_handler(func=lambda m: cmd_text(m).startswith("خوشامد متن"))
def w_txt(m):
    if is_admin(m.chat.id,m.from_user.id):
        welcome_texts[m.chat.id]=cmd_text(m).replace("خوشامد متن","",1).strip()
        msg = bot.reply_to(m,"✍️ متن خوشامد ذخیره شد.")
        auto_del(m.chat.id,msg.message_id,delay=7)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="ثبت عکس")
def w_photo(m):
    if is_admin(m.chat.id,m.from_user.id) and m.reply_to_message.photo:
        welcome_photos[m.chat.id]=m.reply_to_message.photo[-1].file_id
        msg = bot.reply_to(m,"🖼 عکس خوشامد ذخیره شد.")
        auto_del(m.chat.id,msg.message_id,delay=7)

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
            auto_del(m.chat.id,msg.message_id,delay=7)
            return
    locks[key][m.chat.id]=enable
    msg = bot.reply_to(m,f"{'🔒' if enable else '🔓'} {name} {'فعال شد' if enable else 'آزاد شد'}")
    auto_del(m.chat.id,msg.message_id,delay=7)

# ========= پنل شیشه‌ای =========
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
    bot.reply_to(m,"🛠 پنل مدیریت قفل‌ها:",reply_markup=kb)

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
    # آپدیت پنل
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
    except: pass# ========= ساعت (برای همه) =========
@bot.message_handler(func=lambda m: cmd_text(m)=="ساعت")
def time_cmd(m):
    now_utc = datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_teh = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    msg = bot.reply_to(m, f"⏰ ساعت UTC: {now_utc}\n⏰ ساعت تهران: {now_teh}")
    auto_del(m.chat.id,msg.message_id,delay=7)

# ========= ایدی (برای همه) =========
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
    auto_del(m.chat.id,msg.message_id,delay=7)

# ========= آمار (فقط مدیران و سودو) =========
@bot.message_handler(func=lambda m: cmd_text(m)=="آمار")
def stats(m):
    if not is_admin(m.chat.id,m.from_user.id):
        return
    try: 
        count = bot.get_chat_member_count(m.chat.id)
    except: 
        count = "نامشخص"
    msg = bot.reply_to(m, f"📊 اعضای گروه: {count}")
    auto_del(m.chat.id,msg.message_id,delay=7)

# ========= لینک گروه (فقط مدیران و سودو) =========
@bot.message_handler(func=lambda m: cmd_text(m)=="لینک")
def group_link(m):
    if not is_admin(m.chat.id,m.from_user.id):
        return
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        msg = bot.reply_to(m, f"📎 لینک گروه:\n{link}")
    except:
        msg = bot.reply_to(m, "❗ نتوانستم لینک بگیرم. (بات باید ادمین با مجوز دعوت باشد)")
    auto_del(m.chat.id,msg.message_id,delay=7)# ========= بن / سکوت =========
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
            msg = bot.reply_to(m,"🔕 سکوت شد.")
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
        auto_del(m.chat.id,msg.message_id,delay=7)

# ========= لقب و نقش =========
nicknames={}  # chat_id -> { user_id: nickname }

@bot.message_handler(func=lambda m: cmd_text(m)=="من کیم")
def whoami(m):
    role="عضو معمولی"
    if is_sudo(m.from_user.id): role="سودو 👑"
    elif is_admin(m.chat.id,m.from_user.id): role="مدیر 🛡"
    msg = bot.reply_to(m,f"شما {role} هستید.")
    auto_del(m.chat.id,msg.message_id,delay=7)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="این کیه")
def whois(m):
    uid = m.reply_to_message.from_user.id
    role="عضو معمولی"
    if is_sudo(uid): role="سودو 👑"
    elif is_admin(m.chat.id,uid): role="مدیر 🛡"
    nick = nicknames.get(m.chat.id,{}).get(uid)
    extra = f"\n🏷 لقب: {nick}" if nick else ""
    msg = bot.reply_to(m,f"این فرد {role} است.{extra}")
    auto_del(m.chat.id,msg.message_id,delay=7)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m).startswith("لقب "))
def set_nick(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    nickname = cmd_text(m).replace("لقب ","",1).strip()
    if not nickname:
        msg = bot.reply_to(m,"❗ متنی وارد کن.")
    else:
        nicknames.setdefault(m.chat.id,{})[uid] = nickname
        msg = bot.reply_to(m,f"✅ لقب ذخیره شد: {nickname}")
    auto_del(m.chat.id,msg.message_id,delay=7)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="لقب")
def get_nick(m):
    uid = m.reply_to_message.from_user.id
    nickname = nicknames.get(m.chat.id,{}).get(uid)
    msg = bot.reply_to(m,f"🏷 لقب: {nickname}" if nickname else "ℹ️ لقبی ذخیره نشده.")
    auto_del(m.chat.id,msg.message_id,delay=7)# ========= پنل مدیریتی =========
@bot.message_handler(func=lambda m: cmd_text(m)=="پنل")
def locks_panel(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for name,key in LOCK_MAP.items():
        status = "🔒" if locks[key].get(m.chat.id) else "🔓"
        btns.append(types.InlineKeyboardButton(f"{status} {name}", callback_data=f"toggle:{key}:{m.chat.id}"))
    kb.add(*btns)
    kb.add(types.InlineKeyboardButton("❌ بستن", callback_data=f"close:{m.chat.id}"))
    msg = bot.reply_to(m,"🛠 پنل مدیریت قفل‌ها:", reply_markup=kb)
    auto_del(m.chat.id,msg.message_id,delay=30)  # پنل تا 30 ثانیه می‌مونه

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle:"))
def cb_toggle(call):
    try:
        _, key, chat_id = call.data.split(":")
        chat_id = int(chat_id)
        if not is_admin(chat_id, call.from_user.id):
            return bot.answer_callback_query(call.id, "❌ فقط مدیران می‌توانند تغییر دهند.", show_alert=True)
        current = locks[key].get(chat_id, False)
        locks[key][chat_id] = not current
        bot.answer_callback_query(call.id, f"{'فعال' if locks[key][chat_id] else 'غیرفعال'} شد ✅")

        # آپدیت پنل
        kb = types.InlineKeyboardMarkup(row_width=2)
        btns = []
        for name,k in LOCK_MAP.items():
            st = "🔒" if locks[k].get(chat_id) else "🔓"
            btns.append(types.InlineKeyboardButton(f"{st} {name}", callback_data=f"toggle:{k}:{chat_id}"))
        kb.add(*btns)
        kb.add(types.InlineKeyboardButton("❌ بستن", callback_data=f"close:{chat_id}"))
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=kb)
    except:
        bot.answer_callback_query(call.id, "⚠️ خطا در تغییر وضعیت")

@bot.callback_query_handler(func=lambda call: call.data.startswith("close:"))
def cb_close(call):
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass# ========= استارت در پیوی =========
@bot.message_handler(commands=['start'])
def start_cmd(m):
    if m.chat.type == "private":
        kb = types.InlineKeyboardMarkup(row_width=2)
        # افزودن به گروه
        btn1 = types.InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/{bot.get_me().username}?startgroup=new")
        # پشتیبانی (آیدی خودت اینجا بذار)
        btn2 = types.InlineKeyboardButton("📞 پشتیبانی", url="https://t.me/NOORI_NOOR")
        kb.add(btn1, btn2)

        bot.send_message(
            m.chat.id,
            "👋 سلام!\n\n"
            "من ربات مدیریت گروه هستم 🤖\n"
            "میتونی منو به گروهت اضافه کنی یا برای راهنمایی بیشتر با پشتیبانی در تماس باشی.",
            reply_markup=kb
        )# ========= دستورات عمومی (برای همه) =========
@bot.message_handler(func=lambda m: cmd_text(m)=="ساعت")
def time_cmd(m):
    now_utc=datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_teh=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    msg = bot.reply_to(m,f"⏰ ساعت UTC: {now_utc}\n⏰ ساعت تهران: {now_teh}")
    auto_del(m.chat.id,msg.message_id,delay=7)

@bot.message_handler(func=lambda m: cmd_text(m)=="ایدی")
def id_cmd(m):
    try:
        photos=bot.get_user_profile_photos(m.from_user.id,limit=1)
        caption=f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>"
        if photos.total_count>0:
            msg print("🤖 Bot is running...")
bot.infinity_polling()
