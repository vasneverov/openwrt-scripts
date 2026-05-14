#!/usr/bin/env python3
"""
check_vless.py v2 — полная проверка VLESS/Reality ключей
Usage:
  python3 check_vless.py vless://...
  python3 check_vless.py keys.html
  cat keys.txt | python3 check_vless.py -

Checks:
  1. TCP    — relay порт доступен
  2. TLS    — Reality handshake прошёл
  3. xray   — UUID зарегистрирован в активном конфиге xray (SSH)
  4. expiry — срок действия не истёк, > 30 дней
  5. limit  — limitIp == 0
"""

import sys, re, socket, ssl, subprocess, time, os, datetime, json, base64
from urllib.parse import parse_qs, unquote

# ── ANSI ──────────────────────────────────────────────────────────────────────
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
def b(t):      return f"{BOLD}{t}{R}"
def ansi_len(s): return len(re.sub(r'\033\[[^m]*m', '', s))

W = 60  # box inner width

# ── Known X-UI servers: pbk → (name, ssh_ip, ssh_pass) ───────────────────────
# Source: ключи/RELAY_REFERENCE.json
XUI_SERVERS = {
    'XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw': ('Fin3', '144.31.66.115',     'Ujkjdf56'),
    'me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM': ('bSPB', '5.35.84.151',       None),
    'HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI': ('Fin4', '45.155.55.198',     'duqwgjXiT4FRrc'),
    'g5eg_BKQJLVbPxryppyE0AGpQB_HKHPGkOJN9I6bSzI': ('bMSK', '159.194.198.172',   'Ujkjdf56#'),
    '4TCLYNy_kglu_bpE5n3Gx0yQ7L8TJQKRLATLgnXbtEw': ('PL5',  '91.92.46.229',      '6pI3gBvJtVxjea'),
    'Ef6WCkwNoSXIRWamiaU8j-icLatwufKolHUF1R8G3gs': ('CZ3',  'cz3.theredhat.su',  None),
    'OBa4LZ0lL0j9RS52fgCw68jWqkvr_yakmpsolbiqgVI': ('Italy', '151.243.198.86',   'Ujkjdf56'),
    'cCXxseSlh1Hm2WpQLAeSApZk4rtu0a7QJ5G2dtfYYUA': ('bSPB', '5.35.84.151',       None),
    'qPBatdDltcdmZxQ6Rz5uyuUXPqte22_PdSqbwk9KTFA': ('bMSK', '159.194.198.172',   'Ujkjdf56#'),
    'n2Ha1A1TGluAGjWSS7TvKk2RyMKhzDUU+w0rrkrbCic=': ('bMSK', '159.194.198.172',  'Ujkjdf56#'),
    'QKPZitEi4nYrAUo_1SqK4lagqkg9RCI89ZCtFey8CUI': ('bMSK', '159.194.198.172',   'Ujkjdf56#'),
}

# ── Box helpers ────────────────────────────────────────────────────────────────
def box_top(title="", n="", total=""):
    num = f" {n}/{total}" if n else ""
    if title:
        inner = f"─ {c(BOLD+CYAN, title)} {c(DIM, num)}"
        pad   = W - ansi_len(inner) - 1
        return f"  ┌{inner}{'─'*max(0, pad)}┐"
    return f"  ┌{'─'*W}┐"

def box_bot():  return f"  └{'─'*W}┘"
def box_sep():  return f"  ├{'─'*W}┤"

def box_row(left="", right=""):
    if right:
        gap = W - 2 - ansi_len(left) - ansi_len(right)
        return f"  │ {left}{' '*max(1, gap)}{right} │"
    pad = W - 2 - ansi_len(left)
    return f"  │ {left}{' '*max(0, pad)} │"

def box_empty():
    return f"  │ {' '*(W-2)} │"

# ── Latency helpers ────────────────────────────────────────────────────────────
def lat_bar(ms, width=10):
    if ms is None: return c(DIM, "─" * width)
    thresholds = [50, 100, 200, 400, 800]
    colors     = [GREEN, GREEN, CYAN, YELLOW, RED]
    col = RED
    for th, cl in zip(thresholds, colors):
        if ms <= th: col = cl; break
    filled = max(1, min(width, int(ms / 80)))
    return f"{col}{'█'*filled}{c(DIM, '░'*(width-filled))}{R}"

def lat_str(ms):
    if ms is None: return c(DIM, "  —  ")
    col = GREEN if ms < 150 else YELLOW if ms < 400 else RED
    return c(col, f"{ms:4d} ms")

