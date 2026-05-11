#!/usr/bin/env python3
"""
create_vless_key.py v2 — универсальный создатель VLESS-ключей
С псевдографическим интерфейсом в терминале.

Usage:
  python3 create_vless_key.py <router_name> <city> <country> [--type main|yt]
  python3 create_vless_key.py TR56-13 spb finland
  python3 create_vless_key.py Z56-94 msk poland
  python3 create_vless_key.py M56-13 spb yt --type yt

Source: ключи/RELAY_REFERENCE.json
"""

import sys, os, json, uuid, subprocess, time, datetime, threading

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_FILE     = os.path.join(BASE_DIR, 'ключи', 'RELAY_REFERENCE.json')
CHECKER      = os.path.join(BASE_DIR, 'check_vless.py')
CATALOG_FILE = os.path.join(BASE_DIR, 'ключи', 'KEY_CATALOG_ALL.md')

# ── ANSI ───────────────────────────────────────────────────────────────────────
R       = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
GREEN   = "\033[92m"
RED     = "\033[91m"
YELLOW  = "\033[93m"
CYAN    = "\033[96m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
WHITE   = "\033[97m"

def c(col, t): return f"{col}{t}{R}"

# ── Box drawing ────────────────────────────────────────────────────────────────
W = 64  # box width

def box_top(title=""):
    if title:
        inner = f"─ {c(BOLD+CYAN, title)} "
        pad   = W - ansi_len(inner) - 1
        return f"  ┌{inner}{'─'*max(0, pad)}┐"
    return f"  ┌{'─'*W}┐"

def box_bot():  return f"  └{'─'*W}┘"
def box_sep():  return f"  ├{'─'*W}┤"
def box_empty(): return f"  │ {' '*(W-2)} │"

def box_row(left="", right=""):
    if right:
        gap = W - 2 - ansi_len(left) - ansi_len(right)
        return f"  │ {left}{' '*max(1, gap)}{right} │"
    pad = W - 2 - ansi_len(left)
    return f"  │ {left}{' '*max(0, pad)} │"

def ansi_len(s): return len(re.sub(r'\033\[[^m]*m', '', s))

# ── Spinner ────────────────────────────────────────────────────────────────────
SPIN = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']
_si = 0
def spinner():
    global _si
    s = SPIN[_si % len(SPIN)]; _si += 1; return s

def spin_print(msg):
    sys.stdout.write(f"\r  {c(CYAN, spinner())} {c(DIM, msg)}{' '*30}")
    sys.stdout.flush()

def spin_clear():
    sys.stdout.write(f"\r{' '*80}\r")
    sys.stdout.flush()

# ── Progress bar ───────────────────────────────────────────────────────────────
def progress_bar(pct, width=20):
    filled = int(pct * width / 100)
    bar = c(GREEN, '█'*filled) + c(DIM, '░'*(width-filled))
    return f"{bar} {c(BOLD, f'{pct:3d}%')}"

# ── Step display ───────────────────────────────────────────────────────────────
def step_done(num, label, detail=""):
    d = f" {c(DIM, detail)}" if detail else ""
    print(f"  {c(GREEN, '●')} {c(BOLD, f'[{num}/6]')} {c(GREEN, label)}{d}")

def step_fail(num, label, detail=""):
    d = f" {c(RED, detail)}" if detail else ""
    print(f"  {c(RED, '●')} {c(BOLD, f'[{num}/6]')} {c(RED, label)}{d}")

def step_warn(num, label, detail=""):
    d = f" {c(YELLOW, detail)}" if detail else ""
    print(f"  {c(YELLOW, '●')} {c(BOLD, f'[{num}/6]')} {c(YELLOW, label)}{d}")

def step_wait(num, label):
    print(f"  {c(CYAN, '○')} {c(BOLD, f'[{num}/6]')} {c(DIM, label)}", end='')
    sys.stdout.flush()

def step_clear():
    print(f"\r{' '*80}\r", end='')
    sys.stdout.flush()

