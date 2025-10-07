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

# ================== کمکی‌ها ==================
def is_sudo(uid): return uid in sudo_ids
def is_admin(chat_id, user_id):
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator", "creator") or is_sudo(user_id)
    except: return False

def cmd_text(m): return (getattr(m,"text",None) or "").strip()

# ================== دستورات عمومی ==================
@bot.message_handler(func=lambda m: cmd_text(m)=="ساعت")
def cmd_time(m):
    now_utc = datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_teh = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    bot.reply_to(m, f"⏰ UTC: {now_utc}\n⏰ تهران: {now_teh}")

@bot.message_handler(func=lambda m: cmd_text(m)=="آمار")
def cmd_stats(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try: count = bot.get_chat_member_count(m.chat.id)
    except: count = "نامشخص"
    bot.reply_to(m, f"📊 اعضای گروه: {count}")

@bot.message_handler(func=lambda m: cmd_text(m)=="ایدی")
def cmd_id(m):
    caption=f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>"
    try:
        photos=bot.get_user_profile_photos(m.from_user.id,limit=1)
        if photos.total_count>0:
            bot.send_photo(m.chat.id,photos.photos[0][-1].file_id,caption=caption)
        else: bot.reply_to(m,caption)
    except: bot.reply_to(m,caption)

# ================== جواب سودو «ربات» ==================
SUDO_RESPONSES = ["جونم قربان 😎","در خدمتم ✌️","ربات آماده‌ست 🚀","چه خبر رئیس؟ 🤖"]
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ربات")
def cmd_sudo(m):
    bot.reply_to(m, random.choice(SUDO_RESPONSES))

# ================== جوک ==================
jokes=[]
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ثبت جوک")
def joke_add(m):
    if m.reply_to_message:
        if m.reply_to_message.text:
            jokes.append({"type":"text","content":m.reply_to_message.text})
        elif m.reply_to_message.photo:
            jokes.append({"type":"photo","file":m.reply_to_message.photo[-1].file_id,"caption":m.reply_to_message.caption or ""})
        bot.reply_to(m,"😂 جوک ذخیره شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="جوک")
def joke_send(m):
    if not jokes: return bot.reply_to(m,"❗ جوکی ثبت نشده")
    j=random.choice(jokes)
    if j["type"]=="text": bot.send_message(m.chat.id,j["content"])
    else: bot.send_photo(m.chat.id,j["file"],caption=j.get("caption",""))

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="لیست جوک")
def joke_list(m):
    if not jokes: return bot.reply_to(m,"❗ جوکی ثبت نشده")
    txt="\n".join([f"{i+1}. {(j['content'][:30] if j['type']=='text' else '[عکس]' )}" for i,j in enumerate(jokes)])
    bot.reply_to(m,"😂 لیست جوک:\n"+txt)

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("حذف جوک "))
def joke_del(m):
    try:
        idx=int(cmd_text(m).split()[2])-1
        if 0<=idx<len(jokes):
            jokes.pop(idx); bot.reply_to(m,"✅ جوک حذف شد")
        else: bot.reply_to(m,"❗ شماره نامعتبر")
    except: bot.reply_to(m,"❗ فرمت درست: حذف جوک 2")

# ================== فال ==================
fortunes=[]
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ثبت فال")
def fal_add(m):
    if m.reply_to_message:
        if m.reply_to_message.text:
            fortunes.append({"type":"text","content":m.reply_to_message.text})
        elif m.reply_to_message.photo:
            fortunes.append({"type":"photo","file":m.reply_to_message.photo[-1].file_id,"caption":m.reply_to_message.caption or ""})
        bot.reply_to(m,"🔮 فال ذخیره شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="فال")
def fal_send(m):
    if not fortunes: return bot.reply_to(m,"❗ فالی ثبت نشده")
    f=random.choice(fortunes)
    if f["type"]=="text": bot.send_message(m.chat.id,f["content"])
    else: bot.send_photo(m.chat.id,f["file"],caption=f.get("caption",""))

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="لیست فال")
def fal_list(m):
    if not fortunes: return bot.reply_to(m,"❗ فالی ثبت نشده")
    txt="\n".join([f"{i+1}. {(f['content'][:30] if f['type']=='text' else '[عکس]' )}" for i,f in enumerate(fortunes)])
    bot.reply_to(m,"🔮 لیست فال:\n"+txt)

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("حذف فال "))
def fal_del(m):
    try:
        idx=int(cmd_text(m).split()[2])-1
        if 0<=idx<len(fortunes):
            fortunes.pop(idx); bot.reply_to(m,"✅ فال حذف شد")
        else: bot.reply_to(m,"❗ شماره نامعتبر")
    except: bot.reply_to(m,"❗ فرمت درست: حذف فال 2")

