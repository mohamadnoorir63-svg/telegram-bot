# -*- coding: utf-8 -*-
import re
from datetime import datetime
import telebot
from telebot import types

# ====== تنظیمات ======
TOKEN   = "7462131830:AAEGzgbjETaf3eukzGHW613i4y61Cs7lzTE"
SUDO_ID = 7089376754
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
# =====================

HELP_TEXT = """
📖 دستورات مدیریتی و ابزارها:

⏰ ساعت | 📅 تاریخ | 📊 آمار | 🆔 ایدی
🔒 قفل لینک / باز کردن لینک
🧷 قفل استیکر / باز کردن استیکر
🤖 قفل ربات / باز کردن ربات
🚫 قفل تبچی / باز کردن تبچی
🔐 قفل گروه / باز کردن گروه
🖼 قفل عکس / باز کردن عکس
🎥 قفل ویدیو / باز کردن ویدیو
🎭 قفل گیف / باز کردن گیف
📎 قفل فایل / باز کردن فایل
🎶 قفل موزیک / باز کردن موزیک
🎙 قفل ویس / باز کردن ویس
🔄 قفل فوروارد / باز کردن فوروارد
🚫 بن / ✅ حذف بن   (ریپلای)
🔕 سکوت / 🔊 حذف سکوت (ریپلای)
👑 مدیر / ❌ حذف مدیر (ریپلای)
📌 پن / ❌ حذف پن     (ریپلای)
⚠️ اخطار           (ریپلای، سه‌تا = بن)
📋 لیست مدیران گروه | 📋 لیست مدیران ربات
🎉 خوشامد روشن / خاموش
✍️ خوشامد متن [متن دلخواه]
🖼 ثبت عکس (ریپلای روی عکس و بفرست: ثبت عکس)
🧹 پاکسازی [تعداد]  (مثل: پاکسازی 9999)
🔤 فونت [متن]
📢 ارسال (فقط سودو) → سپس متن/عکس را بفرست
🛠 وضعیت ربات
🚪 لفت بده (فقط سودو)
"""

# ===== ذخایر ساده در حافظه =====
joined_groups = set()      # برای ارسال همگانی
warnings = {}              # اخطارها: {(chat_id,user_id): n}
welcome_enabled = {}       # خوشامد روشن/خاموش
welcome_texts = {}         # متن خوشامد
welcome_photos = {}        # عکس خوشامد (file_id)

# قفل‌ها
locks = {
    "links": {}, "stickers": {}, "bots": {}, "tabchi": {}, "group": {},
    "photo": {}, "video": {}, "gif": {}, "file": {}, "music": {}, "voice": {}, "forward": {}
}

# ===== کمک‌تابع‌ها =====
def is_admin(chat_id, user_id):
    if user_id == SUDO_ID:
        return True
    try:
        st = bot.get_chat_member(chat_id, user_id).status
        return st in ("administrator", "creator")
    except:
        return False

def add_warn(chat_id, user_id):
    key = (chat_id, user_id)
    warnings[key] = warnings.get(key, 0) + 1
    return warnings[key]

def reset_warn(chat_id, user_id):
    warnings.pop((chat_id, user_id), None)

# فونت‌ساز
def build_fonts(txt: str):
    txt = txt.strip()
    if not txt:
        return []
    # انگلیسی (اگر حروف لاتین داشت)
    en_samples = []
    normal = txt
    maps = [
        ("𝐌𝐎𝐇𝐀𝐌𝐌𝐀𝐃", str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                                     "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙"
                                     "𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳")),
        ("𝕄𝕆ℍ𝔸𝕄𝕄𝔸𝔻", str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                                     "𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ"
                                     "𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷")),
        ("𝖬𝖮𝖧𝖠𝖬𝖬𝖠𝖣", str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                                     "𝖠𝖡𝖢𝖣𝖤𝖥𝖦𝖧𝖨𝖩𝖪𝖫𝖬𝖭𝖮𝖯𝖰𝖱𝖲𝖳𝖴𝖵𝖶𝖷𝖸𝖹"
                                     "𝖺𝖻𝖼𝖽𝖾𝖿𝗀𝗁𝗂𝗃𝗄𝗅𝗆𝗇𝗈𝗉𝗊𝗋𝗌𝗍𝗎𝗏𝗐𝗑𝗒𝗓")),
        ("ⓂⓄⒽⒶⓂⓂⒶⒹ", str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                                     "ⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏ"
                                     "ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩ")),
        ("ᴍᴏʜᴀᴍᴍᴀᴅ", str.maketrans("abcdefghijklmnopqrstuvwxyz", "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"))
    ]
    for _, mp in maps:
        en_samples.append(normal.translate(mp))

    # فارسی: چند الگوی عاشقانه/خطرناک با کاراکترهای ترکیبی
    fa = txt
    hearts = "ـ"  # کشیده
    fa_samples = [
        f"مَِــَِ{fa}َِ",                     # عاشقانه با حرکات
        f"{fa[0]}{hearts*3}{fa[1:] if len(fa)>1 else ''}",   # کشیده
        f"مُِـٖٖـۘۘـ{fa}ـُِ",                 # فانتزی
        f"ـ{fa}ـ",                               # ساده کشیده
        f"{fa}ۣۣـ🍁",                           # ایموجی
        f"꧁ {fa} ꧂",                           # قاب
        f"『 {fa} 』",
        f"✮ {fa} ✮",
        f"☠️ {fa} ☠️",
        f"❤ {fa} ❤",
    ]
    return fa_samples + en_samples

