# ======================= ⚙️ سیستم مدیریت گروه (نسخه نهایی کامل و پایدار) =======================

import json, os, re
from datetime import datetime
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes

# 🔧 فایل‌های ذخیره
GROUP_CTRL_FILE = "group_control.json"
ALIASES_FILE = "aliases.json"
FILTER_FILE = "filters.json"

# 👑 سودوها
SUDO_IDS = [123456789, 7089376754]  # آی‌دی‌های مجاز

# ✅ alias پیش‌فرض
ALIASES = {
    "ban": ["ban", "بن", "اخراج"],
    "unban": ["unban", "آزاد", "رفع‌بن"],
    "warn": ["warn", "اخطار", "هشدار"],
    "unwarn": ["unwarn", "پاک‌اخطار", "حذف‌اخطار"],
    "mute": ["mute", "سکوت", "خفه"],
    "unmute": ["unmute", "آزادسکوت", "رفع‌سکوت"],
    "lockgroup": ["lockgroup", "قفل‌گروه", "قفل گروه"],
    "unlockgroup": ["unlockgroup", "بازگروه", "باز گروه"],
    "alias": ["alias", "تغییر"]
}

# 📂 بارگذاری / ذخیره فایل‌ها
def load_json_file(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return default

def save_json_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

group_data = load_json_file(GROUP_CTRL_FILE, {})
ALIASES = load_json_file(ALIASES_FILE, ALIASES)

# 🧠 بررسی مجاز بودن
async def is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if user.id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ["administrator", "creator"]
    except:
        return False

# 🧱 بررسی هدف
async def can_act_on_target(update, context, target):
    bot = await context.bot.get_me()
    chat = update.effective_chat

    if target.id == bot.id:
        await update.message.reply_text("😎 نمی‌تونی روی من کاری انجام بدی!")
        return False

    if target.id in SUDO_IDS:
        await update.message.reply_text("⚠️ این کاربر از مدیران ارشد است.")
        return False

    try:
        member = await context.bot.get_chat_member(chat.id, target.id)
        if member.status in ["administrator", "creator"]:
            await update.message.reply_text("⚠️ نمی‌تونی روی مدیر گروه کاری انجام بدی!")
            return False
    except:
        pass
    return True

# 🚫 بن / رفع بن
async def handle_ban(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران مجازند.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید روی پیام کاربر ریپلای بزنی.")
    target = update.message.reply_to_message.from_user
    if not await can_act_on_target(update, context, target):
        return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(f"🚫 <b>{target.first_name}</b> بن شد.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا: {e}")

async def handle_unban(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران مجازند.")
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
    elif context.args:
        user_id = int(context.args[0])
    else:
        return await update.message.reply_text("🔹 باید ریپلای بزنی یا آیدی بدی.")
    try:
        await context.bot.unban_chat_member(update.effective_chat.id, user_id)
        await update.message.reply_text("✅ رفع بن انجام شد.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا: {e}")

# ⚠️ اخطار (۳ اخطار = بن)
async def handle_warn(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران مجازند.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید ریپلای بزنی.")
    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)
    if not await can_act_on_target(update, context, target):
        return
    group = group_data.get(chat_id, {"warns": {}})
    warns = group["warns"]
    warns[str(target.id)] = warns.get(str(target.id), 0) + 1
    count = warns[str(target.id)]
    group["warns"] = warns
    group_data[chat_id] = group
    save_json_file(GROUP_CTRL_FILE, group_data)
    if count >= 3:
        await context.bot.ban_chat_member(chat_id, target.id)
        await update.message.reply_text(f"🚫 {target.first_name} سه اخطار گرفت و بن شد!")
        warns[str(target.id)] = 0
    else:
        await update.message.reply_text(f"⚠️ اخطار شماره {count} برای {target.first_name}")

# 🤐 سکوت / رفع سکوت
async def handle_mute(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران مجازند.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید ریپلای بزنی.")
    target = update.message.reply_to_message.from_user
    if not await can_act_on_target(update, context, target):
        return
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id, target.id, permissions=ChatPermissions(can_send_messages=False))
        await update.message.reply_text(f"🤐 {target.first_name} ساکت شد.")
    except:
        await update.message.reply_text("⚠️ خطا در سکوت کاربر.")

async def handle_unmute(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران مجازند.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("🔹 باید ریپلای بزنی.")
    target = update.message.reply_to_message.from_user
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id, target.id, permissions=ChatPermissions(can_send_messages=True))
        await update.message.reply_text(f"🔊 {target.first_name} از سکوت خارج شد.")
    except:
        await update.message.reply_text("⚠️ خطا در رفع سکوت.")

# 🔒 قفل گروه کامل
async def handle_lockgroup(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران می‌توانند قفل کنند!")
    await context.bot.set_chat_permissions(update.effective_chat.id, ChatPermissions(can_send_messages=False))
    await update.message.reply_text("🔒 گروه قفل شد. فقط مدیران می‌توانند پیام دهند.")

async def handle_unlockgroup(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران می‌توانند باز کنند!")
    await context.bot.set_chat_permissions(update.effective_chat.id, ChatPermissions(can_send_messages=True))
    await update.message.reply_text("🔓 گروه باز شد. همه می‌توانند پیام دهند.")

# 🧩 تغییر alias‌ها
async def handle_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update, context):
        return await update.message.reply_text("⛔ فقط مدیران یا سودوها می‌توانند alias را تغییر دهند!")
    text = update.message.text.strip()
    if " " not in text or "=" not in text:
        return await update.message.reply_text(
            "📝 استفاده:\n<code>alias [alias]=[command]</code>\nمثلاً:\n<code>alias بن=ban</code>",
            parse_mode="HTML"
        )
    _, alias_part = text.split(" ", 1)
    if "=" not in alias_part:
        return await update.message.reply_text("⚠️ فرمت اشتباه است! باید از '=' استفاده شود.", parse_mode="HTML")
    alias_word, command_name = [p.strip().lower() for p in alias_part.split("=", 1)]
    if command_name not in ALIASES:
        return await update.message.reply_text(f"⚠️ دستور <b>{command_name}</b> وجود ندارد.", parse_mode="HTML")
    if alias_word in ALIASES[command_name]:
        return await update.message.reply_text("ℹ️ این alias از قبل وجود دارد.", parse_mode="HTML")
    ALIASES[command_name].append(alias_word)
    save_json_file(ALIASES_FILE, ALIASES)
    await update.message.reply_text(f"✅ alias جدید ثبت شد:\n<code>{alias_word}</code> → <b>{command_name}</b>", parse_mode="HTML")

# ======================= 🔒 قفل‌های پیشرفته پیام =======================
LOCK_TYPES = {
    "links": "ارسال لینک‌ها",
    "photos": "ارسال عکس",
    "videos": "ارسال ویدیو",
    "files": "ارسال فایل",
    "stickers": "ارسال استیکر",
    "voices": "ارسال ویس",
    "chat": "ارسال پیام متنی",
}

def set_lock(chat_id, lock_name, status):
    chat_id = str(chat_id)
    group = group_data.get(chat_id, {"locks": {}})
    group["locks"][lock_name] = status
    group_data[chat_id] = group
    save_json_file(GROUP_CTRL_FILE, group_data)

def get_lock(chat_id, lock_name):
    chat_id = str(chat_id)
    return group_data.get(chat_id, {}).get("locks", {}).get(lock_name, False)

async def handle_lock_generic(update, context, lock_name):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران می‌توانند قفل کنند!")
    set_lock(update.effective_chat.id, lock_name, True)
    await update.message.reply_text(f"🔒 {LOCK_TYPES[lock_name]} قفل شد!")

async def handle_unlock_generic(update, context, lock_name):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران می‌توانند باز کنند!")
    set_lock(update.effective_chat.id, lock_name, False)
    await update.message.reply_text(f"🔓 {LOCK_TYPES[lock_name]} باز شد!")

# 🧹 بررسی و حذف پیام‌های خلاف قفل‌ها
async def check_message_locks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    text = update.message.text.lower() if update.message.text else ""
    chat_id = str(update.effective_chat.id)
    locks = group_data.get(chat_id, {}).get("locks", {})
    if locks.get("links") and ("http" in text or "t.me/" in text):
        await update.message.delete()
    elif locks.get("photos") and update.message.photo:
        await update.message.delete()
    elif locks.get("videos") and update.message.video:
        await update.message.delete()
    elif locks.get("files") and update.message.document:
        await update.message.delete()
    elif locks.get("stickers") and update.message.sticker:
        await update.message.delete()
    elif locks.get("voices") and update.message.voice:
        await update.message.delete()
    elif locks.get("chat") and update.message.text:
        await update.message.delete()

# 🧾 وضعیت قفل‌ها
async def handle_locks_status(update, context):
    chat_id = str(update.effective_chat.id)
    locks = group_data.get(chat_id, {}).get("locks", {})
    if not locks:
        return await update.message.reply_text("🔓 هیچ قفلی فعال نیست.")
    text = "🧱 <b>وضعیت قفل‌های گروه:</b>\n"
    for l, d in LOCK_TYPES.items():
        status = "🔒 فعال" if locks.get(l) else "🔓 غیرفعال"
        text += f"▫️ {d}: {status}\n"
    await update.message.reply_text(text, parse_mode="HTML")

# 🎮 هندلر دستورات اصلی
async def group_command_handler(update, context):
    text = update.message.text.strip().lower()
    if text.startswith("alias "):
        return await handle_alias(update, context)
    if text in ["lockgroup", "قفل گروه"]:
        return await handle_lockgroup(update, context)
    if text in ["unlockgroup", "باز گروه"]:
        return await handle_unlockgroup(update, context)
    if text in ["locks", "وضعیت قفل"]:
        return await handle_locks_status(update, context)

    for cmd, aliases in ALIASES.items():
        if text in aliases:
            for lock in LOCK_TYPES:
                if cmd == f"lock_{lock}":
                    return await handle_lock_generic(update, context, lock)
                elif cmd == f"unlock_{lock}":
                    return await handle_unlock_generic(update, context, lock)
            handlers = {
                "ban": handle_ban,
                "unban": handle_unban,
                "warn": handle_warn,
                "mute": handle_mute,
                "unmute": handle_unmute,
            }
            if cmd in handlers:
                return await handlers[cmd](update, context)

# ======================= 🧠 فیلتر و تگ کاربران =======================
TAG_LIMIT = 5
filters_data = load_json_file(FILTER_FILE, {})

async def handle_addfilter(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران مجازند.")
    if len(context.args) < 1:
        return await update.message.reply_text("📝 استفاده: addfilter [کلمه]")
    word = " ".join(context.args).lower()
    chat_id = str(update.effective_chat.id)
    chat_filters = filters_data.get(chat_id, [])
    if word in chat_filters:
        return await update.message.reply_text("⚠️ از قبل فیلتر شده.")
    chat_filters.append(word)
    filters_data[chat_id] = chat_filters
    save_json_file(FILTER_FILE, filters_data)
    await update.message.reply_text(f"✅ '{word}' فیلتر شد.")

async def handle_delfilter(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران مجازند.")
    if len(context.args) < 1:
        return await update.message.reply_text("📝 استفاده: delfilter [کلمه]")
    word = " ".join(context.args).lower()
    chat_id = str(update.effective_chat.id)
    chat_filters = filters_data.get(chat_id, [])
    if word not in chat_filters:
        return await update.message.reply_text("⚠️ این کلمه در فیلتر نیست.")
    chat_filters.remove(word)
    filters_data[chat_id] = chat_filters
    save_json_file(FILTER_FILE, filters_data)
    await update.message.reply_text(f"🗑️ '{word}' از فیلتر حذف شد.")

async def handle_filters(update, context):
    chat_id = str(update.effective_chat.id)
    chat_filters = filters_data.get(chat_id, [])
    if not chat_filters:
        return await update.message.reply_text("ℹ️ فیلترها خالی است.")
    text = "🚫 <b>لیست فیلترها:</b>\n" + "\n".join(chat_filters)
    await update.message.reply_text(text, parse_mode="HTML")

async def handle_tagall(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران مجازند.")
    chat = update.effective_chat
    args_text = " ".join(context.args)
    await update.message.reply_text("📣 درحال منشن اعضا...", parse_mode="HTML")
    members = []
    async for member in context.bot.get_chat_administrators(chat.id):
        if not member.user.is_bot:
            members.append(member.user)
    batch = []
    for i, user in enumerate(members, start=1):
        batch.append(f"[{user.first_name}](tg://user?id={user.id})")
        if i % TAG_LIMIT == 0:
            await context.bot.send_message(chat.id, " ".join(batch), parse_mode="Markdown")
            batch = []
    if batch:
        await context.bot.send_message(chat.id, " ".join(batch), parse_mode="Markdown")
    await update.message.reply_text("✅ تگ همه انجام شد.", parse_mode="HTML")

async def handle_tagactive(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران مجازند.")
    chat = update.effective_chat
    args_text = " ".join(context.args)
    await update.message.reply_text("👥 درحال تگ کاربران فعال...", parse_mode="HTML")
    members = []
    async for member in context.bot.get_chat_administrators(chat.id):
        if not member.user.is_bot and member.user.is_premium:
            members.append(member.user)
    if not members:
        return await update.message.reply_text("ℹ️ کاربر
                                               if not members:
        return await update.message.reply_text("ℹ️ کاربر فعالی یافت نشد.")

    batch = []
    for i, user in enumerate(members, start=1):
        batch.append(f"[{user.first_name}](tg://user?id={user.id})")
        if i % TAG_LIMIT == 0:
            await context.bot.send_message(chat.id, " ".join(batch), parse_mode="Markdown")
            batch = []
    if batch:
        await context.bot.send_message(chat.id, " ".join(batch), parse_mode="Markdown")
    await update.message.reply_text("✅ تگ کاربران فعال انجام شد.", parse_mode="HTML")


# ======================= 🧠 هندلر کلی alias پیشرفته =======================

ALIASES_ADV = {
    "addfilter": ["addfilter", "افزودن‌فیلتر", "فیلترکن"],
    "delfilter": ["delfilter", "حذف‌فیلتر", "پاک‌فیلتر"],
    "filters": ["filters", "لیست‌فیلتر", "فیلترها"],
    "tagall": ["tagall", "تگ‌همه", "منشن‌همگانی"],
    "tagactive": ["tagactive", "تگ‌فعال", "تگ‌آنلاین"]
}

async def group_text_handler_adv(update, context):
    text = update.message.text.strip().lower()
    for cmd, aliases in ALIASES_ADV.items():
        for alias in aliases:
            if text.startswith(alias):
                context.args = text.replace(alias, "").strip().split()
                handlers = {
                    "addfilter": handle_addfilter,
                    "delfilter": handle_delfilter,
                    "filters": handle_filters,
                    "tagall": handle_tagall,
                    "tagactive": handle_tagactive
                }
                if cmd in handlers:
                    return await handlers[cmd](update, context)
