# -*- coding: utf-8 -*-
import os, random
from datetime import datetime
import pytz
import telebot
import jdatetime

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

# ================== 🎉 خوشامد ==================
def now_time():
    return jdatetime.datetime.now().strftime("%H:%M  ( %A %d %B %Y )")

DATA_FILE = "data.json"
if not os.path.exists(DATA_FILE):
    data = {"welcome": {}}
    import json
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data():
    import json
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    import json
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@bot.message_handler(content_types=["new_chat_members"])
def welcome_new_member(m):
    try:
        data = load_data()
        group = str(m.chat.id)
        settings = data["welcome"].get(group, {"enabled": True, "content": None})
        if not settings.get("enabled", True):
            return
        name = m.new_chat_members[0].first_name or "دوست جدید"
        time_str = now_time()
        text = settings.get("content") or (
            f"سلام {name} عزیز 🌙\n"
            f"به گروه StarryNight خوش آمدی 😎\n\n"
            f"⏰ ساعت الان: {time_str}"
        )
        bot.send_message(m.chat.id, text)
    except Exception as e:
        print(f"⚠️ welcome error: {e}")

@bot.message_handler(func=lambda m: cmd_text(m) in ["خوشامد روشن", "خوشامد خاموش"])
def toggle_welcome(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)):
        return
    data = load_data()
    group = str(m.chat.id)
    en = (cmd_text(m) == "خوشامد روشن")
    data["welcome"].setdefault(group, {"enabled": True})
    data["welcome"][group]["enabled"] = en
    save_data(data)
    bot.reply_to(m, "✅ خوشامد روشن شد" if en else "🚫 خوشامد خاموش شد")

@bot.message_handler(func=lambda m: cmd_text(m) == "تنظیم خوشامد متن" and m.reply_to_message)
def set_welcome_text(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)):
        return
    data = load_data()
    group = str(m.chat.id)
    txt = m.reply_to_message.text or ""
    data["welcome"][group] = {"enabled": True, "content": txt}
    save_data(data)
    bot.reply_to(m, "📝 متن خوشامد تنظیم شد. از {name} و {time} می‌تونی استفاده کنی.")

# ================== 🚀 اجرای ربات ==================
if __name__ == "__main__":
    print("🤖 Bot is running...")
    try:
        bot.infinity_polling(skip_pending=True, timeout=30)
    except Exception as e:
        print(f"❌ Polling error: {e}")
