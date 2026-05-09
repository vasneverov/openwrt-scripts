#!/usr/bin/env python3
import asyncio, aiohttp, os, sys
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID  = int(os.environ.get("ADMIN_ID", "0"))

SERVERS = [
    {"name": "CZ3",   "url": "https://cz3.theredhat.su:5050/5050",     "group": "bundle"},
    {"name": "PL4",   "url": "https://hpl4.theredhat.su:5050/5050",    "group": "bundle"},
    {"name": "Fin",   "url": "https://89.125.196.83:5050/5050",        "group": "bundle"},
    {"name": "NL2",   "url": "https://panelred.xxxtream.net:5050/5050","group": "bundle"},
    {"name": "CZ4",   "url": "https://cz4.theredhat.su:5050/5050",     "group": "cz4"},
    {"name": "Italy", "url": "https://151.243.198.86:5050/5050",       "group": "cz4"},
]

SUB_URL = "https://white.theredhat.su:8888"
USER, PASS = "ad", "56"
TIMEOUT = 10


async def check_server(srv):
    r = {"name": srv["name"], "group": srv["group"],
         "ok": False, "xray": False, "cpu": None, "ram": None, "error": ""}
    connector = aiohttp.TCPConnector(ssl=False)
    jar = aiohttp.CookieJar(unsafe=True)
    timeout = aiohttp.ClientTimeout(total=TIMEOUT)
    try:
        async with aiohttp.ClientSession(connector=connector, cookie_jar=jar) as session:
            resp = await session.post(f"{srv['url']}/login",
                json={"username": USER, "password": PASS}, timeout=timeout)
            data = await resp.json(content_type=None)
            if not data.get("success"):
                r["error"] = "auth"; return r
            resp2 = await session.get(f"{srv['url']}/panel/api/server/status", timeout=timeout)
            st = await resp2.json(content_type=None)
            if st.get("success"):
                obj = st.get("obj", {})
                r["xray"] = obj.get("xray", {}).get("state", "").lower() == "running"
                r["cpu"]  = round(obj.get("cpu", 0))
                mem = obj.get("mem", {})
                used, total = mem.get("current", 0), mem.get("total", 1)
                r["ram"] = round(used / total * 100) if total else 0
                r["ok"] = True
            else:
                r["error"] = "status"
    except asyncio.TimeoutError:
        r["error"] = "t/o"
    except Exception as e:
        r["error"] = str(e)[:12]
    return r


async def check_subscription(session):
    try:
        resp = await session.get(f"{SUB_URL}/", timeout=aiohttp.ClientTimeout(total=TIMEOUT))
        return resp.status < 500
    except Exception:
        return False


async def main():
    async with aiohttp.ClientSession() as sub_session:
        results, sub_ok = await asyncio.gather(
            asyncio.gather(*[check_server(s) for s in SERVERS]),
            check_subscription(sub_session)
        )

    now = datetime.now().strftime("%H:%M")
    ok_count = sum(1 for r in results if r["ok"])
    total = len(results)
    all_ok = ok_count == total and sub_ok

    bundle  = [r for r in results if r["group"] == "bundle"]
    pool_cz = [r for r in results if r["group"] == "cz4"]

    status = "ok" if all_ok else "warn"
    lines = [f"{now}  {ok_count}/{total}  {status}", ""]

    for r in bundle:
        if r["ok"]:
            dot = "+" if r["xray"] else "!"
            lines.append(f"{r['name']:<6} {dot}  cpu {r['cpu']:>2}%  ram {r['ram']:>2}%")
        else:
            lines.append(f"{r['name']:<6} x  {r['error']}")

    lines.append("")

    for r in pool_cz:
        if r["ok"]:
            dot = "+" if r["xray"] else "!"
            lines.append(f"{r['name']:<6} {dot}  cpu {r['cpu']:>2}%  ram {r['ram']:>2}%")
        else:
            lines.append(f"{r['name']:<6} x  {r['error']}")

    lines.append("")
    lines.append(f"sub    {'ok' if sub_ok else 'fail'}")

    text = "\n".join(lines)

    tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": ADMIN_ID, "text": text, "parse_mode": "HTML",
               "disable_notification": True}
    async with aiohttp.ClientSession() as tg_session:
        resp = await tg_session.post(tg_url, json=payload, timeout=aiohttp.ClientTimeout(total=15))
        r = await resp.json()
        if not r.get("ok"):
            print("TG error:", r, file=sys.stderr); sys.exit(1)
        print(f"Sent OK: {ok_count}/{total}, sub={'OK' if sub_ok else 'FAIL'}")


if __name__ == "__main__":
    asyncio.run(main())
