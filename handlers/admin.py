# handlers/admin.py

import os
import zipfile
from datetime import datetime
import aiocron

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from db import (
    is_admin,
    init_user,
    add_coins,
    add_admin,
    insert_character,
    get_all_users,
    c,
)
from config import DB_FILE, OWNER_ID

# ---------------- States ----------------
ADDCOINS_UID = 1
ADDCOINS_AMOUNT = 2
BC_TEXT = 10
BC_CONFIRM = 11

# ---------------- Helper: send backup zip to chat ----------------
async def _send_backup_to_chat(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(DB_FILE):
        await context.bot.send_message(chat_id, "❌ DB file not found")
        return
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{now}.zip"
    try:
        with zipfile.ZipFile(backup_name, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(DB_FILE, arcname=os.path.basename(DB_FILE))
        await context.bot.send_document(chat_id, document=open(backup_name, "rb"), caption="✅ Database Backup")
    except Exception as e:
        await context.bot.send_message(chat_id, f"❌ Backup failed: {e}")
    finally:
        try:
            if os.path.exists(backup_name):
                os.remove(backup_name)
        except:
            pass

# ---------------- Admin panel (command) ----------------
async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("⚠ Admin only")
        return

    keyboard = [
        [
            InlineKeyboardButton("➕ Add Coins", callback_data="admin_addcoins"),
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
        ],
        [
            InlineKeyboardButton("📷 Upload Char", callback_data="admin_upload"),
            InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
            InlineKeyboardButton("💾 Backup", callback_data="admin_backup"),
        ],
        [
            InlineKeyboardButton("❌ Close", callback_data="admin_close"),
        ]
    ]

    await update.message.reply_text(
        "🛠 <b>Admin Panel</b>\nSelect action:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

# ---------------- Admin panel callback handler (entry to flows) ----------------
async def admin_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    if not is_admin(uid):
        await q.message.reply_text("⚠ Admin only")
        return ConversationHandler.END

    # Backup: send zip to chat
    if q.data == "admin_backup":
        await _send_backup_to_chat(q.message.chat.id, context)
        return ConversationHandler.END

    # Start add-coins flow
    if q.data == "admin_addcoins":
        await q.message.reply_text("➕ Send user_id:")
        return ADDCOINS_UID

    # Start broadcast flow
    if q.data == "admin_broadcast":
        await q.message.reply_text("📢 Send broadcast message:")
        return BC_TEXT

    # Upload hint (guide)
    if q.data == "admin_upload":
        await q.message.reply_text(
            "📷 Upload character by:\n"
            "1) Reply to an image with caption lines:\n"
            "   Name: ...\n   Rarity: ...\n   Faction: ...\n   Power: ...\n   Price: ...\n"
            "OR\n"
            "2) Send photo + use command:\n"
            "/upload Name|Rarity|Faction|Power|Price"
        )
        return ConversationHandler.END

    # Stats
    if q.data == "admin_stats":
        try:
            c.execute("SELECT COUNT(*) FROM users")
            users = c.fetchone()[0] or 0
            c.execute("SELECT COUNT(*) FROM characters")
            chars = c.fetchone()[0] or 0
            c.execute("SELECT IFNULL(SUM(coins),0) FROM users")
            coins = c.fetchone()[0] or 0
            text = (
                "📊 <b>Bot Stats</b>\n\n"
                f"👥 Users: {users}\n"
                f"🃏 Characters: {chars}\n"
                f"💰 Total Coins: {coins}"
            )
        except Exception as e:
            text = f"❌ Error reading stats: {e}"
        await q.message.reply_text(text, parse_mode="HTML")
        return ConversationHandler.END

    # Close
    if q.data == "admin_close":
        try:
            await q.message.delete()
        except:
            pass
        return ConversationHandler.END

# ---------------- Add Coins flow ----------------
async def addcoins_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        uid = int(text)
    except:
        await update.message.reply_text("❌ Send valid user_id (digits only)")
        return ADDCOINS_UID
    context.user_data["ac_uid"] = uid
    await update.message.reply_text("➕ Send amount:")
    return ADDCOINS_AMOUNT

async def addcoins_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        amount = int(text)
    except:
        await update.message.reply_text("❌ Send valid amount (digits only)")
        return ADDCOINS_AMOUNT
    target_uid = context.user_data.get("ac_uid")
    if target_uid is None:
        await update.message.reply_text("❌ No user_id found. Start again.")
        return ConversationHandler.END
    init_user(target_uid)
    add_coins(target_uid, amount)
    await update.message.reply_text(f"✅ Added {amount} coins to {target_uid}")
    context.user_data.clear()
    return ConversationHandler.END

# ---------------- Broadcast flow ----------------
async def bc_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("❌ Send a non-empty message")
        return BC_TEXT
    context.user_data["bc_text"] = text
    preview = f"📢 <b>Preview</b>\n\n{text}\n\nSend? (yes / no)"
    await update.message.reply_text(preview, parse_mode="HTML")
    return BC_CONFIRM

async def bc_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ans = update.message.text.strip().lower()
    if ans not in ("yes", "y"):
        await update.message.reply_text("❌ Broadcast cancelled")
        context.user_data.clear()
        return ConversationHandler.END
    text = context.user_data.get("bc_text", "")
    users = get_all_users()
    sent = 0
    for uid in users:
        try:
            await context.bot.send_message(uid, text)
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✅ Broadcast sent to {sent} users")
    context.user_data.clear()
    return ConversationHandler.END

# ---------------- Cancel fallback ----------------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operation canceled")
    context.user_data.clear()
    return ConversationHandler.END

# ---------------- ConversationHandler (entry via callback queries) ----------------
admin_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(admin_btn, pattern=r"^admin_")],
    states={
        ADDCOINS_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, addcoins_uid)],
        ADDCOINS_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, addcoins_amount)],
        BC_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bc_text)],
        BC_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, bc_confirm)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    allow_reentry=True,
    per_message=True,
)

