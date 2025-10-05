# -*- coding: utf-8 -*-
import telebot, os, re, threading, time
from telebot import types
from datetime import datetime
import pytz

# ================== تنظیمات ==================
TOKEN   = os.environ.get("BOT_TOKEN")   # توکن ربات از Config Vars
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))  # آیدی سودو اصلی
SUPPORT_ID = "NOORI_NOOR"  # آیدی پشتیبانی (مثلاً: @NOORI_NOOR)

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
def is_sudo(uid): return uid in sudo_ids

def is_admin(chat_id, user_id):
    if is_sudo(user_id): return True
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator","creator")
    except:
        return False

def cmd_text(m):
    return (getattr(m,"text",None) or getattr(m,"caption",None) or "").strip()

def auto_del(chat_id,msg_id,delay=3):
    """حذف پیام ربات بعد از delay ثانیه"""
    def _():
        time.sleep(delay)
        try: bot.delete_message(chat_id,msg_id)
        except: pass
    threading.Thread(target=_).start()# ========= ذخیره گروه‌ها =========
joined_groups=set()
@bot.my_chat_member_handler()
def track_groups(upd):
    try:
        chat=upd.chat
        if chat and chat.type in ("group","supergroup"):
            joined_groups.add(chat.id)
    except:
        pass

# ========= راهنما با دکمه بستن =========
@bot.message_handler(func=lambda m: cmd_text(m)=="راهنما")
def help_cmd(m):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ بستن", callback_data=f"close:{m.chat.id}"))
    msg = bot.reply_to(m,HELP_TEXT,reply_markup=kb)
    # این یکی حذف نمیشه تا وقتی بستن رو بزنن

# ========= استارت توی پیوی =========
@bot.message_handler(commands=['start'])
def start_cmd(m):
    if m.chat.type == "private":
        kb = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/{bot.get_me().username}?startgroup=new")
        btn2 = types.InlineKeyboardButton("📞 پشتیبانی", url=f"https://t.me/{SUPPORT_ID}")
        kb.add(btn1, btn2)
        bot.send_message(m.chat.id,
            "👋 سلام!\n\nمن ربات مدیریت گروه هستم 🤖\nبرای شروع میتونی منو به گروهت اضافه کنی یا با پشتیبانی در تماس باشی.",
            reply_markup=kb
        )

# ========= خوشامد =========
welcome_enabled, welcome_texts, welcome_photos = {}, {}, {}

@bot.message_handler(content_types=['new_chat_members'])
def welcome(m):
    for u in m.new_chat_members:
        if not welcome_enabled.get(m.chat.id): continue
        name = u.first_name or ""
        date = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y/%m/%d")
        time_ = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%H:%M:%S")
        custom = welcome_texts.get(m.chat.id, "")
        txt = custom or f"• سلام {name} به گروه {m.chat.title} خوش آمدید 🌻\n\n📆 تاریخ : {date}\n⏰ ساعت : {time_}"
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
        auto_del(m.chat.id,msg.message_id)# ========= قفل‌ها =========
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

# ========= بن / سکوت =========
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="بن")
def ban_user(m):
    if is_admin(m.chat.id,m.from_user.id):
        try:
            bot.ban_chat_member(m.chat.id,m.reply_to_message.from_user.id)
            msg = bot.reply_to(m,"🚫 بن شد.")
        except:
            msg = bot.reply_to(m,"❗ نتوانستم بن کنم.")
        auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف بن")
def unban_user(m):
    if is_admin(m.chat.id,m.from_user.id):
        try:
            bot.unban_chat_member(m.chat.id,m.reply_to_message.from_user.id)
            msg = bot.reply_to(m,"✅ بن حذف شد.")
        except:
            msg = bot.reply_to(m,"❗ نتوانستم.")
        auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="سکوت")
