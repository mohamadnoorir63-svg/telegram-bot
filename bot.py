# -*- coding: utf-8 -*-
import os, random
from datetime import datetime
import pytz
import telebot

# ================== تنظیمات ==================
TOKEN   = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
sudo_ids = {SUDO_ID}

# ================== کمکی ==================
def is_sudo(uid): return uid in sudo_ids
def is_admin(chat_id, user_id):
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator","creator")
    except: return False

def cmd_text(m): return (getattr(m,"text",None) or "").strip()

# ================== دستورات عمومی ==================
@bot.message_handler(func=lambda m: cmd_text(m)=="ساعت")
def cmd_time(m):
    now_utc=datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_teh=datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    bot.reply_to(m,f"⏰ UTC: {now_utc}\n⏰ تهران: {now_teh}")

@bot.message_handler(func=lambda m: cmd_text(m)=="آمار")
def cmd_stats(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    try: count=bot.get_chat_member_count(m.chat.id)
    except: count="نامشخص"
    bot.reply_to(m,f"📊 اعضای گروه: {count}")

@bot.message_handler(func=lambda m: cmd_text(m)=="ایدی")
def cmd_id(m):
    caption=f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>"
    try:
        photos=bot.get_user_profile_photos(m.from_user.id,limit=1)
        if photos.total_count>0:
            bot.send_photo(m.chat.id,photos.photos[0][-1].file_id,caption=caption)
        else: bot.reply_to(m,caption)
    except: bot.reply_to(m,caption)

# ================== جواب سودو ==================
SUDO_RESPONSES=["جونم قربان 😎","در خدمتم ✌️","ربات آماده‌ست 🚀","چه خبر رئیس؟ 🤖"]
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ربات")
def cmd_sudo(m): bot.reply_to(m,random.choice(SUDO_RESPONSES))

# ================== جوک و فال ==================
jokes=[]; fortunes=[]

def save_item(arr,m):
    if m.reply_to_message:
        if m.reply_to_message.text:
            arr.append({"type":"text","content":m.reply_to_message.text})
        elif m.reply_to_message.photo:
            arr.append({"type":"photo","file":m.reply_to_message.photo[-1].file_id,"caption":m.reply_to_message.caption or ""})

# جوک
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ثبت جوک")
def add_joke(m): save_item(jokes,m); bot.reply_to(m,"😂 جوک ذخیره شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="جوک")
def send_joke(m):
    if not jokes: return bot.reply_to(m,"❗ جوکی ثبت نشده")
    j=random.choice(jokes)
    if j["type"]=="text": bot.send_message(m.chat.id,j["content"])
    else: bot.send_photo(m.chat.id,j["file"],caption=j["caption"])

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="لیست جوک")
def list_joke(m):
    if not jokes: return bot.reply_to(m,"❗ جوکی ثبت نشده")
    txt="\n".join([f"{i+1}. {(j['content'][:40] if j['type']=='text' else '[عکس]' )}" for i,j in enumerate(jokes)])
    bot.reply_to(m,"😂 لیست جوک:\n"+txt)

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("حذف جوک "))
def del_joke(m):
    try:
        idx=int(cmd_text(m).split()[2])-1
        if 0<=idx<len(jokes): jokes.pop(idx); bot.reply_to(m,"✅ جوک حذف شد")
        else: bot.reply_to(m,"❗ شماره نامعتبر")
    except: bot.reply_to(m,"❗ فرمت: حذف جوک 2")

# فال
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ثبت فال")
def add_fal(m): save_item(fortunes,m); bot.reply_to(m,"🔮 فال ذخیره شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="فال")
def send_fal(m):
    if not fortunes: return bot.reply_to(m,"❗ فالی ثبت نشده")
    f=random.choice(fortunes)
    if f["type"]=="text": bot.send_message(m.chat.id,f["content"])
    else: bot.send_photo(m.chat.id,f["file"],caption=f["caption"])

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="لیست فال")
def list_fal(m):
    if not fortunes: return bot.reply_to(m,"❗ فالی ثبت نشده")
    txt="\n".join([f"{i+1}. {(f['content'][:40] if f['type']=='text' else '[عکس]' )}" for i,f in enumerate(fortunes)])
    bot.reply_to(m,"🔮 لیست فال:\n"+txt)

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("حذف فال "))
def del_fal(m):
    try:
        idx=int(cmd_text(m).split()[2])-1
        if 0<=idx<len(fortunes): fortunes.pop(idx); bot.reply_to(m,"✅ فال حذف شد")
        else: bot.reply_to(m,"❗ شماره نامعتبر")
    except: bot.reply_to(m,"❗ فرمت: حذف فال 2")

