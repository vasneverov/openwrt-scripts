## DeepSeek 3-phase pipeline restored after server reboot

**Date:** 2026-05-12
**Server:** 144.31.244.181 (d-brain)

### Problem
Server rebooted. All uncommitted changes lost. Bot reverted to original Claude Code single-phase processing.

### Root cause
- Git had only original commits (2c745b5, d8fe67c, etc.)
- All DeepSeek changes were uncommitted → lost on reboot
- Two code paths exist: `/home/sbrain/sbrain/` (active, user=sbrain) and `/root/sbrain/` (stale copy)

### What was restored
1. **deepseek_cli.py** → `/home/sbrain/sbrain/scripts/deepseek_cli.py` (DeepSeek API wrapper)
2. **processor.py** → `DeepSeekProcessor` class with 3-phase pipeline:
   - Phase 1: CAPTURE — classify entries → JSON
   - Phase 2: EXECUTE — process entries (save/archive/task)
   - Phase 3: REFLECT — generate HTML report
3. **process.py** (bot handler) → 3-phase with progress messages

### Files changed
- `/home/sbrain/sbrain/scripts/deepseek_cli.py` — new (DeepSeek CLI wrapper)
- `/home/sbrain/sbrain/src/d_brain/services/processor.py` — rewritten (DeepSeekProcessor)
- `/home/sbrain/sbrain/src/d_brain/bot/handlers/process.py` — rewritten (3-phase handler)
- `/root/sbrain/src/d_brain/services/processor.py` — synced copy
- `/root/sbrain/src/d_brain/bot/handlers/process.py` — synced copy

### Lesson
- **Always commit DeepSeek changes to git** — they survive reboot
- Both paths must be updated: `/home/sbrain/sbrain/` (active) and `/root/sbrain/` (stale)
- DEEPSEEK_API_KEY is in `/home/sbrain/sbrain/.env` — survived reboot
- Bot runs as user `sbrain`, WorkingDirectory `/home/sbrain/sbrain`
