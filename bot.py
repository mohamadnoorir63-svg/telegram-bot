# -*- coding: utf-8 -*-
import telebot
import re
import json
import os
from datetime import datetime, timedelta, timezone

# ========= تنظیمات =========
TOKEN    = "PUT_YOUR_TELEGRAM_BOT_TOKEN_HERE"   # ← 7462131830:AAENzKipQzuxQ4UYkl9vcVgmmfDMKMUvZi8"   توکن ربات
SUDO_ID  = 7089376754                           # ← 7089376754آیدی عددی سودو (صاحب ربات)
DATA_FILE = "groups.json"                       # ذخیرهٔ لوکال (برای پایداری بهتر بعداً Redis بگذار)

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
IR_TZ = timezone(timedelta(hours=3, minutes=30))  # Asia/Tehran بدون نیاز به pytz

# ========= ذخیره/لود =========
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

db = load_data()  # ساختار: { chat_id(str): {expires_at:int, locks:{...}, welcome:{...}} }

def ensure_chat(chat_id: int):
    key = str(chat_id)
    if key not in db:
        db[key] = {
            "expires_at": 0,
            "locks": {
                "links": False,
                "stickers": False,
                "group_locked": False
            },
            "welcome": {
                "enabled": False,
                "text": "خوش آمدید 🌹",
                "photo_id": None
            }
        }
        save_data()
    return db[key]

def is_charged(chat_id: int) -> bool:
    data = ensure_chat(chat_id)
    return int(data.get("expires_at", 0)) > int(datetime.now(timezone.utc).timestamp())

def require_bot_admin(message) -> bool:
    try:
        me = bot.get_chat_member(message.chat.id, bot.get_me().id)
        status = me.status
        # باید بتونه Delete/Restrict/Invite داشته باشه برای برخی قابلیت‌ها
        return status in ("administrator", "creator")
    except:
        return False

def is_admin(chat_id: int, user_id: int) -> bool:
    if user_id == SUDO_ID:
        return True
    try:
        m = bot.get_chat_member(chat_id, user_id)
        return m.status in ("administrator", "creator")
    except:
        return False

def sudo_only(user_id: int) -> bool:
    return user_id == SUDO_ID

def persian_or_english(text: str, patterns):
    """بررسی چند عبارت (فارسی/انگلیسی)"""
    t = (text or "").strip()
    return any(t.lower().startswith(p.lower()) for p in patterns)

# ========= پیام‌های کمکی =========
HELP_GROUP = (
    "📌 دستورات گروه (اگر گروه شارژ باشد):\n"
    "• ساعت\n• تاریخ\n• آمار (members)\n• ایدی\n"
    "• لینک (دریافت لینک دعوت)\n"
    "• قفل لینک / باز کردن لینک\n"
    "• قفل استیکر / باز کردن استیکر\n"
    "• قفل گروه / باز کردن گروه\n"
    "• پاکسازی (حذف ۵۰ پیام اخیر)\n"
    "• بن (با ریپلای) / سکوت (با ریپلای) / حذف سکوت (با ریپلای)\n"
    "• لفت بده (فقط سودو)\n"
    "• خوشامد روشن/خاموش — ویرایش خوشامد (متن/عکس)\n"
    "—\n"
    "برای مدیران: پاسخ بده به پیام کاربر و بگو «بن» یا «سکوت» یا «حذف سکوت»."
)

HELP_PM_SUDO = (
    "🔐 پنل مدیریتی (فقط سودو) — در پیوی ربات:\n"
    "/panel – آمار و فهرست گروه‌های شارژ شده\n"
    "/broadcast متن – ارسال پیام به همه گروه‌های شارژ\n"
    "⚡ شارژ از داخل خود گروه: «شارژ 30» (عدد = روز)\n"
    "⚡ یا در پیوی: /charge <group_id> <days>\n"
    "/welcome <group_id> <text> – تنظیم متن خوشامد (یا با عکس: /welcomepic در ریپلای)\n"
)

START_TEXT_USER = "سلام! من یک ربات مدیریت گروه هستم. من را به گروه‌تان اضافه و ادمین کنید تا فعال شوم."

# ========= /start (PM) =========
@bot.message_handler(commands=['start'])
def cmd_start(m):
    if m.chat.type != "private":
        return
    if sudo_only(m.from_user.id):
        bot.reply_to(m, "سلام سودو 👑\n" + HELP_PM_SUDO)
    else:
        bot.reply_to(m, START_TEXT_USER)