# ===== وقتی ربات اضافه/حذف شد (برای ارسال همگانی) =====
@bot.my_chat_member_handler()
def track_groups(upd):
    try:
        if upd.chat and upd.chat.type in ("group", "supergroup"):
            if upd.new_chat_member and upd.new_chat_member.status in ("member","administrator"):
                joined_groups.add(upd.chat.id)
            elif upd.new_chat_member and upd.new_chat_member.status == "kicked":
                joined_groups.discard(upd.chat.id)
    except:
        pass

# ===== دستورات پایه =====
@bot.message_handler(func=lambda m: m.text == "راهنما")
def help_cmd(m): bot.reply_to(m, HELP_TEXT)

@bot.message_handler(func=lambda m: m.text == "ساعت")
def time_cmd(m): bot.reply_to(m, f"⏰ ساعت: {datetime.now().strftime('%H:%M:%S')}")

@bot.message_handler(func=lambda m: m.text == "تاریخ")
def date_cmd(m): bot.reply_to(m, f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d')}")

@bot.message_handler(func=lambda m: m.text == "ایدی")
def id_cmd(m): bot.reply_to(m, f"🆔 آیدی شما: <code>{m.from_user.id}</code>\n🆔 آیدی گروه: <code>{m.chat.id}</code>")

@bot.message_handler(func=lambda m: m.text == "آمار")
def stats(m):
    try: count = bot.get_chat_member_count(m.chat.id)
    except: count = "نامشخص"
    bot.reply_to(m, f"📊 اعضای گروه: {count}")

# ===== وضعیت ربات =====
@bot.message_handler(func=lambda m: m.text == "وضعیت ربات")
def bot_perms(m):
    try:
        me = bot.get_chat_member(m.chat.id, bot.get_me().id)
        if me.status != "administrator":
            return bot.reply_to(m, "❗ ربات ادمین نیست. لطفاً ربات را ادمین کنید.")
        flags = {
            "مدیریت چت": getattr(me, "can_manage_chat", False),
            "حذف پیام": getattr(me, "can_delete_messages", False),
            "محدودسازی اعضا": getattr(me, "can_restrict_members", False),
            "پین پیام": getattr(me, "can_pin_messages", False),
            "دعوت کاربر": getattr(me, "can_invite_users", False),
            "افزودن مدیر": getattr(me, "can_promote_members", False),
            "مدیریت ویدیوچت": getattr(me, "can_manage_video_chats", False),
        }
        bot.reply_to(m, "🛠 وضعیت ربات:\n" + "\n".join(f"{'✅' if v else '❌'} {k}" for k,v in flags.items()))
    except:
        bot.reply_to(m, "نتوانستم وضعیت را بخوانم.")

# ===== خوشامد =====
@bot.message_handler(content_types=['new_chat_members'])
def welcome(m):
    for u in m.new_chat_members:
        # ضد ربات/تبچی
        if u.is_bot and locks["bots"].get(m.chat.id, False):
            try: bot.ban_chat_member(m.chat.id, u.id)
            except: pass
            continue
        if (not u.first_name or u.first_name.strip()=="") and locks["tabchi"].get(m.chat.id, False):
            try: bot.ban_chat_member(m.chat.id, u.id)
            except: pass
            continue

        if not welcome_enabled.get(m.chat.id, False):
            continue
        name = (u.first_name or "").strip()
        txt = welcome_texts.get(m.chat.id, "خوش آمدی 🌹").replace("{name}", name)
        if m.chat.id in welcome_photos:
            bot.send_photo(m.chat.id, welcome_photos[m.chat.id], caption=txt)
        else:
            bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda m: m.text == "خوشامد روشن")
