#!/root/deepseek-env/bin/python3
"""
╔══════════════════════════════════════════════════════════════╗
║  DS — DeepSeek CLI v2                                       ║
║  Полный аналог Cline для удалённой диагностики роутеров     ║
║  Запуск: ds                                                  ║
║  Модель: DeepSeek V4 Flash API                               ║
║  Сервер: PL5 (91.92.46.229)                                  ║
║  Репозиторий: /root/router-lab (синхронизация с GitHub)      ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import subprocess
import readline
import shutil
import re
import signal
import textwrap
from datetime import datetime

# =============================================================================
# КОНФИГУРАЦИЯ
# =============================================================================
DEEPSEEK_API_KEY = "sk-7253edfd69f8438ca39b911ae597ad8e"
DEEPSEEK_MODEL = "deepseek-chat"  # V4 Flash
WORK_DIR = "/root/router-lab"
HISTORY_FILE = "/root/.ds_history"
MAX_HISTORY = 100

# Цены DeepSeek V4 Flash (за 1M токенов)
PRICE_INPUT_PER_1M = 0.07    # $0.07 за 1M input токенов
PRICE_OUTPUT_PER_1M = 0.27   # $0.27 за 1M output токенов

# Трекер стоимости сессии (как в Cline)
session_stats = {
    "input_tokens": 0,
    "output_tokens": 0,
    "total_cost": 0.0,
    "requests": 0
}

# =============================================================================
# ЦВЕТА (как в Cline)
# =============================================================================
class C:
    HDR = '\033[95m'
    BLU = '\033[94m'
    CYN = '\033[96m'
    GRN = '\033[92m'
    YLW = '\033[93m'
    RED = '\033[91m'
    BLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'
    CLR = '\033[2J\033[H'  # Clear screen

def print_banner():
    """Баннер как в Cline"""
    tw = shutil.get_terminal_size().columns
    print(f"{C.CLN}{C.END}")
    print(f"{C.BLD}{C.CYN}  ╔══════════════════════════════════════════════════╗{C.END}")
    print(f"{C.BLD}{C.CYN}  ║  DS — DeepSeek CLI v2                           ║{C.END}")
    print(f"{C.BLD}{C.CYN}  ║  Полный аналог Cline для роутеров               ║{C.END}")
    print(f"{C.BLD}{C.CYN}  ║  Модель: {DEEPSEEK_MODEL}{C.END}")
    print(f"{C.BLD}{C.CYN}  ║  Сервер: PL5 (91.92.46.229)                     ║{C.END}")
    print(f"{C.BLD}{C.CYN}  ║  Репозиторий: {WORK_DIR}{C.END}")
    print(f"{C.BLD}{C.CYN}  ╚══════════════════════════════════════════════════╝{C.END}")
    print()

def print_help():
    """Помощь"""
    print(f"{C.BLD}Команды:{C.END}")
    print(f"  {C.GRN}/help{C.END}       — показать эту справку")
    print(f"  {C.GRN}/exit{C.END}       — выйти (автосохранение в GitHub)")
    print(f"  {C.GRN}/sync{C.END}       — синхронизация с GitHub")
    print(f"  {C.GRN}/status{C.END}     — статус синхронизации")
    print(f"  {C.GRN}/cost{C.END}       — стоимость сессии")
    print(f"  {C.GRN}/bash <cmd>{C.END} — выполнить bash-команду")
    print(f"  {C.GRN}/read <file>{C.END} — прочитать файл")
    print(f"  {C.GRN}/write <file>{C.END} — записать файл")
    print(f"  {C.GRN}/clear{C.END}      — очистить экран")
    print(f"  {C.GRN}/context{C.END}    — показать текущий контекст")
    print()
    print(f"{C.DIM}Или просто задай вопрос — я передам его DeepSeek{C.END}")
    print()

def print_cost():
    """Показать стоимость сессии как в Cline"""
    total = session_stats["total_cost"]
    inp = session_stats["input_tokens"]
    out = session_stats["output_tokens"]
    req = session_stats["requests"]
    
    print(f"\n{C.BLD}{C.CYN}  ╔══ СТОИМОСТЬ СЕССИИ ══╗{C.END}")
    print(f"{C.CYN}  ║{C.END}  Запросов:        {req:>5}")
    print(f"{C.CYN}  ║{C.END}  Input tokens:    {inp:>7}")
    print(f"{C.CYN}  ║{C.END}  Output tokens:   {out:>7}")
    if total > 0:
        print(f"{C.CYN}  ║{C.END}  {C.GRN}Стоимость:      ${total:.4f}{C.END}")
        print(f"{C.CYN}  ║{C.END}  {C.GRN}              ≈ {total*100:.2f}¢{C.END}")
    else:
        print(f"{C.CYN}  ║{C.END}  {C.DIM}Стоимость:      $0.0000{C.END}")
    print(f"{C.BLD}{C.CYN}  ╚══════════════════════╝{C.END}")
    print()

def track_usage(usage):
    """Записать usage в статистику сессии"""
    inp = usage.get("prompt_tokens", 0)
    out = usage.get("completion_tokens", 0)
    session_stats["input_tokens"] += inp
    session_stats["output_tokens"] += out
    session_stats["requests"] += 1
    cost = (inp / 1_000_000 * PRICE_INPUT_PER_1M) + (out / 1_000_000 * PRICE_OUTPUT_PER_1M)
    session_stats["total_cost"] += cost

# =============================================================================
# API ВЫЗОВЫ
# =============================================================================

def call_deepseek(messages, stream=True):
    """Вызов DeepSeek API с поддержкой streaming"""
    import urllib.request
    
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    data = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "stream": stream,
        "max_tokens": 8192,
        "temperature": 0.3
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers=headers,
        method="POST"
    )
    
    try:
        if stream:
            # Streaming режим — выводим токены по мере получения
            response = urllib.request.urlopen(req, timeout=180)
            full_content = ""
            
            for chunk_bytes in response:
                chunk = chunk_bytes.decode('utf-8')
                if chunk.startswith('data: '):
                    chunk_data = chunk[6:].strip()
                    if chunk_data == '[DONE]':
                        break
                    try:
                        parsed = json.loads(chunk_data)
                        delta = parsed.get('choices', [{}])[0].get('delta', {})
                        content = delta.get('content', '')
                        if content:
                            full_content += content
                            print(content, end='', flush=True)
                    except json.JSONDecodeError:
                        pass
            
            print()  # newline after streaming
            # В streaming режиме usage не приходит, оцениваем по длине
            inp_est = len(json.dumps(messages)) // 4  # грубая оценка
            out_est = len(full_content) // 4
            usage_est = {"prompt_tokens": inp_est, "completion_tokens": out_est}
            track_usage(usage_est)
            return full_content, usage_est
        else:
            # Non-streaming
            with urllib.request.urlopen(req, timeout=180) as response:
                result = json.loads(response.read())
                content = result["choices"][0]["message"]["content"]
                usage = result.get("usage", {})
                track_usage(usage)
                return content, usage
    except Exception as e:
        return f"{C.RED}Ошибка API: {e}{C.END}", {}

# =============================================================================
# ВЫПОЛНЕНИЕ КОМАНД
# =============================================================================

def execute_command(cmd):
    """Выполнить bash команду"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=WORK_DIR
        )
        output = result.stdout + result.stderr
        if not output.strip():
            output = f"(команда выполнена, код: {result.returncode})"
        return output
    except subprocess.TimeoutExpired:
        return f"{C.RED}Команда превысила таймаут (120с){C.END}"
    except Exception as e:
        return f"{C.RED}Ошибка: {e}{C.END}"

