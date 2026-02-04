import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "1812962224"))

DATA_DIR = "data"
DB_FILE = f"{DATA_DIR}/bot.db"

START_COINS = 200
DAILY_REWARD = 100

SUMMON_COST = 25
TEN_SUMMON_COST = 220

INV_PAGE = 8

RARITY_RATE = {
    "Common": 55,
    "Rare": 25,
    "Epic": 15,
    "Legendary": 5
}
