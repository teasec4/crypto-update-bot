import sqlite3

def init_db():
    conn = sqlite3.connect("crypto_bot.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            notification_time TEXT,
            currencies TEXT,
            timezone TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_user(user_id, timezone, coins, time):
    conn = sqlite3.connect("crypto_bot.db")
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO users (user_id, notification_time, currencies, timezone)
        VALUES (?, ?, ?, ?)
    ''', (str(user_id), time, ','.join(coins), timezone))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect("crypto_bot.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (str(user_id),))
    user = c.fetchone()
    conn.close()
    if user:
        return {
            "user_id": user[0],
            "timezone": user[3],
            "coins": user[2].split(",") if user[2] else [],
            "time": user[1]
        }
    return None

def get_all_users():
    conn = sqlite3.connect("crypto_bot.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()
    return [
        {
            "user_id": user[0],
            "timezone": user[3],
            "coins": user[2].split(",") if user[2] else [],
            "time": user[1]
        } for user in users
    ]

def remove_user(user_id):
    conn = sqlite3.connect("crypto_bot.db")
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE user_id = ?", (str(user_id),))
    conn.commit()
    affected_rows = c.rowcount
    conn.close()
    return affected_rows > 0