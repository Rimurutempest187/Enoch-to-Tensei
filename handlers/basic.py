from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from db import init_user, get_coins, get_user, add_coins, set_last_daily
import time
from config import START_COINS, DAILY_REWARD

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    init_user(uid)

    text = (
        "🎮 <b>Welcome to A-F-W!</b>\n\n"
        "💡 <i>Adventure, collect, and battle in the world of characters!</i>\n\n"

        "🗂 <b>Available Commands:</b>\n"
        "/summon - Draw a character (Single)\n"
        "/summon10 - Draw 10 characters at once\n"
        "/store - Browse and buy characters in the store\n"
        "/inventory - See all your collected characters\n"
        "/daily - Claim your daily reward coins\n"
        "/balance - Check your coins and stats\n"
        "/tops - View the top players leaderboard\n\n"

        "🔥 Tips:\n"
        "- Summon daily to get rare characters!\n"
        "- Upgrade your characters and collect coins.\n"
        "- Participate in duels and quests to earn rewards.\n\n"

        "⚡ Enjoy the game and may luck be on your side!"
    )

    await update.message.reply_text(
        text, parse_mode="HTML"
    )


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    init_user(uid)
    coins = get_coins(uid)
    await update.message.reply_text(f"💰 Coins: {coins}")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    init_user(uid)
    now = int(time.time())
    user = get_user(uid)
    last = user[4] or 0
    if now - last < 86400:
        left = 86400 - (now - last)
        h = left // 3600
        m = (left % 3600)//60
        await update.message.reply_text(f"⏱ ကိုးနာ {h} နာရီ {m} မိနစ် ကျန်နေသည်")
        return
    add_coins(uid, DAILY_REWARD)
    set_last_daily(uid, now)
    await update.message.reply_text(f"✅ +{DAILY_REWARD} coins")
