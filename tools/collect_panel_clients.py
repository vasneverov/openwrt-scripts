#!/usr/bin/env python3
"""
Сбор всех клиентов с X-UI панелей для создания базы человеческих названий.
Использование:
    python3 collect_panel_clients.py
"""

import asyncio
import json
import ssl

# Список всех панелей (из памяти)
PANELS = [
    {"name": "Fin2", "ip": "89.125.196.83", "port": "5050"},   # HostFin / openred.zapto.org
    {"name": "Fin3", "ip": "144.31.66.115", "port": "5050"},
    {"name": "BegetSPB", "ip": "5.35.84.151", "port": "5050"},
    {"name": "PRG1", "ip": "64.176.35.28", "port": "5050"},
    {"name": "PRG2", "ip": "64.176.39.246", "port": "5050"},
    {"name": "CZ1", "ip": "78.24.97.181", "port": "5050"},
    {"name": "CZ2", "ip": "78.24.97.187", "port": "5050"},
    {"name": "CZ3", "ip": "78.24.99.34", "port": "5050"},
    {"name": "Z56-107", "ip": "185.26.54.34", "port": "5050"},
    {"name": "M56-01", "ip": "185.231.246.73", "port": "5050"},
    {"name": "M56-02", "ip": "185.231.246.93", "port": "5050"},
    {"name": "M56-03", "ip": "185.231.247.28", "port": "5050"},
    {"name": "M56-04", "ip": "185.231.247.30", "port": "5050"},
    {"name": "M56-05", "ip": "185.231.247.43", "port": "5050"},
    {"name": "M56-06", "ip": "185.231.247.44", "port": "5050"},
    {"name": "M56-07", "ip": "185.231.247.58", "port": "5050"},
    {"name": "M56-08", "ip": "185.231.247.73", "port": "5050"},
]

USERNAME = "ad"
PASSWORD = "56"


async def get_panel_clients(panel):
    """Get all clients from panel."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    base_url = f"https://{panel['ip']}:{panel['port']}/{panel['port']}"

    try:
        import aiohttp
    except ImportError:
        print("pip install aiohttp")
        return []

    async with aiohttp.ClientSession() as session:
        # Login
        login_url = f"{base_url}/login"
        resp = await session.post(login_url, json={"username": USERNAME, "password": PASSWORD}, ssl=ctx)

        if resp.status != 200:
            print(f"❌ {panel['name']}: Login failed HTTP {resp.status}")
            return []

        set_cookie = resp.headers.get("Set-Cookie", "")
        if "3x-ui=" not in set_cookie:
            print(f"❌ {panel['name']}: No cookie")
            return []

        cookie = set_cookie.split("3x-ui=")[1].split(";")[0]
        headers = {"Cookie": f"3x-ui={cookie}"}

        # Get inbounds list
        resp = await session.get(f"{base_url}/panel/api/inbounds/list", headers=headers, ssl=ctx)
        if resp.status != 200:
            print(f"❌ {panel['name']}: Failed to get inbounds")
            return []

        data = await resp.json(content_type=None)
        if not data.get("success"):
            print(f"❌ {panel['name']}: API error")
            return []

        clients = []
        for inbound in data.get("obj", []):
            inbound_id = inbound.get("id")
            port = inbound.get("port")
            remark = inbound.get("remark", "")

            settings = json.loads(inbound.get("settings", "{}"))
            for client in settings.get("clients", []):
                clients.append({
                    "panel": panel['name'],
                    "panel_ip": panel['ip'],
                    "inbound_id": inbound_id,
                    "port": port,
                    "remark": remark,
                    "email": client.get("email", ""),
                    "uuid": client.get("id", ""),
                })

        print(f"✅ {panel['name']}: {len(clients)} clients")
        return clients


async def main():
    print("🔍 Сбор клиентов со всех панелей...")
    print("")

    all_clients = []
    for panel in PANELS:
        clients = await get_panel_clients(panel)
        all_clients.extend(clients)
        await asyncio.sleep(0.5)  # Rate limiting

    print("")
    print(f"📊 Всего клиентов: {len(all_clients)}")

    # Save to file
    with open("/Users/vas/panel_clients.json", "w") as f:
        json.dump(all_clients, f, indent=2)

    print("💾 Сохранено в panel_clients.json")

    # Show sample
    print("")
    print("📝 Примера:")
    for c in all_clients[:10]:
        print(f"  {c['panel']:15} | {c['email']:30} | Port: {c['port']}")


if __name__ == "__main__":
    asyncio.run(main())
