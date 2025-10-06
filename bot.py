# -*- coding: utf-8 -*-
import os, re, time, threading, random
from datetime import datetime
import pytz
import telebot
from telebot import types

# ================== تنظیمات ==================
TOKEN     = os.environ.get("BOT_TOKEN")            # توکن بات
SUDO_ID   = int(os.environ.get("SUDO_ID", "0"))    # سودوی اصلی
SUPPORT_ID = "NOORI_NOOR"                          # پشتیبانی

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ===== نقش‌ها =====
sudo_ids   = {SUDO_ID}   # سودوها
bot_admins = set()       # مدیران ربات (اختیاری، جدا از ادمین‌های گروه)

# ================== کمکی‌ها ==================
def is_sudo(uid): 
    return uid in sudo_ids

def is_bot_admin(uid):
    return uid in bot_admins or is_sudo(uid)

def is_admin(chat_id, user_id):
    if is_bot_admin(user_id):
        return True
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator", "creator")
    except:
        return False

def cmd_text(m):
    return (getattr(m, "text", None) or getattr(m, "caption", None) or "").strip()

# حذف خودکار
DELETE_DELAY = 7
def auto_del(chat_id, msg_id, delay=None):
    d = DELETE_DELAY if delay is None else delay
    if d <= 0: 
        return
    def _worker():
        time.sleep(d)
        try: bot.delete_message(chat_id, msg_id)
        except: pass
    threading.Thread(target=_worker, daemon=True).start()

# ================== دستورات عمومی ==================
@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def cmd_time(m):
    now_utc = datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
    now_teh = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    msg = bot.reply_to(m, f"⏰ ساعت UTC: {now_utc}\n⏰ ساعت تهران: {now_teh}")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m) == "ایدی")
def cmd_id(m):
    msg = bot.reply_to(m, f"🆔 شما: <code>{m.from_user.id}</code>\n🆔 گروه: <code>{m.chat.id}</code>")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def cmd_stats(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try: count = bot.get_chat_member_count(m.chat.id)
    except: count = "نامشخص"
    msg = bot.reply_to(m, f"📊 اعضای گروه: {count}")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m) == "لینک")
def cmd_link(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        link = bot.export_chat_invite_link(m.chat.id)
        msg = bot.reply_to(m, f"📎 لینک گروه:\n{link}")
    except:
        msg = bot.reply_to(m, "❗ نتوانستم لینک بگیرم (بات باید ادمین با مجوز دعوت باشد).")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m) == "وضعیت ربات")
def cmd_bot_status(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    now = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
    msg = bot.reply_to(m, f"🤖 ربات فعال است.\n🕒 {now}")
    auto_del(m.chat.id, msg.message_id)

# جواب مخصوص سودو: «ربات»
SUDO_RESPONSES = [
    "جونم قربان 😎", "در خدمتم ✌️", "ربات آماده‌ست قربان 🚀", "چه خبر رئیس؟ 🤖"
]
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "ربات")
def cmd_sudo_hi(m):
    msg = bot.reply_to(m, random.choice(SUDO_RESPONSES))
    auto_del(m.chat.id, msg.message_id)

# ================== خوشامد ==================
welcome_enabled, welcome_texts, welcome_photos = {}, {}, {}
DEFAULT_WELCOME = "• سلام {name} به گروه {title} خوش آمدید 🌻\n📆 {date}\n⏰ {time}"

@bot.message_handler(content_types=['new_chat_members'])
def on_new_members(m):
    for u in m.new_chat_members:
        if not welcome_enabled.get(m.chat.id): 
            continue
        name = u.first_name or ""
        date = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y/%m/%d")
        time_ = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%H:%M:%S")
        tpl = welcome_texts.get(m.chat.id, DEFAULT_WELCOME)
        txt = tpl.format(name=name, title=m.chat.title, date=date, time=time_)
        if m.chat.id in welcome_photos:
            bot.send_photo(m.chat.id, welcome_photos[m.chat.id], caption=txt)
        else:
            bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda m: cmd_text(m) == "خوشامد روشن")
def w_on(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    welcome_enabled[m.chat.id] = True
    msg = bot.reply_to(m, "✅ خوشامد روشن شد.")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m) == "خوشامد خاموش")
