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

# DB helpers - make sure your db.py exports these
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

# ================= STATES =================
ADDCOINS_UID = 1
ADDCOINS_AMOUNT = 2
BC_TEXT = 10
BC_CONFIRM = 11

# ================= ADMIN PANEL =================
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
        ],
    ]

    await update.message.reply_text(
        "🛠 <b>Admin Panel</b>\nSelect action:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )

# ================= PANEL BUTTONS =================
async def admin_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    if not is_admin(uid):
        await q.message.reply_text("⚠ Admin only")
        return ConversationHandler.END

    # BACKUP
    if q.data == "admin_backup":
        # call backup command (wrap update to message-like object)
        await backup_cmd(update, context)
        return ConversationHandler.END

    # ADD COINS
    if q.data == "admin_addcoins":
        await q.message.reply_text("➕ Send user_id:")
        return ADDCOINS_UID

    # BROADCAST
    if q.data == "admin_broadcast":
        await q.message.reply_text("📢 Send broadcast message:")
        return BC_TEXT

    # UPLOAD HINT
    if q.data == "admin_upload":
        await q.message.reply_text(
            "📷 Upload usage:\n"
            "1) Reply to an image with caption lines:\n"
            "   Name: <name>\n"
            "   Rarity: <rarity>\n"
            "   Faction: <faction>\n"
            "   Power: <power>\n"
            "   Price: <price>\n\n"
            "OR\n"
            "2) Send photo and use command:\n"
            "/upload Name|Rarity|Faction|Power|Price"
        )
        return ConversationHandler.END

    # STATS
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

    # CLOSE
    if q.data == "admin_close":
        try:
            await q.message.delete()
        except:
            pass
        return ConversationHandler.END

# ================= ADD COINS WIZARD =================
async def addcoins_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # message handler (after pressing Add Coins)
    try:
        uid = int(update.message.text.strip())
        context.user_data["ac_uid"] = uid
    except:
        await update.message.reply_text("❌ Send valid user_id (numbers only)")
        return ADDCOINS_UID

    await update.message.reply_text("➕ Send amount:")
    return ADDCOINS_AMOUNT

async def addcoins_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text.strip())
    except:
        await update.message.reply_text("❌ Send valid amount (numbers only)")
        return ADDCOINS_AMOUNT

    uid = context.user_data.get("ac_uid")
    if uid is None:
        await update.message.reply_text("❌ Something went wrong. Restart with /admin")
        context.user_data.clear()
        return ConversationHandler.END

    init_user(uid)
    add_coins(uid, amount)

    await update.message.reply_text(f"✅ Added {amount} coins to {uid}")
    context.user_data.clear()
    return ConversationHandler.END

# ================= BROADCAST WIZARD =================
async def bc_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["bc_text"] = update.message.text
    preview = f"📢 <b>Preview</b>\n\n{update.message.text}\n\nSend? (yes / no)"
    await update.message.reply_text(preview, parse_mode="HTML")
    return BC_CONFIRM

async def bc_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ans = update.message.text.strip().lower()
    if ans not in ("yes", "y"):
        await update.message.reply_text("❌ Broadcast canceled")
        context.user_data.clear()
        return ConversationHandler.END

    text = context.user_data.get("bc_text", "")
    if not text:
        await update.message.reply_text("❌ No message found. Restart with /admin")
        return ConversationHandler.END

    users = get_all_users()
    sent = 0
    for u in users:
        try:
            await context.bot.send_message(u, text)
            sent += 1
        except:
            # ignore users who blocked the bot or errors
            pass

    await update.message.reply_text(f"✅ Broadcast sent to {sent} users")
    context.user_data.clear()
    return ConversationHandler.END

# ================= CANCEL =================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # works for /cancel
    await update.message.reply_text("❌ Operation canceled")
    context.user_data.clear()
    return ConversationHandler.END

# ================= UPLOAD COMMAND (admin-only) =================
# Keep upload_cmd as a direct command handler (no conversation)
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
        await update.message.reply_text("📷 Send photo with /upload or reply to a photo with the metadata.")
        return

    args_text = " ".join(context.args).strip()

    # caption mode (reply with caption lines "Name: ...")
    if not args_text:
        caption = photo_msg.caption or ""
        if not caption:
            await update.message.reply_text("Usage: reply to a photo with caption lines or use /upload Name|Rarity|Faction|Power|Price")
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

# ================= BACKUP (manual) =================
async def backup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # update may be CallbackQueryUpdate (when called from admin_btn) or normal Update
    # determine actor id
    actor_id = None
    if isinstance(update, Update) and update.callback_query:
        actor_id = update.callback_query.from_user.id
    else:
        try:
            actor_id = update.effective_user.id
        except:
            actor_id = None

    if not actor_id or not is_admin(actor_id):
        # if we cannot find admin, reply to chat if possible
        try:
            await update.effective_message.reply_text("⚠ Admin only")
        except:
            pass
        return

    if not os.path.exists(DB_FILE):
        await update.effective_message.reply_text("❌ DB file not found")
        return

    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{now}.zip"

    try:
        with zipfile.ZipFile(backup_name, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(DB_FILE, arcname=os.path.basename(DB_FILE))

        # send file
        await update.effective_chat.send_document(document=open(backup_name, "rb"), caption="✅ Database Backup")
        os.remove(backup_name)
    except Exception as e:
        await update.effective_message.reply_text(f"❌ Backup failed: {e}")

# ================= AUTO DAILY BACKUP =================
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

        # Notify owner if available
        OWNER = context.bot_data.get("OWNER_ID", OWNER_ID)
        try:
            await context.bot.send_message(OWNER, f"✅ Daily backup created:\n{backup_name}")
        except:
            pass
    except Exception as e:
        print(f"❌ Auto backup failed: {e}")

def start_auto_backup(app):
    """Schedule daily backup at 02:00 AM server time (cron style)."""
    # aiocron uses cron format: minute hour day month day-of-week
    aiocron.crontab('0 2 * * *', func=lambda: app.create_task(auto_daily_backup(app)), start=True)

# ================= CONVERSATION HANDLER =================
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