# ========= پنل سودو در پیوی =========
@bot.message_handler(commands=['panel'])
def cmd_panel(m):
    if m.chat.type != "private": return
    if not sudo_only(m.from_user.id): return
    now = int(datetime.now(timezone.utc).timestamp())
    total = 0
    charged = 0
    lines = []
    for k, v in db.items():
        if not str(k).startswith('-100') and not str(k).startswith('-'):  # فقط سوپرگروه‌ها غالباً -100...
            pass
        total += 1
        exp = int(v.get("expires_at", 0))
        ok = exp > now
        if ok: charged += 1
        exp_str = datetime.fromtimestamp(exp, IR_TZ).strftime("%Y-%m-%d %H:%M") if exp else "—"
        lines.append(f"گروه <code>{k}</code> | شارژ: {'✅' if ok else '❌'} | انقضا: {exp_str}")
    text = f"📊 آمار گروه‌ها:\nمجموع: <b>{total}</b> | شارژ: <b>{charged}</b>\n\n" + ("\n".join(lines[:50]) or "هیچ گروهی ثبت نیست.")
    bot.reply_to(m, text)

@bot.message_handler(commands=['broadcast'])
def cmd_broadcast(m):
    if m.chat.type != "private": return
    if not sudo_only(m.from_user.id): return
    parts = m.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(m, "فرمت: /broadcast متن")
        return
    msg = parts[1]
    sent = 0
    for k, v in db.items():
        try:
            if is_charged(int(k)):
                bot.send_message(int(k), msg)
                sent += 1
        except: pass
    bot.reply_to(m, f"پیام به {sent} گروه ارسال شد.")

@bot.message_handler(commands=['charge'])
def cmd_charge(m):
    # /charge group_id days  (در پیوی)  یا «شارژ 30» (در خود گروه)
    if m.chat.type == "private":
        if not sudo_only(m.from_user.id): return
        parts = m.text.split()
        if len(parts) != 3:
            bot.reply_to(m, "فرمت درست: /charge group_id روز\nمثال: /charge -1001234567890 30")
            return
        try:
            gid = int(parts[1])
            days = int(parts[2])
        except:
            bot.reply_to(m, "مقادیر نادرست‌اند.")
            return
        data = ensure_chat(gid)
        exp = datetime.now(timezone.utc) + timedelta(days=days)
        data["expires_at"] = int(exp.timestamp())
        save_data()
        bot.reply_to(m, f"گروه <code>{gid}</code> برای {days} روز شارژ شد. ✅")
    else:
        # داخل گروه: «شارژ 30» فقط توسط سودو
        if not sudo_only(m.from_user.id): return
        txt = (m.text or "").strip()
        # اجازه بده /charge 30 یا «شارژ 30»
        mo = re.match(r"^/?charge\s+(\d+)$", txt, re.IGNORECASE) or re.match(r"^شارژ\s+(\d+)$", txt)
        if not mo:
            return
        days = int(mo.group(1))
        data = ensure_chat(m.chat.id)
        exp = datetime.now(timezone.utc) + timedelta(days=days)
        data["expires_at"] = int(exp.timestamp())
        save_data()
        bot.reply_to(m, f"گروه برای <b>{days}</b> روز شارژ شد. ✅")

# ========= خوشامدگویی =========
@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup"), content_types=['new_chat_members'])
def on_new_member(m):
    if not is_charged(m.chat.id):
        try:
            bot.leave_chat(m.chat.id)
        except: pass
        return
    data = ensure_chat(m.chat.id)
    w = data["welcome"]
    if not w.get("enabled"): return
    text = w.get("text") or "خوش آمدید 🌹"
    names = "، ".join([f"<a href='tg://user?id={u.id}'>{telebot.util.escape_html(u.first_name or '')}</a>" for u in m.new_chat_members])
    msg = text.replace("{name}", names).replace("{group}", telebot.util.escape_html(m.chat.title or ""))
    if w.get("photo_id"):
        bot.send_photo(m.chat.id, w["photo_id"], caption=msg)
    else:
        bot.send_message(m.chat.id, msg)