def w_off(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    welcome_enabled[m.chat.id] = False
    msg = bot.reply_to(m, "❌ خوشامد خاموش شد.")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m).startswith("خوشامد متن "))
def w_text(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    welcome_texts[m.chat.id] = cmd_text(m).replace("خوشامد متن ", "", 1).strip()
    msg = bot.reply_to(m, "✍️ متن خوشامد ذخیره شد.")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "ثبت عکس")
def w_photo(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    if m.reply_to_message.photo:
        welcome_photos[m.chat.id] = m.reply_to_message.photo[-1].file_id
        msg = bot.reply_to(m, "🖼 عکس خوشامد ذخیره شد.")
    else:
        msg = bot.reply_to(m, "❗ روی یک «عکس» ریپلای کن.")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست خوشامد")
def w_list(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    t = welcome_texts.get(m.chat.id, "پیش‌فرض")
    p = "ذخیره شده" if welcome_photos.get(m.chat.id) else "ندارد"
    st = "✅ روشن" if welcome_enabled.get(m.chat.id) else "❌ خاموش"
    msg = bot.reply_to(m, f"🎉 تنظیمات خوشامد:\n\n✍️ متن: {t[:50]}\n🖼 عکس: {p}\n🔘 وضعیت: {st}")
    auto_del(m.chat.id, msg.message_id, delay=20)

# ================== فونت‌ساز (10 استایل) ==================
FONTS = [
    # 1) انگلیسی Bold
    lambda txt: "".join({"a":"𝗮","b":"𝗯","c":"𝗰","d":"𝗱","e":"𝗲","f":"𝗳","g":"𝗴","h":"𝗵","i":"𝗶","j":"𝗷","k":"𝗸","l":"𝗹","m":"𝗺","n":"𝗻","o":"𝗼","p":"𝗽","q":"𝗾","r":"𝗿","s":"𝘀","t":"𝘁","u":"𝘂","v":"𝘃","w":"𝘄","x":"𝘅","y":"𝘆","z":"𝘇"}.get(ch.lower(),ch) for ch in txt),
    # 2) انگلیسی Italic
    lambda txt: "".join({"a":"𝑎","b":"𝑏","c":"𝑐","d":"𝑑","e":"𝑒","f":"𝑓","g":"𝑔","h":"ℎ","i":"𝑖","j":"𝑗","k":"𝑘","l":"𝑙","m":"𝑚","n":"𝑛","o":"𝑜","p":"𝑝","q":"𝑞","r":"𝑟","s":"𝑠","t":"𝑡","u":"𝑢","v":"𝑣","w":"𝑤","x":"𝑥","y":"𝑦","z":"𝑧"}.get(ch.lower(),ch) for ch in txt),
    # 3) Bubble
    lambda txt: "".join({"a":"ⓐ","b":"ⓑ","c":"ⓒ","d":"ⓓ","e":"ⓔ","f":"ⓕ","g":"ⓖ","h":"ⓗ","i":"ⓘ","j":"ⓙ","k":"ⓚ","l":"ⓛ","m":"ⓜ","n":"ⓝ","o":"ⓞ","p":"ⓟ","q":"ⓠ","r":"ⓡ","s":"ⓢ","t":"ⓣ","u":"ⓤ","v":"ⓥ","w":"ⓦ","x":"ⓧ","y":"ⓨ","z":"ⓩ"}.get(ch.lower(),ch) for ch in txt),
    # 4) SmallCaps
    lambda txt: "".join({"a":"ᴀ","b":"ʙ","c":"ᴄ","d":"ᴅ","e":"ᴇ","f":"ғ","g":"ɢ","h":"ʜ","i":"ɪ","j":"ᴊ","k":"ᴋ","l":"ʟ","m":"ᴍ","n":"ɴ","o":"ᴏ","p":"ᴘ","q":"ǫ","r":"ʀ","s":"s","t":"ᴛ","u":"ᴜ","v":"ᴠ","w":"ᴡ","x":"x","y":"ʏ","z":"ᴢ"}.get(ch.lower(),ch) for ch in txt),
    # 5) Gothic
    lambda txt: "".join({"a":"𝔞","b":"𝔟","c":"𝔠","d":"𝔡","e":"𝔢","f":"𝔣","g":"𝔤","h":"𝔥","i":"𝔦","j":"𝔧","k":"𝔨","l":"𝔩","m":"𝔪","n":"𝔫","o":"𝔬","p":"𝔭","q":"𝔮","r":"𝔯","s":"𝔰","t":"𝔱","u":"𝔲","v":"𝔳","w":"𝔴","x":"𝔵","y":"𝔶","z":"𝔷"}.get(ch.lower(),ch) for ch in txt),
    # 6) فارسی فانتزی
    lambda txt: "".join({"ا":"ٱ","ب":"بٰ","ت":"تہ","ث":"ثٰ","ج":"جـ","ح":"حہ","خ":"خہ","د":"دٰ","ذ":"ذٰ","ر":"رٰ","ز":"زٰ","س":"سٰ","ش":"شٰ","ص":"صٰ","ض":"ضٰ","ط":"طٰ","ظ":"ظٰ","ع":"عہ","غ":"غہ","ف":"فہ","ق":"قٰ","ک":"ڪ","گ":"گٰ","ل":"لہ","م":"مہ","ن":"نٰ","ه":"ﮬ","و":"ۆ","ی":"ۍ"}.get(ch, ch) for ch in txt),
    # 7) فارسی عربی‌وار
    lambda txt: "".join({"ا":"آ","ب":"ب̍","ت":"تۛ","ث":"ثہ","ج":"ج͠","ح":"حٰٰ","خ":"خ̐","د":"دُ","ذ":"ذٰ","ر":"ر͜","ز":"زٰ","س":"سہ","ش":"شہ","ص":"صہ","ض":"ضہ","ط":"طہ","ظ":"ظہ","ع":"عہ","غ":"غہ","ف":"فہ","ق":"ق͠","ک":"ڪہ","گ":"گہ","ل":"لہ","م":"مہ","ن":"نہ","ه":"ﮬ","و":"و͠","ی":"يہ"}.get(ch, ch) for ch in txt),
    # 8) فارسی کلاسیک
    lambda txt: "".join({"ا":"اٰ","ب":"بـ","ت":"تـ","ث":"ثـ","ج":"ﮔ","ح":"حـ","خ":"خـ","د":"دٰ","ذ":"ذٰ","ر":"رٰ","ز":"زٰ","س":"سـ","ش":"شـ","ص":"صـ","ض":"ضـ","ط":"طـ","ظ":"ظـ","ع":"عـ","غ":"غـ","ف":"فـ","ق":"قـ","ک":"ڪ","گ":"گـ","ل":"لـ","م":"مـ","ن":"نـ","ه":"هـ","و":"ۅ","ی":"ۍ"}.get(ch, ch) for ch in txt),
    # 9) فارسی مدرن
    lambda txt: "".join({"ا":"ﺂ","ب":"ﺑ","ت":"ﺗ","ث":"ﺛ","ج":"ﺟ","ح":"ﺣ","خ":"ﺧ","د":"ﮄ","ذ":"ﮆ","ر":"ﺭ","ز":"ﺯ","س":"ﺳ","ش":"ﺷ","ص":"ﺻ","ض":"ﺿ","ط":"ﻁ","ظ":"ﻅ","ع":"ﻋ","غ":"ﻏ","ف":"ﻓ","ق":"ﻗ","ک":"ﮎ","گ":"ﮒ","ل":"ﻟ","م":"ﻣ","ن":"ﻧ","ه":"ﮬ","و":"ۆ","ی":"ﯼ"}.get(ch, ch) for ch in txt),
    # 10) فارسی ترکیبی
    lambda txt: "".join({"ا":"آ","ب":"بہ","ت":"تـ","ث":"ثہ","ج":"جہ","ح":"حہ","خ":"خہ","د":"دٰ","ذ":"ذہ","ر":"رٰ","ز":"زہ","س":"سہ","ش":"شہ","ص":"صہ","ض":"ضہ","ط":"طہ","ظ":"ظہ","ع":"عہ","غ":"غہ","ف":"فہ","ق":"قہ","ک":"کہ","گ":"گہ","ل":"لہ","م":"مہ","ن":"نہ","ه":"ﮬ","و":"ۅ","ی":"یے"}.get(ch, ch) for ch in txt),
]

@bot.message_handler(func=lambda m: cmd_text(m).startswith("فونت "))
def cmd_fonts(m):
    name = cmd_text(m).replace("فونت ", "", 1).strip()
    if not name:
        msg = bot.reply_to(m, "❗ اسم رو هم بنویس")
        return auto_del(m.chat.id, msg.message_id)
    res = f"🎨 فونت‌های خوشگل برای {name}:\n\n"
    for sty in FONTS:
        try: res += sty(name) + "\n"
        except: pass
    msg = bot.reply_to(m, res)
    auto_del(m.chat.id, msg.message_id, delay=20)

# ================== سیستم «اصل» ==================
origins = {}  # chat_id -> { uid: origin_text }

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m).startswith("ثبت اصل "))
def origin_set(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    val = cmd_text(m).replace("ثبت اصل ", "", 1).strip()
    if not val:
        msg = bot.reply_to(m, "❗ متنی وارد کن.")
    else:
        origins.setdefault(m.chat.id, {})[uid] = val
        msg = bot.reply_to(m, f"✅ اصل برای {m.reply_to_message.from_user.first_name} ثبت شد: {val}")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "اصل")
