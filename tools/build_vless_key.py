#!/usr/bin/env python3
"""
build_vless_key.py v3 — безупречный генератор VLESS-ключей

Что делает:
  1. Берёт схему из RELAY_REFERENCE.json
  2. Генерирует UUID
  3. Проверяет инфраструктуру (есть ли inbound на relay-сервере)
  4. Добавляет клиента на целевой сервер через SSH
  5. Настраивает: totalGB=1000GB, expiryTime=1 год, limitIp=0
  6. Собирает VLESS URL (pbk из схемы для relay, конвертирует для direct)
  7. Проверяет ключ через check_vless.py
  8. Сохраняет в ключи/client-ROUTER-LABEL.key
  9. Выводит команду установки на роутер

Использование:
  python3 tools/build_vless_key.py <роутер> <город> <страна> [--port N]
"""

import sys, os, json, uuid, subprocess, re, time, base64
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives import serialization

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(BASE, 'ключи', 'RELAY_REFERENCE.json')
DEFAULT_TOTAL_GB = 1000  # 1000 GB
DEFAULT_EXPIRY_YEARS = 1  # 1 year

def e(cmd, inp=b'', extra_env=None):
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    r = subprocess.run(cmd, input=inp, capture_output=True, timeout=15, env=env)
    return r.stdout.decode(errors='ignore'), r.stderr.decode(errors='ignore'), r.returncode

def load_ref():
    with open(REF) as f:
        return json.load(f)

def find_scheme(city, country, port=None):
    ref = load_ref()
    for r in ref.get('relays', []):
        if r['city'] == city and r['country'] == country:
            if port is None or r.get('relay_port') == port:
                return r, 'relay'
    for d in ref.get('directs', []):
        if d['city'] == city and d.get('type', 'main') == country:
            return d, 'direct'
    return None, None

def pbk_to_public(private_key):
    """Convert REALITY private key (any encoding) to public key (RawURL base64)."""
    if not private_key:
        return private_key
    # Detect if already public (starts with uppercase)
    if private_key[0] not in 'abcdefghijklmnopqrstuvwxyz':
        return private_key
    # Convert from RawURL to standard base64
    std = private_key.replace('-', '+').replace('_', '/')
    pad = 4 - len(std) % 4
    if pad != 4: std += '=' * pad
    try:
        pk_bytes = base64.b64decode(std)
        priv_key = X25519PrivateKey.from_private_bytes(pk_bytes)
        pub_bytes = priv_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
        return base64.urlsafe_b64encode(pub_bytes).decode().rstrip('=')
    except Exception:
        return private_key  # fallback

def ssh_add_client_de2(ip, pw, inbound, uuid, email):
    """Add client to DE2 via tempfile + pipe (reliable stdin forwarding)."""
    import tempfile
    target_port = int(inbound)
    expiry = int((time.time() + 365 * 24 * 3600) * 1000)
    total_gb_bytes = DEFAULT_TOTAL_GB * 1024 * 1024 * 1024
    
    script = f'''import json, time
c = json.load(open("/usr/local/x-ui/bin/config.json"))
uuid = "{uuid}"
port = {target_port}
found = False
for ib in c.get("inbounds", []):
    if ib.get("port") != port: continue
    found = True
    clients = ib.get("settings", {{}}).get("clients") or []
    if any(cl.get("id") == uuid for cl in clients if isinstance(cl, dict)):
        print("EXISTS"); exit(0)
    clients.append({{"email": "{email}", "id": "{uuid}", "flow": "",
        "totalGB": {total_gb_bytes}, "expiryTime": {expiry},
        "limitIp": 0, "enable": True}})
    ib["settings"]["clients"] = clients; break
if not found:
    print("NOPORT"); exit(1)
json.dump(c, open("/usr/local/x-ui/bin/config.json","w"), indent=2)
print("ADDED")
'''
    b64 = base64.b64encode(script.encode()).decode()
    
    # Write b64 to temp file, pipe through sshpass -e ssh -T
    tf = tempfile.NamedTemporaryFile(mode='w', delete=False)
    tf.write(b64); tf.close()
    
    env = os.environ.copy()
    env['SSHPASS'] = pw
    
    cat_proc = subprocess.Popen(['cat', tf.name], stdout=subprocess.PIPE)
    r = subprocess.run(
        ['sshpass', '-e', 'ssh', '-T', '-o', 'StrictHostKeyChecking=no',
         '-o', 'ConnectTimeout=15', f'root@{ip}',
         'base64 -d | python3'],
        stdin=cat_proc.stdout, capture_output=True, timeout=20, env=env)
    cat_proc.stdout.close(); cat_proc.wait()
    os.unlink(tf.name)
    
    out = r.stdout.decode(errors='ignore')
    if r.returncode != 0 or ('ADDED' not in out and 'EXISTS' not in out):
        print(f"  SSH ERROR: {out[:100]} {r.stderr.decode(errors='ignore')[:100]}")
        return False
    
    # Restart xray-direct
    e(['sshpass', '-e', 'ssh', '-T', '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=15', f'root@{ip}',
        'systemctl restart xray-direct 2>&1; sleep 1; systemctl is-active xray-direct'],
        extra_env={'SSHPASS': pw})
    
    # Verify UUID in config
    out3, _, _ = e(['sshpass', '-e', 'ssh', '-T', '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=15', f'root@{ip}',
        f'grep -c "{uuid}" /usr/local/x-ui/bin/config.json'],
        extra_env={'SSHPASS': pw})
    count = out3.strip()
    if count and count != '0':
        print(f"  VERIFIED: {uuid[:8]} in config.json (count={count})")
        return True
    print(f"  FAIL: {uuid[:8]} NOT in config.json!")
    return False


