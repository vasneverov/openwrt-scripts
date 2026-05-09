#!/usr/bin/env python3
"""
vless_key.py — создание VLESS ключей для роутеров.

Usage:
  python3 vless_key.py z56-128                  # main + yt, профиль bmsk-fin4
  python3 vless_key.py z56-128 --main           # только main
  python3 vless_key.py z56-128 --yt             # только yt
  python3 vless_key.py z56-128 --profile fin3   # профиль fin3-bspb (M56 серия)
  python3 vless_key.py --profiles               # список профилей

Принципы (IRON RULES):
  - sqlite напрямую, никакого X-UI API (RULE 7)
  - kill -9 xray после добавления (RULE 5)
  - 5-уровневая проверка перед выдачей (RULE 4, 13)
  - Ключ НЕ сохраняется если хоть одна проверка не прошла
"""

import sys, uuid, subprocess, socket, time
from pathlib import Path
from datetime import datetime

# ── Цвета ─────────────────────────────────────────────────────────────────────
G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"; D = "\033[2m"
B = "\033[1m";  C = "\033[96m"; X = "\033[0m"
def ok(s):   return f"  {G}✅ {s}{X}"
def fail(s): return f"  {R}❌ {s}{X}"
def step(s): return f"  {D}   {s}...{X}"
def hdr(s):  return f"\n{B}{C}── {s} ──{X}"

SSHPASS  = "/opt/homebrew/bin/sshpass"
KEYS_DIR = Path.home() / "CLAUDECODE" / "ключи"

# ── Серверные профили ──────────────────────────────────────────────────────────
# Каждый профиль = пара (main-сервер, yt-сервер) + параметры ключей
PROFILES = {

    # ── Текущий основной (z56/TR56/M78 — новые роутеры) ──────────────────────
    "bmsk-fin4": {
        "desc": "bMSK relay → Fin4 (main) + bMSK direct (yt) — текущий основной",
        "folder": "bmsk-fin4",
        "main": {
            # UUID хранится на Fin4
            "server_ip":   "45.155.55.198",
            "server_pass": "duqwgjXiT4FRrc",
            "inbound_id":  1,
            "db":          "/etc/x-ui/x-ui.db",
            "xray_conf":   "/usr/local/x-ui/bin/config.json",
            # Клиент подключается через bMSK relay
            "relay_host":  "159.194.198.172",
            "relay_port":  5223,
            "pbk": "HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI",
            "sid": "4b929012",
            "sni": "www.apple.com", "fp": "chrome",
            "vless_type": "grpc&mode=gun&serviceName=",
            # Проверка цепи: с bMSK дотянуться до Fin4
            "chain_check": ("159.194.198.172", "Ujkjdf56#", "45.155.55.198", 4191),
        },
        "yt": {
            # UUID хранится на bMSK, прямой доступ
            "server_ip":   "159.194.198.172",
            "server_pass": "Ujkjdf56#",
            "inbound_id":  1,
            "db":          "/etc/x-ui/x-ui.db",
            "xray_conf":   "/usr/local/x-ui/bin/config.json",
            "relay_host":  "159.194.198.172",
            "relay_port":  8853,
            "pbk": "g5eg_BKQJLVbPxryppyE0AGpQB_HKHPGkOJN9I6bSzI",
            "sid": "1cbf0359",
            "sni": "vk.com", "fp": "firefox",
            "vless_type": "tcp&encryption=none",
            "chain_check": None,  # прямой — цепи нет
        },
    },

    # ── bMSK relay → Fin4 (main) + bMSK direct port 465 (yt) — для z56-84 ──
    "bmsk-fin4-yt465": {
        "desc": "bMSK relay → Fin4 (main) + bMSK direct port 465 (yt) — z56-84",
        "folder": "bmsk-fin4-yt465",
        "main": {
            "server_ip":   "45.155.55.198",
            "server_pass": "duqwgjXiT4FRrc",
            "inbound_id":  1,
            "db":          "/etc/x-ui/x-ui.db",
            "xray_conf":   "/usr/local/x-ui/bin/config.json",
            "relay_host":  "159.194.198.172",
            "relay_port":  5223,
            "pbk": "HfbTqAITJraOSM3J-yHpedrv-lKKe41IkU5m-4yPbHI",
            "sid": "4b929012",
            "sni": "www.apple.com", "fp": "chrome",
            "vless_type": "grpc&mode=gun&serviceName=",
            "chain_check": ("159.194.198.172", "Ujkjdf56#", "45.155.55.198", 4191),
        },
        "yt": {
            "server_ip":   "159.194.198.172",
            "server_pass": "Ujkjdf56#",
            "inbound_id":  9,
            "db":          "/etc/x-ui/x-ui.db",
            "xray_conf":   "/usr/local/x-ui/bin/config.json",
            "relay_host":  "159.194.198.172",
            "relay_port":  465,
            "pbk": "QfVJeoktRoCFJV6YdttWyGHMLnORut86toeStzTsUBk",
            "sid": "a3f7b2c1",
            "sni": "www.apple.com", "fp": "chrome",
            "vless_type": "grpc&mode=gun&serviceName=",
            "chain_check": None,
        },
    },

    # ── bMSK relay → PL5 (Польша) — для Сочи, один профиль на всё ──────────
    "bmsk-pl5": {
        "desc": "bMSK relay → PL5 (main, он же YT) — один профиль на всё",
        "folder": "bmsk-pl5",
        "main": {
            "server_ip":   "91.92.46.229",
            "server_pass": "Ujkjdf56",
            "inbound_id":  1,
            "db":          "/etc/x-ui/x-ui.db",
            "xray_conf":   "/usr/local/x-ui/bin/config.json",
            "relay_host":  "159.194.198.172",
            "relay_port":  5328,
            "pbk": "4TCLYNy_kglu_bpE5n3Gx0yQ7L8TJQKRLATLgnXbtEw",
            "sid": "3e980e42",
            "sni": "www.apple.com", "fp": "chrome",
            "vless_type": "grpc&mode=gun&serviceName=",
            "chain_check": ("159.194.198.172", "Ujkjdf56#", "91.92.46.229", 4191),
        },
        "yt": None,  # нет отдельного YT — всё через main
    },

    # ── Fin3 + bSPB (M56 серия, старые роутеры) ──────────────────────────────
    "fin3-bspb": {
        "desc": "Fin3 direct (main, port 4191) + bSPB direct (yt, port 8853) — M56 серия",
        "folder": "fin3-bspb",
        "main": {
            "server_ip":   "144.31.66.115",
            "server_pass": "Ujkjdf56",
            "inbound_id":  2,
            "db":          "/etc/x-ui/x-ui.db",
            "xray_conf":   "/usr/local/x-ui/bin/config.json",
            "relay_host":  "144.31.66.115",
            "relay_port":  4191,
            "pbk": "XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw",
            "sid": "ddcb53b3",
            "sni": "www.apple.com", "fp": "chrome",
            "vless_type": "grpc&mode=gun&serviceName=",
            "chain_check": None,
        },
        "yt": {
            "server_ip":   "5.35.84.151",
            "server_pass": "dRzEcGR*P!3%",
            "inbound_id":  4,
            "db":          "/etc/x-ui/x-ui.db",
            "xray_conf":   "/usr/local/x-ui/bin/config.json",
            "relay_host":  "5.35.84.151",
            "relay_port":  8853,
            "pbk": "me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM",
            "sid": "ddcb53b3",
            "sni": "www.apple.com", "fp": "chrome",
            "vless_type": "grpc&mode=gun&serviceName=",
            "chain_check": None,
        },
    },

}
DEFAULT_PROFILE = "bmsk-fin4"

# ── SSH helper ─────────────────────────────────────────────────────────────────
def ssh(ip, pw, cmd, timeout=15):
    r = subprocess.run(
        [SSHPASS, "-p", pw, "ssh",
         "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=6",
         "-o", "PreferredAuthentications=password", "-o", "PubkeyAuthentication=no",
         "-o", "LogLevel=quiet", f"root@{ip}", cmd],
        capture_output=True, timeout=timeout
    )
    return r.stdout.decode().strip(), r.returncode == 0

def tcp(host, port, timeout=6):
    try:
        socket.create_connection((host, port), timeout=timeout).close()
        return True
    except Exception:
        return False

# ── Добавление UUID в sqlite ───────────────────────────────────────────────────
def sqlite_add(cfg, uid, email):
    iid = cfg["inbound_id"]
    py  = f"""
import sqlite3, json, time
conn = sqlite3.connect('{cfg["db"]}')
row  = conn.execute('SELECT settings FROM inbounds WHERE id={iid}').fetchone()
data = json.loads(row[0])
data['clients'].append({{
    'id':'{uid}','email':'{email}','limitIp':0,
    'totalGB':1099511627776,
    'expiryTime':int((time.time()+365*24*3600)*1000),
    'enable':True,'tgId':'','subId':'','comment':''
}})
conn.execute('UPDATE inbounds SET settings=? WHERE id={iid}',[json.dumps(data)])
conn.commit()
print(len(data['clients']))
"""
    out, ok = ssh(cfg["server_ip"], cfg["server_pass"], f"python3 -c {repr(py)}")
    return out.strip().split('\n')[-1] if ok else None

# ── Получить поля клиента из sqlite ───────────────────────────────────────────
def sqlite_get_client(cfg, uid):
    iid = cfg["inbound_id"]
    py  = f"""
import sqlite3, json
conn = sqlite3.connect('{cfg["db"]}')
row  = conn.execute('SELECT settings FROM inbounds WHERE id={iid}').fetchone()
data = json.loads(row[0])
for c in data['clients']:
    if c.get('id') == '{uid}':
        import sys
        print(c.get('enable','?'), c.get('expiryTime','?'), c.get('limitIp','?'))
        sys.exit(0)
print('NOT_FOUND')
"""
    out, _ = ssh(cfg["server_ip"], cfg["server_pass"], f"python3 -c {repr(py)}")
    return out.strip()

# ── 5-уровневая проверка ───────────────────────────────────────────────────────
def verify(cfg, uid, key_type):
    ip, pw = cfg["server_ip"], cfg["server_pass"]
    errors = []

    # 1. sqlite: поля клиента
    print(step("1/5 sqlite fields"))
    fields = sqlite_get_client(cfg, uid)
    if "NOT_FOUND" in fields or not fields:
        errors.append("UUID не найден в sqlite")
    else:
        parts = fields.split()
        enable    = parts[0] if len(parts) > 0 else "?"
        expiry_ts = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        limit_ip  = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else -1
        now_ms    = int(time.time() * 1000)
        expiry_ok = (expiry_ts == 0 or expiry_ts > now_ms)
        if enable != "True":
            errors.append(f"enable={enable}")
        if not expiry_ok:
            errors.append("expiryTime истёк")
        if limit_ip != 0:
            errors.append(f"limitIp={limit_ip}")
        if not errors:
            print(ok(f"sqlite: enable=True, limitIp=0, expiry OK"))

    # 2. kill xray → перезапуск
    print(step("2/5 kill xray → reload config"))
    ssh(ip, pw, "kill -9 $(pgrep xray) 2>/dev/null")
    time.sleep(5)

    # 3. UUID в активном config.json
    print(step("3/5 UUID в xray config.json"))
    out, _ = ssh(ip, pw, f"grep -c '{uid}' {cfg['xray_conf']} 2>/dev/null || echo 0")
    count  = int(out.strip().split('\n')[-1]) if out.strip() else 0
    if count == 0:
        errors.append("UUID не в config.json после xray restart")
    else:
        print(ok(f"UUID в config.json: {count} раз"))

    # 4. xray процесс жив
    print(step("4/5 xray process running"))
    out, _ = ssh(ip, pw, "pgrep xray | wc -l")
    procs  = int(out.strip()) if out.strip().isdigit() else 0
    if procs == 0:
        errors.append("xray не запущен после restart!")
    else:
        print(ok(f"xray running (pid count: {procs})"))

    # 5a. TCP на relay
    rh, rp = cfg["relay_host"], cfg["relay_port"]
    print(step(f"5a/5 TCP → {rh}:{rp}"))
    if not tcp(rh, rp):
        errors.append(f"TCP недоступен: {rh}:{rp}")
    else:
        print(ok(f"TCP OK → {rh}:{rp}"))

    # 5b. Relay chain (если есть)
    chain = cfg.get("chain_check")
    if chain:
        chain_relay_ip, chain_relay_pw, chain_dst_ip, chain_dst_port = chain
        print(step(f"5b/5 relay chain: bMSK → {chain_dst_ip}:{chain_dst_port}"))
        out, _ = ssh(chain_relay_ip, chain_relay_pw,
                     f"timeout 5 bash -c 'echo > /dev/tcp/{chain_dst_ip}/{chain_dst_port}' 2>&1 && echo OK || echo FAIL")
        if "OK" not in out:
            errors.append(f"relay chain broken: bMSK → {chain_dst_ip}:{chain_dst_port}")
        else:
            print(ok(f"relay chain OK: bMSK → {chain_dst_ip}:{chain_dst_port}"))

    return errors

# ── Сборка vless URL ───────────────────────────────────────────────────────────
def build_url(cfg, uid, label):
    rh, rp = cfg["relay_host"], cfg["relay_port"]
    vt     = cfg["vless_type"]
    return (
        f"vless://{uid}@{rh}:{rp}?"
        f"type={vt}&security=reality&"
        f"pbk={cfg['pbk']}&sid={cfg['sid']}&sni={cfg['sni']}&fp={cfg['fp']}&spx=%2F"
        f"#{label}"
    )

# ── Сохранение ────────────────────────────────────────────────────────────────
def save(profile_name, folder, router_name, keys):
    dest = KEYS_DIR / folder
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / f"{router_name}.md"
    now  = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"# {router_name} · {profile_name}\nСоздано: {now}\n\n"]
    for kt, uid, vless in keys:
        lines += [f"## {kt.upper()}\n`{uid}`\n```\n{vless}\n```\n\n"]
    path.write_text("".join(lines))
    return path

