# mafia_module.py
import asyncio
import json
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    CommandHandler,
    Application,
    Job,
)

# ========== تنظیمات قابل تغییر ==========
MAFIA_DATA_FILE = "mafia_games.json"  # برای ذخیره موقتی یا بارگذاری بعدی (اختیاری)
DEFAULT_DAY_SECONDS = 60  # مدت زمان روز (ثانیه) - برای تست کوتاه گذاشته شده، در اجرا واقعی بلندتر کن
DEFAULT_NIGHT_SECONDS = 45  # مدت زمان شب
MIN_PLAYERS = 6

# رول‌های پیش‌فرض (قابل تغییر/گسترش)
DEFAULT_ROLES = ["mafia", "mafia", "detective", "doctor", "citizen", "citizen"]

# ========== داده‌های مدل ==========
@dataclass
class Player:
    user_id: int
    name: str
    alive: bool = True
    role: Optional[str] = None
    votes_received: int = 0
    protected: bool = False  # برای دکتر
    last_action: Optional[dict] = None

@dataclass
class MafiaGame:
    chat_id: int
    message_id: Optional[int] = None  # id پیام لابی/وضعیت
    owner_id: int = 0
    players: Dict[int, Player] = field(default_factory=dict)  # user_id -> Player
    status: str = "lobby"  # lobby / running / day / night / finished
    day_count: int = 0
    votes: Dict[int, int] = field(default_factory=dict)  # voter_id -> target_user_id
    lynch_target: Optional[int] = None
    night_actions: List[dict] = field(default_factory=list)  # list of actions
    created_at: float = field(default_factory=time.time)
    day_job_name: Optional[str] = None
    night_job_name: Optional[str] = None

# in-memory store of games by chat_id
GAMES: Dict[int, MafiaGame] = {}

