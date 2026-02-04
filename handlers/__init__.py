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
    admin_btn,
    admin_conv,
    backup_cmd_command,
    upload_cmd,
    addadmin_cmd,
    start_auto_backup,
)

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
    app.add_handler(admin_conv)  # register ConversationHandler (entry via CallbackQueryHandler)
    # also register admin button callback explicitly (safe)
    app.add_handler(CallbackQueryHandler(admin_btn, pattern=r'^admin_'))

    # Admin direct commands
    app.add_handler(CommandHandler("backup", backup_cmd_command))
    app.add_handler(CommandHandler("upload", upload_cmd))
    app.add_handler(CommandHandler("addadmin", addadmin_cmd))
