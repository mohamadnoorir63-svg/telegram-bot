# -*- coding: utf-8 -*-
# Persian Lux Panel V15 – Full Rewrite (ID + Joke Updated)
# Designed for Mohammad 👑

import os, json, random, time, logging
from datetime import datetime
import pytz, jdatetime
import telebot
from telebot import types

# ================= ⚙️ تنظیمات پایه =================
TOKEN   = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot     = telebot.TeleBot(TOKEN, parse_mode="HTML")

DATA_FILE = "data.json"
LOG_FILE  = "error.log"

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# ================= 💾 فایل داده =================
def base_data():
    return {
        "welcome": {}, "locks": {}, "admins": {}, "sudo_list": [],
        "banned": {}, "muted": {}, "warns": {}, "users": [],
        "jokes": [], "falls": []
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
    data["welcome"].setdefault(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})
    data["locks"].setdefault(gid, {k: False for k in ["link","group","photo","video","sticker","gif","file","music","voice","forward"]})
    save_data(data)

# ================= 🧩 ابزارها =================
def shamsi_date(): return jdatetime.datetime.now().strftime("%A %d %B %Y")
def shamsi_time(): return jdatetime.datetime.now().strftime("%H:%M:%S")
def cmd_text(m): return (getattr(m, "text", None) or "").strip()

def is_sudo(uid):
    d = load_data()
    return str(uid) in [str(SUDO_ID)] + d.get("sudo_list", [])

def is_admin(chat_id, uid):
    d = load_data(); gid = str(chat_id)
    if is_sudo(uid): return True
    if str(uid) in d["admins"].get(gid, []): return True
    try:
        st = bot.get_chat_member(chat_id, uid).status
        return st in ("administrator", "creator")
    except: return False

# ================= 🆔 آیدی لوکس =================
@bot.message_handler(func=lambda m: cmd_text(m) in ["آیدی","ایدی"])
def show_id(m):
    try:
        user = m.from_user
        name = user.first_name or ""
        uid = user.id
        caption = (
            f"🧾 <b>مشخصات کاربر</b>\n"
            f"👤 نام: {name}\n"
            f"🆔 آیدی عددی: <code>{uid}</code>\n"
            f"💬 آیدی گروه: <code>{m.chat.id}</code>\n"
            f"📅 تاریخ: {shamsi_date()}\n"
            f"⏰ ساعت: {shamsi_time()}"
        )
        photos = bot.get_user_profile_photos(uid)
        if photos.total_count > 0:
            file_id = photos.photos[0][-1].file_id
            bot.send_photo(m.chat.id, file_id, caption=caption)
        else:
            bot.reply_to(m, caption)
    except Exception as e:
        logging.error(f"show_id error: {e}")
        bot.reply_to(m, f"🆔 <code>{m.from_user.id}</code>\n⏰ {shamsi_time()}")

