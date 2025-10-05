-- coding: utf-8 --

import telebot
from telebot import types
from datetime import datetime
import re, random

================== تنظیمات ==================

TOKEN   = "7462131830:AAEGzgbjETaf3eukzGHW613i4y61Cs7lzTE"
SUDO_ID = 7089376754  # سودوی ربات (فقط این آیدی همه‌کاره است)
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

============================================

HELP_TEXT = """
📖 لیست دستورات:

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
🚫 بن / ✅ حذف بن (ریپلای)
🔕 سکوت / 🔊 حذف سکوت (ریپلای)
⚠️ اخطار / حذف اخطار (ریپلای)
👑 مدیر / ❌ حذف مدیر (ریپلای)
📌 پن / ❌ حذف پن (ریپلای)
📋 لیست مدیران گروه
📋 لیست مدیران ربات
🎉 خوشامد روشن / خاموش
✍️ خوشامد متن [متن دلخواه]
🖼 ثبت عکس (ریپلای → ثبت عکس)
🧹 پاکسازی (۵۰ پیام) | پاکسازی 9999
✍️ فونت [متن دلخواه]
🧾 ثبت اصل [متن] (فقط سودو - ریپلای) | اصل (ریپلای)
🤣 جوک | 🔮 فال | 🧑‍💼 بیو
➕ ثبت جوک / ثبت فال / ثبت بیو
📢 ارسال (فقط سودو)
🛠 وضعیت ربات
🚪 لفت بده (فقط سودو)
"""

——— ذخیره گروه‌ها برای «ارسال» ———

joined_groups = set()
@bot.my_chat_member_handler()
def track_groups(upd):
try:
chat = upd.chat
if chat and chat.type in ("group","supergroup"):
joined_groups.add(chat.id)
except: pass

——— ادمین‌چک ———

def is_admin(chat_id, user_id):
if user_id == SUDO_ID: return True
try:
st = bot.get_chat_member(chat_id,user_id).status
return st in ("administrator","creator")
except: return False

========= دستورات پایه =========

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

========= وضعیت ربات =========

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

========= خوشامد =========

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

========= قفل‌ها =========

locks={k:{} for k in["links","stickers","bots","tabchi","group","photo","video","gif","file","music","voice","forward"]}

def lock_toggle(cid,typ,state): locks[typ][cid]=state

@bot.message_handler(func=lambda m: m.text in [
"قفل لینک","باز کردن لینک","قفل استیکر","باز کردن استیکر",
"قفل ربات","باز کردن ربات","قفل تبچی","باز کردن تبچی",
"قفل گروه","باز کردن گروه","قفل عکس","باز کردن عکس",
"قفل ویدیو","باز کردن ویدیو","قفل گیف","باز کردن گیف",
"قفل فایل","باز کردن فایل","قفل موزیک","باز کردن موزیک",
"قفل ویس","باز کردن ویس","قفل فوروارد","باز کردن فوروارد"])
def toggle(m):
if not is_admin(m.chat.id,m.from_user.id): return
t=m.text; cid=m.chat.id
msgs = {
"قفل لینک":"🔒 لینک قفل شد.","باز کردن لینک":"🔓 لینک آزاد شد.",
"قفل استیکر":"🧷 استیکر قفل شد.","باز کردن استیکر":"🧷 استیکر آزاد شد.",
"قفل ربات":"🤖 ربات قفل شد.","باز کردن ربات":"🤖 ربات آزاد شد.",
"قفل تبچی":"🚫 تبچی قفل شد.","باز کردن تبچی":"🚫 تبچی آزاد شد.",
"قفل عکس":"🖼 عکس قفل شد.","باز کردن عکس":"🖼 عکس آزاد شد.",
"قفل ویدیو":"🎥 ویدیو قفل شد.","باز کردن ویدیو":"🎥 ویدیو آزاد شد.",
"قفل گیف":"🎭 گیف قفل شد.","باز کردن گیف":"🎭 گیف آزاد شد.",
"قفل فایل":"📎 فایل قفل شد.","باز کردن فایل":"📎 فایل آزاد شد.",
"قفل موزیک":"🎶 موزیک قفل شد.","باز کردن موزیک":"🎶 موزیک آزاد شد.",
"قفل ویس":"🎙 ویس قفل شد.","باز کردن ویس":"🎙 ویس آزاد شد.",
"قفل فوروارد":"🔄 فوروارد قفل شد.","باز کردن فوروارد":"🔄 فوروارد آزاد شد."
}
state = "قفل" in t
key = [k for k in locks if k in t][0]
lock_toggle(cid,key,state)
if t in msgs: bot.reply_to(m,msgs[t])

