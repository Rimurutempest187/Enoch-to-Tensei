# main.py

import logging
from telegram.ext import ApplicationBuilder
from db import init_db
from handlers import register_handlers
from keep_alive import keep_alive  # optional; keep if you have keep_alive.py
from config import BOT_TOKEN, OWNER_ID

# admin auto-backup starter
from handlers.admin import start_auto_backup

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

def main():
    init_db()

    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN missing in environment")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    register_handlers(app)

    # expose OWNER_ID to bot_data for notifications
    app.bot_data["OWNER_ID"] = OWNER_ID

    # start auto daily backup (non-blocking)
    try:
        start_auto_backup(app)
        logger.info("Auto daily backup scheduled.")
    except Exception as e:
        logger.warning(f"start_auto_backup failed: {e}")

    # optional keep-alive web server (if implemented)
    try:
        keep_alive()
    except Exception:
        pass

    logger.info("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