# ── Country flags ──────────────────────────────────────────────────────────────
FLAGS = {
    'finland': '🇫🇮', 'poland': '🇵🇱', 'italy': '🇮🇹', 'czech': '🇨🇿',
    'russia': '🇷🇺'
}

# ── Load reference ─────────────────────────────────────────────────────────────
def load_ref():
    if not os.path.exists(REF_FILE):
        print(f"\n  {c(RED, '✗')} {c(BOLD, 'RELAY_REFERENCE.json не найден')}")
        print(f"    {c(DIM, REF_FILE)}")
        sys.exit(1)
    with open(REF_FILE) as f:
        return json.load(f)

def find_scheme(ref, city, country, scheme_type):
    for r in ref.get('relays', []):
        if r['city'] == city and r['country'] == country:
            return ('relay', r)
    for d in ref.get('directs', []):
        if d['city'] == city and d.get('type', 'main') == scheme_type:
            return ('direct', d)
    return None, None

# ── SSH helpers ────────────────────────────────────────────────────────────────
def _has_sshpass():
    r = subprocess.run(['which', 'sshpass'], capture_output=True)
    return r.returncode == 0

def ssh_run(host, password, cmd, timeout=15):
    if _has_sshpass() and password:
        full = ['sshpass', '-p', password, 'ssh',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'ConnectTimeout=5',
                '-o', 'LogLevel=quiet',
                f'root@{host}', cmd]
    else:
        full = ['ssh',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'ConnectTimeout=5',
                '-o', 'BatchMode=yes',
                '-o', 'LogLevel=quiet',
                f'root@{host}', cmd]
    try:
        r = subprocess.run(full, capture_output=True, timeout=timeout)
        return r.stdout.decode(errors='ignore').strip(), r.returncode == 0
    except subprocess.TimeoutExpired:
        return '', False
    except Exception as e:
        return str(e), False

# ── Add client via sqlite ──────────────────────────────────────────────────────
def add_client_sqlite(host, password, inbound_id, email, new_uuid):
    sql = f"""
python3 << 'PYEOF'
import sqlite3, json, time
DB = '/etc/x-ui/x-ui.db'
INBOUND_ID = {inbound_id}
EMAIL = '{email}'
UUID = '{new_uuid}'
conn = sqlite3.connect(DB)
row = conn.execute(f'SELECT settings FROM inbounds WHERE id={{INBOUND_ID}}').fetchone()
if not row:
    print("INBOUND NOT FOUND")
    exit(1)
data = json.loads(row[0])
clients = data.get('clients', [])
for c in clients:
    if c.get('email') == EMAIL:
        print(f"EXISTS: {{EMAIL}}")
        conn.close()
        exit(0)
clients.append({{
    'id': UUID, 'email': EMAIL, 'limitIp': 0,
    'totalGB': 1099511627776,
    'expiryTime': int((time.time() + 365*24*3600) * 1000),
    'enable': True, 'tgId': '', 'subId': '', 'comment': ''
}})
data['clients'] = clients
conn.execute(f'UPDATE inbounds SET settings=? WHERE id={{INBOUND_ID}}', [json.dumps(data)])
conn.commit()
count = len(data['clients'])
conn.close()
print(f"OK: {{count}} clients")
PYEOF
"""
    out, ok = ssh_run(host, password, sql)
    if not ok: return False, f"SSH error: {out[:200]}"
    if 'INBOUND NOT FOUND' in out: return False, f"Inbound {inbound_id} not found"
    if out.startswith('EXISTS:'): return True, "already exists"
    if out.startswith('OK:'): return True, out.strip()
    return False, f"unexpected: {out[:200]}"

def restart_xray(host, password):
    out, ok = ssh_run(host, password,
        "kill -9 $(pgrep xray) 2>/dev/null; sleep 2; pgrep xray && echo 'running' || echo 'restarted'")
    return 'running' in out or 'restarted' in out

def build_vless_url(uuid_val, host, port, pbk, sid, sni, label):
    return f"vless://{uuid_val}@{host}:{port}?type=grpc&security=reality&mode=gun&serviceName=&pbk={pbk}&sid={sid}&sni={sni}&fp=chrome&spx=%2F#{label}"

