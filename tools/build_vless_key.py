#!/usr/bin/env python3
"""
build_vless_key.py — автомат создания VLESS-ключа
Usage:
  python3 tools/build_vless_key.py <роутер> <город> <страна> [--port порт]
  
Пример:
  python3 tools/build_vless_key.py M56-24 msk germany
  python3 tools/build_vless_key.py TR56-13 spb finland --port 4192

Что делает:
  1. Берёт схему из ключи/RELAY_REFERENCE.json
  2. Генерирует UUID
  3. SSH на целевой сервер, добавляет клиента
  4. Перезапускает xray
  5. Собирает VLESS URL
  6. check_vless.py проверка
  7. Сохраняет в ключи/client-ROUTER-LABEL.key
  8. Выводит команду для установки на роутер
"""

import sys, os, json, uuid, subprocess, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(BASE, 'ключи', 'RELAY_REFERENCE.json')

def e(cmd, inp=b''):
    r = subprocess.run(cmd, input=inp, capture_output=True, timeout=15)
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

def ssh_add_client(server_key, inbound, uuid, email):
    """Добавляет клиента на сервер через SSH по протоколу из ref['panels']"""
    ref = load_ref()
    panel = ref['panels'].get(server_key)
    if not panel:
        print(f"  ✗ Неизвестный сервер: {server_key}")
        return False
    
    ssh_pass = panel.get('ssh')
    ssh_ip = panel['url'].split('://')[1].split(':')[0] if '://' in panel['url'] else panel['url']
    
    # DE2 — без панели, правим config.json
    if server_key == 'de2':
        return ssh_add_client_de2(ssh_ip, ssh_pass, inbound, uuid, email)
    
    # Обычный сервер — sqlite
    if not ssh_pass:
        print(f"  ✗ Нет SSH пароля для {server_key}")
        return False
    
    sql = f"INSERT INTO inbounds (remark, port, protocol, settings) SELECT 'key_{email}', {inbound}, 'vless', json_set('{{\"clients\":[]}}', '$', json('[' || char(10) || '  {{\"id\":\"{uuid}\",\"flow\":\"\",\"email\":\"{email}\",\"limitIp\":0,\"totalGB\":0,\"expiryTime\":0,\"enable\":true}}' || char(10) || ']')) WHERE NOT EXISTS (SELECT 1 FROM inbounds WHERE json_extract(settings, '$.clients') LIKE '%{uuid}%');"
    
    _, err, code = e(['sshpass', '-p', ssh_pass, 'ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=5', f'root@{ssh_ip}', 
                       f'sqlite3 /etc/x-ui/x-ui.db "{sql}"'])
    if code != 0:
        print(f"  ⚠ sqlite ошибка (возможно клиент уже есть): {err[:100]}")
        return False
    
    # kill -9 xray
    e(['sshpass', '-p', ssh_pass, 'ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=5', f'root@{ssh_ip}',
       'kill -9 $(pgrep -f "xray-linux") 2>/dev/null; sleep 1; xray run -c /usr/local/x-ui/bin/config.json &>/dev/null &'])
    
    # Проверить что UUID в config.json
    out, _, _ = e(['sshpass', '-p', ssh_pass, 'ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=5', f'root@{ssh_ip}',
                    f'grep -c "{uuid}" /usr/local/x-ui/bin/config.json'])
    return uuid in out

def ssh_add_client_de2(ip, pw, inbound, uuid, email):
    """DE2 — правим config.json напрямую"""
    if isinstance(inbound, str) and inbound == 'room':
        target_port = 2087
    else:
        target_port = int(inbound)
    
    # Записываем Python-скрипт через cat + heredoc (stdin передаёт строки EOF)
    script = f'''cat > /tmp/_add_de2_client.py << 'PYEOF'
import json
c = json.load(open("/usr/local/x-ui/bin/config.json"))
for ib in c["inbounds"]:
    if ib.get("port") == {target_port}:
        cl = ib["settings"].get("clients") or []
        exist = any(cli.get("id") == "{uuid}" for cli in cl)
        if not exist:
            cl.append({{"email": "{email}", "id": "{uuid}"}})
            ib["settings"]["clients"] = cl
json.dump(c, open("/usr/local/x-ui/bin/config.json","w"), indent=2)
PYEOF
python3 /tmp/_add_de2_client.py && rm /tmp/_add_de2_client.py'''
    
    out, err, code = e(['sshpass', '-p', pw, 'ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10', f'root@{ip}',
                         script], inp=b'')
    if code != 0:
        print(f"  ✗ SSH/config правка ошибка: {err[:100]}")
        return False
    
    # restart xray-direct через systemctl
    out2, err2, code2 = e(['sshpass', '-p', pw, 'ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10', f'root@{ip}',
                           'systemctl restart xray-direct 2>&1; sleep 1; systemctl is-active xray-direct'])
    if code2 != 0:
        print(f"  ⚠ restart xray-direct: {err2[:100]}")
    else:
        print(f"  ✓ xray-direct: {out2.strip()}")
    
    # Проверить что UUID появился
    out3, _, code3 = e(['sshpass', '-p', pw, 'ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10', f'root@{ip}',
                         f'grep -c "{uuid}" /usr/local/x-ui/bin/config.json'])
    if code3 == 0 and uuid in out3:
        print(f"  ✓ UUID {uuid[:8]}... подтверждён в config.json")
        return True
    print(f"  ✗ UUID {uuid[:8]} НЕ найден в config.json!")
    return False


