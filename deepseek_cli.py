#!/usr/bin/env python3
"""DeepSeek CLI wrapper — вызывается из process.sh.
Принимает промпт через stdin, выводит ответ в stdout.
Использует DEEPSEEK_API_KEY из окружения.
"""
import os
import sys
import json
import urllib.request

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = "deepseek-chat"  # V4 Flash

if not DEEPSEEK_API_KEY:
    print('{"error": "DEEPSEEK_API_KEY not set"}', file=sys.stderr)
    sys.exit(1)

# Читаем промпт из stdin (поддерживает длинные промпты)
prompt = sys.stdin.read()

if not prompt.strip():
    print('{"error": "No prompt provided"}', file=sys.stderr)
    sys.exit(1)

url = "https://api.deepseek.com/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
}

data = {
    "model": DEEPSEEK_MODEL,
    "messages": [
        {"role": "system", "content": "You are an AI assistant that processes daily journal entries. Always respond with exactly the JSON or HTML requested. No explanations."},
        {"role": "user", "content": prompt}
    ],
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
    with urllib.request.urlopen(req, timeout=300) as response:
        result = json.loads(response.read())
        content = result["choices"][0]["message"]["content"]
        print(content)
        sys.exit(0)
except urllib.error.HTTPError as e:
    error_body = e.read().decode() if e.fp else str(e)
    print(f'{{"error": "HTTP {e.code}: {error_body}"}}', file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f'{{"error": "{e}"}}', file=sys.stderr)
    sys.exit(1)