def welcome_on(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    welcome_enabled[m.chat.id] = True
    bot.reply_to(m, "✅ خوشامد فعال شد.")

@bot.message_handler(func=lambda m: m.text == "خوشامد خاموش")
def welcome_off(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    welcome_enabled[m.chat.id] = False
    bot.reply_to(m, "❌ خوشامد خاموش شد.")

@bot.message_handler(func=lambda m: m.text and m.text.startswith("خوشامد متن"))
def welcome_text(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    txt = m.text.replace("خوشامد متن","",1).strip()
    welcome_texts[m.chat.id] = txt
    bot.reply_to(m, "✍️ متن خوشامد ذخیره شد.")

@bot.message_handler(func=lambda m: m.reply_to_message is not None and m.text == "ثبت عکس")
def save_photo(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    if not m.reply_to_message.photo:
        return bot.reply_to(m, "❗ باید روی یک عکس ریپلای کنید.")
    welcome_photos[m.chat.id] = m.reply_to_message.photo[-1].file_id
    bot.reply_to(m, "🖼 عکس خوشامد ذخیره شد.")

# ===== لفت (فقط سودو) =====
@bot.message_handler(func=lambda m: m.text == "لفت بده")
def leave_cmd(m):
    if m.from_user.id != SUDO_ID: return
    bot.send_message(m.chat.id, "به دستور سودو خارج می‌شوم 👋")
    try: bot.leave_chat(m.chat.id)
    except: pass

# ===== قفل‌ها =====
def lock_set(chat_id, key, state):
    locks[key][chat_id] = state

@bot.message_handler(func=lambda m: m.text in [
    "قفل گروه","باز کردن گروه","قفل لینک","باز کردن لینک","قفل استیکر","باز کردن استیکر",
    "قفل ربات","باز کردن ربات","قفل تبچی","باز کردن تبچی","قفل عکس","باز کردن عکس",
    "قفل ویدیو","باز کردن ویدیو","قفل گیف","باز کردن گیف","قفل فایل","باز کردن فایل",
    "قفل موزیک","باز کردن موزیک","قفل ویس","باز کردن ویس","قفل فوروارد","باز کردن فوروارد"
])
def lock_toggle(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    t = m.text; cid = m.chat.id
    if t=="قفل گروه":
        lock_set(cid,"group",True)
        try: bot.set_chat_permissions(cid, types.ChatPermissions(can_send_messages=False))
        except: pass
        return bot.reply_to(m,"🔐 گروه قفل شد.")
    if t=="باز کردن گروه":
        lock_set(cid,"group",False)
        try: bot.set_chat_permissions(cid, types.ChatPermissions(can_send_messages=True))
        except: pass
        return bot.reply_to(m,"✅ گروه باز شد.")

    mp = {
        "قفل لینک":("links",True,"🔒 لینک قفل شد."),
        "باز کردن لینک":("links",False,"🔓 لینک آزاد شد."),
        "قفل استیکر":("stickers",True,"🧷 استیکر قفل شد."),
        "باز کردن استیکر":("stickers",False,"🧷 استیکر آزاد شد."),
        "قفل ربات":("bots",True,"🤖 ربات‌ها قفل شدند."),
        "باز کردن ربات":("bots",False,"🤖 ربات‌ها آزاد شدند."),
        "قفل تبچی":("tabchi",True,"🚫 تبچی قفل شد."),
        "باز کردن تبچی":("tabchi",False,"🚫 تبچی آزاد شد."),
        "قفل عکس":("photo",True,"🖼 عکس قفل شد."),
        "باز کردن عکس":("photo",False,"🖼 عکس آزاد شد."),
        "قفل ویدیو":("video",True,"🎥 ویدیو قفل شد."),
        "باز کردن ویدیو":("video",False,"🎥 ویدیو آزاد شد."),
        "قفل گیف":("gif",True,"🎭 گیف قفل شد."),
        "باز کردن گیف":("gif",False,"🎭 گیف آزاد شد."),
        "قفل فایل":("file",True,"📎 فایل قفل شد."),
        "باز کردن فایل":("file",False,"📎 فایل آزاد شد."),
        "قفل موزیک":("music",True,"🎶 موزیک قفل شد."),
        "باز کردن موزیک":("music",False,"🎶 موزیک آزاد شد."),
        "قفل ویس":("voice",True,"🎙 ویس قفل شد."),
        "باز کردن ویس":("voice",False,"🎙 ویس آزاد شد."),
        "قفل فوروارد":("forward",True,"🔄 فوروارد قفل شد."),
        "باز کردن فوروارد":("forward",False,"🔄 فوروارد آزاد شد."),
    }
    key, st, msg = mp[t]
    lock_set(cid, key, st)
    bot.reply_to(m, msg)

# حذف رسانه مطابق قفل‌ها
@bot.message_handler(content_types=['photo','video','document','audio','voice','sticker'])
def media_filter(m):
    try:
        if locks["photo"].get(m.chat.id) and m.content_type=="photo": bot.delete_message(m.chat.id, m.message_id)
        if locks["video"].get(m.chat.id) and m.content_type=="video": bot.delete_message(m.chat.id, m.message_id)
        if locks["file"].get(m.chat.id)  and m.content_type=="document": bot.delete_message(m.chat.id, m.message_id)
        if locks["music"].get(m.chat.id) and m.content_type=="audio": bot.delete_message(m.chat.id, m.message_id)
        if locks["voice"].get(m.chat.id) and m.content_type=="voice": bot.delete_message(m.chat.id, m.message_id)
        if locks["gif"].get(m.chat.id)   and (m.content_type=="document" and m.document and m.document.mime_type=="video/mp4"):
            bot.delete_message(m.chat.id, m.message_id)
        if locks["stickers"].get(m.chat.id) and m.content_type=="sticker":
            bot.delete_message(m.chat.id, m.message_id)
    except: pass

# ===== بن/سکوت =====
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="بن")
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.ban_chat_member(m.chat.id, m.reply_to_message.from_user.id)
        bot.reply_to(m,"🚫 کاربر بن شد.")
    except: bot.reply_to(m,"❗ نتوانستم بن کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف بن")
def unban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.unban_chat_member(m.chat.id, m.reply_to_message.from_user.id)
        reset_warn(m.chat.id, m.reply_to_message.from_user.id)
        bot.reply_to(m,"✅ کاربر از بن خارج شد.")
    except: bot.reply_to(m,"❗ نتوانستم حذف بن کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="سکوت")
def mute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.restrict_chat_member(m.chat.id, m.reply_to_message.from_user.id, can_send_messages=False)
        bot.reply_to(m,"🔕 کاربر سایلنت شد.")
    except: bot.reply_to(m,"❗ نتوانستم سکوت کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف سکوت")
def unmute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        bot.restrict_chat_member(m.chat.id, m.reply_to_message.from_user.id,
                                 can_send_messages=True, can_send_media_messages=True,
                                 can_send_other_messages=True, can_add_web_page_previews=True)
        bot.reply_to(m,"🔊 کاربر از سکوت خارج شد.")
    except: bot.reply_to(m,"❗ نتوانستم حذف سکوت کنم.")

# ===== مدیر/حذف مدیر =====
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="مدیر")
def promote(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        me = bot.get_chat_member(m.chat.id, bot.get_me().id)
        if me.status!="administrator" or not getattr(me,"can_promote_members",False):
            return bot.reply_to(m,"❗ ربات مجوز «افزودن مدیر» ندارد.")
        bot.promote_chat_member(
            m.chat.id, m.reply_to_message.from_user.id,
            can_manage_chat=True, can_delete_messages=True,
            can_restrict_members=True, can_pin_messages=True,
            can_invite_users=True, can_manage_video_chats=True,
            can_promote_members=False
        )
        bot.reply_to(m,"👑 کاربر مدیر شد.")
    except: bot.reply_to(m,"❗ نتوانستم مدیر کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف مدیر")
def demote(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        me = bot.get_chat_member(m.chat.id, bot.get_me().id)
        if me.status!="administrator" or not getattr(me,"can_promote_members",False):
            return bot.reply_to(m,"❗ ربات مجوز حذف مدیر ندارد.")
        bot.promote_chat_member(
            m.chat.id, m.reply_to_message.from_user.id,
            can_manage_chat=False, can_delete_messages=False,
            can_restrict_members=False, can_pin_messages=False,
            can_invite_users=False, can_manage_video_chats=False,
            can_promote_members=False
        )
        bot.reply_to(m,"❌ کاربر از مدیریت حذف شد.")
    except: bot.reply_to(m,"❗ نتوانستم حذف مدیر کنم.")

# ===== پین / حذف پین =====
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="پن")
def pin(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        me = bot.get_chat_member(m.chat.id, bot.get_me().id)
        if me.status!="administrator" or not getattr(me,"can_pin_messages",False):
            return bot.reply_to(m,"❗ ربات مجوز پین ندارد.")
        bot.pin_chat_message(m.chat.id, m.reply_to_message.message_id, disable_notification=True)
        bot.reply_to(m,"📌 پیام پین شد.")
    except: bot.reply_to(m,"❗ نتوانستم پین کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف پن")
def unpin(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    try:
        me = bot.get_chat_member(m.chat.id, bot.get_me().id)
        if me.status!="administrator" or not getattr(me,"can_pin_messages",False):
            return bot.reply_to(m,"❗ ربات مجوز حذف پین ندارد.")
        bot.unpin_chat_message(m.chat.id, m.reply_to_message.message_id)
        bot.reply_to(m,"❌ پین پیام برداشته شد.")
    except: bot.reply_to(m,"❗ نتوانستم حذف پین کنم.")

# ===== لیست‌ها =====
@bot.message_handler(func=lambda m: m.text=="لیست مدیران گروه")
def list_group_admins(m):
    try:
        admins = bot.get_chat_administrators(m.chat.id)
        lines = []
        for a in admins:
            u = a.user
            name = ((u.first_name or "") + (" " + u.last_name if u.last_name else "")).strip() or "بدون‌نام"
            lines.append(f"• {name} — <code>{u.id}</code>")
        bot.reply_to(m, "📋 مدیران گروه:\n" + "\n".join(lines))
    except: bot.reply_to(m,"❗ نتوانستم لیست مدیران را بگیرم.")

@bot.message_handler(func=lambda m: m.text=="لیست مدیران ربات")
def list_bot_admins(m):
    bot.reply_to(m, f"📋 مدیران ربات:\n• سودو: <code>{SUDO_ID}</code>")

# ===== پاکسازی =====
@bot.message_handler(func=lambda m: m.text and m.text.startswith("پاکسازی"))
def clear_messages(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    parts = m.text.split()
    n = 50
    if len(parts) > 1:
        try: n = max(1, min(10000, int(parts[1])))
        except: pass
    start = m.message_id - 1
    stop = m.message_id - n - 1
    for msg_id in range(start, stop, -1):
        try: bot.delete_message(m.chat.id, msg_id)
        except: pass
    bot.reply_to(m, f"🧹 {n} پیام آخر پاک شد.")

# ===== اخطار =====
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="اخطار")
def warn_cmd(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = m.reply_to_message.from_user.id
    cnt = add_warn(m.chat.id, uid)
    if cnt >= 3:
        try:
            bot.ban_chat_member(m.chat.id, uid)
            reset_warn(m.chat.id, uid)
            bot.reply_to(m, "⛔️ ۳ اخطار! کاربر بن شد.")
        except:
            bot.reply_to(m, "❗ نتوانستم بن کنم.")
    else:
        bot.reply_to(m, f"⚠️ اخطار {cnt}/3 ثبت شد.")

# ===== ارسال همگانی (فقط سودو) =====
waiting_broadcast = {}

@bot.message_handler(func=lambda m: m.from_user.id==SUDO_ID and m.text=="ارسال")
def ask_broadcast(m):
    waiting_broadcast[m.from_user.id] = True
    bot.reply_to(m, "📢 متن/عکس بعدی را بفرست تا به همهٔ گروه‌ها ارسال شود.")

@bot.message_handler(func=lambda m: m.from_user.id==SUDO_ID and waiting_broadcast.get(m.from_user.id))
def do_broadcast(m):
    waiting_broadcast[m.from_user.id] = False
    sent = 0
    for gid in list(joined_groups):
        try:
            if m.content_type=="text":
                bot.send_message(gid, m.text)
            elif m.content_type=="photo":
                bot.send_photo(gid, m.photo[-1].file_id, caption=m.caption or "")
            sent += 1
        except: pass
    bot.reply_to(m, f"✅ پیام به {sent} گروه ارسال شد.")

# ===== فونت =====
@bot.message_handler(func=lambda m: m.text and m.text.startswith("فونت"))
def font_cmd(m):
    txt = m.text.replace("فونت","",1).strip()
    if not txt:
        return bot.reply_to(m, "مثال: فونت گل")
    variants = build_fonts(txt)[:20]
    bot.reply_to(m, "🎨 نمونه فونت‌ها:\n\n" + "\n".join("• " + v for v in variants))

# ===== ضد لینک + فوروارد + پاسخ سودو =====
@bot.message_handler(content_types=['text'])
def text_guard(m):
    # پاسخ به سودو: «ربات»
    if m.from_user.id == SUDO_ID and m.text.strip() == "ربات":
        return bot.reply_to(m, "جانم سودو 👑")

    # لینک
    if locks["links"].get(m.chat.id, False) and not is_admin(m.chat.id, m.from_user.id):
        if re.search(r"(t\.me|telegram\.me|telegram\.org|https?://)", (m.text or "").lower()):
            try: bot.delete_message(m.chat.id, m.message_id)
            except: pass

    # فوروارد
    if locks["forward"].get(m.chat.id, False):
   
