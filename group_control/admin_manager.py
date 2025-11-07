import os
import json
import re
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

# ================= ⚙️ تنظیمات اولیه =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADMINS_FILE = os.path.join(BASE_DIR, "group_admins.json")
ALIAS_FILE = os.path.join(BASE_DIR, "custom_cmds.json")

SUDO_IDS = [8588347189]  # آیدی سودوها (سودوهای ربات)

# ایجاد فایل‌ها در صورت عدم وجود
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

    # بارگذاری aliasها
    aliases_all = _load_json(ALIAS_FILE)
    aliases = aliases_all.get(chat_key, {})

    # تابع پیدا کردن هدف (target) از ریپلای، @username یا آیدی
    async def get_target():
        if msg.reply_to_message:
            return msg.reply_to_message.from_user
        # @username
        m_user = re.search(r"@([A-Za-z0-9_]{5,32})", text)
        if m_user:
            username = m_user.group(1)
            try:
                member = await context.bot.get_chat_member(chat.id, username)
                return member.user
            except:
                return None
        # user_id
        m_id = re.search(r"\b(\d{6,15})\b", text)
        if m_id:
            try:
                user_id = int(m_id.group(1))
                member = await context.bot.get_chat_member(chat.id, user_id)
                return member.user
            except:
                return None
        return None

    # ===== بررسی alias ها =====
    for cmd_name, cmd_info in aliases.items():
        if text.startswith(cmd_name):
            cmd_type = cmd_info.get("type")
            target = await get_target()
            if not target:
                return await msg.reply_text("⚠️ لطفاً روی پیام کاربر ریپلای کنید یا @username/آیدی وارد کنید.")
            if not await _has_access(context, chat.id, user.id):
                return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

            # محافظت از ربات و سودو
            if target.id == context.bot.id:
                return await msg.reply_text("😅 نمی‌توانم خودم را مدیر کنم یا حذف کنم.")
            if target.id in SUDO_IDS:
                return await msg.reply_text("👑 این کاربر سودو است و تغییر نمی‌کند.")

            try:
                bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
                if getattr(bot_member, "can_promote_members", False) is not True and bot_member.status != "creator":
                    return await msg.reply_text("🚫 من اجازه‌ی تغییر مدیران را ندارم.")

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

    # ===== دستورهای پایه =====
    if text.startswith("افزودن مدیر") or text.startswith("حذف مدیر") or text == "لیست مدیران":
        target = await get_target()
        # این بخش همانند قبل بدون تغییر
        if text.startswith("افزودن مدیر"):
            if not await _has_access(context, chat.id, user.id):
                return await msg.reply_text("🚫 فقط مدیران یا سودوها مجاز به اجرای این دستور هستند.")
            if not target:
                return await msg.reply_text("⚠️ لطفاً روی پیام کاربر ریپلای کنید یا @username/آیدی وارد کنید.")
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
        elif text.startswith("حذف مدیر"):
            if not await _has_access(context, chat.id, user.id):
                return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")
            if not target:
                return await msg.reply_text("⚠️ لطفاً روی پیام مدیر ریپلای کنید یا @username/آیدی وارد کنید.")
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
    """ثبت هندلر مدیریت مدیران (با alias و شناسایی target)"""
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            handle_admin_management,
        ),
        group=group_number,
    )
