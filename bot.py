# -*- coding: utf-8 -*-
import os, random, json
from datetime import datetime
import pytz
import telebot
import jdatetime

# ================== ⚙️ تنظیمات پایه ==================
TOKEN   = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
sudo_ids = {SUDO_ID}

# ================== 🧩 توابع کمکی ==================
def is_sudo(uid): return uid in sudo_ids
def is_admin(chat_id, user_id):
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator", "creator")
    except:
        return False

def cmd_text(m): return (getattr(m, "text", None) or "").strip()

# ================== ⏰ دستورات عمومی ==================
@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def cmd_time(m):
    now_utc = datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_teh = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    bot.reply_to(m, f"⏰ UTC: {now_utc}\n⏰ تهران: {now_teh}")

@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def cmd_stats(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    try:
        count = bot.get_chat_member_count(m.chat.id)
    except:
        count = "نامشخص"
    bot.reply_to(m, f"📊 اعضای گروه: {count}")

@bot.message_handler(func=lambda m: cmd_text(m) == "ایدی")
def cmd_id(m):
    caption = f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>"
    try:
        photos = bot.get_user_profile_photos(m.from_user.id, limit=1)
        if photos.total_count > 0:
            bot.send_photo(m.chat.id, photos.photos[0][-1].file_id, caption=caption)
        else:
            bot.reply_to(m, caption)
    except:
        bot.reply_to(m, caption)

# ================== 😎 جواب سودو ==================
SUDO_RESPONSES = ["جونم قربان 😎", "در خدمتم ✌️", "ربات آماده‌ست 🚀", "چه خبر رئیس؟ 🤖"]

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ربات")
def cmd_sudo(m): bot.reply_to(m, random.choice(SUDO_RESPONSES))

# ================== 😂 جوک و 🔮 فال ==================
jokes, fortunes = [], []

def save_item(arr, m):
    if m.reply_to_message:
        if m.reply_to_message.text:
            arr.append({"type": "text", "content": m.reply_to_message.text})
        elif m.reply_to_message.photo:
            arr.append({"type": "photo", "file": m.reply_to_message.photo[-1].file_id,
                        "caption": m.reply_to_message.caption or ""})

# --- جوک ---
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ثبت جوک")
def add_joke(m): save_item(jokes, m); bot.reply_to(m, "😂 جوک ذخیره شد")

@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def send_joke(m):
    if not jokes: return bot.reply_to(m, "❗ جوکی ثبت نشده")
    j = random.choice(jokes)
    if j["type"] == "text": bot.send_message(m.chat.id, j["content"])
    else: bot.send_photo(m.chat.id, j["file"], caption=j["caption"])

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "لیست جوک")
def list_joke(m):
    if not jokes: return bot.reply_to(m, "❗ جوکی ثبت نشده")
    txt = "\n".join([f"{i+1}. {(j['content'][:40] if j['type']=='text' else '[عکس]' )}" for i, j in enumerate(jokes)])
    bot.reply_to(m, "😂 لیست جوک:\n" + txt)

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("حذف جوک "))
def del_joke(m):
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        if 0 <= idx < len(jokes):
            jokes.pop(idx); bot.reply_to(m, "✅ جوک حذف شد")
        else: bot.reply_to(m, "❗ شماره نامعتبر")
    except: bot.reply_to(m, "❗ فرمت: حذف جوک 2")

# --- فال ---
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ثبت فال")
def add_fal(m): save_item(fortunes, m); bot.reply_to(m, "🔮 فال ذخیره شد")

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def send_fal(m):
    if not fortunes: return bot.reply_to(m, "❗ فالی ثبت نشده")
    f = random.choice(fortunes)
    if f["type"] == "text": bot.send_message(m.chat.id, f["content"])
    else: bot.send_photo(m.chat.id, f["file"], caption=f["caption"])

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "لیست فال")
def list_fal(m):
    if not fortunes: return bot.reply_to(m, "❗ فالی ثبت نشده")
    txt = "\n".join([f"{i+1}. {(f['content'][:40] if f['type']=='text' else '[عکس]' )}" for i, f in enumerate(fortunes)])
    bot.reply_to(m, "🔮 لیست فال:\n" + txt)

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).startswith("حذف فال "))
def del_fal(m):
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        if 0 <= idx < len(fortunes):
            fortunes.pop(idx); bot.reply_to(m, "✅ فال حذف شد")
        else: bot.reply_to(m, "❗ شماره نامعتبر")
    except: bot.reply_to(m, "❗ فرمت: حذف فال 2")

# ================== 🔐 قفل‌ها و 🎉 خوشامد ==================
DATA_FILE = "data.json"
if not os.path.exists(DATA_FILE):
    data = {"groups": {}, "welcome": {}, "autolock": {}}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def register_group(chat_id):
    data = load_data()
    if str(chat_id) not in data["groups"]:
        data["groups"][str(chat_id)] = True
        save_data(data)

def now_time():
    return jdatetime.datetime.now().strftime("%H:%M  ( %A %d %B %Y )")

