# -*- coding: utf-8 -*-
import os, time, threading, random
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

# جواب سودو به "ربات"
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

# ================== راهنما ==================
HELP_TEXT = """
📖 <b>لیست دستورات:</b>

⏰ ساعت | 🆔 ایدی 
📊 آمار | 📎 لینک 
🤖 وضعیت ربات

🎉 خوشامد روشن/خاموش
✍️ خوشامد متن [متن]
🖼 ثبت عکس (ریپلای)

🔒 قفل‌ها (پنل)
🚫 بن | ✅ حذف بن
🔕 سکوت | 🔊 حذف سکوت
⚠️ اخطار | حذف اخطار

👑 مدیر | ❌ حذف مدیر
📌 پن | ❌ حذف پن
🧹 پاکسازی | حذف [عدد]

📋 لیست مدیران گروه
⚡ لیست سودو

📢 ارسال (فقط سودو)
"""

@bot.message_handler(func=lambda m: cmd_text(m)=="راهنما")
def help_cmd(m):
    if m.chat.type!="private" and not is_admin(m.chat.id,m.from_user.id): return
    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ بستن",callback_data="close_help"))
    bot.send_message(m.chat.id,HELP_TEXT,reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data=="close_help")
def close_help(c):
    try: bot.delete_message(c.message.chat.id,c.message.message_id)
    except: pass
    bot.answer_callback_query(c.id,"❌ بسته شد")# ================== قفل‌ها ==================
locks={k:{} for k in ["links","stickers","bots","photo","video","gif","file","music","voice","forward"]}
LOCK_MAP={"لینک":"links","استیکر":"stickers","ربات":"bots","عکس":"photo","ویدیو":"video",
          "گیف":"gif","فایل":"file","موزیک":"music","ویس":"voice","فوروارد":"forward"}

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
    if not is_admin(chat_id,c.from_user.id): return
    locks[key][chat_id]=not locks[key].get(chat_id,False)
    st="فعال" if locks[key][chat_id] else "غیرفعال"
    bot.answer_callback_query(c.id,f"✅ قفل {st} شد")

@bot.callback_query_handler(func=lambda c: c.data.startswith("close:"))
def cb_close(c):
    try: bot.delete_message(c.message.chat.id,c.message.message_id)
    except: pass
    bot.answer_callback_query(c.id,"❌ پنل بسته شد")

# enforce locks
@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation'])
def enforce(m):
    if is_admin(m.chat.id,m.from_user.id): return
    txt=m.text or ""
    try:
        if locks["links"].get(m.chat.id) and any(x in txt for x in ["http://","https://","t.me"]): bot.delete_message(m.chat.id,m.message_id)
        if locks["stickers"].get(m.chat.id) and m.sticker: bot.delete_message(m.chat.id,m.message_id)
        if locks["photo"].get(m.chat.id) and m.photo: bot.delete_message(m.chat.id,m.message_id)
        if locks["video"].get(m.chat.id) and m.video: bot.delete_message(m.chat.id,m.message_id)
        if locks["gif"].get(m.chat.id) and m.animation: bot.delete_message(m.chat.id,m.message_id)
        if locks["file"].get(m.chat.id) and m.document: bot.delete_message(m.chat.id,m.message_id)
        if locks["music"].get(m.chat.id) and m.audio: bot.delete_message(m.chat.id,m.message_id)
        if locks["voice"].get(m.chat.id) and m.voice: bot.delete_message(m.chat.id,m.message_id)
        if locks["forward"].get(m.chat.id) and (m.forward_from or m.forward_from_chat): bot.delete_message(m.chat.id,m.message_id)
    except: pass

# ================== بن / سکوت / اخطار ==================
warnings={}; MAX_WARNINGS=3

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="بن")
def ban(m):
    if is_admin(m.chat.id,m.from_user.id):
        try:
            bot.ban_chat_member(m.chat.id,m.reply_to_message.from_user.id)
            bot.reply_to(m,"🚫 کاربر بن شد")
        except: bot.reply_to(m,"❗ خطا در بن")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف بن")
def unban(m):
    if is_admin(m.chat.id,m.from_user.id):
        try:
            bot.unban_chat_member(m.chat.id,m.reply_to_message.from_user.id)
            bot.reply_to(m,"✅ بن حذف شد")
        except: bot.reply_to(m,"❗ خطا در حذف بن")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="سکوت")
def mute(m):
    if is_admin(m.chat.id,m.from_user.id):
        try:
            bot.restrict_chat_member(m.chat.id,m.reply_to_message.from_user.id,can_send_messages=False)
            bot.reply_to(m,"🔕 کاربر در سکوت قرار گرفت")
        except: bot.reply_to(m,"❗ خطا در سکوت")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف سکوت")
def unmute(m):
    if is_admin(m.chat.id,m.from_user.id):
        try:
            bot.restrict_chat_member(
                m.chat.id,m.reply_to_message.from_user.id,
                can_send_messages=True,can_send_media_messages=True,
                can_send_other_messages=True,can_add_web_page_previews=True
            )
            bot.reply_to(m,"🔊 سکوت حذف شد")
        except: bot.reply_to(m,"❗ خطا در حذف سکوت")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="اخطار")
