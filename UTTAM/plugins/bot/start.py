from UTTAM import app, API_ID, API_HASH
from config import ALIVE_PIC
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

PHONE_NUMBER_TEXT = (
    """**╭────── ˹ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ˼ ────•\n┆⚘ ʜᴇʏ, ɪ ᴀᴍ : [˹ 🅤sᴇʀʙᴏᴛ ˼](t.me/ur_rishu_143)\n┆⚘ ᴍᴏʀᴇ ᴀɴɪᴍᴀᴛɪᴏɴ,ғᴜɴ\n┊⚘ ᴘᴏᴡᴇʀғᴜʟ & ᴜsᴇғᴜʟ ᴜsᴇʀʙᴏᴛ\n╰─────────────────────•\n❍ ʜσᴡ ᴛσ υsє ᴛʜɪs ʙσᴛ - [ᴛɪᴘs ʜᴇʀᴇ](https://t.me/ur_rishu_143) \n❍ sᴛꝛɪηɢ sєᴄᴛɪση ʙσᴛ ⁚ [sᴇssɪᴏɴ-ʙᴏᴛ](https://t.me/Rishustringbot) \n•──────────────────────•\n❍ ᴄʟσηє ⁚ /clone [ ʂᴛɾιɳg ʂҽʂʂισɳ ]\n•──────────────────────•\n❍ ᴘσɯҽɾҽᴅ ʙу ⏤‌‌‌‌  [˹ʀɪsʜυ ʙσᴛ](https://t.me/ur_rishu_143) \n•──────────────────────•**"""
)

HELP_TEXT = """**╭─ ˹ ʜᴇʟᴘ ᴍᴇɴᴜ ˼ ─╮**
‣ /start → Start bot info  
‣ /clone → Clone string session  
‣ More features coming soon...
**╰─────────────────╯**"""

def start_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("˹ ᴏᴡɴᴇʀ ˼", url="https://t.me/rishu1286"),
            InlineKeyboardButton("˹ ᴜᴘᴅᴀᴛᴇ ˼", url="https://t.me/ur_rishu_143"),
        ],
        [
            InlineKeyboardButton("˹ sᴜᴘᴘᴏʀᴛ ˼", url="https://t.me/vip_robotz"),
            InlineKeyboardButton("˹ ᴍᴜsɪᴄ ˼", url="https://t.me/sanataniiMusicBot"),
        ],
        [
            InlineKeyboardButton("˹ ʜᴇʟᴘ ˼", callback_data="help_menu"),
        ],
    ])

def help_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="back_menu")]
    ])

# Start Command
@app.on_message(filters.command("start"))
async def hello(client, message):
    await message.reply_photo(
        ALIVE_PIC,
        caption=PHONE_NUMBER_TEXT,
        reply_markup=start_buttons()
    )

# Help Callback
@app.on_callback_query(filters.regex("help_menu"))
async def help_callback(client, query: CallbackQuery):
    await query.message.reply_text(
        HELP_TEXT,
        reply_markup=help_buttons()
    )

# Back Callback
@app.on_callback_query(filters.regex("back_menu"))
async def back_callback(client, query: CallbackQuery):
    await query.message.reply_photo(
        ALIVE_PIC,
        caption=PHONE_NUMBER_TEXT,
        reply_markup=start_buttons()
    )