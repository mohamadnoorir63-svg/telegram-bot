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
    except: bot.reply_to(m,"❗ فرمت درست: حذف 10")# ================== 🎉 خوشامدگویی پیشرفته (با منوی اینلاین) ==================
from telebot import types
import jdatetime, json, os

DATA_FILE = "data.json"
if not os.path.exists(DATA_FILE):
    data = {"groups": {}, "welcome": {}}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def now_time():
    return jdatetime.datetime.now().strftime("%H:%M  ( %A %d %B %Y )")

# 📥 ثبت گروه هنگام هر پیام
def register_group(chat_id):
    data = load_data()
    if str(chat_id) not in data["groups"]:
        data["groups"][str(chat_id)] = True
        save_data(data)

# 🎊 رویداد ورود کاربر جدید
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new_member(m):
    try:
        register_group(m.chat.id)
        data = load_data()
        group = str(m.chat.id)
        settings = data["welcome"].get(group, {"enabled": True, "type": "text", "content": None, "file_id": None})
        if not settings.get("enabled", True):
            return

        name = m.new_chat_members[0].first_name
        time_str = now_time()

        default_text = (
            f"سلام 𓄂ꪴꪰ🅜‌‌‌‌‌🅞‌‌‌‌‌‌🅗‌‌‌‌‌🅐‌‌‌‌‌‌🅜‌‌‌‌‌🅜‌‌‌‌‌‌🅐‌‌‌‌‌🅓‌‌‌‌‌‌❳𓆃 عزیز\n"
            f"به گروه 𝙎𝙩𝙖𝙧𝙧𝙮𝙉𝙞𝙜𝙝𝙩 ☾꙳⋆ خوش آمدید 😎\n\n"
            f"ساعت ›› {time_str}"
        )

        text = (settings.get("content") or default_text).replace("{name}", name).replace("{time}", time_str)

        if settings.get("type") == "photo" and settings.get("file_id"):
            bot.send_photo(m.chat.id, settings["file_id"], caption=text)
        else:
            bot.send_message(m.chat.id, text)
    except Exception as e:
        print("welcome error:", e)

# 🧭 منوی خوشامد (با دستور “خوشامد”)
@bot.message_handler(func=lambda m: cmd_text(m) == "خوشامد")
def show_welcome_menu(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)):
        return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🟢 روشن / خاموش", callback_data=f"wl_toggle:{m.chat.id}"))
    kb.add(types.InlineKeyboardButton("📝 تنظیم متن", callback_data=f"wl_text:{m.chat.id}"),
           types.InlineKeyboardButton("🖼 تنظیم عکس", callback_data=f"wl_photo:{m.chat.id}"))
    kb.add(types.InlineKeyboardButton("👁 پیش‌نمایش", callback_data=f"wl_preview:{m.chat.id}"))
    bot.send_message(m.chat.id, "⚙️ منوی تنظیمات خوشامد:", reply_markup=kb)

# 🎛 کنترل دکمه‌های منوی خوشامد
@bot.callback_query_handler(func=lambda c: c.data.startswith("wl_"))
def welcome_menu_handler(c):
    try:
        data = load_data()
        group = str(c.message.chat.id)
        settings = data["welcome"].get(group, {"enabled": True, "type": "text", "content": None, "file_id": None})

        if c.data.startswith("wl_toggle"):
            settings["enabled"] = not settings.get("enabled", True)
            data["welcome"][group] = settings
            save_data(data)
            state = "✅ فعال شد" if settings["enabled"] else "🚫 غیرفعال شد"
            bot.answer_callback_query(c.id, f"خوشامد {state}", show_alert=True)

        elif c.data.startswith("wl_text"):
            bot.answer_callback_query(c.id, "برای تنظیم، روی پیامت ریپلای بزن و بنویس: تنظیم خوشامد متن", show_alert=True)

        elif c.data.startswith("wl_photo"):
            bot.answer_callback_query(c.id, "برای تنظیم عکس، روی عکس ریپلای کن و بنویس: تنظیم خوشامد عکس", show_alert=True)

        elif c.data.startswith("wl_preview"):
            if settings["type"] == "photo" and settings.get("file_id"):
                bot.send_photo(c.message.chat.id, settings["file_id"],
                               caption=settings.get("content", "بدون متن"))
            else:
                txt = settings.get("content") or "بدون متن سفارشی (از متن پیش‌فرض استفاده می‌شود)"
                bot.send_message(c.message.chat.id, f"👁 پیش‌نمایش خوشامد:\n\n{txt}")

    except Exception as e:
        print("wl menu error:", e)