def read_file(path):
    """Прочитать файл"""
    full_path = os.path.join(WORK_DIR, path) if not path.startswith("/") else path
    try:
        with open(full_path, 'r') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"{C.RED}Ошибка чтения {path}: {e}{C.END}"

def write_file(path, content):
    """Записать файл"""
    full_path = os.path.join(WORK_DIR, path) if not path.startswith("/") else path
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
        return f"{C.GRN}✓ Файл {path} сохранён{C.END}"
    except Exception as e:
        return f"{C.RED}Ошибка записи {path}: {e}{C.END}"

# =============================================================================
# GIT ОПЕРАЦИИ
# =============================================================================

def git_sync():
    """Синхронизация с GitHub"""
    print(f"{C.YLW}>>> Синхронизация с GitHub...{C.END}")
    
    result = subprocess.run(
        "git fetch origin main 2>&1 && git reset --hard origin/main 2>&1",
        shell=True, capture_output=True, text=True, cwd=WORK_DIR
    )
    output = result.stdout + result.stderr
    
    head = subprocess.run(
        "git rev-parse HEAD | head -c 8",
        shell=True, capture_output=True, text=True, cwd=WORK_DIR
    ).stdout.strip()
    
    print(f"{C.DIM}{output[:300]}{C.END}")
    print(f"{C.GRN}✓ Готово. HEAD: {head}{C.END}")
    return head

