# command_manager.py
import os
import json
import random
import shutil
import zipfile
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional

from telegram import Update, InputFile
from telegram.ext import ContextTypes

# ====== تنظیمات ======
ADMIN_ID = 8588347189

# مسیر پایه (فایل در همان پوشه‌ای است که این ماژول قرار دارد)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# دایرکتوری داده‌ها و بکاپ‌ها (طبق خواست شما همه داخل data ذخیره می‌شوند)
DATA_DIR = os.path.join(BASE_DIR, "data")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
COMMANDS_MEDIA_DIR = os.path.join(DATA_DIR, "commands_media")
FORTUNES_MEDIA_DIR = os.path.join(DATA_DIR, "fortunes_media")
JOKES_MEDIA_DIR = os.path.join(DATA_DIR, "jokes_media")
GROUP_CONTROL_DIR = os.path.join(DATA_DIR, "group_control")

# فایل‌ها
DATA_FILE = os.path.join(DATA_DIR, "custom_commands.json")
BACKUP_FILE = os.path.join(BACKUP_DIR, "custom_commands_backup.json")

# پوشه‌ها لازم رو درست کن
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(COMMANDS_MEDIA_DIR, exist_ok=True)
os.makedirs(FORTUNES_MEDIA_DIR, exist_ok=True)
os.makedirs(JOKES_MEDIA_DIR, exist_ok=True)
os.makedirs(GROUP_CONTROL_DIR, exist_ok=True)

# اگر فایل دستورها وجود نداشت، بساز
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)
    print(f"[command_manager] created new data file: {DATA_FILE}")
else:
    print(f"[command_manager] data file exists: {DATA_FILE}")

# ================= Cloudinary (اختیاری) =================
USE_CLOUDINARY = False
CLOUDINARY_AVAILABLE = False
CLOUDINARY_RAW_FOLDER = "bot_backups"
try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api

    CLOUDINARY_URL = os.environ.get("CLOUDINARY_URL") or os.environ.get("CLOUDINARY_URI")
    if CLOUDINARY_URL:
        cloudinary.config(cloudinary_url=CLOUDINARY_URL, secure=True)
        CLOUDINARY_AVAILABLE = True
        USE_CLOUDINARY = True
        print("[command_manager] Cloudinary configured.")
    else:
        print("[command_manager] CLOUDINARY_URL not set — Cloudinary disabled.")
except Exception as e:
    CLOUDINARY_AVAILABLE = False
    USE_CLOUDINARY = False
    print(f"[command_manager] cloudinary not available: {e}")

# ================= توابع کمکی =================
def _load_json(path: str, default: Any = None):
    if default is None:
        default = {}
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # اگر خواندن شکست خورد، بازنویسی کن با default
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default

def _save_json(path: str, data: Any):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def load_commands() -> Dict[str, Any]:
    return _load_json(DATA_FILE, {})

def save_commands_local(data: Dict[str, Any]):
    # بکاپ ساده محلی: نسخه پشتیبان قبل از نوشتن
    try:
        if os.path.exists(DATA_FILE):
            shutil.copy2(DATA_FILE, BACKUP_FILE)
    except Exception as e:
        print(f"[command_manager] local backup copy failed: {e}")
    _save_json(DATA_FILE, data)

async def upload_json_backup_to_cloud():
    """اگر Cloudinary فعال است، فایل JSON را به‌عنوان raw آپلود کن (برای پایداری)."""
    if not USE_CLOUDINARY:
        return False, "cloudinary disabled"
    try:
        # آپلود مستقیم از رشته JSON (ساخت یک فایل موقت)
        data = load_commands()
        with tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False, suffix=".json") as tf:
            json.dump(data, tf, ensure_ascii=False, indent=2)
            tf.flush()
            tmp_path = tf.name

        res = cloudinary.uploader.upload(
            tmp_path,
            resource_type="raw",
            folder=CLOUDINARY_RAW_FOLDER,
            use_filename=True,
            unique_filename=False,
            overwrite=True
        )
        try:
            os.remove(tmp_path)
        except:
            pass
        print(f"[command_manager] uploaded JSON backup to cloud: {res.get('public_id')}")
        return True, res
    except Exception as e:
        print(f"[command_manager] failed to upload json to cloud: {e}")
        return False, str(e)