بلاک مدیا طبق قفل‌ها

@bot.message_handler(content_types=['photo','video','document','audio','voice','sticker'])
def block_media(m):
try:
if locks["photo"].get(m.chat.id)   and m.content_type=="photo":    bot.delete_message(m.chat.id,m.message_id)
if locks["video"].get(m.chat.id)   and m.content_type=="video":    bot.delete_message(m.chat.id,m.message_id)
if locks["file"].get(m.chat.id)    and m.content_type=="document": bot.delete_message(m.chat.id,m.message_id)
if locks["music"].get(m.chat.id)   and m.content_type=="audio":    bot.delete_message(m.chat.id,m.message_id)
if locks["voice"].get(m.chat.id)   and m.content_type=="voice":    bot.delete_message(m.chat.id,m.message_id)
if locks["gif"].get(m.chat.id)     and (m.document and m.document.mime_type=="video/mp4"): bot.delete_message(m.chat.id,m.message_id)
if locks["stickers"].get(m.chat.id) and m.content_type=="sticker": bot.delete_message(m.chat.id,m.message_id)
except: pass

========= بن / سکوت =========

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="بن")
def ban_user(m):
if not is_admin(m.chat.id,m.from_user.id): return
try: bot.ban_chat_member(m.chat.id,m.reply_to_message.from_user.id); bot.reply_to(m,"🚫 کاربر بن شد.")
except: bot.reply_to(m,"❗ نتوانستم بن کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف بن")
def unban_user(m):
if not is_admin(m.chat.id,m.from_user.id): return
try: bot.unban_chat_member(m.chat.id,m.reply_to_message.from_user.id); bot.reply_to(m,"✅ کاربر از بن خارج شد.")
except: bot.reply_to(m,"❗ نتوانستم حذف بن کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="سکوت")
def mute_user(m):
if not is_admin(m.chat.id,m.from_user.id): return
try: bot.restrict_chat_member(m.chat.id,m.reply_to_message.from_user.id,can_send_messages=False); bot.reply_to(m,"🔕 کاربر سکوت شد.")
except: bot.reply_to(m,"❗ نتوانستم سکوت کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف سکوت")
def unmute_user(m):
if not is_admin(m.chat.id,m.from_user.id): return
try:
bot.restrict_chat_member(m.chat.id,m.reply_to_message.from_user.id,
can_send_messages=True, can_send_media_messages=True,
can_send_other_messages=True, can_add_web_page_previews=True)
bot.reply_to(m,"🔊 کاربر از سکوت خارج شد.")
except: bot.reply_to(m,"❗ نتوانستم حذف سکوت کنم.")

========= اخطار =========

warnings={}; MAX_WARNINGS=3
@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="اخطار")
def warn_user(m):
if not is_admin(m.chat.id,m.from_user.id): return
uid=m.reply_to_message.from_user.id
warnings.setdefault(m.chat.id,{})[uid]=warnings[m.chat.id].get(uid,0)+1
count=warnings[m.chat.id][uid]
if count>=MAX_WARNINGS:
try: bot.ban_chat_member(m.chat.id,uid); bot.reply_to(m,"🚫 کاربر با ۳ اخطار بن شد."); warnings[m.chat.id][uid]=0
except: bot.reply_to(m,"❗ نتوانستم بن کنم.")
else: bot.reply_to(m,f"⚠️ اخطار {count}/{MAX_WARNINGS} ثبت شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف اخطار")
def reset_warn(m):
if not is_admin(m.chat.id,m.from_user.id): return
uid=m.reply_to_message.from_user.id
if uid in warnings.get(m.chat.id,{}): warnings[m.chat.id][uid]=0; bot.reply_to(m,f"✅ اخطارهای {uid} حذف شد.")
else: bot.reply_to(m,"ℹ️ اخطاری برای این کاربر ثبت نشده.")

