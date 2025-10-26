# ======================= 💎 سیستم «اصل» پیشرفته مخصوص هر گروه =======================
import json, os, asyncio
from telegram import Update
from telegram.ext import ContextTypes

ORIGIN_FILE = "origins.json"
SUDO_IDS = [7089376754]  # 👑 آی‌دی سودوها

# 📂 بارگذاری و ذخیره‌سازی
def load_origins():
    if os.path.exists(ORIGIN_FILE):
        try:
            with open(ORIGIN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_origins(data):
    with open(ORIGIN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

origins = load_origins()

# 👑 بررسی مدیر یا سودو بودن
async def is_admin_or_sudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    if user.id in SUDO_IDS:
        return True

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ["administrator", "creator"]
    except:
        return False

# 🧹 وقتی ربات از گروه حذف میشه → داده‌های اون گروه حذف میشه
async def handle_bot_removed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    chat_id = str(chat.id)

    try:
        new_status = update.my_chat_member.new_chat_member.status
        if new_status in ["left", "kicked"]:
            if chat_id in origins:
                del origins[chat_id]
                save_origins(origins)
                print(f"🧹 داده‌های گروه {chat.title or chat_id} حذف شد (ربات از گروه خارج شد)")
    except Exception as e:
        print(f"[handle_bot_removed ERROR] {e}")

# ➕ ثبت اصل (فقط مدیرها و سودوها)
async def handle_set_origin(update, context):
    message = update.message
    user = update.effective_user
    chat_id = str(update.effective_chat.id)

    # فقط مدیران یا سودوها مجازند
    if not await is_admin_or_sudo(update, context):
        return await message.reply_text("🚫 فقط مدیران گروه یا سودوها می‌توانند اصل ثبت کنند!")

    raw_text = message.text.strip()
    origin_text = ""

    # حذف عبارت‌های شروع دستور
    for key in ["ثبت اصل", "set origin", "setorigin"]:
        if raw_text.lower().startswith(key):
            origin_text = raw_text[len(key):].strip()
            break

    # اگر فقط نوشته «ثبت اصل» و ریپلای کرده، متن پیام فرد بشه اصل
    if not origin_text and message.reply_to_message:
        origin_text = message.reply_to_message.text or ""

    if not origin_text:
        msg = await message.reply_text("⚠️ لطفاً متن اصل را بنویس یا روی پیام فردی ریپلای بزن.")
        await asyncio.sleep(10)
        try:
            await msg.delete()
            await message.delete()
        except:
            pass
        return

    target = message.reply_to_message.from_user if message.reply_to_message else user

    # ساخت فضای مخصوص گروه
    if chat_id not in origins:
        origins[chat_id] = {}

    origins[chat_id][str(target.id)] = origin_text
    save_origins(origins)

    # ✨ پیام نهایی زیبا
    if target.id == user.id:
        msg_text = (
            f"💫 اصل شخصی شما با موفقیت ثبت شد ❤️\n\n"
            f"🧿 <b>{origin_text}</b>"
        )
    else:
        msg_text = (
            f"✅ اصل جدید برای <a href='tg://user?id={target.id}'>{target.first_name}</a> ثبت شد 💠\n\n"
            f"🧿 <b>{origin_text}</b>"
        )

    sent = await message.reply_text(msg_text, parse_mode="HTML")
    await asyncio.sleep(10)
    try:
        await sent.delete()
        await message.delete()
    except:
        pass

# 🔍 نمایش اصل (برای همه)
async def handle_show_origin(update, context):
    message = update.message
    text = message.text.strip().lower()
    user = update.effective_user
    chat_id = str(update.effective_chat.id)

    target = None

    # اگر ریپلای کرده → اصل اون فرد رو نشون بده
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif text in ["اصل من", "اصل خودم", "my origin"]:
        target = user
    elif text in ["اصل", "اصلش", "origin"]:
        return

    if not target:
        return

    group_origins = origins.get(chat_id, {})
    origin_text = group_origins.get(str(target.id))

    if origin_text:
        if target.id == user.id:
            await message.reply_text(
                f"🌿 <b>اصل شما:</b>\n{origin_text}",
                parse_mode="HTML"
            )
        else:
            await message.reply_text(
                f"🧿 <b>اصل {target.first_name}:</b>\n{origin_text}",
                parse_mode="HTML"
            )

# ♻️ پاکسازی خودکار گروه‌های غیرفعال (هر ۷ روز)
async def auto_clean_old_origins(context):
    """بررسی خودکار گروه‌ها و حذف داده‌ی گروه‌هایی که ربات ازشون خارج شده"""
    print("🧭 شروع بررسی خودکار داده‌های قدیمی...")

    removed_groups = []
    to_delete = []

    for chat_id in list(origins.keys()):
        try:
            chat = await context.bot.get_chat(chat_id)
            if chat.type not in ["group", "supergroup"]:
                to_delete.append(chat_id)
        except:
            to_delete.append(chat_id)

    for gid in to_delete:
        del origins[gid]
        removed_groups.append(gid)

    if removed_groups:
        save_origins(origins)
        print(f"🧹 {len(removed_groups)} گروه حذف شدند: {', '.join(removed_groups)}")
    else:
        print("✅ همه‌چیز تمیز است، هیچ گروهی برای حذف وجود ندارد.")
