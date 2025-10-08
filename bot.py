# -*- coding: utf-8 -*-
# Persian Lux Panel V16.2 – Full & Stable (Part 1/2)
# Designed for Mohammad 👑

import os, json, random, time, logging
from datetime import datetime
import pytz, jdatetime
import telebot
from telebot import types

# =============== ⚙️ تنظیمات پایه ===============
TOKEN   = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot     = telebot.TeleBot(TOKEN, parse_mode="HTML")

DATA_FILE = "data.json"
LOG_FILE  = "error.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# =============== 💾 داده‌ها ===============
def base_data():
    return {
        "welcome": {},        # gid -> {enabled,type,content,file_id}
        "locks": {},          # gid -> {link:bool,...}
        "admins": {},         # gid -> [uid,...]
        "sudo_list": [],      # [uid,...] (اضافه بر SUDO_ID)
        "banned": {},         # gid -> [uid,...]
        "muted": {},          # gid -> [uid,...]
        "warns": {},          # gid -> {uid:count}
        "users": [],          # کسانی که /start داده‌اند
        "jokes": [],          # جوک‌ها
        "falls": [],          # فال‌ها
        "stats": {}           # gid -> { "YYYY-MM-DD": {counts...,"by_user":{uid:count}} }
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(base_data())
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = base_data()
    # تکمیل کلیدهای جاافتاده
    template = base_data()
    for k in template:
        if k not in data:
            data[k] = template[k]
    save_data(data)
    return data

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def register_group(gid):
    d = load_data()
    gid = str(gid)
    d["welcome"].setdefault(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})
    d["locks"].setdefault(gid, {
        "link": False, "group": False, "photo": False, "video": False,
        "sticker": False, "gif": False, "file": False, "music": False,
        "voice": False, "forward": False
    })
    d["banned"].setdefault(gid, [])
    d["muted"].setdefault(gid, [])
    d["admins"].setdefault(gid, [])
    d["warns"].setdefault(gid, {})
    d["stats"].setdefault(gid, {})
    save_data(d)

# =============== 🧩 ابزارها ===============
def now_teh_dt():
    return datetime.now(pytz.timezone("Asia/Tehran"))

def shamsi_date():
    return jdatetime.datetime.now().strftime("%A %d %B %Y")

def shamsi_time():
    return jdatetime.datetime.now().strftime("%H:%M:%S")

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

# =============== 👋 استارت + راهنما ===============
@bot.message_handler(commands=["start"])
def start_cmd(m):
    d = load_data()
    u = str(m.from_user.id)
    if u not in [str(x) for x in d.get("users", [])]:
        d["users"].append(u)
        save_data(d)
    bot.reply_to(m, "👋 سلام! ربات مدیریتی Persian Lux Panel فعال است.\nبرای راهنما بنویس: «راهنما» یا «فعالیت امروز»")

@bot.message_handler(func=lambda m: cmd_text(m) == "راهنما")
def show_help(m):
    txt = (
        "📘 <b>راهنمای Persian Lux Panel V16.2</b>\n\n"
        "🆔 عمومی:\n"
        "• آیدی / ایدی — ساعت — فعالیت امروز — لینک گروه — لینک ربات\n\n"
        "👋 خوشامد:\n"
        "• تنظیم خوشامد (ریپلای به متن/عکس)\n"
        "• خوشامد روشن / خوشامد خاموش\n"
        "• از {name} و {time} در متن خوشامد می‌تونی استفاده کنی\n\n"
        "🔒 قفل‌ها:\n"
        "• قفل/بازکردن لینک، گروه، عکس، ویدیو، فایل، موزیک، ویس، استیکر، گیف، فوروارد\n\n"
        "👑 مدیر و سودو:\n"
        "• (ریپلای) افزودن مدیر / حذف مدیر — لیست مدیران\n"
        "• (فقط مالک) افزودن سودو / حذف سودو — لیست سودوها\n\n"
        "🚫 نظم گروه:\n"
        "• (ریپلای) بن / حذف بن — سکوت / حذف سکوت — اخطار / حذف اخطار — لیست اخطارها\n\n"
        "😂 تفریح:\n"
        "• (ریپلای) ثبت جوک / ثبت فال — جوک — فال — لیست جوک — لیست فال — حذف جوک N — حذف فال N\n\n"
        "🧹 پاکسازی:\n"
        "• پاکسازی (۱۰۰ پیام آخر) — حذف N\n\n"
        "📢 همگانی (فقط سودو):\n"
        "• (ریپلای) ارسال — متن/عکس به همه کاربران و گروه‌ها\n\n"
        "👑 پاسخ به سودو: «سلام / ربات / bot / هی»\n"
    )
    bot.reply_to(m, txt)

