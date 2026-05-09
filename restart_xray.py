#!/usr/bin/env python3
"""Restart xray via X-UI API"""
import asyncio
import aiohttp
import ssl
import json

PANEL_IP = "159.194.198.172"
PANEL_PORT = "5050"
USERNAME = "ad"
PASSWORD = "56"

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

        # Try restart via different endpoints
        endpoints = [
            f"{url}/panel/api/inbounds/restart",
            f"{url}/panel/api/server/restart",
            f"{url}/panel/api/inbounds/restartXrayService",
        ]
        
        for ep in endpoints:
            print(f"🔄 Trying {ep}...")
            async with session.post(ep, headers={"Cookie": f"3x-ui={cookie}"}, ssl=ctx) as resp:
                text = await resp.text()
                print(f"  Response: {text[:200]}")
        
        # Also try xray restart via SSH
        print("\n📋 Checking if port 587 is listening...")
        async with session.get(f"{url}/panel/api/inbounds/list", headers={"Cookie": f"3x-ui={cookie}"}, ssl=ctx) as resp:
            result = await resp.json(content_type=None)
            if result.get("success"):
                for ib in result.get("obj", []):
                    if ib.get("port") == 587:
                        print(f"  Inbound 587: enable={ib.get('enable')}")
                        if ib.get("enable"):
                            print("✅ Inbound is enabled! xray should pick it up on restart.")
                        break

if __name__ == "__main__":
    asyncio.run(main())
