#!/usr/bin/env python3
import urllib.request, urllib.parse, subprocess, sys, datetime, socket, time

BOT_TOKEN = "7522740777:AAH97UDULbuevaw0vS0IDw3gb4wsuhODm5A"
ADMIN_ID  = "50949302"

SERVERS = [
    {"name": "Relay 🇷🇺", "host": "5.35.84.151",              "port": 8888, "local": True},
    {"name": "CZ3 🇨🇿",   "host": "85.137.164.179",           "port": 2082},
    {"name": "PL4 🇵🇱",   "host": "hpl4.theredhat.su",        "port": 2083},
    {"name": "NL2 🇳🇱",   "host": "panelred.xxxtream.net",    "port": 2083},
    {"name": "Fin2 🇫🇮",  "host": "89.125.196.83",            "port": 2083},
    {"name": "CZ4 🇨🇿",   "host": "193.124.56.2",             "port": 2088},
    {"name": "Italy 🇮🇹", "host": "151.243.198.86",           "port": 2083},
    {"name": "Fin3 🇫🇮",  "host": "144.31.66.115",            "port": 2083},
]

def tcp_ping(host, port, timeout=4):
    t0 = time.time()
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True, int((time.time() - t0) * 1000)
    except Exception:
        return False, None

def local_stats():
    cpu, ram, disk = "?", "?", "?"
    try:
        r = subprocess.run(["top","-bn1"], capture_output=True, text=True)
        for line in r.stdout.splitlines():
            if "Cpu" in line or "cpu" in line:
                idle = float(line.split("id,")[0].split()[-1])
                cpu = str(int(100 - idle)); break
    except: pass
    try:
        r2 = subprocess.run(["free","-m"], capture_output=True, text=True)
        for line in r2.stdout.splitlines():
            if line.startswith("Mem:"):
                parts = line.split()
                ram = str(int(int(parts[2]) / int(parts[1]) * 100)); break
    except: pass
    try:
        r3 = subprocess.run(["df","-h","/"], capture_output=True, text=True)
        parts = r3.stdout.splitlines()[1].split()
        disk = parts[4].replace("%","")
    except: pass
    return cpu, ram, disk

msk = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
cpu, ram, disk = local_stats()

ok_parts = []
fail_parts = []
relay_ms = None

for srv in SERVERS:
    ok, ms = tcp_ping(srv["host"], srv["port"])
    if srv.get("local"):
        relay_ms = ms
        if not ok:
            fail_parts.append("Relay")
    elif ok:
        ok_parts.append(f"{srv['name'].split()[0]}·{ms}")
    else:
        fail_parts.append(srv["name"])

relay_str = f" · Relay {relay_ms}мс" if relay_ms else ""
header = f"🖥 {msk.strftime('%H:%M')} МСК · CPU {cpu}% RAM {ram}% 💾{disk}%{relay_str}"

lines = [header]
if ok_parts:
    lines.append("✅ " + "  ".join(ok_parts))
if fail_parts:
    lines.append("❌ " + "  ".join(fail_parts))

msg = "\n".join(lines)
data = urllib.parse.urlencode({"chat_id": ADMIN_ID, "text": msg}).encode()
try:
    urllib.request.urlopen(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data=data, timeout=10)
    print("sent ok")
except Exception as e:
    print(f"TG error: {e}", file=sys.stderr)
