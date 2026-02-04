from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import get_inventory, init_user
from config import INV_PAGE

def build_pages(rows, per_page):
    pages = [rows[i:i+per_page] for i in range(0, len(rows), per_page)]
    return pages

async def inventory_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    init_user(uid)
    rows = get_inventory(uid)
    if not rows:
        await update.message.reply_text("📦 Inventory empty")
        return
    pages = build_pages(rows, INV_PAGE)
    await send_inventory_page(update.effective_chat.id, context, pages, 0)

async def send_inventory_page(chat_id, context, pages, idx):
    page = pages[idx]
    text = f"📦 Inventory Page {idx+1}/{len(pages)}\n\n"
    for i, row in enumerate(page, 1):
        cid, name, rarity, count = row
        text += f"{i}. {name} ({rarity}) x{count} — ID:{cid}\n"
    buttons = []
    nav = []
    if idx > 0:
        nav.append(InlineKeyboardButton("⬅ Prev", callback_data=f"inv_{idx-1}"))
    if idx < len(pages)-1:
        nav.append(InlineKeyboardButton("Next ➡", callback_data=f"inv_{idx+1}"))
    if nav:
        buttons.append(nav)
    reply_markup = InlineKeyboardMarkup(buttons) if buttons else None
    await context.bot.send_message(chat_id, text, reply_markup=reply_markup)

async def inv_btn(update, context):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    rows = get_inventory(uid)
    if not rows:
        await q.message.reply_text("📦 Inventory empty")
        return
    try:
        idx = int(q.data.split("_",1)[1])
    except:
        idx = 0
    pages = build_pages(rows, INV_PAGE)
    await q.message.delete()
    await send_inventory_page(q.message.chat.id, context, pages, idx)
