from UTTAM import app, API_ID, API_HASH
from config import ALIVE_PIC
from pyrogram import filters
import os
import re
import asyncio
import time
from pyrogram import *
from pyrogram.types import * 

PHONE_NUMBER_TEXT = (
    """**╭────── ˹ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ˼ ────•\n┆⚘ ʜᴇʏ, ɪ ᴀᴍ : [˹ 🅤sᴇʀʙᴏᴛ ˼](t.me/ur_rishu_143)\n┆⚘ ᴍᴏʀᴇ ᴀɴɪᴍᴀᴛɪᴏɴ,ғᴜɴ\n┊⚘ ᴘᴏᴡᴇʀғᴜʟ & ᴜsᴇғᴜʟ ᴜsᴇʀʙᴏᴛ\n╰─────────────────────•\n❍ ʜσᴡ ᴛσ υsє ᴛʜɪs ʙσᴛ - [ᴛɪᴘs ʜᴇʀᴇ](https://t.me/ur_rishu_143) \n❍ sᴛꝛɪηɢ sєᴄᴛɪση ʙσᴛ ⁚ [sᴇssɪᴏɴ-ʙᴏᴛ](https://t.me/Rishustringbot) \n•──────────────────────•\n❍ ᴄʟσηє ⁚ /clone [ ʂᴛɾιɳg ʂҽʂʂισɳ ]\n•──────────────────────•\n❍ ᴘσɯҽɾҽᴅ ʙу ⏤‌‌‌‌  [˹ʀɪsʜυ ʙσᴛ](https://t.me/ur_rishu_143) \n•──────────────────────•**"""
)

@app.on_message(filters.command("start"))
async def hello(client: app, message):
    buttons = [
           [
                InlineKeyboardButton("˹ ᴏᴡɴᴇʀ ˼", url="https://t.me/rishu1286"),
                InlineKeyboardButton("˹ ᴜᴘᴅᴀᴛᴇ ˼", url="https://t.me/ur_rishu_143"),
            ],
            [
                InlineKeyboardButton("˹ sᴜᴘᴘᴏʀᴛ ˼", url="https://t.me/vip_robotz"),
                InlineKeyboardButton("˹ ᴍᴜsɪᴄ ˼", url="https://t.me/sanataniiMusicBot"),
            ],
            ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await client.send_photo(message.chat.id, ALIVE_PIC, caption=PHONE_NUMBER_TEXT, reply_markup=reply_markup)

