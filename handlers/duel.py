from telegram import Update
from telegram.ext import ContextTypes
from db import get_inventory, add_coins
import random

def total_power(uid):
    inv = get_inventory(uid)
    return sum(x[3]*10 for x in inv) if inv else 10

async def duel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    if not context.args:
        return await update.message.reply_text("Usage: /duel @username")

    target = context.args[0]

    try:
        user = await context.bot.get_chat(target)
        tid = user.id
    except:
        return await update.message.reply_text("User not found")

    p1 = total_power(uid)
    p2 = total_power(tid)

    chance = p1 / (p1+p2)

    if random.random() < chance:
        winner = uid
        loser = tid
    else:
        winner = tid
        loser = uid

    reward = 50

    add_coins(winner, reward)

    text = (
        "⚔ <b>Duel Result</b>\n\n"
        f"Winner: {winner}\n"
        f"Loser: {loser}\n"
        f"💰 Reward: {reward}"
    )

    await update.message.reply_text(text, parse_mode="HTML")
