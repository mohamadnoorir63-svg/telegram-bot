import json, os, asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# 📂 مسیر دیتابیس اعضا
MEMBERS_FILE = "data/members.json"
if not os.path.exists("data"):
    os.makedirs("data")
if not os.path.exists(MEMBERS_FILE):
    with open(MEMBERS_FILE, "w") as f:
        json.dump({}, f)

# 🧠 بارگذاری و ذخیره اعضا
def load_members():
    try:
        with open(MEMBERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_members(data):
    with open(MEMBERS_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# 🧩 ذخیره هر کاربر که پیام میده
async def save_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user:
        return
    user = update.message.from_user
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        return

    members = load_members()
    cid = str(chat.id)
    if cid not in members:
        members[cid] = {}

    members[cid][str(user.id)] = user.first_name
    save_members(members)

# 📋 نمایش منوی تگ
async def handle_tag_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👥 تگ همه اعضا", callback_data="tag_all")],
        [InlineKeyboardButton("👑 تگ مدیران", callback_data="tag_admins")],
        [InlineKeyboardButton("🔥 تگ 50 نفر اخیر", callback_data="tag_50")],
        [InlineKeyboardButton("❌ بستن", callback_data="tag_close")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📣 حالت تگ کردن را انتخاب کنید:", reply_markup=markup)

# ⚙️ اجرای تگ‌ها
async def tag_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat = update.effective_chat
    cid = str(chat.id)

    data = load_members()
    users = data.get(cid, {})

    if query.data == "tag_close":
        return await query.edit_message_text("❌ منوی تگ بسته شد.")

    if query.data == "tag_admins":
        admins = await context.bot.get_chat_administrators(chat.id)
        targets = {str(a.user.id): a.user.first_name for a in admins if not a.user.is_bot}
        title = "مدیران گروه"
    elif query.data == "tag_all":
        targets = {uid: name for uid, name in users.items()}
        title = "همه اعضا"
    elif query.data == "tag_50":
        targets = dict(list(users.items())[-50:])
        title = "۵۰ نفر اخیر"
    else:
        targets = {}
        title = "اعضا"

    if not targets:
        return await query.edit_message_text("⚠️ هیچ کاربری برای تگ وجود ندارد.")

    await query.edit_message_text(f"📢 شروع تگ {title} ...")

    batch, count = [], 0
    for i, (uid, name) in enumerate(targets.items(), 1):
        tag = f"<a href='tg://user?id={uid}'>{name}</a>"
        batch.append(tag)
        if len(batch) >= 5 or i == len(targets):
            try:
                await context.bot.send_message(chat.id, " ".join(batch), parse_mode="HTML")
                batch = []
                count += 1
                await asyncio.sleep(1)
            except Exception as e:
                print("❌ خطا در ارسال:", e)

    await context.bot.send_message(chat.id, f"✅ {count*5} کاربر {title} تگ شدند.", parse_mode="HTML")
