# -*- coding: utf-8 -*-
# Simple Persian group manager bot - pyTelegramBotAPI==4.14.0
# Author: you + ChatGPT

import telebot
from telebot import types
import re, json, os, time
from datetime import datetime, timedelta

TOKEN   = "7462131830:AAENzKipQzuxQ4UYkl9vcVgmmfDMKMUvZi8"   # توکن شما
SUDO_ID = 7089376754                                         # آیدی عددی سودو

DATA_FILE = "data.json"

# ---------- helpers: storage ----------
def load_db():
    if not os.path.exists(DATA_FILE):
        save_db({"groups": {}, "await": {}})
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(db):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

db = load_db()

def g(chat_id):
    chat_id = str(chat_id)
    if chat_id not in db["groups"]:
        db["groups"][chat_id] = {
            "expires": 0,
            "locks": {"links": False, "stickers": False, "group": False},
            "welcome": {"enabled": False, "text": "خوش آمدید 🌹", "photo": None}
        }
        save_db(db)
    return db["groups"][chat_id]

def is_charged(chat_id):
    return time.time() < g(chat_id)["expires"]

def iran_now():
    # زمان ایران بدون کتابخانه‌ی اضافی
    return datetime.utcnow() + timedelta(hours=3, minutes=30)

def is_sudo(uid): return int(uid) == int(SUDO_ID)

def is_admin(chat_id, user_id):
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator", "creator")
    except Exception:
        return False

def need_admin_rights(m):
    bot.reply_to(m, "⚠️ ربات باید ادمین با دسترسی حذف/محدودسازی/ارتقا باشد.")
# --------------------------------------

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# =============== SUDO: private panel ===============
@bot.message_handler(commands=["start"])
def start_cmd(m):
    if m.chat.type == "private":
        if is_sudo(m.from_user.id):
            txt = (
                "🔐 <b>پنل سودو</b>\n"
                "• /panel – نمایش پنل\n"
                "• /broadcast – ارسال پیام به همه‌ی گروه‌های شارژ\n"
                "• /stats – آمار گروه‌ها و تاریخ انقضا\n\n"
                "• در گروه: <code>شارژ 30</code> (یا /charge 30) برای شارژ همان گروه\n"
            )
            bot.reply_to(m, txt)
        else:
            bot.reply_to(m, "سلام! من یک ربات مدیریت گروه هستم. مرا به گروه‌تان اضافه و ادمین کنید ✅")
    else:
        pass

@bot.message_handler(commands=["panel"])
def panel_cmd(m):
    if m.chat.type != "private": return
    if not is_sudo(m.from_user.id): return
    total = len(db["groups"])
    active = sum(1 for cid in db["groups"] if is_charged(int(cid)))
    txt = f"🛠 <b>پنل مدیریتی</b>\nگروه‌ها: {total}\nفعّال: {active}\n\n" \
          f"• /stats – لیست گروه‌ها و انقضا\n" \
          f"• /broadcast – ارسال پیام به همه‌ی گروه‌های شارژ"
    bot.reply_to(m, txt)

@bot.message_handler(commands=["stats"])
def stats_cmd(m):
    if m.chat.type != "private": return
    if not is_sudo(m.from_user.id): return
    if not db["groups"]:
        bot.reply_to(m, "هیچ گروهی ثبت نشده.")
        return
    lines = []
    for cid, info in db["groups"].items():
        exp_ts = info.get("expires", 0)
        if exp_ts == 0:
            status = "⛔ شارژ نشده"
        else:
            exp = datetime.utcfromtimestamp(exp_ts) + timedelta(hours=3, minutes=30)
            status = "✅ تا " + exp.strftime("%Y-%m-%d %H:%M")
        lines.append(f"<code>{cid}</code> → {status}")
    bot.reply_to(m, "📊 <b>آمار گروه‌ها</b>\n" + "\n".join(lines))