def warn(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid=m.reply_to_message.from_user.id
    warnings.setdefault(m.chat.id,{})
    warnings[m.chat.id][uid]=warnings[m.chat.id].get(uid,0)+1
    c=warnings[m.chat.id][uid]
    if c>=MAX_WARNINGS:
        bot.ban_chat_member(m.chat.id,uid)
        warnings[m.chat.id][uid]=0
        bot.reply_to(m,"🚫 کاربر با ۳ اخطار بن شد")
    else: bot.reply_to(m,f"⚠️ اخطار {c}/{MAX_WARNINGS}")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف اخطار")
def reset_warn(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid=m.reply_to_message.from_user.id
    warnings.get(m.chat.id,{}).pop(uid,None)
    bot.reply_to(m,"✅ اخطارها حذف شد")

# ================== مدیریت ==================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="مدیر")
def promote(m):
    if is_admin(m.chat.id,m.from_user.id):
        bot.promote_chat_member(
            m.chat.id,m.reply_to_message.from_user.id,
            can_manage_chat=True,can_delete_messages=True,
            can_restrict_members=True,can_pin_messages=True,
            can_invite_users=True,can_manage_video_chats=True
        )
        bot.reply_to(m,"👑 کاربر مدیر شد")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف مدیر")
def demote(m):
    if is_admin(m.chat.id,m.from_user.id):
        bot.promote_chat_member(
            m.chat.id,m.reply_to_message.from_user.id,
            can_manage_chat=False,can_delete_messages=False,
            can_restrict_members=False,can_pin_messages=False,
            can_invite_users=False,can_manage_video_chats=False
        )
        bot.reply_to(m,"❌ مدیر حذف شد")

# ================== پاکسازی ==================
@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m)=="پاکسازی")
def clear_all(m):
    deleted=0
    try:
        for i in range(1,200):
            bot.delete_message(m.chat.id,m.message_id-i)
            deleted+=1
    except: pass
    bot.reply_to(m,f"🧹 {deleted} پیام پاک شد")

@bot.message_handler(func=lambda m: is_admin(m.chat.id,m.from_user.id) and cmd_text(m).startswith("حذف "))
def delete_n(m):
    try:
        n=int(cmd_text(m).split()[1])
        deleted=0
        for i in range(1,n+1):
            bot.delete_message(m.chat.id,m.message_id-i)
            deleted+=1
        bot.reply_to(m,f"🗑 {deleted} پیام پاک شد")
    except:
        bot.reply_to(m,"❗ دستور درست نیست. مثال: حذف 10")

# ================== لیست‌ها ==================
@bot.message_handler(func=lambda m: cmd_text(m)=="لیست مدیران گروه")
def admins_list(m):
    if is_admin(m.chat.id,m.from_user.id):
        admins=bot.get_chat_administrators(m.chat.id)
        txt="👑 مدیران گروه:\n"+"\n".join([f"▪️ {a.user.first_name} — {a.user.id}" for a in admins])
        bot.reply_to(m,txt)

@bot.message_handler(func=lambda m: cmd_text(m)=="لیست سودو")
def sudo_list(m):
    if is_sudo(m.from_user.id):
        txt="⚡ سودوها:\n"+"\n".join([str(x) for x in sudo_ids])
        bot.reply_to(m,txt)

# ================== ذخیره گروه‌ها و ارسال همگانی ==================
GROUPS_FILE="groups.txt"
def save_group(chat_id):
    try:
        groups=set()
        if os.path.exists(GROUPS_FILE):
            with open(GROUPS_FILE,"r") as f: groups=set([int(x.strip()) for x in f if x.strip()])
        groups.add(chat_id)
        with open(GROUPS_FILE,"w") as f: f.write("\n".join(str(x) for x in groups))
    except: pass

@bot.message_handler(content_types=['new_chat_members','text'])
def save_groups_handler(m):
    if m.chat.type in ["supergroup","group"]:
        save_group(m.chat.id)

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("ارسال "))
def broadcast(m):
    text=cmd_text(m).replace("ارسال ","",1)
    sent,failed=0,0
    if not os.path.exists(GROUPS_FILE): return bot.reply_to(m,"❗ گروهی ذخیره نشده")
    with open(GROUPS_FILE,"r") as f: groups=[int(x.strip()) for x in f if x.strip()]
    for gid in groups:
        try: bot.send_message(gid,text); sent+=1
        except: failed+=1
    bot.reply_to(m,f"📢 ارسال تمام شد\n✅ موفق: {sent}\n❌ ناموفق: {failed}")

# ================== پنل پیوی برای ممبر ==================
@bot.message_handler(commands=['start'])
def start_cmd(m):
    if m.chat.type!="private": 
        save_group(m.chat.id); return
    kb=types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("➕ افزودن ربات به گروه", url=f"https://t.me/{bot.get_me().username}?startgroup=new"))
    kb.add(types.InlineKeyboardButton("📞 پشتیبانی", url=f"https://t.me/{SUPPORT_ID}"))
    kb.add(types.InlineKeyboardButton("ℹ️ توضیحات ربات", callback_data="about"))
    kb.add(types.InlineKeyboardButton("❌ بستن", callback_data="close_start"))
    txt=("👋 سلام!\n\nمن ربات مدیریت گروه هستم 🤖\n\nاز دکمه‌های زیر استفاده کن 👇")
    bot.send_message(m.chat.id,txt,reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data=="about")
def cb_about(c):
    txt=("ℹ️ <b>امکانات ربات:</b>\n\n"
         "• خوشامدگویی\n"
         "• قفل لینک / مدیا\n"
         "• بن، سکوت، اخطار\n"
         "• اصل اعضا\n"
         "• جوک و فال\n"
         "• ارتقا مدیر / پاکسازی\n"
         "• ارسال همگانی")
    bot.send_message(c.message.chat.id,txt)
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data=="close_start")
def cb_close_start(c):
    try: bot.delete_message(c.message.chat.id,c.message.message_id)
    except: pass
    bot.answer_callback_query(c.id,"❌ بسته شد")

# ================== اجرا ==================
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True,timeout=30)
