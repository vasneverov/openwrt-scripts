#!/root/deepseek-env/bin/python3
"""
╔══════════════════════════════════════════════════════════════╗
║  DS — DeepSeek CLI для удалённой диагностики роутеров       ║
║  Запуск: ds                                                 ║
║  Аналог Cline, но через DeepSeek V4 Flash API               ║
║  Работает на PL5 (91.92.46.229)                             ║
║  Все файлы: /root/router-lab (синхронизация с GitHub)       ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import subprocess
import readline
import shutil
import re
from datetime import datetime

# =============================================================================
# КОНФИГУРАЦИЯ
# =============================================================================
DEEPSEEK_API_KEY = "sk-7253edfd69f8438ca39b911ae597ad8e"
DEEPSEEK_MODEL = "deepseek-chat"  # V4 Flash
WORK_DIR = "/root/router-lab"
HISTORY_FILE = "/root/.ds_history"
MAX_HISTORY = 50

# =============================================================================
# ЦВЕТА
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

# =============================================================================
# СИСТЕМНЫЙ ПРОМПТ (инструкция для DeepSeek)
# =============================================================================
SYSTEM_PROMPT = """Ты — DS (DeepSeek CLI), аналог Cline для удалённой диагностики и ремонта роутеров OpenWrt.

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
- ПАРОЛЬ от всех роутеров лежит в файле /root/router-lab/MASTER_CREDENTIALS.md — прочитай его через /read, если нужен пароль
- Для ssh используй sshpass: /bash sshpass -p 'ПАРОЛЬ' ssh -o StrictHostKeyChecking=no root@IP КОМАНДА
- Если пользователь просит "починить роутер" — следуй протоколу диагностики

Формат ответа — ТОЛЬКО ЭТИ КОМАНДЫ (без markdown-разметки):
  /bash <команда>     — выполнить bash-команду
  /read <путь>        — прочитать файл
  /write <путь>       — записать файл (содержимое пиши следующими строками)

ПРИМЕР:
/read MASTER_CREDENTIALS.md
/bash sshpass -p 'пароль' ssh -o StrictHostKeyChecking=no root@100.64.0.1 "cat /proc/uptime"

