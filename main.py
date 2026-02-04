# main.py

import logging
from telegram.ext import ApplicationBuilder
from db import init_db
from handlers import register_handlers
from keep_alive import keep_alive
from config import BOT_TOKEN, OWNER_ID

# admin auto-backup starter (if implemented in handlers/admin.py)
from handlers.admin import start_auto_backup

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def main():
    # initialize db (create tables if not exists)
    init_db()

    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN missing in environment")

    # build telegram application
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # register command / callback handlers (from handlers package)
    register_handlers(app)

    # expose OWNER_ID to bot_data for use by handlers (notifications, backup messages, etc.)
    app.bot_data["OWNER_ID"] = OWNER_ID

    # start auto daily backup task (if you implemented start_auto_backup)
    try:
        start_auto_backup(app)
        logger.info("Auto daily backup scheduled (if configured).")
    except Exception as e:
        logger.warning(f"start_auto_backup failed to start: {e}")

    # optional small webserver to keep the process alive (Replit/Glitch/etc.)
    try:
        keep_alive()
    except Exception as e:
        logger.warning(f"keep_alive() failed: {e}")

    logger.info("Bot started, polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