# ── main ──────────────────────────────────────────────────────────────────────
def main():
    args = sys.argv[1:]

    if "--profiles" in args:
        print(f"\n{B}Доступные профили:{X}")
        for k, v in PROFILES.items():
            marker = " ← default" if k == DEFAULT_PROFILE else ""
            print(f"  {C}{k}{X}{marker}  —  {v['desc']}")
        return

    if not args:
        print("Usage: vless_key.py <router_name> [--main|--yt] [--profile NAME]"); sys.exit(1)

    router_name = args[0]
    profile_name = DEFAULT_PROFILE
    if "--profile" in args:
        idx = args.index("--profile")
        profile_name = args[idx + 1] if idx + 1 < len(args) else DEFAULT_PROFILE

    if profile_name not in PROFILES:
        print(fail(f"Профиль '{profile_name}' не найден. Используй --profiles")); sys.exit(1)

    if "--main" in args:
        types = ["main"]
    elif "--yt" in args:
        types = ["yt"]
    else:
        types = ["main", "yt"]

    if not Path(SSHPASS).exists():
        print(fail(f"sshpass не найден: {SSHPASS}")); sys.exit(1)

    profile = PROFILES[profile_name]
    print(f"\n{B}▶ {router_name}  [{profile_name}]  →  {' + '.join(types)}{X}")
    print(f"  {D}{profile['desc']}{X}")

    created = []
    for kt in types:
        cfg = profile[kt]
        uid = str(uuid.uuid4())
        print(hdr(f"{kt.upper()} → {cfg['server_ip']} (inbound {cfg['inbound_id']})"))

        # Добавляем в sqlite
        print(step("0/5 добавляю в sqlite"))
        result = sqlite_add(cfg, uid, router_name)
        if result is None:
            print(fail("sqlite: не удалось добавить клиента")); sys.exit(1)
        print(ok(f"sqlite: клиентов в инбаунде = {result}"))

        # 5-уровневая проверка
        errors = verify(cfg, uid, kt)

        if errors:
            print(f"\n  {R}{B}✗ ПРОВЕРКА НЕ ПРОЙДЕНА:{X}")
            for e in errors:
                print(f"    {R}• {e}{X}")
            print(f"\n  {Y}Ключ НЕ сохранён — исправь ошибки перед установкой{X}")
            sys.exit(1)

        label = f"{router_name}_{kt}"
        vless = build_url(cfg, uid, label)
        created.append((kt, uid, vless))

        print(f"\n  {G}{B}● READY ✓✓✓{X}  {D}{label}{X}")
        print(f"  {vless}")

    # Сохраняем только если все ключи прошли
    path = save(profile_name, profile["folder"], router_name, created)
    print(f"\n{ok(f'Сохранено: {path}')}")
    print(f"\n{G}{B}{'─'*60}")
    print(f"● ГОТОВО: {router_name} — {len(created)} ключ(а) проверены и сохранены")
    print(f"{'─'*60}{X}")
    print(f"  {D}Полная проверка: python3 check_vless.py {path}{X}\n")

if __name__ == "__main__":
    main()
