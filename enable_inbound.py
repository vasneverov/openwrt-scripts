#!/usr/bin/env python3
"""Enable inbound and restart xray"""
import asyncio
import aiohttp
import ssl
import json

PANEL_IP = "159.194.198.172"
PANEL_PORT = "5050"
USERNAME = "ad"
PASSWORD = "56"
INBOUND_ID = 8

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
                print(f"Current state: enable={ib.get('enable')}, port={ib.get('port')}")
                
                # Update to enable
                ib["enable"] = True
                
                update_url = f"{url}/panel/api/inbounds/update/{INBOUND_ID}"
                async with session.post(update_url, json=ib, headers={"Cookie": f"3x-ui={cookie}"}, ssl=ctx) as resp2:
                    result2 = await resp2.json(content_type=None)
                    print(f"Update result: {json.dumps(result2, indent=2)}")
                    
                    if result2.get("success"):
                        print(f"✅ Inbound {INBOUND_ID} enabled!")
                        
                        # Restart xray
                        print("🔄 Restarting xray...")
                        restart_url = f"{url}/panel/api/inbounds/restart"
                        async with session.post(restart_url, headers={"Cookie": f"3x-ui={cookie}"}, ssl=ctx) as resp3:
                            result3 = await resp3.json(content_type=None)
                            print(f"Restart result: {json.dumps(result3, indent=2)}")
                            if result3.get("success"):
                                print("✅✅✅ xray restarted! Inbound is active!")
                            else:
                                print("⚠️ Restart may have failed, trying alternative...")
                    else:
                        print(f"❌ Update failed: {result2}")
            else:
                print(f"❌ Get inbound failed: {result}")

if __name__ == "__main__":
    asyncio.run(main())
