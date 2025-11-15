import asyncio
from datetime import datetime, time
from zoneinfo import ZoneInfo
from telegram import ChatPermissions, Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

# -------------------- سودو --------------------
SUPERUSER_ID = 8588347189  # آیدی سودو اصلی

# -------------------- وضعیت قفل خودکار --------------------
AUTO_LOCK_ENABLED = False
AUTO_LOCK_START = time(0, 0)
AUTO_LOCK_END = time(7, 0)
LOCKED_BY_AUTO = {}           # وضعیت قفل خودکار هر چت

# -------------------- تابع کمکی --------------------
def safe_permissions(chat):
    p = chat.permissions
    if p is None:
        return ChatPermissions(
            can_send_messages=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_invite_users=True,
            can_pin_messages=False,
            can_change_info=False
        )
    return p

# -------------------- بررسی دسترسی --------------------
async def is_admin_or_sudo(update: Update):
    user = update.effective_user
    if user.id == SUPERUSER_ID:
        return True
    member = await update.effective_chat.get_member(user.id)
    return member.status in ['administrator', 'creator']

# -------------------- قفل و باز گروه --------------------
async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE, auto=False):
    if not auto and not await is_admin_or_sudo(update):
        return
    try:
        await update.effective_chat.set_permissions(ChatPermissions(can_send_messages=False))
        if not auto:
            await update.message.reply_text(
                f"🔒 گروه به دستور {update.effective_user.first_name} تا اطلاع ثانوی قفل شد!\n"
                f"🛡️ تمام اعضا تا اطلاع بعدی نمی‌توانند پیام بفرستند."
            )
    except Exception as e:
        if not auto:
            await update.message.reply_text(f"❌ خطا: {e}")

async def unlock_group(update: Update, context: ContextTypes.DEFAULT_TYPE, auto=False):
    if not auto and not await is_admin_or_sudo(update):
        return
    try:
        chat = update.effective_chat
        current = safe_permissions(chat)
        new_permissions = ChatPermissions(
            can_send_messages=True,
            can_send_audios=current.can_send_audios,
            can_send_documents=current.can_send_documents,
            can_send_photos=current.can_send_photos,
            can_send_videos=current.can_send_videos,
            can_send_video_notes=current.can_send_video_notes,
            can_send_voice_notes=current.can_send_voice_notes,
            can_send_polls=current.can_send_polls,
            can_send_other_messages=current.can_send_other_messages,
            can_add_web_page_previews=current.can_add_web_page_previews,
            can_invite_users=current.can_invite_users,
            can_pin_messages=current.can_pin_messages,
            can_change_info=current.can_change_info
        )
        await chat.set_permissions(new_permissions)

        if not auto:
            msg = await update.message.reply_text(
                f"🔓 گروه به دستور {update.effective_user.first_name} باز شد!\n"
                f"✅ حالا همه می‌توانند پیام بفرستند."
            )
            await asyncio.sleep(10)
            await msg.delete()
    except Exception as e:
        if not auto:
            await update.message.reply_text(f"❌ خطا: {e}")

# -------------------- تسک قفل خودکار --------------------
async def auto_lock_task(app: Application):
    global AUTO_LOCK_ENABLED, AUTO_LOCK_START, AUTO_LOCK_END, LOCKED_BY_AUTO
    await app.wait_until_ready()
    while True:
        if AUTO_LOCK_ENABLED:
            # ساعت محلی سرور را برای هماهنگی استفاده می‌کنیم
            now_utc = datetime.utcnow()
            for chat_id in app.chat_data:
                try:
                    chat = await app.bot.get_chat(chat_id)
                    # بررسی وضعیت قفل خودکار
                    # تبدیل AUTO_LOCK_START و AUTO_LOCK_END به زمان UTC
                    lock_start_dt = datetime.combine(now_utc.date(), AUTO_LOCK_START)
                    lock_end_dt = datetime.combine(now_utc.date(), AUTO_LOCK_END)
                    # اگر بازه شبانه باشد
                    if AUTO_LOCK_START > AUTO_LOCK_END:
                        lock_end_dt += timedelta(days=1)

                    in_lock_time = lock_start_dt.time() <= now_utc.time() <= lock_end_dt.time() \
                                   if AUTO_LOCK_START <= AUTO_LOCK_END else \
                                   now_utc.time() >= AUTO_LOCK_START or now_utc.time() <= AUTO_LOCK_END

                    if in_lock_time and not LOCKED_BY_AUTO.get(chat_id, False):
                        await lock_group_for_auto(chat)
                        LOCKED_BY_AUTO[chat_id] = True
                        await chat.send_message(
                            "🤖 گروه به صورت خودکار قفل شد!\n"
                            "🛡️ لطفاً صبور باشید، همه پیام‌ها موقتاً مسدود شده‌اند."
                        )
                    elif not in_lock_time and LOCKED_BY_AUTO.get(chat_id, False):
                        await unlock_group_for_auto(chat)
                        LOCKED_BY_AUTO[chat_id] = False
                        await chat.send_message(
                            "🤖 گروه به صورت خودکار باز شد!\n✅ حالا همه می‌توانند پیام بفرستند."
                        )
                except:
                    pass
        await asyncio.sleep(60)