def git_save():
    """Сохранить изменения в GitHub"""
    print(f"{C.YLW}>>> Сохраняю изменения в GitHub...{C.END}")
    
    status = subprocess.run(
        "git status --short",
        shell=True, capture_output=True, text=True, cwd=WORK_DIR
    ).stdout.strip()
    
    if not status:
        print(f"{C.DIM}Нет изменений{C.END}")
        return
    
    subprocess.run(
        f"git add -A 2>&1 && git commit -m 'ds: auto-save {datetime.now().strftime('%Y-%m-%d %H:%M')}' 2>&1",
        shell=True, capture_output=True, text=True, cwd=WORK_DIR
    )
    
    result = subprocess.run(
        "git push origin main --force 2>&1",
        shell=True, capture_output=True, text=True, cwd=WORK_DIR
    )
    output = result.stdout + result.stderr
    
    head = subprocess.run(
        "git rev-parse HEAD | head -c 8",
        shell=True, capture_output=True, text=True, cwd=WORK_DIR
    ).stdout.strip()
    
    print(f"{C.DIM}{output[:300]}{C.END}")
    print(f"{C.GRN}✓ Изменения сохранены. HEAD: {head}{C.END}")

# =============================================================================
# ОБРАБОТКА ОТВЕТА DEEPSEEK
# =============================================================================

def process_deepseek_response(response):
    """Обработать ответ DeepSeek — выполнить команды /bash, /read, /write"""
    lines = response.split('\n')
    result_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # /bash <команда>
        if line.strip().startswith('/bash '):
            cmd = line.strip()[6:]
            print(f"\n{C.BLD}{C.YLW}⚡ Выполняю: {cmd}{C.END}")
            output = execute_command(cmd)
            output_preview = output[:1500]
            if len(output) > 1500:
                output_preview += f"\n... (ещё {len(output) - 1500} символов)"
            print(f"{C.DIM}{output_preview}{C.END}")
            result_lines.append(f"[BASH] {cmd}")
            result_lines.append(f"[OUTPUT] {output[:1000]}")
        
        # /read <путь>
        elif line.strip().startswith('/read '):
            path = line.strip()[6:]
            print(f"\n{C.BLD}{C.BLU}📖 Читаю: {path}{C.END}")
            content = read_file(path)
            content_preview = content[:1000]
            if len(content) > 1000:
                content_preview += f"\n... (ещё {len(content) - 1000} символов)"
            print(f"{C.DIM}{content_preview}{C.END}")
            result_lines.append(f"[READ] {path}")
            result_lines.append(f"[CONTENT] {content[:1000]}")
        
        # /write <путь>
        elif line.strip().startswith('/write '):
            path = line.strip()[7:]
            content_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('/'):
                content_lines.append(lines[i])
                i += 1
            content = '\n'.join(content_lines)
            print(f"\n{C.BLD}{C.GRN}✏️  Пишу: {path}{C.END}")
            result = write_file(path, content)
            print(f"{C.DIM}{result}{C.END}")
            result_lines.append(f"[WRITE] {path}")
            continue
        
        else:
            result_lines.append(line)
        
        i += 1
    
    return '\n'.join(result_lines)

# =============================================================================
# ЗАГРУЗКА КОНТЕКСТА
# =============================================================================

def load_context():
    """Загрузить контекст для DeepSeek"""
    context_parts = []
    
    # 1. IRON_RULES.md
    iron_rules = read_file("IRON_RULES.md")
    if not iron_rules.startswith(f"{C.RED}"):
        context_parts.append(f"=== ЖЕЛЕЗНЫЕ ПРАВИЛА (IRON RULES) ===\n{iron_rules}")
    
    # 2. deepsick_memory.md
    memory = read_file("deepsick_memory.md")
    if not memory.startswith(f"{C.RED}"):
        context_parts.append(f"=== ПАМЯТКА (deepsick_memory) ===\n{memory}")
    
    # 3. Последние 3 урока
    lessons_result = execute_command("ls -t memory-lessons/*.md 2>/dev/null | head -3")
    if lessons_result and not lessons_result.startswith(f"{C.RED}"):
        for lesson_path in lessons_result.strip().split('\n'):
            lesson_path = lesson_path.strip()
            if lesson_path:
                lesson_content = read_file(lesson_path)
                if not lesson_content.startswith(f"{C.RED}"):
                    context_parts.append(f"=== УРОК ({lesson_path}) ===\n{lesson_content}")
    
    # 4. Список файлов
    files_list = execute_command(
        "find . -type f -not -path './.git/*' -not -path './__pycache__/*' "
        "-not -name '*.pyc' -not -name '.gitignore*' | sort | head -80"
    )
    context_parts.append(f"=== ФАЙЛЫ В РЕПОЗИТОРИИ ===\n{files_list}")
    
    return '\n\n'.join(context_parts)