# مدیر گروه می‌تواند خوشامد را روشن/خاموش/ویرایش کند
@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup"))
def group_text_commands(m):
    txt = (m.text or "").strip()

    # شارژ تمام شده؟ هر پیام تریگر چک
    if not is_charged(m.chat.id):
        if sudo_only(m.from_user.id):
            pass
        else:
            try: bot.leave_chat(m.chat.id)
            except: pass
            return

    # فقط سودو: لفت بده
    if txt in ("لفت بده", "leave") and sudo_only(m.from_user.id):
        try:
            bot.send_message(m.chat.id, "خدانگهدار 👋")
            bot.leave_chat(m.chat.id)
        except: pass
        return

    # راهنما
    if txt in ("راهنما", "help", "/help"):
        bot.reply_to(m, HELP_GROUP)
        return

    # ساعت/تاریخ
    if txt in ("ساعت", "time"):
        now = datetime.now(IR_TZ).strftime("%H:%M:%S")
        bot.reply_to(m, f"⏰ ساعت: <b>{now}</b>")
        return
    if txt in ("تاریخ", "date"):
        d = datetime.now(IR_TZ).strftime("%Y-%m-%d")
        bot.reply_to(m, f"📅 تاریخ: <b>{d}</b>")
        return

    # آمار اعضا
    if txt in ("آمار", "stats", "/stats"):
        try:
            cnt = bot.get_chat_members_count(m.chat.id)
            bot.reply_to(m, f"👥 اعضا: <b>{cnt}</b>")
        except:
            bot.reply_to(m, "نتوانستم آمار را بگیرم.")
        return

    # ایدی
    if txt in ("ایدی", "id", "/id"):
        bot.reply_to(m, f"🆔 آیدی شما: <code>{m.from_user.id}</code>\n🆔 آیدی گروه: <code>{m.chat.id}</code>")
        return

    # لینک گروه
    if txt in ("لینک", "link", "/link"):
        if not require_bot_admin(m):
            bot.reply_to(m, "⚠️ ربات باید ادمین باشد (اجازهٔ invite).")
            return
        try:
            link = bot.export_chat_invite_link(m.chat.id)
            bot.reply_to(m, f"🔗 لینک گروه:\n{link}")
        except:
            bot.reply_to(m, "نتوانستم لینک را بگیرم. مطمئن شو ربات اجازهٔ Invite دارد.")
        return

    # قفل/باز کردن لینک
    if txt in ("قفل لینک", "lock links"):
        if not is_admin(m.chat.id, m.from_user.id): return
        data = ensure_chat(m.chat.id)
        data["locks"]["links"] = True
        save_data()
        bot.reply_to(m, "🔒 لینک‌ها قفل شدند. ✅")
        return
    if txt in ("باز کردن لینک", "unlock links"):
        if not is_admin(m.chat.id, m.from_user.id): return
        data = ensure_chat(m.chat.id)
        data["locks"]["links"] = False
        save_data()
        bot.reply_to(m, "🔓 لینک‌ها آزاد شدند. ✅")
        return

    # قفل/باز کردن استیکر
    if txt in ("قفل استیکر", "lock stickers"):
        if not is_admin(m.chat.id, m.from_user.id): return
        data = ensure_chat(m.chat.id)
        data["locks"]["stickers"] = True
        save_data()
        bot.reply_to(m, "🧷 ارسال استیکر ممنوع شد. ✅")
        return
    if txt in ("باز کردن استیکر", "unlock stickers"):
        if not is_admin(m.chat.id, m.from_user.id): return
        data = ensure_chat(m.chat.id)
        data["locks"]["stickers"] = False
        save_data()
        bot.reply_to(m, "🧷 ارسال استیکر آزاد شد. ✅")
        return

    # قفل/باز کردن گروه (فقط مدیر – نیاز به Restrict Members برای ربات)
    if txt in ("قفل گروه", "lock group"):
        if not is_admin(m.chat.id, m.from_user.id): return
        if not require_bot_admin(m):
            bot.reply_to(m, "⚠️ ربات باید ادمین با دسترسی محدودکردن باشد.")
            return
        try:
            bot.set_chat_permissions(m.chat.id, telebot.types.ChatPermissions(can_send_messages=False))
            data = ensure_chat(m.chat.id)
            data["locks"]["group_locked"] = True
            save_data()
            bot.reply_to(m, "گروه قفل شد. 🔒")
        except:
            bot.reply_to(m, "نتوانستم گروه را قفل کنم.")
        return

    if txt in ("باز کردن گروه", "unlock group"):
        if not is_admin(m.chat.id, m.from_user.id): return
        if not require_bot_admin(m):
            bot.reply_to(m, "⚠️ ربات باید ادمین باشد.")
            return
        try:
            bot.set_chat_permissions(m.chat.id, telebot.types.ChatPermissions(can_send_messages=True))
            data = ensure_chat(m.chat.id)
            data["locks"]["group_locked"] = False
            save_data()
            bot.reply_to(m, "گروه باز شد. 🔓")
        except:
            bot.reply_to(m, "نتوانستم گروه را باز کنم.")
        return

    # پاکسازی ۵۰ پیام
    if txt in ("پاکسازی", "clear", "/clear"):
        if not is_admin(m.chat.id, m.from_user.id): return
        if not require_bot_admin(m):
            bot.reply_to(m, "⚠️ ربات باید دسترسی حذف پیام داشته باشد.")
            return
        deleted = 0
        base = m.message_id
        for mid in range(base-1, base-1-50, -1):
            if mid <= 0: break
            try:
                bot.delete_message(m.chat.id, mid); deleted += 1
            except: pass
        bot.reply_to(m, f"🧹 {deleted} پیام اخیر حذف شد.")
        return

    # خوشامد روشن/خاموش/ویرایش
    if txt in ("خوشامد روشن", "welcome on"):
        if not is_admin(m.chat.id, m.from_user.id): return
        data = ensure_chat(m.chat.id)
        data["welcome"]["enabled"] = True
        save_data()
        bot.reply_to(m, "✨ خوشامدگویی روشن شد.")
        return
    if txt in ("خوشامد خاموش", "welcome off"):
        if not is_admin(m.chat.id, m.from_user.id): return
        data = ensure_chat(m.chat.id)
        data["welcome"]["enabled"] = False
        save_data()
        bot.reply_to(m, "✨ خوشامدگویی خاموش شد.")
        return
    if txt.startswith("ویرایش خوشامد ") or txt.lower().startswith("setwelcome "):
        if not is_admin(m.chat.id, m.from_user.id): return
        new_text = txt.replace("ویرایش خوشامد", "", 1).strip() if txt.startswith("ویرایش خوشامد ") else txt.split(" ",1)[1]
        data = ensure_chat(m.chat.id)
        data["welcome"]["text"] = new_text or "خوش آمدید 🌹"
        save_data()
        bot.reply_to(m, "متن خوشامد ویرایش شد. می‌تونی از {name} و {group} هم استفاده کنی.")
        return
    if txt in ("خوشامد عکس", "welcomepic"):
        # باید روی یک عکس ریپلای شود
        if not is_admin(m.chat.id, m.from_user.id): return
        if not m.reply_to_message or not (m.reply_to_message.photo):
            bot.reply_to(m, "روی یک عکس ریپلای کن و بگو «خوشامد عکس».")
            return
        file_id = m.reply_to_message.photo[-1].file_id
        data = ensure_chat(m.chat.id)
        data["welcome"]["photo_id"] = file_id
        save_data()
        bot.reply_to(m, "عکس خوشامد ذخیره شد.")
        return
    if txt in ("حذف عکس خوشامد", "rmwelcomepic"):
        if not is_admin(m.chat.id, m.from_user.id): return
        data = ensure_chat(m.chat.id)
        data["welcome"]["photo_id"] = None
        save_data()
        bot.reply_to(m, "عکس خوشامد حذف شد.")
        return

    # بن/سکوت/حذف سکوت (با ریپلای)
    if txt in ("بن", "ban"):
        if not is_admin(m.chat.id, m.from_user.id): return
        if not require_bot_admin(m): return
        if not m.reply_to_message: return
        try:
            bot.ban_chat_member(m.chat.id, m.reply_to_message.from_user.id)
            bot.reply_to(m, "کاربر بن شد. 🚫")
        except:
            pass
        return
    if txt in ("سکوت", "mute"):
        if not is_admin(m.chat.id, m.from_user.id): return
        if not require_bot_admin(m): return
        if not m.reply_to_message: return
        try:
            perms = telebot.types.ChatPermissions(can_send_messages=False)
            bot.restrict_chat_member(m.chat.id, m.reply_to_message.from_user.id, permissions=perms)
            bot.reply_to(m, "کاربر در سکوت قرار گرفت. 🔇")
        except:
            pass
        return
    if txt in ("حذف سکوت", "unmute"):
        if not is_admin(m.chat.id, m.from_user.id): return
        if not require_bot_admin(m): return
        if not m.reply_to_message: return
        try:
            perms = telebot.types.ChatPermissions(can_send_messages=True)
            bot.restrict_chat_member(m.chat.id, m.reply_to_message.from_user.id, permissions=perms)
            bot.reply_to(m, "سکوت کاربر برداشته شد. 🔊")
        except:
            pass
        return

# ========= حذف لینک‌ها / استیکرها وقتی قفل است =========
URL_RE = re.compile(r"(https?://|t\.me/)", re.IGNORECASE)

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup"), content_types=['text','sticker','photo','document','animation'])
def filters_guard(m):
    if not is_charged(m.chat.id):
        return
    data = ensure_chat(m.chat.id)
    # لینک
    if data["locks"].get("links") and m.content_type == 'text':
        if URL_RE.search(m.text or "") and not is_admin(m.chat.id, m.from_user.id):
            if require_bot_admin(m):
                try: bot.delete_message(m.chat.id, m.message_id)
                except: pass
            return
    # استیکر
    if data["locks"].get("stickers") and m.content_type == 'sticker':
        if not is_admin(m.chat.id, m.from_user.id) and require_bot_admin(m):
            try: bot.delete_message(m.chat.id, m.message_id)
            except: pass
            return

# ========= اجرای ربات =========
print("Bot is running...")
bot.infinity_polling(timeout=30, long_polling_timeout=30, skip_pending=True)