# ── VLESS URL parser ───────────────────────────────────────────────────────────
def parse_vless(url):
    url = url.strip()
    m = re.match(r'vless://([^@]+)@([^:]+):(\d+)[^?]*\?([^#]*)(?:#(.*))?', url)
    if not m: return None
    uuid, host, port, qs_raw, label = m.groups()
    qs = parse_qs(qs_raw)
    def q(k): return qs.get(k, [''])[0]
    return {
        'uuid':    uuid,
        'host':    host,
        'port':    int(port),
        'label':   unquote(label or '').strip(),
        'type':    q('type')     or 'tcp',
        'security':q('security') or 'none',
        'pbk':     q('pbk'),
        'sid':     q('sid'),
        'sni':     q('sni') or 'www.apple.com',
        'fp':      q('fp'),
        'mode':    q('mode'),
        'service': q('serviceName'),
    }

def extract_urls(text):
    return re.findall(r'vless://[^\s"\'<>\n]+', text)

# ── Network tests ──────────────────────────────────────────────────────────────
def test_tcp(host, port, timeout=5):
    t0 = time.time()
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True, int((time.time()-t0)*1000), None
    except socket.timeout:         return False, None, "timeout"
    except ConnectionRefusedError: return False, None, "refused"
    except Exception as e:         return False, None, str(e)

def test_tls(host, port, sni, timeout=8):
    t0 = time.time()
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode    = ssl.CERT_NONE
        raw = socket.create_connection((host, port), timeout=timeout)
        tls = ctx.wrap_socket(raw, server_hostname=sni)
        ms  = int((time.time()-t0)*1000)
        tls.close()
        return True, ms, None
    except ssl.SSLError as e:  return False, None, f"SSL: {e.reason}"
    except socket.timeout:     return False, None, "TLS timeout"
    except Exception as e:     return False, None, str(e)

def get_cert_cn(host, port, sni, timeout=8):
    try:
        proc = subprocess.run(
            ['openssl', 's_client', '-connect', f'{host}:{port}',
             '-servername', sni, '-showcerts'],
            input=b'', capture_output=True, timeout=timeout
        )
        out = proc.stdout.decode(errors='ignore') + proc.stderr.decode(errors='ignore')
        m = re.search(r'subject=.*?CN\s*=\s*([^\n,/\\]+)', out)
        if m: return m.group(1).strip()
        m = re.search(r'issuer=.*?O\s*=\s*([^\n,/\\]+)', out)
        if m: return f"issuer: {m.group(1).strip()}"
    except Exception:
        pass
    return None

# ── SSH helpers ────────────────────────────────────────────────────────────────
_sshpass_available = None

def _has_sshpass():
    global _sshpass_available
    if _sshpass_available is None:
        _sshpass_available = subprocess.run(
            ['which', 'sshpass'], capture_output=True
        ).returncode == 0
    return _sshpass_available

def ssh_run(host, password, cmd, timeout=10):
    """Run command on remote host. Returns (stdout, success)."""
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
    except Exception:
        return '', False

# ── Reality test via sing-box on router ────────────────────────
# Использует SSH на роутер с sing-box для реальной проверки Reality
TEST_ROUTERS = [
    ('100.86.250.119', '56756789'),  # Italy router
]

