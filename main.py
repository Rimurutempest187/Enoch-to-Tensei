import logging
from telegram.ext import ApplicationBuilder
from db import init_db
from handlers import register_handlers
from keep_alive import keep_alive
from config import BOT_TOKEN
from handlers.admin import start_auto_backup

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

def main():
    init_db()
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN missing in environment")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    register_handlers(app)

# save OWNER_ID in bot_data for notification
    app.bot_data["OWNER_ID"] = OWNER_ID

# start auto daily backup
    start_auto_backup(app)
    keep_alive()  # optional small web server

    logger.info("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
