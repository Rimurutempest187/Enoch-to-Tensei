from telegram import Update
from telegram.ext import ContextTypes
from db import get_character, get_inventory, add_coins
import sqlite3
from db import conn

async def sell_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /sell <char_id> <amount>")
        return

    try:
        cid = int(context.args[0])
        amt = int(context.args[1])
    except:
        return await update.message.reply_text("Invalid number")

    if amt <= 0:
        return await update.message.reply_text("Amount must be > 0")

    inv = get_inventory(uid)

    target = None
    for row in inv:
        if row[0] == cid:
            target = row
            break

    if not target:
        return await update.message.reply_text("❌ You don't own this character")

    if target[3] < amt:
        return await update.message.reply_text("❌ Not enough amount")

    char = get_character(cid)

    sell_price = char[5] // 2 * amt   # 50% refund

    # update inventory
    c = conn.cursor()
    c.execute("""
        UPDATE inventory 
        SET count = count - ? 
        WHERE user_id=? AND char_id=?
    """, (amt, uid, cid))

    c.execute("""
        DELETE FROM inventory
        WHERE count<=0
    """)

    conn.commit()

    add_coins(uid, sell_price)

    await update.message.reply_text(
        f"✅ Sold {amt}x {char[1]}\n💰 +{sell_price} coins"
    )
