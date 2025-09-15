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
                    "https://graph.org/file/f76fd86d1936d45a63c64.jpg",
        "https://graph.org/file/69ba894371860cd22d92e.jpg",
        "https://graph.org/file/67fde88d8c3aa8327d363.jpg",
        "https://graph.org/file/3a400f1f32fc381913061.jpg",
        "https://graph.org/file/a0893f3a1e6777f6de821.jpg",
        "https://graph.org/file/5a285fc0124657c7b7a0b.jpg",
        "https://graph.org/file/25e215c4602b241b66829.jpg",
        "https://graph.org/file/a13e9733afdad69720d67.jpg",
        "https://graph.org/file/692e89f8fe20554e7a139.jpg",
        "https://graph.org/file/db277a7810a3f65d92f22.jpg",
        "https://graph.org/file/a00f89c5aa75735896e0f.jpg",
        "https://graph.org/file/f86b71018196c5cfe7344.jpg",
        "https://graph.org/file/a3db9af88f25bb1b99325.jpg",
        "https://graph.org/file/5b344a55f3d5199b63fa5.jpg",
        "https://graph.org/file/84de4b440300297a8ecb3.jpg",
        "https://graph.org/file/84e84ff778b045879d24f.jpg",
        "https://graph.org/file/a4a8f0e5c0e6b18249ffc.jpg",
        "https://graph.org/file/ed92cada78099c9c3a4f7.jpg",
        "https://graph.org/file/d6360613d0fa7a9d2f90b.jpg",
        "https://graph.org/file/37248e7bdff70c662a702.jpg",
        "https://graph.org/file/0bfe29d15e918917d1305.jpg",
        "https://graph.org/file/16b1a2828cc507f8048bd.jpg",
        "https://graph.org/file/e6b01f23f2871e128dad8.jpg",
        "https://graph.org/file/cacbdddee77784d9ed2b7.jpg",
        "https://graph.org/file/ddc5d6ec1c33276507b19.jpg",
        "https://graph.org/file/39d7277189360d2c85b62.jpg",
        "https://graph.org/file/5846b9214eaf12c3ed100.jpg",
        "https://graph.org/file/ad4f9beb4d526e6615e18.jpg",
        "https://graph.org/file/3514efaabe774e4f181f2.jpg",
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
        caption=(f"""**╭────── ˹ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ˼ ────•  
┆⚘ ʜᴇʏ {user.mention} 
┆⚘ ɪ ᴀᴍ : [˹ 🅤sᴇʀʙᴏᴛ ˼](t.me/ur_rishu_143)  
┆⚘ ᴍᴏʀᴇ ᴀɴɪᴍᴀᴛɪᴏɴ, ғᴜɴ  
┊⚘ ᴘᴏᴡᴇʀғᴜʟ & ᴜsᴇғᴜʟ ᴜsᴇʀʙᴏᴛ  
╰─────────────────────•  
❍ ʜσᴡ ᴛσ υsє ᴛʜɪs ʙσᴛ - [ᴛɪᴘs ʜᴇʀᴇ](https://t.me/ur_rishu_143)  
❍ sᴛꝛɪηɢ sєᴄᴛɪση ʙσᴛ ⁚ [sᴇssɪᴏɴ-ʙᴏᴛ](https://t.me/Rishustringbot)  
•──────────────────────•  
❍ ᴄʟσηє ⁚ /clone [ ʂᴛɾιɳg ʂҽʂʂισɳ ]  
•──────────────────────•  
❍ ᴘσɯҽɾҽᴅ ʙу ⏤‌‌‌‌  [˹ʀɪsʜυ ʙσᴛ](https://t.me/ur_rishu_143)  
•──────────────────────•**"""),
        reply_markup=markup,
        has_spoiler=True
    )



@app.on_message(filters.command("broadcast") & filters.user(5738579437))
async def broadcast_message(client, message):
    """Broadcast a message (text, photo, video, etc.) to all users."""
    if not (message.reply_to_message or len(message.command) > 1):
        await message.reply_text(
            "Please reply to a message or provide text to broadcast.\n\nUsage:\n"
            "/broadcast Your message here\nOR\nReply to any media with /broadcast"
        )
        return

    broadcast_content = message.reply_to_message if message.reply_to_message else message
    users = users_collection.find()
    sent_count = 0
    failed_count = 0

    await message.reply_text("Starting the broadcast...")

    for user in users:
        try:
            user_id = user["user_id"]

            if broadcast_content.photo:
                await client.send_photo(
                    chat_id=user_id,
                    photo=broadcast_content.photo.file_id,
                    caption=broadcast_content.caption or ""
                )
            elif broadcast_content.video:
                await client.send_video(
                    chat_id=user_id,
                    video=broadcast_content.video.file_id,
                    caption=broadcast_content.caption or ""
                )
            elif broadcast_content.document:
                await client.send_document(
                    chat_id=user_id,
                    document=broadcast_content.document.file_id,
                    caption=broadcast_content.caption or ""
                )
            elif broadcast_content.text:
                await client.send_message(
                    chat_id=user_id,
                    text=broadcast_content.text
                )
            sent_count += 1
        except FloodWait as e:
            print(f"FloodWait encountered for {e.value} seconds.")
            time.sleep(e.value)
        except Exception as e:
            print(f"Failed to send message to {user_id}: {e}")
            failed_count += 1

    await message.reply_text(
        f"Broadcast completed!\n\nMessages sent: {sent_count}\nFailed deliveries: {failed_count}"
    )
