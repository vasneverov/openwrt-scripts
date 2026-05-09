#!/usr/bin/env python3
"""Create new YT direct inbound on bMSK with low port and add client"""
import asyncio
import aiohttp
import ssl
import json
import sys
import uuid as uuid_mod

# bMSK panel
PANEL_IP = "159.194.198.172"
PANEL_PORT = "5050"
USERNAME = "ad"
PASSWORD = "56"

# New inbound params
NEW_PORT = 587  # SMTP Submission - low port, looks legit
NEW_TAG = "inbound-587"

# New REALITY keys
PRIVATE_KEY = "ENDDMqGTA/ttLHd1FtFs7k9jL2uR40910SP0lj/2kGQ="
PUBLIC_KEY = "n2Ha1A1TGluAGjWSS7TvKk2RyMKhzDUU+w0rrkrbCic="
SHORT_ID = "1d0385b7"

async def create_inbound(session, cookie, url):
    """Create new inbound on bMSK"""
    inbound_config = {
        "port": NEW_PORT,
        "listen": "0.0.0.0",
        "protocol": "vless",
        "settings": json.dumps({
            "clients": [],
            "decryption": "none",
            "fallbacks": []
        }),
        "streamSettings": json.dumps({
            "network": "grpc",
            "security": "reality",
            "realitySettings": {
                "dest": "www.apple.com:443",
                "serverNames": ["www.apple.com"],
                "privateKey": PRIVATE_KEY,
                "shortIds": [SHORT_ID],
                "show": False
            },
            "grpcSettings": {
                "serviceName": "",
                "multiMode": False
            }
        }),
        "sniffing": json.dumps({
            "enabled": True,
            "destOverride": ["http", "tls", "quic", "fakedns"]
        }),
        "tag": NEW_TAG
    }

    add_url = f"{url}/panel/api/inbounds/add"
    async with session.post(add_url, json=inbound_config, headers={"Cookie": f"3x-ui={cookie}"}, ssl=ctx) as resp:
        result = await resp.json(content_type=None)
        return result

async def add_client_to_inbound(session, cookie, url, inbound_id, client_uuid, email):
    """Add client to inbound"""
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
    async with session.post(add_url, json=payload, headers={"Cookie": f"3x-ui={cookie}"}, ssl=ctx) as resp:
        result = await resp.json(content_type=None)
        return result

async def get_inbounds(session, cookie, url):
    """Get list of inbounds to find the new one's ID"""
    list_url = f"{url}/panel/api/inbounds/list"
    async with session.get(list_url, headers={"Cookie": f"3x-ui={cookie}"}, ssl=ctx) as resp:
        result = await resp.json(content_type=None)
        return result

async def main():
    global ctx
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    url = f"https://{PANEL_IP}:{PANEL_PORT}/{PANEL_PORT}"

    async with aiohttp.ClientSession() as session:
        # 1. Login
        print("🔑 Logging in to bMSK panel...")
        login_url = f"{url}/login"
        async with session.post(login_url, json={"username": USERNAME, "password": PASSWORD}, ssl=ctx) as resp:
            if "Set-Cookie" not in resp.headers:
                print(f"❌ Login failed: {resp.status}")
                return False
            cookie = resp.headers["Set-Cookie"].split("3x-ui=")[1].split(";")[0]
            print(f"✅ Logged in, cookie obtained")

        # 2. Check if inbound already exists
        print(f"🔍 Checking if inbound on port {NEW_PORT} already exists...")
        inbounds = await get_inbounds(session, cookie, url)
        if inbounds.get("success"):
            for ib in inbounds.get("obj", []):
                if ib.get("port") == NEW_PORT:
                    print(f"⚠️  Inbound on port {NEW_PORT} already exists with ID={ib.get('id')}")
                    inbound_id = ib.get("id")
                    break
            else:
                inbound_id = None
        else:
            print(f"⚠️  Could not list inbounds, will try to create anyway")
            inbound_id = None

        # 3. Create inbound if not exists
        if inbound_id is None:
            print(f"📦 Creating new inbound on port {NEW_PORT}...")
            result = await create_inbound(session, cookie, url)
            print(f"Create result: {json.dumps(result, indent=2)}")
            
            if result.get("success"):
                inbound_id = result.get("obj", {}).get("id")
                print(f"✅ Inbound created with ID={inbound_id}")
            else:
                print(f"❌ Failed to create inbound: {result}")
                # Maybe it already exists - try to find it
                inbounds2 = await get_inbounds(session, cookie, url)
                if inbounds2.get("success"):
                    for ib in inbounds2.get("obj", []):
                        if ib.get("port") == NEW_PORT:
                            inbound_id = ib.get("id")
                            print(f"📌 Found existing inbound with ID={inbound_id}")
                            break
                
                if inbound_id is None:
                    return False
        else:
            print(f"✅ Using existing inbound ID={inbound_id}")

        # 4. Generate UUID and add client
        client_uuid = str(uuid_mod.uuid4())
        email = "VasyaOnline_YT_587"
        
        print(f"👤 Adding client {email} with UUID {client_uuid}...")
        result = await add_client_to_inbound(session, cookie, url, inbound_id, client_uuid, email)
        
        if result.get("success"):
            print(f"\n✅✅✅ SUCCESS! Client added!")
            print(f"\n🔑 YOUR VLESS KEY FOR YOUTUBE (DIRECT):")
            print(f"=" * 70)
            vless = f"vless://{client_uuid}@{PANEL_IP}:{NEW_PORT}?type=grpc&security=reality&mode=gun&serviceName=&pbk={PUBLIC_KEY}&sid={SHORT_ID}&sni=www.apple.com&fp=chrome&spx=%2F#{email}"
            print(vless)
            print(f"=" * 70)
            print(f"\n📋 Server: {PANEL_IP}")
            print(f"📋 Port: {NEW_PORT} (SMTP Submission - low port, bypasses DPI)")
            print(f"📋 Type: gRPC+Reality direct (no relay)")
            print(f"📋 SNI: www.apple.com")
            print(f"📋 Public Key: {PUBLIC_KEY}")
            print(f"📋 Short ID: {SHORT_ID}")
            print(f"📋 Email: {email}")
            
            # Save to file
            filename = f"/Users/vas/CLAUDECODE/ключи/vless_bMSK_direct_{NEW_PORT}_{email}.md"
            with open(filename, "w") as f:
                f.write(f"# bMSK YT direct — bMSK_direct_{NEW_PORT} 🇷🇺\n")
                f.write(f"IP: {PANEL_IP} | Порт: {NEW_PORT} | SNI: www.apple.com | Transport: gRPC+Reality\n")
                f.write("---\n")
                f.write(f"## {email}\n")
                f.write("```\n")
                f.write(vless)
                f.write("\n```\n")
            print(f"\n💾 Saved to: {filename}")
            
            return True
        else:
            print(f"❌ Failed to add client: {result}")
            return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