# =============================================================================
# СИСТЕМНЫЙ ПРОМПТ
# =============================================================================

SYSTEM_PROMPT = """Ты — DS (DeepSeek CLI), полный аналог Cline для удалённой диагностики и ремонта роутеров OpenWrt.

ЯЗЫК ОБЩЕНИЯ:
- Пользователь говорит ПО-РУССКИ. Отвечай ему тоже по-русски.
- Понимай любые русские фразы: "синхронизируй с гитхабом", "проверь роутер", "сколько я потратил", "выйди" и т.д.
- Не жди точных команд — пользователь может выражаться как угодно, ты должен понять суть и сделать нужное действие.

Твои возможности:
1. Отвечать на вопросы пользователя о роутерах, диагностике, ремонте
2. Выполнять команды на сервере через /bash
3. Читать файлы через /read
4. Писать файлы через /write

ВАЖНЫЕ ПРАВИЛА:
- Всегда используй /bash для выполнения команд (ssh, ping, curl и т.д.)
- Для чтения файлов используй /read <путь>
- Для записи файлов используй /write <путь>
- После изменения файлов всегда делай git add + git commit + git push
- Рабочая директория: /root/router-lab (git-репозиторий, синхронизированный с GitHub)
- Если нужно подключиться к роутеру — используй ssh через Tailscale IP
- ПАРОЛЬ от всех роутеров: 56756789
- Для ssh используй sshpass: /bash sshpass -p '56756789' ssh -o StrictHostKeyChecking=no root@IP КОМАНДА
- Если пользователь просит "починить роутер" — следуй протоколу диагностики
- ВАЖНО: Если нужно узнать правила или историю — прочитай файлы через /read: IRON_RULES.md, deepsick_memory.md, memory-lessons/ (последний урок)

Формат ответа — ТОЛЬКО ЭТИ КОМАНДЫ (без markdown-разметки):
  /bash <команда>     — выполнить bash-команду
  /read <путь>        — прочитать файл
  /write <путь>       — записать файл (содержимое пиши следующими строками)

ПРИМЕР правильного ответа на вопрос "проверь роутер 00-vasin-boss (100.122.66.80)":
/read MASTER_CREDENTIALS.md
/bash ping -c 3 -W 5 100.122.66.80
/bash sshpass -p '56756789' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@100.122.66.80 "echo 'ROUTER_ACCESS_OK'; uptime; cat /proc/loadavg"

ВАЖНО: Не используй markdown-форматирование (```bash, ``` и т.д.). Используй ТОЛЬКО команды /bash, /read, /write в чистом виде, каждая на отдельной строке.

ОТВЕЧАЙ БЫСТРО. Не пиши длинных рассуждений. Сразу переходи к делу. Если пользователь просит проверить роутер — сразу делай ping и ssh, не жди дополнительных указаний."""


# =============================================================================
# ГЛАВНЫЙ ЦИКЛ
# =============================================================================

