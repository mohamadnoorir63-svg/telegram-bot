# -*- coding: utf-8 -*-
# Khengool v5.5 – بدون API خارجی، حافظه پایدار، پنل، ارسال همگانی، شوخی ساعتی

import os, json, random, re, html
from datetime import timedelta
from typing import Dict, List, Any

from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated
)
from telegram.constants import ChatType, ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ChatMemberHandler, ContextTypes, filters
)

# ---------------------- تنظیمات اصلی ----------------------
TOKEN = os.environ.get("BOT_TOKEN", "").strip()
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))  # شناسه تلگرام مدیر اصلی
DATA_FILE = "memory.json"

# ---------------------- ابزار ذخیره/خواندن ----------------------
DEFAULT_DATA = {
    "active": True,              # روشن/خاموش بودن ربات
    "learning": True,            # یادگیری روشن/خاموش
    "mode": "normal",            # normal | funny | sad | rude
    "groups": {},                # {chat_id: {"title": str}}
    "replies": {},               # {"سلام": ["سلام خوبی؟", ...]}
    "last_reply": {}             # برای جلوگیری از تکرار پاسخ‌ها
}

def load_data() -> Dict[str, Any]:
    try:
        if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
            save_data(DEFAULT_DATA)
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # تطبیق با اسکیمای جدید
        for k, v in DEFAULT_DATA.items():
            if k not in data:
                data[k] = v
        return data
    except Exception:
        # اگر خراب بود، ریست امن
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA.copy()

def save_data(data: Dict[str, Any]) -> None:
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)

# ---------------------- کمکی‌ها ----------------------
def is_admin(user_id: int) -> bool:
    return SUDO_ID and user_id == SUDO_ID

def normalize_text(t: str) -> str:
    t = t.strip()
    # ساده‌سازی: حذف فاصله‌های زیاد
    t = re.sub(r"\s+", " ", t)
    return t

def pick_reply(key: str, data: Dict[str, Any]) -> str:
    """از بین پاسخ‌های یادگرفته‌شده برای یک کلید، بدون تکرار متوالی انتخاب می‌کند."""
    key = normalize_text(key)
    pool: List[str] = data["replies"].get(key, [])
    if not pool:
        return ""
    last = data["last_reply"].get(key)
    candidates = [x for x in pool if x != last] or pool[:]
    ans = random.choice(candidates)
    data["last_reply"][key] = ans
    save_data(data)
    return ans

def mood_wrap(text: str, mode: str) -> str:
    if mode == "funny":
        tails = ["😂", "😜", "😆", "🤪", "😎", "👌", "🔥"]
        return f"{text} {random.choice(tails)}"
    if mode == "sad":
        tails = ["😔", "🥲", "😕", "💔"]
        return f"{text} {random.choice(tails)}"
    if mode == "rude":
        # بی‌ادب ملایم (بدون توهین مستقیم)
        spices = ["باشه دیگه", "چشم؟!🙄", "عه جدی؟", "بابا معلومه", "خب که چی"]
        return f"{random.choice(spices)} — {text}"
    return text

def human_join_msg(title: str) -> str:
    jokes = [
        f"سلام به همه! نصب «خنگول» در «{title}» با موفقیت انجام شد 😎✨",
        f"اوه اوه! من اومدم تو «{title}» — آماده‌ی شوخی و شیطنت! 😜",
        f"درود! خنگول به گروه «{title}» پیوست؛ از الان مسئول بامزگی‌هام منم 😂",
    ]
    return random.choice(jokes)

