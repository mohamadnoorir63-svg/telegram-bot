import random
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

ASK_NAME = 1

# ======================= 🔎 تشخیص فارسی =======================

def is_persian(text: str):
    for ch in text:
        if '\u0600' <= ch <= '\u06FF' or '\u0750' <= ch <= '\u077F' or '\u08A0' <= ch <= '\u08FF':
            return True
    return False


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

    if text.startswith("فونت "):
        name = text.replace("فونت", "").strip()
        return await send_fonts(update, context, name)

    return ConversationHandler.END


# ======================= 🌸 دریافت اسم =======================

async def receive_font_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    return await send_fonts(update, context, name)


# ======================= 🎭 تولید فونت‌های انگلیسی =======================

def apply_style(name, style):
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
    return result

def generate_fonts(name: str, count: int = 240):
    symbols = [
        "◯", "◿", "𖠳", "𖠴", "𖠵", "𖠶", "𖠷", "𖠸", "𖠹", "𖠺", "𖠻", "𖠼", "𖠽", "𖠾", "𖠿",
        "𖡀", "𖡁", "𖡂", "𖡃", "𖡄", "𖡅", "𖡆", "𖡇", "𖡈", "𖡉", "𖡊", "𖡋", "𖡌", "𖡍", "𖡎",
        "❆", "❈", "❉", "❊", "❋", "⏆", "▿", "▾", "⬚", "⁂", "✃", "☆", "✩", "★", "✰", "✯", "✠", "☩",
        "☨", "✙", "✚", "✛", "✜", "✞", "†", "☥", "☓", "♁", "✦", "✧", "✪", "✫", "✬", "✭", "✮", "✯",
        "☾", "☽", "☼", "☻", "♪", "♫", "♬", "✄", "✆", "∞", "♂", "♀", "☿", "▲", "▼", "△", "▽", "◆",
        "◇", "◕", "◔", "ʊ", "ϟ", "ღ", "₪", "✓", "✔️", "✕", "☥", "™", "©", "®", "¿", "¡", "№", "⇨"
    ]

    # تقسیم symbols به گروه‌های پیشوند و پسوند  
    pre_groups = [symbols[i:i+5] for i in range(0, len(symbols), 5)]  
    post_groups = [symbols[i:i+5] for i in range(0, len(symbols), 5)]  

    unicode_styles = [  
        "𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩",  
        "𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃",  
        "ᎯᏰℭⅅ℮ℱᏩℋᏐℐӃℒℳℕᎾ⅌ℚℜᏕƬƲᏉᏔℵᎽℤ",  
        "🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉",  
        "🅐🅑🅒🅓🅔🅕🅖🅗🅘🅙🅚🅛🅜🅝🅞🅟🅠🅡🅢🅣🅤🅥🅦🅧🅨🅩",  
        "𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ",  
        "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭"  
    ]  

    decorated_templates = [  
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
        "♥️⃝⃭𝄞❉্͜͡▪️𒌍꯭🦋⃝⃡.𝅯.𝅰.꯭𝅱.𝅲.꯭𝅱.𝅰.𝅯.𝅮.꯭.{} 𝄞͡،⚛️",  
        "𓄂ꪰ𓁪❥𝄞{}𝄞❥𓀛꯭𓆃ᵐᶠᶰ↬𓃬",  
        "➹‌❬⃟꯭💕꯭‌⃟❭꯭ ꯭꯭‌꯭꯭‌{} ꯭ ❬⃟‌꯭꯭🪽꯭꯭‌⃟❭➹",  
        "𓄂ꪴꪰ❨💎{}❩↬𓃬"
    ]

    fixed_patterns = decorated_templates  # اصلاح شده: استفاده از decorated_templates

    fonts = set()  

    while len(fonts) < count:  
        if random.random() < 0.4:  
            pattern = random.choice(fixed_patterns)  
            style = random.choice(unicode_styles)  
            uname = apply_style(name, style)  
            fonts.add(pattern.format(uname))  
            continue  

        pre = "".join(random.choice(group) for group in pre_groups)  
        post = "".join(random.choice(group) for group in post_groups)  
        style = random.choice(unicode_styles)  
        uname = apply_style(name, style)  
        fonts.add(f"{pre}{uname}{post}")  

    return list(fonts)
        
# ======================= 🎭 فونت فارسی =======================