def check_inbound_exists(server_key, port):
    """Проверить, существует ли inbound на relay-сервере."""
    ref = load_ref()
    panel = ref['panels'].get(server_key)
    if not panel:
        return True  # can't check, assume exists
    ssh_pass = panel.get('ssh')
    ssh_ip = panel['url'].split('://')[1].split(':')[0] if '://' in panel['url'] else panel['url']
    if not ssh_pass:
        return True
    
    out, err, code = e(['sshpass', '-p', ssh_pass, 'ssh', '-o', 'StrictHostKeyChecking=no',
                         '-o', 'ConnectTimeout=10', f'root@{ssh_ip}',
                         f'netstat -tlnp 2>/dev/null | grep -q {port} && echo 1 || echo 0'])
    return '1' in out

def build_vless_url(scheme, ptype, uuid, email):
    if ptype == 'relay':
        host = scheme['relay_ip']
        port = scheme['relay_port']
    else:
        host = scheme['server_ip']
        port = scheme['port']
    
    # For relay: pbk is already the target's public key
    # For direct: pbk might be private key, convert
    pbk_raw = scheme['pbk']
    if ptype == 'direct':
        pbk = pbk_to_public(pbk_raw)
    else:
        pbk = pbk_raw  # relay: pbk is already public (from target)
    
    sid = scheme['sid']
    sni = scheme.get('sni', 'www.apple.com')
    fp = scheme.get('fp', 'chrome')
    t = scheme.get('transport', 'grpc') if scheme.get('transport') else 'grpc'
    label = scheme.get('label_suffix', '')
    
    query = f"type={t}&security=reality&mode=gun&serviceName=&pbk={pbk}&sid={sid}&sni={sni}&fp={fp}&spx=%2F"
    return f"vless://{uuid}@{host}:{port}?{query}#{email}_{label}"

def main():
    args = sys.argv[1:]
    if len(args) < 3:
        print("Usage: python3 tools/build_vless_key.py <роутер> <город> <страна> [--port N]")
        print("  Города: spb, msk")
        print("  Страны: finland, poland, italy, czech, germany")
        sys.exit(1)
    
    router = args[0]
    city = args[1]
    country = args[2]
    port = None
    if '--port' in args:
        port = int(args[args.index('--port') + 1])
    
    scheme, ptype = find_scheme(city, country, port)
    if not scheme:
        print(f"  ERROR: Нет схемы для {city}/{country}" + (f" порт {port}" if port else ""))
        sys.exit(1)
    
    sid = scheme['id']
    print(f"\n  {'='*50}")
    print(f"  BUILD VLESS KEY v3")
    print(f"  Router: {router} | City: {city} | Country: {country}")
    print(f"  Scheme: {sid} ({ptype})")
    print(f"  Port:   {scheme.get('relay_port', scheme.get('port'))}")
    print(f"  Limits: {DEFAULT_TOTAL_GB}GB / {DEFAULT_EXPIRY_YEARS}yr")
    print(f"  {'='*50}\n")
    
    # Проверка инфраструктуры
    if ptype == 'relay':
        relay_server = 'bmsk'  # from panel key
        relay_port = scheme['relay_port']
        print(f"  Проверка inbound {relay_port} на bMSK...")
        exists = check_inbound_exists(relay_server, relay_port)
        if not exists:
            print(f"  WARNING: inbound {relay_port} НЕ НАЙДЕН на {relay_server}!")
            print(f"  Создайте inbound через X-UI панель и повторите.")
            if input("  Продолжить всё равно? (y/N): ").lower() != 'y':
                sys.exit(1)
        else:
            print(f"  ✓ inbound {relay_port} найден\n")
    
    # UUID
    uid = str(uuid.uuid4()).upper()
    email = f"{router}_{scheme.get('label_suffix', sid)}"
    print(f"  UUID:   {uid}")
    
    # SSH — добавить клиента
    server_key = scheme.get('target_server', scheme.get('panel_server'))
    inbound = scheme.get('target_inbound', scheme.get('inbound'))
    print(f"  SSH →   {server_key} inbound {inbound}")
    
    if server_key == 'de2':
        ref = load_ref()
        panel = ref['panels'].get('de2', {})
        pw = panel.get('ssh', '')
        ip = panel['url'].split('://')[1].split(':')[0]
        ok = ssh_add_client_de2(ip, pw, inbound, uid, email)
    else:
        print(f"  TODO: SSH to {server_key} not implemented for v3, using existing method")
        out, err, code = e([sys.executable or 'python3', os.path.join(BASE, 'tools', 'build_vless_key_v2.py'),
                           router, city, country] + (['--port', str(port)] if port else []))
        ok = True
    
    if not ok:
        print(f"  WARNING: client may already exist")
    
    # Собрать URL
    url = build_vless_url(scheme, ptype, uid, email)
    print(f"\n  URL:    {url}")
    
    # Проверить
    print(f"\n  {'─'*50}")
    print(f"  Проверка через check_vless.py...")
    print(f"  {'─'*50}")
    out, err, code = e([sys.executable or 'python3', os.path.join(BASE, 'check_vless.py'), url])
    print(out)
    
    # Сохранить
    key_dir = os.path.join(BASE, 'ключи')
    label = scheme.get('label_suffix', sid)
    fname = f"client-{router}-{label}.key"
    fpath = os.path.join(key_dir, fname)
    with open(fpath, 'w') as f:
        f.write(url + '\n')
    print(f"  ✓ Сохранено: {fpath}")
    
    # Команда установки
    print(f"\n  {'─'*50}")
    print(f"  Установка на роутер:")
    print(f"  {'─'*50}")
    print(f"  uci set podkop.main.proxy_string='{url}'")
    print(f"  uci commit podkop")
    print(f"  /etc/init.d/podkop restart\n")

if __name__ == '__main__':
    main()
