from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import get_all_characters, get_character, add_inventory, get_coins, init_user, add_coins
from utils import format_char
import random

async def send_store(chat_id, context):
    chars = get_all_characters()
    if not chars:
        await context.bot.send_message(chat_id, "⚠ Store empty")
        return
    char = random.choice(chars)
    keyboard = [[
        InlineKeyboardButton("Buy", callback_data=f"buy_{char[0]}"),
        InlineKeyboardButton("Next", callback_data="next_store")
    ]]
    await context.bot.send_photo(chat_id, char[6], caption=format_char(char),
                                 reply_markup=InlineKeyboardMarkup(keyboard))

async def store_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_store(update.effective_chat.id, context)

async def store_btn(update, context):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    init_user(uid)

    if q.data == "next_store":
        await q.message.delete()
        await send_store(q.message.chat.id, context)
        return

    if q.data.startswith("buy_"):
        cid = int(q.data.split("_",1)[1])
        char = get_character(cid)
        if not char:
            await q.edit_message_caption("❌ Character မတွေ့ပါ")
            return
        coins = get_coins(uid)
        price = char[5]
        if coins < price:
            await q.edit_message_caption("❌ Coins မလုံလောက်ပါ")
            return
        add_coins(uid, -price)
        add_inventory(uid, cid)
        await q.edit_message_caption(f"✅ {char[1]} ကို ဝယ်ယူပြီးပါပြီ")