# --- خوشامد ---
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new_member(m):
    try:
        register_group(m.chat.id)
        data = load_data()
        group = str(m.chat.id)
        settings = data["welcome"].get(group, {"enabled": True, "type": "text", "content": None})
        if not settings.get("enabled", True): return

        name = m.new_chat_members[0].first_name
        time_str = now_time()

        default_text = (
            f"سلام 𓄂ꪴꪰ🅜‌‌‌‌‌🅞‌‌‌‌‌‌🅗‌‌‌‌‌🅐‌‌‌‌‌‌🅜‌‌‌‌‌🅜‌‌‌‌‌‌🅐‌‌‌‌‌🅓‌‌‌‌‌‌❳𓆃 عزیز\n"
            f"به گروه 𝙎𝙩𝙖𝙧𝙧𝙮𝙉𝙞𝙜𝙝𝙩 ☾꙳⋆ خوش آمدید 😎\n\n"
            f"ساعت ›› {time_str}"
        )

        text = settings.get("content") or default_text
        text = text.replace("{name}", name).replace("{time}", time_str)

        if settings.get("type") == "photo" and settings.get("file_id"):
            bot.send_photo(m.chat.id, settings["file_id"], caption=text)
        else:
            bot.send_message(m.chat.id, text)
    except Exception as e:
        print("welcome error:", e)

@bot.message_handler(func=lambda m: cmd_text(m).lower() in ["خوشامد روشن", "خوشامد on"])
def welcome_on(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data = load_data()
    group = str(m.chat.id)
    data["welcome"].setdefault(group, {"enabled": True})
    data["welcome"][group]["enabled"] = True
    save_data(data)
    bot.reply_to(m, "✅ خوشامد فعال شد")

@bot.message_handler(func=lambda m: cmd_text(m).lower() in ["خوشامد خاموش", "خوشامد off"])
def welcome_off(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data = load_data()
    group = str(m.chat.id)
    data["welcome"].setdefault(group, {"enabled": False})
    data["welcome"][group]["enabled"] = False
    save_data(data)
    bot.reply_to(m, "🚫 خوشامد غیرفعال شد")

@bot.message_handler(func=lambda m: cmd_text(m) == "تنظیم خوشامد متن" and m.reply_to_message)
def set_welcome_text(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data = load_data()
    group = str(m.chat.id)
    txt = m.reply_to_message.text or ""
    data["welcome"][group] = {"enabled": True, "type": "text", "content": txt}
    save_data(data)
    bot.reply_to(m, "📝 متن خوشامد تنظیم شد. از {name} و {time} می‌تونی استفاده کنی.")

# --- قفل‌ها ---
locks = {k: {} for k in ["links", "stickers", "photo", "video", "gif", "file", "music", "voice", "forward"]}
LOCK_MAP = {
    "لینک": "links", "استیکر": "stickers", "عکس": "photo", "ویدیو": "video",
    "گیف": "gif", "فایل": "file", "موزیک": "music", "ویس": "voice", "فوروارد": "forward"
}
group_lock = {}

@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل "))
def cmd_lock(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    k = cmd_text(m).replace("قفل ", "", 1)
    if k == "گروه":
        group_lock[m.chat.id] = True
        return bot.reply_to(m, "🔒 گروه بسته شد — کاربران عادی نمی‌توانند پیام ارسال کنند.")
    key = LOCK_MAP.get(k)
    if key:
        locks[key][m.chat.id] = True
        bot.reply_to(m, f"🔒 قفل {k} فعال شد.")
    else:
        bot.reply_to(m, "❗ نوع قفل نامشخص است.")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("باز کردن "))
def cmd_unlock(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    k = cmd_text(m).replace("باز کردن ", "", 1)
    if k == "گروه":
        group_lock[m.chat.id] = False
        return bot.reply_to(m, "🔓 گروه باز شد.")
    key = LOCK_MAP.get(k)
    if key:
        locks[key][m.chat.id] = False
        bot.reply_to(m, f"🔓 قفل {k} باز شد.")
    else:
        bot.reply_to(m, "❗ نوع قفل نامشخص است.")

@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation'])
def enforce_locks(m):
    register_group(m.chat.id)
    if is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id): return
    txt = m.text or ""
    if group_lock.get(m.chat.id):
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass
        return
    try:
        if locks["links"].get(m.chat.id) and any(x in txt for x in ["http://","https://","t.me","telegram.me"]):
            bot.delete_message(m.chat.id, m.message_id)
        if locks["stickers"].get(m.chat.id) and m.sticker:
            bot.delete_message(m.chat.id, m.message_id)
        if locks["photo"].get(m.chat.id) and m.photo:
            bot.delete_message(m.chat.id, m.message_id)
        if locks["video"].get(m.chat.id) and m.video:
            bot.delete_message(m.chat.id, m.message_id)
        if locks["gif"].get(m.chat.id) and m.animation:
            bot.delete_message(m.chat.id, m.message_id)
        if locks["file"].get(m.chat.id) and m.document:
            bot.delete_message(m.chat.id, m.message_id)
        if locks["music"].get(m.chat.id) and m.audio:
            bot.delete_message(m.chat.id, m.message_id)
        if locks["voice"].get(m.chat.id) and m.voice:
            bot.delete_message(m.chat.id, m.message_id)
        if locks["forward"].get(m.chat.id) and (m.forward_from or m.forward_from_chat):
            bot.delete_message(m.chat.id, m.message_id)
    except:
        pass

# ================== 🚀 اجرای ربات ==================
if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.infinity_polling(skip_pending=True, timeout=30)