def origin_get(m):
    uid = m.reply_to_message.from_user.id
    val = origins.get(m.chat.id, {}).get(uid)
    msg = bot.reply_to(m, f"🧾 اصل: {val}" if val else "ℹ️ اصل ثبت نشده.")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: cmd_text(m) == "اصل من")
def origin_me(m):
    val = origins.get(m.chat.id, {}).get(m.from_user.id)
    msg = bot.reply_to(m, f"🧾 اصل شما: {val}" if val else "ℹ️ اصل شما ثبت نشده.")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف اصل")
def origin_del(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    ok = origins.get(m.chat.id, {}).pop(uid, None)
    msg = bot.reply_to(m, "🗑 اصل حذف شد." if ok is not None else "ℹ️ اصلی ثبت نشده بود.")
    auto_del(m.chat.id, msg.message_id)

# ================== جوک و فال ==================
jokes = []     # [{"type":"text","content":...} or {"type":"photo","file":file_id,"caption":...}]
fortunes = []  # ساختار مشابه

# ثبت جوک/فال با ریپلای
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "ثبت جوک")
def joke_add(m):
    if not m.reply_to_message:
        msg = bot.reply_to(m, "❗ روی پیام جوک ریپلای کن.")
        return auto_del(m.chat.id, msg.message_id)
    if m.reply_to_message.text:
        jokes.append({"type":"text", "content": m.reply_to_message.text})
    elif m.reply_to_message.photo:
        jokes.append({"type":"photo","file": m.reply_to_message.photo[-1].file_id, "caption": m.reply_to_message.caption or ""})
    msg = bot.reply_to(m, "😂 جوک ذخیره شد.")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "ثبت فال")
