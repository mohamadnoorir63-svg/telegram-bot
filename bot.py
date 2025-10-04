# -*- coding: utf-8 -*-
# Persian Group Manager Bot – pyTelegramBotAPI==4.14.0
import os, json, re, time
from datetime import datetime, timedelta, timezone
import telebot
from telebot import types

# ====== CONFIG ======
TOKEN   = "7462131830:AAENzKipQzuxQ4UYkl9vcVgmmfDMKMUvZi8"  # توکن شما
SUDO_ID = 7089376754                                         # آیدی سودو
DATA    = "data.json"
IR_TZ   = timezone(timedelta(hours=3, minutes=30))
bot     = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ====== STORAGE ======
def load():
    if not os.path.exists(DATA):
        save({"groups": {}})
    with open(DATA, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {"groups": {}}

def save(obj): 
    with open(DATA, "w", encoding="utf-8") as f: json.dump(obj, f, ensure_ascii=False, indent=2)

db = load()

def G(cid:int):
    k=str(cid)
    if k not in db["groups"]:
        db["groups"][k] = {
            "locks": {"links": False, "stickers": False, "group": False},
            "welcome": {"enabled": False, "text": "خوش آمدید 🌹", "photo": None}
        }
        save(db)
    return db["groups"][k]

def is_sudo(uid:int)->bool: return uid == SUDO_ID

def is_admin(cid:int, uid:int)->bool:
    if is_sudo(uid): return True
    try:
        st = bot.get_chat_member(cid, uid).status
        return st in ("administrator", "creator")
    except: return False

def bot_has_admin(cid:int)->bool:
    try:
        me = bot.get_me().id
        st = bot.get_chat_member(cid, me).status
        return st in ("administrator","creator")
    except: return False

# ====== HELP TEXTS ======
HELP_GROUP = (
"📌 دستورات گروه:\n"
"• ساعت | تاریخ | آمار | ایدی | لینک | راهنما\n"
"• قفل لینک / باز کردن لینک\n"
"• قفل استیکر / باز کردن استیکر\n"
"• قفل گروه / باز کردن گروه\n"
"• پاکسازی (حذف ۵۰ پیام اخیر)\n"
"• بن / حذف بن (ریپلای) — سکوت / حذف سکوت (ریپلای)\n"
"• مدیر / حذف مدیر (ریپلای)\n"
"• خوشامد روشن / خوشامد خاموش\n"
"• خوشامد متن <متن>\n"
"• ثبت عکس (روی عکس ریپلای کن و بفرست ثبت عکس)\n"
"• لفت بده (فقط سودو)\n"
)

# ====== WELCOME ======
@bot.message_handler(content_types=['new_chat_members'], func=lambda m: m.chat.type in ("group","supergroup"))
def welcome_members(m):
    w = G(m.chat.id)["welcome"]
    if not w["enabled"]: return
    group_name = telebot.util.escape_html(m.chat.title or "")
    for u in m.new_chat_members:
        name = telebot.util.escape_html((u.first_name or "") + ((" "+u.last_name) if u.last_name else ""))
        text = (w["text"] or "خوش آمدید 🌹").replace("{name}", name).replace("{group}", group_name)
        if w["photo"]:
            try: bot.send_photo(m.chat.id, w["photo"], caption=text)
            except: bot.send_message(m.chat.id, text)
        else:
            bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: m.text in ("خوشامد روشن","/welcome_on"))
def welcome_on(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    G(m.chat.id)["welcome"]["enabled"]=True
    save(db)
    bot.reply_to(m, "✅ خوشامد روشن شد.")

@bot.message_handler(func=lambda m: m.text in ("خوشامد خاموش","/welcome_off"))
def welcome_off(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    G(m.chat.id)["welcome"]["enabled"]=False
    save(db)
    bot.reply_to(m, "❌ خوشامد خاموش شد.")

@bot.message_handler(func=lambda m: m.text and m.text.startswith("خوشامد متن"))
def welcome_text(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    txt = m.text.replace("خوشامد متن", "", 1).strip()
    if not txt: return bot.reply_to(m, "نمونه: خوشامد متن خوش آمدی {name} به {group} 🌹")
    G(m.chat.id)["welcome"]["text"] = txt
    save(db)
    bot.reply_to(m, f"✏️ متن خوشامد ذخیره شد:\n{txt}")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="ثبت عکس")
def welcome_photo(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    if not m.reply_to_message.photo: return bot.reply_to(m, "❗ باید روی یک عکس ریپلای کنید.")
    fid = m.reply_to_message.photo[-1].file_id
    G(m.chat.id)["welcome"]["photo"] = fid
    save(db)
    bot.reply_to(m, "📸 عکس خوشامد ذخیره شد.")

# ====== BASIC GROUP COMMANDS ======
def ir_time(): return datetime.now(IR_TZ)

@bot.message_handler(func=lambda m: m.text in ("راهنما","/help","help"))
def help_cmd(m): bot.reply_to(m, HELP_GROUP)

@bot.message_handler(func=lambda m: m.text in ("ساعت","/time","time"))
def time_cmd(m): bot.reply_to(m, f"⏰ ساعت: <b>{ir_time().strftime('%H:%M:%S')}</b>")

@bot.message_handler(func=lambda m: m.text in ("تاریخ","/date","date"))
def date_cmd(m): bot.reply_to(m, f"📅 تاریخ: <b>{ir_time().strftime('%Y-%m-%d')}</b>")

@bot.message_handler(func=lambda m: m.text in ("آمار","/stats","stats"))
def stats_group(m):
    try: cnt = bot.get_chat_member_count(m.chat.id)
    except: cnt = "نامشخص"
    locks = G(m.chat.id)["locks"]
    bot.reply_to(m, f"👥 اعضا: <b>{cnt}</b>\n"
                    f"🔒 لینک: {'✅' if locks['links'] else '❌'} | "
                    f"استیکر: {'✅' if locks['stickers'] else '❌'} | "
                    f"گروه: {'✅' if locks['group'] else '❌'}")

@bot.message_handler(func=lambda m: m.text in ("ایدی","/id","id"))
def id_cmd(m):
    bot.reply_to(m, f"🆔 آیدی شما: <code>{m.from_user.id}</code>\n🆔 آیدی گروه: <code>{m.chat.id}</code>")

@bot.message_handler(func=lambda m: m.text in ("لینک","/link","بهشت"))
def link_cmd(m):
    if not bot_has_admin(m.chat.id):
        return bot.reply_to(m, "⚠️ ربات باید ادمین با اجازه Invite باشد.")
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 {link}")
    except: bot.reply_to(m, "نتوانستم لینک را بگیرم.")

# ====== LEAVE (SUDO ONLY) ======
@bot.message_handler(func=lambda m: m.text in ("لفت بده","/leave"))
def leave_here(m):
    if not is_sudo(m.from_user.id): return
    bot.reply_to(m, "خداحافظ 👋")
    try: bot.leave_chat(m.chat.id)
    except: pass

# ====== RUN ======
print("🤖 Bot is running...")
bot.infinity_polling(timeout=30, long_polling_timeout=30, skip_pending=True)
