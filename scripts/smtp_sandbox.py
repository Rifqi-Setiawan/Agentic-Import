"""Loopback-only SMTP sink for fictional demo mail; never relays externally.

The saved .eml is evidence of SMTP receipt, not delivery to an external inbox.
"""
import asyncio
import logging
import os
import uuid
from pathlib import Path

MAILBOX = Path(__file__).resolve().parents[1] / "private" / "mail-sandbox"
MAX_MESSAGE_BYTES = 1024 * 1024
LOGGER = logging.getLogger("imporjaga.smtp_sandbox")


async def handle_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    async def reply(message: str):
        writer.write((message + "\r\n").encode("ascii"))
        await writer.drain()

    sender = None
    recipients = []
    await reply("220 localhost ImporJaga demo SMTP sink (no external relay)")
    try:
        while not reader.at_eof():
            line = await asyncio.wait_for(reader.readline(), timeout=60)
            if not line:
                break
            command = line.decode("ascii", errors="replace").strip()
            verb = command.split(" ", 1)[0].upper()
            if verb in ("EHLO", "HELO"):
                await reply("250-localhost")
                await reply("250 SIZE 1048576")
            elif verb == "MAIL":
                sender = command[5:]
                recipients = []
                await reply("250 Sender accepted for local sandbox")
            elif verb == "RCPT" and sender is not None:
                recipients.append(command[5:])
                await reply("250 Recipient accepted for local sandbox")
            elif verb == "DATA" and recipients:
                await reply("354 End with <CRLF>.<CRLF>")
                content = bytearray()
                too_large = False
                while True:
                    data = await asyncio.wait_for(reader.readline(), timeout=60)
                    if not data:
                        raise ConnectionError("Client disconnected before end of DATA")
                    if data == b".\r\n":
                        break
                    if data.startswith(b".."):
                        data = data[1:]
                    if len(content) + len(data) <= MAX_MESSAGE_BYTES:
                        content.extend(data)
                    else:
                        too_large = True
                if too_large:
                    await reply("552 Demo message exceeds 1 MB")
                else:
                    MAILBOX.mkdir(mode=0o700, parents=True, exist_ok=True)
                    message_id = uuid.uuid4().hex
                    target = MAILBOX / f"{message_id}.eml"
                    with target.open("xb") as stream:
                        stream.write(content)
                    os.chmod(target, 0o600)
                    LOGGER.info("SMTP sandbox receipt id=%s bytes=%s", message_id, len(content))
                    await reply(f"250 Sandbox receipt id={message_id}; not externally delivered")
                sender = None
                recipients = []
            elif verb == "RSET":
                sender = None
                recipients = []
                await reply("250 Reset")
            elif verb == "NOOP":
                await reply("250 OK")
            elif verb == "QUIT":
                await reply("221 Bye")
                break
            else:
                await reply("503 Command unavailable or invalid sequence")
    except (TimeoutError, ConnectionError, ValueError):
        LOGGER.warning("SMTP sandbox connection closed before completion")
    finally:
        writer.close()
        await writer.wait_closed()


async def main():
    logging.basicConfig(level=logging.INFO)
    server = await asyncio.start_server(handle_connection, "127.0.0.1", 1025, limit=65536)
    LOGGER.info("Demo SMTP sink listening at 127.0.0.1:1025; no external relay")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
