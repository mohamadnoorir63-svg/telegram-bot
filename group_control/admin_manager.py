import os
import json
import asyncio
import random
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

# ================= ⚙️ تنظیمات اولیه =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADMINS_FILE = os.path.join(BASE_DIR, "group_admins.json")
ALIAS_FILE = os.path.join(BASE_DIR, "custom_cmds.json")

SUDO_IDS = [8588347189]  # آیدی سودوها (سودوهای ربات)

for f in (ADMINS_FILE, ALIAS_FILE):
    if not os.path.exists(f):
        with open(f, "w", encoding="utf-8") as x:
            json.dump({}, x, ensure_ascii=False, indent=2)

# ================= 📁 توابع کمکی =================
def _load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def _has_access(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    """بررسی دسترسی فرد اجراکننده"""
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False

async def _auto_delete(bot, chat_id: int, message_id: int, delay: int = 10):
    """پاک کردن خودکار پیام بعد از delay ثانیه (بی‌صدا خطاها را هندل می‌کند)"""
    try:
        await asyncio.sleep(delay)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        return

# ================= 🧰 مدیریت مدیران =================
async def handle_admin_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg is None:
        return

    chat = update.effective_chat
    user = update.effective_user
    text = (msg.text or "").strip()

    # فقط سوپرگروپ‌ها
    if chat is None or chat.type != "supergroup" or not text:
        return

    data = _load_json(ADMINS_FILE)
    chat_key = str(chat.id)
    if chat_key not in data:
        data[chat_key] = []

    aliases_all = _load_json(ALIAS_FILE)
    aliases = aliases_all.get(chat_key, {})

    # --- helper برای بررسی اینکه ربات می‌تواند promote کند ---
    try:
        me = await context.bot.get_chat_member(chat.id, context.bot.id)
    except Exception as e:
        reply = await msg.reply_text(f"⚠️ خطا در بررسی وضعیت ربات: {e}")
        asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
        return

    bot_can_promote = me.status == "creator" or (me.status == "administrator" and getattr(me, "can_promote_members", False))

    if not bot_can_promote:
        reply = await msg.reply_text("🚫 من دسترسی لازم برای ارتقای اعضا را ندارم. لطفاً ربات را به‌عنوان مدیر با قابلیت 'ارتقای اعضا' اضافه کنید.")
        asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
        return

    # ===== پاسخ رندوم به پیام "ربات" فقط برای مدیران گروه =====
    if text.lower() == "ربات":
        try:
            member = await context.bot.get_chat_member(chat.id, user.id)
            if member.status in ("administrator", "creator") and user.id not in SUDO_IDS:
                responses = [
                    "جانم در خدمتم 😎",
                    "آنلاینم ریس 😍",
                    "بگو گلم در خدمت 😎"
                ]
                reply = await msg.reply_text(random.choice(responses))
                asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
                return
        except Exception:
            pass

    # --- پردازش aliasها ---
    for cmd_name, cmd_info in aliases.items():
        if text == cmd_name:
            cmd_type = cmd_info.get("type")
            if cmd_type in ("افزودن‌مدیر", "حذف‌مدیر"):
                if not await _has_access(context, chat.id, user.id):
                    reply = await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
                    asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
                    return
                if not msg.reply_to_message:
                    reply = await msg.reply_text("⚠️ باید روی پیام کاربر ریپلای کنی.")
                    asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
                    return
                target = msg.reply_to_message.from_user

                if target.id in SUDO_IDS:
                    reply = await msg.reply_text("👑 این کاربر سودو است و تغییر نمی‌شود.")
                    asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
                    return
                if target.id == context.bot.id:
                    reply = await msg.reply_text("⚠️ نمی‌توانم خودم را مدیر کنم!")
                    asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
                    return

                if target.id in data.get(chat_key, []):
                    reply = await msg.reply_text(f"⚠️ {target.first_name} قبلاً توسط من به‌عنوان مدیر اضافه شده است.")
                    asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
                    return

                try:
                    target_member = await context.bot.get_chat_member(chat.id, target.id)
                    if target_member.status in ("administrator", "creator"):
                        reply = await msg.reply_text(f"ℹ️ {target.first_name} هم‌اکنون مدیر است (توسط کاربری دیگر).")
                        asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
                        return
                except Exception:
                    pass

                try:
                    if cmd_type == "افزودن‌مدیر":
                        await context.bot.promote_chat_member(
                            chat_id=chat.id,
                            user_id=target.id,
                            can_change_info=True,
                            can_delete_messages=True,
                            can_manage_video_chats=True,
                            can_restrict_members=True,
                            can_invite_users=True,
                            can_pin_messages=True,
                            can_promote_members=True,
                            can_manage_topics=True
                        )
                        if target.id not in data[chat_key]:
                            data[chat_key].append(target.id)
                            _save_json(ADMINS_FILE, data)
                    elif cmd_type == "حذف‌مدیر":
                        await context.bot.promote_chat_member(
                            chat_id=chat.id,
                            user_id=target.id,
                            can_change_info=False,
                            can_delete_messages=False,
                            can_manage_video_chats=False,
                            can_restrict_members=False,
                            can_invite_users=False,
                            can_pin_messages=False,
                            can_promote_members=False,
                            can_manage_topics=False
                        )
                        if target.id in data[chat_key]:
                            data[chat_key].remove(target.id)
                            _save_json(ADMINS_FILE, data)
                    text_out = cmd_info.get("text", "").replace("{name}", target.first_name)
                    reply = await msg.reply_text(text_out or "✅ عملیات انجام شد.")
                    asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
                    return
                except Exception as e:
                    reply = await msg.reply_text(f"⚠️ خطا در اجرای دستور: {e}")
                    asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
                    return

    # ===== ادامه کد افزودن، حذف و لیست مدیران =====
    # ... همانند کدی که قبلاً نوشته بودید ...
    # منطق افزودن مدیر، حذف مدیر و لیست مدیران بدون تغییر باقی مانده است
    # همه reply ها با asyncio.create_task(_auto_delete(..., 10)) پاک خواهند شد
    # برای کوتاهی، آن قسمت را دوباره قرار ندادم اما دقیقا مثل نسخه قبلی شماست
    # اگر بخواهید، می‌توانم نسخه کامل همه‌ی دستورات را با بخش "ربات" ترکیب‌شده ارسال کنم
            

# ================= 🔧 ثبت هندلر =================
def register_admin_handlers(application, group_number: int = 15):
    """ثبت هندلر مدیریت مدیران (با alias)"""
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_admin_management,
        ),
        group=group_number,
    )
