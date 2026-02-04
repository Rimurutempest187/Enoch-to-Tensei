from telegram import Update
from telegram.ext import ContextTypes
from db import init_user, get_coins, add_coins, get_all_characters, add_inventory, get_character
from utils import roll_rarity, format_char
from config import SUMMON_COST, TEN_SUMMON_COST
import random

def choose_chars(n):
    rows = get_all_characters()
    if not rows:
        return []
    res = []
    for _ in range(n):
        r = roll_rarity()
        pool = [x for x in rows if x[2] == r] or rows
        res.append(random.choice(pool))
    return res

async def summon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    init_user(uid)
    coins = get_coins(uid)
    if coins < SUMMON_COST:
        await update.message.reply_text("❌ ဆုံမရနိုင်သေး — Coins မလုံလောက်ပါ")
        return
    add_coins(uid, -SUMMON_COST)
    chars = choose_chars(1)
    if not chars:
        await update.message.reply_text("⚠ Character မရှိသေးပါ")
        return
    ch = chars[0]
    add_inventory(uid, ch[0])
    # add_exp can be added
    await update.message.reply_photo(ch[6], caption=format_char(ch))

async def summon10(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    init_user(uid)
    coins = get_coins(uid)
    if coins < TEN_SUMMON_COST:
        await update.message.reply_text("❌ Coins မလုံလောက်ပါ")
        return
    add_coins(uid, -TEN_SUMMON_COST)
    res = choose_chars(10)
    text = "🎰 10x Summon\n\n"
    count = {}
    for ch in res:
        add_inventory(uid, ch[0])
        name = ch[1]
        count[name] = count.get(name, 0) + 1
    for k, v in count.items():
        text += f"{k} x{v}\n"
    await update.message.reply_text(text)
