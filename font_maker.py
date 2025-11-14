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

# ======================= 🎭 تولید فونت‌های شلوغ و فانتزی =======================
def generate_fonts(name):
    # ---------------- مجموعه گسترده نمادها ----------------
    fancy_symbols = [
        "𓄂", "𓃬", "𓆃", "𓋥", "ꪰ", "ꪴ", "𝅔", "𝆭", "⸨", "⸩", "༒", "⚝", "☬", "❁", "☾", "☽",
        "✿", "♡", "░", "❖", "★", "✧", "✦", "❂", "✺", "⋆", "⟡", "❋", "•", "★", "♛", "♚", "☯", "⚡",
        "🜂", "🜄", "🜃", "🜁", "✪", "✯", "✰", "☘", "⚜", "✵", "☀", "☁", "☂", "☃", "☄"
    ]

    # ---------------- فونت فارسی ----------------
    farsi_fonts = [f"{random.choice(fancy_symbols)} {name} {random.choice(fancy_symbols)}" for _ in range(25)]
    farsi_fonts += [
        f"『{name}』", f"〘{name}〙", f"⌜{name}⌝", f"•{name}•", f"{name}ــ",
        f"︵‿︵‿︵‿{name}", f"𓆩♡𓆪 {name} 𓆩♡𓆪"
    ]

    # ---------------- فونت انگلیسی ----------------
    english_styles = [
        ("𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝑾𝑿𝒀𝒁", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        ("𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        ("𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        ("🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉", "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    ]

    english_fonts = []
    for uni, orig in english_styles:
        trans = str.maketrans(orig + orig.lower(), uni + orig.lower())
        translated = name.translate(trans)
        for _ in range(5):
            sym1 = random.choice(fancy_symbols)
            sym2 = random.choice(fancy_symbols)
            english_fonts.append(f"{sym1}{translated}{sym2}")
            english_fonts.append(f"{translated}{sym2}")
        english_fonts.append(translated)

    # ---------------- ترکیب و شلوغ سازی ----------------
    all_fonts = farsi_fonts + english_fonts
    random.shuffle(all_fonts)

    # ---------------- تقسیم به صفحات ----------------
    return make_pages(name, all_fonts, page_size=10, max_pages=5)

# ======================= 📄 تقسیم فونت‌ها به صفحات با دکمه کپی =======================
def make_pages(name, all_fonts, page_size=10, max_pages=5):
    pages = []
    chunks = [all_fonts[i:i + page_size] for i in range(0, len(all_fonts), page_size)]
    if len(chunks) > max_pages:
        chunks = chunks[:max_pages]

    for idx, chunk in enumerate(chunks):
        text = f"<b>↻ {name} ⇦</b>\n:• لیست فونت های پیشنهادی :\n"
        keyboard = []

        for i, style in enumerate(chunk, start=1):
            text += f"{i}- {style}\n"
            # دکمه کپی فوری
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

# ======================= 🔁 هندلر صفحات بعدی و قبلی =======================
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
