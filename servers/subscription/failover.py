#!/usr/bin/env python3
"""
failover.py — экстренное переключение если активный сервер упал.
Запускается каждые 2 минуты. НЕ ротирует если сервер жив.
"""
import json, socket, datetime, urllib.request, urllib.parse, sys

BOT_TOKEN = "7522740777:AAH97UDULbuevaw0vS0IDw3gb4wsuhODm5A"
ADMIN_ID  = "50949302"

BUNDLES = [
    {
        "state_file": "/opt/subscription/bundle1_active.json",
        "label": "B1",
        "panels": [
            {"url": "https://cz3.theredhat.su:5050/5050",  "name": "CZ3 🇨🇿",   "host": "85.137.164.179",    "port": 2082},
            {"url": "https://hpl4.theredhat.su:5050/5050", "name": "PL4 🇵🇱",   "host": "hpl4.theredhat.su", "port": 2083},
            {"url": "https://151.243.198.86:5050/5050",    "name": "Italy 🇮🇹", "host": "151.243.198.86",    "port": 2083},
            {"url": "https://89.125.196.83:5050/5050",     "name": "Fin 🇫🇮",   "host": "89.125.196.83",     "port": 2083},
        ]
    },
    {
        "state_file": "/opt/subscription/bundle2_active.json",
        "label": "B2",
        "panels": [
            {"url": "https://cz4.theredhat.su:5050/5050",  "name": "CZ4 🇨🇿",   "host": "193.124.56.2",   "port": 2088},
            {"url": "https://151.243.198.86:5050/5050",    "name": "Italy 🇮🇹", "host": "151.243.198.86", "port": 2083},
            {"url": "https://144.31.66.115:5050/5050",     "name": "Fin3 🇫🇮",  "host": "144.31.66.115",  "port": 2083},
        ]
    },
    {
        "state_file": "/opt/subscription/bundle3_active.json",
        "label": "B3",
        "panels": [
            {"url": "https://hostde.theredhat.su:5050/5050", "name": "DE 🇩🇪",   "host": "192.91.186.242", "port": 5223},
            {"url": "https://144.31.66.115:5050/5050",       "name": "Fin3 🇫🇮", "host": "144.31.66.115",  "port": 2083},
            {"url": "https://45.155.54.25:5050/5050",        "name": "FR 🇫🇷",   "host": "45.155.54.25",   "port": 2084},
        ]
    },
]

def tcp_ok(host, port, timeout=3):
    try:
        s = socket.socket()
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

def send_tg(msg):
    data = urllib.parse.urlencode({"chat_id": ADMIN_ID, "text": msg}).encode()
    try:
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data=data, timeout=10)
    except Exception as e:
        print(f"TG error: {e}", file=sys.stderr)

def msk_now():
    return datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=3))).strftime("%H:%M")

def process_bundle(bundle):
    panels     = bundle["panels"]
    state_file = bundle["state_file"]
    label      = bundle["label"]

    try:
        state      = json.load(open(state_file))
        active_url = state.get("active_panel", panels[0]["url"])
    except Exception:
        active_url = panels[0]["url"]

    active_panel = next((p for p in panels if p["url"] == active_url), panels[0])

    if tcp_ok(active_panel["host"], active_panel["port"]):
        return  # живой — ничего не делаем

    # мёртвый — ищем первый живой
    for p in panels:
        if p["url"] == active_url:
            continue
        if tcp_ok(p["host"], p["port"]):
            json.dump({
                "active_idx":   panels.index(p),
                "active_panel": p["url"],
                "active_name":  p["name"],
                "updated_at":   msk_now() + " MSK",
                "failover":     True,
            }, open(state_file, "w"), ensure_ascii=False)
            send_tg(
                f"🚨 {label} FAILOVER {msk_now()} МСК\n"
                f"❌ {active_panel['name']} — недоступен\n"
                f"✅ Переключён на {p['name']}"
            )
            print(f"{label}: {active_panel['name']} → {p['name']}")
            return

    send_tg(f"💀 {label} {msk_now()} МСК — ВСЕ серверы недоступны!")
    print(f"{label}: все мертвы", file=sys.stderr)

for bundle in BUNDLES:
    process_bundle(bundle)