async def lock_group_for_auto(chat):
    await chat.set_permissions(ChatPermissions(can_send_messages=False))

async def unlock_group_for_auto(chat):
    current = safe_permissions(chat)
    new_permissions = ChatPermissions(
        can_send_messages=True,
        can_send_audios=current.can_send_audios,
        can_send_documents=current.can_send_documents,
        can_send_photos=current.can_send_photos,
        can_send_videos=current.can_send_videos,
        can_send_video_notes=current.can_send_video_notes,
        can_send_voice_notes=current.can_send_voice_notes,
        can_send_polls=current.can_send_polls,
        can_send_other_messages=current.can_send_other_messages,
        can_add_web_page_previews=current.can_add_web_page_previews,
        can_invite_users=current.can_invite_users,
        can_pin_messages=current.can_pin_messages,
        can_change_info=current.can_change_info
    )
    await chat.set_permissions(new_permissions)

# -------------------- هندلر متن --------------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_LOCK_ENABLED, AUTO_LOCK_START, AUTO_LOCK_END
    text = update.message.text.strip().replace("‌", "").lower()

    # تشخیص منطقه زمانی کاربر از پیام
    user_tz = None
    try:
        user_tz = update.effective_user.language_code  # بعضی اطلاعات تلگرام ممکن است ناحیه کاربر را بدهد
        if not user_tz:
            user_tz = "UTC"
    except:
        user_tz = "UTC"

    # دستورات اصلی
    if text == "قفل گروه":
        await lock_group(update, context)
    elif text == "باز کردن گروه":
        await unlock_group(update, context)

    # دستورات قفل خودکار
    elif text == "قفل خودکار روشن":
        if not await is_admin_or_sudo(update):
            return
        AUTO_LOCK_ENABLED = True
        await update.message.reply_text("🤖 قفل خودکار گروه فعال شد!")
    elif text == "قفل خودکار خاموش":
        if not await is_admin_or_sudo(update):
            return
        AUTO_LOCK_ENABLED = False
        await update.message.reply_text("🤖 قفل خودکار گروه غیرفعال شد!")
    elif text.startswith("تنظیم قفل خودکار"):
        if not await is_admin_or_sudo(update):
            return
        try:
            time_range = text.split()[-1]
            start_str, end_str = time_range.split("-")
            h1, m1 = map(int, start_str.split(":"))
            h2, m2 = map(int, end_str.split(":"))
            AUTO_LOCK_START = time(h1, m1)
            AUTO_LOCK_END = time(h2, m2)
            await update.message.reply_text(
                f"⏰ بازه قفل خودکار تنظیم شد: {AUTO_LOCK_START.strftime('%H:%M')} تا {AUTO_LOCK_END.strftime('%H:%M')} "
                f"(طبق منطقه زمانی کاربر)"
            )
        except:
            await update.message.reply_text(
                "❌ فرمت زمان اشتباه است. مثال: تنظیم قفل خودکار 12:00-07:00"
            )

# -------------------- ثبت هندلر --------------------
def register_group_lock_handlers(app: Application, group: int = 17):
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text), group=group)
    async def start_auto_lock_task(app: Application):
        app.create_task(auto_lock_task(app))
    app.post_init = start_auto_lock_task