# ---------------------- پنل و دکمه‌ها ----------------------
def build_panel(data: Dict[str, Any]) -> InlineKeyboardMarkup:
    active = "✅" if data["active"] else "❌"
    learning = "✅" if data["learning"] else "❌"
    mode = data["mode"]
    kb = [
        [
            InlineKeyboardButton(f"روشن/خاموش: {active}", callback_data="toggle_active"),
            InlineKeyboardButton(f"یادگیری: {learning}", callback_data="toggle_learn"),
        ],
        [
            InlineKeyboardButton("مود: normal", callback_data="mode_normal"),
            InlineKeyboardButton("مود: funny", callback_data="mode_funny"),
        ],
        [
            InlineKeyboardButton("مود: sad", callback_data="mode_sad"),
            InlineKeyboardButton("مود: rude", callback_data="mode_rude"),
        ],
        [
            InlineKeyboardButton("📤 ارسال همگانی", callback_data="broadcast_prompt"),
            InlineKeyboardButton("🧠 یادگرفته‌ها", callback_data="show_learned"),
        ]
    ]
    return InlineKeyboardMarkup(kb)

async def send_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    txt = (
        "وضعیت خنگول 📊:\n"
        f"فعال: {'✅' if data['active'] else '❌'}\n"
        f"یادگیری: {'✅' if data['learning'] else '❌'}\n"
        f"مود فعلی: {data['mode']}\n"
        f"تعداد گروه‌ها: {len(data['groups'])}"
    )
    await update.effective_chat.send_message(txt, reply_markup=build_panel(data))

# ---------------------- دستورات اصلی ----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_status(update, context)

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_status(update, context)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (
        "دستورات خنگول:\n"
        "• پنل یا /panel → نمایش پنل مدیریتی\n"
        "• وضعیت → نمایش وضعیت\n"
        "• روشن شو / خاموش شو → فعال/غیرفعال کردن\n"
        "• یادگیری روشن / یادگیری خاموش → کنترل یادگیری\n"
        "• مود [نرمال|شوخ|غمگین|بی‌ادب] → تغییر مود\n"
        "• یادبگیر کلید -> جواب۱ | جواب۲ | ... → ثبت پاسخ‌ها\n"
        "• یاد گرفتی؟ یا /learned → نمایش چیزهای یادگرفته\n"
        "• لفت بده → خنگول گروه را ترک می‌کند (فقط ادمین اصلی)\n"
        "• ارسال همگانی: از پنل دکمه‌اش را بزن (فقط ادمین اصلی)\n"
    )
    await update.effective_chat.send_message(txt)

# ---------------------- کال‌بک پنل ----------------------
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.callback_query:
        return
    q = update.callback_query
    await q.answer()
    data = load_data()
    uid = q.from_user.id

    if q.data == "toggle_active":
        data["active"] = not data["active"]
        save_data(data)
        await q.edit_message_reply_markup(build_panel(data))
        await q.message.reply_text(f"ربات اکنون {'فعال' if data['active'] else 'غیرفعال'} شد.")
        return

    if q.data == "toggle_learn":
        data["learning"] = not data["learning"]
        save_data(data)
        await q.edit_message_reply_markup(build_panel(data))
        await q.message.reply_text(f"یادگیری {'روشن' if data['learning'] else 'خاموش'} شد.")
        return

    if q.data.startswith("mode_"):
        data["mode"] = q.data.split("_", 1)[1]
        save_data(data)
        await q.edit_message_reply_markup(build_panel(data))
        await q.message.reply_text(f"مود به {data['mode']} تغییر کرد.")
        return

    if q.data == "show_learned":
        txt = preview_learned_text(data)
        await q.message.reply_text(txt, disable_web_page_preview=True)
        return

    if q.data == "broadcast_prompt":
        if not is_admin(uid):
            await q.message.reply_text("فقط مدیر اصلی اجازه‌ی این کار را دارد.")
            return
        context.user_data["await_broadcast"] = True
        await q.message.reply_text("متن ارسال همگانی را بفرست (تا ۴۰۹۶ کاراکتر).")
        return

