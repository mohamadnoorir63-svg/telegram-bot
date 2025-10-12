import sqlite3
import random

DB_FILE = "memory.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS replies (
        phrase TEXT PRIMARY KEY,
        responses TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS groups (
        chat_id TEXT PRIMARY KEY,
        title TEXT
    )
    """)

    conn.commit()
    conn.close()


# 🧠 یادگیری جمله و پاسخ
def learn(phrase, response):
    phrase = phrase.lower().strip()
    response = response.strip()

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("SELECT responses FROM replies WHERE phrase = ?", (phrase,))
    row = cur.fetchone()

    if row:
        responses = row[0].split("|||")
        if response not in responses:
            responses.append(response)
        cur.execute("UPDATE replies SET responses = ? WHERE phrase = ?", ("|||".join(responses), phrase))
    else:
        cur.execute("INSERT INTO replies (phrase, responses) VALUES (?, ?)", (phrase, response))

    conn.commit()
    conn.close()


# 🎯 پاسخ دادن
def get_reply(text):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT responses FROM replies WHERE phrase = ?", (text.lower().strip(),))
    row = cur.fetchone()
    conn.close()

    if row:
        responses = row[0].split("|||")
        return random.choice(responses)

    random_words = ["عه", "جدی؟", "باشه", "نمی‌دونم والا 😅", "اوه!", "جالبه 😂"]
    return random.choice(random_words)


# 🎭 مود
def set_mode(mode):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("REPLACE INTO settings (key, value) VALUES (?, ?)", ("mode", mode))
    conn.commit()
    conn.close()


def get_mode():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key='mode'")
    row = cur.fetchone()
    conn.close()
    return row[0] if row else "نرمال"


# 📊 آمار
def get_stats():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM replies")
    phrases = cur.fetchone()[0]

    cur.execute("SELECT responses FROM replies")
    all_responses = cur.fetchall()
    total_responses = sum(len(r[0].split("|||")) for r in all_responses)

    mode = get_mode()

    conn.close()
    return {"phrases": phrases, "responses": total_responses, "mode": mode}


# 🧩 بهبود جمله تصادفی
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


# 🧾 ثبت گروه‌ها
def register_group(chat_id, title):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO groups (chat_id, title) VALUES (?, ?)", (str(chat_id), title))
    conn.commit()
    conn.close()


def get_all_groups():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT chat_id FROM groups")
    groups = [row[0] for row in cur.fetchall()]
    conn.close()
    return groups
