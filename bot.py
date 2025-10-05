# -*- coding: utf-8 -*-
import telebot
from telebot import types
from datetime import datetime
import re, random

# ================== تنظیمات ==================
TOKEN   = "7462131830:AAEGzgbjETaf3eukzGHW613i4y61Cs7lzTE"
SUDO_ID = 7089376754  # سودوی ربات (فقط این آیدی همه‌کاره است)
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
# ============================================

HELP_TEXT = """
📖 لیست دستورات:

⏰ ساعت | 📅 تاریخ | 📊 آمار | 🆔 ایدی
🔒 قفل لینک / باز کردن لینک
🧷 قفل استیکر / باز کردن استیکر
🤖 قفل ربات / باز کردن ربات
🚫 قفل تبچی / باز کردن تبچی
🔐 قفل گروه / باز کردن گروه
🚫 بن / ✅ حذف بن (ریپلای)
🔕 سکوت / 🔊 حذف سکوت (ریپلای)
⚠️ اخطار / حذف اخطار (ریپلای) — سه اخطار = بن
👑 مدیر / ❌ حذف مدیر (ریپلای)
📌 پن / ❌ حذف پن (ریپلای)
📋 لیست مدیران گروه
📋 لیست مدیران ربات
🎉 خوشامد روشن / خاموش
✍️ خوشامد متن [متن دلخواه]
🖼 ثبت عکس (روی عکس ریپلای کن و بفرست: ثبت عکس)
🧹 پاکسازی (حذف ۵۰ پیام آخر) | پاکسازی 9999 | حذف پیام 9999
✍️ فونت [متن دلخواه]
🧾 ثبت اصل [متن] (فقط سودو - ریپلای) | اصل (ریپلای)
🤣 جوک | 🔮 فال | 🧑‍💼 بیو
➕ ثبت جوک / ثبت فال / ثبت بیو  (فقط سودو؛ متن یا عکس)
📢 ارسال (فقط سودو)
🛠 وضعیت ربات
🚪 لفت بده (فقط سودو)
"""

# ——— ذخیره گروه‌ها برای «ارسال» ———
joined_groups = set()
@bot.my_chat_member_handler()
def track_groups(upd):
    try:
        chat = upd.chat
        if chat and chat.type in ("group","supergroup"):
            joined_groups.add(chat.id)
    except:
        pass

# ——— ادمین‌چک ———
def is_admin(chat_id, user_id):
    if user_id == SUDO_ID: return True
    try:
        st = bot.get_chat_member(chat_id,user_id).status
        return st in ("administrator","creator")
    except:
        return False

# ========= دستورات پایه =========
@bot.message_handler(func=lambda m: m.text=="راهنما")
def help_cmd(m): bot.reply_to(m, HELP_TEXT)

@bot.message_handler(func=lambda m: m.text=="ساعت")
def time_cmd(m): bot.reply_to(m, f"⏰ ساعت: {datetime.now().strftime('%H:%M:%S')}")