def preview_learned_text(data: Dict[str, Any]) -> str:
    if not data["replies"]:
        return "هنوز چیزی یاد نگرفتم! با الگو:\n«یادبگیر سلام -> سلام خوبی | درود» آموزش بده."
    lines = []
    for k, v in list(data["replies"].items())[:50]:  # نمایش تا ۵۰ کلید
        smp = " | ".join(v[:5])  # هر کلید تا ۵ پاسخ نمونه
        lines.append(f"• {k} → {smp}")
    more = "" if len(data["replies"]) <= 50 else f"\n… و {len(data['replies'])-50} مورد دیگر"
    return "چیزهایی که یاد گرفتم:\n" + "\n".join(lines) + more# ---------------------- پردازش پیام‌های متنی ----------------------
def try_parse_learn_cmd(text: str):
    """
    فرمت‌های قابل قبول:
    - یادبگیر سلام -> سلام خوبی | درود | علیک
    - یادبگیر سلام : سلام خوبی | درود
    - یادبگیر سلام = سلام خوبی | درود
    """
    m = re.match(r"^(?:یادبگیر|یاد بگیر)\s+(.+?)\s*(?:->|:|=)\s*(.+)$", text, flags=re.I)
    if not m:
        return None, None
    key = normalize_text(m.group(1))
    vals = [normalize_text(x) for x in re.split(r"\|", m.group(2)) if normalize_text(x)]
    return key, vals

def try_parse_simple_toggles(text: str):
    low = text.replace("‌", "").strip().lower()
    if low in ["روشن شو", "فعال شو", "روشن"]:
        return ("active", True)
    if low in ["خاموش شو", "غیرفعال شو", "خاموش"]:
        return ("active", False)
    if low in ["یادگیری روشن", "یادگیری رو روشن کن", "یادگیری فعال"]:
        return ("learning", True)
    if low in ["یادگیری خاموش", "یادگیری رو خاموش کن", "یادگیری غیر فعال"]:
        return ("learning", False)
    # مودها
    if low in ["مود شوخ", "شوخ شو", "شوخ"]:
        return ("mode", "funny")
    if low in ["مود غمگین", "غمگین شو", "غمگین"]:
        return ("mode", "sad")
    if low in ["مود بی ادب", "بی ادب شو", "بی‌ادب شو", "بی‌ادب"]:
        return ("mode", "rude")
    if low in ["مود نرمال", "نرمال شو", "عادی شو", "نورمال"]:
        return ("mode", "normal")
    return (None, None)

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    data = load_data()
    chat = update.effective_chat
    txt = normalize_text(update.message.text)

    # ثبت گروه
    if chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        if str(chat.id) not in data["groups"]:
            data["groups"][str(chat.id)] = {"title": chat.title or str(chat.id)}
            save_data(data)

    # اگر درحال انتظار متن همگانی هستیم
    if context.user_data.get("await_broadcast"):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("فقط مدیر اصلی می‌تواند همگانی بفرستد.")
        else:
            await do_broadcast(context, txt)
        context.user_data.pop("await_broadcast", None)
        return

    # برخی کوئری‌های طبیعی
    if txt in ["پنل", "/panel", "وضعیت", "/status", "/start"]:
        await send_status(update, context)
        return

    if txt in ["یاد گرفتی؟", "چی یاد گرفتی", "/learned"]:
        await update.message.reply_text(preview_learned_text(data))
        return

    # سوییچ‌های ساده
    key, val = try_parse_simple_toggles(txt)
    if key is not None:
        if key in ["active", "learning"]:
            data[key] = val
            save_data(data)
            await update.message.reply_text(
                f"{'فعال' if key=='active' else 'یادگیری'} اکنون {'روشن' if val else 'خاموش'} شد."
            )
        elif key == "mode":
            data["mode"] = val
            save_data(data)
            await update.message.reply_text(f"مود به {val} تغییر کرد.")
        return

    # اگر ربات خاموش است و کاربر مدیر نیست، ساکت
    if not data["active"] and not is_admin(update.effective_user.id):
        return

    # یادگیری
    lk, lvals = try_parse_learn_cmd(txt)
    if lk and lvals:
        pool = data["replies"].setdefault(lk, [])
        added = 0
        for v in lvals:
            if v not in pool:
                pool.append(v)
                added += 1
        save_data(data)
        await update.message.reply_text(
            mood_wrap(f"{added} پاسخ برای «{lk}» ذخیره شد.", data["mode"])
        )
        return

    # پاسخ بر اساس چیزهای یادگرفته
    ans = pick_reply(txt, data)
    if not ans:
        # اگر یادگیری فعاله، یک پاسخِ پایه تولید و ذخیره کن
        if data["learning"]:
            seed = [
                "خب که چی؟", "جالبه!", "باشه دیدم.", "باشه noted.", "اوکی گرفتم.",
                "عه این خوب بود.", "درباره‌ش فکر می‌کنم.", "باشه ذخیره شد."
            ]
            base = random.choice(seed)
            data["replies"].setdefault(txt, []).append(base)
            save_data(data)
            ans = base
        else:
            return
    await update.message.reply_text(mood_wrap(ans, data["mode"]))

