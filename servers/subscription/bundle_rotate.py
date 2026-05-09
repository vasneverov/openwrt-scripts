#!/usr/bin/env python3
import json, urllib.request, urllib.parse, datetime, sys, socket, asyncio

BOT_TOKEN = "7522740777:AAH97UDULbuevaw0vS0IDw3gb4wsuhODm5A"
ADMIN_ID  = "50949302"

BUNDLES = [
    {
        "state_file": "/opt/subscription/bundle1_active.json",
        "label": "B1",
        "panels": [
            {"url": "https://cz3.theredhat.su:5050/5050",      "name": "CZ3 🇨🇿", "host": "85.137.164.179",        "port": 2082},
            {"url": "https://hpl4.theredhat.su:5050/5050",     "name": "PL4 🇵🇱", "host": "hpl4.theredhat.su",     "port": 2083},
            {"url": "https://151.243.198.86:5050/5050",  "name": "Italy 🇮🇹", "host": "151.243.198.86", "port": 2083},
            {"url": "https://89.125.196.83:5050/5050",          "name": "Fin 🇫🇮", "host": "89.125.196.83",         "port": 2083},
        ]
    },
    {
        "state_file": "/opt/subscription/bundle2_active.json",
        "label": "B2",
        "panels": [
            {"url": "https://cz4.theredhat.su:5050/5050",  "name": "CZ4 🇨🇿",   "host": "193.124.56.2",   "port": 2088},
            {"url": "https://151.243.198.86:5050/5050",     "name": "Italy 🇮🇹", "host": "151.243.198.86", "port": 2083},
            {"url": "https://144.31.66.115:5050/5050",      "name": "Fin3 🇫🇮",  "host": "144.31.66.115",  "port": 2083},
        ]
    },
    {
        "state_file": "/opt/subscription/bundle3_active.json",
        "label": "B3",
        "panels": [
            {"url": "https://hostde.theredhat.su:5050/5050", "name": "DE 🇩🇪",   "host": "192.91.186.242", "port": 5223},
            {"url": "https://144.31.66.115:5050/5050",        "name": "Fin3 🇫🇮", "host": "144.31.66.115",  "port": 2083},
            {"url": "https://45.155.54.25:5050/5050",         "name": "FR 🇫🇷",   "host": "45.155.54.25",   "port": 2084},
        ]
    },
]

async def tcp_ok(host, port, timeout=2):
    loop = asyncio.get_event_loop()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        await loop.run_in_executor(None, sock.connect, (host, port))
        sock.close()
        return True
    except Exception:
        return False

async def check_panel(panel):
    return await tcp_ok(panel["host"], panel["port"])

def send_tg(msg):
    data = urllib.parse.urlencode({"chat_id": ADMIN_ID, "text": msg}).encode()
    try:
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data=data, timeout=10)
    except Exception as e:
        print(f"TG error: {e}", file=sys.stderr)

async def process_bundle(bundle):
    panels = bundle["panels"]
    state_file = bundle["state_file"]
    label = bundle["label"]

    try:
        state = json.load(open(state_file))
        current_idx = state.get("active_idx", 0)
    except Exception:
        current_idx = 0

    dead = []
    chosen = None

    candidates_to_check = []
    for i in range(1, len(panels) + 1):
        candidate_idx = (current_idx + i) % len(panels)
        candidate = panels[candidate_idx]
        candidates_to_check.append((candidate_idx, candidate))

    results = await asyncio.gather(*[check_panel(c) for _, c in candidates_to_check])

    for (candidate_idx, candidate), is_alive in zip(candidates_to_check, results):
        if is_alive:
            chosen = (candidate_idx, candidate)
            break
        else:
            dead.append(candidate["name"].split()[0])

    if chosen is None:
        current = panels[current_idx]
        return label, current['name'].split()[0], dead, False

    next_idx, next_panel = chosen
    json.dump({
        "active_idx": next_idx,
        "active_panel": next_panel["url"],
        "active_name": next_panel["name"],
        "updated_at": datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=3))).strftime("%H:%M") + " MSK"
    }, open(state_file, "w"), ensure_ascii=False)

    return label, next_panel['name'], dead, True

async def main():
    msk_time = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=3))).strftime("%H:%M")

    parts = []
    warnings = []

    for label, name, dead, ok in await asyncio.gather(*[process_bundle(b) for b in BUNDLES]):
        if not ok:
            parts.append(f"{label}:❌{name}")
            warnings.append(f"⚠️ {label} все недоступны")
            print(f"{label}: all dead, staying on {name}")
            continue

        parts.append(f"{label}:{name}")
        if dead:
            warnings.append(f"⚠️ {label} пропущен: {', '.join(dead)}")
        print(f"{label} → {name}" + (f" (skipped: {', '.join(dead)})" if dead else ""))

    msg = f"🔄 {msk_time} · " + " · ".join(parts)
    if warnings:
        msg += "\n" + "\n".join(warnings)

    send_tg(msg)

if __name__ == "__main__":
    asyncio.run(main())
