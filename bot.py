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

db = load()  # { chat_id(str): {expires:int, locks:{links,stickers,group}, welcome:{enabled,text,photo}} }

def G(cid:int):
    k=str(cid)
    if k not in db["groups"]:
        db["groups"][k] = {
            "expires": 0,
            "locks": {"links": False, "stickers": False, "group": False},
            "welcome": {"enabled": False, "text": "خوش آمدید 🌹", "photo": None}
        }
        save(db)
    return db["groups"][k]

def is_charged(cid:int)->bool:
    return int(G(cid)["expires"]) > int(time.time())

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
"• خوشامد متن <متن>  (از {name} و {group} می‌تونی استفاده کنی)\n"
"• خوشامد عکس (ریپلای روی عکس و بفرست «ثبت عکس»)\n"
"• لفت بده (فقط سودو)\n"
"—\n"
"شارژ گروه فقط با سودو: «شارژ 30» یا /charge 30\n"
)

# ====== NOTIFY SUDO WHEN ADDED ======
@bot.my_chat_member_handler()
def on_bot_status_changed(upd):
    try:
        chat = upd.chat
        new = upd.new_chat_member
        if chat and chat.type in ("group","supergroup"):
            if new.status in ("administrator","member"):
                # تازه اضافه/ادمین شد
                bot.send_message(SUDO_ID, f"➕ ربات به گروه جدید اضافه شد:\n"
                                          f"📛 نام: <b>{telebot.util.escape_html(chat.title or '')}</b>\n"
                                          f"🆔 آیدی: <code>{chat.id}</code>\n"
                                          f"وضعیت: {'ادمین' if new.status=='administrator' else 'عضو'}")
                G(chat.id); save(db)
    except: pass

# ====== SUDO PANEL (Inline) ======
def panel_markup():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📊 آمار گروه‌ها", callback_data="panel_stats"),
        types.InlineKeyboardButton("📩 ارسال پیام", callback_data="panel_broadcast"),
    )
    kb.add(
        types.InlineKeyboardButton("⏳ شارژ گروه", callback_data="panel_charge"),
        types.InlineKeyboardButton("🚪 خروج از گروه", callback_data="panel_leave"),
    )
    return kb

@bot.message_handler(commands=['start','panel'])
def start_or_panel(m):
    if m.chat.type!="private":
        return
    if is_sudo(m.from_user.id):
        bot.send_message(m.chat.id, "🔧 <b>پنل مدیریت ربات</b>", reply_markup=panel_markup())
    else:
        bot.send_message(m.chat.id, "سلام! من ربات مدیریت گروه هستم.\n✅ من را به گروه اضافه و ادمین کنید.")

@bot.callback_query_handler(func=lambda c: c.message.chat.type=="private" and is_sudo(c.from_user.id))
def panel_actions(c):
    if c.data=="panel_stats":
        if not db["groups"]:
            bot.answer_callback_query(c.id, "هیچ گروهی ثبت نیست.")
            bot.edit_message_text("هیچ گروهی ثبت نشده.", c.message.chat.id, c.message.message_id, reply_markup=panel_markup())
            return
        now = int(time.time())
        lines=[]
        active=0
        for k,v in db["groups"].items():
            exp=v.get("expires",0)
            ok=exp>now
            if ok: active+=1
            expstr = datetime.fromtimestamp(exp, IR_TZ).strftime("%Y-%m-%d %H:%M") if exp else "—"
            lines.append(f"<code>{k}</code> | {'✅' if ok else '❌'} | {expstr}")
        txt = f"📊 آمار گروه‌ها\nفعّال: {active}/{len(db['groups'])}\n\n" + "\n".join(lines[:60])
        bot.edit_message_text(txt, c.message.chat.id, c.message.message_id, reply_markup=panel_markup())
        bot.answer_callback_query(c.id)

    elif c.data=="panel_broadcast":
        bot.answer_callback_query(c.id, "پیام متنی بعدی‌ات را بفرست تا برای همهٔ گروه‌های شارژ ارسال شود.")
        bot.edit_message_text("✏️ پیام بعدی‌ات را بفرست.\n/cancel برای لغو.", c.message.chat.id, c.message.message_id)
        bot.register_next_step_handler(c.message, do_broadcast)

    elif c.data=="panel_charge":
        bot.answer_callback_query(c.id, "فرمت: /charge <group_id> <days>")
        bot.edit_message_text("⏳ نمونه:\n<code>/charge -100123456789 30</code>", c.message.chat.id, c.message.message_id, reply_markup=panel_markup())

    elif c.data=="panel_leave":
        bot.answer_callback_query(c.id, "آیدی گروهی که باید لفت بدم رو بفرست.", cache_time=2)
        bot.edit_message_text("🚪 آیدی گروه را بفرست (مثال: <code>-100123456789</code>)\n/cancel برای لغو.", c.message.chat.id, c.message.message_id)
        bot.register_next_step_handler(c.message, do_leave_by_id)

