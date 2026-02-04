# handlers/__init__.py
"""
Register all Telegram command & callback handlers here.

Usage:
    from handlers import register_handlers
    register_handlers(app)   # where `app` is ApplicationBuilder().build()
"""

from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# Basic
from .basic import start, balance, daily

# Summon
from .summon import summon, summon10

# Store
from .store import store_cmd, store_btn, send_store

# Inventory
from .inventory import inventory_cmd, inv_btn

# Admin (ensure admin.py exports these)
from .admin import (
    admin_cmd,        # opens the admin panel (inline keyboard)
    admin_btn,        # handles admin panel button callbacks
    addcoins_cmd,
    addadmin_cmd,
    upload_cmd,
)

# Player features
from .profile import profile_cmd
from .sell import sell_cmd
from .quest import quest_cmd, claimquest_cmd
from .duel import duel_cmd

# Optional: broadcast, ban, backup handlers if you implement them
# from .admin import broadcast_cmd, ban_cmd, backup_cmd

# Config / helpers (for owner checks if needed)
from db import is_admin
from config import OWNER_ID


def register_handlers(app):
    # ---- Basic ----
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("daily", daily))

    # ---- Summon ----
    app.add_handler(CommandHandler("summon", summon))
    app.add_handler(CommandHandler("summon10", summon10))

    # ---- Store ----
    app.add_handler(CommandHandler("store", store_cmd))
    app.add_handler(CallbackQueryHandler(store_btn, pattern=r'^(buy_\d+|next_store)$'))

    # ---- Inventory ----
    app.add_handler(CommandHandler("inventory", inventory_cmd))
    app.add_handler(CallbackQueryHandler(inv_btn, pattern=r'^inv_\d+$'))

    # ---- Player features ----
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("sell", sell_cmd))
    app.add_handler(CommandHandler("quest", quest_cmd))
    app.add_handler(CommandHandler("claimquest", claimquest_cmd))
    app.add_handler(CommandHandler("duel", duel_cmd))

    # ---- Admin commands & panel ----
    # Admin panel (inline keyboard)
    app.add_handler(CommandHandler("admin", admin_cmd))
    # admin panel buttons (prefix "admin_")
    app.add_handler(CallbackQueryHandler(admin_btn, pattern=r'^admin_'))

    # Admin action commands (also kept available)
    app.add_handler(CommandHandler("upload", upload_cmd))
    app.add_handler(CommandHandler("addcoins", addcoins_cmd))

    # addadmin should be owner-only — wrap or check ownership here
    def owner_only_addadmin(update, context):
        uid = update.effective_user.id
        if uid != OWNER_ID:
            return update.message.reply_text("Owner only")
        return addadmin_cmd(update, context)

    app.add_handler(CommandHandler("addadmin", owner_only_addadmin))

    # ---- Optional: fallback / help ----
    # If you want to catch unknown commands, uncomment and implement unknown_cmd
    # app.add_handler(MessageHandler(filters.COMMAND, unknown_cmd))

    # Keep handlers registration centralized — add new handlers here.
