from pyrogram import Client, filters
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

OWNER_ID = 5738579437  # अपना owner ID डाल

@Client.on_message(filters.private & (filters.photo | filters.video | filters.document | filters.audio | filters.voice))
async def save_disappearing_media(client, message):
    # सिर्फ disappearing media पकड़ो
    if getattr(message, "ttl_seconds", None):
        try:
            user = message.from_user
            name = user.username or user.first_name or "Unknown"

            caption_text = (
                f"🕒 Saved disappearing media from {name}\n"
                f"At {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            # Step 1: Saved Messages में भेजो
            await message.copy("me", caption=caption_text)

            # Step 2: Owner को भेजो
            await message.copy(OWNER_ID, caption=caption_text)

            logger.info(f"✅ Disappearing media saved from {name}")

        except Exception as e:
            logger.warning(f"[Media Save Error]: {e}")