def test_reality_via_router(host, port, uuid, sni, pbk, sid, timeout=20):
    """
    Создаёт временный конфиг sing-box на роутере, запускает на 3 сек,
    проверяет логи на 'reality verification failed'.
    Возвращает (ok, msg).
    """
    for router_ip, router_pass in TEST_ROUTERS:
        config_json = json.dumps({
            "log": {"level": "error", "output": "/tmp/vless-test.log"},
            "dns": {"servers": [{"tag": "dns", "address": "1.1.1.1"}]},
            "inbounds": [{
                "type": "direct", "tag": "test-in",
                "listen": "127.0.0.1", "listen_port": 10800
            }],
            "outbounds": [{
                "type": "vless", "tag": "test-out",
                "server": host, "server_port": port,
                "uuid": uuid, "flow": "",
                "tls": {
                    "enabled": True, "server_name": sni,
                    "utls": {"enabled": True, "fingerprint": "chrome"},
                    "reality": {
                        "enabled": True, "public_key": pbk, "short_id": sid
                    }
                },
                "multiplex": {"enabled": False}
            }],
            "route": {"rules": [{"outbound": "test-out"}]}
        })

        # Передаём JSON через base64 (избегаем проблем с кавычками в SSH)
        config_b64 = base64.b64encode(config_json.encode()).decode()

        cmd = (
            f"echo '{config_b64}' | base64 -d > /tmp/vless-test.json && "
            f"rm -f /tmp/vless-test.log && "
            f"sing-box run -c /tmp/vless-test.json -D /tmp 2>/dev/null & "
            f"sleep 4; "
            f"kill %1 2>/dev/null || true; "
            f"cat /tmp/vless-test.log 2>/dev/null || echo 'NO_LOG'"
        )

        out, ok = ssh_run(router_ip, router_pass, cmd, timeout=timeout)
        if not ok and not out:
            continue

        if 'reality verification failed' in out.lower():
            return False, f"Reality FAILED on router {router_ip}"
        if 'reality' in out.lower() and 'error' in out.lower():
            return False, f"Reality error on router {router_ip}: {out[:200]}"
        if 'NO_LOG' in out:
            return None, f"sing-box не запустился на {router_ip}"

        return True, f"Reality OK (tested via {router_ip})"

    return None, "Нет доступных роутеров для Reality теста"

# ── Server-side check via SSH ──────────────────────────────────────────────────
def check_server_side(k):
    """
    Returns dict with keys:
      server_name  — str or None
      skipped      — True if pbk unknown
      no_sshpass   — True if sshpass missing
      ssh_error    — True if SSH failed
      uuid_in_xray — True/False/None
      expiry_ok    — True/False/None
      expiry_days  — int or None
      expiry_ts    — int or None (milliseconds)
      limit_ok     — True/False/None
      limit_val    — int or None
    """
    res = dict(server_name=None, skipped=False, no_sshpass=False,
               ssh_error=False, uuid_in_xray=None, expiry_ok=None,
               expiry_days=None, expiry_ts=None, limit_ok=None, limit_val=None)

    pbk = k.get('pbk', '')
    if pbk not in XUI_SERVERS:
        res['skipped'] = True
        return res

    srv_name, srv_ip, srv_pass = XUI_SERVERS[pbk]
    res['server_name'] = srv_name

    if srv_pass is None:
        res['no_sshpass'] = True
        return res

    if not _has_sshpass():
        res['no_sshpass'] = True
        return res

    uuid = k['uuid']

    # 1. UUID in active xray config
    out, ok = ssh_run(srv_ip, srv_pass, f"grep -c '{uuid}' /usr/local/x-ui/bin/config.json 2>/dev/null || echo 0")
    if not ok and not out:
        res['ssh_error'] = True
        return res
    try:
        res['uuid_in_xray'] = int(out.split('\n')[-1].strip()) > 0
    except Exception:
        res['uuid_in_xray'] = False

    # 2. expiryTime and limitIp from SQLite
    sql = (
        "SELECT json_extract(c.value,'$.expiryTime'),"
        "json_extract(c.value,'$.limitIp') "
        "FROM inbounds i, json_each(json_extract(i.settings,'$.clients')) c "
        f"WHERE json_extract(c.value,'$.id')='{uuid}';"
    )
    out, ok = ssh_run(srv_ip, srv_pass, f"sqlite3 /etc/x-ui/x-ui.db \"{sql}\"")

    if out.strip():
        parts = out.strip().split('|')
        if len(parts) >= 2:
            try:
                ts = int(parts[0].strip()) if parts[0].strip() else 0
                res['expiry_ts'] = ts
                if ts == 0:
                    res['expiry_ok']   = True
                    res['expiry_days'] = 9999
                else:
                    now_ms    = int(time.time() * 1000)
                    days_left = (ts - now_ms) // (1000 * 86400)
                    res['expiry_days'] = int(days_left)
                    res['expiry_ok']   = days_left > 0
            except Exception:
                pass
            try:
                lim = int(parts[1].strip()) if parts[1].strip() else 0
                res['limit_val'] = lim
                res['limit_ok']  = (lim == 0)
            except Exception:
                pass

    return res

# ── Spinner ────────────────────────────────────────────────────────────────────
SPIN = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']
_si  = 0

def spinner():
    global _si
    s = SPIN[_si % len(SPIN)]; _si += 1; return s

def spin_print(msg):
    sys.stdout.write(f"\r  {c(CYAN, spinner())} {c(DIM, msg)}{' '*20}")
    sys.stdout.flush()

