# -*- coding: utf-8 -*-
import os, json, random, logging
from datetime import datetime
import pytz, jdatetime
import telebot
from telebot import types

# ================= ⚙️ تنظیمات اولیه =================
TOKEN   = os.environ.get("BOT_TOKEN") or "PUT_YOUR_BOT_TOKEN_HERE"
SUDO_ID = int(os.environ.get("SUDO_ID", "0")) or 123456789
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

DATA_FILE = "data.json"
LOG_FILE  = "error.log"

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# ================= 🔒 قفل‌ها (کلیدهای فارسی → نام فنی) =================
LOCK_MAP = {
    "لینک": "link",
    "گروه": "group",
    "عکس": "photo",
    "ویدیو": "video",
    "استیکر": "sticker",
    "گیف": "gif",
    "فایل": "file",
    "موزیک": "music",
    "ویس": "voice",
    "فوروارد": "forward"
}

# ================= 📂 داده‌ها =================
def _base_data():
    return {
        "welcome": {},      # gid -> {enabled,type,content,file_id}
        "locks": {},        # gid -> {link:bool,...}
        "admins": {},       # gid -> [uid,...]
        "sudo_list": [],    # [uid,...] (اضافه بر SUDO_ID)
        "banned": {},       # gid -> [uid,...]
        "muted": {},        # gid -> [uid,...]
        "warns": {},        # gid -> {uid:count}
        "jokes": [],        # لیست جوک‌ها
        "falls": [],        # لیست فال‌ها
        "users": [],        # یوزرهایی که /start دادن
        "stats": {}         # gid -> {date, users{uid:count}, counts{...}}
    }

def _ensure_datafile():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(_base_data(), f, ensure_ascii=False, indent=2)

def load_data():
    _ensure_datafile()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = _base_data()
    # تکمیل کلیدهای جاافتاده
    base = _base_data()
    for k in base:
        if k not in data:
            data[k] = base[k]
    save_data(data)
    return data

def save_data(d):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"save_data: {e}")

# ================= 🕒 زمان و تاریخ =================
def now_teh_dt():
    return datetime.now(pytz.timezone("Asia/Tehran"))

def shamsi_date():
    return jdatetime.datetime.now().strftime("%A %d %B %Y")

def shamsi_time():
    return jdatetime.datetime.now().strftime("%H:%M:%S")

# ================= 🧩 ثبت گروه/آماده‌سازی =================
def register_group(gid):
    data = load_data()
    gid = str(gid)
    data["welcome"].setdefault(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})
    data["locks"].setdefault(gid, {k: False for k in LOCK_MAP.values()})
    if gid not in data["stats"]:
        data["stats"][gid] = {
            "date": str(datetime.now().date()),
            "users": {},
            "counts": {k: 0 for k in ["msg","photo","video","voice","music","sticker","gif","fwd"]}
        }
    save_data(data)

# ================= 🛠 ابزار دسترسی =================
def cmd_text(m):
    return (getattr(m, "text", None) or "").strip()

def is_sudo(uid):
    d = load_data()
    return str(uid) in [str(SUDO_ID)] + [str(x) for x in d.get("sudo_list", [])]

def is_admin(chat_id, uid):
    d = load_data()
    gid = str(chat_id)
    if is_sudo(uid):
        return True
    if str(uid) in d["admins"].get(gid, []):
        return True
    try:
        st = bot.get_chat_member(chat_id, uid).status
        return st in ("administrator", "creator")
    except Exception:
        return False

# ================= 👋 استارت و ثبت کاربران =================
@bot.message_handler(commands=["start"])
def start_cmd(m):
    d = load_data()
    u = str(m.from_user.id)
    if u not in [str(x) for x in d.get("users", [])]:
        d["users"].append(int(u))
        save_data(d)
    bot.reply_to(m, "سلام 👋\nمن ربات مدیریتی شما هستم. برای راهنما: «پنل» یا /panel")

