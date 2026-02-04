import os
import sqlite3
from typing import List, Tuple
from config import DATA_DIR, DB_FILE

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=30, isolation_level=None)
c = conn.cursor()

def init_db():
    # users
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        coins INTEGER,
        level INTEGER,
        exp INTEGER,
        last_daily INTEGER
    )
    """)
    # characters
    c.execute("""
    CREATE TABLE IF NOT EXISTS characters(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        rarity TEXT,
        faction TEXT,
        power INTEGER,
        price INTEGER,
        file_id TEXT
    )
    """)

    # inventory
    c.execute("""
    CREATE TABLE IF NOT EXISTS inventory(
        user_id INTEGER,
        char_id INTEGER,
        count INTEGER,
        PRIMARY KEY(user_id,char_id)
    )
    """)

    # admins
    c.execute("""
    CREATE TABLE IF NOT EXISTS admins(
        user_id INTEGER PRIMARY KEY
    )
    """)

    conn.commit()

# --- user helpers ---
def init_user(uid: int):
    c.execute("SELECT 1 FROM users WHERE id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES(?,?,?,?,?)", (uid, 0, 1, 0, 0))
        c.execute("UPDATE users SET coins=? WHERE id=?", (0 + 0, uid))  # avoid None issues
        # set start coins
        c.execute("UPDATE users SET coins=? WHERE id=?", (int(os.getenv("START_COINS", 200)), uid))
        conn.commit()

def get_user(uid: int):
    c.execute("SELECT id,coins,level,exp,last_daily FROM users WHERE id=?", (uid,))
    return c.fetchone()

def get_coins(uid: int) -> int:
    c.execute("SELECT coins FROM users WHERE id=?", (uid,))
    r = c.fetchone()
    return r[0] if r else 0

def add_coins(uid: int, amount: int):
    c.execute("UPDATE users SET coins = coins + ? WHERE id=?", (amount, uid))
    conn.commit()

def set_last_daily(uid: int, ts: int):
    c.execute("UPDATE users SET last_daily = ? WHERE id=?", (ts, uid))
    conn.commit()

def add_exp(uid: int, amount: int):
    c.execute("SELECT level, exp FROM users WHERE id=?", (uid,))
    row = c.fetchone()
    if not row:
        return
    lvl, exp = row
    exp += amount
    while exp >= lvl * 100:
        exp -= lvl * 100
        lvl += 1
    c.execute("UPDATE users SET level=?, exp=? WHERE id=?", (lvl, exp, uid))
    conn.commit()

# --- characters ---
def insert_character(name, rarity, faction, power, price, file_id):
    c.execute("""
        INSERT INTO characters (name, rarity, faction, power, price, file_id)
        VALUES (?,?,?,?,?,?)
    """, (name, rarity, faction, power, price, file_id))
    conn.commit()
    return c.lastrowid

def get_all_characters() -> List[Tuple]:
    c.execute("SELECT * FROM characters")
    return c.fetchall()

def get_character(cid: int):
    c.execute("SELECT * FROM characters WHERE id=?", (cid,))
    return c.fetchone()

# --- inventory ---
def add_inventory(uid: int, cid: int, amt: int = 1):
    c.execute("SELECT count FROM inventory WHERE user_id=? AND char_id=?", (uid, cid))
    r = c.fetchone()
    if r:
        c.execute("UPDATE inventory SET count = count + ? WHERE user_id=? AND char_id=?", (amt, uid, cid))
    else:
        c.execute("INSERT INTO inventory VALUES(?,?,?)", (uid, cid, amt))
    conn.commit()

def get_inventory(uid: int):
    c.execute("""
    SELECT characters.id, characters.name, characters.rarity, inventory.count
    FROM inventory
    JOIN characters ON inventory.char_id=characters.id
    WHERE inventory.user_id=?
    ORDER BY characters.id
    """, (uid,))
    return c.fetchall()

def get_tops(limit:int=10):
    c.execute("""
    SELECT id, level, exp, coins
    FROM users
    ORDER BY level DESC, exp DESC, coins DESC
    LIMIT ?
    """, (limit,))
    return c.fetchall()

# --- admin ---
def is_admin(uid: int) -> bool:
    c.execute("SELECT 1 FROM admins WHERE user_id=?", (uid,))
    return bool(c.fetchone())

def add_admin(uid: int):
    try:
        c.execute("INSERT INTO admins(user_id) VALUES(?)", (uid,))
        conn.commit()
        return True
    except:
        return False
