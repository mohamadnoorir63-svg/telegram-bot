from telegram import MessageEntity
import re
from datetime import datetime, timedelta

# === جایگزین تابع حل هدف (resolve) ===
async def _resolve_target(msg, context, chat_id, explicit_arg: str = None):
    """
    برمی‌گرداند: telegram.User یا None
    اولویت‌ها:
      1) ریپلای
      2) entity: text_mention -> ent.user
      3) entity: mention -> متن mention -> get_chat(username)
      4) explicit_arg (از الگوی دستور): اگر @username یا id باشد
      5) fallback: پیدا کردن @username در متن
      6) آیدی عددی در متن
    """
    # 1) ریپلای
    if msg.reply_to_message and getattr(msg.reply_to_message, "from_user", None):
        return msg.reply_to_message.from_user

    text = (msg.text or "") or ""
    entities = msg.entities or []

    # 2) بررسی entityها
    for ent in entities:
        try:
            if ent.type == MessageEntity.TEXT_MENTION and getattr(ent, "user", None):
                return ent.user

            if ent.type == MessageEntity.MENTION:
                # ent.offset و ent.length به متن اشاره می‌کنند
                start = ent.offset
                length = ent.length
                raw = text[start:start + length]  # مثل "@username"
                username = raw.lstrip("@").strip()
                if username:
                    try:
                        # get_chat برای username عمومی کار می‌کنه و object با id برمی‌گردونه
                        user_obj = await context.bot.get_chat(username)
                        # user_obj ممکنه Chat یا User باشه؛ در هر صورت id رو داریم
                        return user_obj
                    except Exception:
                        # اگر get_chat موفق نبود ادامه میدیم تا fallbackها چک شوند
                        continue
        except Exception:
            continue

    # 3) explicit_arg (مثلاً capture group از regex)
    if explicit_arg:
        arg = explicit_arg.strip()
        # اگر با @ اومده
        if arg.startswith("@"):
            username = arg.lstrip("@")
            try:
                user_obj = await context.bot.get_chat(username)
                return user_obj
            except Exception:
                pass
        # اگر عددی (آیدی)
        if re.fullmatch(r"\d{6,15}", arg):
            try:
                cm = await context.bot.get_chat_member(chat_id, int(arg))
                return cm.user
            except Exception:
                # اگر get_chat_member نشد، شاید کاربر بیرون گروه باشه؛ تلاش برای get_chat
                try:
                    user_obj = await context.bot.get_chat(int(arg))
                    return user_obj
                except Exception:
                    pass

    # 4) fallback: جستجوی @username در متن (بدون entity)
    m_user = re.search(r"@([A-Za-z0-9_]{3,})", text)
    if m_user:
        username = m_user.group(1)
        try:
            user_obj = await context.bot.get_chat(username)
            return user_obj
        except Exception:
            pass

    # 5) آیدی عددی در متن
    m_id = re.search(r"\b(\d{6,15})\b", text)
    if m_id:
        try:
            target_id = int(m_id.group(1))
            # اگر در گروه عضو است، get_chat_member جواب می‌دهد
            cm = await context.bot.get_chat_member(chat_id, target_id)
            return cm.user
        except Exception:
            # تلاش get_chat به عنوان fallback
            try:
                user_obj = await context.bot.get_chat(int(m_id.group(1)))
                return user_obj
            except Exception:
                pass

    # هیچ‌کدوم هم نشد
    return None