@bot.message_handler(commands=["broadcast"])
def bc_start(m):
    if m.chat.type != "private": return
    if not is_sudo(m.from_user.id): return
    db["await"][str(m.from_user.id)] = "broadcast"
    save_db(db)
    bot.reply_to(m, "پیام بعدی شما به همه‌ی گروه‌های شارژ ارسال خواهد شد. برای لغو: /cancel")

@bot.message_handler(commands=["cancel"])
def cancel_await(m):
    if m.chat.type != "private": return
    key = str(m.from_user.id)
    if db["await"].get(key):
        db["await"].pop(key, None)
        save_db(db)
        bot.reply_to(m, "لغو شد.")
    else:
        bot.reply_to(m, "در حال انتظار پیام نبودم.")

@bot.message_handler(func=lambda m: m.chat.type=="private")
def private_flow(m):
    key = str(m.from_user.id)
    if db["await"].get(key) == "broadcast" and is_sudo(m.from_user.id):
        sent = 0
        for cid, info in db["groups"].items():
            if is_charged(int(cid)):
                try:
                    bot.copy_message(cid, m.chat.id, m.message_id)
                    sent += 1
                except Exception:
                    pass
        db["await"].pop(key, None)
        save_db(db)
        bot.reply_to(m, f"پیام به {sent} گروهِ شارژ ارسال شد ✅")

# =============== GROUP: charge ===============
# فارسی: "شارژ 30" ، انگلیسی: "/charge 30"
@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"], regexp=r"^/?charge\s+\d+$")
def charge_en(m):
    if not is_sudo(m.from_user.id): return
    days = int(m.text.split()[-1])
    charge_group(m.chat.id, days)

@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text and m.text.strip().startswith("شارژ "))
def charge_fa(m):
    if not is_sudo(m.from_user.id): return
    try:
        days = int(m.text.strip().split()[1])
        charge_group(m.chat.id, days)
    except Exception:
        bot.reply_to(m, "فرمت: <code>شارژ 30</code>")

def charge_group(chat_id, days):
    info = g(chat_id)
    base = max(time.time(), info["expires"])
    info["expires"] = int(base + days*24*3600)
    save_db(db)
    till = datetime.utcfromtimestamp(info["expires"]) + timedelta(hours=3, minutes=30)
    bot.send_message(chat_id, f"✅ گروه برای <b>{days}</b> روز شارژ شد.\nانقضا: <code>{till.strftime('%Y-%m-%d %H:%M')}</code>")

# =============== GROUP: helpers guard ===============
def need_charge(m):
    if not is_charged(m.chat.id):
        if is_sudo(m.from_user.id):
            return False
        bot.reply_to(m, "⛔ این گروه شارژ نیست. فقط سودو قادر به استفاده از فرمان‌هاست.")
        return True
    return False

def need_admin(m):
    if not is_admin(m.chat.id, m.from_user.id) and not is_sudo(m.from_user.id):
        bot.reply_to(m, "این دستور مخصوص مدیران گروه است.")
        return True
    return False

# =============== GROUP: basic info ===============
@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text in ["ساعت","/time"])
def time_cmd(m):
    if need_charge(m): return
    now = iran_now().strftime("%H:%M:%S")
    bot.reply_to(m, f"⏰ ساعت: <code>{now}</code>")

@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text in ["تاریخ","/date"])
def date_cmd(m):
    if need_charge(m): return
    d = iran_now().strftime("%Y-%m-%d")
    bot.reply_to(m, f"📅 تاریخ: <code>{d}</code>")

@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text in ["آمار","/stats"])
def group_stats(m):
    if need_charge(m): return
    try:
        cnt = bot.get_chat_member_count(m.chat.id)
    except Exception:
        cnt = "نامشخص"
    info = g(m.chat.id)
    locks = info["locks"]
    exp = datetime.utcfromtimestamp(info["expires"]) + timedelta(hours=3, minutes=30) if info["expires"] else None
    txt = (
        f"📊 آمار گروه\n"
        f"اعضا: <b>{cnt}</b>\n"
        f"قفل لینک: {'✅' if locks['links'] else '❌'} | "
        f"قفل استیکر: {'✅' if locks['stickers'] else '❌'} | "
        f"قفل گروه: {'✅' if locks['group'] else '❌'}\n"
        f"انقضا: {exp.strftime('%Y-%m-%d %H:%M') if exp else 'نامشخص'}"
    )
    bot.reply_to(m, txt)

