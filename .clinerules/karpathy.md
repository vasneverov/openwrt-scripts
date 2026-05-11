100.105.51.17
## KARPATHY PRINCIPLES — ALWAYS ACTIVE

Source: `/Users/vas/.claude/KARPATHY.md`

### Core: Think Before Coding
- State assumptions. If uncertain — ask.
- If multiple interpretations — present them, don't pick silently.
- If simpler approach exists — say so. Push back.
- If unclear — stop. Name confusion. Ask.

### Core: Simplicity First
- Minimum code that solves problem. Nothing speculative.
- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" not requested.
- If 200 lines could be 50 — rewrite.

### Core: Surgical Changes
- Touch only what you must. Clean up only your own mess.
- Don't "improve" adjacent code/comments/formatting.
- Don't refactor things not broken.
- Match existing style.

### Core: Goal-Driven Execution
- **Define success criteria BEFORE starting.**
- Transform tasks into verifiable goals.
- For multi-step: state plan with verify checks.
- Strong criteria = loop independently. Weak = constant clarification.

### Integration with IRON_RULES
Before ANY router/server task — mandatory sequence:
1. **Think Before Coding** → Read relevant IRON_RULES section before first command
2. **Goal-Driven** → State aloud: "Router X will: Tailscale online ✅ + podkop green ✅ + key READY ✓✓✓"
3. **Surgical Changes** → Touch only device/file/service from task
4. **Simplicity First** → Use existing key/script/template — don't create new unless broken

### When to read IRON_RULES (BEFORE, not after)
| Action | Read section |
|--------|-------------|
| Reboot anything | RULE 1 — 5 checks before reboot |
| Install VLESS key | RULE 4 + 13 — check_vless.py READY ✓✓✓ |
| Add client to X-UI | RULE 7 — sqlite only, no API |
| New server | RULE 8 — version, port 5050, login ad/56 |
| Touch Mac network | RULE 6 — don't touch at all |

### Skill lookup
| User says | Skill |
|-----------|-------|
| "прошиваем роутер", "flash router", "прошить" | `skills/flash_router_universal.md` |
| "диагностика роутера", "router diag" | `skills/podkop_repair_guide.md` |
| "создать ключ", "clone key", "ключ-клон" | `skills/create_clone_key.md` |
| "groom routers", "причесать роутеры" | `skills/groom-routers/SKILL.md` |
| "причеши подкоп", "groom podkop", "оставить только main" | `skills/groom-podkop/SKILL.md` |
| "покажи полный отчёт по роутеру", "полный отчёт", "full report", "диагностика роутера полная" | `skills/router-full-report/SKILL.md` |
| "созови консилиум", "consilium", "созвать консилиум", "нужен консилиум" | `skills/consilium/SKILL.md` |