ВАЖНО: Не используй markdown-форматирование (```bash, ``` и т.д.). Используй ТОЛЬКО команды /bash, /read, /write в чистом виде, каждая на отдельной строке."""

# =============================================================================
# ФУНКЦИИ
# =============================================================================

def print_banner():
    """Красивый баннер"""
    tw = shutil.get_terminal_size().columns
    print(f"{C.CYN}{'═' * tw}{C.END}")
    print(f"{C.BLD}{C.CYN}  ██████╗ ███████╗    DeepSeek V4 Flash на PL5{C.END}")
    print(f"{C.CYN}  ╚════██╗██╔════╝    Модель: {DEEPSEEK_MODEL}{C.END}")
    print(f"{C.CYN}  ███████║███████╗    Папка: {WORK_DIR}{C.END}")
    print(f"{C.CYN}  ██╔══██║╚════██║    Режим: Cline-совместимый{C.END}")
    print(f"{C.CYN}  ███████║███████║    {C.END}")
    print(f"{C.CYN}  ╚══════╝╚══════╝    Команды: /help, /exit, /sync{C.END}")
    print(f"{C.CYN}{'═' * tw}{C.END}")
    print()

def print_help():
    """Помощь"""
    print(f"{C.BLD}Команды:{C.END}")
    print(f"  {C.GRN}/help{C.END}     — показать эту справку")
    print(f"  {C.GRN}/exit{C.END}     — выйти (автосохранение в GitHub)")
    print(f"  {C.GRN}/sync{C.END}     — синхронизация с GitHub")
    print(f"  {C.GRN}/status{C.END}   — статус синхронизации")
    print(f"  {C.GRN}/bash <cmd>{C.END} — выполнить bash-команду")
    print(f"  {C.GRN}/read <file>{C.END} — прочитать файл")
    print(f"  {C.GRN}/write <file>{C.END} — записать файл")
    print()
    print(f"{C.DIM}Или просто задай вопрос — я передам его DeepSeek{C.END}")
    print()

def call_deepseek(messages):
    """Вызов DeepSeek API"""
    import urllib.request
    
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    data = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "stream": False,
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
        with urllib.request.urlopen(req, timeout=180) as response:
            result = json.loads(response.read())
            content = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})
            return content, usage
    except Exception as e:
        return f"{C.RED}Ошибка API: {e}{C.END}", {}

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
            output = "(команда выполнена, код: {})".format(result.returncode)
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

def git_sync():
    """Синхронизация с GitHub"""
    print(f"{C.YLW}>>> Синхронизация с GitHub...{C.END}")
    
    # Pull
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
    
    # Проверяем, есть ли изменения
    status = subprocess.run(
        "git status --short",
        shell=True, capture_output=True, text=True, cwd=WORK_DIR
    ).stdout.strip()
    
    if not status:
        print(f"{C.DIM}Нет изменений{C.END}")
        return
    
    # Commit
    subprocess.run(
        f"git add -A 2>&1 && git commit -m 'ds: auto-save {datetime.now().strftime('%Y-%m-%d %H:%M')}' 2>&1",
        shell=True, capture_output=True, text=True, cwd=WORK_DIR
    )
    
    # Push
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
            print(f"{C.BLD}{C.YLW}⚡ Выполняю: {cmd}{C.END}")
            output = execute_command(cmd)
            print(f"{C.DIM}{output[:2000]}{C.END}")
            result_lines.append(f"[BASH] {cmd}")
            result_lines.append(f"[OUTPUT] {output[:500]}")
        
        # /read <путь>
        elif line.strip().startswith('/read '):
            path = line.strip()[6:]
            print(f"{C.BLD}{C.BLU}📖 Читаю: {path}{C.END}")
            content = read_file(path)
            print(f"{C.DIM}{content[:1000]}{C.END}")
            result_lines.append(f"[READ] {path}")
            result_lines.append(f"[CONTENT] {content[:500]}")
        
        # /write <путь>
        elif line.strip().startswith('/write '):
            path = line.strip()[7:]
            # Собираем многострочное содержимое до следующей команды
            content_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('/'):
                content_lines.append(lines[i])
                i += 1
            content = '\n'.join(content_lines)
            print(f"{C.BLD}{C.GRN}✏️  Пишу: {path}{C.END}")
            result = write_file(path, content)
            print(f"{C.DIM}{result}{C.END}")
            result_lines.append(f"[WRITE] {path}")
            continue
        
        else:
            result_lines.append(line)
        
        i += 1
    
    return '\n'.join(result_lines)

def load_context():
    """Загрузить контекст для DeepSeek: IRON_RULES, deepsick_memory, последний урок"""
    context_parts = []
    
    # 1. IRON_RULES.md
    iron_rules = read_file("IRON_RULES.md")
    if not iron_rules.startswith(f"{C.RED}"):
        context_parts.append(f"=== ЖЕЛЕЗНЫЕ ПРАВИЛА (IRON RULES) ===\n{iron_rules}")
    
    # 2. deepsick_memory.md
    memory = read_file("deepsick_memory.md")
    if not memory.startswith(f"{C.RED}"):
        context_parts.append(f"=== ПАМЯТКА (deepsick_memory) ===\n{memory}")
    
    # 3. Последний урок из memory-lessons/
    lessons = execute_command("ls -t memory-lessons/*.md 2>/dev/null | head -3")
    if lessons and not lessons.startswith(f"{C.RED}"):
        latest = lessons.split('\n')[0].strip()
        if latest:
            lesson_content = read_file(latest)
            if not lesson_content.startswith(f"{C.RED}"):
                context_parts.append(f"=== ПОСЛЕДНИЙ УРОК ({latest}) ===\n{lesson_content}")
    
    # 4. Список всех файлов в router-lab
    files_list = execute_command(
        "find . -type f -not -path './.git/*' -not -path './__pycache__/*' "
        "-not -name '*.pyc' -not -name '.gitignore*' | sort | head -80"
    )
    context_parts.append(f"=== ФАЙЛЫ В РЕПОЗИТОРИИ ===\n{files_list}")
    
    return '\n\n'.join(context_parts)

def main():
    """Главный цикл"""
    os.chdir(WORK_DIR)
    
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
    
    # История
    history = []
    
    # Системный промпт + контекст
    system_message = SYSTEM_PROMPT + "\n\nВАЖНЫЙ КОНТЕКСТ ПЕРЕД НАЧАЛОМ РАБОТЫ:\n" + context
    
    messages = [
        {"role": "system", "content": system_message}
    ]
    
    # Интерактивный цикл
    while True:
        try:
            # Ввод пользователя
            user_input = input(f"{C.BLD}{C.CYN}DS> {C.END}").strip()
            
            if not user_input:
                continue
            
            # Добавляем в историю
            history.append(user_input)
            if len(history) > MAX_HISTORY:
                history.pop(0)
            
            # Обработка команд
            if user_input == '/exit':
                print(f"\n{C.YLW}Сохраняю изменения...{C.END}")
                git_save()
                print(f"{C.GRN}До встречи! 👋{C.END}")
                break
            
            elif user_input == '/help':
                print_help()
                continue
            
            elif user_input == '/sync':
                git_sync()
                continue
            
            elif user_input == '/status':
                result = execute_command(
                    "echo 'HEAD: $(git rev-parse HEAD | head -c 8)' && "
                    "echo 'GitHub: $(git ls-remote origin main | head -c 8)' && "
                    "echo '---' && git status --short | head -10"
                )
                print(result)
                continue
            
            elif user_input.startswith('/bash '):
                cmd = user_input[6:]
                print(f"{C.YLW}⚡ {cmd}{C.END}")
                output = execute_command(cmd)
                print(f"{C.DIM}{output}{C.END}")
                continue
            
            elif user_input.startswith('/read '):
                path = user_input[6:]
                content = read_file(path)
                print(f"{C.DIM}{content}{C.END}")
                continue
            
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
            
            # Отправляем запрос в DeepSeek
            print(f"{C.DIM}⏳ Думаю...{C.END}")
            
            # Добавляем контекст — список файлов в router-lab
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
            
            # Цикл: DeepSeek → команды → результат → DeepSeek анализирует → ещё команды
            max_iterations = 10
            for iteration in range(max_iterations):
                response, usage = call_deepseek(messages)
                
                # Выводим ответ
                print(f"\n{C.BLD}{C.CYN}DeepSeek:{C.END}")
                print(f"{response}")
                
                # Обрабатываем команды из ответа
                result = process_deepseek_response(response)
                
                # Показываем использованные токены
                if usage:
                    print(f"\n{C.DIM}Tokens: {usage.get('total_tokens', '?')} | "
                          f"Prompt: {usage.get('prompt_tokens', '?')} | "
                          f"Completion: {usage.get('completion_tokens', '?')}{C.END}")
                
                # Проверяем, есть ли ещё команды в ответе
                if '/bash ' not in response and '/read ' not in response and '/write ' not in response:
                    # Нет команд — DeepSeek закончил анализ, сохраняем ответ
                    messages.append({"role": "assistant", "content": response})
                    break
                
                # Отправляем результаты выполнения команд обратно DeepSeek
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": f"Результаты выполнения команд:\n{result}\n\nПроанализируй результаты. Если нужно сделать ещё что-то — используй /bash, /read, /write. Если всё готово — напиши итоговый вывод."})
                print(f"{C.DIM}⏳ Анализирую результаты...{C.END}")
            
            print()
            
        except KeyboardInterrupt:
            print(f"\n{C.YLW}Прерывание...{C.END}")
            git_save()
            print(f"{C.GRN}До встречи! 👋{C.END}")
            break
        
        except EOFError:
            print(f"\n{C.YLW}Сохраняю изменения...{C.END}")
            git_save()
            print(f"{C.GRN}До встречи! 👋{C.END}")
            break
        
        except Exception as e:
            print(f"{C.RED}Ошибка: {e}{C.END}")

if __name__ == "__main__":
    main()