@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text in ["ایدی","/id"])
def id_cmd(m):
    if need_charge(m): return
    bot.reply_to(m, f"🆔 آیدی شما: <code>{m.from_user.id}</code>\n🆔 آیدی گروه: <code>{m.chat.id}</code>")

# =============== GROUP: link (invite) ===============
@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text in ["لینک","بهشت","/link"])
def link_cmd(m):
    if need_charge(m): return
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        bot.reply_to(m, f"🔗 لینک گروه:\n{link}")
    except Exception:
        need_admin_rights(m)

# =============== GROUP: locks ===============
@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text in ["قفل لینک","/lock_links"])
def lock_links(m):
    if need_charge(m): return
    if need_admin(m): return
    g(m.chat.id)["locks"]["links"] = True
    save_db(db)
    bot.reply_to(m, "✅ لینک‌ها قفل شدند.")

@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text in ["باز کردن لینک","/unlock_links"])
def unlock_links(m):
    if need_charge(m): return
    if need_admin(m): return
    g(m.chat.id)["locks"]["links"] = False
    save_db(db)
    bot.reply_to(m, "🔓 لینک‌ها آزاد شدند.")

@bot.message_handler(content_types=["text"], func=lambda m: m.chat.type in ["group","supergroup"])
def anti_link(m):
    if not is_charged(m.chat.id): return
    if g(m.chat.id)["locks"]["links"]:
        has_entity_link = any(ent.type in ("url","text_link") for ent in (m.entities or []))
        has_pattern = bool(re.search(r"(https?://|t\.me/|telegram\.me/|telegram\.org/)", m.text or "", flags=re.I))
        if (has_entity_link or has_pattern) and not is_admin(m.chat.id, m.from_user.id) and not is_sudo(m.from_user.id):
            try:
                bot.delete_message(m.chat.id, m.message_id)
            except Exception:
                pass

@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text in ["قفل استیکر","/lock_stickers"])
def lock_stickers(m):
    if need_charge(m): return
    if need_admin(m): return
    g(m.chat.id)["locks"]["stickers"] = True
    save_db(db)
    bot.reply_to(m, "✅ ارسال استیکر ممنوع شد.")

@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text in ["باز کردن استیکر","/unlock_stickers"])
def unlock_stickers(m):
    if need_charge(m): return
    if need_admin(m): return
    g(m.chat.id)["locks"]["stickers"] = False
    save_db(db)
    bot.reply_to(m, "🔓 ارسال استیکر آزاد شد.")

@bot.message_handler(content_types=["sticker"], func=lambda m: m.chat.type in ["group","supergroup"])
def anti_sticker(m):
    if not is_charged(m.chat.id): return
    if g(m.chat.id)["locks"]["stickers"] and not is_admin(m.chat.id, m.from_user.id) and not is_sudo(m.from_user.id):
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass

@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text in ["قفل گروه","/lock_group"])
def lock_group(m):
    if need_charge(m): return
    if need_admin(m): return
    try:
        perms = types.ChatPermissions(can_send_messages=False)
        bot.set_chat_permissions(m.chat.id, perms)
        g(m.chat.id)["locks"]["group"] = True
        save_db(db)
        bot.reply_to(m, "🔒 گروه قفل شد (فقط مدیران مجازند).")
    except Exception:
        need_admin_rights(m)

@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text in ["باز کردن گروه","/unlock_group"])
def unlock_group(m):
    if need_charge(m): return
    if need_admin(m): return
    try:
        perms = types.ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True)
        bot.set_chat_permissions(m.chat.id, perms)
        g(m.chat.id)["locks"]["group"] = False
        save_db(db)
        bot.reply_to(m, "✅ گروه باز شد.")
    except Exception:
        need_admin_rights(m)

