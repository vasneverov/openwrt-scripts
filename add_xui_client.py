#!/usr/bin/env python3
"""Add client to X-UI panel via API"""
import asyncio
import aiohttp
import ssl
import json
import sys

# Panel credentials
PANEL_IP = "5.35.84.151"
PANEL_PORT = "5050"
USERNAME = "ad"
PASSWORD = "56"

# Inbound ID for port 8853
INBOUND_ID = 4

async def add_client(uuid: str, email: str):
    url = f"https://{PANEL_IP}:{PANEL_PORT}/{PANEL_PORT}"

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    async with aiohttp.ClientSession() as session:
        # Login
        login_url = f"{url}/login"
        resp = await session.post(login_url, json={"username": USERNAME, "password": PASSWORD}, ssl=ctx)
        if "Set-Cookie" not in resp.headers:
            print(f"Login failed: {resp.status}")
            return False

        cookie = resp.headers["Set-Cookie"].split("3x-ui=")[1].split(";")[0]

        # Add client
        payload = {
            "id": INBOUND_ID,
            "settings": json.dumps({
                "clients": [
                    {
                        "id": uuid,
                        "email": email,
                        "limitIp": 0,
                        "enable": True,
                        "expiryTime": 0,
                        "totalGB": 0,
                        "tgId": "",
                        "subId": "",
                        "comment": "",
                    }
                ]
            }),
        }

        add_url = f"{url}/panel/api/inbounds/addClient"
        resp = await session.post(add_url, json=payload, headers={"Cookie": f"3x-ui={cookie}"}, ssl=ctx)
        result = await resp.json(content_type=None)

        if result.get("success"):
            print(f"✅ Client {email} added successfully")
            return True
        else:
            print(f"❌ Failed: {result}")
            return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 add_xui_client.py <uuid> <email>")
        sys.exit(1)

    uuid = sys.argv[1]
    email = sys.argv[2]
    asyncio.run(add_client(uuid, email))
