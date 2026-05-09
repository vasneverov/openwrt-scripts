# Автозапуск Claude Code в VS Code

Добавь в конец файла `~/.zshrc` следующие строки:

```bash
# Открывать VS Code в рабочей папке (замени CLAUDECODE на свою папку)
alias code='command code ~/CLAUDECODE'

# Авто-запуск Claude Code в терминале VS Code
if [[ "$TERM_PROGRAM" == "vscode" ]]; then
  rm -f /tmp/claude_auth_status_cache
  claude
fi
```

Затем перезапусти терминал или выполни:

```bash
source ~/.zshrc
```

---

**Что это даёт:**

- `code` в терминале — открывает VS Code сразу в рабочей папке `~/CLAUDECODE`
- При каждом открытии терминала внутри VS Code — автоматически запускается `claude`
- `rm -f /tmp/claude_auth_status_cache` — сбрасывает кеш авторизации, чтобы статусная строка сразу показала актуальный логин
