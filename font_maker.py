# ======================= 💎 خنگول فونت‌مستر 13.7 — Persian Power Edition =======================
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def font_maker(update, context):
    text = update.message.text.strip()
    if not text.startswith("فونت "):
        return False

    name = text.replace("فونت", "").strip()
    if not name:
        return await update.message.reply_text("✨ لطفاً بعد از «فونت» نام خودت رو بنویس تا جادوی خنگول شروع شه!")

    # ⚡️ فونت‌های خلاقانه فارسی طراحی‌شده با احساس و استایل
    fonts = [
        f"꧁༺💎 {name} 💎༻꧂",
        f"༒🔥 {name} 🔥༒",
        f"❖✨ {name} ✨❖",
        f"♛『 {name} 』♛",
        f"꧁𓊈𒆜 {name} 𒆜𓊉꧂",
        f"🌙✧ {name} ✧🌙",
        f"🕯️༺ {name} ༻🕯️",
        f"💞⟆ {name} ⟅💞",
        f"☯️⌜ {name} ⌟☯️",
        f"🩷✦ {name} ✦🩷",
        f"💠༒ {name} ༒💠",
        f"⚜️‹ {name} ›⚜️",
        f"✨ꕥ {name} ꕥ✨",
        f"🌺⊱•⩊•⊰ {name} ⊱•⩊•⊰🌺",
        f"🔥『 {name} 』🔥",
        f"💫༼ {name} ༽💫",
        f"🪷⋆ {name} ⋆🪷",
        f"🌈﹏ {name} ﹏🌈",
        f"💀☠️ {name} ☠️💀",
        f"🌹❖ {name} ❖🌹",
        f"✨⊰ {name} ⊱✨",
        f"🧿══『 {name} 』══🧿",
        f"💎꧁ {name} ꧂💎",
        f"🌙⋆｡°✩ {name} ✩°｡⋆🌙",
        f"⚡ 『 {name.upper()} 』 ⚡",
        f"🎭︵‿︵‿୨♡୧‿︵‿︵🎭\n{name}\n🎭︵‿︵‿୨♡୧‿︵‿︵🎭",
        f"🕊️☾ {name} ☽🕊️",
        f"💞╰☆☆ {name} ☆☆╮💞",
        f"🌠《 {name} 》🌠",
        f"💫•° {name} °•💫",
        f"🎇⟆ {name} ⟅🎇",
        f"🌸『💖 {name} 💖』🌸",
        f"🩵❋ {name} ❋🩵",
        f"🕯️✶ {name} ✶🕯️",
        f"✨⟪ {name} ⟫✨",
        f"🌻꧁༒☬ {name} ☬༒꧂🌻",
        f"💎⟬ {name} ⟭💎",
        f"🌺✦ {name} ✦🌺",
        f"♛🩶 {name} 🩶♛",
        f"🔥⧽ {name} ⧼🔥",
    ]

    selected_fonts = random.sample(fonts, 10)
    prefix = random.choice(["💫", "✨", "🌙", "🔥", "💎", "🩷", "🌸", "🕊️"])
    suffix = random.choice(["🌈", "⚜️", "💖", "🌠", "💐", "⭐", "🌺"])

    result = f"{prefix} <b>فونت‌های خاص و حرفه‌ای برای</b> <i>{name}</i> {suffix}\n\n"
    for i, style in enumerate(selected_fonts, start=1):
        result += f"{i}️⃣ <code>{style}</code>\n\n"

    result += "🔁 برای فونت‌های جدید، دوباره بنویس: <b>فونت اسم‌ت</b>"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 فونت‌های جدید", callback_data=f"next_font:{name}")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="feature_back")]
    ])

    await update.message.reply_text(result, parse_mode="HTML", reply_markup=keyboard)
    return True


# ======================= 🔁 دکمه تولید فونت جدید =======================
async def next_font(update, context):
    query = update.callback_query
    await query.answer()
    name = query.data.split(":")[1]
    fake_update = type("FakeUpdate", (), {"message": query.message})
    fake_update.message.text = f"فونت {name}"
    await font_maker(fake_update, context)
