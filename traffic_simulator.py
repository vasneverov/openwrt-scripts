#!/usr/bin/env python3
"""
traffic_simulator.py — симуляция трафика роутера к ключевым сервисам
Запускает curl через sing-box на роутере и проверяет доступность сайтов.

Usage:
  python3 traffic_simulator.py <router_ip> [password]
  
Пример:
  python3 traffic_simulator.py 100.113.119.79 56756789
"""

import sys, subprocess, json, re, time, os
from datetime import datetime

# ── ANSI ──
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

# ── Список сервисов для проверки ──
SERVICES = [
    # (имя, URL, ожидаемый статус, описание)
    ("🌐 Google",       "https://www.google.com",       200, "Поисковик"),
    ("📺 YouTube",      "https://www.youtube.com",      200, "Видео"),
    ("✈️ Telegram",     "https://telegram.org",         200, "Мессенджер"),
    ("📘 Facebook",     "https://www.facebook.com",     200, "Соцсеть"),
    ("🐙 GitHub",       "https://github.com",           200, "Git"),
    ("🟢 WhatsApp",     "https://www.whatsapp.com",     200, "WhatsApp"),
]

def ssh_run(router_ip, password, cmd, timeout=15):
    """Run command on router via sshpass"""
    full = [
        'sshpass', '-p', password,
        'ssh', '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=5',
        '-o', 'LogLevel=quiet',
        f'root@{router_ip}',
        cmd
    ]
    try:
        r = subprocess.run(full, capture_output=True, timeout=timeout)
        return r.stdout.decode(errors='ignore').strip(), r.stderr.decode(errors='ignore').strip(), r.returncode
    except subprocess.TimeoutExpired:
        return '', 'TIMEOUT', -1
    except Exception as e:
        return '', str(e), -1

def check_service_via_router(router_ip, password, name, url, expected_status):
    """Check service access through router's sing-box"""
    
    # Команда curl через роутер с таймаутом
    cmd = (
        f'curl -sL -o /dev/null -w "%{{http_code}}:%{{time_total}}" '
        f'--connect-timeout 8 --max-time 12 '
        f'-H "User-Agent: Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36" '
        f'"{url}" 2>&1'
    )
    
    stdout, stderr, rc = ssh_run(router_ip, password, cmd, timeout=20)
    
    # Парсим результат
    http_code = None
    latency = None
    error = None
    
    if stdout and ':' in stdout:
        parts = stdout.split(':')
        try:
            http_code = int(parts[0])
            latency = float(parts[1]) if len(parts) > 1 else None
        except ValueError:
            error = stdout[:100]
    elif stderr:
        error = stderr[:100]
    else:
        error = f"rc={rc}"
    
    # Определяем статус
    if http_code and http_code == expected_status:
        status = "✅"
        status_text = "OK"
    elif http_code:
        status = "⚠️"
        status_text = f"HTTP {http_code}"
    else:
        status = "❌"
        status_text = error or "NO RESPONSE"
    
    return {
        'name': name,
        'url': url,
        'http_code': http_code,
        'latency': latency,
        'status': status,
        'status_text': status_text,
        'expected': expected_status,
    }