# ================= 🕒 آمار / ساعت =================
@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def show_stats(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data = load_data()
    users = len(set(data.get("users", [])))
    groups = len(data.get("welcome", {}))
    bot.reply_to(m,
        f"📊 <b>آمار ربات Persian Lux Panel</b>\n"
        f"👤 کاربران: {users}\n👥 گروه‌ها: {groups}\n"
        f"📅 {shamsi_date()} | ⏰ {shamsi_time()}")

@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def show_time(m):
    bot.reply_to(m, f"⏰ {shamsi_time()} | 📅 {shamsi_date()}")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک ربات")
def bot_link(m):
    bot.reply_to(m, f"🤖 لینک ربات:\nhttps://t.me/{bot.get_me().username}")

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک گروه")
def group_link(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 لینک گروه:\n{link}")
    except:
        bot.reply_to(m, "⚠️ دسترسی ساخت لینک ندارم.")

# ================= 👋 خوشامد =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new(m):
    register_group(m.chat.id)
    data = load_data(); gid = str(m.chat.id)
    s = data["welcome"].get(gid, {"enabled": True})
    if not s.get("enabled", True): return
    user = m.new_chat_members[0]
    name = user.first_name or "دوست جدید"
    text = s.get("content") or f"✨ سلام {name}!\nبه گروه <b>{m.chat.title}</b> خوش اومدی 🌸\n⏰ {shamsi_time()}"
    text = text.replace("{name}", name).replace("{time}", shamsi_time())
    if s.get("file_id"):
        bot.send_photo(m.chat.id, s["file_id"], caption=text)
    else:
        bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "تنظیم خوشامد")
def set_welcome(m):
    data = load_data(); gid = str(m.chat.id)
    msg = m.reply_to_message
    if msg.photo:
        fid = msg.photo[-1].file_id
        data["welcome"][gid] = {"enabled": True, "type": "photo", "content": msg.caption or "", "file_id": fid}
    elif msg.text:
        data["welcome"][gid] = {"enabled": True, "type": "text", "content": msg.text, "file_id": None}
    save_data(data)
    bot.reply_to(m, "✅ پیام خوشامد جدید تنظیم شد.\nاز {name} و {time} در متن می‌تونی استفاده کنی.")

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) in ["خوشامد روشن","خوشامد خاموش"])
def toggle_welcome(m):
    data = load_data(); gid = str(m.chat.id)
    en = cmd_text(m) == "خوشامد روشن"
    data["welcome"].setdefault(gid, {"enabled": True})
    data["welcome"][gid]["enabled"] = en
    save_data(data)
    bot.reply_to(m, "🟢 خوشامد روشن شد." if en else "🔴 خوشامد خاموش شد.")# ================= 🔒 قفل‌ها =================
LOCK_MAP = {
    "لینک":"link","گروه":"group","عکس":"photo","ویدیو":"video",
    "استیکر":"sticker","گیف":"gif","فایل":"file","موزیک":"music",
    "ویس":"voice","فوروارد":"forward"
}

@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل ") or cmd_text(m).startswith("بازکردن "))
def toggle_lock(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    part = cmd_text(m).split(" ")
    if len(part) < 2: return
    key_fa = part[1]; lock_type = LOCK_MAP.get(key_fa)
    if not lock_type: return bot.reply_to(m, "❌ نوع قفل نامعتبر است.")
    en = cmd_text(m).startswith("قفل ")
    d["locks"].setdefault(gid, {k: False for k in LOCK_MAP.values()})
    if d["locks"][gid][lock_type] == en:
        return bot.reply_to(m, "⚠️ این قفل همین حالا هم در همین حالت است.")
    d["locks"][gid][lock_type] = en; save_data(d)
    if lock_type == "group":
        if en:
            bot.send_message(m.chat.id, "🚫 گروه موقتاً <b>بسته شد</b> ❌\n🔒 فقط مدیران می‌توانند پیام ارسال کنند.\n⏰ " + shamsi_time())
        else:
            bot.send_message(m.chat.id, "✅ گروه <b>باز شد</b> 🌸\n💬 حالا همه می‌تونن گفتگو کنن!\n⏰ " + shamsi_time())
    else:
        bot.reply_to(m, f"{'🔒' if en else '🔓'} قفل {key_fa} {'فعال' if en else 'غیرفعال'} شد.")

# ================= 👑 مدیر و سودو =================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "افزودن مدیر")
def add_admin(m):
    if not is_sudo(m.from_user.id): return
    data = load_data(); gid = str(m.chat.id)
    uid = str(m.reply_to_message.from_user.id)
    data["admins"].setdefault(gid, [])
    if uid in data["admins"][gid]:
        return bot.reply_to(m, "⚠️ این کاربر از قبل مدیر است.")
    data["admins"][gid].append(uid)
    save_data(data)
    bot.reply_to(m, f"✅ <a href='tg://user?id={uid}'>کاربر</a> به مدیران افزوده شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست مدیران")
def list_admins(m):
    data = load_data(); gid = str(m.chat.id)
    lst = data["admins"].get(gid, [])
    if not lst: return bot.reply_to(m, "📋 هیچ مدیری ثبت نشده.")
    msg = "👑 لیست مدیران:\n" + "\n".join([f"• <a href='tg://user?id={a}'>کاربر {a}</a>" for a in lst])
    bot.reply_to(m, msg)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "افزودن سودو")