# ================= 📜 عمومی: آیدی / ساعت / لینک‌ها =================
@bot.message_handler(func=lambda m: cmd_text(m) in ["آیدی","ایدی"])
def show_id(m):
    try:
        caption = (
            f"🧾 <b>نام:</b> {m.from_user.first_name}\n"
            f"🆔 <b>آیدی شما:</b> <code>{m.from_user.id}</code>\n"
            f"💬 <b>آیدی گروه:</b> <code>{m.chat.id}</code>\n"
            f"📅 {shamsi_date()} | ⏰ {shamsi_time()}"
        )
        ph = bot.get_user_profile_photos(m.from_user.id, limit=1)
        if ph.total_count > 0:
            bot.send_photo(m.chat.id, ph.photos[0][-1].file_id, caption=caption)
        else:
            bot.reply_to(m, caption)
    except Exception as e:
        logging.error(f"show_id: {e}")
        bot.reply_to(m, f"🆔 <code>{m.from_user.id}</code> | ⏰ {shamsi_time()}")

@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def show_time(m):
    bot.reply_to(m, f"⏰ {shamsi_time()}\n📅 {shamsi_date()}")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک گروه")
def group_link(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 لینک گروه:\n{link}")
    except Exception:
        bot.reply_to(m, "⚠️ دسترسی ساخت/دریافت لینک ندارم.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک ربات")
def bot_link(m):
    uname = bot.get_me().username
    bot.reply_to(m, f"🤖 لینک ربات:\nhttps://t.me/{uname}")

# ================= 👋 خوشامد =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome(m):
    register_group(m.chat.id)
    d = load_data(); gid = str(m.chat.id)
    s = d["welcome"].get(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})
    if not s.get("enabled", True): return
    user = m.new_chat_members[0]
    name = user.first_name or "دوست جدید"
    t = shamsi_time()
    text = s.get("content") or f"سلام {name} 🌹\nبه {m.chat.title} خوش اومدی 🌸\n⏰ {t}"
    text = text.replace("{name}", name).replace("{time}", t)
    try:
        if s.get("file_id"):
            bot.send_photo(m.chat.id, s["file_id"], caption=text)
        else:
            bot.send_message(m.chat.id, text)
    except Exception as e:
        logging.error(f"welcome send: {e}")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "تنظیم خوشامد" and m.reply_to_message)