# ========== ابزارهای کمکی ==========
def save_games_to_file():
    try:
        data = {}
        for cid, g in GAMES.items():
            data[cid] = {
                "chat_id": g.chat_id,
                "owner_id": g.owner_id,
                "players": {uid: {"user_id": p.user_id, "name": p.name, "alive": p.alive, "role": p.role} for uid, p in g.players.items()},
                "status": g.status,
                "day_count": g.day_count,
                "created_at": g.created_at,
            }
        with open(MAFIA_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_games_from_file():
    try:
        with open(MAFIA_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # بالافاصله بارگذاری کامل بازی‌ها نیازمند منطق بیشتر است؛ اینجا فقط برای اطلاع‌دهی است
    except Exception:
        pass

def game_status_text(game: MafiaGame) -> str:
    players_text = "\n".join([f"- {p.name} ({'زنده' if p.alive else 'مرده'})" for p in game.players.values()])
    text = (
        f"🎭 <b>MAFIA — بازی در چت</b>\n"
        f"🏷️ مالک بازی: <code>{game.owner_id}</code>\n"
        f"📣 وضعیت: <b>{game.status}</b>\n"
        f"👥 تعداد بازیکنان: <b>{len(game.players)}</b>\n"
        f"🕒 شبانه‌روز: روز {game.day_count}\n\n"
        f"👥 بازیکنان:\n{players_text}\n\n"
        "🔸 دستورات:\n"
        "• /mafia_join — شرکت در بازی\n"
        "• /mafia_leave — خروج از لابی\n"
        "• /mafia_start — شروع بازی (مالک یا مدیر)\n"
    )
    return text

def get_role_distribution(num_players: int) -> List[str]:
    # ساختار ساده: برای 6+ از DEFAULT_ROLES استفاده کن، برای بیشتر اضافه کن citizen
    roles = DEFAULT_ROLES.copy()
    while len(roles) < num_players:
        roles.append("citizen")
    random.shuffle(roles)
    return roles[:num_players]

# ========== ارسال پیام خصوصی نقش ==========
async def send_private_role(context: ContextTypes.DEFAULT_TYPE, player: Player, role_text: str):
    """ارسال نقش به کاربر به صورت خصوصی. اگر ارسال نشد، خطا را در گروه اطلاع بده."""
    try:
        await context.bot.send_message(chat_id=player.user_id, text=role_text, parse_mode="HTML")
        return True
    except Exception as e:
        # اگر نتوانستیم پیام خصوصی بفرستیم، خطا را در group لاگ کن
        print(f"[mafia] cannot PM {player.user_id}: {e}")
        return False

# ========== حالت‌ها و منطق بازی ==========
async def create_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if chat_id in GAMES and GAMES[chat_id].status != "finished":
        await update.message.reply_text("❗ در حال حاضر یک بازی در این گروه فعال است. لطفاً صبر کنید یا آن را خاتمه دهید.")
        return

    game = MafiaGame(chat_id=chat_id, owner_id=user.id)
    GAMES[chat_id] = game
    text = f"🎭 بازی مافیا ساخته شد!\nمالک: <b>{user.first_name}</b>\n\nبرای شرکت: /mafia_join\nمالک می‌تواند با /mafia_start بازی را آغاز کند."
    msg = await update.message.reply_text(text, parse_mode="HTML")
    game.message_id = msg.message_id
    save_games_to_file()

async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    uid = update.effective_user.id
    uname = update.effective_user.first_name
    if chat_id not in GAMES:
        await update.message.reply_text("❗ هیچ لابی فعالی وجود ندارد. با /mafia_create لابی بساز.")
        return
    game = GAMES[chat_id]
    if game.status != "lobby":
        await update.message.reply_text("❗ بازی در حال انجام است؛ الان نمی‌توانید وارد شوید.")
        return
    if uid in game.players:
        await update.message.reply_text("✅ شما قبلاً در لابی هستید.")
        return
    game.players[uid] = Player(user_id=uid, name=uname)
    await update.message.reply_text(f"✅ <b>{uname}</b> به لابی اضافه شد.", parse_mode="HTML")
    save_games_to_file()

async def leave_lobby(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    uid = update.effective_user.id
    if chat_id not in GAMES:
        await update.message.reply_text("❗ لابی فعالی نیست.")
        return
    game = GAMES[chat_id]
    if uid not in game.players:
        await update.message.reply_text("❗ شما در لابی نیستید.")
        return
    del game.players[uid]
    await update.message.reply_text("✅ شما از لابی خارج شدید.")
    save_games_to_file()

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    uid = update.effective_user.id
    # مجاز بودن: مالک یا مدیر گروه
    if chat_id not in GAMES:
        await update.message.reply_text("❗ لابی ای وجود ندارد.")
        return
    game = GAMES[chat_id]
    # فقط مالک یا ادمین اجازه شروع داره
    is_owner = (uid == game.owner_id)
    try:
        member = await context.bot.get_chat_member(chat_id, uid)
        is_admin = member.status in ("administrator", "creator")
    except:
        is_admin = False

    if not (is_owner or is_admin):
        await update.message.reply_text("❗ فقط مالک لابی یا مدیر گروه می‌تواند بازی را شروع کند.")
        return

    if len(game.players) < MIN_PLAYERS:
        await update.message.reply_text(f"❗ حداقل {MIN_PLAYERS} بازیکن لازم است. فعلاً {len(game.players)} نفر هستند.")
        return

    # توزیع نقش‌ها
    roles = get_role_distribution(len(game.players))
    for p, role in zip(list(game.players.values()), roles):
        p.role = role

    # ارسال نقش‌ها به صورت خصوصی
    for p in game.players.values():
        role_text = f"🎭 نقش شما در بازی: <b>{p.role.upper()}</b>\n\n"
        if p.role == "mafia":
            role_text += "🔪 شما مافیا هستید. با هم‌مافیاها هماهنگ شوید."
        elif p.role == "detective":
            role_text += "🕵️ شما کارآگاه هستید. هر شب می‌توانید یک نفر را تحقیق کنید."
        elif p.role == "doctor":
            role_text += "🩺 شما دکتر هستید. هر شب می‌توانید یک نفر را نجات دهید."
        else:
            role_text += "👤 شما شهروند هستید. هدف: زنده ماندن و شناسایی مافیا."

        ok = await send_private_role(context, p, role_text)
        if not ok:
            # اگر نتوانیم PM ارسال کنیم، اطلاع در گروه
            await context.bot.send_message(chat_id, f"⚠️ نتوانستم نقش <b>{p.name}</b> را به‌صورت خصوصی ارسال کنم. لطفاً اجازه ارسال پیام خصوصی را فعال کند.", parse_mode="HTML")

    game.status = "night"
    game.day_count = 0
    await context.bot.send_message(chat_id, "🌙 بازی شروع شد — شب اول! نقش‌ها به صورت خصوصی ارسال شد.", parse_mode="HTML")
    save_games_to_file()
    # زمان‌بندی شب
    await schedule_night_end(context, game, DEFAULT_NIGHT_SECONDS)

# ========== عملیات شب ==========
async def schedule_night_end(context: ContextTypes.DEFAULT_TYPE, game: MafiaGame, delay_seconds: int):
    # نام یونیک job
    job_name = f"mafia_night_{game.chat_id}_{int(time.time())}"
    async def night_timeout(job_context):
        try:
            await process_night_actions(context, game.chat_id)
        except Exception as e:
            print("[mafia] night timeout error:", e)

    job = context.job_queue.run_once(night_timeout, when=delay_seconds, name=job_name)
    game.night_job_name = job_name

async def process_night_actions(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    # پردازش اکشن‌ها، اعمال مرگ/نجات/تحقیق
    game = GAMES.get(chat_id)
    if not game:
        return
    # جمع‌بندی اکشن‌ها
    mafia_targets = []
    doctor_targets = []
    detective_checks = []

    for action in game.night_actions:
        act = action.get("action")
        actor = action.get("actor")
        target = action.get("target")
        if act == "kill":
            mafia_targets.append({"by": actor, "target": target})
        elif act == "save":
            doctor_targets.append(target)
        elif act == "investigate":
            detective_checks.append({"by": actor, "target": target})

    # انتخاب هدف نهایی مافیا: رای گیری بین اهداف
    target_counts = {}
    for t in mafia_targets:
        target_counts[t["target"]] = target_counts.get(t["target"], 0) + 1
    lynch_target = None
    if target_counts:
        lynch_target = max(target_counts.items(), key=lambda x: x[1])[0]

    died = []
    if lynch_target is not None:
        if lynch_target in doctor_targets:
            # محافظت شده
            await context.bot.send_message(chat_id, f"🛡️ یکی محافظت شد — کسی کشته نشد در این شب.")
        else:
            # کشته می‌شود
            if lynch_target in game.players:
                game.players[lynch_target].alive = False
                died.append(lynch_target)

    # پردازش تحقیقات کارآگاه
    for check in detective_checks:
        by = check["by"]
        target = check["target"]
        # جواب به کارآگاه
        role = game.players.get(target).role if target in game.players else None
        res = "mafia" if role == "mafia" else "not mafia"
        try:
            await context.bot.send_message(by, f"🔎 تحقیق شما: کاربر <b>{game.players[target].name}</b> => <b>{res}</b>", parse_mode="HTML")
        except Exception as e:
            print("[mafia] cannot PM detective:", e)

    # گزارش مرگ‌ها
    if died:
        for uid in died:
            await context.bot.send_message(chat_id, f"🪦 <b>{game.players[uid].name}</b> در این شب کشته شد.", parse_mode="HTML")
    else:
        await context.bot.send_message(chat_id, "🌙 شب به پایان رسید — هیچکس کشته نشد.", parse_mode="HTML")

    # پاکسازی و آماده‌سازی روز
    game.night_actions.clear()
    game.status = "day"
    game.day_count += 1
    save_games_to_file()
    await schedule_day_end(context, game, DEFAULT_DAY_SECONDS)

# ========== روز: رای‌گیری ==========
async def schedule_day_end(context: ContextTypes.DEFAULT_TYPE, game: MafiaGame, delay_seconds: int):
    job_name = f"mafia_day_{game.chat_id}_{int(time.time())}"
    async def day_timeout(job_context):
        try:
            await process_day_votes(context, game.chat_id)
        except Exception as e:
            print("[mafia] day timeout error:", e)

    job = context.job_queue.run_once(day_timeout, when=delay_seconds, name=job_name)
    game.day_job_name = job_name

async def process_day_votes(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    game = GAMES.get(chat_id)
    if not game:
        return
    # شمارش آراء
    counts = {}
    for voter, target in game.votes.items():
        if target not in counts:
            counts[target] = 0
        counts[target] += 1
    if not counts:
        await context.bot.send_message(chat_id, "🔇 رای‌گیری به پایان رسید، هیچ رای‌ای ثبت نشد.")
    else:
        # نفر با بیشترین رای حذف می‌شود
        target, cnt = max(counts.items(), key=lambda x: x[1])
        if target in game.players:
            game.players[target].alive = False
            await context.bot.send_message(chat_id, f"🔨 با {cnt} رای، <b>{game.players[target].name}</b> از بازی حذف شد.", parse_mode="HTML")
    # پاکسازی آراء
    game.votes.clear()
    save_games_to_file()

    # بررسی پایان بازی
    await check_end_conditions_and_proceed(context, game)

# ========== بررسی پایان ==========
async def check_end_conditions_and_proceed(context: ContextTypes.DEFAULT_TYPE, game: MafiaGame):
    # اگر همه مافیا ها حذف شدند => شهر برد
    mafia_alive = [p for p in game.players.values() if p.role == "mafia" and p.alive]
    citizens_alive = [p for p in game.players.values() if p.role != "mafia" and p.alive]
    if not mafia_alive:
        await context.bot.send_message(game.chat_id, "🏆 شهر برنده شد! تمام مافیاها نابود شدند.")
        game.status = "finished"
        save_games_to_file()
        return
    # اگر تعداد مافیا >= بقیه -> مافیا برد
    if len(mafia_alive) >= len(citizens_alive):
        await context.bot.send_message(game.chat_id, "💀 مافیا برنده شد! تعداد مافیا برابر یا بیشتر از شهروندان است.")
        game.status = "finished"
        save_games_to_file()
        return

    # در غیر این صورت ادامه: شب بعد
    game.status = "night"
    await context.bot.send_message(game.chat_id, "🌙 شب بعدی آغاز می‌شود — لطفاً نقش‌ها عملیات شب را انجام دهند (پیام خصوصی).", parse_mode="HTML")
    save_games_to_file()
    await schedule_night_end(context, game, DEFAULT_NIGHT_SECONDS)

# ========== اکشن‌ها (دکمه‌ها و Callback ها) ==========
def mk_inline(buttons):
    return InlineKeyboardMarkup([[InlineKeyboardButton(t, callback_data=c) for t, c in buttons]])

async def vote_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # format: mafia_vote:{target_user_id}
    if not data.startswith("mafia_vote:"):
        return
    target_id = int(data.split(":", 1)[1])
    chat_id = query.message.chat_id
    game = GAMES.get(chat_id)
    if not game or game.status != "day":
        await query.message.reply_text("❗ الان دوره رای‌گیری نیست.")
        return
    voter = query.from_user.id
    if voter not in game.players or not game.players[voter].alive:
        await query.message.reply_text("❗ فقط بازیکنان زنده می‌توانند رای بدهند.")
        return
    game.votes[voter] = target_id
    await query.message.reply_text(f"✅ رأی شما به <b>{game.players[target_id].name}</b> ثبت شد.", parse_mode="HTML")

async def night_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # e.g. mafia_kill:target_id or doctor_save:target_id or detective_check:target_id
    if ":" not in data:
        return
    action, target = data.split(":", 1)
    target_id = int(target)
    chat_id = query.message.chat_id
    # پیدا کردن بازی بر اساس چت (البته اکشن‌ها از پیوی کاربر می‌آیند)
    # این callback برای دکمه‌های خصوصی به کار میره؛ در پیوی کاربر دکمه‌ها را فشار می‌دهد
    # بنابراین برای ایمنی، بازی را از context.user_data بگیریم
    user_id = query.from_user.id
    # جستجو بازی‌ای که شامل این بازیکن باشه و status=='night'
    game = None
    for g in GAMES.values():
        if user_id in g.players and g.status == "night":
            game = g
            break
    if not game:
        await query.edit_message_text("❗ الان مرحله‌ی شب نیست یا شما در هیچ بازی‌ای شرکت ندارید.")
        return

    # ثبت اکشن
    if action.startswith("mafia_kill"):
        # فقط مافیاها مجازند
        p = game.players.get(user_id)
        if not p or p.role != "mafia":
            await query.answer("❗ فقط مافیاها می‌توانند این عمل را انجام دهند.", show_alert=True)
            return
        game.night_actions.append({"action": "kill", "actor": user_id, "target": target_id})
        await query.edit_message_text("✅ درخواست شلیک ثبت شد.")
        return

    if action.startswith("doctor_save"):
        p = game.players.get(user_id)
        if not p or p.role != "doctor":
            await query.answer("❗ فقط دکتر می‌تواند این عمل را انجام دهد.", show_alert=True)
            return
        game.night_actions.append({"action": "save", "actor": user_id, "target": target_id})
        await query.edit_message_text("✅ درخواست نجات ثبت شد.")
        return

    if action.startswith("detective_check"):
        p = game.players.get(user_id)
        if not p or p.role != "detective":
            await query.answer("❗ فقط کارآگاه می‌تواند این عمل را انجام دهد.", show_alert=True)
            return
        game.night_actions.append({"action": "investigate", "actor": user_id, "target": target_id})
        await query.edit_message_text("✅ درخواست تحقیق ثبت شد.")
        return

# ========== دستورات کمکی برای بازیکنان ==========
async def open_night_panel_for_player(context: ContextTypes.DEFAULT_TYPE, game: MafiaGame, player: Player):
    """ارسال دکمه‌های شب به پیوی بازیکن (بر اساس نقش)"""
    try:
        if not player.alive:
            return
        if player.role == "mafia":
            # مافیا لیست هدف‌ها
            buttons = []
            for p in game.players.values():
                if p.user_id != player.user_id and p.alive:
                    buttons.append((p.name, f"mafia_kill:{p.user_id}"))
            if not buttons:
                return
            kb = mk_inline(buttons)
            await context.bot.send_message(player.user_id, "🌙 شما مافیا هستید — هدف خود را انتخاب کنید:", reply_markup=kb)
        elif player.role == "doctor":
            buttons = []
            for p in game.players.values():
                if p.alive:
                    buttons.append((p.name, f"doctor_save:{p.user_id}"))
            kb = mk_inline(buttons)
            await context.bot.send_message(player.user_id, "🌙 شما دکتر هستید — یک نفر را برای نجات انتخاب کنید:", reply_markup=kb)
        elif player.role == "detective":
            buttons = []
            for p in game.players.values():
                if p.user_id != player.user_id and p.alive:
                    buttons.append((p.name, f"detective_check:{p.user_id}"))
            kb = mk_inline(buttons)
            await context.bot.send_message(player.user_id, "🌙 شما کارآگاه هستید — یک نفر را برای تحقیق انتخاب کنید:", reply_markup=kb)
        else:
            # شهروندان نیاز به دکمه ندارند؛ می‌توانند حرف بزنند یا پیشنهاد بدند
            await context.bot.send_message(player.user_id, "🌙 شب است — شما نقش شهروند دارید و نیازی به عمل خاصی ندارید.")
    except Exception as e:
        print("[mafia] open_night_panel error:", e)

async def night_phase_broadcast(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """وقتی شب آغاز شد، این را صدا کن برای همه بازیکنان تا دکمه شب را برایشان بفرستی"""
    game = GAMES.get(chat_id)
    if not game:
        return
    for p in game.players.values():
        await open_night_panel_for_player(context, game, p)

# ========== رابط‌ها (API) برای register کردن ==========
def register_mafia_handlers(application: Application, group_number: int = 6):
    # دستورات پایه
    application.add_handler(CommandHandler("mafia_create", create_game), group=group_number)
    application.add_handler(CommandHandler("mafia_join", join_game), group=group_number)
    application.add_handler(CommandHandler("mafia_leave", leave_lobby), group=group_number)
    application.add_handler(CommandHandler("mafia_start", start_game), group=group_number)

    # callback برای رای و اکشن‌های شب
    application.add_handler(CallbackQueryHandler(vote_callback, pattern=r"^mafia_vote:"), group=group_number)
    application.add_handler(CallbackQueryHandler(night_action_callback, pattern=r"^(mafia_kill:|doctor_save:|detective_check:)"), group=group_number)

    # در صورت نیاز می‌توان handler‌های ذخیره/بارگذاری اضافه کرد
    print("[mafia] handlers registered")

# ========== اگر خواستی بازی ها را لود کنی ==========
load_games_from_file()