def fal_add(m):
    if not m.reply_to_message:
        msg = bot.reply_to(m, "❗ روی پیام فال ریپلای کن.")
        return auto_del(m.chat.id, msg.message_id)
    if m.reply_to_message.text:
        fortunes.append({"type":"text", "content": m.reply_to_message.text})
    elif m.reply_to_message.photo:
        fortunes.append({"type":"photo","file": m.reply_to_message.photo[-1].file_id, "caption": m.reply_to_message.caption or ""})
    msg = bot.reply_to(m, "🔮 فال ذخیره شد.")
    auto_del(m.chat.id, msg.message_id)

# ارسال تصادفی
@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def joke_send(m):
    if not jokes:
        return bot.reply_to(m, "❗ هیچ جوکی ذخیره نشده.")
    j = random.choice(jokes)
    if j["type"] == "text":
        bot.send_message(m.chat.id, j["content"])
    else:
        bot.send_photo(m.chat.id, j["file"], caption=j.get("caption") or "")

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def fal_send(m):
    if not fortunes:
        return bot.reply_to(m, "❗ هیچ فالی ذخیره نشده.")
    f = random.choice(fortunes)
    if f["type"] == "text":
        bot.send_message(m.chat.id, f["content"])
    else:
        bot.send_photo(m.chat.id, f["file"], caption=f.get("caption") or "")

