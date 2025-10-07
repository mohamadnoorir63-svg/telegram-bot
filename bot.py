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

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ثبت جوک")
def add_joke(m): save_item(jokes,m); bot.reply_to(m,"😂 جوک ذخیره شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="جوک")
def send_joke(m):
    if not jokes: return bot.reply_to(m,"❗ جوکی ثبت نشده")
    j=random.choice(jokes)
    if j["type"]=="text": bot.send_message(m.chat.id,j["content"])
    else: bot.send_photo(m.chat.id,j["file"],caption=j["caption"])

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m)=="ثبت فال")
def add_fal(m): save_item(fortunes,m); bot.reply_to(m,"🔮 فال ذخیره شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="فال")
def send_fal(m):
    if not fortunes: return bot.reply_to(m,"❗ فالی ثبت نشده")
    f=random.choice(fortunes)
    if f["type"]=="text": bot.send_message(m.chat.id,f["content"])
    else: bot.send_photo(m.chat.id,f["file"],caption=f["caption"])

# ================== بن / سکوت ==================
banned = {}
muted = {}
def protect_user(chat_id, uid):
    if is_sudo(uid): return "⚡ این کاربر سودو است"
    try:
        member = bot.get_chat_member(chat_id, uid)
        if member.status == "creator": return "❗ صاحب گروه قابل مدیریت نیست"
    except: pass
    return None

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="بن")
def ban(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid = m.reply_to_message.from_user.id
    if protect_user(m.chat.id,uid): return
    bot.ban_chat_member(m.chat.id, uid)
    banned.setdefault(m.chat.id,set()).add(uid)
    bot.reply_to(m,"🚫 کاربر بن شد")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m)=="سکوت")
def mute(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    uid=m.reply_to_message.from_user.id
    if protect_user(m.chat.id,uid): return
    bot.restrict_chat_member(m.chat.id,uid,can_send_messages=False)
    muted.setdefault(m.chat.id,set()).add(uid)
    bot.reply_to(m,"🔕 کاربر در سکوت قرار گرفت")

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
    except: bot.reply_to(m,"❗ فرمت درست: حذف 10")

# ================== قفل‌ها ==================
locks = {k:{} for k in ["links","stickers","bots","photo","video","gif","file","music","voice","forward"]}
LOCK_MAP = {
    "لینک":"links","استیکر":"stickers","ربات":"bots","عکس":"photo","ویدیو":"video",
    "گیف":"gif","فایل":"file","موزیک":"music","ویس":"voice","فوروارد":"forward"
}

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
        bot.reply_to(m,f"🔓 قفل {key_fa} باز شد")

# ================== قفل کل گروه ==================
group_lock = {}

@bot.message_handler(func=lambda m: cmd_text(m)=="قفل گروه")
def lock_group(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    group_lock[m.chat.id] = True
    bot.send_message(m.chat.id, "🔒 گروه قفل شد.\n🚫 اعضا اجازه ارسال پیام ندارند.")

@bot.message_handler(func=lambda m: cmd_text(m)=="باز کردن گروه")
def unlock_group(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    group_lock[m.chat.id] = False
    bot.send_message(m.chat.id, "🔓 گروه باز شد.\n✅ کاربران می‌توانند پیام بفرستند.")

# ================== enforce همه قفل‌ها ==================
@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation'])
def enforce_all(m):
    # ادمین و سودو آزاد هستند
    if is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id):
        return

    # اگر پیام دستور مدیریتی بود، enforce اجرا نشود
    if m.text:
        commands = ["قفل","باز کردن","پاکسازی","حذف","بن","سکوت","اخطار","فال","جوک"]
        if any(m.text.startswith(c) for c in commands):
            return

    # اگر گروه قفل است
    if group_lock.get(m.chat.id):
        try:
            bot.delete_message(m.chat.id, m.message_id)
        except: pass
        return

    # بقیه قفل‌ها
    txt = m.text or ""
    try:
        if locks["links"].get(m.chat.id) and any(x in txt for x in ["http://","https://","t.me"]):
            bot.delete_message(m.chat.id, m.message_id)
        elif locks["stickers"].get(m.chat.id) and m.sticker:
            bot.delete_message(m.chat.id, m.message_id)
        elif locks["photo"].get(m.chat.id) and m.photo:
            bot.delete_message(m.chat.id, m.message_id)
        elif locks["video"].get(m.chat.id) and m.video:
            bot.delete_message(m.chat.id, m.message_id)
        elif locks["gif"].get(m.chat.id) and m.animation:
            bot.delete_message(m.chat.id, m.message_id)
        elif locks["file"].get(m.chat.id) and m.document:
            bot.delete_message(m.chat.id, m.message_id)
        elif locks["music"].get(m.chat.id) and m.audio:
            bot.delete_message(m.chat.id, m.message_id)
        elif locks["voice"].get(m.chat.id) and m.voice:
            bot.delete_message(m.chat.id, m.message_id)
        elif locks["forward"].get(m.chat.id) and (m.forward_from or m.forward_from_chat):
            bot.delete_message(m.chat.id, m.message_id)
    except:
        pass

# ================== اجرای ربات ==================
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True, timeout=30)