========= مدیر / حذف مدیر =========

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="مدیر")
def promote_user(m):
if not is_admin(m.chat.id,m.from_user.id): return
try:
bot.promote_chat_member(m.chat.id,m.reply_to_message.from_user.id,
can_manage_chat=True,can_delete_messages=True,
can_restrict_members=True,can_pin_messages=True,
can_invite_users=True,can_manage_video_chats=True)
bot.reply_to(m,"👑 کاربر مدیر شد.")
except: bot.reply_to(m,"❗ نتوانستم مدیر کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف مدیر")
def demote_user(m):
if not is_admin(m.chat.id,m.from_user.id): return
try:
bot.promote_chat_member(m.chat.id,m.reply_to_message.from_user.id,
can_manage_chat=False,can_delete_messages=False,
can_restrict_members=False,can_pin_messages=False,
can_invite_users=False,can_manage_video_chats=False)
bot.reply_to(m,"❌ مدیر حذف شد.")
except: bot.reply_to(m,"❗ نتوانستم حذف مدیر کنم.")

========= پن =========

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="پن")
def pin_msg(m):
if not is_admin(m.chat.id,m.from_user.id): return
try: bot.pin_chat_message(m.chat.id,m.reply_to_message.message_id,disable_notification=True); bot.reply_to(m,"📌 پیام پین شد.")
except: bot.reply_to(m,"❗ نتوانستم پین کنم.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text=="حذف پن")
def unpin_msg(m):
if not is_admin(m.chat.id,m.from_user.id): return
try: bot.unpin_chat_message(m.chat.id,m.reply_to_message.message_id); bot.reply_to(m,"❌ پین برداشته شد.")
except: bot.reply_to(m,"❗ نتوانستم حذف پین کنم.")

========= لیست‌ها =========

@bot.message_handler(func=lambda m: m.text=="لیست مدیران گروه")
def list_group_admins(m):
try:
admins=bot.get_chat_administrators(m.chat.id)
lines=[f"• {(a.user.first_name or 'بدون‌نام')} — <code>{a.user.id}</code>" for a in admins]
bot.reply_to(m,"📋 مدیران گروه:\n"+"\n".join(lines))
except: bot.reply_to(m,"❗ نتوانستم لیست مدیران را بگیرم.")

@bot.message_handler(func=lambda m: m.text=="لیست مدیران ربات")
def list_bot_admins(m): bot.reply_to(m,f"📋 مدیران ربات:\n• سودو: <code>{SUDO_ID}</code>")

========= اصل =========

originals_global={}
@bot.message_handler(func=lambda m: m.reply_to_message and m.text and m.text.startswith("ثبت اصل"))
def set_original(m):
if m.from_user.id!=SUDO_ID: return
txt=m.text.replace("ثبت اصل","",1).strip()
if not txt: return bot.reply_to(m,"❗ متن معرفی را بعد از «ثبت اصل» بنویس.")
uid=m.reply_to_message.from_user.id; originals_global[uid]=txt
bot.reply_to(m,f"✅ اصل برای {uid} ذخیره شد.")

@bot.message_handler(func=lambda m: m.text=="اصل")
def show_original(m):
uid=m.reply_to_message.from_user.id if m.reply_to_message else m.from_user.id
if uid in originals_global: bot.reply_to(m,f"🧾 اصل کاربر {uid}:\n{originals_global[uid]}")
else: bot.reply_to(m,"ℹ️ اصل برای این کاربر ثبت نشده.")

========= جوک / فال / بیو =========

jokes_db, fortunes_db, bios_db = [], [], []
def add_item_to_db(m,target_list,label,keyword):
if m.from_user.id!=SUDO_ID: return
if m.content_type=="text":
txt=m.text.replace(keyword,"",1).strip()
if not txt: return bot.reply_to(m,f"❗ بعد از «{keyword}» متن بنویس.")
target_list.append({'type':'text','data':txt,'caption':''})
bot.reply_to(m,f"✅ {label} متنی ذخیره شد. مجموع: {len(target_list)}")
elif m.content_type=="photo":
target_list.append({'type':'photo','data':m.photo[-1].file_id,'caption':m.caption or ''})
bot.reply_to(m,f"✅ {label} عکسی ذخیره شد. مجموع: {len(target_list)}")

@bot.message_handler(content_types=['text','photo'], func=lambda m:m.text and m.text.startswith("ثبت جوک"))
def add_joke(m): add_item_to_db(m,jokes_db,"جوک","ثبت جوک")
@bot.message_handler(content_types=['text','photo'], func=lambda m:m.text and m.text.startswith("ثبت فال"))
def add_fortune(m): add_item_to_db(m,fortunes_db,"فال","ثبت فال")
@bot.message_handler(content_types=['text','photo'], func=lambda m:m.text and m.text.startswith("ثبت بیو"))
def add_bio(m): add_item_to_db(m,bios_db,"بیو","ثبت بیو")

def send_random_from_db(m,target_list,empty_msg):
if not target_list: return bot.reply_to(m,empty_msg)
item=random.choice(target_list)
if item['type']=="text": bot.reply_to(m,item['data'])
else: bot.send_photo(m.chat.id,item['data'],caption=item['caption'])

@bot.message_handler(func=lambda m:m.text=="جوک")
def get_joke(m): send_random_from_db(m,jokes_db,"ℹ️ هنوز جوکی ثبت نشده.")
@bot.message_handler(func=lambda m:m.text=="فال")
def get_fortune(m): send_random_from_db(m,fortunes_db,"ℹ️ هنوز فالی ثبت نشده.")
@bot.message_handler(func=lambda m:m.text=="بیو")
def get_bio(m): send_random_from_db(m,bios_db,"ℹ️ هنوز بیویی ثبت نشده.")

========= فونت =========

def spaced(t): return " ".join(list(t))
def heart(t): return f"💖 {t} 💖"
def danger(t): return f"☠️ {t.upper()} ☠️"
def strike(t): return ''.join([c+'̶' for c in t])
def underline(t): return ''.join([c+'̲' for c in t])
fonts=[spaced,lambda t:t.upper(),lambda t:f"★ {t} ★",heart,danger,strike,underline]

@bot.message_handler(func=lambda m:m.text and m.text.startswith("فونت"))
def font_cmd(m):
txt=m.text.replace("فونت","",1).strip()
if not txt: return bot.reply_to(m,"❗ متنی وارد کن")
out="\n".join([f"{i+1}- {f(txt)}" for i,f in enumerate(fonts)])
bot.reply_to(m,"✍️ متن با فونت‌های مختلف:\n"+out)

========= پاکسازی =========

@bot.message_handler(func=lambda m: m.text=="پاکسازی")
def clear_50(m):
if not is_admin(m.chat.id,m.from_user.id): return
for i in range(m.message_id-1,m.message_id-51,-1):
try: bot.delete_message(m.chat.id,i)
except: pass
bot.reply_to(m,"🧹 ۵۰ پیام پاک شد.")

@bot.message_handler(func=lambda m: m.text in ("پاکسازی 9999","حذف پیام 9999"))
def clear_9999(m):
if not is_admin(m.chat.id,m.from_user.id): return
for i in range(m.message_id-1,m.message_id-10000,-1):
try: bot.delete_message(m.chat.id,i)
except: pass
bot.reply_to(m,"🧹 تا ۹۹۹۹ پیام اخیر حذف شد.")

========= ارسال همگانی =========

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

========= ضد لینک + سودو =========

@bot.message_handler(content_types=['text'])
def text_handler(m):
if m.from_user.id==SUDO_ID and m.text.strip()=="ربات": return bot.reply_to(m,"جانم سودو 👑")
if locks["links"].get(m.chat.id) and not is_admin(m.chat.id,m.from_user.id):
if re.search(r"(t.me|http)",(m.text or "").lower()):
try: bot.delete_message(m.chat.id,m.message_id)
except: pass

========= RUN =========

print("🤖 Bot is running...")
bot.infinity_polling()
