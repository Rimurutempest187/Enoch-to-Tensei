# main.py
import logging
from telegram.ext import ApplicationBuilder
from db import init_db
from handlers import register_handlers
from keep_alive import keep_alive
from config import BOT_TOKEN, OWNER_ID
from handlers.admin import start_auto_backup

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

def main():
    init_db()

    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN missing in environment")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # register handlers
    register_handlers(app)

    # save OWNER_ID for notifications
    app.bot_data["OWNER_ID"] = OWNER_ID

    # start auto backups (safe guarded)
    try:
        start_auto_backup(app)
        logger.info("Auto daily backup scheduled.")
    except Exception as e:
        logger.warning(f"Failed to schedule auto backup: {e}")

    # keep alive (optional)
    try:
        keep_alive()
    except Exception:
        pass

    logger.info("Bot started, running polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