# ---------------- Upload command (admin-only) ----------------
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

    args_text = " ".join(context.args).strip()

    # reply-with-caption mode
    if photo_msg and not args_text:
        caption = photo_msg.caption or ""
        if not caption:
            await update.message.reply_text("Reply to photo with caption or use /upload Name|Rarity|Faction|Power|Price")
            return
        data = {}
        for line in caption.splitlines():
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            data[k.strip().lower()] = v.strip()
        required = ["name", "rarity", "faction", "power", "price"]
        if not all(k in data for k in required):
            await update.message.reply_text("Caption must include name, rarity, faction, power, price")
            return
        try:
            power = int(data["power"]); price = int(data["price"])
        except:
            await update.message.reply_text("Power/Price must be numbers")
            return
        file_id = photo_msg.photo[-1].file_id
        new_id = insert_character(data["name"], data["rarity"], data["faction"], power, price, file_id)
        await update.message.reply_text(f"✅ Uploaded! ID: {new_id} Name: {data['name']}")
        return

    # pipe mode: require photo_msg + args_text
    if not photo_msg:
        await update.message.reply_text("📷 Send photo and use /upload or reply to photo with caption")
        return

    if args_text:
        parts = [p.strip() for p in args_text.split("|")]
        if len(parts) != 5:
            await update.message.reply_text("Usage: /upload Name|Rarity|Faction|Power|Price")
            return
        try:
            name, rarity, faction, power, price = parts
            power = int(power); price = int(price)
        except:
            await update.message.reply_text("Power/Price must be numbers")
            return
        file_id = photo_msg.photo[-1].file_id
        new_id = insert_character(name, rarity, faction, power, price, file_id)
        await update.message.reply_text(f"✅ Uploaded! ID: {new_id} Name: {name}")
        return

# ---------------- Backup command wrapper (command) ----------------
async def backup_cmd_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("⚠ Admin only")
        return
    await _send_backup_to_chat(update.effective_chat.id, context)

# ---------------- Addadmin (owner-only) ----------------
async def addadmin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != OWNER_ID:
        await update.message.reply_text("Owner only")
        return
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /addadmin <user_id>")
        return
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

# ---------------- Auto daily backup ----------------
BACKUP_DIR = "data/backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

async def auto_daily_backup(context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(DB_FILE):
        print("DB not found, skipping daily backup")
        return
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = os.path.join(BACKUP_DIR, f"backup_{now}.zip")
    try:
        with zipfile.ZipFile(backup_name, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(DB_FILE, arcname=os.path.basename(DB_FILE))
        print(f"✅ Auto daily backup created: {backup_name}")
        # notify owner
        OWNER = context.bot_data.get("OWNER_ID", OWNER_ID)
        try:
            await context.bot.send_message(OWNER, f"✅ Daily backup created:\n{backup_name}")
        except:
            pass
    except Exception as e:
        print(f"❌ Auto backup failed: {e}")

def start_auto_backup(app):
    # runs at 02:00 server time every day
    aiocron.crontab('0 2 * * *', func=lambda: app.create_task(auto_daily_backup(app)), start=True)
