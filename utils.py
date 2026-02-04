import random
from config import RARITY_RATE

def roll_rarity():
    r = random.randint(1, 100)
    total = 0
    for k, v in RARITY_RATE.items():
        total += v
        if r <= total:
            return k
    return "Common"

def format_char(row):
    # row = (id, name, rarity, faction, power, price, file_id)
    return (
        f"🆔 ID: {row[0]}\n"
        f"✨ Name: {row[1]}\n"
        f"⭐ Rarity: {row[2]}\n"
        f"🏹 Faction: {row[3]}\n"
        f"💪 Power: {row[4]}\n"
        f"💰 Price: {row[5]}"
    )
