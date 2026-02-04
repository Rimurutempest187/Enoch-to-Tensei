# handlers/__init__.py
"""
Central handler registration.
Put this file in your handlers/ folder and import register_handlers(app)
from your main.py (where `app` is ApplicationBuilder().build()).
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

# Player features
from .profile import profile_cmd
from .sell import sell_cmd
from .quest import quest_cmd, claimquest_cmd
from .duel import duel_cmd

# Admin (panel + convo)
from .admin import (
    admin_cmd,
    admin_conv,
    admin_btn,
    backup_cmd,
)

# DB helper for owner-only addadmin wrapper
from db import add_admin
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

    # ---- Admin panel & wizard ----
    # /admin opens the inline admin panel
    app.add_handler(CommandHandler("admin", admin_cmd))
    # ConversationHandler for admin wizards (add coins, broadcast, ...)
    app.add_handler(admin_conv)
    # If admin buttons need a separate CallbackQueryHandler entry point (not required because admin_conv uses CallbackQueryHandler as entry),
    # you can still register admin_btn for direct callback handling:
    # app.add_handler(CallbackQueryHandler(admin_btn, pattern=r'^admin_'))

    # ---- Admin utilities ----
    # /backup (admin-only) - implemented in handlers.admin.backup_cmd
    app.add_handler(CommandHandler("backup", backup_cmd))

    # ---- Owner-only addadmin (wrapper) ----
    async def owner_only_addadmin(update, context):
        uid = update.effective_user.id
        if uid != OWNER_ID:
            return await update.message.reply_text("Owner only")
        # Expect: /addadmin <user_id>
        if len(context.args) != 1:
            return await update.message.reply_text("Usage: /addadmin <user_id>")
        try:
            target_id = int(context.args[0])
        except:
            return await update.message.reply_text("Invalid user_id")
        ok = add_admin(target_id)
        if ok:
            await update.message.reply_text(f"✅ {target_id} added as admin")
        else:
            await update.message.reply_text("User already admin or DB error")

    app.add_handler(CommandHandler("addadmin", owner_only_addadmin))

    # ---- Notes ----
    # - Do not register duplicate handlers (e.g., if you previously had a separate addcoins_cmd,
    #   the wizard handles add-coins flow via admin_conv).
    # - If you want broadcast or backup to be available only via the admin panel buttons,
    #   you may omit the CommandHandler registrations and rely solely on the panel.
