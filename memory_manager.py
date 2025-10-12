import sqlite3
import random

DB_PATH = "bot_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS replies (
        phrase TEXT,
        response TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS groups (
        chat_id TEXT PRIMARY KEY,
        title TEXT
    )
    """)
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_PATH)

# 🧠 یادگیری جمله و پاسخ
def learn(phrase, response):
    phrase, response = phrase.strip().lower(), response.strip()
    if not phrase or not response:
        return
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO replies (phrase, response) VALUES (?, ?)", (phrase, response))
    conn.commit()
    conn.close()

# 💬 گرفتن پاسخ تصادفی
def get_reply(text):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT response FROM replies WHERE phrase=?", (text.lower().strip(),))
    results = [r[0] for r in c.fetchall()]
    conn.close()
    if results:
        return random.choice(results)
    return random.choice(["عه", "جدی؟", "باشه", "نمی‌دونم والا", "جالبه 😅", "اوه"])

# 🎭 تغییر مود
def set_mode(mode):
    conn = get_connection()
    c = conn.cursor()
    c.execute("REPLACE INTO settings (key, value) VALUES ('mode', ?)", (mode,))
    conn.commit()
    conn.close()

# 🔍 گرفتن مود فعلی
def get_mode():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='mode'")
    row = c.fetchone()
    conn.close()
    return row[0] if row else "نرمال"

# 📊 آمار حافظه
def get_stats():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(DISTINCT phrase) FROM replies")
    total_phrases = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM replies")
    total_responses = c.fetchone()[0]
    mode = get_mode()
    conn.close()
    return {"phrases": total_phrases, "responses": total_responses, "mode": mode}

# 🧾 ثبت گروه‌ها
def register_group(chat_id, title):
    conn = get_connection()
    c = conn.cursor()
    c.execute("REPLACE INTO groups (chat_id, title) VALUES (?, ?)", (str(chat_id), title))
    conn.commit()
    conn.close()

# 🧠 لیست گروه‌ها
def get_all_groups():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT chat_id FROM groups")
    groups = [r[0] for r in c.fetchall()]
    conn.close()
    return groups

# 🌈 بهبود جمله
def enhance_sentence(sentence):
    replacements = {
        "خوب": ["عالی", "باحال", "اوکی"],
        "نه": ["نخیر", "اصلاً", "نچ"],
        "آره": ["آرههه", "اوهوم", "قطعاً"],
    }
    words = sentence.split()
    new_words = []
    for word in words:
        if word in replacements and random.random() < 0.4:
            new_words.append(random.choice(replacements[word]))
        else:
            new_words.append(word)
    return " ".join(new_words)