@bot.message_handler(func=lambda m: m.text=="تاریخ")
def date_cmd(m): bot.reply_to(m, f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d')}")

@bot.message_handler(func=lambda m: m.text=="ایدی")
def id_cmd(m): bot.reply_to(m, f"🆔 آیدی شما: <code>{m.from_user.id}</code>\n🆔 آیدی گروه: <code>{m.chat.id}</code>")

@bot.message_handler(func=lambda m: m.text=="آمار")
def stats(m):
    try: count=bot.get_chat_member_count(m.chat.id)
    except: count="نامشخص"
    bot.reply_to(m,f"📊 اعضای گروه: {count}")

# ========= وضعیت ربات =========
@bot.message_handler(func=lambda m: m.text=="وضعیت ربات")
def bot_perms(m):
    try:
        me_id = bot.get_me().id
        cm = bot.get_chat_member(m.chat.id, me_id)
        if cm.status != "administrator":
            return bot.reply_to(m, "❗ ربات ادمین نیست.")
        flags = {
            "مدیریت چت": getattr(cm, "can_manage_chat", False),
            "حذف پیام": getattr(cm, "can_delete_messages", False),
            "محدودسازی اعضا": getattr(cm, "can_restrict_members", False),
            "پین پیام": getattr(cm, "can_pin_messages", False),
            "دعوت کاربر": getattr(cm, "can_invite_users", False),
            "افزودن مدیر": getattr(cm, "can_promote_members", False),
            "مدیریت ویدیوچت": getattr(cm, "can_manage_video_chats", False),
        }
        lines = [f"{'✅' if v else '❌'} {k}" for k,v in flags.items()]
        bot.reply_to(m, "🛠 وضعیت ربات:\n" + "\n".join(lines))
    except:
        bot.reply_to(m, "نتوانستم وضعیت را بخوانم.")

# ========= خوشامد =========
welcome_enabled,welcome_texts,welcome_photos={}, {}, {}

@bot.message_handler(content_types=['new_chat_members'])
def welcome(m):
    for u in m.new_chat_members:
        if not welcome_enabled.get(m.chat.id): continue
        name=u.first_name or ""
        txt=welcome_texts.get(m.chat.id,"خوش آمدی 🌹").replace("{name}",name)
        if m.chat.id in welcome_photos:
            bot.send_photo(m.chat.id,welcome_photos[m.chat.id],caption=txt)
        else:
            bot.send_message(m.chat.id,txt)

@bot.message_handler(func=lambda m:m.text=="خوشامد روشن")
def w_on(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    welcome_enabled[m.chat.id]=True; bot.reply_to(m,"✅ خوشامد فعال شد.")

@bot.message_handler(func=lambda m:m.text=="خوشامد خاموش")
def w_off(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    welcome_enabled[m.chat.id]=False; bot.reply_to(m,"❌ خوشامد خاموش شد.")

@bot.message_handler(func=lambda m:m.text and m.text.startswith("خوشامد متن"))
def w_txt(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    txt=m.text.replace("خوشامد متن","",1).strip()
    welcome_texts[m.chat.id]=txt; bot.reply_to(m,"✍️ متن خوشامد ذخیره شد.")

@bot.message_handler(func=lambda m:m.reply_to_message and m.text=="ثبت عکس")
def w_photo(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    if not m.reply_to_message.photo: return
    welcome_photos[m.chat.id]=m.reply_to_message.photo[-1].file_id
    bot.reply_to(m,"🖼 عکس خوشامد ذخیره شد.")

# ========= قفل‌ها =========
lock_links, lock_stickers, lock_bots, lock_tabcchi, lock_group = {},{},{},{},{}

@bot.message_handler(func=lambda m: m.text=="قفل گروه")
def lock_group_cmd(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    bot.set_chat_permissions(m.chat.id, types.ChatPermissions(can_send_messages=False))
    bot.reply_to(m,"🔐 گروه قفل شد.")

@bot.message_handler(func=lambda m: m.text=="باز کردن گروه")
def unlock_group_cmd(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    bot.set_chat_permissions(m.chat.id, types.ChatPermissions(can_send_messages=True))
    bot.reply_to(m,"✅ گروه باز شد.")

@bot.message_handler(func=lambda m: m.text=="قفل لینک")
def lock_links_cmd(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    lock_links[m.chat.id]=True; bot.reply_to(m,"🔒 لینک‌ها قفل شدند.")

@bot.message_handler(func=lambda m: m.text=="باز کردن لینک")
def unlock_links_cmd(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    lock_links[m.chat.id]=False; bot.reply_to(m,"🔓 لینک‌ها آزاد شدند.")

@bot.message_handler(func=lambda m: m.text=="قفل استیکر")
def lock_sticker_cmd(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    lock_stickers[m.chat.id]=True; bot.reply_to(m,"🧷 استیکرها قفل شدند.")

@bot.message_handler(func=lambda m: m.text=="باز کردن استیکر")
def unlock_sticker_cmd(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    lock_stickers[m.chat.id]=False; bot.reply_to(m,"🧷 استیکرها آزاد شدند.")

@bot.message_handler(func=lambda m: m.text=="قفل ربات")
def lock_bot_cmd(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    lock_bots[m.chat.id]=True; bot.reply_to(m,"🤖 اضافه شدن ربات‌ها قفل شد.")

@bot.message_handler(func=lambda m: m.text=="باز کردن ربات")
def unlock_bot_cmd(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    lock_bots[m.chat.id]=False; bot.reply_to(m,"🤖 اضافه شدن ربات‌ها آزاد شد.")

@bot.message_handler(func=lambda m: m.text=="قفل تبچی")
def lock_tabcchi_cmd(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    lock_tabcchi[m.chat.id]=True; bot.reply_to(m,"🚫 ورود تبچی‌ها قفل شد.")

@bot.message_handler(func=lambda m: m.text=="باز کردن تبچی")
def unlock_tabcchi_cmd(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    lock_tabcchi[m.chat.id]=False; bot.reply_to(m,"🚫 ورود تبچی‌ها آزاد شد.")

# جلوگیری از استیکر
@bot.message_handler(content_types=['sticker'])
def block_sticker(m):
    if lock_stickers.get(m.chat.id) and m.from_user.id!=SUDO_ID:
        try: bot.delete_message(m.chat.id,m.message_id)
        except: pass

# ========= بن و سکوت =========
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
        bot.restrict_chat_member(
            m.chat.id, m.reply_to_message.from_user.id,
            can_send_messages=True, can_send_media_messages=True,
            can_send_other_messages=True, can_add_web_page_previews=True
        )
        bot.reply_to(m,"🔊 کاربر از سکوت خارج شد.")
    except: bot.reply_to(m,"❗ نتوانستم حذف سکوت کنم.")

# ========= اخطار =========
warnings = {}
MAX_WARNINGS=3

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="اخطار")
def warn_user(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid=m.reply_to_message.from_user.id
    warnings.setdefault(m.chat.id,{}); warnings[m.chat.id][uid]=warnings[m.chat.id].get(uid,0)+1
    count=warnings[m.chat.id][uid]
    if count>=MAX_WARNINGS:
        try:
            bot.ban_chat_member(m.chat.id,uid)
            bot.reply_to(m,"🚫 کاربر با ۳ اخطار بن شد.")
            warnings[m.chat.id][uid]=0
        except: bot.reply_to(m,"❗ نتوانستم بن کنم.")
    else:
        bot.reply_to(m,f"⚠️ اخطار {count}/{MAX_WARNINGS} ثبت شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف اخطار")
def reset_warn(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    uid=m.reply_to_message.from_user.id
    if m.chat.id in warnings and uid in warnings[m.chat.id]:
        warnings[m.chat.id][uid]=0; bot.reply_to(m,f"✅ اخطارهای <code>{uid}</code> حذف شد.")
    else:
        bot.reply_to(m,"ℹ️ اخطاری برای این کاربر ثبت نشده.")

# ========= مدیر / حذف مدیر =========
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="مدیر")
def promote_user(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        me=bot.get_chat_member(m.chat.id, bot.get_me().id)
        if me.status!="administrator" or not getattr(me,"can_promote_members",False):
            return bot.reply_to(m,"❗ ربات مجوز افزودن مدیر ندارد.")
        bot.promote_chat_member(m.chat.id, m.reply_to_message.from_user.id,
            can_manage_chat=True, can_delete_messages=True,
            can_restrict_members=True, can_pin_messages=True,
            can_invite_users=True, can_manage_video_chats=True,
            can_promote_members=False)
        bot.reply_to(m,"👑 کاربر مدیر شد.")
    except: bot.reply_to(m,"❗ نتوانستم مدیر کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف مدیر")
def demote_user(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        bot.promote_chat_member(m.chat.id, m.reply_to_message.from_user.id,
            can_manage_chat=False, can_delete_messages=False,
            can_restrict_members=False, can_pin_messages=False,
            can_invite_users=False, can_manage_video_chats=False,
            can_promote_members=False)
        bot.reply_to(m,"❌ کاربر از مدیریت حذف شد.")
    except: bot.reply_to(m,"❗ نتوانستم حذف مدیر کنم.")

# ========= پن / حذف پن =========
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="پن")
def pin_msg(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        bot.pin_chat_message(m.chat.id, m.reply_to_message.message_id, disable_notification=True)
        bot.reply_to(m,"📌 پیام پین شد.")
    except: bot.reply_to(m,"❗ نتوانستم پین کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف پن")
def unpin_msg(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    try:
        bot.unpin_chat_message(m.chat.id, m.reply_to_message.message_id)
        bot.reply_to(m,"❌ پین پیام برداشته شد.")
    except: bot.reply_to(m,"❗ نتوانستم حذف پین کنم.")

# ========= لیست مدیران =========
@bot.message_handler(func=lambda m: m.text=="لیست مدیران گروه")
def list_group_admins(m):
    try:
        admins=bot.get_chat_administrators(m.chat.id)
        lines=[f"• {((a.user.first_name or '') + (' ' + a.user.last_name if a.user.last_name else '')).strip() or 'بدون‌نام'} — <code>{a.user.id}</code>" for a in admins]
        bot.reply_to(m,"📋 مدیران گروه:\n"+"\n".join(lines))
    except: bot.reply_to(m,"❗ نتوانستم لیست مدیران را بگیرم.")

@bot.message_handler(func=lambda m: m.text=="لیست مدیران ربات")
def list_bot_admins(m):
    bot.reply_to(m,f"📋 مدیران ربات:\n• سودو: <code>{SUDO_ID}</code>")

# ========= «اصل» (پروفایل/معرفی کاربر) =========
# فقط سودو می‌تواند ذخیره کند؛ سراسری برای همه‌ی گروه‌ها
originals_global = {}  # uid -> text

@bot.message_handler(func=lambda m: m.reply_to_message and m.text and m.text.startswith("ثبت اصل"))
def set_original(m):
    if m.from_user.id != SUDO_ID: return
    txt = m.text.replace("ثبت اصل","",1).strip()
    if not txt: return bot.reply_to(m,"❗ متن معرفی را بعد از «ثبت اصل» بنویس.")
    uid = m.reply_to_message.from_user.id
    originals_global[uid] = txt
    bot.reply_to(m, f"✅ اصل برای <code>{uid}</code> ذخیره شد.")

@bot.message_handler(func=lambda m: m.text=="اصل")
def show_original(m):
    # اگر ریپلای بود، اصلِ همان کاربر را بده؛ وگرنه اصلِ خودِ فرد
    uid = m.reply_to_message.from_user.id if m.reply_to_message else m.from_user.id
    if uid in originals_global:
        bot.reply_to(m, f"🧾 اصل کاربر <code>{uid}</code>:\n{originals_global[uid]}")
    else:
        bot.reply_to(m, "ℹ️ اصل برای این کاربر ثبت نشده.")

# ========= دیتابیس جوک / فال / بیو =========
# فقط سودو اضافه می‌کند (متن یا عکس)، همه می‌توانند با دستور کوتاه بگیرند
jokes_db = []   # لیست آیتم‌ها: {'type':'text'|'photo', 'data': str, 'caption': str}
fortunes_db = []
bios_db = []

def add_item_to_db(m, target_list, label):
    if m.from_user.id != SUDO_ID: return
    if m.content_type == "text":
        target_list.append({'type':'text', 'data': m.text.split(' ',1)[1] if ' ' in m.text else '', 'caption':''})
        bot.reply_to(m, f"✅ {label} متنی ذخیره شد. مجموع: {len(target_list)}")
    elif m.content_type == "photo":
        target_list.append({'type':'photo', 'data': m.photo[-1].file_id, 'caption': m.caption or ''})
        bot.reply_to(m, f"✅ {label} عکسی ذخیره شد. مجموع: {len(target_list)}")
    else:
        bot.reply_to(m, "❗ فقط متن یا عکس پشتیبانی می‌شود.")

@bot.message_handler(content_types=['text','photo'], func=lambda m: m.text and m.text.startswith("ثبت جوک"))
def add_joke(m): add_item_to_db(m, jokes_db, "جوک")

@bot.message_handler(content_types=['text','photo'], func=lambda m: m.text and m.text.startswith("ثبت فال"))
def add_fortune(m): add_item_to_db(m, fortunes_db, "فال")

@bot.message_handler(content_types=['text','photo'], func=lambda m: m.text and m.text.startswith("ثبت بیو"))
def add_bio(m): add_item_to_db(m, bios_db, "بیو")

def send_random_from_db(m, target_list, empty_msg):
    if not target_list:
        return bot.reply_to(m, empty_msg)
    item = random.choice(target_list)
    if item['type'] == 'text':
        bot.reply_to(m, item['data'])
    else:
        try:
            bot.send_photo(m.chat.id, item['data'], caption=item['caption'])
        except:
            bot.reply_to(m, "❗ نتوانستم عکس را ارسال کنم.")

@bot.message_handler(func=lambda m: m.text=="جوک")
def get_joke(m): send_random_from_db(m, jokes_db, "ℹ️ هنوز جوکی ثبت نشده.")

@bot.message_handler(func=lambda m: m.text=="فال")
def get_fortune(m): send_random_from_db(m, fortunes_db, "ℹ️ هنوز فالی ثبت نشده.")

@bot.message_handler(func=lambda m: m.text=="بیو")
def get_bio(m): send_random_from_db(m, bios_db, "ℹ️ هنوز بیویی ثبت نشده.")

# ========= فونت ساده (نمونه) =========
fonts=[lambda t: " ".join(list(t)), lambda t: t.upper(), lambda t: f"★{t}★"]
@bot.message_handler(func=lambda m: m.text and m.text.startswith("فونت"))
def font_cmd(m):
    txt=m.text.replace("فونت","",1).strip()
    if not txt: return bot.reply_to(m,"❗ متنی وارد کن")
    out="\n".join([f"{i+1}- {f(txt)}" for i,f in enumerate(fonts)])
    bot.reply_to(m,"✍️ متن با فونت‌های مختلف:\n"+out)

# ========= پاکسازی =========
@bot.message_handler(func=lambda m: m.text=="پاکسازی")
def clear_50(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    for i in range(m.message_id-1, m.message_id-51, -1):
        try: bot.delete_message(m.chat.id,i)
        except: pass
    bot.reply_to(m,"🧹 ۵۰ پیام پاک شد.")

@bot.message_handler(func=lambda m: m.text in ("پاکسازی 9999","حذف پیام 9999"))
def clear_9999(m):
    if not is_admin(m.chat.id,m.from_user.id): return
    for i in range(m.message_id-1, m.message_id-10000, -1):
        try: bot.delete_message(m.chat.id,i)
        except: pass
    bot.reply_to(m,"🧹 تا ۹۹۹۹ پیام اخیر تلاش شد حذف شود.")

# ========= ارسال همگانی =========
waiting_broadcast={}
@bot.message_handler(func=lambda m: m.from_user.id==SUDO_ID and m.text=="ارسال")
def ask_broadcast(m):
    waiting_broadcast[m.from_user.id]=True
    bot.reply_to(m,"📢 متن یا عکس بعدی‌ات را بفرست تا به همه گروه‌ها ارسال شود.")

@bot.message_handler(func=lambda m: m.from_user.id==SUDO_ID and waiting_broadcast.get(m.from_user.id))
def do_broadcast(m):
    waiting_broadcast[m.from_user.id]=False; sent=0
    for gid in list(joined_groups):
        try:
            if m.content_type=="text": bot.send_message(gid,m.text)
            elif m.content_type=="photo": bot.send_photo(gid,m.photo[-1].file_id,caption=(m.caption or ""))
            sent+=1
        except: pass
    bot.reply_to(m,f"✅ به {sent} گروه ارسال شد.")

# ========= ضد لینک + «ربات» =========
@bot.message_handler(content_types=['text'])
def text_handler(m):
    # فقط اگر سودو بگه "ربات"
    if m.from_user.id==SUDO_ID and m.text.strip()=="ربات":
        return bot.reply_to(m,"جانم سودو 👑")
    # حذف لینک
    if lock_links.get(m.chat.id) and not is_admin(m.chat.id,m.from_user.id):
        if re.search(r"(t\.me|telegram\.me|telegram\.org|https?://)",(m.text or "").lower()):
            try: bot.delete_message(m.chat.id,m.message_id)
            except: pass

# ========= RUN =========
print("🤖 Bot is running...")
bot.infinity_polling()