# لیست‌ها (نمایش تا 20 مورد اخیر + اندیس)
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "لیست جوک‌ها")
def jokes_list(m):
    if not jokes:
        return bot.reply_to(m, "ℹ️ هیچ جوکی ثبت نشده.")
    start = max(0, len(jokes) - 20)
    lines = []
    for i, j in enumerate(jokes[start:], start=1):
        if j["type"] == "text":
            prev = (j["content"][:40] + "…") if len(j["content"]) > 40 else j["content"]
        else:
            prev = "[📸 عکس]" + (f" — {j.get('caption')[:30]}…" if j.get('caption') else "")
        lines.append(f"{i}. {prev}")
    msg = bot.reply_to(m, "😂 لیست جوک‌ها (۲۰ تای آخر):\n\n" + "\n".join(lines))
    auto_del(m.chat.id, msg.message_id, delay=30)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "لیست فال‌ها")
def fal_list(m):
    if not fortunes:
        return bot.reply_to(m, "ℹ️ هیچ فالی ثبت نشده.")
    start = max(0, len(fortunes) - 20)
    lines = []
    for i, f in enumerate(fortunes[start:], start=1):
        if f["type"] == "text":
            prev = (f["content"][:40] + "…") if len(f["content"]) > 40 else f["content"]
        else:
            prev = "[📸 عکس]" + (f" — {f.get('caption')[:30]}…" if f.get('caption') else "")
        lines.append(f"{i}. {prev}")
    msg = bot.reply_to(m, "🔮 لیست فال‌ها (۲۰ تای آخر):\n\n" + "\n".join(lines))
    auto_del(m.chat.id, msg.message_id, delay=30)

# حذف با شماره (بعد از دیدن لیست)
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف جوک "))
def jokes_del_by_index(m):
    parts = cmd_text(m).split()
    if len(parts) < 3:
        msg = bot.reply_to(m, "❗ فرمت: «حذف جوک 3»")
        return auto_del(m.chat.id, msg.message_id)
    try:
        idx = int(parts[2])
        start = max(0, len(jokes) - 20)
        real = start + idx - 1
        if 0 <= real < len(jokes):
            jokes.pop(real)
            msg = bot.reply_to(m, "✅ جوک حذف شد.")
        else:
            msg = bot.reply_to(m, "❗ شماره نامعتبر.")
    except:
        msg = bot.reply_to(m, "❗ فقط عدد صحیح بزن.")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m).startswith("حذف فال "))
def fal_del_by_index(m):
    parts = cmd_text(m).split()
    if len(parts) < 3:
        msg = bot.reply_to(m, "❗ فرمت: «حذف فال 2»")
        return auto_del(m.chat.id, msg.message_id)
    try:
        idx = int(parts[2])
        start = max(0, len(fortunes) - 20)
        real = start + idx - 1
        if 0 <= real < len(fortunes):
            fortunes.pop(real)
            msg = bot.reply_to(m, "✅ فال حذف شد.")
        else:
            msg = bot.reply_to(m, "❗ شماره نامعتبر.")
    except:
        msg = bot.reply_to(m, "❗ فقط عدد صحیح بزن.")
    auto_del(m.chat.id, msg.message_id)

# حذف با ریپلای (تطبیق دقیق متن/فایل)
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "حذف جوک")
def jokes_del_by_reply(m):
    t = m.reply_to_message
    removed = False
    if t.text:
        for i, j in enumerate(jokes):
            if j["type"] == "text" and j["content"] == t.text:
                jokes.pop(i); removed = True; break
    elif t.photo:
        fid = t.photo[-1].file_id
        for i, j in enumerate(jokes):
            if j["type"] == "photo" and j.get("file") == fid:
                jokes.pop(i); removed = True; break
    msg = bot.reply_to(m, "✅ جوک حذف شد." if removed else "ℹ️ جوک مطابق پیدا نشد.")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "حذف فال")
def fal_del_by_reply(m):
    t = m.reply_to_message
    removed = False
    if t.text:
        for i, f in enumerate(fortunes):
            if f["type"] == "text" and f["content"] == t.text:
                fortunes.pop(i); removed = True; break
    elif t.photo:
        fid = t.photo[-1].file_id
        for i, f in enumerate(fortunes):
            if f["type"] == "photo" and f.get("file") == fid:
                fortunes.pop(i); removed = True; break
    msg = bot.reply_to(m, "✅ فال حذف شد." if removed else "ℹ️ فال مطابق پیدا نشد.")
    auto_del(m.chat.id, msg.message_id)

