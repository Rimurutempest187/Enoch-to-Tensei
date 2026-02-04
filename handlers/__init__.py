# handlers/__init__.py
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
)

# Basic
from .basic import start, balance, daily

# Summon
from .summon import summon, summon10

# Store
from .store import store_cmd, store_btn

# Inventory
from .inventory import inventory_cmd, inv_btn

# Player features
from .profile import profile_cmd
from .sell import sell_cmd
from .quest import quest_cmd, claimquest_cmd
from .duel import duel_cmd

# Admin
from .admin import (
    admin_cmd,
    admin_conv,
    backup_cmd,
    upload_cmd,
)

from db import add_admin
from config import OWNER_ID

def register_handlers(app):
    # Basic
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("daily", daily))

    # Summon
    app.add_handler(CommandHandler("summon", summon))
    app.add_handler(CommandHandler("summon10", summon10))

    # Store
    app.add_handler(CommandHandler("store", store_cmd))
    app.add_handler(CallbackQueryHandler(store_btn, pattern=r'^(buy_\d+|next_store)$'))

    # Inventory
    app.add_handler(CommandHandler("inventory", inventory_cmd))
    app.add_handler(CallbackQueryHandler(inv_btn, pattern=r'^inv_\d+$'))

    # Player features
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("sell", sell_cmd))
    app.add_handler(CommandHandler("quest", quest_cmd))
    app.add_handler(CommandHandler("claimquest", claimquest_cmd))
    app.add_handler(CommandHandler("duel", duel_cmd))

    # Admin panel & wizard
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(admin_conv)

    # Admin utilities
    app.add_handler(CommandHandler("backup", backup_cmd))
    app.add_handler(CommandHandler("upload", upload_cmd))

    # Owner-only addadmin wrapper
    async def owner_only_addadmin(update, context):
        uid = update.effective_user.id
        if uid != OWNER_ID:
            return await update.message.reply_text("Owner only")
        if len(context.args) != 1:
            return await update.message.reply_text("Usage: /addadmin <user_id>")
        try:
            target_id = int(context.args[0])
        except:
            return await update.message.reply_text("Invalid user_id")
        ok = add_admin(target_id)
        if ok:
            return await update.message.reply_text(f"✅ {target_id} added as admin")
        else:
            return await update.message.reply_text("User already admin or DB error")

    app.add_handler(CommandHandler("addadmin", owner_only_addadmin))
