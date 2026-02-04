from telegram import Update
from telegram.ext import ContextTypes
from db import get_user, get_inventory, get_tops

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    user = get_user(uid)
    if not user:
        await update.message.reply_text("❌ Profile not found")
        return

    _, coins, lvl, exp, _ = user

    inv = get_inventory(uid)
    total_chars = sum(x[3] for x in inv) if inv else 0

    tops = get_tops(100)
    rank = "N/A"
    for i, row in enumerate(tops, 1):
        if row[0] == uid:
            rank = i
            break

    text = (
        "👤 <b>Your Profile</b>\n\n"
        f"🎚 Level: {lvl}\n"
        f"📊 EXP: {exp}\n"
        f"💰 Coins: {coins}\n"
        f"🎒 Characters: {total_chars}\n"
        f"🏆 Rank: {rank}"
    )

    await update.message.reply_text(text, parse_mode="HTML")
