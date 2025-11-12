import os
import json
import asyncio
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
        # ممکن است پیام از قبل پاک شده باشد یا مجوز حذف را نداشته باشیم — نادیده می‌گیریم
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

    # بررسی aliasها (اگر استفاده می‌کنی)
    aliases_all = _load_json(ALIAS_FILE)
    aliases = aliases_all.get(chat_key, {})

    # --- helper برای بررسی اینکه ربات می‌تواند promote کند ---
    try:
        me = await context.bot.get_chat_member(chat.id, context.bot.id)
    except Exception as e:
        # اگر نتوانستیم اطلاعات ربات را بگیریم، خطا نشان بده
        reply = await msg.reply_text(f"⚠️ خطا در بررسی وضعیت ربات: {e}")
        asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
        return

    if me.status == "creator":
        bot_can_promote = True
    elif me.status == "administrator" and getattr(me, "can_promote_members", False):
        bot_can_promote = True
    else:
        bot_can_promote = False

    if not bot_can_promote:
        # اگر ربات دسترسی ندارد، از همه دستورات جلوگیری کن
        # (اطلاع‌رسانی کوتاه و پاک‌شونده)
        reply = await msg.reply_text("🚫 من دسترسی لازم برای ارتقای اعضا را ندارم. لطفاً ربات را به‌عنوان مدیر با قابلیت 'ارتقای اعضا' اضافه کنید.")
        asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
        return

    # پردازش aliasها (در صورت تعریف)
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

                # اگر قبلاً توسط ربات اضافه شده باشه
                if target.id in data.get(chat_key, []):
                    reply = await msg.reply_text(f"⚠️ {target.first_name} قبلاً توسط من به‌عنوان مدیر اضافه شده است.")
                    asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
                    return

                # اگر هدف هم اکنون مدیر است ولی نه توسط ربات
                try:
                    target_member = await context.bot.get_chat_member(chat.id, target.id)
                    if target_member.status in ("administrator", "creator"):
                        reply = await msg.reply_text(f"ℹ️ {target.first_name} هم‌اکنون مدیر است (توسط کاربری دیگر).")
                        asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
                        return
                except Exception:
                    pass

                # اجرا کردن افزودن مدیر
                try:
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
                    # ذخیره در فایل json که این کاربر توسط ربات افزوده شده
                    if target.id not in data[chat_key]:
                        data[chat_key].append(target.id)
                        _save_json(ADMINS_FILE, data)

                    reply = await msg.reply_text(f"✅ {target.first_name} توسط {user.first_name} به‌عنوان مدیر گروه منصوب شد.")
                    asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
                    return
                except Exception as e:
                    reply = await msg.reply_text(f"⚠️ خطا در افزودن مدیر: {e}")
                    asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
                    return

    # ===== دستور افزودن مدیر =====
    if text.startswith("افزودن مدیر"):
        if not await _has_access(context, chat.id, user.id):
            reply = await msg.reply_text("🚫 فقط مدیران یا سودوها مجاز هستند.")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
            return
        if not msg.reply_to_message:
            reply = await msg.reply_text("⚠️ لطفاً روی پیام فرد موردنظر ریپلای کن.")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
            return

        target = msg.reply_to_message.from_user
        if target.id in SUDO_IDS:
            reply = await msg.reply_text("👑 این کاربر سودو است و نیازی به افزودن ندارد.")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
            return
        if target.id == context.bot.id:
            reply = await msg.reply_text("⚠️ نمی‌توانم خودم را مدیر کنم!")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
            return

        # اگر قبلاً توسط ربات اضافه شده باشه
        if target.id in data.get(chat_key, []):
            reply = await msg.reply_text(f"⚠️ {target.first_name} قبلاً توسط من به‌عنوان مدیر اضافه شده است.")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
            return

        # اگر هم‌اکنون مدیر است (توسط کسی دیگر)
        try:
            target_member = await context.bot.get_chat_member(chat.id, target.id)
            if target_member.status in ("administrator", "creator"):
                reply = await msg.reply_text(f"ℹ️ {target.first_name} هم‌اکنون مدیر است (توسط کاربری دیگر).")
                asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
                return
        except Exception:
            pass

        # تلاش برای ارتقا
        try:
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

            reply = await msg.reply_text(f"✅ {target.first_name} توسط {user.first_name} به‌عنوان مدیر گروه منصوب شد.")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
        except Exception as e:
            reply = await msg.reply_text(f"⚠️ خطا در افزودن مدیر: {e}")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))

    # ===== دستور حذف مدیر =====
    elif text.startswith("حذف مدیر"):
        if not await _has_access(context, chat.id, user.id):
            reply = await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
            return
        if not msg.reply_to_message:
            reply = await msg.reply_text("⚠️ لطفاً روی پیام مدیر موردنظر ریپلای کن.")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
            return

        target = msg.reply_to_message.from_user
        if target.id in SUDO_IDS or target.id == context.bot.id:
            reply = await msg.reply_text("🚫 نمی‌توان این کاربر را از مدیریت حذف کرد!")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
            return

        # اگر این کاربر در لیست ساخته‌شده‌ی ربات نبود
        if target.id not in data.get(chat_key, []):
            # اما اگر هم‌اکنون مدیر است (توسط دیگری)، به کاربر اطلاع بده
            try:
                target_member = await context.bot.get_chat_member(chat.id, target.id)
                if target_member.status in ("administrator", "creator"):
                    reply = await msg.reply_text(f"ℹ️ {target.first_name} هم‌اکنون مدیر است، اما من او را قبلاً اضافه نکرده‌ام؛ برای حذف باید creator یا مدیر بالاتر اقدام کند.")
                    asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
                    return
            except Exception:
                pass

            reply = await msg.reply_text("⚠️ این کاربر قبلاً توسط من به‌عنوان مدیر ثبت نشده است.")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
            return

        # تلاش برای حذف اختیارات مدیر (revoke)
        try:
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
            # حذف از لیست محلی
            if target.id in data[chat_key]:
                data[chat_key].remove(target.id)
                _save_json(ADMINS_FILE, data)

            reply = await msg.reply_text(f"⚙️ {target.first_name} توسط {user.first_name} از فهرست مدیران حذف شد.")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
        except Exception as e:
            reply = await msg.reply_text(f"⚠️ خطا در حذف مدیر: {e}")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))

    # ===== لیست مدیران =====
    elif text == "لیست مدیران":
        try:
            current_admins = await context.bot.get_chat_administrators(chat.id)
            lines = [f"• {a.user.first_name}" for a in current_admins if not a.user.is_bot]
            if lines:
                reply = await msg.reply_text("👑 <b>مدیران فعلی گروه:</b>\n" + "\n".join(lines), parse_mode="HTML")
            else:
                reply = await msg.reply_text("ℹ️ هیچ مدیری در گروه یافت نشد.")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))
        except Exception as e:
            reply = await msg.reply_text(f"⚠️ خطا در دریافت لیست مدیران: {e}")
            asyncio.create_task(_auto_delete(context.bot, chat.id, reply.message_id, 10))

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
