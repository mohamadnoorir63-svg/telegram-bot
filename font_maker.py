import random
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

ASK_NAME = 1

# ======================= 🎨 تابع اصلی =======================
async def font_maker(update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_type = update.effective_chat.type

    if chat_type in ["group", "supergroup"]:
        msg = await update.message.reply_text("✨ لطفاً برای ساخت فونت، به پیوی ربات مراجعه کنید 🙏")
        await asyncio.sleep(6)
        try:
            await msg.delete()
            await update.message.delete()
        except Exception as e:
            if "message to be replied not found" not in str(e).lower():
                print(f"⚠️ خطا در حذف پیام: {e}")
        return ConversationHandler.END

    if text.strip() == "فونت":
        await update.message.reply_text("🌸 چه اسمی رو برات فونت کنم؟")
        return ASK_NAME

    if text.startswith("فونت "):
        name = text.replace("فونت", "").strip()
        return await send_fonts(update, context, name)

    return ConversationHandler.END

# ======================= 🌸 دریافت اسم کاربر =======================
async def receive_font_name(update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("❗ لطفاً یه اسم بنویس تا فونت بسازم.")
        return ASK_NAME
    return await send_fonts(update, context, name)

# ======================= 💎 ارسال فونت‌ها =======================
async def send_fonts(update, context, name):
    fonts = generate_fonts(name)
    context.user_data["font_pages"] = fonts
    context.user_data["font_index"] = 0

    if fonts:
        await update.message.reply_text(
            fonts[0]["text"],
            parse_mode="HTML",
            reply_markup=fonts[0]["keyboard"]
        )
    return ConversationHandler.END

# ======================= 🎭 تولید فونت‌های خفن =======================
def generate_fonts(name):
    # ================= نمادهای قبل و بعد اسم =================
    symbols = [
        "𓄂","𓃬","𓆃","𓋥","ꪰ","ꪴ","𝄠","𝅔","⚝","☬","❁","☾","☽",
        "✿","♡","░","❖","★","✧","✦","❂","✺","⋆","⟡","❋","•","♛","♚","☯","⚡",
        "🜂","🜄","🜃","🜁","✪","✯","✰","☘","⚜","✵","☀","☁","☂","☃","☄","❨","❩",
        "⃘","۪","ٜ","♕","𝄠","༒","⸨","⸩","❀","✧✧","☽☾","❖❖","★✦","✺✿","⚝⚝",
        "𓋥𓄂","𓃬𓆃","ꪰ𓄂","ꪴ𓃬"
    ]

    # ================= فونت یونیکد =================
    unicode_styles = [
        ("🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉"
         "🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉",
         "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"),
        ("𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩"
         "𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃")
    ]

    fonts = []
    for _ in range(50):
        # ---------------- نماد قبل و بعد اسم ----------------
        pre = "".join(random.choices(symbols, k=random.randint(3,5)))
        post = "".join(random.choices(symbols, k=random.randint(3,5)))

        # ---------------- فونت کل اسم ----------------
        style = random.choice(unicode_styles)
        trans = str.maketrans(style[1], style[0])
        uname = name.translate(trans)

        # ---------------- ترکیب نهایی ----------------
        final_font = f"{pre}{uname}{post}"
        fonts.append(final_font)

    return make_pages(name, fonts, page_size=10, max_pages=5)

# ======================= 📄 تقسیم فونت‌ها به صفحات =======================
def make_pages(name, fonts, page_size=10, max_pages=5):
    pages = []
    chunks = [fonts[i:i + page_size] for i in range(0, len(fonts), page_size)]
    if len(chunks) > max_pages:
        chunks = chunks[:max_pages]

    for idx, chunk in enumerate(chunks):
        text = f"<b>↻ {name} ⇦</b>\n:• لیست فونت های پیشنهادی :\n"
        keyboard = []

        for i, style in enumerate(chunk, start=1):
            text += f"{i}- {style}\n"
            keyboard.append([InlineKeyboardButton(f"📋 کپی {i}", callback_data=f"copy_font:{style}")])

        text += f"\n📄 صفحه {idx + 1} از {len(chunks)}"

        nav_buttons = []
        if idx > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"prev_font:{idx - 1}"))
        if idx < len(chunks) - 1:
            nav_buttons.append(InlineKeyboardButton("➡️ بعدی", callback_data=f"next_font:{idx + 1}"))

        keyboard.append(nav_buttons)
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="feature_back")])

        pages.append({
            "text": text,
            "keyboard": InlineKeyboardMarkup(keyboard)
        })

    return pages

# ======================= 🔁 هندلر دکمه کپی =======================
async def copy_font(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    font_text = query.data.split(":", 1)[1]
    await query.message.reply_text(f"📋 فونت کپی شد:\n{font_text}")

# ======================= 🔁 هندلر صفحات =======================
async def next_font(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    index = int(query.data.split(":")[1])
    fonts = context.user_data.get("font_pages", [])
    if 0 <= index < len(fonts):
        await query.edit_message_text(
            fonts[index]["text"],
            parse_mode="HTML",
            reply_markup=fonts[index]["keyboard"]
        )

async def prev_font(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    index = int(query.data.split(":")[1])
    fonts = context.user_data.get("font_pages", [])
    if 0 <= index < len(fonts):
        await query.edit_message_text(
            fonts[index]["text"],
            parse_mode="HTML",
            reply_markup=fonts[index]["keyboard"]
        )