def set_welcome(m):
    d = load_data(); gid = str(m.chat.id)
    msg = m.reply_to_message
    if msg.photo:
        fid = msg.photo[-1].file_id
        caption = (msg.caption or "").strip()
        d["welcome"][gid] = {"enabled": True, "type": "photo", "content": caption, "file_id": fid}
    elif msg.text:
        d["welcome"][gid] = {"enabled": True, "type": "text", "content": msg.text.strip(), "file_id": None}
    save_data(d)
    bot.reply_to(m, "✅ پیام خوشامد تنظیم شد. از {name} و {time} می‌تونی داخل متن استفاده کنی.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) in ["خوشامد روشن","خوشامد خاموش"])
def toggle_welcome(m):
    d = load_data(); gid = str(m.chat.id)
    en = cmd_text(m) == "خوشامد روشن"
    d["welcome"].setdefault(gid, {"enabled": True})
    d["welcome"][gid]["enabled"] = en
    save_data(d)
    bot.reply_to(m, "🌕 خوشامد فعال شد." if en else "🌑 خوشامد غیرفعال شد.")

# ================= 👑 مدیران و سودو =================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "افزودن مدیر")
def add_admin(m):
    if not is_sudo(m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    uid = str(m.reply_to_message.from_user.id)
    d["admins"].setdefault(gid, [])
    if uid not in d["admins"][gid]:
        d["admins"][gid].append(uid); save_data(d)
        bot.reply_to(m, f"✅ <code>{uid}</code> به مدیران افزوده شد.")
    else:
        bot.reply_to(m, "⚠️ این کاربر قبلاً مدیر است.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف مدیر")
def remove_admin(m):
    if not is_sudo(m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    uid = str(m.reply_to_message.from_user.id)
    if uid in d["admins"].get(gid, []):
        d["admins"][gid].remove(uid); save_data(d)
        bot.reply_to(m, f"🗑 مدیر <code>{uid}</code> حذف شد.")
    else:
        bot.reply_to(m, "❌ این کاربر مدیر نیست.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست مدیران")
def list_admins(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    lst = d["admins"].get(gid, [])
    if not lst: return bot.reply_to(m, "❗ هیچ مدیری ثبت نشده.")
    txt = "\n".join([f"{i+1}. <code>{u}</code>" for i,u in enumerate(lst)])
    bot.reply_to(m, "👥 <b>لیست مدیران:</b>\n" + txt)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "افزودن سودو")
def add_sudo_cmd(m):
    # فقط مالک اصلی می‌تونه سودو اضافه/حذف کنه
    if m.from_user.id != SUDO_ID: return
    d = load_data()
    uid = str(m.reply_to_message.from_user.id)
    if uid in [str(x) for x in d.get("sudo_list", [])] or uid == str(SUDO_ID):
        return bot.reply_to(m, "⚠️ این کاربر از قبل سودو است.")
    d["sudo_list"].append(int(uid)); save_data(d)
    bot.reply_to(m, f"👑 کاربر <code>{uid}</code> به سودوها اضافه شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف سودو")
def remove_sudo_cmd(m):
    if m.from_user.id != SUDO_ID: return
    d = load_data()
    uid = str(m.reply_to_message.from_user.id)
    if uid in [str(x) for x in d.get("sudo_list", [])]:
        d["sudo_list"] = [int(x) for x in d["sudo_list"] if str(x) != uid]
        save_data(d)
        bot.reply_to(m, f"🗑 سودو <code>{uid}</code> حذف شد.")
    else:
        bot.reply_to(m, "❌ این کاربر در لیست سودوها نیست.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست سودوها")
def list_sudos(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    d = load_data()
    lst = [str(SUDO_ID)] + [str(x) for x in d.get("sudo_list", [])]
    txt = "\n".join([f"{i+1}. <code>{u}</code>" for i,u in enumerate(lst)])
    bot.reply_to(m, "👑 <b>لیست سودوها:</b>\n" + (txt or "—"))

# ================= 🔒 قفل‌ها: فعال/غیرفعال =================
@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل ") or cmd_text(m).startswith("بازکردن "))
def toggle_lock(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    part = cmd_text(m).split()
    if len(part) < 2: return
    key_fa = part[1]
    lock_type = LOCK_MAP.get(key_fa)
    if not lock_type:
        return bot.reply_to(m, "❌ نوع قفل نامعتبر است.")
    en = cmd_text(m).startswith("قفل ")
    d["locks"].setdefault(gid, {k: False for k in LOCK_MAP.values()})
    if d["locks"][gid][lock_type] == en:
        return bot.reply_to(m, "⚠️ همین الان هم همین وضعیت است.")
    d["locks"][gid][lock_type] = en; save_data(d)

    if lock_type == "group":
        bot.send_message(m.chat.id, "🔒 گروه به دستور مدیر بسته شد." if en else "🔓 گروه توسط مدیر باز شد.")
    else:
        bot.reply_to(m, f"{'🔒' if en else '🔓'} قفل {key_fa} {'فعال' if en else 'غیرفعال'} شد.")# ================= 🚧 اعمال قفل‌ها + آمار روزانه =================
@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation','video_note'])
def enforce_and_stats(m):
    try:
        register_group(m.chat.id)
        d = load_data(); gid = str(m.chat.id)

        # مدیرها/سودوها مستثنی از قفل
        if is_admin(m.chat.id, m.from_user.id):
            pass
        else:
            locks = d["locks"].get(gid, {})
            txt = (m.text or "") + " " + (getattr(m, "caption", "") or "")
            # group
            if locks.get("group"):
                try: bot.delete_message(m.chat.id, m.message_id)
                except: pass
                return
            # link
            if locks.get("link") and any(x in txt for x in ["http://","https://","t.me","telegram.me"]):
                try: bot.delete_message(m.chat.id, m.message_id)
                except: pass
                else:
                    bot.send_message(m.chat.id, "🚫 ارسال لینک مجاز نیست.", disable_notification=True)
                return
            # others
            if locks.get("photo") and m.photo:
                try: bot.delete_message(m.chat.id, m.message_id)
                except: pass
                else: bot.send_message(m.chat.id, "🖼 ارسال عکس ممنوع است.", disable_notification=True); return
            if locks.get("video") and m.video:
                try: bot.delete_message(m.chat.id, m.message_id)
                except: pass
                else: bot.send_message(m.chat.id, "🎬 ارسال ویدیو مجاز نیست.", disable_notification=True); return
            if locks.get("sticker") and m.sticker:
                try: bot.delete_message(m.chat.id, m.message_id)
                except: pass
                else: bot.send_message(m.chat.id, "😜 ارسال استیکر ممنوع است.", disable_notification=True); return
            if locks.get("gif") and m.animation:
                try: bot.delete_message(m.chat.id, m.message_id)
                except: pass
                else: bot.send_message(m.chat.id, "🎞 ارسال گیف مجاز نیست.", disable_notification=True); return
            if locks.get("file") and m.document:
                try: bot.delete_message(m.chat.id, m.message_id)
                except: pass
                else: bot.send_message(m.chat.id, "📎 ارسال فایل بسته است.", disable_notification=True); return
            if locks.get("music") and m.audio:
                try: bot.delete_message(m.chat.id, m.message_id)
                except: pass
                else: bot.send_message(m.chat.id, "🎵 ارسال موزیک مجاز نیست.", disable_notification=True); return
            if locks.get("voice") and m.voice:
                try: bot.delete_message(m.chat.id, m.message_id)
                except: pass
                else: bot.send_message(m.chat.id, "🎙 ارسال ویس بسته است.", disable_notification=True); return
            if locks.get("forward") and (m.forward_from or m.forward_from_chat):
                try: bot.delete_message(m.chat.id, m.message_id)
                except: pass
                else: bot.send_message(m.chat.id, "⚠️ فوروارد در این گروه ممنوع است.", disable_notification=True); return

        # ثبت آمار روزانه
        today = str(datetime.now().date())
        st = d["stats"].setdefault(gid, {"date": today, "users": {}, "counts": {k:0 for k in ["msg","photo","video","voice","music","sticker","gif","fwd"]}})
        if st["date"] != today:
            st["date"] = today
            st["users"] = {}
            st["counts"] = {k:0 for k in st["counts"]}

        uid = str(m.from_user.id)
        st["users"][uid] = st["users"].get(uid, 0) + 1
        if m.photo: st["counts"]["photo"] += 1
        elif m.video: st["counts"]["video"] += 1
        elif m.voice: st["counts"]["voice"] += 1
        elif m.audio: st["counts"]["music"] += 1
        elif m.sticker: st["counts"]["sticker"] += 1
        elif m.animation: st["counts"]["gif"] += 1
        elif (m.forward_from or m.forward_from_chat): st["counts"]["fwd"] += 1
        else: st["counts"]["msg"] += 1

        save_data(d)
    except Exception as e:
        logging.error(f"enforce_and_stats: {e}")

# ================= 💬 آمار روزانه =================
@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def group_stats(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    d = load_data(); gid = str(m.chat.id)
    register_group(gid)
    st = d["stats"].get(gid, {})
    counts = st.get("counts", {})
    total = sum(counts.values()) if counts else 0

    if st.get("users"):
        top_uid = max(st["users"], key=st["users"].get)
        try:
            top_name = bot.get_chat_member(m.chat.id, int(top_uid)).user.first_name
        except: top_name = top_uid
        top_line = f"• نفر اول🥇 : ({st['users'][top_uid]} پیام | {top_name})"
    else:
        top_line = "هیچ فعالیتی ثبت نشده است!"

    msg = f"""♡ فعالیت‌های امروز تا این لحظه
➲ تاریخ: {shamsi_date()}
➲ ساعت: {shamsi_time()}
✛ کل پیام‌ها: {total}
✛ فوروارد: {counts.get('fwd',0)}
✛ فیلم: {counts.get('video',0)}
✛ آهنگ: {counts.get('music',0)}
✛ ویس: {counts.get('voice',0)}
✛ عکس: {counts.get('photo',0)}
✛ گیف: {counts.get('gif',0)}
✛ استیکر: {counts.get('sticker',0)}

✶ فعال‌ترین اعضای گروه:
{top_line}

📆 آخرین بروزرسانی: {now_teh_dt().strftime('%Y-%m-%d %H:%M:%S')}
"""
    bot.reply_to(m, msg)

# ================= 🚫 بن / حذف بن / سکوت / حذف سکوت / اخطار / حذف اخطار + لیست‌ها =================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "بن")
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    if is_sudo(uid): return bot.reply_to(m, "⚡ نمی‌توان سودو را بن کرد.")
    try:
        bot.ban_chat_member(m.chat.id, uid)
        d = load_data(); gid = str(m.chat.id)
        d["banned"].setdefault(gid, [])
        if str(uid) not in d["banned"][gid]:
            d["banned"][gid].append(str(uid)); save_data(d)
        bot.reply_to(m, f"🚫 کاربر {m.reply_to_message.from_user.first_name} بن شد.")
    except Exception:
        bot.reply_to(m, "❗ خطا در انجام عملیات بن.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف بن")
def unban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    try:
        bot.unban_chat_member(m.chat.id, uid, only_if_banned=True)
        d = load_data(); gid = str(m.chat.id)
        d["banned"].setdefault(gid, [])
        d["banned"][gid] = [u for u in d["banned"][gid] if u != str(uid)]
        save_data(d)
        bot.reply_to(m, "✅ کاربر از بن خارج شد.")
    except Exception:
        bot.reply_to(m, "❗ خطا در حذف بن.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "سکوت")
def mute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    try:
        perms = types.ChatPermissions(can_send_messages=False)
        bot.restrict_chat_member(m.chat.id, uid, permissions=perms)
        d = load_data(); gid = str(m.chat.id)
        d["muted"].setdefault(gid, [])
        if str(uid) not in d["muted"][gid]:
            d["muted"][gid].append(str(uid)); save_data(d)
        bot.reply_to(m, f"🔇 کاربر {m.reply_to_message.from_user.first_name} در سکوت قرار گرفت.")
    except Exception:
        bot.reply_to(m, "❗ خطا در سکوت کاربر.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف سکوت")
def unmute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    try:
        perms = types.ChatPermissions(can_send_messages=True)
        bot.restrict_chat_member(m.chat.id, uid, permissions=perms)
        d = load_data(); gid = str(m.chat.id)
        d["muted"].setdefault(gid, [])
        d["muted"][gid] = [u for u in d["muted"][gid] if u != str(uid)]
        save_data(d)
        bot.reply_to(m, "🔊 سکوت کاربر برداشته شد.")
    except Exception:
        bot.reply_to(m, "❗ خطا در حذف سکوت.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "اخطار")
def warn_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = str(m.reply_to_message.from_user.id); gid = str(m.chat.id)
    d = load_data()
    d["warns"].setdefault(gid, {})
    d["warns"][gid][uid] = d["warns"][gid].get(uid, 0) + 1
    c = d["warns"][gid][uid]; save_data(d)
    if c >= 3:
        try:
            bot.ban_chat_member(m.chat.id, int(uid))
            d["warns"][gid][uid] = 0; save_data(d)
            bot.reply_to(m, f"🚫 کاربر به دلیل ۳ اخطار بن شد.")
        except Exception:
            bot.reply_to(m, "❗ خطا در بن کاربر.")
    else:
        bot.reply_to(m, f"⚠️ اخطار {c}/3 ثبت شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف اخطار")
def clear_warn(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = str(m.reply_to_message.from_user.id); gid = str(m.chat.id)
    d = load_data()
    if d.get("warns", {}).get(gid, {}).get(uid):
        d["warns"][gid][uid] = 0; save_data(d)
        bot.reply_to(m, "✅ اخطارهای کاربر صفر شد.")
    else:
        bot.reply_to(m, "ℹ️ کاربر اخطاری نداشت.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست بن‌شده‌ها")
def list_banned(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    lst = d["banned"].get(gid, [])
    if not lst: return bot.reply_to(m, "✅ لیست بن خالی است.")
    txt = "\n".join([f"{i+1}. <code>{u}</code>" for i,u in enumerate(lst)])
    bot.reply_to(m, "🚫 <b>لیست بن‌شده‌ها:</b>\n" + txt)

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست سکوت‌ها")
def list_muted(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    lst = d["muted"].get(gid, [])
    if not lst: return bot.reply_to(m, "✅ کسی در سکوت نیست.")
    txt = "\n".join([f"{i+1}. <code>{u}</code>" for i,u in enumerate(lst)])
    bot.reply_to(m, "🔇 <b>لیست سکوت‌ها:</b>\n" + txt)

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست اخطارها")
def list_warns(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    w = d["warns"].get(gid, {})
    if not w: return bot.reply_to(m, "✅ هیچ اخطاری ثبت نشده.")
    txt = "\n".join([f"{i+1}. <code>{uid}</code> — {c} اخطار" for i,(uid,c) in enumerate(w.items())])
    bot.reply_to(m, "⚠️ <b>لیست اخطارها:</b>\n" + txt)

# ================= 😂 جوک و 🔮 فال (ثبت/نمایش/لیست/حذف) =================
@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def joke(m):
    d = load_data(); j = d.get("jokes", [])
    bot.reply_to(m, random.choice(j) if j else "😅 هنوز جوکی ثبت نشده.")

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def fal(m):
    d = load_data(); f = d.get("falls", [])
    bot.reply_to(m, random.choice(f) if f else "🔮 هنوز فالی ثبت نشده.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "ثبت جوک" and m.reply_to_message)
def add_joke(m):
    d = load_data(); txt = (m.reply_to_message.text or "").strip()
    if not txt: return bot.reply_to(m, "⚠️ فقط متن رو ریپلای کن.")
    d["jokes"].append(txt); save_data(d)
    bot.reply_to(m, "😂 جوک ذخیره شد.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "ثبت فال" and m.reply_to_message)
def add_fal(m):
    d = load_data(); txt = (m.reply_to_message.text or "").strip()
    if not txt: return bot.reply_to(m, "⚠️ فقط متن رو ریپلای کن.")
    d["falls"].append(txt); save_data(d)
    bot.reply_to(m, "🔮 فال ذخیره شد.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "لیست جوک‌ها")
def list_jokes(m):
    d = load_data(); j = d.get("jokes", [])
    if not j: return bot.reply_to(m, "❗ جوکی ثبت نشده.")
    txt = "\n".join([f"{i+1}. {t}" for i,t in enumerate(j)])
    bot.reply_to(m, "📜 <b>لیست جوک‌ها:</b>\n" + txt)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "لیست فال‌ها")
def list_falls(m):
    d = load_data(); f = d.get("falls", [])
    if not f: return bot.reply_to(m, "❗ فالی ثبت نشده.")
    txt = "\n".join([f"{i+1}. {t}" for i,t in enumerate(f)])
    bot.reply_to(m, "📜 <b>لیست فال‌ها:</b>\n" + txt)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف جوک "))
def del_joke(m):
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        d = load_data(); j = d.get("jokes", [])
        j.pop(idx); d["jokes"] = j; save_data(d)
        bot.reply_to(m, "🗑 جوک حذف شد.")
    except Exception:
        bot.reply_to(m, "❗ شماره جوک نامعتبر است.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف فال "))
def del_fal(m):
    try:
        idx = int(cmd_text(m).split()[2]) - 1
        d = load_data(); f = d.get("falls", [])
        f.pop(idx); d["falls"] = f; save_data(d)
        bot.reply_to(m, "🗑 فال حذف شد.")
    except Exception:
        bot.reply_to(m, "❗ شماره فال نامعتبر است.")

# ================= 🧹 پاکسازی =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "پاکسازی")
def clear_recent(m):
    deleted = 0
    for i in range(1, 101):
        try:
            bot.delete_message(m.chat.id, m.message_id - i); deleted += 1
        except: pass
    bot.send_message(m.chat.id, f"🧼 {deleted} پیام اخیر پاک شد.", disable_notification=True)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف "))
def delete_n(m):
    try:
        n = int(cmd_text(m).split()[1])
    except:
        return bot.reply_to(m, "❗ فرمت درست: حذف 20")
    deleted = 0
    for i in range(1, n+1):
        try:
            bot.delete_message(m.chat.id, m.message_id - i); deleted += 1
        except: pass
    bot.send_message(m.chat.id, f"🗑 {deleted} پیام پاک شد.", disable_notification=True)

# ================= 📢 ارسال همگانی (فقط سودو) =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ارسال" and m.reply_to_message)
def broadcast(m):
    d = load_data()
    users  = list(set(d.get("users", [])))
    groups = [int(g) for g in d.get("welcome", {}).keys()]
    msg = m.reply_to_message; total = 0
    for uid in users + groups:
        try:
            if msg.text:
                bot.send_message(uid, msg.text)
            elif msg.photo:
                bot.send_photo(uid, msg.photo[-1].file_id, caption=msg.caption or "")
            total += 1
        except: continue
    bot.reply_to(m, f"📢 پیام به {total} مقصد ارسال شد.")

# ================= 🎛️ پنل شیشه‌ای لوکس =================
def main_panel():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🔒 قفل‌ها", callback_data="locks"),
        types.InlineKeyboardButton("👋 خوشامد", callback_data="welcome"),
        types.InlineKeyboardButton("🚫 بن/سکوت/اخطار", callback_data="ban"),
        types.InlineKeyboardButton("😂 جوک و فال", callback_data="fun"),
        types.InlineKeyboardButton("📊 آمار", callback_data="stats"),
        types.InlineKeyboardButton("🧹 پاکسازی", callback_data="clear"),
        types.InlineKeyboardButton("👥 مدیران", callback_data="admins"),
        types.InlineKeyboardButton("👑 سودوها", callback_data="sudos"),
        types.InlineKeyboardButton("ℹ️ راهنما", callback_data="help"),
        types.InlineKeyboardButton("🔙 بستن پنل", callback_data="close")
    )
    return kb

@bot.message_handler(commands=["panel", "پنل"])
def open_panel(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    bot.send_message(m.chat.id, "🎛️ <b>پنل مدیریتی لوکس فعال شد!</b>\nاز دکمه‌ها استفاده کن 👇",
                     reply_markup=main_panel())

@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    data = call.data
    if data == "close":
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
    elif data == "help":
        txt = (
            "📘 <b>راهنمای سریع:</b>\n"
            "• آیدی / ساعت / آمار / لینک گروه / لینک ربات\n"
            "• قفل/بازکردن (عکس/فیلم/استیکر/لینک/...)\n"
            "• خوشامد: تنظیم متن/عکس، روشن/خاموش\n"
            "• بن/حذف بن | سکوت/حذف سکوت | اخطار/حذف اخطار + لیست‌ها\n"
            "• جوک/فال + ثبت/حذف/لیست\n"
            "• پاکسازی | حذف N\n"
            "• ارسال (فقط سودو)"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="main"))
        try:
            bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=kb)
        except: pass
    elif data == "main":
        try:
            bot.edit_message_text("🎛️ منوی اصلی:", call.message.chat.id, call.message.message_id, reply_markup=main_panel())
        except: pass

# ================= 👑 پاسخ مخصوص سودو =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).lower() in ["سلام","ربات","bot"])
def sudo_reply(m):
    bot.reply_to(m, f"سلام 👑 {m.from_user.first_name}!\nدر خدمتتم سودوی عزیز 🤖")

# ================= 🚀 اجرای ربات =================
if __name__ == "__main__":
    print("🤖 ربات مدیریتی Persian Lux Panel – آماده به کار!")
    bot.infinity_polling(timeout=60, long_polling_timeout=30)