def print_table(results, router_ip, router_name):
    """Print beautiful table"""
    
    # Заголовок
    print()
    print(f"  {'═'*68}")
    print(f"  {b(CYAN)}📡  СИМУЛЯЦИЯ ТРАФИКА РОУТЕРА{R}")
    print(f"  {DIM}   Роутер: {router_name} ({router_ip}){R}")
    print(f"  {DIM}   Время:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{R}")
    print(f"  {'═'*68}")
    print()
    
    # Таблица
    header = (
        f"  {b('№')}  {b('Сервис'):<20} {b('URL'):<38} {b('Код')}  {b('Задержка')}  {b('Статус')}"
    )
    print(header)
    print(f"  {'─'*68}")
    
    passed = 0
    total = len(results)
    
    for i, r in enumerate(results, 1):
        name = r['name']
        url_short = r['url'].replace('https://www.', '').replace('https://', '')[:35]
        code = str(r['http_code']) if r['http_code'] else '—'
        
        if r['latency'] is not None:
            lat = f"{r['latency']*1000:.0f}ms"
            lat_col = GREEN if r['latency'] < 2 else YELLOW if r['latency'] < 5 else RED
            lat_str = c(lat_col, f"{lat:>7}")
        else:
            lat_str = c(DIM, "     —")
        
        status = r['status']
        if r['status'] == "✅":
            passed += 1
            status_str = c(GREEN, f"  {status} {r['status_text']}")
        elif r['status'] == "⚠️":
            status_str = c(YELLOW, f"  {status} {r['status_text']}")
        else:
            status_str = c(RED, f"  {status} {r['status_text']}")
        
        code_col = GREEN if r['http_code'] == r['expected'] else YELLOW if r['http_code'] else RED
        code_str = c(code_col, f"{code:>4}")
        
        print(f"  {i:<2} {name:<20} {url_short:<38} {code_str} {lat_str} {status_str}")
    
    print(f"  {'─'*68}")
    
    # Итог
    if passed == total:
        print(f"  {c(GREEN, '✅  ВСЕ СЕРВИСЫ ДОСТУПНЫ')}  {c(DIM, f'({passed}/{total})')}")
    elif passed > 0:
        print(f"  {c(YELLOW, f'⚠️  {passed}/{total} сервисов доступны')}  {c(DIM, f'{total-passed} недоступны')}")
    else:
        print(f"  {c(RED, f'❌  ВСЕ {total} СЕРВИСОВ НЕДОСТУПНЫ')}")
    
    print(f"  {'═'*68}")
    print()

def get_router_name(router_ip, password):
    """Get router hostname"""
    out, _, _ = ssh_run(router_ip, password, 'hostname 2>/dev/null || echo "Router"', timeout=5)
    return out.strip() or router_ip

def main():
    if len(sys.argv) < 2:
        print(f"Usage: python3 traffic_simulator.py <router_ip> [password]")
        print(f"Пример: python3 traffic_simulator.py 100.113.119.79 56756789")
        sys.exit(1)
    
    router_ip = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else "56756789"
    
    # Проверяем sshpass
    if subprocess.run(['which', 'sshpass'], capture_output=True).returncode != 0:
        print(f"{RED}sshpass не найден. Установи: brew install sshpass{R}")
        sys.exit(1)
    
    # Получаем имя роутера
    router_name = get_router_name(router_ip, password)
    
    # Проверяем доступность роутера
    print(f"\n  {CYAN}🔌 Подключаюсь к {router_name} ({router_ip})...{R}")
    out, err, rc = ssh_run(router_ip, password, 'echo OK', timeout=5)
    if out != 'OK':
        print(f"  {RED}❌ Роутер недоступен: {err or out}{R}")
        sys.exit(1)
    print(f"  {GREEN}✅ Подключение установлено{R}")
    
    # Проверяем curl на роутере
    out, _, _ = ssh_run(router_ip, password, 'which curl 2>/dev/null || echo "NO_CURL"', timeout=5)
    if 'NO_CURL' in out:
        print(f"  {YELLOW}⚠️ curl не найден на роутере. Установка...{R}")
        ssh_run(router_ip, password, 'opkg update && opkg install curl', timeout=60)
    
    # Запускаем проверки
    print(f"\n  {CYAN}📡 Запуск симуляции трафика...{R}\n")
    
    results = []
    for i, (name, url, expected, desc) in enumerate(SERVICES, 1):
        sys.stdout.write(f"\r  {CYAN}▶ [{i}/{len(SERVICES)}]{R} {name}...  ")
        sys.stdout.flush()
        
        result = check_service_via_router(router_ip, password, name, url, expected)
        results.append(result)
        
        status_icon = result['status']
        lat_info = f" {result['latency']*1000:.0f}ms" if result['latency'] else ""
        sys.stdout.write(f"\r  {' ' * 60}\r")
        sys.stdout.write(f"  {status_icon} [{i}/{len(SERVICES)}] {name} — {result['status_text']}{lat_info}\n")
        sys.stdout.flush()
        
        time.sleep(0.3)  # небольшая пауза между запросами
    
    # Выводим таблицу
    print_table(results, router_ip, router_name)
    
    # Сохраняем отчёт
    report = {
        'router': router_name,
        'router_ip': router_ip,
        'timestamp': datetime.now().isoformat(),
        'results': results,
        'passed': sum(1 for r in results if r['status'] == "✅"),
        'total': len(results),
    }
    
    report_file = f"/Users/vas/Desktop/traffic_report_{router_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"  {DIM}📄 Отчёт сохранён: {report_file}{R}")
    print()

if __name__ == '__main__':
    main()