# ================== بن / سکوت / اخطار ==================
banned = {}
muted = {}
warnings = {}
MAX_WARNINGS = 3

def protect_user(chat_id, uid):
    if is_sudo(uid): return "⚡ این کاربر سودو است"
    try:
        member = bot.get_chat_member(chat_id, uid)
        if member.status == "creator": return "❗ صاحب گروه قابل مدیریت نیست"
    except: pass
    return None

# --- بن
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="بن")
def ban(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    protect=protect_user(m.chat.id,uid)
    if protect: return bot.reply_to(m,protect)
    try:
        bot.ban_chat_member(m.chat.id, uid)
        banned.setdefault(m.chat.id,set()).add(uid)
        bot.reply_to(m,"🚫 کاربر بن شد")
    except: bot.reply_to(m,"❗ خطا در بن")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف بن")
def unban(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    try:
        bot.unban_chat_member(m.chat.id, uid)
        banned.get(m.chat.id,set()).discard(uid)
        bot.reply_to(m,"✅ بن حذف شد")
    except: bot.reply_to(m,"❗ خطا در حذف بن")

@bot.message_handler(func=lambda m: cmd_text(m)=="لیست بن")
def list_ban(m):
    ids=banned.get(m.chat.id,set())
    if not ids: return bot.reply_to(m,"❗ لیست بن خالی است")
    txt="\n".join([f"▪️ {i}" for i in ids])
    bot.reply_to(m,"🚫 لیست بن:\n"+txt)

# --- سکوت
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="سکوت")
def mute(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid=m.reply_to_message.from_user.id
    protect=protect_user(m.chat.id,uid)
    if protect: return bot.reply_to(m,protect)
    try:
        bot.restrict_chat_member(m.chat.id,uid,can_send_messages=False)
        muted.setdefault(m.chat.id,set()).add(uid)
        bot.reply_to(m,"🔕 کاربر در سکوت قرار گرفت")
    except: bot.reply_to(m,"❗ خطا در سکوت")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف سکوت")
def unmute(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid=m.reply_to_message.from_user.id
    try:
        bot.restrict_chat_member(m.chat.id,uid,
            can_send_messages=True,can_send_media_messages=True,
            can_send_other_messages=True,can_add_web_page_previews=True)
        muted.get(m.chat.id,set()).discard(uid)
        bot.reply_to(m,"🔊 سکوت حذف شد")
    except: bot.reply_to(m,"❗ خطا در حذف سکوت")

@bot.message_handler(func=lambda m: cmd_text(m)=="لیست سکوت")
def list_mute(m):
    ids=muted.get(m.chat.id,set())
    if not ids: return bot.reply_to(m,"❗ لیست سکوت خالی است")
    txt="\n".join([f"▪️ {i}" for i in ids])
    bot.reply_to(m,"🔕 لیست سکوت:\n"+txt)

# --- اخطار
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="اخطار")
def warn(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid=m.reply_to_message.from_user.id
    protect=protect_user(m.chat.id,uid)
    if protect: return bot.reply_to(m,protect)
    warnings.setdefault(m.chat.id,{})
    warnings[m.chat.id][uid]=warnings[m.chat.id].get(uid,0)+1
    c=warnings[m.chat.id][uid]
    if c>=MAX_WARNINGS:
        try:
            bot.ban_chat_member(m.chat.id,uid)
            warnings[m.chat.id][uid]=0
            bot.reply_to(m,"🚫 کاربر با ۳ اخطار بن شد")
        except: bot.reply_to(m,"❗ خطا در بن با اخطار")
    else: bot.reply_to(m,f"⚠️ اخطار {c}/{MAX_WARNINGS}")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف اخطار")
def reset_warn(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid=m.reply_to_message.from_user.id
    warnings.get(m.chat.id,{}).pop(uid,None)
    bot.reply_to(m,"✅ اخطارها حذف شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="لیست اخطار")
def list_warn(m):
    ws=warnings.get(m.chat.id,{})
    if not ws: return bot.reply_to(m,"❗ لیست اخطار خالی است")
    txt="\n".join([f"▪️ {uid} — {c} اخطار" for uid,c in ws.items()])
    bot.reply_to(m,"⚠️ لیست اخطار:\n"+txt)

# ================== پاکسازی ==================
@bot.message_handler(func=lambda m: (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)) and cmd_text(m)=="پاکسازی")
def clear_all(m):
    deleted=0
    try:
        for i in range(1,201):
            bot.delete_message(m.chat.id,m.message_id-i)
            deleted+=1
    except: pass
    bot.reply_to(m,f"🧹 {deleted} پیام پاک شد")

@bot.message_handler(func=lambda m: (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)) and cmd_text(m).startswith("حذف "))
def delete_n(m):
    try:
        n=int(cmd_text(m).split()[1])
        deleted=0
        for i in range(1,n+1):
            bot.delete_message(m.chat.id,m.message_id-i)
            deleted+=1
        bot.reply_to(m,f"🗑 {deleted} پیام پاک شد")
    except: bot.reply_to(m,"❗ فرمت درست: حذف 10")# ================== قفل‌ها ==================
locks={k:{} for k in ["links","stickers","bots","photo","video","gif","file","music","voice","forward"]}
LOCK_MAP={
    "لینک":"links","استیکر":"stickers","ربات":"bots","عکس":"photo","ویدیو":"video",
    "گیف":"gif","فایل":"file","موزیک":"music","ویس":"voice","فوروارد":"forward"
}

@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل "))
def lock(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    key_fa=cmd_text(m).replace("قفل ","",1)
    key=LOCK_MAP.get(key_fa)
    if key:
        locks[key][m.chat.id]=True
        bot.reply_to(m,f"🔒 قفل {key_fa} فعال شد")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("باز کردن "))
def unlock(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    key_fa=cmd_text(m).replace("باز کردن ","",1)
    key=LOCK_MAP.get(key_fa)
    if key:
        locks[key][m.chat.id]=False
        bot.reply_to(m,f"🔓 قفل {key_fa} باز شد")

# enforce locks
@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation'])
def enforce(m):
    if is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id): return
    txt=m.text or ""
    try:
        if locks["links"].get(m.chat.id) and any(x in txt for x in ["http://","https://","t.me"]):
            bot.delete_message(m.chat.id,m.message_id)
        if locks["stickers"].get(m.chat.id) and m.sticker:
            bot.delete_message(m.chat.id,m.message_id)
        if locks["photo"].get(m.chat.id) and m.photo:
            bot.delete_message(m.chat.id,m.message_id)
        if locks["video"].get(m.chat.id) and m.video:
            bot.delete_message(m.chat.id,m.message_id)
        if locks["gif"].get(m.chat.id) and m.animation:
            bot.delete_message(m.chat.id,m.message_id)
        if locks["file"].get(m.chat.id) and m.document:
            bot.delete_message(m.chat.id,m.message_id)
        if locks["music"].get(m.chat.id) and m.audio:
            bot.delete_message(m.chat.id,m.message_id)
        if locks["voice"].get(m.chat.id) and m.voice:
            bot.delete_message(m.chat.id,m.message_id)
        if locks["forward"].get(m.chat.id) and (m.forward_from or m.forward_from_chat):
            bot.delete_message(m.chat.id,m.message_id)
    except: pass# ================== قفل‌ها ==================

# دیکشنری قفل‌ها
locks={k:{} for k in ["links","stickers","bots","photo","video","gif","file","music","voice","forward"]}
LOCK_MAP={
    "لینک":"links",
    "استیکر":"stickers",
    "ربات":"bots",
    "عکس":"photo",
    "ویدیو":"video",
    "گیف":"gif",
    "فایل":"file",
    "موزیک":"music",
    "ویس":"voice",
    "فوروارد":"forward"
}

# تابع گرفتن متن دستور
def cmd_text(m):
    return (getattr(m,"text",None) or "").strip()

# تابع بررسی سودو
def is_sudo(uid):
    return uid in sudo_ids

# تابع بررسی ادمین
def is_admin(chat_id, user_id):
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator","creator")
    except:
        return False

# نمایش پنل
@bot.message_handler(func=lambda m: cmd_text(m)=="پنل")
def locks_panel(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)):
        return
    kb=telebot.types.InlineKeyboardMarkup(row_width=2)
    for name,key in LOCK_MAP.items():
        st="🔒" if locks[key].get(m.chat.id) else "🔓"
        kb.add(telebot.types.InlineKeyboardButton(f"{st} {name}",callback_data=f"toggle:{key}:{m.chat.id}"))
    kb.add(telebot.types.InlineKeyboardButton("❌ بستن",callback_data=f"close:{m.chat.id}"))
    bot.reply_to(m,"🛠 پنل مدیریت قفل‌ها:",reply_markup=kb)

# تغییر وضعیت قفل
@bot.callback_query_handler(func=lambda c: c.data.startswith("toggle:"))
def cb_toggle(c):
    _,key,chat_id=c.data.split(":")
    chat_id=int(chat_id)
    if not (is_admin(chat_id,c.from_user.id) or is_sudo(c.from_user.id)):
        return
    locks[key][chat_id]=not locks[key].get(chat_id,False)
    st="فعال" if locks[key][chat_id] else "غیرفعال"
    bot.answer_callback_query(c.id,f"✅ قفل {st} شد")

# بستن پنل
@bot.callback_query_handler(func=lambda c: c.data.startswith("close:"))
def cb_close(c):
    try:
        bot.delete_message(c.message.chat.id,c.message.message_id)
    except:
        pass
    bot.answer_callback_query(c.id,"❌ پنل بسته شد")

# enforce (اجرای قفل‌ها)
@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation'])
def enforce(m):
    if is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id):
        return
    txt=m.text or ""
    try:
        if locks["links"].get(m.chat.id) and any(x in txt for x in ["http://","https://","t.me"]):
            bot.delete_message(m.chat.id,m.message_id)
        if locks["stickers"].get(m.chat.id) and m.sticker:
            bot.delete_message(m.chat.id,m.message_id)
        if locks["photo"].get(m.chat.id) and m.photo:
            bot.delete_message(m.chat.id,m.message_id)
        if locks["video"].get(m.chat.id) and m.video:
            bot.delete_message(m.chat.id,m.message_id)
        if locks["gif"].get(m.chat.id) and m.animation:
            bot.delete_message(m.chat.id,m.message_id)
        if locks["file"].get(m.chat.id) and m.document:
            bot.delete_message(m.chat.id,m.message_id)
        if locks["music"].get(m.chat.id) and m.audio:
            bot.delete_message(m.chat.id,m.message_id)
        if locks["voice"].get(m.chat.id) and m.voice:
            bot.delete_message(m.chat.id,m.message_id)
        if locks["forward"].get(m.chat.id) and (m.forward_from or m.forward_from_chat):
            bot.delete_message(m.chat.id,m.message_id)
    except:
        pass# ================== پنل قفل‌ها ==================
locks = {k:{} for k in ["links","stickers","bots","photo","video","gif","file","music","voice","forward"]}
LOCK_MAP = {
    "لینک":"links","استیکر":"stickers","ربات":"bots","عکس":"photo",
    "ویدیو":"video","گیف":"gif","فایل":"file","موزیک":"music",
    "ویس":"voice","فوروارد":"forward"
}

# دستور پنل
@bot.message_handler(func=lambda m: cmd_text(m)=="پنل")
def locks_panel(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    kb = types.InlineKeyboardMarkup(row_width=2)
    for name,key in LOCK_MAP.items():
        st = "🔒" if locks[key].get(m.chat.id) else "🔓"
        kb.add(types.InlineKeyboardButton(f"{st} {name}", callback_data=f"toggle:{key}:{m.chat.id}"))
    kb.add(types.InlineKeyboardButton("❌ بستن", callback_data=f"close:{m.chat.id}"))
    bot.reply_to(m,"🛠 پنل مدیریت قفل‌ها:", reply_markup=kb)

# هندلر کلیک روی دکمه‌ها
@bot.callback_query_handler(func=lambda c: c.data.startswith("toggle:") or c.data.startswith("close:"))
def cb_handler(c):
    if c.data.startswith("toggle:"):
        _,key,chat_id = c.data.split(":")
        chat_id = int(chat_id)
        if not (is_admin(chat_id,c.from_user.id) or is_sudo(c.from_user.id)):
            return bot.answer_callback_query(c.id,"⛔ فقط مدیر یا سودو!")
        # تغییر وضعیت قفل
        locks[key][chat_id] = not locks[key].get(chat_id, False)
        st = "فعال" if locks[key][chat_id] else "غیرفعال"
        bot.answer_callback_query(c.id, f"✅ قفل {st} شد")

    elif c.data.startswith("close:"):
        try: bot.delete_message(c.message.chat.id, c.message.message_id)
        except: pass
        bot.answer_callback_query(c.id,"❌ پنل بسته شد")# ================== دستورات متنی قفل ==================
@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل "))
def lock(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    key_fa = cmd_text(m).replace("قفل ","",1)
    key = LOCK_MAP.get(key_fa)
    if key:
        locks[key][m.chat.id] = True
        bot.reply_to(m,f"🔒 قفل {key_fa} فعال شد")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("باز کردن "))
def unlock(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    key_fa = cmd_text(m).replace("باز کردن ","",1)
    key = LOCK_MAP.get(key_fa)
    if key:
        locks[key][m.chat.id] = False
        bot.reply_to(m,f"🔓 قفل {key_fa} باز شد")# ================== اجرای ربات ==================
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True, timeout=30)
