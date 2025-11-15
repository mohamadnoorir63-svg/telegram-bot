import asyncio
from datetime import datetime, time
from zoneinfo import ZoneInfo
from telegram import ChatPermissions, Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

SUPERUSER_ID = 8588347189  # آیدی سودو اصلی
AUTO_LOCK_ENABLED = False
AUTO_LOCK_START = time(0, 0)
AUTO_LOCK_END = time(7, 0)
LOCKED_BY_AUTO = {}  # وضعیت قفل خودکار هر چت
AFGHAN_TZ = ZoneInfo("Asia/Kabul")
AUTO_LOCK_CHATS = set()  # چت‌هایی که قفل خودکار برایشان فعال است

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

async def is_admin_or_sudo(update: Update):
    user = update.effective_user
    if user.id == SUPERUSER_ID:
        return True
    member = await update.effective_chat.get_member(user.id)
    return member.status in ['administrator', 'creator']

async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE, auto=False):
    if not auto and not await is_admin_or_sudo(update):
        return
    try:
        await update.effective_chat.set_permissions(ChatPermissions(can_send_messages=False))
        if not auto:
            await update.message.reply_text(
                f"🔒 گروه به دستور {update.effective_user.first_name} تا اطلاع ثانوی قفل شد!\n🛡️ تمام اعضا تا اطلاع بعدی نمی‌توانند پیام بفرستند."
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
                f"🔓 گروه به دستور {update.effective_user.first_name} باز شد!\n✅ حالا همه می‌توانند پیام بفرستند."
            )
            await asyncio.sleep(10)
            await msg.delete()
    except Exception as e:
        if not auto:
            await update.message.reply_text(f"❌ خطا: {e}")

async def auto_lock_task(app: Application):
    global AUTO_LOCK_ENABLED, AUTO_LOCK_START, AUTO_LOCK_END, LOCKED_BY_AUTO
    await app.wait_until_ready()
    while True:
        if AUTO_LOCK_ENABLED:
            now_af = datetime.now(AFGHAN_TZ).time()
            for chat_id in AUTO_LOCK_CHATS:
                try:
                    chat = await app.bot.get_chat(chat_id)
                    if AUTO_LOCK_START <= AUTO_LOCK_END:
                        in_lock_time = AUTO_LOCK_START <= now_af <= AUTO_LOCK_END
                    else:
                        in_lock_time = now_af >= AUTO_LOCK_START or now_af <= AUTO_LOCK_END

                    if in_lock_time and not LOCKED_BY_AUTO.get(chat_id, False):
                        await chat.set_permissions(ChatPermissions(can_send_messages=False))
                        LOCKED_BY_AUTO[chat_id] = True
                        await chat.send_message("🤖 گروه به صورت خودکار قفل شد!\n🛡️ لطفاً صبور باشید.")
                    elif not in_lock_time and LOCKED_BY_AUTO.get(chat_id, False):
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
                        LOCKED_BY_AUTO[chat_id] = False
                        msg = await chat.send_message("🤖 گروه به صورت خودکار باز شد!\n✅ حالا همه می‌توانند پیام بفرستند.")
                        await asyncio.sleep(10)
                        await msg.delete()
                except:
                    pass
        await asyncio.sleep(30)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_LOCK_ENABLED, AUTO_LOCK_START, AUTO_LOCK_END
    text = update.message.text.strip().replace("‌", "").lower()
    chat_id = update.effective_chat.id

    if text == "قفل گروه":
        await lock_group(update, context)
    elif text == "باز کردن گروه":
        await unlock_group(update, context)
    elif text == "قفل خودکار روشن":
        if not await is_admin_or_sudo(update): return
        AUTO_LOCK_ENABLED = True
        AUTO_LOCK_CHATS.add(chat_id)
        await update.message.reply_text("🤖 قفل خودکار گروه فعال شد!")
    elif text == "قفل خودکار خاموش":
        if not await is_admin_or_sudo(update): return
        AUTO_LOCK_ENABLED = False
        AUTO_LOCK_CHATS.discard(chat_id)
        await update.message.reply_text("🤖 قفل خودکار گروه غیرفعال شد!")
    elif text.startswith("تنظیم قفل خودکار"):
        if not await is_admin_or_sudo(update): return
        try:
            time_range = text.split()[-1]
            start_str, end_str = time_range.split("-")
            h1, m1 = map(int, start_str.split(":"))
            h2, m2 = map(int, end_str.split(":"))
            AUTO_LOCK_START = time(h1, m1)
            AUTO_LOCK_END = time(h2, m2)
            await update.message.reply_text(
                f"⏰ بازه قفل خودکار تنظیم شد: {AUTO_LOCK_START.strftime('%H:%M')} تا {AUTO_LOCK_END.strftime('%H:%M')} "
                f"(طبق ساعت افغانستان)"
            )
        except:
            await update.message.reply_text("❌ فرمت زمان اشتباه است. مثال: تنظیم قفل خودکار 12:00-07:00")

def register_group_lock_handlers(app: Application, group: int = 17):
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text), group=group)
    async def start_task(app: Application):
        app.create_task(auto_lock_task(app))
    app.post_init = start_task
