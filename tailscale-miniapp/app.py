import os
import time
import httpx
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

ACCOUNTS = [
    {"num": 1, "token": os.getenv("TS1_TOKEN"), "tailnet": os.getenv("TS1_TAILNET")},
    {"num": 2, "token": os.getenv("TS2_TOKEN"), "tailnet": os.getenv("TS2_TAILNET")},
    {"num": 3, "token": os.getenv("TS3_TOKEN"), "tailnet": os.getenv("TS3_TAILNET")},
    {"num": 4, "token": os.getenv("TS4_TOKEN"), "tailnet": os.getenv("TS4_TAILNET")},
]

# Кеш — обновляется не чаще раза в 30 секунд
_cache = {"data": [], "ts": 0}
CACHE_TTL = 30


def format_last_seen(iso: str) -> str:
    """2026-04-07T08:55:10Z → '07 апр 11:55' (UTC+3, Москва)"""
    from datetime import datetime, timezone, timedelta
    MSK = timezone(timedelta(hours=3))
    months = ["янв","фев","мар","апр","май","июн","июл","авг","сен","окт","ноя","дек"]
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(MSK)
        mon = months[dt.month - 1]
        return f"{dt.day:02d} {mon} {dt.hour:02d}:{dt.minute:02d}"
    except Exception:
        return iso[:10]


async def fetch_account(acc: dict) -> list:
    url = f"https://api.tailscale.com/api/v2/tailnet/{acc['tailnet']}/devices?fields=all"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, auth=(acc["token"], ""))
        r.raise_for_status()
        devices = r.json().get("devices", [])

    result = []
    for d in devices:
        hostname = d.get("hostname", "")
        # Пропускаем не-роутеры (маки, телефоны)
        os_type = d.get("os", "")
        if os_type in ("macOS", "iOS", "windows"):
            continue

        # name из Tailscale — полное имя с суффиксом типа .tail38ae3b.ts.net
        # Обрезаем суффикс, оставляем только то что пользователь задал в панели
        full_name = d.get("name", hostname)
        display_name = full_name.split(".")[0] if full_name else hostname

        result.append({
            "name": display_name,
            "ip": d.get("addresses", ["?"])[0],
            "online": d.get("connectedToControl", False),
            "acc": acc["num"],
            "last": format_last_seen(d.get("lastSeen", "")),
            "created": d.get("created", "")[:10],
        })
    return result


async def get_all_devices(force=False) -> list:
    global _cache
    now = time.time()
    if not force and _cache["data"] and (now - _cache["ts"]) < CACHE_TTL:
        return _cache["data"]

    all_devices = []
    for acc in ACCOUNTS:
        try:
            devs = await fetch_account(acc)
            all_devices.extend(devs)
        except Exception as e:
            print(f"Ошибка учётки {acc['num']}: {e}")

    all_devices.sort(key=lambda d: (not d["online"], d["name"]))
    _cache = {"data": all_devices, "ts": now}
    return all_devices


@app.get("/api/devices")
async def api_devices():
    devices = await get_all_devices()
    online = sum(1 for d in devices if d["online"])
    return JSONResponse({
        "devices": devices,
        "total": len(devices),
        "online": online,
        "offline": len(devices) - online,
    })


@app.get("/api/refresh")
async def api_refresh():
    devices = await get_all_devices(force=True)
    online = sum(1 for d in devices if d["online"])
    return JSONResponse({
        "devices": devices,
        "total": len(devices),
        "online": online,
        "offline": len(devices) - online,
    })


# Отдаём фронтенд
app.mount("/", StaticFiles(directory="static", html=True), name="static")
