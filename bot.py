# -*- coding: utf-8 -*-
# Persian Lux Panel V17 – English Commands + Persian Responses
# Designed for Mohammad 👑

import os, json, time, logging, jdatetime, telebot
from telebot import types

# ================= ⚙️ CONFIG =================
TOKEN = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

DATA_FILE = "data.json"
LOG_FILE = "error.log"

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# ================= 💾 DATA HANDLER =================
def base_data():
    return {
        "welcome": {}, "locks": {}, "admins": {}, "sudo_list": [],
        "banned": {}, "muted": {}, "warns": {}, "users": [],
        "filters": {}
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(base_data())
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = base_data()
    for k in base_data():
        if k not in data:
            data[k] = base_data()[k]
    save_data(data)
    return data

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def register_group(gid):
    data = load_data()
    gid = str(gid)
    data["welcome"].setdefault(gid, {"enabled": True, "type": "text",
                                     "content": None, "file_id": None})
    data["locks"].setdefault(gid,
        {k: False for k in ["link","group","photo","video","sticker",
                            "gif","file","music","voice","forward","text"]})
    save_data(data)

# ================= 🧩 UTILS =================
def shamsi_date():
    return jdatetime.datetime.now().strftime("%A %d %B %Y")

def shamsi_time():
    return jdatetime.datetime.now().strftime("%H:%M:%S")

def cmd_text(m): return (getattr(m, "text", None) or "").strip()

def is_sudo(uid):
    d = load_data()
    return str(uid) in [str(SUDO_ID)] + d.get("sudo_list", [])

def is_admin(chat_id, uid):
    d = load_data()
    gid = str(chat_id)
    if is_sudo(uid): return True
    if str(uid) in d["admins"].get(gid, []): return True
    try:
        st = bot.get_chat_member(chat_id, uid).status
        return st in ("administrator", "creator")
    except: return False

print("✅ [1] Config & Data Loaded")

# ================= 🆔 INFO / TIME / LINK =================
@bot.message_handler(commands=["id"])
def cmd_id(m):
    try:
        user = m.from_user
        txt = (f"🧾 مشخصات شما:\n"
               f"👤 نام: {user.first_name}\n"
               f"🆔 آیدی: <code>{user.id}</code>\n"
               f"💬 چت: <code>{m.chat.id}</code>\n"
               f"📅 {shamsi_date()} | ⏰ {shamsi_time()}")
        bot.reply_to(m, txt)
    except Exception as e:
        logging.error(e)
        bot.reply_to(m, str(user.id))

@bot.message_handler(commands=["time"])
def cmd_time(m):
    bot.reply_to(m, f"⏰ {shamsi_time()} | 📅 {shamsi_date()}")

@bot.message_handler(commands=["botlink"])
def bot_link(m):
    bot.reply_to(m, f"https://t.me/{bot.get_me().username}")

@bot.message_handler(commands=["grouplink"])
def group_link(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 {link}")
    except:
        bot.reply_to(m, "⚠️ دسترسی ساخت لینک ندارم.")
print("✅ [2] Info Commands Loaded")

# ================= 🔒 LOCK SYSTEM =================
LOCK_MAP = {
    "link": "link", "group": "group", "photo": "photo",
    "video": "video", "sticker": "sticker", "gif": "gif",
    "file": "file", "music": "music", "voice": "voice",
    "forward": "forward", "text": "text"
}

@bot.message_handler(commands=["lock","unlock"])
def toggle_lock(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    parts = cmd_text(m).split(" ",1)
    if len(parts)<2: return bot.reply_to(m,"⚠️ Example: /lock link")
    key = parts[1].lower()
    lock_type = LOCK_MAP.get(key)
    if not lock_type: return bot.reply_to(m,"❌ Invalid lock type.")
    enable = m.text.startswith("/lock")
    d["locks"].setdefault(gid,{k:False for k in LOCK_MAP.values()})
    d["locks"][gid][lock_type] = enable; save_data(d)
    if lock_type=="group":
        try:
            perms=types.ChatPermissions(can_send_messages=not enable)
            bot.set_chat_permissions(m.chat.id,perms)
        except Exception as e:
            logging.error(e)
    bot.reply_to(m,f"{'🔒' if enable else '🔓'} {key} {'enabled' if enable else 'disabled'}.")

@bot.message_handler(content_types=["text","photo","video","sticker",
                                   "animation","document","audio","voice"])
def lock_filter_system(m):
    d=load_data(); gid=str(m.chat.id)
    locks=d.get("locks",{}).get(gid,{})
    if not locks: return
    def warn_delete(reason):
        if is_admin(m.chat.id,m.from_user.id): return
        try: bot.delete_message(m.chat.id,m.id)
        except: pass
        msg=bot.send_message(m.chat.id,
            f"🚨 <b>اخطار:</b> {reason}\n👤 {m.from_user.first_name}",
            parse_mode="HTML")
        time.sleep(3)
        try: bot.delete_message(m.chat.id,msg.id)
        except: pass
    if locks.get("link") and m.text and any(x in m.text.lower() for x in ["http","t.me/"]):
        return warn_delete("ارسال لینک مجاز نیست")
    if locks.get("photo") and m.content_type=="photo": return warn_delete("عکس ممنوع")
    if locks.get("video") and m.content_type=="video": return warn_delete("ویدیو مجاز نیست")
    if locks.get("sticker") and m.content_type=="sticker": return warn_delete("استیکر ممنوع")
print("✅ [3] Lock System Loaded")

# ================= 👮 ADMIN / SUDO =================
@bot.message_handler(commands=["addsudo"])
def addsudo(m):
    if not is_sudo(m.from_user.id): return
    target = m.reply_to_message.from_user.id if m.reply_to_message else None
    if not target: return bot.reply_to(m,"Reply to user")
    d=load_data()
    if str(target) not in d["sudo_list"]:
        d["sudo_list"].append(str(target)); save_data(d)
        bot.reply_to(m,"👑 سودو اضافه شد")
    else: bot.reply_to(m,"ℹ️ از قبل سودو بود")

@bot.message_handler(commands=["addadmin"])
def addadmin(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    target = m.reply_to_message.from_user.id if m.reply_to_message else None
    if not target: return bot.reply_to(m,"Reply to user")
    d=load_data(); gid=str(m.chat.id)
    d["admins"].setdefault(gid,[])
    if str(target) in d["admins"][gid]: return bot.reply_to(m,"قبلاً مدیر بود")
    d["admins"][gid].append(str(target)); save_data(d)
    bot.reply_to(m,"👮 مدیر اضافه شد")

@bot.message_handler(commands=["admins"])
def list_admins(m):
    d=load_data(); lst=d.get("admins",{}).get(str(m.chat.id),[])
    bot.reply_to(m,"👮 لیست مدیران:\n"+"\n".join(lst) if lst else "نداریم")
print("✅ [4] Admin & Sudo Loaded")

# ================= 🚫 BAN / MUTE / WARN =================
def bot_can_restrict(m):
    try:
        me=bot.get_me()
        st=bot.get_chat_member(m.chat.id,me.id)
        return st.status in ("administrator","creator")
    except: return False

def target_user(m):
    if m.reply_to_message: return m.reply_to_message.from_user.id
    p=cmd_text(m).split()
    if len(p)>1 and p[1].isdigit(): return int(p[1])
    return None

@bot.message_handler(commands=["ban"])
def ban_user(m):
    if not is_admin(m.chat.id,m.from_user.id) or not bot_can_restrict(m): return
    t=target_user(m)
    if not t: return bot.reply_to(m,"Reply or ID")
    if is_admin(m.chat.id,t) or is_sudo(t): return
    d=load_data(); gid=str(m.chat.id)
    d["banned"].setdefault(gid,[]); d["banned"][gid].append(t); save_data(d)
    try: bot.ban_chat_member(m.chat.id,t)
    except: pass
    bot.send_message(m.chat.id,f"🚫 کاربر {t} بن شد")

@bot.message_handler(commands=["mute"])
def mute_user(m):
    if not is_admin(m.chat.id,m.from_user.id) or not bot_can_restrict(m): return
    t=target_user(m)
    if not t: return bot.reply_to(m,"Reply or ID")
    if is_admin(m.chat.id,t) or is_sudo(t): return
    bot.restrict_chat_member(m.chat.id,t,permissions=types.ChatPermissions(can_send_messages=False))
    bot.reply_to(m,"🔇 کاربر ساکت شد")

@bot.message_handler(commands=["warn"])
def warn_user(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    t=target_user(m)
    if not t: return bot.reply_to(m,"Reply or ID")
    d=load_data(); gid=str(m.chat.id)
    d["warns"].setdefault(gid,{})
    d["warns"][gid][str(t)]=d["warns"][gid].get(str(t),0)+1
    if d["warns"][gid][str(t)]>=3:
        try: bot.ban_chat_member(m.chat.id,t)
        except: pass
        d["warns"][gid][str(t)]=0
    save_data(d)
    bot.reply_to(m,f"⚠️ اخطار {d['warns'][gid][str(t)]}")
print("✅ [5] Ban / Mute / Warn Loaded")

# ================= 🚫 FILTER =================
@bot.message_handler(commands=["addfilter"])
def addfilter(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    parts=cmd_text(m).split(" ",1)
    if len(parts)<2: return bot.reply_to(m,"Usage: /addfilter word")
    word=parts[1].lower(); d=load_data(); gid=str(m.chat.id)
    d["filters"].setdefault(gid,[])
    if word in d["filters"][gid]: return
    d["filters"][gid].append(word); save_data(d)
    bot.reply_to(m,f"🚫 فیلتر شد: {word}")

@bot.message_handler(commands=["filters"])
def list_filters(m):
    d=load_data(); lst=d.get("filters",{}).get(str(m.chat.id),[])
    bot.reply_to(m,"\n".join(lst) if lst else "فیلتر خالی است")

@bot.message_handler(content_types=["text"])
def check_filter(m):
    d=load_data(); gid=str(m.chat.id)
    fs=d.get("filters",{}).get(gid,[])
    if not fs or is_admin(m.chat.id,m.from_user.id): return
    for w in fs:
        if w in m.text.lower():
            try:
                bot.delete_message(m.chat.id,m.id)
                msg=bot.send_message(m.chat.id,
                    f"🚫 {w} فیلتر شده است.",parse_mode="HTML")
                time.sleep(2); bot.delete_message(m.chat.id,msg.id)
            except Exception as e:
                logging.error(e)
            break
print("✅ [6] Filter Loaded")

# ================= 🚀 RUN =================
if __name__ == "__main__":
    print("🤖 Persian Lux Panel V17 Running...")
    while True:
        try:
            bot.infinity_polling(timeout=60,long_polling_timeout=40,skip_pending=True)
        except Exception as e:
            logging.error(f"Polling Error: {e}")
            time.sleep(5)