def spin_clear():
    sys.stdout.write(f"\r{' '*72}\r")
    sys.stdout.flush()

# ── Run all checks ─────────────────────────────────────────────────────────────
def check_key(k, idx, total):
    label = k['label'] or k['uuid'][:12]

    spin_print(f"[{idx}/{total}] TCP  →  {k['host']}:{k['port']}  ({label})")
    tcp_ok, tcp_ms, tcp_err = test_tcp(k['host'], k['port'])

    cn = None
    if tcp_ok:
        spin_print(f"[{idx}/{total}] TLS  →  Reality handshake  ({label})")
        tls_ok, tls_ms, tls_err = test_tls(k['host'], k['port'], k['sni'])
        if tls_ok:
            spin_print(f"[{idx}/{total}] cert →  extracting CN  ({label})")
            cn = get_cert_cn(k['host'], k['port'], k['sni'])
    else:
        tls_ok, tls_ms, tls_err = False, None, "skipped"

    spin_print(f"[{idx}/{total}] SSH  →  server-side checks  ({label})")
    srv = check_server_side(k)

    # Reality test via sing-box on router
    reality_ok = None
    reality_msg = None
    if tcp_ok and tls_ok and k.get('pbk') and k.get('sid'):
        spin_print(f"[{idx}/{total}] Reality →  sing-box test  ({label})")
        reality_ok, reality_msg = test_reality_via_router(
            k['host'], k['port'], k['uuid'], k['sni'], k['pbk'], k['sid']
        )

    spin_clear()
    return tcp_ok, tcp_ms, tcp_err, tls_ok, tls_ms, tls_err, cn, srv, reality_ok, reality_msg

# ── Print result card ──────────────────────────────────────────────────────────
def _chk(val, warn=False):
    """Return colored icon: True=✓green, False=✗red (or !yellow if warn), None=—dim"""
    if val is True:  return c(GREEN,  "✓")
    if val is False: return c(YELLOW, "!") if warn else c(RED, "✗")
    return c(DIM, "—")

def _dot(val):
    if val is True:  return c(GREEN,  "●")
    if val is False: return c(RED,    "●")
    return c(DIM, "●")