# ================== مدیریت (بن/سکوت/اخطار) ==================
banned, muted, warnings={}, {}, {}

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="بن")
def ban(m):
    if is_admin(m.chat.id,m.from_user.id):
        uid=m.reply_to_message.from_user.id
        try: bot.ban_chat_member(m.chat.id,uid); banned.setdefault(m.chat.id,set()).add(uid); bot.reply_to(m,"🚫 کاربر بن شد")
        except: bot.reply_to(m,"❗ خطا در بن")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف بن")
def unban(m):
    if is_admin(m.chat.id,m.from_user.id):
        uid=m.reply_to_message.from_user.id
        try: bot.unban_chat_member(m.chat.id,uid); banned.get(m.chat.id,set()).discard(uid); bot.reply_to(m,"✅ بن حذف شد")
        except: bot.reply_to(m,"❗ خطا در حذف بن")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="سکوت")
def mute(m):
    if is_admin(m.chat.id,m.from_user.id):
        uid=m.reply_to_message.from_user.id
        try:
            bot.restrict_chat_member(m.chat.id,uid,can_send_messages=False)
            muted.setdefault(m.chat.id,set()).add(uid)
            bot.reply_to(m,"🔕 سکوت شد")
        except: bot.reply_to(m,"❗ خطا در سکوت")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف سکوت")
def unmute(m):
    if is_admin(m.chat.id,m.from_user.id):
        uid=m.reply_to_message.from_user.id
        try:
            bot.restrict_chat_member(m.chat.id,uid,
                can_send_messages=True,can_send_media_messages=True,
                can_send_other_messages=True,can_add_web_page_previews=True)
            muted.get(m.chat.id,set()).discard(uid)
            bot.reply_to(m,"🔊 سکوت حذف شد")
        except: bot.reply_to(m,"❗ خطا در حذف سکوت")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="اخطار")
def warn(m):
    if is_admin(m.chat.id,m.from_user.id):
        uid=m.reply_to_message.from_user.id
        warnings.setdefault(m.chat.id,{})
        warnings[m.chat.id][uid]=warnings[m.chat.id].get(uid,0)+1
        c=warnings[m.chat.id][uid]
        if c>=3:
            bot.ban_chat_member(m.chat.id,uid)
            warnings[m.chat.id][uid]=0
            bot.reply_to(m,"🚫 کاربر با ۳ اخطار بن شد")
        else: bot.reply_to(m,f"⚠️ اخطار {c}/3")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="حذف اخطار")
def reset_warn(m):
    if is_admin(m.chat.id,m.from_user.id):
        uid=m.reply_to_message.from_user.id
        warnings.get(m.chat.id,{}).pop(uid,None)
        bot.reply_to(m,"✅ اخطارها حذف شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="لیست بن")
def list_ban(m):
    if is_admin(m.chat.id,m.from_user.id):
        ids=banned.get(m.chat.id,set())
        txt="\n".join(map(str,ids)) if ids else "❗ لیست خالی"
        bot.reply_to(m,"🚫 لیست بن:\n"+txt)

@bot.message_handler(func=lambda m: cmd_text(m)=="لیست سکوت")
def list_mute(m):
    if is_admin(m.chat.id,m.from_user.id):
        ids=muted.get(m.chat.id,set())
        txt="\n".join(map(str,ids)) if ids else "❗ لیست خالی"
        bot.reply_to(m,"🔕 لیست سکوت:\n"+txt)

@bot.message_handler(func=lambda m: cmd_text(m)=="لیست اخطار")
def list_warn(m):
    if is_admin(m.chat.id,m.from_user.id):
        data=warnings.get(m.chat.id,{})
        txt="\n".join([f"{uid}: {c}" for uid,c in data.items()]) if data else "❗ لیست خالی"
        bot.reply_to(m,"⚠️ لیست اخطار:\n"+txt)

# ================== قفل‌ها ==================
locks={k:{} for k in ["links","stickers","bots","photo","video","gif","file","music","voice","forward"]}
@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل "))
def lock(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    key=cmd_text(m).replace("قفل ","",1)
    if key in locks:
        locks[key][m.chat.id]=True
        bot.reply_to(m,f"🔒 قفل {key} فعال شد")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("باز کردن "))
def unlock(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    key=cmd_text(m).replace("باز کردن ","",1)
    if key in locks:
        locks[key][m.chat.id]=False
        bot.reply_to(m,f"🔓 قفل {key} باز شد")

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
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True, timeout=30)