# =============== GROUP: moderation (reply) ===============
def target_user_id(m):
    if not m.reply_to_message: return None
    if m.reply_to_message.from_user: return m.reply_to_message.from_user.id
    return None

@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text in ["سکوت","/mute"])
def mute_user(m):
    if need_charge(m): return
    if need_admin(m): return
    uid = target_user_id(m)
    if not uid: return bot.reply_to(m, "روی پیام شخص ریپلای کنید.")
    try:
        bot.restrict_chat_member(m.chat.id, uid, types.ChatPermissions(can_send_messages=False))
        bot.reply_to(m, "🔇 کاربر در سکوت قرار گرفت.")
    except Exception:
        need_admin_rights(m)

@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text in ["حذف سکوت","/unmute"])
def unmute_user(m):
    if need_charge(m): return
    if need_admin(m): return
    uid = target_user_id(m)
    if not uid: return bot.reply_to(m, "روی پیام شخص ریپلای کنید.")
    try:
        bot.restrict_chat_member(m.chat.id, uid, types.ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
        bot.reply_to(m, "🔉 سکوت کاربر برداشته شد.")
    except Exception:
        need_admin_rights(m)

@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text in ["بن","/ban"])
def ban_user(m):
    if need_charge(m): return
    if need_admin(m): return
    uid = target_user_id(m)
    if not uid: return bot.reply_to(m, "روی پیام شخص ریپلای کنید.")
    try:
        bot.ban_chat_member(m.chat.id, uid)
        bot.reply_to(m, "⛔ کاربر بن شد.")
    except Exception:
        need_admin_rights(m)

@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text in ["حذف بن","/unban"])
def unban_user(m):
    if need_charge(m): return
    if need_admin(m): return
    uid = target_user_id(m)
    if not uid: return bot.reply_to(m, "روی پیام شخص ریپلای کنید.")
    try:
        bot.unban_chat_member(m.chat.id, uid, only_if_banned=True)
        bot.reply_to(m, "✅ بن کاربر برداشته شد.")
    except Exception:
        need_admin_rights(m)

@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text in ["مدیر","/promote"])
def promote_user(m):
    if need_charge(m): return
    if not is_admin(m.chat.id, m.from_user.id) and not is_sudo(m.from_user.id):
        return bot.reply_to(m, "فقط مدیران می‌توانند ارتقا دهند.")
    uid = target_user_id(m)
    if not uid: return bot.reply_to(m, "روی پیام شخص ریپلای کنید.")
    try:
        bot.promote_chat_member(
            m.chat.id, uid,
            can_manage_chat=True, can_delete_messages=True, can_invite_users=True,
            can_restrict_members=True, can_pin_messages=True, can_promote_members=False,
            can_manage_video_chats=True
        )
        bot.reply_to(m, "🛡 کاربر مدیر شد.")
    except Exception:
        need_admin_rights(m)

@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text in ["حذف مدیر","/demote"])
def demote_user(m):
    if need_charge(m): return
    if not is_admin(m.chat.id, m.from_user.id) and not is_sudo(m.from_user.id):
        return bot.reply_to(m, "فقط مدیران می‌توانند عزل کنند.")
    uid = target_user_id(m)
    if not uid: return bot.reply_to(m, "روی پیام شخص ریپلای کنید.")
    try:
        bot.promote_chat_member(
            m.chat.id, uid,
            can_manage_chat=False, can_delete_messages=False, can_invite_users=False,
            can_restrict_members=False, can_pin_messages=False, can_promote_members=False,
            can_manage_video_chats=False
        )
        bot.reply_to(m, "⬇️ کاربر از مدیریت حذف شد.")
    except Exception:
        need_admin_rights(m)