# پاکسازی کامل لیست‌ها
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "پاکسازی جوک‌ها")
def jokes_clear(m):
    jokes.clear()
    msg = bot.reply_to(m, "🗑 همه جوک‌ها پاک شدند.")
    auto_del(m.chat.id, msg.message_id)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) == "پاکسازی فال‌ها")
def fal_clear(m):
    fortunes.clear()
    msg = bot.reply_to(m, "🗑 همه فال‌ها پاک شدند.")
    auto_del(m.chat.id, msg.message_id)

# ================== قفل‌ها: پنل (فعال/غیرفعال) ==================
locks = {k:{} for k in ["links","stickers","bots","tabchi","group","photo","video","gif","file","music","voice","forward"]}
LOCK_MAP = {
    "لینک":"links","استیکر":"stickers","ربات":"bots","تبچی":"tabchi","گروه":"group",
    "عکس":"photo","ویدیو":"video","گیف":"gif","فایل":"file","موزیک":"music","ویس":"voice","فوروارد":"forward"
}

@bot.message_handler(func=lambda m: cmd_text(m) == "پنل")
def locks_panel(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for name, key in LOCK_MAP.items():
        st = "🔒" if locks[key].get(m.chat.id) else "🔓"
        btns.append(types.InlineKeyboardButton(f"{st} {name}", callback_data=f"toggle:{key}:{m.chat.id}"))
    kb.add(*btns)
    kb.add(types.InlineKeyboardButton("❌ بستن", callback_data=f"close:{m.chat.id}"))
    bot.reply_to(m, "🛠 پنل مدیریت قفل‌ها:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("toggle:"))
def cb_toggle(c):
    _, key, chat_id = c.data.split(":")
    chat_id = int(chat_id)
    if not is_admin(chat_id, c.from_user.id):
        return bot.answer_callback_query(c.id, "❌ فقط مدیران", show_alert=True)
    cur = locks[key].get(chat_id, False)
    locks[key][chat_id] = not cur
    bot.answer_callback_query(c.id, "✅ تغییر انجام شد.")
    # بازسازی کیبورد
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for name, k in LOCK_MAP.items():
        st = "🔒" if locks[k].get(chat_id) else "🔓"
        btns.append(types.InlineKeyboardButton(f"{st} {name}", callback_data=f"toggle:{k}:{chat_id}"))
    kb.add(*btns)
    kb.add(types.InlineKeyboardButton("❌ بستن", callback_data=f"clos# ================== اجرای قفل‌های واقعی ==================

@bot.message_handler(content_types=['text','photo','video','document','audio','voice','sticker','animation','forward_from','forward_from_chat'])
def enforce_locks(m):
    if is_admin(m.chat.id, m.from_user.id): 
        return  # مدیرها مستثنی هستند

    # لینک
    if locks["links"].get(m.chat.id) and m.text and ("http://" in m.text or "https://" in m.text or "t.me" in m.text):
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass

    # استیکر
    if locks["stickers"].get(m.chat.id) and m.sticker:
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass

    # عکس
    if locks["photo"].get(m.chat.id) and m.photo:
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass

    # ویدیو
    if locks["video"].get(m.chat.id) and m.video:
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass

    # گیف
    if locks["gif"].get(m.chat.id) and m.animation:
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass

    # فایل
    if locks["file"].get(m.chat.id) and m.document:
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass

    # موزیک
    if locks["music"].get(m.chat.id) and m.audio:
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass

    # ویس
    if locks["voice"].get(m.chat.id) and m.voice:
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass

    # فوروارد
    if locks["forward"].get(m.chat.id) and (m.forward_from or m.forward_from_chat):
        try: bot.delete_message(m.chat.id, m.message_id)
        except: pass


# قفل ورود ربات‌ها / تبچی‌ها
@bot.message_handler(content_types=['new_chat_members'])
def block_new_bots(m):
    for u in m.new_chat_members:
        if u.is_bot and locks["bots"].get(m.chat.id):
            try: bot.kick_chat_member(m.chat.id, u.id)
            except: pass
        if "tabchi" in (u.username or "").lower() and locks["tabchi"].get(m.chat.id):
            try: bot.kick_chat_member(m.chat.id, u.id)
            except: pass


# ================== اجرای ربات ==================
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True, timeout=30)