@bot.message_handler(commands=['cancel'])
def cancel_pm(m):
    if m.chat.type=="private" and is_sudo(m.from_user.id):
        bot.send_message(m.chat.id, "لغو شد ✅", reply_markup=panel_markup())

def do_broadcast(m):
    if m.chat.type!="private" or not is_sudo(m.from_user.id): return
    sent=0
    for k in list(db["groups"].keys()):
        try:
            if is_charged(int(k)):
                bot.copy_message(int(k), m.chat.id, m.message_id)
                sent+=1
        except: pass
    bot.send_message(m.chat.id, f"📩 پیام به {sent} گروه ارسال شد.", reply_markup=panel_markup())

def do_leave_by_id(m):
    if m.chat.type!="private" or not is_sudo(m.from_user.id): return
    try:
        gid=int(m.text.strip())
        bot.send_message(gid, "به دستور سودو خارج می‌شوم. 👋")
        bot.leave_chat(gid)
        bot.send_message(m.chat.id, "خارج شدم ✅", reply_markup=panel_markup())
    except:
        bot.send_message(m.chat.id, "آیدی نامعتبر یا دسترسی ندارم.", reply_markup=panel_markup())

# ====== CHARGE (group & PM) ======
@bot.message_handler(commands=['charge'])
def charge_cmd(m):
    if m.chat.type=="private":
        if not is_sudo(m.from_user.id): return
        try:
            _, gid, days = m.text.split()
            gid, days = int(gid), int(days)
            info = G(gid)
            base = max(time.time(), info["expires"])
            info["expires"] = int(base + days*24*3600)
            save(db)
            t = datetime.fromtimestamp(info["expires"], IR_TZ).strftime("%Y-%m-%d %H:%M")
            bot.reply_to(m, f"گروه <code>{gid}</code> تا <b>{t}</b> شارژ شد ✅")
        except:
            bot.reply_to(m, "فرمت: <code>/charge -100123456789 30</code>")
    else:
        # در گروه: /charge 30 یا «شارژ 30» — فقط سودو
        if not is_sudo(m.from_user.id): return
        try:
            days = int(m.text.split()[1])
        except:
            return
        info = G(m.chat.id)
        base = max(time.time(), info["expires"])
        info["expires"] = int(base + days*24*3600)
        save(db)
        t = datetime.fromtimestamp(info["expires"], IR_TZ).strftime("%Y-%m-%d %H:%M")
        bot.reply_to(m, f"✅ این گروه تا <b>{t}</b> شارژ شد.")

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and m.text and m.text.startswith("شارژ "))
def charge_fa(m):
    if not is_sudo(m.from_user.id): return
    try:
        days = int(m.text.split()[1])
        info = G(m.chat.id)
        base = max(time.time(), info["expires"])
        info["expires"] = int(base + days*24*3600)
        save(db)
        t = datetime.fromtimestamp(info["expires"], IR_TZ).strftime("%Y-%m-%d %H:%M")
        bot.reply_to(m, f"✅ این گروه تا <b>{t}</b> شارژ شد.")
    except:
        bot.reply_to(m, "نمونه: «شارژ 30»")

# ====== AUTO LEAVE WHEN EXPIRED ======
@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup"))
def guard_expired(m):
    info = G(m.chat.id)
    if info["expires"] and time.time() > info["expires"]:
        try:
            bot.send_message(m.chat.id, "⛔ شارژ گروه تمام شده. ربات خارج می‌شود.")
            bot.leave_chat(m.chat.id)
        except: pass

