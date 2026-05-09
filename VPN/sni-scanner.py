#!/usr/bin/env python3
"""
SNI Scanner для VLESS+Reality
Ищет подходящие домены: TLS 1.3 + HTTP/2 + нет редиректа + низкий пинг

Запуск:
  python3 sni-scanner.py                    # проверяет встроенный список
  python3 sni-scanner.py domains.txt        # проверяет домены из файла
  python3 sni-scanner.py via 82.38.66.75    # через SSH на VPS (нужен sshpass)

Подходящий SNI: TLS1.3=✓, H2=✓, Redir=✗, пинг < 300ms
"""

import ssl, socket, sys, time, concurrent.futures
from datetime import datetime

# Список кандидатов (польские/европейские корпоративные)
DOMAINS = [
    # Польские банки/корпорации
    "www.bnpparibas.pl",
    "www.ing.pl",
    "www.pekao.com.pl",
    "www.mbank.pl",
    "www.pkobp.pl",
    "www.santander.pl",
    "www.aliorbank.pl",

    # Польские госорганы/корпорации
    "www.pkn.pl",
    "www.pge.pl",
    "www.orlen.pl",
    "www.lotos.pl",

    # EU институции (работают отлично)
    "www.europarl.europa.eu",
    "ec.europa.eu",
    "www.consilium.europa.eu",
    "www.ecb.europa.eu",

    # Немецкие корпорации
    "www.commerzbank.de",
    "www.dw.com",
    "www.siemens.com",
    "www.bayer.com",
    "www.volkswagen.de",
    "www.bmwgroup.com",

    # Французские
    "www.bnpparibas.com",
    "group.credit-agricole.com",
    "www.airbus.com",

    # Нидерланды/Бельгия
    "www.ing.com",
    "www.shell.com",
    "www.philips.com",
    "www.ab-inbev.com",
]

def check_domain(domain, port=443, timeout=4):
    """Проверяет домен на совместимость с Reality"""
    result = {
        "domain": domain,
        "tls13": False,
        "h2": False,
        "redirect": False,
        "latency_ms": None,
        "error": None,
    }

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.set_alpn_protocols(["h2", "http/1.1"])

    try:
        t0 = time.time()
        with socket.create_connection((domain, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                t1 = time.time()
                result["latency_ms"] = round((t1 - t0) * 1000)
                result["tls13"] = ssock.version() == "TLSv1.3"
                result["h2"] = ssock.selected_alpn_protocol() == "h2"

                # Быстрая проверка на редирект через HTTP/1.1 HEAD
                try:
                    req = f"HEAD / HTTP/1.1\r\nHost: {domain}\r\nConnection: close\r\n\r\n"
                    ssock.sendall(req.encode())
                    resp = ssock.recv(512).decode("utf-8", errors="replace")
                    first_line = resp.split("\r\n")[0] if resp else ""
                    if any(code in first_line for code in ["301", "302", "303", "307", "308"]):
                        result["redirect"] = True
                except Exception:
                    pass

    except ssl.SSLError as e:
        # TLS 1.3 не поддерживается — пробуем без минимальной версии
        result["error"] = f"TLS: {e}"
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        result["error"] = f"Conn: {e}"
    except Exception as e:
        result["error"] = f"Err: {e}"

    return result


def main():
    domains = DOMAINS

    if len(sys.argv) >= 2:
        if sys.argv[1] == "via" and len(sys.argv) >= 3:
            # Запуск через SSH на VPS
            vps_ip = sys.argv[2]
            print(f"[*] Запуск сканера на VPS {vps_ip} через SSH...")
            import subprocess, os
            script_path = os.path.abspath(__file__)
            cmd = ["sshpass", "-p", "T-RUeIl9%+", "ssh", "-o", "StrictHostKeyChecking=no",
                   f"root@{vps_ip}", f"python3 -c \"{open(script_path).read().replace('\"', chr(39))}\""]
            # Проще: скопировать и запустить
            subprocess.run(["sshpass", "-p", "T-RUeIl9%+", "scp", "-o", "StrictHostKeyChecking=no",
                           script_path, f"root@{vps_ip}:/tmp/sni_scan.py"])
            subprocess.run(["sshpass", "-p", "T-RUeIl9%+", "ssh", "-o", "StrictHostKeyChecking=no",
                           f"root@{vps_ip}", "python3 /tmp/sni_scan.py"])
            return
        elif not sys.argv[1].startswith("via"):
            # Файл с доменами
            try:
                with open(sys.argv[1]) as f:
                    domains = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                print(f"[*] Загружено {len(domains)} доменов из {sys.argv[1]}")
            except FileNotFoundError:
                print(f"Файл не найден: {sys.argv[1]}")
                sys.exit(1)

    print(f"[*] Проверяем {len(domains)} доменов... ({datetime.now().strftime('%H:%M:%S')})")
    print("-" * 70)

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_domain, d): d for d in domains}
        for future in concurrent.futures.as_completed(futures):
            r = future.result()
            status = "✓" if (r["tls13"] and r["h2"] and not r["redirect"] and not r["error"]) else "✗"
            if r["error"]:
                print(f"  {status} {r['domain']:<35} ERROR: {r['error']}")
            else:
                redir = "REDIR" if r["redirect"] else "     "
                print(f"  {status} {r['domain']:<35} TLS1.3={'✓' if r['tls13'] else '✗'}  H2={'✓' if r['h2'] else '✗'}  {redir}  {r['latency_ms']}ms")
            results.append(r)

    # Финальный список подходящих
    good = [r for r in results if r["tls13"] and r["h2"] and not r["redirect"] and not r["error"] and r["latency_ms"] is not None]
    good.sort(key=lambda x: x["latency_ms"])

    print()
    print("=" * 70)
    print(f"ПОДХОДЯЩИЕ SNI для Reality ({len(good)} из {len(domains)}):")
    print("=" * 70)
    for r in good:
        print(f"  {r['domain']:<40}  {r['latency_ms']}ms")

    if good:
        print()
        print("Лучший SNI (для вставки в Reality serverNames):")
        print(f"  {good[0]['domain']}")
        if len(good) > 1:
            print(f"  Запасной: {good[1]['domain']}")

if __name__ == "__main__":
    main()
