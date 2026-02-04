# handlers/admin.py

import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
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
    c,
)
from config import DB_FILE


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
        ]
    ]

    await update.message.reply_text(
        "🛠 <b>Admin Panel</b>\nSelect action:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


# ================= PANEL BUTTONS =================

async def admin_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    if not is_admin(uid):
        await q.message.reply_text("⚠ Admin only")
        return ConversationHandler.END

# ----- BACKUP -----
    if q.data == "admin_backup":
        await backup_cmd(q.message, context)
        return ConversationHandler.END

    # ----- ADD COINS -----
    if q.data == "admin_addcoins":

        await q.message.reply_text("➕ Send user_id:")
        return ADDCOINS_UID


    # ----- BROADCAST -----
    if q.data == "admin_broadcast":

        await q.message.reply_text("📢 Send broadcast message:")
        return BC_TEXT


    # ----- UPLOAD HINT -----
    if q.data == "admin_upload":

        await q.message.reply_text(
            "📷 Use:\n"
            "/upload Name|Rarity|Faction|Power|Price\n"
            "or reply photo with caption."
        )
        return ConversationHandler.END


    # ----- STATS -----
    if q.data == "admin_stats":

        c.execute("SELECT COUNT(*) FROM users")
        users = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(*) FROM characters")
        chars = c.fetchone()[0] or 0

        c.execute("SELECT IFNULL(SUM(coins),0) FROM users")
        coins = c.fetchone()[0] or 0

        text = (
            "📊 <b>Bot Stats</b>\n\n"
            f"👥 Users: {users}\n"
            f"🃏 Chars: {chars}\n"
            f"💰 Coins: {coins}"
        )

        await q.message.reply_text(text, parse_mode="HTML")
        return ConversationHandler.END


    # ----- CLOSE -----
    if q.data == "admin_close":

        await q.message.delete()
        return ConversationHandler.END


# ================= ADD COINS WIZARD =================

async def addcoins_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        uid = int(update.message.text)
        context.user_data["ac_uid"] = uid
    except:
        await update.message.reply_text("❌ Send valid user_id")
        return ADDCOINS_UID

    await update.message.reply_text("➕ Send amount:")
    return ADDCOINS_AMOUNT


async def addcoins_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        amount = int(update.message.text)
    except:
        await update.message.reply_text("❌ Send valid amount")
        return ADDCOINS_AMOUNT

    uid = context.user_data["ac_uid"]

    init_user(uid)
    add_coins(uid, amount)

    await update.message.reply_text(
        f"✅ Added {amount} coins to {uid}"
    )

    context.user_data.clear()
    return ConversationHandler.END


# ================= BROADCAST WIZARD =================

async def bc_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    context.user_data["bc_text"] = text

    preview = (
        "📢 <b>Preview</b>\n\n"
        f"{text}\n\n"
        "Send? (yes / no)"
    )

    await update.message.reply_text(preview, parse_mode="HTML")
    return BC_CONFIRM


async def bc_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):

    ans = update.message.text.lower()

    if ans not in ["yes", "y"]:
        await update.message.reply_text("❌ Broadcast canceled")
        context.user_data.clear()
        return ConversationHandler.END


    text = context.user_data["bc_text"]

    from db import get_all_users   # must exist in db.py

    users = get_all_users()

    sent = 0

    for uid in users:
        try:
            await context.bot.send_message(uid, text)
            sent += 1
        except:
            pass

    await update.message.reply_text(
        f"✅ Broadcast sent to {sent} users"
    )

    context.user_data.clear()
    return ConversationHandler.END


# ================= CANCEL =================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("❌ Operation canceled")
    context.user_data.clear()

    return ConversationHandler.END


# ================= CONVERSATION HANDLER =================

admin_conv = ConversationHandler(

    entry_points=[
        CallbackQueryHandler(admin_btn, pattern=r"^admin_")
    ],

    states={

        ADDCOINS_UID: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, addcoins_uid)
        ],

        ADDCOINS_AMOUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, addcoins_amount)
        ],

        BC_TEXT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, bc_text)
        ],

        BC_CONFIRM: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, bc_confirm)
        ],
    },

    fallbacks=[
        CommandHandler("cancel", cancel)
    ],

    allow_reentry=True
)
# ================= BACKUP =================

import zipfile
from datetime import datetime


async def backup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    if not is_admin(uid):
        await update.message.reply_text("⚠ Admin only")
        return

    from config import DB_FILE

    if not os.path.exists(DB_FILE):
        await update.message.reply_text("❌ DB file not found")
        return


    now = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_name = f"backup_{now}.zip"


    try:
        with zipfile.ZipFile(backup_name, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(DB_FILE)


        await update.message.reply_document(
            document=open(backup_name, "rb"),
            caption="✅ Database Backup"
        )

        os.remove(backup_name)


    except Exception as e:

        await update.message.reply_text(
            f"❌ Backup failed:\n{e}"
        )