def main():
    """Главный цикл — как в Cline"""
    os.chdir(WORK_DIR)
    
    # Обработка Ctrl+C
    def signal_handler(sig, frame):
        print(f"\n{C.YLW}Прерывание...{C.END}")
        print_cost()
        git_save()
        print(f"{C.GRN}До встречи! 👋{C.END}")
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Баннер
    print_banner()
    
    # Автосинхронизация при старте
    git_sync()
    print()
    
    # Загружаем контекст
    print(f"{C.DIM}⏳ Загружаю контекст...{C.END}")
    context = load_context()
    print(f"{C.GRN}✓ Контекст загружен{C.END}")
    print()
    
    # Системный промпт + контекст
    system_message = SYSTEM_PROMPT + "\n\nВАЖНЫЙ КОНТЕКСТ ПЕРЕД НАЧАЛОМ РАБОТЫ:\n" + context
    
    messages = [
        {"role": "system", "content": system_message}
    ]
    
    # Интерактивный цикл
    while True:
        try:
            # Ввод пользователя — как в Cline
            user_input = input(f"{C.BLD}{C.CYN}DS> {C.END}").strip()
            
            if not user_input:
                continue
            
            # Обработка команд (только /команды, без русских алиасов)
            
            # /exit — выход
            if user_input == '/exit':
                print(f"\n{C.YLW}Сохраняю изменения...{C.END}")
                print_cost()
                git_save()
                print(f"{C.GRN}До встречи! 👋{C.END}")
                break
            
            # /help — помощь
            elif user_input == '/help':
                print_help()
                continue
            
            # /sync — синхронизация с GitHub
            elif user_input == '/sync':
                git_sync()
                continue
            
            # /clear — очистить экран
            elif user_input == '/clear':
                print(f"{C.CLR}", end='')
                print_banner()
                continue
            
            # /context — показать контекст
            elif user_input == '/context':
                print(f"{C.DIM}{context[:2000]}{C.END}")
                print(f"\n{C.DIM}... (контекст сокращён, всего {len(context)} символов){C.END}")
                continue
            
            # /cost — стоимость сессии
            elif user_input == '/cost':
                print_cost()
                continue
            
            # /status — статус
            elif user_input == '/status':
                result = execute_command(
                    "echo 'HEAD: $(git rev-parse HEAD | head -c 8)' && "
                    "echo '---' && git status --short | head -10"
                )
                print(result)
                continue
            
            # /bash — выполнить команду
            elif user_input.startswith('/bash '):
                cmd = user_input[6:]
                print(f"{C.YLW}⚡ {cmd}{C.END}")
                output = execute_command(cmd)
                print(f"{C.DIM}{output}{C.END}")
                continue
            
            # /read — прочитать файл
            elif user_input.startswith('/read '):
                path = user_input[6:]
                content = read_file(path)
                print(f"{C.DIM}{content}{C.END}")
                continue
            
            # /write — записать файл
            elif user_input.startswith('/write '):
                path = user_input[7:]
                print(f"{C.YLW}✏️  Введи содержимое (Ctrl+D для завершения):{C.END}")
                content_lines = []
                try:
                    while True:
                        line = input()
                        content_lines.append(line)
                except EOFError:
                    pass
                content = '\n'.join(content_lines)
                result = write_file(path, content)
                print(result)
                continue
            
            # Всё остальное — отправляем в DeepSeek (он понимает русский)
            print(f"{C.DIM}⏳ Думаю...{C.END}")
            
            # Добавляем контекст — список файлов
            files_list = execute_command(
                "find . -type f -not -path './.git/*' -not -path './__pycache__/*' "
                "-not -name '*.pyc' -not -name '.gitignore*' | sort | head -50"
            )
            
            user_message = f"""Контекст (файлы в /root/router-lab):
{files_list}

Вопрос пользователя: {user_input}

Ответь на вопрос. Если нужно выполнить команды — используй /bash, /read, /write.
После изменения файлов обязательно сделай git add + git commit + git push."""

            messages.append({"role": "user", "content": user_message})
            
            # Цикл: DeepSeek → команды → результат → DeepSeek анализирует
            max_iterations = 10
            for iteration in range(max_iterations):
                if iteration > 0:
                    print(f"{C.DIM}⏳ Анализирую результаты...{C.END}")
                
                response, usage = call_deepseek(messages, stream=True)
                
                # Обрабатываем команды из ответа
                result = process_deepseek_response(response)
                
                # Проверяем, есть ли ещё команды
                if '/bash ' not in response and '/read ' not in response and '/write ' not in response:
                    messages.append({"role": "assistant", "content": response})
                    break
                
                # Отправляем результаты обратно DeepSeek
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": f"Результаты выполнения команд:\n{result}\n\nПроанализируй результаты. Если нужно сделать ещё что-то — используй /bash, /read, /write. Если всё готово — напиши итоговый вывод."})
            
            print()
            
        except KeyboardInterrupt:
            print(f"\n{C.YLW}Прерывание...{C.END}")
            print_cost()
            git_save()
            print(f"{C.GRN}До встречи! 👋{C.END}")
            break
        
        except EOFError:
            print(f"\n{C.YLW}Сохраняю изменения...{C.END}")
            print_cost()
            git_save()
            print(f"{C.GRN}До встречи! 👋{C.END}")
            break
        
        except Exception as e:
            print(f"{C.RED}Ошибка: {e}{C.END}")

if __name__ == "__main__":
    main()