def mute_user(m):
    if is_admin(m.chat.id,m.from_user.id):
        try:
            bot.restrict_chat_member(m.chat.id,m.reply_to_message.from_user.id,can_send_messages=False)
            msg = bot.reply_to(m,"🔕 سکوت شد.")
        except:
            msg = bot.reply_to(m,"❗ خطا")
        auto_del(m.chat.id,msg.message_id)

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
            msg = bot.reply_to(m,"❗ خطا")
        auto_del(m.chat.id,msg.message_id)

# ========= اخطار =========
warnings={}; MAX_WARNINGS=3
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="اخطار")
def warn_user(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid=m.reply_to_message.from_user.id
    warnings.setdefault(m.chat.id,{})
    warnings[m.chat.id][uid]=warnings[m.chat.id].get(uid,0)+1
    c=warnings[m.chat.id][uid]
    if c>=MAX_WARNINGS:
        try:
            bot.ban_chat_member(m.chat.id,uid)
            msg = bot.reply_to(m,"🚫 با ۳ اخطار بن شد.")
            warnings[m.chat.id][uid]=0
        except:
            msg = bot.reply_to(m,"❗ خطا در بن")
    else:
        msg = bot.reply_to(m,f"⚠️ اخطار {c}/{MAX_WARNINGS}")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف اخطار")
def reset_warn(m):
    if is_admin(m.chat.id,m.from_user.id):
        uid=m.reply_to_message.from_user.id
        if uid in warnings.get(m.chat.id,{}):
            warnings[m.chat.id][uid]=0
            msg = bot.reply_to(m,"✅ اخطارها حذف شد.")
        else:
            msg = bot.reply_to(m,"ℹ️ اخطاری نیست.")
        auto_del(m.chat.id,msg.message_id)# ========= مدیر / حذف مدیر =========
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
            msg = bot.reply_to(m,"👑 مدیر شد.")
        except:
            msg = bot.reply_to(m,"❗ خطا در ارتقا")
        auto_del(m.chat.id,msg.message_id)

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
            msg = bot.reply_to(m,"❗ خطا در حذف مدیر")
        auto_del(m.chat.id,msg.message_id)

# ========= پن =========
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="پن")
def pin(m):
    if is_admin(m.chat.id,m.from_user.id):
        try:
            bot.pin_chat_message(m.chat.id,m.reply_to_message.message_id,disable_notification=True)
            msg = bot.reply_to(m,"📌 پین شد.")
        except:
            msg = bot.reply_to(m,"❗ خطا")
        auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف پن")
def unpin(m):
    if is_admin(m.chat.id,m.from_user.id):
        try:
            bot.unpin_chat_message(m.chat.id,m.reply_to_message.message_id)
            msg = bot.reply_to(m,"❌ پین حذف شد.")
        except:
            msg = bot.reply_to(m,"❗ خطا")
        auto_del(m.chat.id,msg.message_id)

# ========= لقب و نقش =========
nicknames={}  # chat_id -> { user_id: nickname }

@bot.message_handler(func=lambda m: cmd_text(m)=="من کیم")
def whoami(m):
    role="عضو معمولی"
    if is_sudo(m.from_user.id): role="سودو 👑"
    elif is_admin(m.chat.id,m.from_user.id): role="مدیر 🛡"
    msg = bot.reply_to(m,f"شما {role} هستید.")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="این کیه")
def whois(m):
    uid=m.reply_to_message.from_user.id
    role="عضو معمولی"
    if is_sudo(uid): role="سودو 👑"
    elif is_admin(m.chat.id,uid): role="مدیر 🛡"
    nick = nicknames.get(m.chat.id,{}).get(uid)
    extra = f"\n🏷 لقب: {nick}" if nick else ""
    msg = bot.reply_to(m,f"این فرد {role} است.{extra}")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m).startswith("لقب "))
