import os
import json
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

async def _has_access(context, chat_id, user_id):
    """بررسی دسترسی فرد اجراکننده"""
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False

async def _bot_can_promote(context, chat_id):
    """بررسی اینکه ربات اجازه ارتقا به مدیر را دارد یا خیر"""
    try:
        me = await context.bot.get_chat_member(chat_id, context.bot.id)
        return me.status == "creator" or getattr(me, "can_promote_members", False)
    except:
        return False

# ================= 🧰 مدیریت مدیران با alias =================
async def handle_admin_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    text = (msg.text or "").strip()

    if chat.type not in ("group", "supergroup") or not text:
        return

    data = _load_json(ADMINS_FILE)
    chat_key = str(chat.id)
    if chat_key not in data:
        data[chat_key] = []

    aliases_all = _load_json(ALIAS_FILE)
    aliases = aliases_all.get(chat_key, {})

    # ================= 📌 افزودن دستور جدید =================
    if text.startswith("دستور جدید"):
        if not await _has_access(context, chat.id, user.id):
            return await msg.reply_text("🚫 فقط مدیران یا سودوها مجاز به افزودن دستور هستند.")

        # فرمت: دستور جدید [نام دستور] [افزودن‌مدیر|حذف‌مدیر] [متن پاسخ]
        import re
        match = re.match(r"^دستور جدید\s+(\S+)\s+(افزودن‌مدیر|حذف‌مدیر)\s+(.+)$", text)
        if not match:
            return await msg.reply_text(
                "📘 فرمت درست:\n"
                "<code>دستور جدید [نام دستور] [افزودن‌مدیر|حذف‌مدیر] [متن پاسخ]</code>\n"
                "مثال:\n"
                "<code>دستور جدید ارتقا مدیر افزودن‌مدیر {name} به عنوان مدیر منصوب شد!</code>",
                parse_mode="HTML"
            )

        name, cmd_type, response = match.groups()
        if name in aliases:
            return await msg.reply_text("⚠️ این نام قبلاً تعریف شده.")

        aliases[name] = {"type": cmd_type, "text": response}
        aliases_all[chat_key] = aliases
        _save_json(ALIAS_FILE, aliases_all)
        return await msg.reply_text(f"✅ دستور جدید <b>{name}</b> ثبت شد.", parse_mode="HTML")

    # ================= بررسی aliasها =================
    for cmd_name, cmd_info in aliases.items():
        if text == cmd_name:
            cmd_type = cmd_info.get("type")
            if cmd_type in ("افزودن‌مدیر", "حذف‌مدیر"):
                if not await _has_access(context, chat.id, user.id):
                    return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
                if not msg.reply_to_message:
                    return await msg.reply_text("⚠️ باید روی پیام کاربر ریپلای کنی.")
                target = msg.reply_to_message.from_user

                if target.id == context.bot.id:
                    return await msg.reply_text("😅 نمی‌توانم خودم را مدیر کنم!")
                if target.id in SUDO_IDS:
                    return await msg.reply_text("👑 این کاربر سودو است و تغییر نمی‌کند.")

                if not await _bot_can_promote(context, chat.id):
                    return await msg.reply_text("🚫 من اجازه‌ی تغییر مدیران را ندارم. لطفاً ربات را ادمین کنید و دسترسی Promote Members بدهید.")

                try:
                    if cmd_type == "افزودن‌مدیر":
                        await context.bot.promote_chat_member(
                            chat_id=chat.id,
                            user_id=target.id,
                            can_delete_messages=True,
                            can_restrict_members=True,
                            can_invite_users=True,
                            can_pin_messages=True,
                            can_manage_topics=True
                        )
                        if target.id not in data[chat_key]:
                            data[chat_key].append(target.id)
                            _save_json(ADMINS_FILE, data)
                    elif cmd_type == "حذف‌مدیر":
                        await context.bot.promote_chat_member(
                            chat_id=chat.id,
                            user_id=target.id,
                            can_manage_chat=False,
                            can_delete_messages=False,
                            can_manage_video_chats=False,
                            can_restrict_members=False,
                            can_promote_members=False,
                            can_change_info=False,
                            can_invite_users=False,
                            can_pin_messages=False,
                            can_manage_topics=False
                        )
                        if target.id in data[chat_key]:
                            data[chat_key].remove(target.id)
                            _save_json(ADMINS_FILE, data)

                    text_out = cmd_info.get("text", "").replace("{name}", target.first_name)
                    return await msg.reply_text(text_out or "✅ عملیات انجام شد.")
                except Exception as e:
                    return await msg.reply_text(f"⚠️ خطا در اجرای دستور: {e}")

    # ================= ➕ افزودن مدیر =================
    if text.startswith("افزودن مدیر"):
        if not await _has_access(context, chat.id, user.id):
            return await msg.reply_text("🚫 فقط مدیران یا سودوها مجاز به اجرای این دستور هستند.")
        if not msg.reply_to_message:
            return await msg.reply_text("⚠️ لطفاً روی پیام فرد موردنظر ریپلای کن.")
        target = msg.reply_to_message.from_user

        if target.id == context.bot.id:
            return await msg.reply_text("😅 نمی‌توانم خودم را مدیر کنم!")
        if target.id in SUDO_IDS:
            return await msg.reply_text("👑 این کاربر سودو است و نیازی به افزودن ندارد.")
        if not await _bot_can_promote(context, chat.id):
            return await msg.reply_text("🚫 من اجازه‌ی تغییر مدیران را ندارم. لطفاً ربات را ادمین کنید و دسترسی Promote Members بدهید.")

        try:
            await context.bot.promote_chat_member(
                chat_id=chat.id,
                user_id=target.id,
                can_delete_messages=True,
                can_restrict_members=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_manage_topics=True
            )
            if target.id not in data[chat_key]:
                data[chat_key].append(target.id)
                _save_json(ADMINS_FILE, data)
            await msg.reply_text(
                f"👑 {target.first_name} توسط {user.first_name} به‌عنوان <b>مدیر گروه</b> منصوب شد.",
                parse_mode="HTML"
            )
        except Exception as e:
            await msg.reply_text(f"⚠️ خطا در افزودن مدیر: {e}")

    # ================= ❌ حذف مدیر =================
    elif text.startswith("حذف مدیر"):
        if not await _has_access(context, chat.id, user.id):
            return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
        if not msg.reply_to_message:
            return await msg.reply_text("⚠️ لطفاً روی پیام مدیر موردنظر ریپلای کن.")
        target = msg.reply_to_message.from_user

        if target.id == context.bot.id:
            return await msg.reply_text("😅 نمی‌توانم خودم را حذف کنم!")
        if target.id in SUDO_IDS:
            return await msg.reply_text("🚫 نمی‌توان سودو را از مدیریت حذف کرد!")
        if not await _bot_can_promote(context, chat.id):
            return await msg.reply_text("🚫 من اجازه‌ی تغییر مدیران را ندارم. لطفاً ربات را ادمین کنید و دسترسی Promote Members بدهید.")

        try:
            await context.bot.promote_chat_member(
                chat_id=chat.id,
                user_id=target.id,
                can_manage_chat=False,
                can_delete_messages=False,
                can_manage_video_chats=False,
                can_restrict_members=False,
                can_promote_members=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False,
                can_manage_topics=False
            )
            if target.id in data[chat_key]:
                data[chat_key].remove(target.id)
                _save_json(ADMINS_FILE, data)
            await msg.reply_text(
                f"⚙️ {target.first_name} توسط {user.first_name} از فهرست <b>مدیران گروه</b> کنار گذاشته شد.",
                parse_mode="HTML"
            )
        except Exception as e:
            await msg.reply_text(f"⚠️ خطا در حذف مدیر: {e}")

    # ================= 📋 لیست مدیران =================
    elif text == "لیست مدیران":
        try:
            current_admins = await context.bot.get_chat_administrators(chat.id)
            lines = [f"• {a.user.first_name}" for a in current_admins if not a.user.is_bot]
            if lines:
                await msg.reply_text("👑 <b>مدیران فعلی گروه:</b>\n" + "\n".join(lines), parse_mode="HTML")
            else:
                await msg.reply_text("ℹ️ هیچ مدیری در گروه یافت نشد.")
        except Exception as e:
            await msg.reply_text(f"⚠️ خطا در دریافت لیست مدیران: {e}")

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