# ====== BASIC GROUP COMMANDS ======
def ir_time(): return datetime.now(IR_TZ)

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and m.text in ("راهنما","/help","help"))
def help_cmd(m):
    if not is_charged(m.chat.id) and not is_sudo(m.from_user.id): return
    bot.reply_to(m, HELP_GROUP)

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and m.text in ("ساعت","/time","time"))
def time_cmd(m):
    if not is_charged(m.chat.id) and not is_sudo(m.from_user.id): return
    bot.reply_to(m, f"⏰ ساعت: <b>{ir_time().strftime('%H:%M:%S')}</b>")

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and m.text in ("تاریخ","/date","date"))
def date_cmd(m):
    if not is_charged(m.chat.id) and not is_sudo(m.from_user.id): return
    bot.reply_to(m, f"📅 تاریخ: <b>{ir_time().strftime('%Y-%m-%d')}</b>")

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and m.text in ("آمار","/stats","stats"))
def stats_group(m):
    if not is_charged(m.chat.id) and not is_sudo(m.from_user.id): return
    try: cnt = bot.get_chat_member_count(m.chat.id)
    except: cnt = "نامشخص"
    locks = G(m.chat.id)["locks"]
    exp   = G(m.chat.id)["expires"]
    exp_s = datetime.fromtimestamp(exp, IR_TZ).strftime("%Y-%m-%d %H:%M") if exp else "—"
    bot.reply_to(m, f"👥 اعضا: <b>{cnt}</b>\n"
                    f"🔒 لینک: {'✅' if locks['links'] else '❌'} | استیکر: {'✅' if locks['stickers'] else '❌'} | گروه: {'✅' if locks['group'] else '❌'}\n"
                    f"⏳ انقضا: {exp_s}")

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and m.text in ("ایدی","/id","id"))
def id_cmd(m):
    if not is_charged(m.chat.id) and not is_sudo(m.from_user.id): return
    bot.reply_to(m, f"🆔 آیدی شما: <code>{m.from_user.id}</code>\n🆔 آیدی گروه: <code>{m.chat.id}</code>")

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and m.text in ("لینک","/link","link","بهشت"))
def link_cmd(m):
    if not is_charged(m.chat.id) and not is_sudo(m.from_user.id): return
    if not bot_has_admin(m.chat.id):
        return bot.reply_to(m, "⚠️ ربات باید ادمین با اجازه Invite باشد.")
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 {link}")
    except: bot.reply_to(m, "نتوانستم لینک را بگیرم.")

# ====== LOCKS ======
URL_RE = re.compile(r"(https?://|t\.me/|telegram\.me/|telegram\.org/)", re.I)

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and m.text in ("قفل لینک","/lock_links"))
def lock_links(m):
    if not is_charged(m.chat.id) and not is_sudo(m.from_user.id): return
    if not is_admin(m.chat.id, m.from_user.id): return
    G(m.chat.id)["locks"]["links"]=True; save(db)
    bot.reply_to(m, "🔒 لینک‌ها قفل شدند.")

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and m.text in ("باز کردن لینک","/unlock_links"))
def unlock_links(m):
    if not is_charged(m.chat.id) and not is_sudo(m.from_user.id): return
    if not is_admin(m.chat.id, m.from_user.id): return
    G(m.chat.id)["locks"]["links"]=False; save(db)
    bot.reply_to(m, "🔓 لینک‌ها آزاد شدند.")

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup"), content_types=['text'])
def anti_link(m):
    if not is_charged(m.chat.id): return
    if not G(m.chat.id)["locks"]["links"]: return
    if is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id): return
    if URL_RE.search(m.text or ""):
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and m.text in ("قفل استیکر","/lock_stickers"))
def lock_stickers(m):
    if not is_charged(m.chat.id) and not is_sudo(m.from_user.id): return
    if not is_admin(m.chat.id, m.from_user.id): return
    G(m.chat.id)["locks"]["stickers"]=True; save(db)
    bot.reply_to(m, "🧷 استیکرها قفل شدند.")

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and m.text in ("باز کردن استیکر","/unlock_stickers"))
def unlock_stickers(m):
    if not is_charged(m.chat.id) and not is_sudo(m.from_user.id): return
    if not is_admin(m.chat.id, m.from_user.id): return
    G(m.chat.id)["locks"]["stickers"]=False; save(db)
    bot.reply_to(m, "🧷 استیکرها آزاد شدند.")

