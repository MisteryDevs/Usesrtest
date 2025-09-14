from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from UTTAM import app  # yahi tera main Client instance hai

# /start command
@app.on_message(filters.command("start"))
async def start_command(client, message):
    buttons = [
        [InlineKeyboardButton("📖 Help", callback_data="help_menu")],
        [InlineKeyboardButton("👑 Owner", url="https://t.me/rishu1286")],
    ]
    await message.reply_text(
        "👋 Hello! Ye mera start message hai.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# Callback handler
@app.on_callback_query()
async def callback_handler(client: Client, query: CallbackQuery):
    if query.data == "help_menu":
        buttons = [
            [InlineKeyboardButton("⬅ Back", callback_data="back_menu")]
        ]
        await query.message.edit_text(
            "📖 **Help Menu**\n\n- /start → Start info\n- /clone → Clone session",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif query.data == "back_menu":
        buttons = [
            [InlineKeyboardButton("📖 Help", callback_data="help_menu")],
            [InlineKeyboardButton("👑 Owner", url="https://t.me/rishu1286")],
        ]
        await query.message.edit_text(
            "👋 Hello! Ye mera start message hai.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # Ye zaroori hai warna callback silent fail ho jata hai
    await query.answer()