def set_nick(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid=m.reply_to_message.from_user.id
    nickname=cmd_text(m).replace("لقب ","",1).strip()
    if not nickname:
        msg = bot.reply_to(m,"❗ متنی وارد کن.")
        auto_del(m.chat.id,msg.message_id)
        return
    nicknames.setdefault(m.chat.id,{})[uid]=nickname
    msg = bot.reply_to(m,f"✅ لقب ذخیره شد: {nickname}")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="لقب")
def get_nick(m):
    uid=m.reply_to_message.from_user.id
    nickname=nicknames.get(m.chat.id,{}).get(uid)
    if nickname: 
        msg = bot.reply_to(m,f"🏷 لقب: {nickname}")
    else: 
        msg = bot.reply_to(m,"ℹ️ لقبی ذخیره نشده.")
    auto_del(m.chat.id,msg.message_id)# ========= پاکسازی =========
def bulk_delete(m,n):
    if not is_admin(m.chat.id,m.from_user.id): return
    d=0
    for i in range(m.message_id-1, m.message_id-n-1, -1):
        try:
            bot.delete_message(m.chat.id,i); d+=1
        except: pass
    msg = bot.reply_to(m,f"🧹 {d} پیام پاک شد.")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m)=="پاکسازی")
def clear_all(m): bulk_delete(m,9999)

