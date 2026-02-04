from telegram import Update
from telegram.ext import ContextTypes
import time
from db import conn, add_coins

def today():
    return int(time.time() // 86400)

async def quest_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    cur = conn.cursor()
    d = today()

    cur.execute("SELECT * FROM quests WHERE user_id=?", (uid,))
    q = cur.fetchone()

    if not q or q[4] != d:
        cur.execute("""
        REPLACE INTO quests VALUES(?,?,?,?,?)
        """, (uid, 0, 0, 0, d))
        conn.commit()
        q = (uid,0,0,0,d)

    _, summon, win, claimed, _ = q

    text = (
        "📜 <b>Daily Quest</b>\n\n"
        f"🎯 Summon: {summon}/3\n"
        f"⚔ Duel Win: {win}/1\n"
        f"🎁 Claimed: {'Yes' if claimed else 'No'}"
    )

    await update.message.reply_text(text, parse_mode="HTML")


async def claimquest_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    cur = conn.cursor()

    cur.execute("SELECT summon_count, duel_win, claimed FROM quests WHERE user_id=?", (uid,))
    q = cur.fetchone()

    if not q:
        return await update.message.reply_text("❌ No quest")

    summon, win, claimed = q

    if claimed:
        return await update.message.reply_text("Already claimed")

    if summon < 3 or win < 1:
        return await update.message.reply_text("Quest not completed")

    reward = 150
    add_coins(uid, reward)

    cur.execute("UPDATE quests SET claimed=1 WHERE user_id=?", (uid,))
    conn.commit()

    await update.message.reply_text(f"🎉 Quest Complete! +{reward} coins")
