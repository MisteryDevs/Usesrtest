from pyrogram import Client, filters
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@Client.on_message(filters.private & filters.media)
async def save_disappearing_media(client, message):
    # ttl_seconds check करो (disappearing media है या नहीं)
    if getattr(message, "ttl_seconds", None):
        try:
            user = message.from_user
            name = user.username or user.first_name or "Unknown"
            logger.info(f"📥 Disappearing media from {name}")

            # Download file
            file = await message.download()

            # Send to "Saved Messages"
            await client.send_document(
                "me",
                file,
                caption=f"🕒 Saved disappearing media from\n @{name} \n at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except Exception as e:
            logger.warning(f"[Media Save Error]: {e}")