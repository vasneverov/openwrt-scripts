#!/usr/bin/env python3
"""Fix REALITY keys for inbound-993 and restart xray"""
import asyncio
import aiohttp
import ssl
import json
import subprocess

PANEL_IP = "159.194.198.172"
PANEL_PORT = "5050"
USERNAME = "ad"
PASSWORD = "56"
INBOUND_ID = 8

# Correct keys from xray x25519
PRIVATE_KEY = "KIaF-HcHQ05ayjOFUzHPv8w8EN6PWwH5WOMUGde-0Gk"
PUBLIC_KEY = "yxRiFPlbjjcodOzcbVuntFdpnzFnXLF1Nj9bma3H-lQ"
SHORT_ID = "1d0385b7"

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

        # Get current inbound config
        print(f"📋 Getting inbound {INBOUND_ID}...")
        get_url = f"{url}/panel/api/inbounds/get/{INBOUND_ID}"
        async with session.get(get_url, headers={"Cookie": f"3x-ui={cookie}"}, ssl=ctx) as resp:
            result = await resp.json(content_type=None)
            if result.get("success"):
                ib = result.get("obj", {})
                print(f"Current: port={ib.get('port')}, enable={ib.get('enable')}")
                
                # Fix streamSettings with correct keys
                stream_settings = {
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
                }
                ib["streamSettings"] = json.dumps(stream_settings)
                ib["enable"] = True
                
                update_url = f"{url}/panel/api/inbounds/update/{INBOUND_ID}"
                async with session.post(update_url, json=ib, headers={"Cookie": f"3x-ui={cookie}"}, ssl=ctx) as resp2:
                    result2 = await resp2.json(content_type=None)
                    print(f"Update result: success={result2.get('success')}")
                    
                    if result2.get("success"):
                        print(f"✅ Keys fixed!")
                        
                        # Restart xray via SSH
                        print("🔄 Restarting xray via SSH...")
                        subprocess.run([
                            "sshpass", "-p", "Ujkjdf56#",
                            "ssh", "-o", "StrictHostKeyChecking=no",
                            "-o", "ConnectTimeout=10",
                            "root@159.194.198.172",
                            "/usr/local/x-ui/x-ui.sh restart"
                        ], capture_output=True, timeout=30)
                        
                        await asyncio.sleep(3)
                        
                        # Check if port is listening
                        print(f"🔍 Checking port 993...")
                        result = subprocess.run([
                            "sshpass", "-p", "Ujkjdf56#",
                            "ssh", "-o", "StrictHostKeyChecking=no",
                            "-o", "ConnectTimeout=10",
                            "root@159.194.198.172",
                            "ss -tlnp | grep 993 || echo 'NOT LISTENING'"
                        ], capture_output=True, text=True, timeout=15)
                        print(f"Result: {result.stdout.strip()}")
                        
                        if "993" in result.stdout:
                            print(f"✅✅✅ Port 993 is now listening!")
                            print(f"\n🔑 YOUR VLESS KEY FOR YOUTUBE (DIRECT):")
                            print(f"=" * 70)
                            # Get client UUID
                            settings = json.loads(ib.get("settings", "{}"))
                            if settings.get("clients"):
                                client_uuid = settings["clients"][0].get("id", "?")
                                email = settings["clients"][0].get("email", "?")
                                vless = f"vless://{client_uuid}@{PANEL_IP}:993?type=grpc&security=reality&mode=gun&serviceName=&pbk={PUBLIC_KEY}&sid={SHORT_ID}&sni=www.apple.com&fp=chrome&spx=%2F#{email}"
                                print(vless)
                                print(f"=" * 70)
                                print(f"\n📋 Server: {PANEL_IP}")
                                print(f"📋 Port: 993 (IMAPS - low port, bypasses DPI)")
                                print(f"📋 Public Key: {PUBLIC_KEY}")
                                print(f"📋 Short ID: {SHORT_ID}")
                        else:
                            print(f"⚠️ Port 993 is NOT listening. Check xray logs.")
                            # Show logs
                            log_result = subprocess.run([
                                "sshpass", "-p", "Ujkjdf56#",
                                "ssh", "-o", "StrictHostKeyChecking=no",
                                "-o", "ConnectTimeout=10",
                                "root@159.194.198.172",
                                "journalctl -u x-ui --no-pager -n 10 2>/dev/null | grep -i error"
                            ], capture_output=True, text=True, timeout=15)
                            print(f"Logs: {log_result.stdout.strip()[:500]}")
            else:
                print(f"❌ Get inbound failed: {result}")

if __name__ == "__main__":
    asyncio.run(main())
