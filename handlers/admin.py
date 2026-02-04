# handlers/admin.py

import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# adjust these imports to match your db module
from db import is_admin, init_user, add_coins, add_admin, insert_character, conn, c
from config import DB_FILE

# ---------------- Admin Panel Command ----------------
async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("⚠ Admin only")
        return

    keyboard = [
        [
            InlineKeyboardButton("➕ Add Coins", callback_data="admin_addcoins"),
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
            InlineKeyboardButton("💾 Backup", callback_data="admin_backup")
        ],
        [
            InlineKeyboardButton("📷 Upload Char", callback_data="admin_upload_hint"),
            InlineKeyboardButton("❌ Close", callback_data="admin_close")
        ]
    ]

    await update.message.reply_text(
        "🛠 <b>Admin Panel</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

# ---------------- Admin Button Callback ----------------
async def admin_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if not is_admin(uid):
        await q.message.reply_text("⚠ Admin only")
        return

    # Add coins -> show usage hint (use /addcoins command already present)
    if q.data == "admin_addcoins":
        await q.message.reply_text(
            "Usage:\n/addcoins <user_id> <amount>\n\nExample:\n/addcoins 123456789 500"
        )
        return

    # Broadcast -> show usage hint
    if q.data == "admin_broadcast":
        await q.message.reply_text(
            "Usage:\n/broadcast <your message here>\n\nThis will send the message to all users."
        )
        return

    # Stats -> query DB and show
    if q.data == "admin_stats":
        try:
            c.execute("SELECT COUNT(*) FROM users")
            users = c.fetchone()[0] or 0

            c.execute("SELECT COUNT(*) FROM characters")
            chars = c.fetchone()[0] or 0

            c.execute("SELECT IFNULL(SUM(coins),0) FROM users")
            total_coins = c.fetchone()[0] or 0

            text = (
                "📊 <b>Bot Statistics</b>\n\n"
                f"👥 Users: {users}\n"
                f"🃏 Characters: {chars}\n"
                f"💰 Total Coins: {total_coins}"
            )
        except Exception as e:
            text = f"❌ Error reading stats: {e}"

        await q.message.reply_text(text, parse_mode="HTML")
        return

    # Backup -> send DB file
    if q.data == "admin_backup":
        try:
            if not os.path.exists(DB_FILE):
                await q.message.reply_text("❌ DB file not found.")
                return
            # send DB file to the admin chat as document
            await context.bot.send_document(q.message.chat.id, document=open(DB_FILE, "rb"))
        except Exception as e:
            await q.message.reply_text(f"❌ Backup failed: {e}")
        return

    # Upload hint (explain /upload usage)
    if q.data == "admin_upload_hint":
        await q.message.reply_text(
            "Upload character:\n\n"
            "1) Reply to an image with caption lines:\n"
            "Name: <name>\nRarity: <rarity>\nFaction: <faction>\nPower: <power>\nPrice: <price>\n\n"
            "OR\n"
            "2) Send photo and command:\n"
            "/upload Name|Rarity|Faction|Power|Price"
        )
        return

    # Close -> delete the panel message
    if q.data == "admin_close":
        try:
            await q.message.delete()
        except:
            pass
        return

# ---------------- addcoins command ----------------
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

# ---------------- addadmin command (owner-only) ----------------
async def addadmin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    # you can check owner in main when registering or check here with OWNER_ID
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

# ---------------- upload command ----------------
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
