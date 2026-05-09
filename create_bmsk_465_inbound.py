#!/usr/bin/env python3
"""Create new inbound on bMSK port 465 (SMTP SSL) for Moscow router"""
import asyncio
import aiohttp
import ssl
import json
import uuid
import subprocess

PANEL_IP = "159.194.198.172"
PANEL_PORT = "5050"
USERNAME = "ad"
PASSWORD = "56"

# New REALITY keys for this inbound
PRIVATE_KEY = "qPBatdDltcdmZxQ6Rz5uyuUXPqte22_PdSqbwk9KTFA"
PUBLIC_KEY = "QfVJeoktRoCFJV6YdttWyGHMLnORut86toeStzTsUBk"
SHORT_ID = "a3f7b2c1"
NEW_PORT = 465
SNI = "www.apple.com"

# Router info
ROUTER_NAME = "TR30-25"  # example, change as needed
CLIENT_EMAIL = f"{ROUTER_NAME}_bMSK_465"

async def main():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    url = f"https://{PANEL_IP}:{PANEL_PORT}/{PANEL_PORT}"

    async with aiohttp.ClientSession() as session:
        # Login
        print("🔑 Logging in...")
        login_url = f"{url}/login"
        async with session.post(login_url, json={"username": USERNAME, "password": PASSWORD}, ssl=ctx) as resp:
            if "Set-Cookie" not in resp.headers:
                print(f"❌ Login failed: {resp.status}")
                return
            cookie = resp.headers["Set-Cookie"].split("3x-ui=")[1].split(";")[0]
            print(f"✅ Logged in")

        # Get list of inbounds to find next available ID
        print("📋 Getting inbound list...")
        list_url = f"{url}/panel/api/inbounds/list"
        async with session.get(list_url, headers={"Cookie": f"3x-ui={cookie}"}, ssl=ctx) as resp:
            result = await resp.json(content_type=None)
            if result.get("success"):
                inbounds = result.get("obj", [])
                existing_ids = [ib.get("id", 0) for ib in inbounds]
                next_id = max(existing_ids) + 1 if existing_ids else 1
                print(f"Existing IDs: {existing_ids}")
                print(f"Next available ID: {next_id}")
                
                # Check if port 465 already exists
                for ib in inbounds:
                    if ib.get("port") == NEW_PORT:
                        print(f"⚠️ Port {NEW_PORT} already exists! ID={ib.get('id')}")
                        return
                
                # Generate new UUID for client
                new_uuid = str(uuid.uuid4())
                print(f"🆕 Generated UUID: {new_uuid}")
                
                # Build inbound payload
                settings = {
                    "clients": [
                        {
                            "id": new_uuid,
                            "email": CLIENT_EMAIL,
                            "limitIp": 0,
                            "enable": True,
                            "expiryTime": 0,
                            "totalGB": 0,
                            "tgId": "",
                            "subId": "",
                            "comment": ""
                        }
                    ],
                    "decryption": "none",
                    "fallbacks": []
                }
                
                stream_settings = {
                    "network": "grpc",
                    "security": "reality",
                    "realitySettings": {
                        "dest": f"{SNI}:443",
                        "serverNames": [SNI],
                        "privateKey": PRIVATE_KEY,
                        "shortIds": [SHORT_ID],
                        "show": False
                    },
                    "grpcSettings": {
                        "serviceName": "",
                        "multiMode": False
                    }
                }
                
                sniffing = {
                    "enabled": True,
                    "destOverride": ["http", "tls", "quic", "fakedns"]
                }
                
                payload = {
                    "id": next_id,
                    "remark": f"bMSK_{NEW_PORT}_{ROUTER_NAME}",
                    "enable": True,
                    "port": NEW_PORT,
                    "protocol": "vless",
                    "settings": json.dumps(settings),
                    "streamSettings": json.dumps(stream_settings),
                    "sniffing": json.dumps(sniffing),
                    "listen": "0.0.0.0",
                    "tag": f"inbound-{NEW_PORT}"
                }
                
                print(f"\n📝 Creating inbound on port {NEW_PORT}...")
                add_url = f"{url}/panel/api/inbounds/add"
                async with session.post(add_url, json=payload, headers={"Cookie": f"3x-ui={cookie}"}, ssl=ctx) as resp2:
                    result2 = await resp2.json(content_type=None)
                    print(f"Create result: success={result2.get('success')}")
                    
                    if result2.get("success"):
                        print(f"✅ Inbound on port {NEW_PORT} created!")
                        
                        # Restart xray
                        print("🔄 Restarting xray...")
                        subprocess.run([
                            "sshpass", "-p", "Ujkjdf56#",
                            "ssh", "-o", "StrictHostKeyChecking=no",
                            "-o", "ConnectTimeout=10",
                            "root@159.194.198.172",
                            "/usr/local/x-ui/x-ui.sh restart"
                        ], capture_output=True, timeout=30)
                        
                        await asyncio.sleep(3)
                        
                        # Check if port is listening
                        print(f"🔍 Checking port {NEW_PORT}...")
                        check = subprocess.run([
                            "sshpass", "-p", "Ujkjdf56#",
                            "ssh", "-o", "StrictHostKeyChecking=no",
                            "-o", "ConnectTimeout=10",
                            "root@159.194.198.172",
                            f"ss -tlnp | grep {NEW_PORT} || echo 'NOT LISTENING'"
                        ], capture_output=True, text=True, timeout=15)
                        print(f"Result: {check.stdout.strip()}")
                        
                        if str(NEW_PORT) in check.stdout:
                            print(f"✅✅✅ Port {NEW_PORT} is now listening!")
                            
                            # Build VLESS key
                            vless = (
                                f"vless://{new_uuid}@{PANEL_IP}:{NEW_PORT}"
                                f"?type=grpc&security=reality&mode=gun&serviceName="
                                f"&pbk={PUBLIC_KEY}&sid={SHORT_ID}&sni={SNI}"
                                f"&fp=chrome&spx=%2F#{CLIENT_EMAIL}"
                            )
                            
                            print(f"\n{'='*70}")
                            print(f"🔑 VLESS KEY FOR {ROUTER_NAME} (bMSK port {NEW_PORT}):")
                            print(f"{'='*70}")
                            print(vless)
                            print(f"{'='*70}")
                            print(f"\n📋 Server: {PANEL_IP}")
                            print(f"📋 Port: {NEW_PORT} (SMTP SSL - low port)")
                            print(f"📋 Public Key: {PUBLIC_KEY}")
                            print(f"📋 Private Key: {PRIVATE_KEY}")
                            print(f"📋 Short ID: {SHORT_ID}")
                            print(f"📋 UUID: {new_uuid}")
                            print(f"📋 Email: {CLIENT_EMAIL}")
                            print(f"📋 Inbound ID: {next_id}")
                            
                            # Save to file
                            filename = f"/Users/vas/Desktop/vless_bMSK_{NEW_PORT}_{ROUTER_NAME}.txt"
                            with open(filename, "w") as f:
                                f.write(vless + "\n")
                            print(f"\n💾 Saved to: {filename}")
                        else:
                            print(f"⚠️ Port {NEW_PORT} is NOT listening!")
                            # Show logs
                            log_check = subprocess.run([
                                "sshpass", "-p", "Ujkjdf56#",
                                "ssh", "-o", "StrictHostKeyChecking=no",
                                "-o", "ConnectTimeout=10",
                                "root@159.194.198.172",
                                "journalctl -u x-ui --no-pager -n 10 2>/dev/null | grep -i error"
                            ], capture_output=True, text=True, timeout=15)
                            print(f"Logs: {log_check.stdout.strip()[:500]}")
                    else:
                        print(f"❌ Create failed: {result2}")
            else:
                print(f"❌ List inbounds failed: {result}")

if __name__ == "__main__":
    asyncio.run(main())