# 📝 تنظیم خوشامد متنی
@bot.message_handler(func=lambda m: cmd_text(m) == "تنظیم خوشامد متن" and m.reply_to_message)
def set_welcome_text(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)):
        return
    data = load_data()
    group = str(m.chat.id)
    txt = m.reply_to_message.text or ""
    data["welcome"][group] = {"enabled": True, "type": "text", "content": txt, "file_id": None}
    save_data(data)
    bot.reply_to(m, "📝 متن خوشامد تنظیم شد. از {name} و {time} می‌تونی استفاده کنی.")

# 🖼 تنظیم خوشامد تصویری
@bot.message_handler(func=lambda m: cmd_text(m) == "تنظیم خوشامد عکس" and m.reply_to_message and m.reply_to_message.photo)
def set_welcome_photo(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)):
        return
    data = load_data()
    group = str(m.chat.id)
    fid = m.reply_to_message.photo[-1].file_id
    caption = m.reply_to_message.caption or "خوش آمدی {name}"
    data["welcome"][group] = {"enabled": True, "type": "photo", "file_id": fid, "content": caption}
    save_data(data)
    bot.reply_to(m, "🖼 عکس خوشامد تنظیم شد.")

# 🔘 دستورهای متنی سنتی (برای سازگاری با نسخه قبلی)
@bot.message_handler(func=lambda m: cmd_text(m).lower() in ["خوشامد روشن", "خوشامد on"])
def welcome_on(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)):
        return
    data = load_data()
    group = str(m.chat.id)
    data["welcome"].setdefault(group, {"enabled": True})
    data["welcome"][group]["enabled"] = True
    save_data(data)
    bot.reply_to(m, "✅ خوشامد فعال شد")

@bot.message_handler(func=lambda m: cmd_text(m).lower() in ["خوشامد خاموش", "خوشامد off"])
def welcome_off(m):
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)):
        return
    data = load_data()
    group = str(m.chat.id)
    data["welcome"].setdefault(group, {"enabled": False})
    data["welcome"][group]["enabled"] = False
    save_data(data)
    bot.reply_to(m, "🚫 خوشامد غیرفعال شد")# ================== 🔐 ماژول قفل‌ها و خوشامد ==================
import jdatetime

# ========== تنظیمات اولیه فایل داده‌ها ==========
DATA_FILE = "data.json"

if not os.path.exists(DATA_FILE):
    data = {"groups": {}, "welcome": {}, "autolock": {}}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ========== توابع کمکی ==========
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

# ================== 🎉 خوشامد ==================
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new_member(m):
    try:
        register_group(m.chat.id)
        data = load_data()
        group = str(m.chat.id)
        settings = data["welcome"].get(group, {"enabled": True, "type": "text", "content": None})
        if not settings.get("enabled", True):
            return

        name = m.new_chat_members[0].first_name
        time_str = now_time()

        # پیام پیش‌فرض خوشامد
        default_text = (
            f"سلام 𓄂ꪴꪰ🅜‌‌‌‌‌🅞‌‌‌‌‌‌🅗‌‌‌‌‌🅐‌‌‌‌‌‌🅜‌‌‌‌‌🅜‌‌‌‌‌‌🅐‌‌‌‌‌🅓‌‌‌‌‌‌❳𓆃 عزیز\n"
            f"به گروه 𝙎𝙩𝙖𝙧𝙧𝙮𝙉𝙞𝙜𝙝𝙩 ☾꙳⋆ خوش آمدید 😎\n\n"
            f"ساعت ›› {time_str}"
        )

        text = settings.get("content") or default_text
        text = text.replace("{name}", name).replace("{time}", time_str)

        if settings.get("type") == "photo" and settings.get("file_id"):
            msg = bot.send_photo(m.chat.id, settings["file_id"], caption=text)
        else:
            msg = bot.send_message(m.chat.id, text)

        # اگر خواستی پین خودکار هم بشه این خط رو فعال کن:
        # bot.pin_chat_message(m.chat.id, msg.message_id)

    except Exception as e:
        print("welcome error:", e)

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
    if not (is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id)): return
    data = load_data()
    group = str(m.chat.id)
    txt = m.reply_to_message.text or ""
    data["welcome"][group] = {"enabled": True, "type": "text", "content": txt}
    save_data(data)
    bot.reply_to(m, "📝 متن خوشامد تنظیم شد. از {name} و {time} می‌تونی استفاده کنی.")

# ================== 🔒 قفل‌ها ==================
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

# کنترل پیام‌ها برای قفل‌ها
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
    try:
        bot.infinity_polling(skip_pending=True, timeout=30)
    except Exception as e:
        print("Bot stopped with error:", e)