# =============== 🆔 آیدی لوکس / ساعت / لینک‌ها ===============
@bot.message_handler(func=lambda m: cmd_text(m) in ["آیدی", "ایدی"])
def show_id(m):
    user = m.from_user
    name = user.first_name or "کاربر"
    uid  = user.id
    cap = (
        f"🧾 <b>مشخصات کاربر</b>\n"
        f"👤 نام: {name}\n"
        f"🆔 آیدی عددی: <code>{uid}</code>\n"
        f"💬 آیدی گروه: <code>{m.chat.id}</code>\n"
        f"📅 تاریخ: {shamsi_date()}\n"
        f"⏰ ساعت: {shamsi_time()}"
    )
    try:
        ph = bot.get_user_profile_photos(uid, limit=1)
        if ph.total_count > 0:
            bot.send_photo(m.chat.id, ph.photos[0][-1].file_id, caption=cap)
        else:
            bot.reply_to(m, cap)
    except Exception:
        bot.reply_to(m, cap)

@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def show_time(m):
    bot.reply_to(m, f"⏰ {shamsi_time()}\n📅 {shamsi_date()}")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک ربات")
def bot_link(m):
    uname = bot.get_me().username
    bot.reply_to(m, f"🤖 لینک ربات:\nhttps://t.me/{uname}")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک گروه")
def group_link(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 لینک گروه:\n{link}")
    except Exception:
        bot.reply_to(m, "⚠️ دسترسی ساخت/دریافت لینک ندارم.")

# =============== 📊 «آمار» کلی ربات (اختیاری) ===============
@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def bot_stats(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)):
        return
    d = load_data()
    users  = len(set(d.get("users", [])))
    groups = len(d.get("welcome", {}))
    bot.reply_to(
        m,
        f"📊 <b>آمار ربات</b>\n"
        f"👤 کاربران: {users}\n"
        f"👥 گروه‌ها: {groups}\n"
        f"📅 {shamsi_date()} | ⏰ {shamsi_time()}"
    )

# =============== 👋 خوشامد ===============
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new(m):
    register_group(m.chat.id)
    d = load_data(); gid = str(m.chat.id)
    s = d["welcome"].get(gid, {"enabled": True})
    if not s.get("enabled", True):
        return
    user = m.new_chat_members[0]
    name = user.first_name or "دوست جدید"
    text = s.get("content") or f"✨ سلام {name}!\nبه گروه <b>{m.chat.title}</b> خوش اومدی 🌸\n⏰ {shamsi_time()}"
    text = text.replace("{name}", name).replace("{time}", shamsi_time())
    try:
        if s.get("file_id"):
            bot.send_photo(m.chat.id, s["file_id"], caption=text)
        else:
            bot.send_message(m.chat.id, text)
    except Exception as e:
        logging.error(f"welcome send: {e}")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "تنظیم خوشامد")
