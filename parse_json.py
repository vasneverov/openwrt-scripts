#!/usr/bin/env python3
"""Depth-based JSON parser — extracts first valid JSON object from mixed text.
Replaces grep -o '{.*}' which fails on multi-line JSON.
"""
import sys
import json


def parse_json(text: str) -> str:
    """Find first valid JSON object using {/} depth counting."""
    start = text.find('{')
    if start == -1:
        # No JSON found — return as-is
        return text.strip()

    depth = 0
    in_string = False
    escape = False

    for i in range(start, len(text)):
        ch = text[i]

        if escape:
            escape = False
            continue

        if ch == '\\':
            escape = True
            continue

        if ch == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                candidate = text[start:i + 1]
                try:
                    parsed = json.loads(candidate)
                    return json.dumps(parsed, ensure_ascii=False)
                except json.JSONDecodeError:
                    # Try next '{' after this failed candidate
                    next_start = text.find('{', start + 1)
                    if next_start == -1:
                        return text.strip()
                    start = next_start
                    depth = 0
                    continue

    # No complete JSON object found
    return text.strip()


def main():
    text = sys.stdin.read()
    result = parse_json(text)
    print(result)


if __name__ == "__main__":
    main()