def add_sudo(m):
    if m.from_user.id != SUDO_ID: return
    d = load_data(); uid = str(m.reply_to_message.from_user.id)
    if uid in d["sudo_list"]: return bot.reply_to(m, "⚠️ این کاربر از قبل سودو است.")
    d["sudo_list"].append(uid); save_data(d)
    bot.reply_to(m, f"✅ <a href='tg://user?id={uid}'>کاربر</a> به سودوها افزوده شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست سودو")
def list_sudos(m):
    if not is_sudo(m.from_user.id): return
    d = load_data(); s = d.get("sudo_list", [])
    if not s: return bot.reply_to(m, "❗ هیچ سودویی ثبت نشده.")
    txt = "👑 لیست سودوها:\n" + "\n".join([f"• <a href='tg://user?id={x}'>کاربر {x}</a>" for x in s])
    bot.reply_to(m, txt)

# ================= 🚫 بن / سکوت / اخطار =================
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "بن")
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    if is_sudo(uid): return bot.reply_to(m, "⚡ نمی‌توان سودو را بن کرد.")
    try:
        bot.ban_chat_member(m.chat.id, uid)
        bot.reply_to(m, f"🚫 کاربر <a href='tg://user?id={uid}'>بن</a> شد.")
    except Exception as e:
        bot.reply_to(m, f"❗ خطا در بن کاربر: {e}")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف بن")
