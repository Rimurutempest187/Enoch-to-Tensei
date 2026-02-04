import sqlite3
from config import DB_FILE

def get_conn():
    return sqlite3.connect(DB_FILE)

def get_users():
    db = get_conn()
    c = db.cursor()
    c.execute("SELECT id, coins, level, exp FROM users")
    rows = c.fetchall()
    db.close()
    return rows

def get_chars():
    db = get_conn()
    c = db.cursor()
    c.execute("SELECT id,name,rarity,faction,power,price FROM characters")
    rows = c.fetchall()
    db.close()
    return rows

def update_coins(uid, amount):
    db = get_conn()
    c = db.cursor()
    c.execute("UPDATE users SET coins=? WHERE id=?", (amount, uid))
    db.commit()
    db.close()
