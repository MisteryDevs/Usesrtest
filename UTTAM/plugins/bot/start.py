from UTTAM import app
import config 
import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant, ChatAdminRequired
import time
from flask import Flask
from threading import Thread
import pymongo
import random

# Bot details from environment variables
CHANNEL_1_USERNAME = "Ur_Rishu_143"  # First channel username
CHANNEL_2_USERNAME = "Vip_robotz"    # Second channel username

ADMIN_ID = int(os.getenv("ADMIN_ID", "5738579437"))  # Admin ID for new user notifications

# Flask app for monitoring
flask_app = Flask(__name__)
start_time = time.time()

# MongoDB setup
mongo_client = pymongo.MongoClient(os.getenv("MONGO_URL"))
db = mongo_client[os.getenv("MONGO_DB_NAME", "Rishtu-free-db")]
users_collection = db[os.getenv("MONGO_COLLECTION_NAME", "users")]

# ---- FORCE JOIN CHECK ----
async def is_user_in_channel(client, user_id: int, channel_username: str) -> bool:
    try:
        member = await client.get_chat_member(channel_username, user_id)
        return member.status not in ["kicked", "left"]
    except UserNotParticipant:
        return False
    except ChatAdminRequired:
        # Bot ko admin hona chahiye agar channel private hai
        return False
    except Exception as e:
        print(f"Error while checking user in {channel_username}: {e}")
        return False

# ---- JOIN PROMPT ----
async def send_join_prompt(client, chat_id):
    join_button_1 = InlineKeyboardButton("♡ Join ♡", url=f"https://t.me/{CHANNEL_1_USERNAME}")
    join_button_2 = InlineKeyboardButton("♡ Join ♡", url=f"https://t.me/{CHANNEL_2_USERNAME}")
    markup = InlineKeyboardMarkup([[join_button_1], [join_button_2]])
    await client.send_message(
        chat_id,
        "♡ You need to join both channels to use this bot.. ♡",
        reply_markup=markup,
    )

# ---- START ROUTE FOR FLASK ----
@flask_app.route('/hh')
def home():
    uptime_minutes = (time.time() - start_time) / 60
    user_count = users_collection.count_documents({})
    return f"Bot uptime: {uptime_minutes:.2f} minutes\nUnique users: {user_count}"

# ---- START COMMAND ----
@app.on_message(filters.command("start"))
async def start_message(client, message):
    user_id = message.from_user.id
    user = message.from_user

    # Simulate progress
    baby = await message.reply_text("[□□□□□□□□□□] 0%")
    progress = [
        "[■□□□□□□□□□] 10%", "[■■□□□□□□□□] 20%", "[■■■□□□□□□□] 30%", "[■■■■□□□□□□] 40%",
        "[■■■■■□□□□□] 50%", "[■■■■■■□□□□] 60%", "[■■■■■■■□□□] 70%", "[■■■■■■■■□□] 80%",
        "[■■■■■■■■■□] 90%", "[■■■■■■■■■■] 100%"
    ]
    for step in progress:
        await baby.edit_text(f"**{step}**")
        await asyncio.sleep(0.3)

    await baby.edit_text("**❖ Jᴀʏ sʜʀᴇᴇ ʀᴀᴍ 🚩...**")
    await asyncio.sleep(1)
    await baby.delete()

    # Force join check
    if not (await is_user_in_channel(client, user_id, CHANNEL_1_USERNAME) and
            await is_user_in_channel(client, user_id, CHANNEL_2_USERNAME)):
        await send_join_prompt(client, message.chat.id)
        return

    # New user check
    if users_collection.count_documents({'user_id': user_id}) == 0:
        users_collection.insert_one({'user_id': user_id})
        await client.send_message(
            chat_id=ADMIN_ID,
            text=(f"╔═══ ⋆ʟᴏᴠᴇ ᴡɪᴛʜ⋆ ══╗\n\n💡 **New User Alert**:\n\n"
                  f"👤 **User:** {message.from_user.mention}\n\n"
                  f"🆔 **User ID:** {user_id}\n\n"
                  f"📊 **Total Users:** {users_collection.count_documents({})}\n\n╚═════ ⋆★⋆ ═════╝")
        )

    # Random image
    image_urls = [
        "https://te.legra.ph/file/e39f523acdff582a038a0-3c18ee0d2867947e54.jpg",
        "https://te.legra.ph/file/06055cba18cb7ccebfb45-11fb6855ffc84a3673.jpg",
        "https://te.legra.ph/file/5f168341b6cd181b9bf0b-26aba72cbc5dc82cde.jpg",
        "https://envs.sh/rOk.jpg"
    ]
    random_image = random.choice(image_urls)

    # Buttons
    join_button_1 = InlineKeyboardButton("˹sυᴘᴘσꝛᴛ˼", url="https://t.me/Ur_rishu_143")
    join_button_2 = InlineKeyboardButton("˹ᴧʟʟ ʙσᴛ˼", url="https://t.me/vip_robotz/4")
    music_button = InlineKeyboardButton("˹ϻυsɪᴄ ʙσᴛ˼", url="https://t.me/vip_music_vc_bot")
    repo_button = InlineKeyboardButton("˹ ʀєᴘσ ˼", url="https://github.com/RishuBot/RishuString")
    help_button = InlineKeyboardButton(" ˹ ɢєηєꝛᴧᴛє sᴛꝛɪηɢ ˼", url="t.me/rishu1286")

    markup = InlineKeyboardMarkup([[help_button],[join_button_1,join_button_2],[music_button,repo_button]])

    # Send welcome
    await client.send_photo(
        chat_id=message.chat.id,
        photo=random_image,
        caption=(f"""**┌────── ˹ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ˼──────•
┆◍ ʜᴇʏ {user.mention} 
└──────────────────────•
 ✦ ɪ'ᴍ ᴀ sᴛʀɪɴɢ ɢᴇɴᴇʀᴀᴛᴇ ʙᴏᴛ.
 ✦ ʏᴏᴜ ᴄᴀɴ ᴜsᴇ ɢᴇɴᴇʀᴀᴛᴇ sᴇssɪᴏɴ.
 ✦ 𝛅ᴜᴘᴘᴏʀᴛ - ᴘʏʀᴏɢʀᴀᴍ | ᴛᴇʟᴇᴛʜᴏɴ.
 ✦ ηᴏ ɪᴅ ʟᴏɢ ᴏᴜᴛ ɪssᴜᴇ.

•──────────────────────•
 ❖ 𝐏ᴏᴡᴇʀᴇᴅ ʙʏ  :-  [˹ʀɪsʜυ-ʙσᴛ ](https://t.me/ur_rishu_143) ❤️‍🔥
•──────────────────────•**"""),
        reply_markup=markup
    )