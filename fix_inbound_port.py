#!/usr/bin/env python3
"""Change inbound port from 587 to 993 and restart xray"""
import asyncio
import aiohttp
import ssl
import json

PANEL_IP = "159.194.198.172"
PANEL_PORT = "5050"
USERNAME = "ad"
PASSWORD = "56"
INBOUND_ID = 8
NEW_PORT = 993

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
                
                # Change port
                ib["port"] = NEW_PORT
                ib["enable"] = True
                
                update_url = f"{url}/panel/api/inbounds/update/{INBOUND_ID}"
                async with session.post(update_url, json=ib, headers={"Cookie": f"3x-ui={cookie}"}, ssl=ctx) as resp2:
                    result2 = await resp2.json(content_type=None)
                    print(f"Update result: {json.dumps(result2, indent=2)}")
                    
                    if result2.get("success"):
                        print(f"✅ Port changed to {NEW_PORT}!")
                        
                        # Restart xray via SSH
                        print("🔄 Restarting xray via SSH...")
                        import subprocess
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
                        result = subprocess.run([
                            "sshpass", "-p", "Ujkjdf56#",
                            "ssh", "-o", "StrictHostKeyChecking=no",
                            "-o", "ConnectTimeout=10",
                            "root@159.194.198.172",
                            f"ss -tlnp | grep {NEW_PORT} || echo 'NOT LISTENING'"
                        ], capture_output=True, text=True, timeout=15)
                        print(f"Result: {result.stdout.strip()}")
                        
                        if str(NEW_PORT) in result.stdout:
                            print(f"✅✅✅ Port {NEW_PORT} is now listening!")
                        else:
                            print(f"⚠️ Port {NEW_PORT} is NOT listening. Check xray logs.")
            else:
                print(f"❌ Get inbound failed: {result}")

if __name__ == "__main__":
    asyncio.run(main())
