# -*- coding: utf-8 -*-
import os, json, random, jdatetime, pytz
from datetime import datetime, timedelta
import telebot
from telebot import types

# ================= ⚙️ تنظیمات اصلی =================
TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("BOT_TOK") or "توکن_ربات"
SUDO_ID = int(os.environ.get("SUDO_ID", "123456789"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
sudo_ids = {SUDO_ID}

DATA_FILE = "data.json"
if not os.path.exists(DATA_FILE):
    data = {"admins": [], "sudos": list(sudo_ids), "groups": {}, "welcome": {}, "autolock": {}}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================= 🧩 توابع کمکی =================
def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def is_sudo(uid): return uid in sudo_ids
def is_admin(chat_id, user_id):
    try: return bot.get_chat_member(chat_id, user_id).status in ("administrator", "creator")
    except: return False
def cmd_text(m): return (getattr(m,"text",None) or "").strip()
def register_group(chat_id):
    data = load_data()
    if str(chat_id) not in data["groups"]:
        data["groups"][str(chat_id)] = True
        save_data(data)

# ================= 💬 دستورات عمومی =================
@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def time_cmd(m):
    now = jdatetime.datetime.now().strftime("%H:%M  (%A %d %B %Y)")
    bot.reply_to(m, f"🕓 ساعت و تاریخ شمسی:\n{now}")

@bot.message_handler(func=lambda m: cmd_text(m) == "آیدی")
def id_cmd(m):
    caption = f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 چت: <code>{m.chat.id}</code>"
    try:
        photos = bot.get_user_profile_photos(m.from_user.id, limit=1)
        if photos.total_count > 0:
            bot.send_photo(m.chat.id, photos.photos[0][-1].file_id, caption=caption)
        else:
            bot.reply_to(m, caption)
    except:
        bot.reply_to(m, caption)

# ================= 😂 جوک و 🔮 فال =================
jokes, fortunes = [], []
def save_item(arr, m):
    if not m.reply_to_message: return
    if m.reply_to_message.text:
        arr.append({"type":"text","content":m.reply_to_message.text})
    elif m.reply_to_message.photo:
        arr.append({"type":"photo","file":m.reply_to_message.photo[-1].file_id,"caption":m.reply_to_message.caption or ""})

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ثبت جوک")
def add_joke(m):
    save_item(jokes, m)
    bot.reply_to(m, "😂 جوک ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def send_joke(m):
    if not jokes: return bot.reply_to(m, "❗ هنوز جوکی ثبت نشده.")
    j = random.choice(jokes)
    if j["type"] == "text": bot.send_message(m.chat.id, j["content"])
    else: bot.send_photo(m.chat.id, j["file"], caption=j["caption"])

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ثبت فال")
def add_fal(m):
    save_item(fortunes, m)
    bot.reply_to(m, "🔮 فال ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def send_fal(m):
    if not fortunes: return bot.reply_to(m, "❗ هنوز فالی ثبت نشده.")
    f = random.choice(fortunes)
    if f["type"] == "text": bot.send_message(m.chat.id, f["content"])
    else: bot.send_photo(m.chat.id, f["file"], caption=f["caption"])

# ================= 🎉 خوشامد حرفه‌ای =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new(m):
    try:
        register_group(m.chat.id)
        data = load_data()
        group = str(m.chat.id)
        w = data["welcome"].get(group, {"enabled":True,"type":"text"})
        if not w.get("enabled",True): return

        name = m.new_chat_members[0].first_name
        now = jdatetime.datetime.now().strftime("%H:%M ( %A %d %B %Y )")
        text = f"سلام 𓄂ꪴꪰ🅜‌‌‌‌‌🅞‌‌‌‌‌‌🅗‌‌‌‌‌🅐‌‌‌‌‌‌🅜‌‌‌‌‌🅜‌‌‌‌‌‌🅐‌‌‌‌‌🅓‌‌‌‌‌‌❳𓆃 عزیز\nبه گروه 𝙎𝙩𝙖𝙧𝙧𝙮𝙉𝙞𝙜𝙝𝙩 ☾꙳⋆ خوش آمدید 😎\n\nساعت ›› {now}"
        if w["type"] == "photo" and w.get("file_id"):
            bot.send_photo(m.chat.id, w["file_id"], caption=text)
        else:
            bot.send_message(m.chat.id, text)
    except Exception as e:
        print("Welcome Error:", e)

@bot.message_handler(func=lambda m: cmd_text(m) in ["خوشامد روشن","خوشامد خاموش"])
def toggle_welcome(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    data = load_data(); group = str(m.chat.id)
    en = (cmd_text(m) == "خوشامد روشن")
    data["welcome"][group] = data["welcome"].get(group, {"enabled":True})
    data["welcome"][group]["enabled"] = en
    save_data(data)
    bot.reply_to(m, "✅ خوشامد فعال شد" if en else "🚫 خوشامد غیرفعال شد")

@bot.message_handler(func=lambda m: cmd_text(m)=="تنظیم خوشامد متن" and m.reply_to_message)
def set_welcome_text(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    data=load_data(); group=str(m.chat.id)
    text=m.reply_to_message.text
    data["welcome"][group]={"enabled":True,"type":"text","content":text}
    save_data(data)
    bot.reply_to(m,"📝 متن خوشامد تنظیم شد.")

# ================= 🔐 قفل‌ها =================
locks = {k:{} for k in ["links","stickers","photo","video","gif","file","music","voice","forward"]}
LOCK_MAP = {
    "لینک":"links","استیکر":"stickers","عکس":"photo","ویدیو":"video",
    "گیف":"gif","فایل":"file","موزیک":"music","ویس":"voice","فوروارد":"forward"
}
group_lock = {}
autolock = {}

@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل "))
def lock(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    k = cmd_text(m).replace("قفل ","",1)
    if k=="گروه": group_lock[m.chat.id]=True; return bot.reply_to(m,"🔒 گروه بسته شد.")
    key=LOCK_MAP.get(k); 
    if key: locks[key][m.chat.id]=True; bot.reply_to(m,f"🔒 قفل {k} فعال شد.")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("باز کردن "))
def unlock(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    k=cmd_text(m).replace("باز کردن ","",1)
    if k=="گروه": group_lock[m.chat.id]=False; return bot.reply_to(m,"🔓 گروه باز شد.")
    key=LOCK_MAP.get(k)
    if key: locks[key][m.chat.id]=False; bot.reply_to(m,f"🔓 قفل {k} باز شد.")

@bot.message_handler(func=lambda m: cmd_text(m)=="قفل خودکار")
def autolock_toggle(m):
    if not (is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id)): return
    chat=str(m.chat.id); data=load_data(); auto=data.get("autolock",{})
    enabled=not auto.get(chat,False)
    auto[chat]=enabled; data["autolock"]=auto; save_data(data)
    bot.reply_to(m,"🕔 قفل خودکار فعال شد." if enabled else "🚫 قفل خودکار غیرفعال شد.")

# اعمال قفل‌ها
@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation'])
def enforce(m):
    register_group(m.chat.id)
    if is_admin(m.chat.id,m.from_user.id) or is_sudo(m.from_user.id): return
    txt=m.text or ""
    if group_lock.get(m.chat.id):
        try: bot.delete_message(m.chat.id,m.message_id)
        except: pass; return
    try:
        if locks["links"].get(m.chat.id) and any(x in txt for x in ["http","https","t.me"]): bot.delete_message(m.chat.id,m.message_id)
        if locks["stickers"].get(m.chat.id) and m.sticker: bot.delete_message(m.chat.id,m.message_id)
        if locks["photo"].get(m.chat.id) and m.photo: bot.delete_message(m.chat.id,m.message_id)
        if locks["video"].get(m.chat.id) and m.video: bot.delete_message(m.chat.id,m.message_id)
        if locks["gif"].get(m.chat.id) and m.animation: bot.delete_message(m.chat.id,m.message_id)
        if locks["file"].get(m.chat.id) and m.document: bot.delete_message(m.chat.id,m.message_id)
        if locks["music"].get(m.chat.id) and m.audio: bot.delete_message(m.chat.id,m.message_id)
        if locks["voice"].get(m.chat.id) and m.voice: bot.delete_message(m.chat.id,m.message_id)
        if locks["forward"].get(m.chat.id) and (m.forward_from or m.forward_from_chat): bot.delete_message(m.chat.id,m.message_id)
    except: pass

# ================= 🚀 اجرای ربات =================
print("🤖 مرحله ۱ اجرا شد ...")
bot.infinity_polling(skip_pending=True, timeout=30)