def set_welcome(m):
    d = load_data(); gid = str(m.chat.id)
    msg = m.reply_to_message
    if msg.photo:
        d["welcome"][gid] = {
            "enabled": True, "type": "photo",
            "content": (msg.caption or ""),
            "file_id": msg.photo[-1].file_id
        }
    elif msg.text:
        d["welcome"][gid] = {"enabled": True, "type": "text", "content": msg.text, "file_id": None}
    save_data(d)
    bot.reply_to(m, "✅ پیام خوشامد تنظیم شد. از {name} و {time} داخل متن می‌تونی استفاده کنی.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) in ["خوشامد روشن", "خوشامد خاموش"])
def toggle_welcome(m):
    d = load_data(); gid = str(m.chat.id)
    en = cmd_text(m) == "خوشامد روشن"
    d["welcome"].setdefault(gid, {"enabled": True})
    d["welcome"][gid]["enabled"] = en
    save_data(d)
    bot.reply_to(m, "🟢 خوشامد روشن شد." if en else "🔴 خوشامد خاموش شد.")

# =============== 🔒 قفل‌ها: فعال/غیرفعال ===============
LOCK_MAP = {
    "لینک": "link", "گروه": "group", "عکس": "photo", "ویدیو": "video",
    "استیکر": "sticker", "گیف": "gif", "فایل": "file", "موزیک": "music",
    "ویس": "voice", "فوروارد": "forward"
}

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
        if en:
            bot.send_message(
                m.chat.id,
                "🚫 <b>اعلان امنیتی</b>\n"
                "گروه موقتاً <b>بسته شد</b> و فقط مدیران می‌توانند پیام ارسال کنند.\n"
                f"⏰ {shamsi_time()}"
            )
        else:
            bot.send_message(
                m.chat.id,
                "✅ <b>اعلان</b>\n"
                "گروه <b>باز شد</b> — همه می‌تونن گفت‌وگو کنن 🌸\n"
                f"⏰ {shamsi_time()}"
            )
    else:
        bot.reply_to(m, f"{'🔒' if en else '🔓'} قفل {key_fa} {'فعال' if en else 'غیرفعال'} شد.")

# =============== 👑 مدیر و سودو ===============
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "افزودن مدیر")
def add_admin(m):
    if not is_sudo(m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    uid = str(m.reply_to_message.from_user.id)
    d["admins"].setdefault(gid, [])
    if uid in d["admins"][gid]:
        return bot.reply_to(m, "⚠️ این کاربر از قبل مدیر است.")
    d["admins"][gid].append(uid); save_data(d)
    bot.reply_to(m, f"✅ <a href='tg://user?id={uid}'>کاربر</a> به مدیران افزوده شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف مدیر")
def remove_admin(m):
    if not is_sudo(m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    uid = str(m.reply_to_message.from_user.id)
    if uid not in d["admins"].get(gid, []):
        return bot.reply_to(m, "❌ این کاربر مدیر نیست.")
    d["admins"][gid].remove(uid); save_data(d)
    bot.reply_to(m, "🗑 مدیر حذف شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست مدیران")
def list_admins(m):
    d = load_data(); gid = str(m.chat.id)
    lst = d["admins"].get(gid, [])
    if not lst:
        return bot.reply_to(m, "📋 هیچ مدیری ثبت نشده.")
    txt = "👑 <b>لیست مدیران</b>:\n" + "\n".join([f"• <a href='tg://user?id={u}'>کاربر {u}</a>" for u in lst])
    bot.reply_to(m, txt)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "افزودن سودو")
def add_sudo_cmd(m):
    if m.from_user.id != SUDO_ID: return
    d = load_data(); uid = str(m.reply_to_message.from_user.id)
    if uid in [str(x) for x in d.get("sudo_list", [])] or uid == str(SUDO_ID):
        return bot.reply_to(m, "⚠️ این کاربر از قبل سودو است.")
    d["sudo_list"].append(uid); save_data(d)
    bot.reply_to(m, f"✅ <a href='tg://user?id={uid}'>کاربر</a> به سودوها اضافه شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف سودو")
def remove_sudo_cmd(m):
    if m.from_user.id != SUDO_ID: return
    d = load_data(); uid = str(m.reply_to_message.from_user.id)
    if uid not in [str(x) for x in d.get("sudo_list", [])]:
        return bot.reply_to(m, "❌ این کاربر در لیست سودوها نیست.")
    d["sudo_list"] = [str(x) for x in d["sudo_list"] if str(x) != uid]
    save_data(d)
    bot.reply_to(m, "🗑 سودو حذف شد.")

@bot.message_handler(func=lambda m: cmd_text(m) in ["لیست سودو","لیست سودوها"])
def list_sudo(m):
    if not is_sudo(m.from_user.id): return
    d = load_data(); s = [str(x) for x in d.get("sudo_list", [])]
    if not s:
        return bot.reply_to(m, "❗ هیچ سودویی ثبت نشده.")
    txt = "👑 <b>لیست سودوها</b>:\n" + "\n".join([f"• <a href='tg://user?id={u}'>کاربر {u}</a>" for u in s] + [f"• <a href='tg://user?id={SUDO_ID}'>مالک اصلی</a>"])
    bot.reply_to(m, txt)

# =============== 🚫 بن / سکوت / اخطار + لیست‌ها ===============
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
        bot.reply_to(m, f"🚫 کاربر <a href='tg://user?id={uid}'>بن</a> شد.")
    except Exception:
        bot.reply_to(m, "❗ خطا در بن کاربر.")

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

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست بن‌شده‌ها")
def list_banned(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    lst = d["banned"].get(gid, [])
    if not lst: return bot.reply_to(m, "✅ لیست بن خالی است.")
    txt = "\n".join([f"{i+1}. <code>{u}</code>" for i,u in enumerate(lst)])
    bot.reply_to(m, "🚫 <b>لیست بن‌شده‌ها:</b>\n" + txt)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "سکوت")
def mute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    try:
        perms = types.ChatPermissions(can_send_messages=False)
        bot.restrict_chat_member(m.chat.id, uid, permissions=perms)
    except Exception:
        pass
    d = load_data(); gid = str(m.chat.id)
    d["muted"].setdefault(gid, [])
    if str(uid) not in d["muted"][gid]:
        d["muted"][gid].append(str(uid)); save_data(d)
    bot.reply_to(m, f"🔇 کاربر <a href='tg://user?id={uid}'>ساکت</a> شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف سکوت")
def unmute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    try:
        perms = types.ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
        bot.restrict_chat_member(m.chat.id, uid, permissions=perms)
    except Exception:
        pass
    d = load_data(); gid = str(m.chat.id)
    d["muted"].setdefault(gid, [])
    d["muted"][gid] = [u for u in d["muted"][gid] if u != str(uid)]
    save_data(d)
    bot.reply_to(m, f"🔊 سکوت کاربر <a href='tg://user?id={uid}'>برداشته</a> شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "اخطار")
def warn_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = str(m.reply_to_message.from_user.id); gid = str(m.chat.id)
    d = load_data()
    d["warns"].setdefault(gid, {})
    d["warns"][gid][uid] = d["warns"][gid].get(uid, 0) + 1
    c = d["warns"][gid][uid]; save_data(d)
    msg = f"⚠️ کاربر <a href='tg://user?id={uid}'>اخطار {c}</a> گرفت."
    if c >= 3:
        try:
            bot.ban_chat_member(m.chat.id, int(uid))
            msg += "\n🚫 چون ۳ اخطار گرفت، از گروه اخراج شد."
            d["warns"][gid][uid] = 0; save_data(d)
        except Exception:
            pass
    bot.reply_to(m, msg)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف اخطار")
def clear_warn(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = str(m.reply_to_message.from_user.id); gid = str(m.chat.id)
    d = load_data(); d["warns"].setdefault(gid, {})
    if d["warns"][gid].get(uid):
        d["warns"][gid][uid] = 0; save_data(d)
        bot.reply_to(m, "✅ اخطارهای کاربر صفر شد.")
    else:
        bot.reply_to(m, "ℹ️ کاربر اخطاری نداشت.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست اخطارها")
def list_warns(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    w = d["warns"].get(gid, {})
    if not w: return bot.reply_to(m, "✅ هیچ اخطاری ثبت نشده.")
    txt = "\n".join([f"{i+1}. <code>{uid}</code> — {c} اخطار" for i,(uid,c) in enumerate(w.items())])
    bot.reply_to(m, "⚠️ <b>لیست اخطارها:</b>\n" + txt)

# =============== 😂 جوک و 🔮 فال ===============
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت جوک")
def add_joke(m):
    d = load_data(); txt = (m.reply_to_message.text or "").strip()
    if not txt: return bot.reply_to(m, "⚠️ لطفاً روی پیام متنی ریپلای کن.")
    d["jokes"].append(txt); save_data(d)
    bot.reply_to(m, "😂 جوک ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def joke(m):
    d = load_data(); j = d.get("jokes", [])
    bot.reply_to(m, random.choice(j) if j else "😅 هنوز جوکی ثبت نشده.")

@bot.message_handler(func=lambda m: cmd_text(m) in ["لیست جوک","لیست جوک‌ها"])
def list_jokes(m):
    d = load_data(); j = d.get("jokes", [])
    if not j: return bot.reply_to(m, "❗ هیچ جوکی ثبت نشده.")
    txt = "\n".join([f"{i+1}. {t}" for i,t in enumerate(j)])
    bot.reply_to(m, "📜 <b>لیست جوک‌ها:</b>\n" + txt)

@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف جوک "))
def del_joke(m):
    try:
        idx = int(cmd_text(m).split()[2]) - 1
    except Exception:
        return bot.reply_to(m, "❗ فرمت درست: حذف جوک 3")
    d = load_data(); j = d.get("jokes", [])
    if 0 <= idx < len(j):
        removed = j.pop(idx); d["jokes"] = j; save_data(d)
        bot.reply_to(m, f"🗑 جوک حذف شد:\n{removed}")
    else:
        bot.reply_to(m, "❗ شماره جوک نامعتبر است.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت فال")
def add_fal(m):
    d = load_data(); txt = (m.reply_to_message.text or "").strip()
    if not txt: return bot.reply_to(m, "⚠️ لطفاً روی پیام متنی ریپلای کن.")
    d["falls"].append(txt); save_data(d)
    bot.reply_to(m, "🔮 فال ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def fal(m):
    d = load_data(); f = d.get("falls", [])
    bot.reply_to(m, random.choice(f) if f else "🔮 هنوز فالی ثبت نشده.")

@bot.message_handler(func=lambda m: cmd_text(m) in ["لیست فال","لیست فال‌ها"])
def list_falls(m):
    d = load_data(); f = d.get("falls", [])
    if not f: return bot.reply_to(m, "❗ فالی ثبت نشده.")
    txt = "\n".join([f"{i+1}. {t}" for i,t in enumerate(f)])
    bot.reply_to(m, "📜 <b>لیست فال‌ها:</b>\n" + txt)

@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف فال "))
def del_fal(m):
    try:
        id# Persian Lux Panel V16.2 – Full & Stable (Part 2/2)
# ================= 🚧 اعمال قفل‌ها + آمار روزانه =================
@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker', 'animation', 'video_note'])
def enforce_and_stats(m):
    try:
        register_group(m.chat.id)
        d = load_data()
        gid = str(m.chat.id)

        # --- اعمال قفل‌ها برای کاربران عادی ---
        if not is_admin(m.chat.id, m.from_user.id):
            locks = d["locks"].get(gid, {})
            txt = (m.text or "") + " " + (getattr(m, "caption", "") or "")

            # قفل گروه
            if locks.get("group"):
                bot.delete_message(m.chat.id, m.message_id)
                return

            # قفل لینک
            if locks.get("link") and any(x in txt for x in ["http://", "https://", "t.me/", "telegram.me/", "www."]):
                bot.delete_message(m.chat.id, m.message_id)
                bot.send_message(m.chat.id, "🚫 ارسال لینک مجاز نیست.", disable_notification=True)
                return

            # قفل عکس
            if locks.get("photo") and m.photo:
                bot.delete_message(m.chat.id, m.message_id)
                bot.send_message(m.chat.id, "🖼 ارسال عکس ممنوع است.", disable_notification=True)
                return

            # قفل ویدیو
            if locks.get("video") and m.video:
                bot.delete_message(m.chat.id, m.message_id)
                bot.send_message(m.chat.id, "🎬 ارسال ویدیو مجاز نیست.", disable_notification=True)
                return

            # قفل استیکر
            if locks.get("sticker") and m.sticker:
                bot.delete_message(m.chat.id, m.message_id)
                bot.send_message(m.chat.id, "😜 ارسال استیکر ممنوع است.", disable_notification=True)
                return

            # قفل گیف
            if locks.get("gif") and m.animation:
                bot.delete_message(m.chat.id, m.message_id)
                bot.send_message(m.chat.id, "🎞 ارسال گیف مجاز نیست.", disable_notification=True)
                return

            # قفل فایل
            if locks.get("file") and m.document:
                bot.delete_message(m.chat.id, m.message_id)
                bot.send_message(m.chat.id, "📎 ارسال فایل بسته است.", disable_notification=True)
                return

            # قفل موزیک
            if locks.get("music") and m.audio:
                bot.delete_message(m.chat.id, m.message_id)
                bot.send_message(m.chat.id, "🎵 ارسال موزیک مجاز نیست.", disable_notification=True)
                return

            # قفل ویس
            if locks.get("voice") and m.voice:
                bot.delete_message(m.chat.id, m.message_id)
                bot.send_message(m.chat.id, "🎙 ارسال ویس بسته است.", disable_notification=True)
                return

            # قفل فوروارد
            if locks.get("forward") and (m.forward_from or m.forward_from_chat):
                bot.delete_message(m.chat.id, m.message_id)
                bot.send_message(m.chat.id, "⚠️ فوروارد در این گروه ممنوع است.", disable_notification=True)
                return

        # --- ثبت آمار فعالیت امروز ---
        today = datetime.now().strftime("%Y-%m-%d")
        d["stats"].setdefault(gid, {})
        d["stats"][gid].setdefault(today, {
            "total": 0, "forward": 0, "video": 0, "voice": 0,
            "photo": 0, "sticker": 0, "gif": 0, "audio": 0, "by_user": {}
        })
        s = d["stats"][gid][today]
        s["total"] += 1
        uid = str(m.from_user.id)
        s["by_user"][uid] = s["by_user"].get(uid, 0) + 1

        if m.forward_from or m.forward_from_chat:
            s["forward"] += 1
        if m.photo:
            s["photo"] += 1
        if m.video:
            s["video"] += 1
        if m.voice:
            s["voice"] += 1
        if m.audio:
            s["audio"] += 1
        if m.sticker:
            s["sticker"] += 1
        if m.animation:
            s["gif"] += 1

        save_data(d)
    except Exception as e:
        logging.error(f"enforce_and_stats error: {e}")

# ================= 📊 فعالیت امروز =================
@bot.message_handler(func=lambda m: cmd_text(m) == "فعالیت امروز")
def daily_stats(m):
    d = load_data()
    gid = str(m.chat.id)
    today = datetime.now().strftime("%Y-%m-%d")
    s = d["stats"].get(gid, {}).get(today, {
        "total": 0, "forward": 0, "video": 0, "voice": 0,
        "photo": 0, "sticker": 0, "gif": 0, "audio": 0, "by_user": {}
    })

    # پیدا کردن فعال‌ترین کاربر
    if s["by_user"]:
        top_uid = max(s["by_user"], key=lambda u: s["by_user"][u])
        try:
            top_name = bot.get_chat_member(int(gid), int(top_uid)).user.first_name
        except Exception:
            top_name = top_uid
        top_line = f"• نفر اول🥇 : ({s['by_user'][top_uid]} پیام | {top_name})"
    else:
        top_line = "هیچ فعالیتی ثبت نشده است!"

    msg = (
        f"♡ فعالیت های امروز تا این لحظه :\n\n"
        f"➲ تاریخ : {shamsi_date()}\n"
        f"➲ ساعت : {shamsi_time()}\n\n"
        f"✛ کل پیام‌ها : {s['total']}\n"
        f"✛ پیام فورواردی : {s['forward']}\n"
        f"✛ فیلم : {s['video']}\n"
        f"✛ آهنگ : {s['audio']}\n"
        f"✛ ویس : {s['voice']}\n"
        f"✛ عکس : {s['photo']}\n"
        f"✛ گیف : {s['gif']}\n"
        f"✛ استیکر : {s['sticker']}\n\n"
        f"✶ فعال‌ترین اعضای گروه:\n{top_line}\n\n"
        f"✧ Persian Lux Panel V16.2 👑"
    )
    bot.reply_to(m, msg)

# ================= 🚀 اجرای نهایی =================
if __name__ == "__main__":
    print("🤖 Persian Lux Panel V16.2 is running...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            logging.error(f"polling crash: {e}")
            time.sleep(5)
