import os
import json
import re
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

# ================= ⚙️ تنظیمات اولیه =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADMINS_FILE = os.path.join(BASE_DIR, "group_admins.json")
ALIAS_FILE = os.path.join(BASE_DIR, "custom_cmds.json")

SUDO_IDS = [8588347189]  # آیدی سودوها

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
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False

async def _bot_can_promote(context, chat_id):
    try:
        me = await context.bot.get_chat_member(chat_id, context.bot.id)
        return me.status == "creator" or getattr(me, "can_promote_members", False)
    except:
        return False

async def _get_target_user(update: Update, context, text: str):
    """بررسی هدف: ریپلای یا یوزرنیم/آیدی"""
    msg = update.effective_message
    if msg.reply_to_message:
        return msg.reply_to_message.from_user
    parts = text.split()
    if len(parts) >= 2:
        identifier = parts[1]
        if identifier.startswith("@"):
            try:
                user = await context.bot.get_chat_member(update.effective_chat.id, identifier)
                return user.user
            except:
                return None
        else:
            try:
                user_id = int(identifier)
                user = await context.bot.get_chat_member(update.effective_chat.id, user_id)
                return user.user
            except:
                return None
    return None

# ================= 🧰 مدیریت مدیران و alias =================
async def handle_admin_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    text = (msg.text or "").strip()
    handled = False  # 🔹 برای جلوگیری از ارسال دوباره پیام

    if chat.type not in ("group", "supergroup") or not text:
        return

    data = _load_json(ADMINS_FILE)
    chat_key = str(chat.id)
    if chat_key not in data:
        data[chat_key] = []

    aliases_all = _load_json(ALIAS_FILE)
    aliases = aliases_all.get(chat_key, {})

    # ================= 📌 ایجاد دستور جدید =================
    if text.startswith("دستور جدید"):
        if not await _has_access(context, chat.id, user.id):
            await msg.reply_text("🚫 فقط مدیران یا سودوها می‌توانند دستور جدید بسازند.")
            return
        match = re.match(r"^دستور جدید\s+(.+?)\s+(افزودن‌مدیر|حذف‌مدیر)\s+(.+)$", text)
        if not match:
            await msg.reply_text(
                "📘 فرمت درست:\n"
                "<code>دستور جدید [نام دستور] [افزودن‌مدیر|حذف‌مدیر] [متن پاسخ]</code>\n"
                "مثال:\n"
                "<code>دستور جدید ارتقا مدیر افزودن‌مدیر {name} به عنوان مدیر گروه منصوب شد!</code>",
                parse_mode="HTML"
            )
            return
        name, cmd_type, response = match.groups()
        if name in aliases:
            await msg.reply_text("⚠️ این نام قبلاً تعریف شده.")
            return
        aliases[name] = {"type": cmd_type, "text": response}
        aliases_all[chat_key] = aliases
        _save_json(ALIAS_FILE, aliases_all)
        await msg.reply_text(f"✅ دستور جدید <b>{name}</b> ثبت شد.", parse_mode="HTML")
        return

    # ================= بررسی aliasها =================
    if text in aliases:
        cmd_info = aliases[text]
        cmd_type = cmd_info.get("type")
        target = await _get_target_user(update, context, text)
        if not target:
            await msg.reply_text("⚠️ لطفاً روی پیام کاربر ریپلای کنید یا یوزرنیم/آیدی وارد کنید.")
            return
        # 🔹 بررسی شرایط خاص: خود ربات یا سودو
        if target.id == context.bot.id:
            await msg.reply_text("😅 نمی‌توانم خودم را مدیر کنم!")
            return
        if target.id in SUDO_IDS:
            await msg.reply_text("👑 این کاربر جزو سودوهاست و تغییر نمی‌کند.")
            return
        if not await _bot_can_promote(context, chat.id):
            await msg.reply_text("🚫 من اجازه‌ی تغییر مدیران را ندارم. لطفاً ربات را ادمین کنید و دسترسی Promote Members بدهید.")
            return
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
            await msg.reply_text(text_out or "✅ عملیات انجام شد.")
            handled = True
        except Exception as e:
            await msg.reply_text(f"⚠️ خطا در اجرای دستور: {e}")
            handled = True

    if handled:  # 🔹 اگر alias اجرا شد، دیگر ادامه نده
        return

    # ================= ➕ افزودن مدیر =================
    if text.startswith("افزودن مدیر"):
        target = await _get_target_user(update, context, text)
        if not target:
            await msg.reply_text("⚠️ لطفاً روی پیام کاربر ریپلای کنید یا یوزرنیم/آیدی وارد کنید.")
            return
        if not await _has_access(context, chat.id, user.id):
            await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
            return
        if target.id == context.bot.id:
            await msg.reply_text("😅 نمی‌توانم خودم را مدیر کنم!")
            return
        if target.id in SUDO_IDS:
            await msg.reply_text("👑 این کاربر جزو سودوهاست و تغییر نمی‌کند.")
            return
        if not await _bot_can_promote(context, chat.id):
            await msg.reply_text("🚫 من اجازه‌ی تغییر مدیران را ندارم. لطفاً ربات را ادمین کنید و دسترسی Promote Members بدهید.")
            return
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
            await msg.reply_text(f"👑 {target.first_name} به‌عنوان مدیر گروه منصوب شد.")
        except Exception as e:
            await msg.reply_text(f"⚠️ خطا در افزودن مدیر: {e}")

    # ================= ❌ حذف مدیر =================
    elif text.startswith("حذف مدیر"):
        target = await _get_target_user(update, context, text)
        if not target:
            await msg.reply_text("⚠️ لطفاً روی پیام کاربر ریپلای کنید یا یوزرنیم/آیدی وارد کنید.")
            return
        if not await _has_access(context, chat.id, user.id):
            await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
            return
        if target.id == context.bot.id:
            await msg.reply_text("😅 نمی‌توانم خودم را حذف کنم!")
            return
        if target.id in SUDO_IDS:
            await msg.reply_text("👑 این کاربر جزو سودوهاست و تغییر نمی‌کند.")
            return
        if not await _bot_can_promote(context, chat.id):
            await msg.reply_text("🚫 من اجازه‌ی تغییر مدیران را ندارم. لطفاً ربات را ادمین کنید و دسترسی Promote Members بدهید.")
            return
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
            await msg.reply_text(f"⚙️ {target.first_name} از فهرست مدیران گروه حذف شد.")
        except Exception as e:
            await msg.reply_text(f"⚠️ خطا در حذف مدیر: {e}")

    # ================= 📋 لیست مدیران =================
    elif text == "لیست مدیران":
        try:
            current_admins = await context.bot.get_chat_administrators(chat.id)
            lines = [f"• {a.user.first_name}" for a in current_admins if not a.user.is_bot]
            if lines:
                await msg.reply_text("👑 مدیران فعلی گروه:\n" + "\n".join(lines))
            else:
                await msg.reply_text("ℹ️ هیچ مدیری در گروه یافت نشد.")
        except Exception as e:
            await msg.reply_text(f"⚠️ خطا در دریافت لیست مدیران: {e}")

# ================= 🔧 ثبت هندلر =================
def register_admin_handlers(application, group_number: int = 15):
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_admin_management,
        ),
        group=group_number,
    )