@bot.message_handler(content_types=['sticker'], func=lambda m: m.chat.type in ("group","supergroup"))
def anti_sticker(m):
    if not is_charged(m.chat.id): return
    if not G(m.chat.id)["locks"]["stickers"]: return
    if is_admin(m.chat.id, m.from_user.id) or is_sudo(m.from_user.id): return
    try: bot.delete_message(m.chat.id, m.message_id)
    except: pass

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and m.text in ("قفل گروه","/lock_group"))
def lock_group(m):
    if not is_charged(m.chat.id) and not is_sudo(m.from_user.id): return
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.set_chat_permissions(m.chat.id, types.ChatPermissions(can_send_messages=False))
        G(m.chat.id)["locks"]["group"]=True; save(db)
        bot.reply_to(m, "🔒 گروه قفل شد (فقط مدیران).")
    except: bot.reply_to(m, "نیاز به دسترسی محدودسازی توسط ربات است.")

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and m.text in ("باز کردن گروه","/unlock_group"))
def unlock_group(m):
    if not is_charged(m.chat.id) and not is_sudo(m.from_user.id): return
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.set_chat_permissions(m.chat.id, types.ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
        G(m.chat.id)["locks"]["group"]=False; save(db)
        bot.reply_to(m, "✅ گروه باز شد.")
    except: bot.reply_to(m, "نیاز به دسترسی محدودسازی توسط ربات است.")

# ====== MODERATION (reply) ======
def target_id(m):
    return m.reply_to_message.from_user.id if m.reply_to_message and m.reply_to_message.from_user else None

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and m.text in ("بن","/ban"))
def ban_user(m):
    if not is_charged(m.chat.id) and not is_sudo(m.from_user.id): return
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = target_id(m)
    if not uid: return bot.reply_to(m, "روی پیام شخص ریپلای کن.")
    try: bot.ban_chat_member(m.chat.id, uid); bot.reply_to(m, "⛔ کاربر بن شد.")
    except: bot.reply_to(m, "نشد! ربات باید اجازه بن داشته باشد.")

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and m.text in ("حذف بن","/unban"))
def unban_user(m):
    if not is_charged(m.chat.id) and not is_sudo(m.from_user.id): return
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = target_id(m)
    if not uid: return bot.reply_to(m, "روی پیام شخص ریپلای کن.")
    try: bot.unban_chat_member(m.chat.id, uid, only_if_banned=True); bot.reply_to(m, "✅ بن برداشته شد.")
    except: bot.reply_to(m, "نشد! دسترسی کافی نیست.")

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and m.text in ("سکوت","/mute"))
def mute_user(m):
    if not is_charged(m.chat.id) and not is_sudo(m.from_user.id): return
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = target_id(m)
    if not uid: return bot.reply_to(m, "روی پیام شخص ریپلای کن.")
    try:
        bot.restrict_chat_member(m.chat.id, uid, types.ChatPermissions(can_send_messages=False))
        bot.reply_to(m, "🔇 کاربر سکوت شد.")
    except: bot.reply_to(m, "دسترسی محدودسازی لازم است.")

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and m.text in ("حذف سکوت","/unmute"))
def unmute_user(m):
    if not is_charged(m.chat.id) and not is_sudo(m.from_user.id): return
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = target_id(m)
    if not uid: return bot.reply_to(m, "روی پیام شخص ریپلای کن.")
    try:
        bot.restrict_chat_member(m.chat.id, uid, types.ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
        bot.reply_to(m, "🔊 سکوت برداشته شد.")
    except: bot.reply_to(m, "دسترسی محدودسازی لازم است.")

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and m.text in ("مدیر","/promote"))
def promote_user(m):
    if not is_charged(m.chat.id) and not is_sudo(m.from_user.id): return
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = target_id(m)
    if not uid: return bot.reply_to(m, "روی پیام شخص ریپلای کن.")
    try:
        bot.promote_chat_member(m.chat.id, uid,
            can_manage_chat=True, can_delete_messages=True, can_invite_users=True,
            can_restrict_members=True, can_pin_messages=True, can_manage_video_chats=True
        )
        bot.reply_to(m, "🛡 کاربر مدیر شد.")
    except: bot.reply_to(m, "نیاز به دسترسی Promote توسط ربات است.")

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and m.text in ("حذف مدیر","/demote"))
def demote_user(m):
    if not is_charged(m.chat.id) and not is_sudo(m.from_user.id): return
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = target_id(m)
    if not uid: return bot.reply_to(m, "روی پیام شخص ریپلای کن.")
    try:
        bot.promote_chat_member(m.chat.id, uid,
            can_manage_chat=False, can_delete_messages=False, can_invite_users=False,
            can_restrict_members=False, can_pin_messages=False, can_manage_video_chats=False
        )
        bot.reply_to(m, "⬇️ کاربر از مدیریت حذف شد.")
    except: bot.reply_to(m, "نیاز به دسترسی Promote توسط ربات است.")

# ====== WELCOME (IN GROUP) ======
@bot.message_handler(content_types=['new_chat_members'], func=lambda m: m.chat.type in ("group","supergroup"))
def welcome_members(m):
    if not is_charged(m.chat.id): return
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

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and m.text in ("خوشامد روشن","/welcome_on"))
def welcome_on(m):
    if not is_charged(m.chat.id): return
    if not is_admin(m.chat.id, m.from_user.id): return
    G(m.chat.id)["welcome"]["enabled"]=True; save(db)
    bot.reply_to(m, "✅ خوشامد روشن شد.")

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and m.text in ("خوشامد خاموش","/welcome_off"))
def welcome_off(m):
    if not is_charged(m.chat.id): return
    if not is_admin(m.chat.id, m.from_user.id): return
    G(m.chat.id)["wel