# ---------------------- ارسال همگانی ----------------------
async def do_broadcast(context: ContextTypes.DEFAULT_TYPE, text: str):
    data = load_data()
    sent, failed = 0, 0
    for chat_id in list(data["groups"].keys()):
        try:
            await context.bot.send_message(chat_id=int(chat_id), text=mood_wrap(text, data["mode"]))
            sent += 1
        except Exception:
            failed += 1
    await context.bot.send_message(chat_id=SUDO_ID, text=f"ارسال شد ✅ {sent} | ناموفق ❌ {failed}")

# ---------------------- لفت بده ----------------------
async def leave_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("فقط مدیر اصلی می‌تواند من را خارج کند.")
    if update.effective_chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        await update.message.reply_text("باشه من رفتم! 😂✌️")
        await context.bot.leave_chat(update.effective_chat.id)
    else:
        await update.message.reply_text("این دستور مخصوص گروه‌هاست.")

# ---------------------- پیام خوش‌آمد ربات ----------------------
async def on_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upd: ChatMemberUpdated = update.my_chat_member
    if not upd:
        return
    new = upd.new_chat_member.status
    chat = upd.chat
    if new in ("member", "administrator"):
        data = load_data()
        data["groups"][str(chat.id)] = {"title": chat.title or str(chat.id)}
        save_data(data)
        try:
            await context.bot.send_message(chat.id, human_join_msg(chat.title or "این‌جا"))
        except Exception:
            pass

# ---------------------- شوخی خودکار ساعتی ----------------------
JOKES = [
    "می‌دونستی خندیدن کالری می‌سوزونه؟ پس با من لاغر شو 😂",
    "زندگی کوتاهه؛ تا می‌تونی بخند 😜",
    "می‌خواستم کاریزما داشته باشم، یادم رفت شارژش کنم 🤖",
    "من خنگولم؛ ولی باهوشِ شما رو دوست دارم 😎",
    "یکی گفت جدی باش؛ گفتم بعداً! الان وقته خندست 🤡",
]

async def hourly_jokes(context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    for chat_id in list(data["groups"].keys()):
        try:
            msg = mood_wrap(random.choice(JOKES), data["mode"])
            await context.bot.send_message(chat_id=int(chat_id), text=msg)
        except Exception:
            pass

# ---------------------- راه‌اندازی برنامه ----------------------
def main():
    if not TOKEN:
        raise SystemExit("BOT_TOKEN تنظیم نشده است.")

    app = ApplicationBuilder().token(TOKEN).build()

    # دستورات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("leave", leave_cmd))

    # پیام‌های متنی + دستورات طبیعی
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    # پنل
    app.add_handler(CallbackQueryHandler(on_callback))

    # پیوستن ربات به گروه
    app.add_handler(ChatMemberHandler(on_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))

    # شوخی ساعتی
    app.job_queue.run_repeating(hourly_jokes, interval=timedelta(hours=1), first=timedelta(minutes=5))

    print("🤖 Khengool v5.5 started ...")
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