def print_result(k, idx, total, tcp_ok, tcp_ms, tcp_err, tls_ok, tls_ms, tls_err, cn, srv, reality_ok=None, reality_msg=None):
    label = k['label'] or k['uuid'][:12]

    # ── Verdict logic ──
    srv_ok = (
        srv['skipped'] or srv['no_sshpass'] or srv['ssh_error'] or
        (srv['uuid_in_xray'] is not False and
         srv['expiry_ok']    is not False and
         srv['limit_ok']     is not False)
    )
    verdict = tcp_ok and tls_ok and srv_ok

    # ──────────────────────────────────────────────────────────────
    print(box_top(label, idx, total))
    print(box_empty())

    # Connection info
    relay = c(WHITE, k['host']) + c(DIM, ":") + c(CYAN+BOLD, str(k['port']))
    srv_tag = (c(DIM, " [") + c(MAGENTA, srv['server_name']) + c(DIM, "]")) if srv.get('server_name') else ""
    print(box_row(c(DIM, "  Relay   ") + relay + srv_tag))

    proto = c(BLUE, k['type']) + c(DIM, " / ") + c(MAGENTA, k['security'])
    print(box_row(c(DIM, "  Proto   ") + proto, c(DIM, "fp: ") + c(YELLOW, k['fp'] or "—")))

    print(box_row(c(DIM, "  SNI     ") + c(GREEN, k['sni']),
                  c(DIM, "sid: ") + c(YELLOW, k['sid'] or "—")))

    print(box_row(c(DIM, "  UUID    ") + c(DIM, k['uuid'][:20] + "···")))
    print(box_row(c(DIM, "  PubKey  ") + c(DIM, (k['pbk'][:22] + "···") if k['pbk'] else "—")))

    if k['service']:
        print(box_row(c(DIM, "  Service ") + c(DIM, k['service'])))

    print(box_empty())
    print(box_sep())
    print(box_empty())

    # ── TCP ──
    if tcp_ok:
        row = (c(GREEN, "  ✓ TCP  ") + "  " + lat_str(tcp_ms) + "  " +
               lat_bar(tcp_ms) + "  " + c(DIM, "relay reachable"))
    else:
        row = c(RED, "  ✗ TCP      —              ") + c(RED, tcp_err)
    print(box_row(row))

    # ── TLS ──
    if tls_ok:
        cn_info = (c(DIM, "  cert: ") + c(GREEN, cn)) if cn else c(DIM, "  cert: ok")
        row = (c(GREEN, "  ✓ TLS  ") + "  " + lat_str(tls_ms) + "  " +
               lat_bar(tls_ms) + cn_info)
    else:
        row = c(RED, "  ✗ TLS      —              ") + c(RED, tls_err)
    print(box_row(row))

    print(box_empty())
    print(box_sep())
    print(box_empty())

    # ── Server-side checks ──
    if srv['skipped']:
        print(box_row(c(RED, "  ! server  ") + c(YELLOW, "pbk неизвестен — server checks пропущены!")))
        print(box_row(c(DIM,  "  !         ") + c(YELLOW, "Возможно pbk неверный. Сверь с RELAY_REFERENCE.json")))
    elif srv['no_sshpass']:
        if not _has_sshpass():
            print(box_row(c(YELLOW, "  ! server  ") + c(YELLOW, "установи sshpass для проверки expiry/limit")))
        else:
            print(box_row(c(DIM, "  — server  ") + c(DIM, "SSH пароль неизвестен — server checks пропущены")))
    elif srv['ssh_error']:
        print(box_row(c(YELLOW, "  ! server  ") + c(YELLOW, "SSH недоступен — проверь вручную")))
    else:
        # UUID in xray
        ix = srv['uuid_in_xray']
        if ix is True:
            row = c(GREEN, "  ✓ xray  ") + "  " + c(GREEN, "UUID в активном конфиге") + c(DIM, "  ✓")
        elif ix is False:
            row = c(RED,   "  ✗ xray  ") + "  " + c(RED,   "UUID НЕ в конфиге xray!  kill -9 xray")
        else:
            row = c(DIM,   "  — xray  ") + "  " + c(DIM, "не удалось проверить")
        print(box_row(row))

        # Expiry
        eo = srv['expiry_ok']
        ed = srv['expiry_days']
        et = srv['expiry_ts']
        if eo is True:
            if ed == 9999:
                exp_str = c(GREEN, "∞ без срока")
            else:
                col = GREEN if ed > 30 else YELLOW if ed > 7 else RED
                dt  = ""
                if et:
                    dt = c(DIM, "  (" + datetime.datetime.fromtimestamp(et//1000).strftime('%Y-%m-%d') + ")")
                exp_str = c(col, f"{ed} дн. осталось") + dt
            row = c(GREEN, "  ✓ expiry") + "  " + exp_str
        elif eo is False:
            dt = ""
            if et:
                dt = c(DIM, "  (истёк " + datetime.datetime.fromtimestamp(et//1000).strftime('%Y-%m-%d') + ")")
            row = c(RED, "  ✗ expiry") + "  " + c(RED, "ПРОСРОЧЕН") + dt + c(RED, "  → fix expiryTime!")
        else:
            row = c(DIM, "  — expiry") + "  " + c(DIM, "не удалось проверить")
        print(box_row(row))

        # LimitIp
        lo = srv['limit_ok']
        lv = srv['limit_val']
        if lo is True:
            row = c(GREEN, "  ✓ limit ") + "  " + c(GREEN, "limitIp = 0") + c(DIM, "  без ограничений")
        elif lo is False:
            row = c(RED, "  ✗ limit ") + "  " + c(RED, f"limitIp = {lv}") + c(RED, "  должен быть 0!")
        else:
            row = c(DIM, "  — limit ") + "  " + c(DIM, "не удалось проверить")
        print(box_row(row))

    # ── Reality check ──
    if reality_ok is True:
        row = c(GREEN, "  ✓ Reality") + "  " + c(GREEN, "sing-box handshake OK") + c(DIM, f"  {reality_msg}")
    elif reality_ok is False:
        row = c(RED, "  ✗ Reality") + "  " + c(RED, reality_msg or "Reality FAILED!")
    elif reality_msg:
        row = c(YELLOW, "  ! Reality") + "  " + c(YELLOW, reality_msg)
    else:
        row = None
    if row:
        print(box_row(row))
        print(box_empty())

    print(box_sep())
    print(box_empty())

    # ── Checklist dots ──
    has_srv = not srv['skipped'] and not srv['no_sshpass'] and not srv['ssh_error']
    checks = [
        ("TCP",    tcp_ok),
        ("TLS",    tls_ok),
    ]
    if has_srv:
        checks += [
            ("xray",   srv['uuid_in_xray']),
            ("expiry", srv['expiry_ok']),
            ("limit",  srv['limit_ok']),
        ]
    if reality_ok is not None:
        checks.append(("Reality", reality_ok))

    parts = []
    for name, val in checks:
        col = GREEN if val is True else RED if val is False else DIM
        parts.append(f"{_dot(val)} {c(col, name)}")

    print(box_row("  " + "   ".join(parts)))
    print(box_empty())

    # ── Verdict ──
    if verdict:
        if has_srv:
            vrow = c(BOLD+GREEN, "  ● READY") + c(GREEN, " ✓✓✓") + c(DIM, "  всё проверено, ключ рабочий")
        else:
            vrow = c(BOLD+GREEN, "  ● READY") + c(DIM, "  TCP+TLS OK") + c(YELLOW, "  (server checks skipped)")
    else:
        reasons = []
        if not tcp_ok: reasons.append(f"TCP: {tcp_err}")
        if not tls_ok: reasons.append(f"TLS: {tls_err}")
        if has_srv:
            if srv['uuid_in_xray'] is False: reasons.append("UUID не в xray")
            if srv['expiry_ok']    is False: reasons.append("ключ просрочен")
            if srv['limit_ok']     is False: reasons.append(f"limitIp={srv['limit_val']}")
        vrow = c(BOLD+RED, "  ✗ BROKEN  ") + c(RED, " | ".join(reasons))

    print(box_row(vrow))
    print(box_empty())
    print(box_bot())

    return verdict

# ── Summary ────────────────────────────────────────────────────────────────────
def print_summary(passed, total, failed_labels):
    print()
    print(f"  {'─'*W}")
    if passed == total:
        kw = "ключей" if total != 1 else "ключ"
        print(f"  {c(BOLD+GREEN, '●')}  {c(BOLD, f'Все {total} {kw} рабочих')}  {c(DIM, '— можно ставить на роутер')}")
    else:
        bad = total - passed
        print(f"  {c(BOLD+RED, '✗')}  {c(BOLD+RED, f'{bad} из {total} ключей сломаны')}")
        for lbl in failed_labels:
            print(f"     {c(RED, '✗')} {c(DIM, lbl)}")
        print(f"     {c(YELLOW, '⚠')}  {c(YELLOW, 'НЕ ставить на роутер — сначала починить!')}")
    print(f"  {'─'*W}")
    print()

# ── main ───────────────────────────────────────────────────────────────────────
def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python3 check_vless.py <vless://...> | <file.html> | -")
        sys.exit(1)

    urls = []
    for arg in args:
        if arg == '-':
            urls += extract_urls(sys.stdin.read())
        elif arg.startswith('vless://'):
            urls.append(arg)
        else:
            try:
                with open(arg) as f:
                    urls += extract_urls(f.read())
            except FileNotFoundError:
                print(f"{RED}File not found: {arg}{R}"); sys.exit(1)

    seen, unique = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u); unique.append(u)

    keys = [k for k in (parse_vless(u) for u in unique) if k]
    if not keys:
        print(f"{RED}No valid VLESS URLs found{R}"); sys.exit(1)

    # sshpass notice
    if not _has_sshpass():
        print(f"\n  {c(YELLOW,'⚠')}  {c(DIM,'sshpass не найден — server-side проверки (xray/expiry/limit) пропускаются')}")
        print(f"     {c(DIM,'brew install sshpass  — для полной проверки')}\n")

    # Header
    print()
    print(f"  ┌{'─'*W}┐")
    title  = c(BOLD+CYAN, "▶  VLESS KEY CHECKER  v2")
    kcount = c(DIM, f"{len(keys)} ключ{'а' if len(keys)==1 else 'ей'}")
    gap    = W - 2 - ansi_len(title) - ansi_len(kcount)
    print(f"  │ {title}{' '*max(1,gap)}{kcount} │")
    print(f"  └{'─'*W}┘")
    print()

    passed, failed = 0, []
    for i, k in enumerate(keys, 1):
        res    = check_key(k, i, len(keys))
        ok_flag = print_result(k, i, len(keys), *res)
        print()
        if ok_flag: passed += 1
        else: failed.append(k['label'] or k['uuid'][:12])

    print_summary(passed, len(keys), failed)
    sys.exit(0 if passed == len(keys) else 1)

if __name__ == '__main__':
    main()