def check_key(vless_url):
    r = subprocess.run([sys.executable, CHECKER, vless_url], capture_output=True, text=True, timeout=30)
    return r.stdout + r.stderr

def save_to_catalog(router_name, city, country, scheme_type, vless_url, label, scheme):
    os.makedirs(os.path.dirname(CATALOG_FILE), exist_ok=True)
    entry = f"""
## {router_name} — {city.upper()} → {country.upper()} ({scheme_type})

| Параметр | Значение |
|----------|----------|
| Дата | {datetime.date.today().isoformat()} |
| Тип | {scheme_type} |
| Город | {city} |
| Страна | {country} |
| Relay | {scheme.get('relay_ip', 'direct')}:{scheme.get('relay_port', scheme.get('port', '?'))} |
| Label | {label} |

```
{vless_url}
```
"""
    with open(CATALOG_FILE, 'a') as f:
        f.write(entry)

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 4:
        print(f"\n  {c(BOLD+CYAN, 'create_vless_key.py')} {c(DIM, '— создание VLESS-ключа')}")
        print(f"\n  {c(DIM, 'Использование:')}")
        print(f"    python3 create_vless_key.py {c(CYAN, '<роутер>')} {c(GREEN, '<город>')} {c(YELLOW, '<страна>')} {c(DIM, '[--type main|yt]')}")
        print(f"\n  {c(DIM, 'Примеры:')}")
        print(f"    python3 create_vless_key.py {c(CYAN, 'TR56-13')} {c(GREEN, 'spb')} {c(YELLOW, 'finland')}")
        print(f"    python3 create_vless_key.py {c(CYAN, 'Z56-94')}  {c(GREEN, 'msk')} {c(YELLOW, 'poland')}")
        print(f"    python3 create_vless_key.py {c(CYAN, 'M56-13')}  {c(GREEN, 'spb')} {c(YELLOW, 'yt')} {c(DIM, '--type yt')}")
        print(f"\n  {c(DIM, 'Города:')} spb, msk")
        print(f"  {c(DIM, 'Страны:')} finland, poland, italy, czech")
        sys.exit(1)

    router_name = sys.argv[1]
    city        = sys.argv[2].lower()
    country     = sys.argv[3].lower()
    scheme_type = 'main'
    if '--type' in sys.argv:
        idx = sys.argv.index('--type')
        if idx + 1 < len(sys.argv):
            scheme_type = sys.argv[idx + 1].lower()

    flag = FLAGS.get(country, '🌍')

    # ── HEADER ──────────────────────────────────────────────────────────────
    print()
    print(box_top(f"▶  VLESS KEY CREATOR  v2"))
    print(box_empty())
    print(box_row(f"  {c(DIM, 'Роутер:')}  {c(BOLD+WHITE, router_name)}"))
    print(box_row(f"  {c(DIM, 'Схема:')}   {c(CYAN, city.upper())} → {flag} {c(YELLOW, country.upper())}  {c(DIM, f'({scheme_type})')}"))
    print(box_empty())
    print(box_bot())
    print()

    # ── STEP 1: Load reference ──────────────────────────────────────────────
    step_wait(1, "Загрузка справочника...")
    ref = load_ref()
    step_clear()
    step_done(1, "Справочник загружен", f"({len(ref.get('relays',[]))} relay, {len(ref.get('directs',[]))} direct схем)")

    # ── STEP 2: Find scheme ─────────────────────────────────────────────────
    step_wait(2, "Поиск схемы...")
    mode, scheme = find_scheme(ref, city, country, scheme_type)
    step_clear()
    if not scheme:
        step_fail(2, "Схема не найдена")
        print(f"\n  {c(RED, 'Доступные relay-схемы:')}")
        for r in ref.get('relays', []):
            f = FLAGS.get(r['country'], '')
            print(f"    {c(CYAN, r['city']+'/'+r['country']):25s} → {c(DIM, r['relay_ip']+':'+str(r['relay_port']))} → {c(GREEN, r['target_server'])}  {f}")
        print(f"\n  {c(RED, 'Доступные direct-схемы:')}")
        for d in ref.get('directs', []):
            print(f"    {c(CYAN, d['city']+'/'+d.get('type','main')):25s} → {c(DIM, d['server_ip']+':'+str(d['port']))}  {c(GREEN, d['label_suffix'])}")
        sys.exit(1)

    if mode == 'relay':
        relay_ip   = scheme['relay_ip']
        relay_port = scheme['relay_port']
        target_server = scheme['target_server']
        target_inbound = scheme['target_inbound']
        pbk  = scheme['pbk']
        sid  = scheme['sid']
        sni  = scheme['sni']
        label_suffix = scheme['label_suffix']
        route_str = f"{c(CYAN, relay_ip+':'+str(relay_port))} {c(DIM, '→')} {c(GREEN, target_server+':'+str(scheme['target_port']))}"
    else:
        relay_ip   = scheme['server_ip']
        relay_port = scheme['port']
        target_server = scheme['panel_server']
        target_inbound = scheme['inbound']
        pbk  = scheme['pbk']
        sid  = scheme['sid']
        sni  = scheme['sni']
        label_suffix = scheme['label_suffix']
        route_str = f"{c(CYAN, relay_ip+':'+str(relay_port))} {c(DIM, '(direct)')}"

    step_done(2, "Схема найдена", f"{route_str}")

    # ── STEP 3: Generate UUID ───────────────────────────────────────────────
    step_wait(3, "Генерация UUID...")
    new_uuid = str(uuid.uuid4())
    email = f"{router_name}_{label_suffix}"
    step_clear()
    step_done(3, "UUID сгенерирован", f"{c(YELLOW, new_uuid)}")

    # ── STEP 4: Add client via sqlite ───────────────────────────────────────
    panel = ref.get('panels', {}).get(target_server)
    if not panel:
        step_fail(4, "Панель не найдена")
        sys.exit(1)

    ssh_pass = panel.get('ssh')
    host = panel.get('url', '').replace('https://', '').split(':')[0]

    if ssh_pass:
        step_wait(4, "Добавление клиента на сервер...")
        success, msg = add_client_sqlite(host, ssh_pass, target_inbound, email, new_uuid)
        step_clear()
        if success:
            step_done(4, "Клиент добавлен", f"{c(DIM, email)} → {c(GREEN, target_server)} (inbound {target_inbound})")
        else:
            step_warn(4, "Клиент: " + msg, "проверь вручную")

        # Restart xray
        step_wait(4, "Перезапуск xray...")
        time.sleep(1)
        xray_ok = restart_xray(host, ssh_pass)
        step_clear()
        if xray_ok:
            step_done(4, "xray перезапущен", c(GREEN, "✓"))
        else:
            step_warn(4, "xray: не удалось перезапустить", "kill -9 вручную?")
        time.sleep(2)
    else:
        step_warn(4, "SSH пароль неизвестен", "добавь клиента вручную через панель")
        print(f"    {c(DIM, 'Панель:')}  {c(CYAN, panel['url'])}")
        print(f"    {c(DIM, 'Inbound:')} {c(YELLOW, target_inbound)}")
        print(f"    {c(DIM, 'Email:')}   {c(YELLOW, email)}")
        print(f"    {c(DIM, 'UUID:')}    {c(YELLOW, new_uuid)}")

    # ── STEP 5: Build and check ─────────────────────────────────────────────
    label = f"{router_name}_{label_suffix}"
    vless_url = build_vless_url(new_uuid, relay_ip, relay_port, pbk, sid, sni, label)

    step_done(5, "VLESS URL собран", c(DIM, "готов к проверке"))

    step_wait(5, "Проверка ключа...")
    check_out = check_key(vless_url)
    step_clear()

    # Parse check result
    if '● READY' in check_out:
        step_done(5, "Проверка пройдена", c(GREEN, "● READY ✓✓✓"))
    elif '✗ BROKEN' in check_out:
        step_fail(5, "Проверка не пройдена", c(RED, "✗ BROKEN"))
    else:
        step_warn(5, "Проверка: не удалось определить статус", "смотри вывод ниже")

    # ── STEP 6: Save ────────────────────────────────────────────────────────
    save_to_catalog(router_name, city, country, scheme_type, vless_url, label, scheme)
    step_done(6, "Сохранено в каталог", c(DIM, CATALOG_FILE))

    # ── RESULT CARD ─────────────────────────────────────────────────────────
    print()
    print(box_top("РЕЗУЛЬТАТ"))
    print(box_empty())

    # Progress bar
    if '● READY' in check_out:
        print(box_row(f"  {progress_bar(100)}  {c(GREEN, '● READY')}"))
    elif '✗ BROKEN' in check_out:
        print(box_row(f"  {progress_bar(50)}  {c(RED, '✗ BROKEN')}"))
    else:
        print(box_row(f"  {progress_bar(75)}  {c(YELLOW, '⚠ CHECK')}"))

    print(box_empty())
    print(box_sep())
    print(box_empty())

    # Key info
    print(box_row(f"  {c(DIM, 'Роутер:')}  {c(BOLD+WHITE, router_name)}"))
    print(box_row(f"  {c(DIM, 'Схема:')}   {c(CYAN, city.upper())} → {flag} {c(YELLOW, country.upper())}"))
    print(box_row(f"  {c(DIM, 'Relay:')}   {c(CYAN, f'{relay_ip}:{relay_port}')}"))
    print(box_row(f"  {c(DIM, 'Email:')}   {c(YELLOW, email)}"))
    print(box_row(f"  {c(DIM, 'UUID:')}    {c(DIM, new_uuid)}"))
    print(box_empty())
    print(box_sep())
    print(box_empty())

    # VLESS URL
    print(box_row(f"  {c(BOLD, 'VLESS URL:')}"))
    print(box_empty())
    # Split long URL
    if len(vless_url) > W - 6:
        print(box_row(f"  {c(DIM, vless_url[:W-8])}"))
        print(box_row(f"  {c(DIM, vless_url[W-8:])}"))
    else:
        print(box_row(f"  {c(GREEN, vless_url)}"))
    print(box_empty())
    print(box_bot())
    print()

    # ── FINAL VERDICT ───────────────────────────────────────────────────────
    if '● READY' in check_out:
        print(f"  {c(BOLD+GREEN, '┌──────────────────────────────────────────────┐')}")
        print(f"  {c(BOLD+GREEN, '│')}  {c(BOLD+WHITE, '✅  КЛЮЧ РАБОЧИЙ — можно ставить на роутер')}  {c(BOLD+GREEN, '│')}")
        print(f"  {c(BOLD+GREEN, '└──────────────────────────────────────────────┘')}")
        print()
        print(f"  {c(DIM, 'Скопируй строку ниже в uci set podkop.main.proxy_string:')}")
        print(f"  {c(BOLD, '────────────────────────────────────────────────────')}")
        print(f"  {c(GREEN, vless_url)}")
        print(f"  {c(BOLD, '────────────────────────────────────────────────────')}")
    else:
        print(f"  {c(BOLD+YELLOW, '┌──────────────────────────────────────────────┐')}")
        print(f"  {c(BOLD+YELLOW, '│')}  {c(YELLOW, '⚠️  КЛЮЧ НЕ ПРОШЁЛ ПРОВЕРКУ')}              {c(BOLD+YELLOW, '│')}")
        print(f"  {c(BOLD+YELLOW, '│')}  {c(DIM, 'Проверь вручную через check_vless.py')}     {c(BOLD+YELLOW, '│')}")
        print(f"  {c(BOLD+YELLOW, '└──────────────────────────────────────────────┘')}")
        print()
        print(f"  {c(DIM, vless_url)}")

    # Show check_vless output if not READY
    if '● READY' not in check_out:
        print()
        print(f"  {c(DIM, 'Вывод check_vless:')}")
        for line in check_out.split('\n'):
            print(f"  {c(DIM, line)}")

if __name__ == '__main__':
    main()
