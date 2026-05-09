#!/usr/bin/env python3
"""Add all M56-14..22 clients to X-UI panels"""
import asyncio
import aiohttp
import ssl
import json
import uuid as uuid_lib

# Panel credentials
FIN3_IP = "144.31.66.115"
BSPB_IP = "5.35.84.151"
PANEL_PORT = "5050"
USERNAME = "ad"
PASSWORD = "56"

# Inbound IDs
FIN3_INBOUND_ID = 2  # port 4191
BSPB_INBOUND_ID = 4  # port 8853

# UUIDs from M56-15_22_ГОТОВО.txt + generate M56-14
CLIENTS = [
    # M56-14 - generate new
    {"router": "M56-14", "main_uuid": str(uuid_lib.uuid4()), "yt_uuid": str(uuid_lib.uuid4())},
    # M56-15..22 from file
    {"router": "M56-15", "main_uuid": "c80acb93-1c61-4df5-964a-ca0d23a5d018", "yt_uuid": "afed0637-bb53-48a1-980c-5f2ce77ea54d"},
    {"router": "M56-16", "main_uuid": "0309b41c-a817-4c7b-ab92-2f3f93c5824b", "yt_uuid": "6d10f242-5421-46c1-9ea8-62debc7efdb4"},
    {"router": "M56-17", "main_uuid": "c2879279-eec8-45d5-98b0-52cce0249d4a", "yt_uuid": "76b47766-3dfb-4930-99fe-498ac6a99305"},
    {"router": "M56-18", "main_uuid": "e510ad99-aa8b-4e21-b94f-d1ce3ef88831", "yt_uuid": "9358dd7e-d754-439b-8694-20571311159c"},
    {"router": "M56-19", "main_uuid": "8b47ab84-c6f3-46c1-90ac-1d5a51bbd62a", "yt_uuid": "99da7b58-52e7-4ae0-a5fa-38303b9bd20c"},
    {"router": "M56-20", "main_uuid": "8d77d5cf-312e-40f7-979a-7942aff87537", "yt_uuid": "32035f0a-726d-4e47-9abc-a7d1f0906286"},
    {"router": "M56-21", "main_uuid": "41f01d9d-f85a-4ed1-acc9-5b528e31aca1", "yt_uuid": "86b3534f-d78d-423e-8949-558778775e67"},
    {"router": "M56-22", "main_uuid": "0bd5ca6d-ea93-4ab5-8533-b4475069cf60", "yt_uuid": "22d1c261-5b35-4d5a-a40d-003a5e4ddc62"},
]

async def add_client(session, ssl_ctx, panel_ip, inbound_id, client_uuid, email):
    url = f"https://{panel_ip}:{PANEL_PORT}/{PANEL_PORT}"

    # Login
    login_url = f"{url}/login"
    resp = await session.post(login_url, json={"username": USERNAME, "password": PASSWORD}, ssl=ssl_ctx)
    if "Set-Cookie" not in resp.headers:
        print(f"  ❌ Login failed: {resp.status}")
        return False

    cookie = resp.headers["Set-Cookie"].split("3x-ui=")[1].split(";")[0]

    # Add client
    payload = {
        "id": inbound_id,
        "settings": json.dumps({
            "clients": [
                {
                    "id": client_uuid,
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
    resp = await session.post(add_url, json=payload, headers={"Cookie": f"3x-ui={cookie}"}, ssl=ssl_ctx)
    result = await resp.json(content_type=None)

    if result.get("success"):
        print(f"  ✅ {email} added")
        return True
    else:
        print(f"  ❌ {email} failed: {result}")
        return False

async def main():
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    async with aiohttp.ClientSession() as session:
        print("=== Adding clients to Fin3 panel (144.31.66.115) ===")
        for client in CLIENTS:
            print(f"{client['router']} Main: {client['main_uuid']}")
            await add_client(session, ssl_ctx, FIN3_IP, FIN3_INBOUND_ID, client['main_uuid'], f"{client['router']}_Fin3")

        print("\n=== Adding clients to bSPB panel (5.35.84.151) ===")
        for client in CLIENTS:
            print(f"{client['router']} YT: {client['yt_uuid']}")
            await add_client(session, ssl_ctx, BSPB_IP, BSPB_INBOUND_ID, client['yt_uuid'], f"{client['router']}_bSPB")

        print("\n=== Generated UUIDs for M56-14 ===")
        print(f"Main: {CLIENTS[0]['main_uuid']}")
        print(f"YT:   {CLIENTS[0]['yt_uuid']}")

if __name__ == "__main__":
    asyncio.run(main())
