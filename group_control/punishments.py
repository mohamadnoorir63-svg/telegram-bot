import os
import json
import re
import asyncio
from telegram import Update, ChatPermissions, MessageEntity
from telegram.ext import ContextTypes, MessageHandler, filters
from datetime import timedelta, datetime

# ================= ⚙️ Grundeinstellungen =================
BASIS_VERZEICHNIS = os.path.dirname(os.path.abspath(__file__))
WARN_DATEI = os.path.join(BASIS_VERZEICHNIS, "warnings.json")
BENUTZERDEFINIERTE_BEFEHLE_DATEI = os.path.join(BASIS_VERZEICHNIS, "custom_commands.json")
SUDO_IDS = [8588347189]

# Erstelle Dateien falls sie nicht existieren
for datei in (WARN_DATEI, BENUTZERDEFINIERTE_BEFEHLE_DATEI):
    if not os.path.exists(datei):
        with open(datei, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

# ================= 🔧 JSON-Helfer =================
def lade_json(datei):
    try:
        with open(datei, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def speichere_json(datei, daten):
    with open(datei, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)

# ================= 🔐 Zugriff prüfen =================
async def hat_zugriff(context, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_IDS:
        return True
    try:
        mitglied = await context.bot.get_chat_member(chat_id, user_id)
        return mitglied.status in ("creator", "administrator")
    except:
        return False

# ================= 🔧 Ziel auflösen =================
async def loese_ziel(msg, context, chat_id):
    if msg.reply_to_message:
        return msg.reply_to_message.from_user, None

    text = msg.text or ""
    entities = msg.entities or []

    for ent in entities:
        try:
            if ent.type == MessageEntity.TEXT_MENTION:
                return ent.user, None
            if ent.type == MessageEntity.MENTION:
                start, laenge = ent.offset, ent.length
                username = text[start:start + laenge].lstrip("@")
                try:
                    cm = await context.bot.get_chat_member(chat_id, username)
                    return cm.user, None
                except:
                    return None, username
        except:
            continue

    einfache_mention = re.search(r"@([A-Za-z0-9_]{5,32})", text)
    if einfache_mention:
        username = einfache_mention.group(1)
        try:
            cm = await context.bot.get_chat_member(chat_id, username)
            return cm.user, None
        except:
            return None, username

    m = re.search(r"\b(\d{6,15})\b", text)
    if m:
        try:
            ziel_id = int(m.group(1))
            cm = await context.bot.get_chat_member(chat_id, ziel_id)
            return cm.user, None
        except:
            return None, None

    return None, None

# ================= 📦 Temporäre Nachrichten =================
async def sende_temp(msg, text, context, loesche_nach=10):
    gesendet = await msg.reply_text(text)
    asyncio.create_task(loesche_nach_zeit(gesendet, loesche_nach, context))

async def loesche_nach_zeit(nachricht, sekunden, context):
    await asyncio.sleep(sekunden)
    try:
        await context.bot.delete_message(nachricht.chat.id, nachricht.message_id)
    except:
        pass

# ================= 🔧 Haupt-Handler =================
async def bestrafen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nachricht = update.effective_message
    benutzer = update.effective_user
    chat = update.effective_chat

    if not nachricht or chat.type not in ("group", "supergroup"):
        return

    text = (nachricht.text or "").strip()
    if not text:
        return

    # ---------------- Benutzerdefinierten Befehl hinzufügen ----------------
    if text.startswith("دستور جدید") or text.startswith("افزودن دستور"):
        if not await hat_zugriff(context, chat.id, benutzer.id):
            return
        match = re.match(
            r"^(?:دستور جدید|افزودن دستور)\s+(.+?)\s+(افزودن‌مدیر|حذف‌مدیر)\s+(.+)$", text
        )
        if not match:
            await sende_temp(
                nachricht,
                "📘 فرمت درست:\n<code>افزودن دستور [نام دستور] [افزودن‌مدیر|حذف‌مدیر] [متن پاسخ]</code>",
                context,
            )
            return
        name, befehl_typ, antwort = match.groups()
        alle_befehle = lade_json(BENUTZERDEFINIERTE_BEFEHLE_DATEI)
        chat_schluessel = str(chat.id)
        chat_befehle = alle_befehle.get(chat_schluessel, {})
        if name in chat_befehle:
            await sende_temp(nachricht, "⚠️ این نام قبلاً تعریف شده.", context)
            return
        chat_befehle[name] = {"typ": befehl_typ, "text": antwort}
        alle_befehle[chat_schluessel] = chat_befehle
        speichere_json(BENUTZERDEFINIERTE_BEFEHLE_DATEI, alle_befehle)
        await sende_temp(nachricht, f"✅ دستور جدید <b>{name}</b> ثبت شد.", context)
        return

    # ---------------- Benutzerdefinierten Befehl ausführen ----------------
    alle_befehle = lade_json(BENUTZERDEFINIERTE_BEFEHLE_DATEI)
    chat_schluessel = str(chat.id)
    chat_befehle = alle_befehle.get(chat_schluessel, {})
    if text in chat_befehle:
        befehl_info = chat_befehle[text]
        ziel, fehlgeschlagen = await loese_ziel(nachricht, context, chat.id)
        if fehlgeschlagen or not ziel:
            return
        if ziel.id == context.bot.id:
            await sende_temp(nachricht, "😅 من ربات هستم!", context)
            return
        if ziel.id in SUDO_IDS:
            await sende_temp(nachricht, "👑 این کاربر سودو است.", context)
            return
        t_mitglied = await context.bot.get_chat_member(chat.id, ziel.id)
        if t_mitglied.status in ("creator", "administrator"):
            await sende_temp(nachricht, "🛡 امکان اجرای دستور روی این کاربر وجود ندارد.", context)
            return
        try:
            if befehl_info["typ"] == "افزودن‌مدیر":
                await context.bot.promote_chat_member(
                    chat.id, ziel.id,
                    can_delete_messages=True,
                    can_restrict_members=True,
                    can_invite_users=True,
                    can_pin_messages=True,
                    can_manage_topics=True
                )
            elif befehl_info["typ"] == "حذف‌مدیر":
                await context.bot.promote_chat_member(
                    chat.id, ziel.id,
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
            text_ausgabe = befehl_info.get("text", "").replace("{name}", ziel.first_name)
            await sende_temp(nachricht, text_ausgabe or "✅ عملیات انجام شد.", context)
        except:
            return
        return

    # ---------------- Nur persische Befehle ----------------
    BEFEHL_MUSTER = {
        "ban": [r"^بن(?:\s+|$)"],
        "unban": [r"^حذف\s*بن(?:\s+|$)"],
        "mute": [r"^سکوت(?:\s+|$)"],
        "unmute": [r"^حذف\s*سکوت(?:\s+|$)"],
        "warn": [r"^اخطار(?:\s+|$)"],
        "delwarn": [r"^حذف\s*اخطار(?:\s+|$)"]
    }

    befehl_typ = None
    for b, muster in BEFEHL_MUSTER.items():
        for m in muster:
            if re.match(m, text):
                befehl_typ = b
                break
        if befehl_typ:
            break

    if not befehl_typ:
        return

    if not await hat_zugriff(context, chat.id, benutzer.id):
        return

    ziel, fehlgeschlagen = await loese_ziel(nachricht, context, chat.id)
    if fehlgeschlagen or not ziel:
        return

    if ziel.id == context.bot.id:
        await sende_temp(nachricht, "😅 من ربات هستم — نمی‌توانم تنبیه شوم.", context)
        return
    if ziel.id in SUDO_IDS:
        await sende_temp(nachricht, "🚫 امکان اجرای دستور روی این کاربر وجود ندارد.", context)
        return
    try:
        t_mitglied = await context.bot.get_chat_member(chat.id, ziel.id)
        if t_mitglied.status in ("creator", "administrator"):
            await sende_temp(nachricht, "🛡 امکان اجرای دستور روی این کاربر وجود ندارد.", context)
            return
    except:
        pass

    # ---------------- Hauptbefehle ausführen ----------------
    try:
        if befehl_typ == "ban":
            await context.bot.ban_chat_member(chat.id, ziel.id)
            await nachricht.reply_text(f"🚫 {ziel.first_name} از گروه بن شد.")
        elif befehl_typ == "unban":
            await context.bot.unban_chat_member(chat.id, ziel.id)
            await nachricht.reply_text(f"✅ {ziel.first_name} از بن خارج شد.")
        elif befehl_typ == "mute":
            m = re.search(r"سکوت\s*(\d+)?\s*(ثانیه|دقیقه|ساعت)?", text)
            if m and m.group(1):
                num = int(m.group(1))
                unit = m.group(2)
                if unit == "ساعت":
                    sekunden = num * 3600
                elif unit == "دقیقه":
                    sekunden = num * 60
                elif unit == "ثانیه":
                    sekunden = num
                else:
                    sekunden = num * 60
            else:
                sekunden = 3600
            bis_datum = datetime.utcnow() + timedelta(seconds=sekunden)
            await context.bot.restrict_chat_member(
                chat.id, ziel.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=bis_datum
            )
            await nachricht.reply_text(f"🤐 {ziel.first_name} برای {sekunden} ثانیه سکوت شد.")
        elif befehl_typ == "unmute":
            await context.bot.restrict_chat_member(
                chat.id, ziel.id,
                permissions=ChatPermissions(can_send_messages=True)
            )
            await nachricht.reply_text(f"🔊 {ziel.first_name} از سکوت خارج شد.")
        elif befehl_typ == "warn":
            warns = lade_json(WARN_DATEI)
            schluessel = f"{chat.id}:{ziel.id}"
            warns[schluessel] = warns.get(schluessel, 0) + 1
            speichere_json(WARN_DATEI, warns)
            if warns[schluessel] >= 3:
                await context.bot.ban_chat_member(chat.id, ziel.id)
                warns[schluessel] = 0
                speichere_json(WARN_DATEI, warns)
                await nachricht.reply_text(f"🚫 {ziel.first_name} به‌دلیل ۳ اخطار بن شد.")
            else:
                await nachricht.reply_text(f"⚠️ {ziel.first_name} اخطار {warns[schluessel]}/3 گرفت.")
        elif befehl_typ == "delwarn":
            warns = lade_json(WARN_DATEI)
            schluessel = f"{chat.id}:{ziel.id}"
            if schluessel in warns:
                del warns[schluessel]
                speichere_json(WARN_DATEI, warns)
                await nachricht.reply_text(f"✅ اخطارهای {ziel.first_name} حذف شد.")
    except:
        return

# ================= 🔧 Handler registrieren =================
def registriere_bestrafen_handler(application, gruppen_nummer: int = 12):
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            bestrafen_handler,
        ),
        group=gruppen_nummer,
    )
