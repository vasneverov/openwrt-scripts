#!/usr/bin/env python3
import json, urllib.request, urllib.parse, datetime, sys, socket, time

STATE_FILE = "/opt/subscription/bundle1_active.json"
BOT_TOKEN  = "7522740777:AAH97UDULbuevaw0vS0IDw3gb4wsuhODm5A"
ADMIN_ID   = "50949302"

PANELS = [
    {"url": "https://cz3.theredhat.su:5050/5050",        "name": "CZ3 🇨🇿", "host": "85.137.164.179",        "port": 2082},
    {"url": "https://hpl4.theredhat.su:5050/5050",        "name": "PL4 🇵🇱", "host": "hpl4.theredhat.su",     "port": 2083},
    {"url": "https://panelred.xxxtream.net:5050/5050",    "name": "NL2 🇳🇱", "host": "panelred.xxxtream.net", "port": 2083},
    {"url": "https://89.125.196.83:5050/5050",         "name": "Fin 🇫🇮", "host": "89.125.196.83",         "port": 2083},
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

# Ищем следующий живой сервер
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
    # Все серверы мертвы — остаёмся на текущем
    current = PANELS[current_idx]
    msg = (f"⚠️ Пул 🇨🇿🇵🇱🇳🇱 · {len(PANELS)} сервера\n"
           f"❌ Все серверы недоступны — остаёмся на {current['name']}\n"
           f"⏰ {msk_time} МСК")
    send_tg(msg)
    print(f"All servers dead, staying on {current['name']}")
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
msg = (f"🔄 Пул 🇨🇿🇵🇱🇳🇱 · {len(PANELS)} сервера\n"
       f"✅ Активен: {next_panel['name']}\n"
       f"⏰ {msk_time} МСК{dead_str}")
send_tg(msg)
print(f"Bundle1 rotated → {next_panel['name']} at {msk_time} MSK"
      + (f" (skipped: {', '.join(dead)})" if dead else ""))