@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف "))
def clear_custom(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try: num=int(cmd_text(m).split()[1])
    except: 
        msg = bot.reply_to(m,"❗ عدد معتبر وارد کن.")
        auto_del(m.chat.id,msg.message_id)
        return
    if num<=0: 
        msg = bot.reply_to(m,"❗ عدد باید بیشتر از صفر باشد.")
        auto_del(m.chat.id,msg.message_id)
        return
    if num>9999: num=9999
    bulk_delete(m,num)

# ========= وضعیت ربات =========
@bot.message_handler(func=lambda m: cmd_text(m)=="وضعیت ربات")
def bot_status(m):
    msg = bot.reply_to(m,"✅ ربات فعال است و بدون مشکل کار می‌کند.")
    auto_del(m.chat.id,msg.message_id)

# ========= مدیریت سودو =========
@bot.message_handler(func=lambda m: cmd_text(m).startswith("افزودن سودو "))
def add_sudo(m):
    if not is_sudo(m.from_user.id): return
    try: uid=int(cmd_text(m).split()[-1])
    except: 
        msg = bot.reply_to(m,"❗ آیدی نامعتبر")
        auto_del(m.chat.id,msg.message_id)
        return
    sudo_ids.add(uid)
    msg = bot.reply_to(m,f"✅ <code>{uid}</code> به سودوها اضافه شد.")
    auto_del(m.chat.id,msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف سودو "))
def del_sudo(m):
    if not is_sudo(m.from_user.id): return
    try: uid=int(cmd_text(m).split()[-1])
    except: 
        msg = bot.reply_to(m,"❗ آیدی نامعتبر")
        auto_del(m.chat.id,msg.message_id)
        return
    if uid==SUDO_ID:
        msg = bot.reply_to(m,"❗ سودوی اصلی حذف نمی‌شود.")
    elif uid in sudo_ids:
        sudo_ids.remove(uid)
        msg = bot.reply_to(m,f"✅ <code>{uid}</code> حذف شد.")
    else:
        msg = bot.reply_to(m,"ℹ️ این آیدی در سودوها نیست.")
    auto_del(m.chat.id,msg.message_id)

# ========= لفت بده =========
@bot.message_handler(func=lambda m: cmd_text(m)=="لفت بده")
def leave_cmd(m):
    if is_sudo(m.from_user.id):
        bot.send_message(m.chat.id,"به دستور سودو خارج می‌شوم 👋")
        try: bot.leave_chat(m.chat.id)
        except: pass

# ========= استارت توی پیوی =========
@bot.message_handler(commands=['start'])
def start_cmd(m):
    if m.chat.type == "private":
        kb = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/{bot.get_me().username}?startgroup=new")
        btn2 = types.InlineKeyboardButton("📞 پشتیبانی", url="https://t.me/NOORI_NOOR")
        kb.add(btn1, btn2)
        bot.send_message(m.chat.id,
            "👋 سلام!\n\nمن ربات مدیریت گروه هستم 🤖\nبرای شروع منو به گروهت اضافه کن یا با پشتیبانی در تماس باش.",
            reply_markup=kb
        )

# ========= پنل با دکمه بستن =========
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("close:"))
def cb_close(call):
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass# ========= فونت‌ساز =========
FONTS_EN = [
    "Ⓜ️ⓄⒽⒶⓂ️Ⓜ️ⒶⒹ",
    "𝐌𝐎𝐇𝐀𝐌𝐌𝐀𝐃",
    "𝑴𝑶𝑯𝑨𝑴𝑴𝑨𝑫",
    "𝗠𝗢𝗛𝗔𝗠𝗠𝗔𝗗",
    "𝕸𝕺𝕳𝕬𝕸𝕸𝕬𝕯",
    "мσнαммα∂",
    "ᴍᴏʜᴀᴍᴍᴀᴅ",
    "ＭＯＨＡＭＭＡＤ",
    "🅼🅾️🅷🅰️🅼🅼🅰️🅳",
    "🇲 🇴 🇭 🇦 🇲 🇲 🇦 🇩"
]

FONTS_FA = [
    "مَِــَِحَِـَِمَِــَِدَِ",
    "مـــحــمـــدّ",
    "مـ﹏ـحـ﹏ـمـ﹏ـد",
    "مـؒؔ◌‌‌ࢪحــٌ۝ؔؑـެِمـؒؔ◌‌‌ࢪـ‌َد",
    "مـ۪ٜـ۪ٜـ۪ٜـ۪ٜ‌حـ۪ٜـ۪ٜـ۪ٜـمـ۪ٜـ۪ٜـد۪ٜ",
    "م❈ۣۣـ🍁ـح❈ۣۣـ🍁ـم❈ۣۣـ🍁ـد❈ۣۣـ🍁ـ",
    "مـ෴ِْحـ෴ِْمـ෴ِْد",
    "مـًٍʘًٍʘـحـًٍʘًٍʘـمـًٍʘًٍʘـدََ",
    "مـْْـْْـْْ/ْْحْْـْْـْْـْْ/ْْمـْْـْْـْْ/ْْـْْـْْـدْْ/",
    "مـٍ‌ــٍ‌ــٍ‌❉حـٍ‌ــٍ‌ــٍ‌❉مـٍ‌ــٍ‌ــٍ‌❉دٍ‌❉"
]

@bot.message_handler(func=lambda m: cmd_text(m).startswith("فونت "))
def make_fonts(m):
    name = cmd_text(m).replace("فونت ","",1).strip()
    if not name: 
        msg = bot.reply_to(m,"❗ اسم رو هم بنویس")
        auto_del(m.chat.id,msg.message_id)
        return
    
    # انتخاب فونت‌های مناسب
    res = "🎨 فونت‌های خوشگل برای اسم:\n\n"
    if re.search(r'[a-zA-Z]', name):   # اگر انگلیسی بود
        for f in FONTS_EN:
            styled = f.replace("MOHAMMAD", name.upper())
            res += styled + "\n"
    else:  # اگر فارسی بود
        for f in FONTS_FA:
            styled = f.replace("محمد", name)
            res += styled + "\n"

    msg = bot.reply_to(m,res)
    auto_del(m.chat.id,msg.message_id,delay=12)

# ========= جواب سودو =========
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ربات")
def sudo_reply(m):
    msg = bot.reply_to(m,"جانم سودو 👑")
    auto_del(m.chat.id,msg.message_id)

# ========= RUN =========
print("🤖 Bot is running...")
bot.infinity_polling()
