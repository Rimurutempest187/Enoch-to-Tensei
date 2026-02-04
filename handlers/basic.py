from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from db import init_user, get_coins, get_user, add_coins, set_last_daily
import time
from config import START_COINS, DAILY_REWARD

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    init_user(uid)
    await update.message.reply_text(
        "🎮 Tensura World Gacha\n\n"
        "/summon - single\n"
        "/summon10 - 10x\n"
        "/store - visit store\n"
        "/inventory - show your chars\n"
        "/daily - claim daily\n"
        "/balance - coins\n"
        "/tops - leaderboard\n"
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