async def backup_local_zip():
    """ایجاد یک zip محلی از پوشه data و ذخیره در backups (برای مشاهده محلی)"""
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    zip_name = os.path.join(BACKUP_DIR, f"commands_backup_{now}.zip")
    try:
        with zipfile.ZipFile(zip_name, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(DATA_DIR):
                for file in files:
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, DATA_DIR)
                    z.write(full_path, arcname)
        print(f"[command_manager] local zip backup created: {zip_name}")
        return zip_name
    except Exception as e:
        print(f"[command_manager] failed to create zip backup: {e}")
        return None

async def maybe_upload_zip_to_cloud(zip_path: str):
    if not USE_CLOUDINARY or not zip_path:
        return False, "cloud disabled or no zip"
    try:
        res = cloudinary.uploader.upload(
            zip_path,
            resource_type="raw",
            folder=CLOUDINARY_RAW_FOLDER,
            use_filename=True,
            unique_filename=False,
            overwrite=True
        )
        print(f"[command_manager] uploaded zip to cloud: {res.get('public_id')}")
        return True, res
    except Exception as e:
        print(f"[command_manager] failed to upload zip: {e}")
        return False, str(e)

def _make_media_filename(base_name: str, ext: str):
    ts = int(datetime.now().timestamp())
    safe = reify_filename(base_name)
    return f"{safe}_{ts}{ext}"

def reify_filename(s: str) -> str:
    # ساده‌سازی اسم برای filename
    return "".join(c for c in s if c.isalnum() or c in ("-", "_")).strip()[:60] or "file"

# ================= ذخیره مدیا: آپلود در Cloudinary در صورت امکان =================
async def store_media_and_get_info(file_obj, filename_hint: str) -> Dict[str, str]:
    """
    file_obj: telegram File object که .download_to_drive(path) قبول می‌کنه
    بازمی‌گرداند دیکشنری شامل: {'url': ..., 'public_id': ..., 'format': ..., 'local_path': ...}
    """
    # دانلود فایل موقت به مسیر محلی
    tmp_filename = os.path.join(COMMANDS_MEDIA_DIR, filename_hint)
    try:
        await file_obj.download_to_drive(tmp_filename)
    except Exception as e:
        print(f"[command_manager] failed to download media: {e}")
        raise

    result = {"local_path": tmp_filename}
    if not USE_CLOUDINARY:
        return result

    try:
        res = cloudinary.uploader.upload(
            tmp_filename,
            resource_type="auto",
            folder="commands_media",
            use_filename=True,
            unique_filename=False,
            overwrite=False
        )
        # حذف محلی بعد از آپلود (اختیاری - بررسی کن که نیاز داری یا نه)
        try:
            os.remove(tmp_filename)
        except:
            pass

        result.update({
            "url": res.get("secure_url") or res.get("url"),
            "public_id": res.get("public_id"),
            "format": res.get("format")
        })
    except Exception as e:
        print(f"[command_manager] cloud upload failed: {e}")
    return result

# ================= API اصلی: save_command, handle_custom_command, delete_command, list_commands, cleanup_group_commands =================

import re  # لازم برای reify_filename که بالاتر ساخته شد