# =============== GROUP: clean last 50 ===============
@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text in ["پاکسازی","/clear"])
def clear_msgs(m):
    if need_charge(m): return
    if not is_admin(m.chat.id, m.from_user.id) and not is_sudo(m.from_user.id):
        return bot.reply_to(m, "این دستور مخصوص مدیران است.")
    ok = 0
    for mid in range(m.message_id-1, max(m.message_id-200, 1), -1):
        try:
            bot.delete_message(m.chat.id, mid)
            ok += 1
            if ok >= 50: break
        except Exception:
            pass
    bot.reply_to(m, f"🧹 {ok} پیام حذف شد.")

# =============== GROUP: welcome ===============
@bot.message_handler(content_types=["new_chat_members"], func=lambda m: m.chat.type in ["group","supergroup"])
def welcome(m):
    if not is_charged(m.chat.id): return
    w = g(m.chat.id)["welcome"]
    if not w["enabled"]: return
    for u in m.new_chat_members:
        name = (u.first_name or "") + (" " + u.last_name if u.last_name else "")
        text = w["text"].replace("{name}", name).replace("{id}", str(u.id))
        if w["photo"]:
            try:
                bot.send_photo(m.chat.id, w["photo"], caption=text)
            except Exception:
                bot.send_message(m.chat.id, text)
        else:
            bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text in ["خوشامد روشن","/welcome_on"])
def welcome_on(m):
    if need_charge(m): return
    if need_admin(m): return
    g(m.chat.id)["welcome"]["enabled"] = True
    save_db(db)
    bot.reply_to(m, "✅ خوشامدگویی روشن شد.")

@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text in ["خوشامد خاموش","/welcome_off"])
def welcome_off(m):
    if need_charge(m): return
    if need_admin(m): return
    g(m.chat.id)["welcome"]["enabled"] = False
    save_db(db)
    bot.reply_to(m, "🔕 خوشامدگویی خاموش شد.")

@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text and m.text.startswith("خوشامد متن"))
def welcome_text(m):
    if need_charge(m): return
    if need_admin(m): return
    txt = m.text.replace("خوشامد متن", "", 1).strip()
    if not txt:
        return bot.reply_to(m, "نمونه: <code>خوشامد متن خوش آمدی {name}</code>\nمتغیرها: {name} {id}")
    g(m.chat.id)["welcome"]["text"] = txt
    save_db(db)
    bot.reply_to(m, "✍️ متن خوشامد ذخیره شد.")

@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text in ["خوشامد عکس","/welcome_photo"])
def welcome_photo_set(m):
    if need_charge(m): return
    if need_admin(m): return
    bot.reply_to(m, "روی عکس مورد نظر ریپلای کنید و بفرستید: «ثبت عکس»")

@bot.message_handler(content_types=["photo"], func=lambda m: m.chat.type in ["group","supergroup"] and m.reply_to_message and (m.reply_to_message.text or "") == "ثبت عکس")
def save_welcome_photo(m):
    if need_charge(m): return
    if need_admin(m): return
    fid = m.photo[-1].file_id
    g(m.chat.id)["welcome"]["photo"] = fid
    save_db(db)
    bot.reply_to(m, "🖼 عکس خوشامد ذخیره شد.")

# =============== GROUP: leave by sudo ===============
@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and m.text in ["لفت بده","/leave"])
def leave_group(m):
    if not is_sudo(m.from_user.id): return
    bot.reply_to(m, "خداحافظ 👋")
    try:
        bot.leave_chat(m.chat.id)
    except Exception:
        pass

# =============== guard: auto leave when expired ===============
@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"])
def quit_if_expired(m):
    info = g(m.chat.id)
    if info["expires"] and time.time() > info["expires"]:
        try:
            bot.send_message(m.chat.id, "⛔ شارژ این گروه تمام شد. ربات خارج می‌شود.")
            bot.leave_chat(m.chat.id)
        except Exception:
            pass

# =============== run ===============
print("Bot is up.")
bot.infinity_polling(skip_pending=True, timeout=20)
