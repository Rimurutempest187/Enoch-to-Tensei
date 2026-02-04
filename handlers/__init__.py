from telegram.ext import CommandHandler, CallbackQueryHandler
from .basic import start, balance, daily
from .summon import summon, summon10
from .store import store_cmd, store_btn, send_store
from .inventory import inventory_cmd, inv_btn
from .admin import addcoins_cmd, addadmin_cmd, upload_cmd
from db import is_admin
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

    # Admin
    app.add_handler(CommandHandler("upload", upload_cmd))
    app.add_handler(CommandHandler("addcoins", addcoins_cmd))
    # addadmin should be owner-only — check in callback
    def owner_only_addadmin(update, context):
        uid = update.effective_user.id
        if uid != OWNER_ID:
            return update.message.reply_text("Owner only")
        return addadmin_cmd(update, context)
    app.add_handler(CommandHandler("addadmin", owner_only_addadmin))
