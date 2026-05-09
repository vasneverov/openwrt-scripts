#!/usr/bin/env python3
import json, urllib.request, urllib.parse, datetime, sys, socket

STATE_FILE = "/opt/subscription/bundle3_active.json"
BOT_TOKEN  = "7522740777:AAH97UDULbuevaw0vS0IDw3gb4wsuhODm5A"
ADMIN_ID   = "50949302"

PANELS = [
    {"url": "https://hostde.theredhat.su:5050/5050", "name": "DE 🇩🇪",   "host": "192.91.186.242", "port": 2084},
    {"url": "https://144.31.66.115:5050/5050",        "name": "Fin3 🇫🇮", "host": "144.31.66.115",  "port": 2083},
]

def tcp_ok(host, port, timeout=5):
    try:
        s = socket.create_connection((host, port), timeout=timeout)
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

try:
    state = json.load(open(STATE_FILE))
    current_idx = state.get("active_idx", 0)
except Exception:
    current_idx = 0

msk_time = datetime.datetime.now(
    datetime.timezone(datetime.timedelta(hours=3))).strftime("%H:%M")

dead = []
chosen = None
for i in range(1, len(PANELS) + 1):
    candidate_idx = (current_idx + i) % len(PANELS)
    candidate = PANELS[candidate_idx]
    if tcp_ok(candidate["host"], candidate["port"]):
        chosen = (candidate_idx, candidate)
        break
    else:
        dead.append(candidate["name"])

if chosen is None:
    current = PANELS[current_idx]
    msg = (f"⚠️ Пул 🇩🇪🇫🇮 · {len(PANELS)} сервера\n"
           f"❌ Все серверы недоступны — остаёмся на {current['name']}\n"
           f"⏰ {msk_time} МСК")
    send_tg(msg)
    print(f"All dead, staying on {current['name']}")
    sys.exit(0)

next_idx, next_panel = chosen
new_state = {
    "active_idx": next_idx,
    "active_panel": next_panel["url"],
    "active_name": next_panel["name"],
    "updated_at": msk_time + " MSK"
}
json.dump(new_state, open(STATE_FILE, "w"), ensure_ascii=False)

dead_str = f"\n⚠️ Пропущен: {', '.join(dead)}" if dead else ""
msg = (f"🔄 Пул 🇩🇪🇫🇮 · {len(PANELS)} сервера\n"
       f"✅ Активен: {next_panel['name']}\n"
       f"⏰ {msk_time} МСК{dead_str}")
send_tg(msg)
print(f"Bundle3 rotated → {next_panel['name']} at {msk_time} MSK")
