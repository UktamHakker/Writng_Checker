import sqlite3
# SQL bazasini sozlash
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        username TEXT,
                        message_type TEXT,
                        message_content TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )''')
    conn.commit()
    conn.close()

# Ma'lumotni bazaga qo'shish
def save_message(user_id, username, message_type, message_content):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (user_id, username, message_type, message_content) VALUES (?, ?, ?, ?)",
                   (user_id, username, message_type, message_content))
    conn.commit()
    conn.close()