# === جایگزین هندلر تنبیهات (handle_punishments) ===
async def handle_punishments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not msg or chat.type not in ("group", "supergroup"):
        return

    text = (msg.text or "").strip()
    if not text:
        return

    # الگوهای دستور: حالا username یا id را می‌پذیرد (گروه capture 1)
    PATTERNS = {
        "ban": re.compile(r"^بن(?:\s+(@?[A-Za-z0-9_]{3,}|[0-9]{6,15}))?\s*$"),
        "unban": re.compile(r"^حذف\s*بن(?:\s+(@?[A-Za-z0-9_]{3,}|[0-9]{6,15}))?\s*$"),
        "mute": re.compile(r"^سکوت(?:\s+(@?[A-Za-z0-9_]{3,}|[0-9]{6,15}))?(?:\s+(\d+)\s*(ثانیه|دقیقه|ساعت)?)?\s*$"),
        "unmute": re.compile(r"^حذف\s*سکوت(?:\s+(@?[A-Za-z0-9_]{3,}|[0-9]{6,15}))?\s*$"),
        "warn": re.compile(r"^اخطار(?:\s+(@?[A-Za-z0-9_]{3,}|[0-9]{6,15}))?\s*$"),
        "delwarn": re.compile(r"^حذف\s*اخطار(?:\s+(@?[A-Za-z0-9_]{3,}|[0-9]{6,15}))?\s*$"),
    }

    matched = None
    cmd_type = None
    for k, pat in PATTERNS.items():
        m = pat.match(text)
        if m:
            cmd_type = k
            matched = m
            break

    if not cmd_type:
        return

    # بررسی دسترسی
    if not await _has_access(context, chat.id, user.id):
        return await msg.reply_text("🚫 فقط مدیران یا سودوها مجازند.")

    # explicit_arg از گروه 1 (ممکنه @username یا id یا None)
    explicit_arg = None
    extra_time = None
    if matched:
        explicit_arg = matched.group(1) if matched.lastindex and matched.lastindex >= 1 else None
        if cmd_type == "mute" and matched.lastindex and matched.lastindex >= 3:
            num = matched.group(2)
            unit = matched.group(3)
            if num:
                extra_time = (int(num), unit)

    # resolve target (ریپلای یا explicit_arg)
    target_user = await _resolve_target(msg, context, chat.id, explicit_arg)
    if not target_user:
        return await msg.reply_text(
            "⚠️ هدف مشخص نیست.\n• ریپلای روی پیام کاربر\n• یا آیدی/یوزرنیم\n",
            parse_mode="Markdown"
        )

    # محافظت‌ها
    bot_user = await context.bot.get_me()
    try:
        target_id = target_user.id
    except Exception:
        return await msg.reply_text("⚠️ خطا: نتوانستم شناسهٔ کاربر را استخراج کنم.")

    if target_id == bot_user.id:
        return await msg.reply_text("😅 نمی‌تونم خودم رو تنبیه کنم.")
    if target_id in SUDO_IDS:
        return await msg.reply_text("🚫 این کاربر در لیست سودو است و قابل تنبیه نیست.")
    try:
        tm = await context.bot.get_chat_member(chat.id, target_id)
        if tm.status in ("creator", "administrator"):
            return await msg.reply_text("🛡 امکان اجرای دستور روی این کاربر وجود ندارد (ادمین).")
    except Exception:
        # اگر get_chat_member خطا داد، ممکنه کاربر عضو گروه نباشد؛ اما برای بن با آیدی هم تلاش خواهیم کرد
        pass

    # اجرای دستورها
    try:
        if cmd_type == "ban":
            await context.bot.ban_chat_member(chat.id, target_id)
            return await msg.reply_text(f"🚫 {getattr(target_user, 'first_name', str(target_id))} از گروه بن شد.")

        if cmd_type == "unban":
            await context.bot.unban_chat_member(chat.id, target_id)
            return await msg.reply_text(f"✅ {getattr(target_user, 'first_name', str(target_id))} از بن خارج شد.")

        if cmd_type == "mute":
            seconds = 3600
            if extra_time:
                num, unit = extra_time
                if unit == "ساعت":
                    seconds = num * 3600
                elif unit == "دقیقه":
                    seconds = num * 60
                else:
                    seconds = num
            until = datetime.utcnow() + timedelta(seconds=seconds)
            await context.bot.restrict_chat_member(
                chat.id, target_id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until
            )
            return await msg.reply_text(f"🤐 {getattr(target_user, 'first_name', str(target_id))} برای {seconds} ثانیه سکوت شد.")

        if cmd_type == "unmute":
            await context.bot.restrict_chat_member(
                chat.id, target_id,
                permissions=ChatPermissions(can_send_messages=True)
            )
            return await msg.reply_text(f"🔊 {getattr(target_user, 'first_name', str(target_id))} از سکوت خارج شد.")

        if cmd_type == "warn":
            warns = _load_json(WARN_FILE)
            key = f"{chat.id}:{target_id}"
            warns[key] = warns.get(key, 0) + 1
            _save_json(WARN_FILE, warns)
            if warns[key] >= 3:
                await context.bot.ban_chat_member(chat.id, target_id)
                warns[key] = 0
                _save_json(WARN_FILE, warns)
                return await msg.reply_text(f"🚫 {getattr(target_user, 'first_name', str(target_id))} به‌دلیل ۳ اخطار بن شد.")
            else:
                return await msg.reply_text(f"⚠️ {getattr(target_user, 'first_name', str(target_id))} اخطار {warns[key]}/3 گرفت.")

        if cmd_type == "delwarn":
            warns = _load_json(WARN_FILE)
            key = f"{chat.id}:{target_id}"
            if key in warns:
                del warns[key]
                _save_json(WARN_FILE, warns)
                return await msg.reply_text(f"✅ اخطارهای {getattr(target_user, 'first_name', str(target_id))} حذف شد.")
            return await msg.reply_text("ℹ️ این کاربر اخطاری نداشت.")

    except Exception as e:
        print("handle_punishments execution exception:", e)
        return await msg.reply_text(f"⚠️ خطا در اجرای دستور: {e}")