templates = [
    "{0}ـ {1}ـ {2}ـ {3}",
    "{0}❈ۣۣـ🍁ـ{1}❈ۣۣـ🍁ـ{2}❈ۣۣـ🍁ـ{3}❈ۣۣـ🍁ـ",
    "↜{0}ٍٍـُِ➲ِِனُِ↜ٍٍ{1}ـُِ➲ِِனُِ↜{2}ـُِ➲ِِனُِ↜ٍٍـُِ{3}➲ِِனُِ",
    "]‌‌ـ‌‌ـ{0}‌‌ـ‌‌ـ]‌‌]‌‌ـ‌‌ـ{1}‌‌ـ‌‌ـ]‌‌]‌‌ـ‌‌ـ{2}‌‌ـ‌‌ـ]‌‌]‌‌ـ‌‌ـ{3}ـ‌‌ـ]",
    "{0}ـٰٰـٰٰـפ{1}ـٰٰـٰٰــ{2}ـٰٰـٰٰــ{3}ٍٕ",
    "{0}ؔؑـَؔ ـؔؑـَؔ๛ٖؔ{1}ؔؑـَؔ ـؔؑـَؔ๛ٖؔ{2}ؔؑـَؔ ـؔؑـَؔ๛ٖؔ{3}",
    "{0}ैـ۪ٜـ۪ٜـ۪ٜ❀‌‌ــؒؔؒؔ{1}ैـ۪ٜـ۪ٜـ۪ٜ❀‌‌ــؒؔ{2}ـैـ۪ٜـ۪ٜـ۪ٜ❀‌‌ــؒؔ{3}❀''",
    "{0}‌‌ــ‌‌◕‌‌₰‌‌◚‌‌₰‌‌{1}ـ‌‌ــ‌‌ـ‌‌◕‌‌₰‌‌◚‌‌₰‌‌{2}ـ‌‌ــ‌‌◕‌‌₰‌‌◚‌‌₰‌‌{3}‌‌◕‌‌₰",
    "{0}ــৡৡ{1}ــৡৡ{2}ــৡৡৡ'{3}",
    "{0}ــٍ‌ـۘۘــ{1}ْْـــْْـ{2}ــٍ‌ـۘۘــ{3}ۘۘـ",
    "{0}ــ{1}ــ{2}ّ{3}",
    "{0}ٖؒـؒؔـٰٰـٖٖ{1}ٖؒـؒؔـٰٰـٖٖ{2}ٖؒـؒؔـٰٰـٖٖ{3}ٖؒـؒؔـٰٰـٖٖ",
    "{0}ٰٖـۘۘـــٍٰـ{1}ـٰٖـۘۘـــٍٰـ{2}ـٰٖـۘۘـــٍٰـ{3}ٰٖ",
    "[ِْـ{0}ِْـِْ❉ِْـِْ[ِْـِْ{1}ـِْ❉ِْـِْ[ِْـ{2}ِْـِْ❉ِْـِْ[ِْـِْ{3}ـِْ❉ِْـِْ]",
    "{0}ـٓٓـ{1}◌◌{2}ـٓٓـ{3}◌◌",
    "{0}்்ৡ{1}்்ৡ{2}்்ৡ{3}்்ৡ",
    "{0}ٜ٘ـٍٜـٜۘـٜۘـٍٍـ{1}ـٜٜـٍٍـ{2}ـٜۘـٜٓـٍٜ{3}ـٜ٘ـٍٜ",
    "➤{0}➤{1}➤{2}➤{3}",
    "{0}ًٍʘًٍʘ-{1}ـ{2}-{3}ًٍʘًٍʘ",
    "{0}ـٰٓـًً◑ِّ◑ًً{1}ـٰٓـًً◑ِّ◑ًً{2}ـٰٓـًً◑ِّ◑ًً{3}◑ِّ◑ًً",
    "{0}ٰٖـٰٖ℘ـَ✾ـ{1}ٰٖـٰٖ℘ـَ✾ـ{2}ٰٖـٰٖ℘ـَ✾ـ{3}ٰٖـٰٖ℘ـَ✾ـ",
    "{0}✘{1}✘{2}✘{3}✘",
    "{0}ــؒؔـ{1}ـــؒؔـ{2}ــؒؔـ{3}❁",
    "{0}✓{1}✓{2}✓{3}✓",
    "{0}ــٍؓـٍ۪ـ۪ؔـٍ℘ًً{1}ــٍؓـٍ۪ـ۪ؔـٍ℘ًً{2}ــٍؓـٍ۪ـ۪ؔـٍ℘ًً{3}",
    "{0}ـؒؔـؒؔـ۪۪ـؒؔـؒؔـົ◌ฺ{1}ـؒؔـؒؔـ۪۪ـؒؔـؒؔـົ◌ฺ{2}ـؒؔـؒؔـ۪۪ـؒؔـؒؔـົ◌ฺ{3}✯",
    "{0}ْْـْْـْْ/ْْ{1}ْْـْْـْْـْْ/{2}ْْـْْـْْ/ْْـْْـْْـ{3}ْْ/",
    "{0}ــؕؕـٜٜـٜٜ✿{1}ٜٜــؕؕـٜٜـٜٜ✿{2}ــؕؕـٜٜـٜٜ✿{3}ٜٜ",
    "{0}‌‌ـ‌‌ـ✨{1}]‌‌ـ‌‌ـ‌‌✨{2}‌‌ـ‌‌ـ✨{3}‌‌ـ‌‌ـ✨",
    "{0}ؒؔ◌‌‌ࢪ{1}ــٌ۝ؔؑـެِ{2}◌‌‌ࢪ{3}",
    "{0}﹏{1}﹏{2}﹏{3}",
    "{0}◌ٕؓ※{1}◌ٕؓ※{2}◌ٕؓ※{3}◌ٕؓ※",
    "{0}ًٍـؒؔـؒؔ⸙ؒৡ✪{1}ـًٍـؒؔـؒؔ⸙ؒৡ✪{2}ـًٍـؒؔـؒؔ⸙ؒৡ✪{3}✪",
    "{0}✺{1}✺{2}✺{3}",
    "{0}ـَِ{1}ـَِ{2}ـَِ{3}",
    "{0}ُِ{1}ُِ{2}ُِ{3}",
    "{0}✿{1}✿{2}✿{3}",
    "{0}◎۪۪❖ु{1}◎۪۪❖ु{2}◎۪۪❖ु{3}",
    "{0}‌‌ـ‌‌ـ‌‌✭{1}ـ‌‌ـ‌‌✭{2}‌‌ـ‌‌ـ‌‌✭{3}✭",
    "{0}ٖٖـۘۘ℘{1}ٖٖـۘۘ℘{2}ٖٖـۘۘ℘{3}",
    "{0}ـٜٜঊٌٍـ↯ـٜٜـٍٍـ{1}ـٜٜঊٌٍـ↯ـٜٜـٍٍـ{2}ـٜٜঊٌٍـ↯ـٜٜـٍٍـ{3}ٜٜঊٌٍ",
    # ---------------- قالب‌های جدید اضافه شده ----------------
    "{0}❀⸙{1}⸙❀{2}⸙❀{3}",
    "★{0}★{1}★{2}★{3}★",
    "✧{0}✧{1}✧{2}✧{3}✧",
    "☾{0}☾{1}☾{2}☾{3}☽",
    "❁{0}❁{1}❁{2}❁{3}❁",
    "ღ{0}ღ{1}ღ{2}ღ{3}ღ",
    "✿☯{0}☯✿{1}☯✿{2}☯✿{3}☯",
]