async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ذخیره‌ی دستور با /save <name> روی پیام ریپلای شده.
    اگر پیام شامل مدیا بود، مدیا آپلود می‌شود و لینک در JSON ذخیره می‌شود.
    """
    user = update.effective_user
    chat = update.effective_chat

    if not context.args:
        return await update.message.reply_text("❗ استفاده: /save <نام دستور> (روی پیام ریپلای کنید)")

    name = " ".join(context.args).strip().lower()
    reply = update.message.reply_to_message

    if not reply:
        return await update.message.reply_text("📎 باید روی یک پیام ریپلای کنید.")

    commands = load_commands()
    doc = commands.get(name, {
        "name": name,
        "responses": [],
        "created": datetime.now().isoformat(),
        "group_id": chat.id if chat and chat.type in ["group", "supergroup"] else None,
        "owner_id": user.id
    })

    entry = {}
    # متن ساده
    if reply.text or reply.caption:
        val = (reply.text or reply.caption).strip()
        entry = {"type": "text", "data": val}

    else:
        # عکس
        if reply.photo:
            file = await reply.photo[-1].get_file()
            fname = _make_media_filename(name, ".jpg")
            store_info = await store_media_and_get_info(file, fname)
            entry = {"type": "photo", "data": file.file_id}
            if "url" in store_info:
                entry["cloud_url"] = store_info["url"]
                entry["public_id"] = store_info.get("public_id")
        elif reply.video:
            file = await reply.video.get_file()
            fname = _make_media_filename(name, ".mp4")
            store_info = await store_media_and_get_info(file, fname)
            entry = {"type": "video", "data": file.file_id}
            if "url" in store_info:
                entry["cloud_url"] = store_info["url"]
                entry["public_id"] = store_info.get("public_id")
        elif reply.document:
            file = await reply.document.get_file()
            ext = os.path.splitext(reply.document.file_name or "")[1] or ".dat"
            fname = _make_media_filename(name, ext)
            store_info = await store_media_and_get_info(file, fname)
            entry = {"type": "document", "data": file.file_id, "filename": reply.document.file_name}
            if "url" in store_info:
                entry["cloud_url"] = store_info["url"]
                entry["public_id"] = store_info.get("public_id")
        elif reply.voice:
            file = await reply.voice.get_file()
            fname = _make_media_filename(name, ".ogg")
            store_info = await store_media_and_get_info(file, fname)
            entry = {"type": "voice", "data": file.file_id}
            if "url" in store_info:
                entry["cloud_url"] = store_info["url"]
                entry["public_id"] = store_info.get("public_id")
        elif reply.animation:
            file = await reply.animation.get_file()
            fname = _make_media_filename(name, ".mp4")
            store_info = await store_media_and_get_info(file, fname)
            entry = {"type": "animation", "data": file.file_id}
            if "url" in store_info:
                entry["cloud_url"] = store_info["url"]
                entry["public_id"] = store_info.get("public_id")
        elif reply.sticker:
            file = await reply.sticker.get_file()
            fname = _make_media_filename(name, ".webp")
            store_info = await store_media_and_get_info(file, fname)
            entry = {"type": "sticker", "data": file.file_id}
            if "url" in store_info:
                entry["cloud_url"] = store_info["url"]
                entry["public_id"] = store_info.get("public_id")
        else:
            return await update.message.reply_text("⚠️ نوع این پیام پشتیبانی نمی‌شود.")

    # ذخیره در ساختار
    doc["responses"].append(entry)
    if len(doc["responses"]) > 100:
        doc["responses"].pop(0)
    commands[name] = doc

    # ذخیره محلی و بکاپ
    try:
        save_commands_local(commands)
    except Exception as e:
        print(f"[command_manager] failed to save local: {e}")

    # بکاپ JSON به Cloudinary (اختیاری)
    try:
        if USE_CLOUDINARY:
            await upload_json_backup_to_cloud()
            # و zip محلی و آپلود zip (هر دو اختیاری)
            zip_path = await backup_local_zip()
            if zip_path:
                await maybe_upload_zip_to_cloud(zip_path)
    except Exception as e:
        print(f"[command_manager] backup/upload error: {e}")

    await update.message.reply_text(
        f"✅ پاسخ برای دستور <b>{name}</b> ذخیره شد. ({len(doc['responses'])}/100)",
        parse_mode="HTML"
    )

async def handle_custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اجرای دستور ذخیره‌شده (متن یا مدیا)"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip().lower()
    commands = load_commands()

    if text not in commands:
        return

    cmd = commands[text]
    responses = cmd.get("responses", [])
    if not responses:
        return await update.message.reply_text("⚠️ هنوز پاسخی برای این دستور ثبت نشده.")

    response = random.choice(responses)
    t = response.get("type")
    try:
        if t == "text":
            await update.message.reply_text(response.get("data", ""))
        elif t == "photo":
            # اگر Cloud URL هست ازش استفاده کن، در غیر این صورت فایل_id
            if response.get("cloud_url"):
                await update.message.reply_photo(photo=response["cloud_url"])
            else:
                await update.message.reply_photo(photo=response.get("data"))
        elif t == "video":
            if response.get("cloud_url"):
                await update.message.reply_video(video=response["cloud_url"])
            else:
                await update.message.reply_video(video=response.get("data"))
        elif t == "document":
            if response.get("cloud_url"):
                await update.message.reply_document(document=response["cloud_url"])
            else:
                await update.message.reply_document(document=response.get("data"))
        elif t == "voice":
            if response.get("cloud_url"):
                await update.message.reply_voice(voice=response["cloud_url"])
            else:
                await update.message.reply_voice(voice=response.get("data"))
        elif t == "animation":
            if response.get("cloud_url"):
                await update.message.reply_animation(animation=response["cloud_url"])
            else:
                await update.message.reply_animation(animation=response.get("data"))
        elif t == "sticker":
            # استیکرها معمولاً با file_id فرستاده می‌شوند
            if response.get("data"):
                await update.message.reply_sticker(sticker=response["data"])
            elif response.get("cloud_url"):
                await update.message.reply_sticker(sticker=response["cloud_url"])
        context.user_data["custom_handled"] = True
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در اجرای دستور:\n{e}")

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی اجازه این کار را دارد.")

    if not context.args:
        return await update.message.reply_text("❗ استفاده: /del <نام دستور>")

    name = " ".join(context.args).strip().lower()
    commands = load_commands()

    if name in commands:
        # اگر public_id مدیا وجود داشت، می‌توانیم تلاش کنیم آن را از Cloudinary حذف کنیم (اختیاری)
        try:
            for resp in commands[name].get("responses", []):
                pid = resp.get("public_id")
                if pid and USE_CLOUDINARY:
                    try:
                        cloudinary.uploader.destroy(pid, resource_type="raw")
                    except Exception:
                        pass
        except Exception:
            pass

        del commands[name]
        save_commands_local(commands)
        # آپلود بکاپ جدید
        try:
            if USE_CLOUDINARY:
                await upload_json_backup_to_cloud()
        except:
            pass

        await update.message.reply_text(f"🗑 دستور '{name}' حذف شد.")
    else:
        await update.message.reply_text("⚠️ چنین دستوری وجود ندارد.")

async def list_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ فقط مدیر اصلی مجاز است.")

    commands = load_commands()
    if not commands:
        return await update.message.reply_text("📭 هنوز هیچ دستوری ثبت نشده.")

    txt = "📜 <b>لیست دستورها:</b>\n\n"
    for name, info in commands.items():
        owner = "👑 سودو" if info.get("owner_id") == ADMIN_ID else f"👤 {info.get('owner_id')}"
        group = f" | 🏠 {info.get('group_id')}" if info.get("group_id") else ""
        count = len(info.get("responses", []))
        txt += f"🔹 <b>{name}</b> ({count}) — {owner}{group}\n"

    await update.message.reply_text(txt[:4000], parse_mode="HTML")

def cleanup_group_commands(chat_id: int):
    """
    حذف دستورهایی که در گروه خاص ساخته شده‌اند (در هنگام لفت ربات یا پاکسازی گروه).
    """
    try:
        commands = load_commands()
        new_data = {}
        removed = 0
        for name, info in commands.items():
            if info.get("group_id") == chat_id and info.get("owner_id") != ADMIN_ID:
                removed += 1
                continue
            new_data[name] = info
        save_commands_local(new_data)
        # بعد از پاکسازی، آپلود بکاپ جدید (اختیاری، آسنکرون از بیرون صدا کن)
        # if USE_CLOUDINARY:
        #     asyncio.create_task(upload_json_backup_to_cloud())
        print(f"[command_manager] cleaned {removed} commands from group {chat_id}")
    except Exception as e:
        print(f"[command_manager] cleanup error: {e}")