def build_vless_url(scheme, ptype, uuid, email):
    if ptype == 'relay':
        host = scheme['relay_ip']
        port = scheme['relay_port']
    else:
        host = scheme['server_ip']
        port = scheme['port']
    
    pbk = scheme['pbk']
    sid = scheme['sid']
    sni = scheme.get('sni', 'www.apple.com')
    fp = scheme.get('fp', 'chrome')
    t = scheme.get('type', 'grpc')
    label = scheme.get('label_suffix', '')
    
    query = f"type={t}&security=reality&mode=gun&serviceName=&pbk={pbk}&sid={sid}&sni={sni}&fp={fp}&spx=%2F"
    return f"vless://{uuid}@{host}:{port}?{query}#{email}_{label}"

def main():
    args = sys.argv[1:]
    if len(args) < 3:
        print("Usage: python3 tools/build_vless_key.py <роутер> <город> <страна> [--port N]")
        print("Города: spb, msk")
        print("Страны: finland, poland, italy, czech, germany")
        sys.exit(1)
    
    router = args[0]
    city = args[1]
    country = args[2]
    port = None
    if '--port' in args:
        port = int(args[args.index('--port') + 1])
    
    scheme, ptype = find_scheme(city, country, port)
    if not scheme:
        print(f"  ✗ Нет схемы для {city}/{country}" + (f" порт {port}" if port else ""))
        sys.exit(1)
    
    sid = scheme['id']
    print(f"\n  ┌─ BUILD VLESS KEY ─────────────────────────────┐")
    print(f"  │ Роутер: {router}  Город: {city}  Страна: {country}")
    print(f"  │ Схема:  {sid} ({ptype})")
    print(f"  └────────────────────────────────────────────────┘\n")
    
    # UUID
    uid = str(uuid.uuid4()).upper()
    email = f"{router}_{scheme.get('label_suffix', sid)}"
    print(f"  UUID:   {uid}")
    
    # SSH — добавить клиента
    server_key = scheme.get('target_server', scheme.get('panel_server'))
    inbound = scheme.get('target_inbound', scheme.get('inbound'))
    print(f"  SSH →   {server_key} inbound {inbound}")
    
    ok = ssh_add_client(server_key, inbound, uid, email)
    if not ok:
        print(f"  ⚠ Клиент мог уже быть. Продолжаем...")
    
    # Собрать URL
    url = build_vless_url(scheme, ptype, uid, email)
    print(f"\n  URL:    {url[:80]}...")
    
    # Проверить
    print(f"\n  ── Проверка через check_vless.py ──")
    out, err, code = e([sys.executable or 'python3', os.path.join(BASE, 'check_vless.py'), url])
    print(out)
    
    # Сохранить
    key_dir = os.path.join(BASE, 'ключи')
    label = scheme.get('label_suffix', sid)
    fname = f"client-{router}-{label}.key"
    fpath = os.path.join(key_dir, fname)
    with open(fpath, 'w') as f:
        f.write(url + '\n')
    print(f"  Сохранено: {fpath}")
    
    # Команда для установки на роутер
    print(f"\n  ── Установка на роутер ──")
    print(f"  uci set podkop.main.proxy_string='{url}'")
    print(f"  uci commit podkop")
    print(f"  /etc/init.d/podkop restart")
    print(f"\n  Или: python3 check_vless.py {fpath}")
    print()

if __name__ == '__main__':
    main()
