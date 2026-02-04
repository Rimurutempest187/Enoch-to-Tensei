from telegram import Update
from telegram.ext import ContextTypes
from db import is_admin, init_user, add_coins, add_admin, insert_character
from utils import format_char
import traceback

async def addcoins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("⚠ Admin only")
        return
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /addcoins <user_id> <amount>")
        return
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
    except:
        await update.message.reply_text("Invalid user_id or amount")
        return
    init_user(target_id)
    add_coins(target_id, amount)
    await update.message.reply_text(f"✅ Added {amount} coins to {target_id}")

async def addadmin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    # only owner allowed — owner check in main when registering this command
    try:
        target_id = int(context.args[0])
    except:
        await update.message.reply_text("Invalid user_id")
        return
    ok = add_admin(target_id)
    if ok:
        await update.message.reply_text(f"✅ {target_id} added as admin")
    else:
        await update.message.reply_text("User already admin or DB error")

async def upload_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("⚠ Admin only")
        return
    photo_msg = None
    if update.message.photo:
        photo_msg = update.message
    elif update.message.reply_to_message and update.message.reply_to_message.photo:
        photo_msg = update.message.reply_to_message
    if not photo_msg:
        await update.message.reply_text("📷 Send photo with /upload or reply to photo")
        return

    args_text = " ".join(context.args).strip()
    # caption mode
    if not args_text:
        caption = update.message.caption or ""
        if not caption:
            await update.message.reply_text("Usage: /upload Name|Rarity|Faction|Power|Price or reply photo with caption lines Name: ...")
            return
        data = {}
        for line in caption.splitlines():
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            data[k.strip().lower()] = v.strip()
        required = ["name","rarity","faction","power","price"]
        if not all(k in data for k in required):
            await update.message.reply_text("Caption must include name, rarity, faction, power, price")
            return
        try:
            power = int(data["power"]); price = int(data["price"])
        except:
            await update.message.reply_text("Power / Price must be numbers")
            return
        file_id = photo_msg.photo[-1].file_id
        new_id = insert_character(data["name"], data["rarity"], data["faction"], power, price, file_id)
        await update.message.reply_text(f"✅ Uploaded!\nID: {new_id}\nName: {data['name']}")
        return

    # pipe mode
    parts = [p.strip() for p in args_text.split("|")]
    if len(parts) != 5:
        await update.message.reply_text("Usage: /upload Name|Rarity|Faction|Power|Price")
        return
    try:
        name, rarity, faction, power, price = parts
        power = int(power); price = int(price)
    except:
        await update.message.reply_text("Power / Price must be numbers")
        return
    file_id = photo_msg.photo[-1].file_id
    new_id = insert_character(name, rarity, faction, power, price, file_id)
    await update.message.reply_text(f"✅ Uploaded!\nID: {new_id}\nName: {name}")