def generate_persian_fonts(name: str):
    results = []
    chars = list(name)

    while len(chars) < 4:
        chars.append(chars[-1])

    a, b, c, d = chars[:4]

    for temp in templates:
        try:
            results.append(temp.format(a, b, c, d))
        except:
            pass

    return results


# ======================= ✨ ارسال فونت =======================

async def send_fonts(update: Update, context: ContextTypes.DEFAULT_TYPE, name: str):

    if is_persian(name):
        fonts = generate_persian_fonts(name)
    else:
        fonts = generate_fonts(name, count=240)

    context.user_data["all_fonts"] = fonts
    context.user_data["font_pages"] = make_pages(name, fonts, page_size=8, max_pages=30)

    pages = context.user_data["font_pages"]
    await update.message.reply_text(
        pages[0]["text"],
        parse_mode="HTML",
        reply_markup=pages[0]["keyboard"]
    )
    return ConversationHandler.END


# ======================= 📄 ساخت صفحات =======================

def make_pages(name: str, fonts: list, page_size=8, max_pages=30):
    pages = []
    total_pages = min((len(fonts) + page_size - 1) // page_size, max_pages)

    for idx in range(total_pages):
        chunk = fonts[idx*page_size : (idx+1)*page_size]
        text = f"<b>↻ {name}</b>\n\n• لیست فونت‌ها:\n"
        keyboard = []

        for i, style in enumerate(chunk, start=1):
            global_index = idx*page_size + (i-1)
            text += f"{i}- {style}\n"
            keyboard.append([InlineKeyboardButton(f"{i}", callback_data=f"send_font_{global_index}")])

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


# ======================= 📋 ارسال گزینه انتخاب‌شده =======================

async def send_selected_font(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    font_id = int(query.data.replace("send_font_", ""))
    all_fonts = context.user_data.get("all_fonts", [])

    if 0 <= font_id < len(all_fonts):
        await query.message.reply_text(all_fonts[font_id])
    else:
        await query.message.reply_text("❗ فونت پیدا نشد.")


# ======================= 🔁 ناوبری =======================

async def next_font(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    index = int(query.data.replace("next_font_", ""))
    pages = context.user_data.get("font_pages", [])

    if 0 <= index < len(pages):
        await query.edit_message_text(
            pages[index]["text"],
            parse_mode="HTML",
            reply_markup=pages[index]["keyboard"]
        )


async def prev_font(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    index = int(query.data.replace("prev_font_", ""))
    pages = context.user_data.get("font_pages", [])

    if 0 <= index < len(pages):
        await query.edit_message_text(
            pages[index]["text"],
            parse_mode="HTML",
            reply_markup=pages[index]["keyboard"]
        )


# ======================= 🎛 بازگشت =======================

async def feature_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        await query.message.delete()
    except:
        pass
    return ConversationHandler.END