def unban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.unban_chat_member(m.chat.id, m.reply_to_message.from_user.id, only_if_banned=True)
        bot.reply_to(m, "✅ کاربر از بن خارج شد.")
    except:
        bot.reply_to(m, "❗ خطا در حذف بن.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "سکوت")
def mute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = str(m.reply_to_message.from_user.id)
    d = load_data(); d["muted"][uid] = True; save_data(d)
    bot.reply_to(m, f"🔇 کاربر <a href='tg://user?id={uid}'>ساکت</a> شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف سکوت")
def unmute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = str(m.reply_to_message.from_user.id)
    d = load_data()
    if uid in d["muted"]: d["muted"].pop(uid)
    save_data(d)
    bot.reply_to(m, f"🔊 سکوت کاربر <a href='tg://user?id={uid}'>برداشته</a> شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "اخطار")
def warn_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = str(m.reply_to_message.from_user.id)
    d = load_data(); d["warns"][uid] = d["warns"].get(uid, 0) + 1; save_data(d)
    count = d["warns"][uid]
    msg = f"⚠️ کاربر <a href='tg://user?id={uid}'>اخطار {count}</a> گرفت."
    if count >= 3:
        bot.ban_chat_member(m.chat.id, int(uid))
        msg += "\n🚫 چون ۳ اخطار گرفت، از گروه اخراج شد."
    bot.reply_to(m, msg)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف اخطار")
def del_warn(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = str(m.reply_to_message.from_user.id)
    d = load_data()
    if uid in d["warns"]: d["warns"].pop(uid)
    save_data(d)
    bot.reply_to(m, "✅ تمام اخطارهای کاربر پاک شد.")# ================= 🚪 خروج از گروه =================
@bot.message_handler(func=lambda m: cmd_text(m) in ["لفت بده", "ترک گروه", "خارج شو"])
def leave_group(m):
    # فقط سودو می‌تواند دستور لفت بدهد
    if not is_sudo(m.from_user.id):
        return bot.reply_to(m, "⚠️ فقط سودو می‌تواند من را از گروه خارج کند.")
    try:
        chat_title = m.chat.title or "گروه"
        bot.reply_to(m, f"👋 با اجازه! از {chat_title} خارج می‌شوم...")
        time.sleep(1.5)
        bot.leave_chat(m.chat.id)
    except Exception as e:
        bot.reply_to(m, f"❗ خطا در خروج از گروه:\n<code>{e}</code>")# ================= 🚀 شروع ربات با دکمه‌های شیشه‌ای =================
@bot.message_handler(commands=["start"])
def start_cmd(m):
    d = load_data()
    uid = str(m.from_user.id)
    if uid not in d["users"]:
        d["users"].append(uid)
        save_data(d)

    # متن معرفی ربات ✨
    caption = (
        "👋 سلام دوست عزیز!\n\n"
        "به ربات مدیریتی Persian Lux Panel خوش اومدی 💎\n\n"
        "این ربات برای مدیریت حرفه‌ای گروه‌ها طراحی شده:\n"
        "🔹 قفل لینک، گیف، عکس و ویدیو\n"
        "🔹 خوشامدگویی خودکار با عکس یا متن\n"
        "🔹 اخطار، بن، سکوت و آمار دقیق فعالیت\n"
        "🔹 ثبت جوک و فال روزانه 😂🔮\n\n"
        "برای استفاده، یکی از گزینه‌های زیر رو انتخاب کن 👇"
    )

    # دکمه‌های شیشه‌ای
    keyboard = types.InlineKeyboardMarkup()
    add_btn = types.InlineKeyboardButton("➕ افزودن ربات به گروه", url="https://t.me/Noorir63_Bot?startgroup=true")
    support_btn = types.InlineKeyboardButton("💬 پشتیبانی", url="https://t.me/NOORI_NOOR")
    keyboard.add(add_btn)
    keyboard.add(support_btn)

    bot.send_message(m.chat.id, caption, reply_markup=keyboard)# ================= 😂 جوک‌های جدید و 🔮 فال =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت جوک")
def add_joke(m):
    d = load_data()
    txt = (m.reply_to_message.text or "").strip()
    if not txt:
        return bot.reply_to(m, "⚠️ لطفاً روی پیام متنی ریپلای کن تا ذخیره کنم.")
    if txt in d["jokes"]:
        return bot.reply_to(m, "⚠️ این جوک قبلاً ثبت شده بود.")
    d["jokes"].append(txt)
    save_data(d)
    bot.reply_to(m, f"😂 جوک جدید با موفقیت ذخیره شد!\n\n«{txt[:60]}...»")

@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def random_joke(m):
    d = load_data()
    jokes = d.get("jokes", [])
    if not jokes:
        return bot.reply_to(m, "😅 هنوز هیچ جوکی ثبت نشده!\nبا دستور «ثبت جوک» اضافه کن.")
    joke = random.choice(jokes)
    bot.reply_to(m, f"😂 <b>جوک امروز:</b>\n{joke}")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست جوک")
def list_jokes(m):
    d = load_data()
    jokes = d.get("jokes", [])
    if not jokes:
        return bot.reply_to(m, "❗ هیچ جوکی ثبت نشده.")
    text = "\n".join([f"{i+1}. {j}" for i, j in enumerate(jokes)])
    bot.reply_to(m, f"📜 <b>لیست جوک‌های ذخیره‌شده:</b>\n{text}")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف جوک "))
def del_joke(m):
    d = load_data()
    jokes = d.get("jokes", [])
    try:
        parts = cmd_text(m).split()
        if len(parts) < 3:
            return bot.reply_to(m, "⚠️ فرمت درست دستور: حذف جوک 1")
        idx = int(parts[2]) - 1
        if idx < 0 or idx >= len(jokes):
            raise ValueError
        removed = jokes.pop(idx)
        save_data(d)
        bot.reply_to(m, f"🗑 جوک شماره {idx+1} حذف شد:\n«{removed}»")
    except Exception as e:
        bot.reply_to(m, "❗ شماره‌ی جوک نامعتبر است یا خطایی رخ داده.")

# ==== فال ====
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت فال")
def add_fal(m):
    d = load_data()
    txt = (m.reply_to_message.text or "").strip()
    if not txt:
        return bot.reply_to(m, "⚠️ لطفاً روی پیام متنی ریپلای کن.")
    d["falls"].append(txt)
    save_data(d)
    bot.reply_to(m, "🔮 فال ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def random_fal(m):
    d = load_data()
    f = d.get("falls", [])
    if not f:
        return bot.reply_to(m, "😅 هنوز هیچ فالی ثبت نشده!")
    bot.reply_to(m, f"🔮 <b>فال امروز:</b>\n{random.choice(f)}")

# ================= 🧹 پاکسازی =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف "))
def del_msgs(m):
    try:
        n = int(cmd_text(m).split()[1])
    except:
        return bot.reply_to(m, "❗ فرمت درست: حذف 20")
    for i in range(1, n+1):
        try:
            bot.delete_message(m.chat.id, m.message_id - i)
        except:
            pass
    bot.send_message(m.chat.id, f"🧹 {n} پیام پاک شد.", disable_notification=True)

# ================= 📢 ارسال همگانی =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and m.reply_to_message and cmd_text(m) == "ارسال")
def broadcast(m):
    d = load_data()
    users = list(set(d.get("users", [])))
    groups = [int(g) for g in d["welcome"].keys()]
    msg = m.reply_to_message
    total = 0
    for uid in users + groups:
        try:
            if msg.text:
                bot.send_message(uid, msg.text)
            elif msg.photo:
                bot.send_photo(uid, msg.photo[-1].file_id, caption=msg.caption or "")
            total += 1
        except:
            continue
    bot.reply_to(m, f"📢 پیام برای {total} کاربر ارسال شد.")

# ================= ℹ️ راهنما =================
@bot.message_handler(func=lambda m: cmd_text(m) == "راهنما")
def show_help(m):
    txt = (
        "📘 <b>راهنمای Persian Lux Panel V15 (Updated)</b>\n\n"
        "🆔 آیدی لوکس | ساعت | آمار | لینک ربات/گروه\n"
        "👋 خوشامد | تنظیم | روشن/خاموش\n"
        "🔒 قفل‌ها (لینک | عکس | فیلم | گیف...)\n"
        "🚫 بن | 🔇 سکوت | ⚠️ اخطار (۳=اخراج)\n"
        "😂 جوک‌ها: ثبت جوک | جوک | لیست جوک | حذف جوک N\n"
        "🔮 فال‌ها: ثبت فال | فال\n"
        "🧹 حذف N پیام | 📢 ارسال همگانی (فقط سودو)\n\n"
        "👑 سازنده: محمد | Persian Lux Panel"
    )
    bot.reply_to(m, txt)

# ================= 🤖 پاسخ سودو =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m).lower() in ["سلام","ربات","هی","bot"])
def sudo_reply(m):
    replies = [
        f"👑 جانم {m.from_user.first_name} 💎",
        f"✨ سلام {m.from_user.first_name}! آماده‌ام 💪",
        f"🤖 بله {m.from_user.first_name}، در خدمتتم 🔥"
    ]
    bot.reply_to(m, random.choice(replies))

# ================= 🚀 اجرای نهایی =================
@bot.message_handler(commands=["start"])
def start_cmd(m):
    d = load_data()
    uid = str(m.from_user.id)
    if uid not in d["users"]:
        d["users"].append(uid)
        save_data(d)
    bot.reply_to(m, "👋 سلام! ربات مدیریتی Persian Lux Panel فعال است.\nبرای راهنما بنویس: «راهنما»")

print("🤖 Persian Lux Panel V15 (Joke Updated) در حال اجراست...")
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logging.error(f"polling crash: {e}")
        time.sleep(5)
