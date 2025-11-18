import random
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

ASK_NAME = 1
ASK_DECOR = 2

# ======================= 🎨 تابع اصلی =======================
async def font_maker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_type = update.effective_chat.type

    if chat_type in ["group", "supergroup"]:
        msg = await update.message.reply_text(
            "✨ لطفاً برای ساخت فونت، به پیوی ربات مراجعه کنید 🙏"
        )
        await asyncio.sleep(6)
        try:
            await msg.delete()
            await update.message.delete()
        except:
            pass
        return ConversationHandler.END

    if text == "فونت":
        await update.message.reply_text("🌸 چه اسمی رو برات فونت کنم؟")
        return ASK_NAME

    if text == "فونت تزئینی":
        await update.message.reply_text("🌸 اسم و کاراکترهای تزئینی دلخواهت رو وارد کن (مثلاً 🌸❖♡)؟")
        return ASK_DECOR

    if text.startswith("فونت "):
        name = text.replace("فونت", "").strip()
        return await send_fonts(update, context, name)

    return ConversationHandler.END

# ======================= 🌸 دریافت اسم =======================
async def receive_font_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    return await send_fonts(update, context, name)

# ======================= 🎨 دریافت کاراکترهای دلخواه =======================
async def receive_decor_chars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if " " in text:
        # فرض کنیم فرمت: اسم + فاصله + کاراکترها
        parts = text.split(" ", 1)
        name, decor = parts[0], parts[1]
    else:
        name, decor = text, ""
    context.user_data["decor_chars"] = list(decor)
    return await send_fonts(update, context, name)

# ======================= 💎 ارسال فونت‌ها =======================
async def send_fonts(update: Update, context: ContextTypes.DEFAULT_TYPE, name: str):
    decor = context.user_data.get("decor_chars", [])
    fonts = generate_fonts(name, decor=decor, count=240)  # 30 صفحه × 8 فونت
    context.user_data["all_fonts"] = fonts
    context.user_data["font_pages"] = make_pages(name, fonts, page_size=8, max_pages=30)

    pages = context.user_data["font_pages"]
    await update.message.reply_text(
        pages[0]["text"],
        parse_mode="HTML",
        reply_markup=pages[0]["keyboard"]
    )
    return ConversationHandler.END

# ======================= 🎨 تابع کمکی جایگزینی استایل =======================
def apply_style(name, style, decor=None):
    decor = decor or []
    result = ""
    for ch in name:
        if ch.lower() in "abcdefghijklmnopqrstuvwxyz":
            idx = ord(ch.lower()) - 97
            if isinstance(style, str):
                if idx < len(style):
                    result += style[idx]
                else:
                    result += ch
            elif isinstance(style, list):
                if idx < len(style):
                    result += style[idx]
                else:
                    result += ch
        else:
            result += ch
        if decor and random.random() < 0.3:
            result += random.choice(decor)  # اضافه کردن کاراکتر تزئینی بین حروف
    return result

# ======================= 🎭 تولید فونت‌های حرفه‌ای =======================
def generate_fonts(name: str, decor=None, count: int = 240):
    pre_groups = [
        ["𓄂","𓃬","𓋥","𓄼","𓂀","𓅓"],
        ["ꪰ","ꪴ","𝄠","𝅔","꧁","꧂","ꕥ"],
        ["⚝","☬","☾","☽","★","✦","✧"]
    ]
    post_groups = [
        ["✿","♡","❖","░","❋","☯","❂"],
        ["✧","✦","❂","★","✺","✶","✸"],
        ["⋆","⟡","❋","•","✾","✢","✤"]
    ]

    unicode_styles = [
        "𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩",
        "𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃",
        "ᎯᏰℭⅅ℮ℱᏩℋᏐℐӃℒℳℕᎾ⅌ℚℜᏕƬƲᏉᏔℵᎽℤ",
        "🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉",
        "🅐🅑🅒🅓🅔🅕🅖🅗🅘🅙🅚🅛🅜🅝🅞🅟🅠🅡🅢🅣🅤🅥🅦🅧🅨🅩",
        "ⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏ",
        "𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ",
        "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭",
        ["𓂀","ꕥ","⚝","【","】","ᴄ","❖","★","⋆"],
        ["𓄼","ꕥ","✦","Ⓜ","Ⓞ","Ⓗ","Ⓐ","Ⓜ","Ⓜ","Ⓐ","Ⓓ","❂","✦","❋"]
    ]

    fixed_patterns = [
        "۝ؔؑ❁➹‌❬⃟꯭({})꯭꯭‌⃟❭➹❁۝ؔؑ",
        "𓄂{}𓆃",
        "【♫❀꯭͞༄꯭͞𝄞_{}___❀꯭͞͞༄꯭͞𝄞",
        "⋆𝅦𝆉𓄂ꪰ☾︎⃝꯭🪩{}◆⃝🪩",
        "ـ‌‌ـ‌‌‌༊‌꯭ـ{}🐲ـ‌‌ـ‌‌‌‌‌༊‌꯭ـ",
        "┏┅┅🌸⃝⃭.  {}🌸⃝⃭❤━┅┅┓",
        " ᷤ‌‌➠🌼⃟🍃{}✿⃟⃘݊💞",
        "𝄟♔꯭⃮⃝⃮ 🦋 ꯭⃝⃮ ☾︎⃝ 𓄂{}𓆃☾︎⃝⋆♔꯭⃮⃝⃮ 🦋 ꯭⃝⃮ 𝄟",
        "𓋜𔘓❀{}❀𔒝",
        "🎀ꕥ✧»{}«✧ꕥ🎀",
    ]

    fonts = set()

    while len(fonts) < count:
        if random.random() < 0.4:
            pattern = random.choice(fixed_patterns)
            style = random.choice(unicode_styles)
            uname = apply_style(name, style, decor=decor)
            fonts.add(pattern.format(uname))
            continue

        pre = "".join(random.choice(group) for group in pre_groups)
        post = "".join(random.choice(group) for group in post_groups)
        style = random.choice(unicode_styles)
        uname = apply_style(name, style, decor=decor)
        fonts.add(f"{pre}{uname}{post}")

    return list(fonts)

# ======================= 📄 ساخت صفحات پویا =======================
def make_pages(name: str, fonts: list, page_size=8, max_pages=30):
    pages = []
    total_pages = min((len(fonts) + page_size - 1) // page_size, max_pages)

    for idx in range(total_pages):
        chunk = fonts[idx*page_size : (idx+1)*page_size]
        text = f"**↻ {name} ⇦**\n:• لیست فونت های پیشنهادی :\n"
        keyboard = []

        for i, style in enumerate(chunk, start=1):
            global_index = idx*page_size + (i-1)
            text += f"{i}- {style}\n"
            keyboard.append([InlineKeyboardButton(f"{i}- {style}", callback_data=f"send_font_{global_index}")])

        text += f"\n📄 صفحه {idx+1} از {total_pages}"

        nav = []
        if idx > 0:
            nav.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"prev_font_{idx-1}"))
        if idx < total_pages - 1:
            nav.append(InlineKeyboardButton("➡️ بعدی", callback_data=f"next_font_{idx+1}"))
        if nav:
            keyboard.append(nav)
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="feature_back")])

        pages.append({"text": text, "keyboard": InlineKeyboardMarkup(keyboard)})

    return pages
