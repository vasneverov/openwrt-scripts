#!/usr/bin/env python3
"""
Проверка серверов 3x-ui: живые/мёртвые, авторизация, активные клиенты.
Запуск: python check_servers.py
"""
import asyncio
import aiohttp
import json
import ssl
import time
import re
from datetime import datetime

# Нормализация URL — убираем /panel/, /inbounds, trailing slash
def normalize_url(raw: str) -> str:
    u = raw.strip().rstrip("/")
    u = re.sub(r"/panel(/inbounds)?$", "", u)
    u = re.sub(r"/inbounds$", "", u)
    return u

SERVERS = [
    # (display_name, raw_url, username, password)
    ("AdminVPS FIN",  "https://217.11.167.181:9090/9090/panel/",                  "ad", "56"),
    ("Wiesel EST",    "https://94.156.236.241:5050/5050/",                        "ad", "56"),
    ("W_NL",          "https://45.88.67.154:5050/5050/",                          "ad", "56"),
    ("AdminDE",       "http://206.245.159.131:5050/5050/",                        "ad", "56"),
    ("HOSTKEY US",    "https://162.120.19.181:5050/5050/",                        "ad", "56"),
    ("wPL",           "https://138.124.72.238:5050/5050/panel/",                  "ad", "56"),
    ("wNL2",          "https://panelred.xxxtream.net:5050/5050/panel/",           "ad", "56"),
    ("wRU2",          "https://ru2panel.8bit.ca:5050/5050/panel/inbounds",        "ad", "56"),
    ("ApeCZ",         "https://cz.8bit.ca:5050/5050/panel/inbounds",              "ad", "56"),
    ("HipLT",         "https://92.118.170.193:5050/5050/panel/",                  "ad", "56"),
    ("Fin2",          "https://89.125.196.83:5050/5050/",                         "ad", "56"),
    ("ApeCZ2",        "https://cz2.theredhat.su:5050/5050/panel/inbounds",        "ad", "56"),
    ("HandyRU",       "https://handyru.theredhat.su:5050/5050/panel/inbounds",    "ad", "56"),
    ("IPhoster PL",   "https://plhoster.theredhat.su:5050/5050/panel/inbounds",   "ad", "56"),
    ("HostRU",        "https://hostru.theredhat.su:5050/5050/panel/inbounds",     "ad", "56"),
    ("ipHoster DE",   "https://hostde.theredhat.su:5050/5050/panel/inbounds",     "ad", "56"),
    ("ipHoster PL2",  "https://pl2iph.theredhat.su:5050/5050/panel/inbounds",     "ad", "56"),
    ("PL3host",       "https://pl3host.theredhat.su:5050/5050/panel/inbounds",    "ad", "56"),
    ("PL4host",       "https://hpl4.theredhat.su:5050/5050/panel/inbounds",       "ad", "56"),
    ("BegetSPB",      "https://5.35.84.151:5050/5050/",                           "ad", "56"),
    ("ApeCZ3",        "https://cz3.theredhat.su:5050/5050/panel/inbounds",        "ad", "56"),
]

NOW_MS = int(time.time() * 1000)

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE


def count_active_clients(inbounds: list) -> int:
    total = 0
    for inb in inbounds:
        settings = inb.get("settings", "{}")
        if isinstance(settings, str):
            try:
                settings = json.loads(settings)
            except Exception:
                continue
        clients = settings.get("clients", [])
        for c in clients:
            if not c.get("enable", True):
                continue
            expiry = c.get("expiryTime", 0)
            if expiry == 0 or expiry > NOW_MS:
                total += 1
    return total


async def check_server(session: aiohttp.ClientSession, name: str, raw_url: str, username: str, password: str) -> dict:
    url = normalize_url(raw_url)
    result = {
        "name": name,
        "url": url,
        "username": username,
        "password": password,
        "reachable": False,
        "auth_ok": False,
        "inbounds": [],
        "active_clients": 0,
        "error": None,
    }
    timeout = aiohttp.ClientTimeout(total=10)
    try:
        resp = await session.post(
            f"{url}/login",
            json={"username": username, "password": password},
            timeout=timeout,
            ssl=ssl_ctx,
        )
        result["reachable"] = True
        try:
            data = await resp.json(content_type=None)
            if data.get("success"):
                result["auth_ok"] = True
            else:
                result["error"] = f"auth fail: {data.get('msg', '?')}"
                return result
        except Exception:
            result["error"] = "bad JSON on login"
            return result

        # Получаем инбаунды
        resp2 = await session.get(f"{url}/panel/api/inbounds/list", timeout=timeout, ssl=ssl_ctx)
        data2 = await resp2.json(content_type=None)
        if data2.get("success"):
            result["inbounds"] = data2.get("obj") or []
            result["active_clients"] = count_active_clients(result["inbounds"])
        else:
            result["error"] = "inbounds list failed"

    except asyncio.TimeoutError:
        result["error"] = "timeout"
    except aiohttp.ClientConnectorError as e:
        result["error"] = f"connection refused"
    except Exception as e:
        result["error"] = str(e)[:60]

    return result


async def main():
    connector = aiohttp.TCPConnector(ssl=ssl_ctx, limit=10)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            check_server(session, name, url, user, pwd)
            for name, url, user, pwd in SERVERS
        ]
        results = await asyncio.gather(*tasks)

    print("\n" + "=" * 70)
    print(f"{'СЕРВЕР':<20} {'URL':<42} {'СТАТУС'}")
    print("=" * 70)

    alive = []
    dead = []

    for r in results:
        if r["auth_ok"]:
            clients = r["active_clients"]
            inb_count = len(r["inbounds"])
            status = f"✅ {clients} клиентов, {inb_count} инбаундов"
            alive.append(r)
        elif r["reachable"]:
            status = f"⚠️  достижим, {r['error']}"
            dead.append(r)
        else:
            status = f"❌ {r['error']}"
            dead.append(r)

        print(f"{r['name']:<20} {r['url']:<42} {status}")

    print("=" * 70)
    print(f"\n✅ Живых (авторизация OK): {len(alive)}")
    print(f"❌ Мёртвых / недоступных: {len(dead)}")

    if alive:
        print("\n── Живые серверы (инбаунды) ──────────────────────────────────────")
        for r in alive:
            print(f"\n  {r['name']} ({r['url']})")
            for inb in r["inbounds"]:
                print(f"    id={inb['id']}  protocol={inb.get('protocol','?'):<8}  remark={inb.get('remark','—')}")

    if dead:
        print("\n── Недоступные ────────────────────────────────────────────────────")
        for r in dead:
            print(f"  {r['name']:<20} {r['error']}")


if __name__ == "__main__":
    asyncio.run(main())
