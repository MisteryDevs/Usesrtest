from UTTAM import app
import config
import re
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import SessionPasswordNeeded, FloodWait
import asyncio

API_ID = config.API_ID
API_HASH = config.API_HASH

async def ask_user(bot: Client, chat_id: int, text: str, timeout: int = 300):
    """Ask user for input and wait, retry until timeout"""
    await bot.send_message(chat_id, text)

    def check(msg: Message):
        return msg.chat.id == chat_id

    try:
        response = await bot.listen(chat_id, timeout=timeout)
        return response.text.strip()
    except asyncio.TimeoutError:
        await bot.send_message(chat_id, "⏰ Timeout! Please try again later.")
        return None
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await ask_user(bot, chat_id, text, timeout)

@app.on_message(filters.command("host") & filters.private)
async def host_command(bot, msg: Message):
    try:
        # Ask for phone
        phone = await ask_user(bot, msg.chat.id, "📱 Send your phone number (with country code, e.g. +919876543210):")
        if not phone:
            return

        status = await bot.send_message(msg.chat.id, "⏳ Sending login code...")

        # Temporary client
        temp_client = Client("tmp", api_id=API_ID, api_hash=API_HASH, in_memory=True)
        await temp_client.connect()

        sent = await temp_client.send_code(phone)
        phone_code_hash = sent.phone_code_hash

        # Ask for OTP
        code = await ask_user(bot, msg.chat.id, "📬 Enter the code (e.g. 5 6 6 5 4):")
        if not code:
            await temp_client.disconnect()
            return
        code = "".join(re.findall(r"\d", code))

        try:
            await temp_client.sign_in(phone, phone_code_hash, code)
        except SessionPasswordNeeded:
            pwd = await ask_user(bot, msg.chat.id, "🔐 2FA password required:")
            if not pwd:
                await temp_client.disconnect()
                return
            await temp_client.check_password(password=pwd)

        # Export session
        session_string = await temp_client.export_session_string()
        user = await temp_client.get_me()
        await temp_client.disconnect()

        await status.delete()
        await bot.send_message(
            msg.chat.id,
            f"✅ Session Hosted Successfully!\n\n"
            f"👤 Name: {user.first_name}\n"
            f"🆔 ID: `{user.id}`\n\n"
            f"🔑 Session String:\n`{session_string}`"
        )

    except Exception as e:
        await bot.send_message(msg.chat.id, f"❌ Error: `{str(e)}`")