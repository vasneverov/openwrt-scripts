#!/usr/bin/env python3
"""
Создаёт SNI Scanner.app для macOS.
Запусти один раз: python3 make-app.py
Результат: SNI Scanner.app в текущей папке — перетащи в /Applications или Dock.
"""

import os, sys, subprocess, shutil, plistlib, stat, struct, zlib, math

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
APP_NAME = "SNI Scanner"
APP_PATH = os.path.join(THIS_DIR, f"{APP_NAME}.app")

# ── 1. Читаем исходный код GUI-приложения ──────────────────────────────────
SRC = os.path.join(THIS_DIR, "sni-scanner-app.py")
if not os.path.exists(SRC):
    print(f"Ошибка: не найден {SRC}")
    sys.exit(1)
app_code = open(SRC, encoding="utf-8").read()


# ── 2. Создаём PNG-иконку без сторонних зависимостей ──────────────────────
def write_png(filename, width, height, pixels_rgb):
    """Записывает RGB-пиксели в PNG-файл (чистый Python)."""
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    raw = b""
    for y in range(height):
        raw += b"\x00"
        for x in range(width):
            r, g, b = pixels_rgb[y * width + x]
            raw += bytes([r, g, b])

    png  = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")

    with open(filename, "wb") as f:
        f.write(png)


def make_icon_pixels(size):
    """Рисует иконку: тёмный фон + фиолетовый круг + лупа + «SNI»."""
    BG     = (22,  22,  36)
    CARD   = (42,  42,  66)
    PURPLE = (124, 58, 237)
    LITE   = (205, 214, 244)
    WHITE  = (255, 255, 255)

    px = [BG] * (size * size)

    def blend(c1, c2, t):
        t = max(0.0, min(1.0, t))
        return (int(c1[0]*(1-t)+c2[0]*t),
                int(c1[1]*(1-t)+c2[1]*t),
                int(c1[2]*(1-t)+c2[2]*t))

    def setpx(x, y, color, aa=1.0):
        if 0 <= x < size and 0 <= y < size:
            idx = y * size + x
            px[idx] = blend(px[idx], color, aa)

    def circle(cx, cy, r, color, thick=None):
        ir = int(r) + 2
        for dy in range(-ir, ir+1):
            for dx in range(-ir, ir+1):
                d = math.sqrt(dx*dx + dy*dy)
                if thick is None:          # filled
                    aa = max(0.0, min(1.0, r - d + 1.0))
                else:                      # ring
                    aa = max(0.0, min(1.0, 1.0 - abs(d - r) + thick * 0.5))
                    aa = min(aa, 1.0)
                if aa > 0:
                    setpx(int(cx)+dx, int(cy)+dy, color, aa)

    def line(x0, y0, x1, y1, color, thick=3):
        dx, dy = x1-x0, y1-y0
        length = math.sqrt(dx*dx + dy*dy)
        if length == 0:
            return
        nx, ny = -dy/length, dx/length
        steps = int(length * 2) + 1
        for i in range(steps):
            t = i / max(steps-1, 1)
            cx = x0 + dx*t
            cy = y0 + dy*t
            for w in range(-thick, thick+1):
                setpx(int(cx + nx*w), int(cy + ny*w), color, 1.0)

    s = size

    # Фон — скруглённый прямоугольник
    pad = s * 0.07
    for y in range(s):
        for x in range(s):
            cx, cy = s/2, s/2
            rx, ry = abs(x - cx), abs(y - cy)
            r_corner = s * 0.22
            in_rect = rx < s/2 - pad and ry < s/2 - pad
            in_corner = (rx > s/2 - pad - r_corner and ry > s/2 - pad - r_corner)
            if in_rect and not in_corner:
                px[y * s + x] = CARD
            elif in_corner:
                dist = math.sqrt((rx - (s/2 - pad - r_corner))**2 +
                                 (ry - (s/2 - pad - r_corner))**2)
                aa = max(0.0, min(1.0, r_corner - dist + 1.0))
                if aa > 0:
                    px[y * s + x] = blend(BG, CARD, aa)

    # Фиолетовый круг-фон для лупы
    circle(s*0.46, s*0.45, s*0.30, PURPLE)

    # Лупа: кольцо + ручка
    mg_r  = s * 0.155
    mg_cx = s * 0.42
    mg_cy = s * 0.41
    circle(mg_cx, mg_cy, mg_r,      WHITE, thick=s*0.055)  # кольцо
    # Ручка (линия под углом 45°)
    hlen = s * 0.16
    ang  = math.radians(135)
    hx0  = mg_cx + mg_r * math.cos(ang)
    hy0  = mg_cy + mg_r * math.sin(ang)
    hx1  = hx0 + hlen * math.cos(ang)
    hy1  = hy0 + hlen * math.sin(ang)
    line(int(hx0), int(hy0), int(hx1), int(hy1), WHITE, thick=max(2, int(s*0.033)))

    # Текст "SNI" — рисуем геометрически (пиксельные буквы, масштабируемые)
    def draw_letter_S(ox, oy, sc):
        w, h, t = int(sc*5), int(sc*7), max(1, int(sc*1.2))
        for i in range(w):
            setpx(ox+i, oy,     WHITE)
            setpx(ox+i, oy+h//2, WHITE)
            setpx(ox+i, oy+h,   WHITE)
        for i in range(h//2+1):
            setpx(ox,   oy+i,   WHITE)
        for i in range(h//2, h+1):
            setpx(ox+w, oy+i,   WHITE)

    def draw_letter_N(ox, oy, sc):
        w, h = int(sc*5), int(sc*7)
        for i in range(h+1):
            setpx(ox,   oy+i, WHITE)
            setpx(ox+w, oy+i, WHITE)
        for i in range(h+1):
            diag_x = ox + int(w * i / h)
            setpx(diag_x, oy+i, WHITE)

    def draw_letter_I(ox, oy, sc):
        w, h = int(sc*5), int(sc*7)
        cx = ox + w//2
        for i in range(h+1):
            setpx(cx, oy+i, WHITE)
        for i in range(w+1):
            setpx(ox+i, oy,   WHITE)
            setpx(ox+i, oy+h, WHITE)

    sc   = s / 100.0
    lw   = int(sc * 6)   # ширина буквы
    gap  = int(sc * 2)   # зазор
    total_w = 3 * lw + 2 * gap
    tx   = int(s/2 - total_w/2)
    ty   = int(s * 0.73)

    draw_letter_S(tx,             ty, sc)
    draw_letter_N(tx + lw + gap,  ty, sc)
    draw_letter_I(tx + 2*(lw+gap),ty, sc)

    return px


def create_icns(output_path):
    """Создаёт .icns из набора PNG разных размеров."""
    iconset_dir = output_path + ".iconset"
    os.makedirs(iconset_dir, exist_ok=True)

    sizes = [16, 32, 64, 128, 256, 512]
    for sz in sizes:
        px = make_icon_pixels(sz)
        write_png(os.path.join(iconset_dir, f"icon_{sz}x{sz}.png"), sz, sz, px)
        if sz <= 512:
            px2 = make_icon_pixels(sz * 2)
            write_png(os.path.join(iconset_dir, f"icon_{sz}x{sz}@2x.png"), sz*2, sz*2, px2)

    result = subprocess.run(
        ["iconutil", "-c", "icns", iconset_dir, "-o", output_path],
        capture_output=True
    )
    shutil.rmtree(iconset_dir)
    return result.returncode == 0


# ── 3. Собираем .app bundle ────────────────────────────────────────────────
def build_app():
    # Удаляем старый bundle, если есть
    if os.path.exists(APP_PATH):
        shutil.rmtree(APP_PATH)

    macos_dir     = os.path.join(APP_PATH, "Contents", "MacOS")
    resources_dir = os.path.join(APP_PATH, "Contents", "Resources")
    os.makedirs(macos_dir,     exist_ok=True)
    os.makedirs(resources_dir, exist_ok=True)

    # Info.plist
    plist = {
        "CFBundleName":                  APP_NAME,
        "CFBundleDisplayName":           APP_NAME,
        "CFBundleIdentifier":            "su.vas.sni-scanner",
        "CFBundleVersion":               "1.0.0",
        "CFBundleShortVersionString":    "1.0",
        "CFBundleExecutable":            "launcher",
        "CFBundleIconFile":              "AppIcon",
        "NSHighResolutionCapable":       True,
        "LSMinimumSystemVersion":        "10.14",
        "CFBundlePackageType":           "APPL",
        # Принудительно светлый режим — без этого dark mode ломает tkinter
        "NSRequiresAquaSystemAppearance": True,
    }
    with open(os.path.join(APP_PATH, "Contents", "Info.plist"), "wb") as f:
        plistlib.dump(plist, f)

    # Копируем Python-скрипт в ресурсы
    dest_py = os.path.join(resources_dir, "sni_scanner.py")
    with open(dest_py, "w", encoding="utf-8") as f:
        f.write(app_code)

    # Лаунчер (shell-скрипт в MacOS/)
    python_bin = sys.executable
    launcher_path = os.path.join(macos_dir, "launcher")
    launcher_code = f"""#!/bin/bash
SCRIPT="$(dirname "$0")/../Resources/sni_scanner.py"
exec "{python_bin}" "$SCRIPT"
"""
    with open(launcher_path, "w") as f:
        f.write(launcher_code)
    os.chmod(launcher_path, os.stat(launcher_path).st_mode
             | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # Иконка
    print("Создаю иконку...", end=" ", flush=True)
    icns_path = os.path.join(resources_dir, "AppIcon.icns")
    if create_icns(icns_path):
        print("✓")
    else:
        print("⚠ iconutil не сработал, иконка по умолчанию")

    # Говорим macOS обновить кеш иконок
    subprocess.run(["touch", APP_PATH], capture_output=True)
    subprocess.run(["killall", "Dock"], capture_output=True)

    return APP_PATH


def build_dmg(app_path, out_dmg):
    """Создаёт стандартный macOS DMG с маленьким окном (как у нормальных приложений)."""
    import tempfile, time

    stage = tempfile.mkdtemp(prefix="sni_dmg_")
    try:
        shutil.copytree(app_path, os.path.join(stage, f"{APP_NAME}.app"),
                        symlinks=True)
        os.symlink("/Applications", os.path.join(stage, "Applications"))

        # Временный rw-образ
        tmp_dmg = out_dmg.replace(".dmg", "_tmp.dmg")
        subprocess.run([
            "hdiutil", "create",
            "-volname", APP_NAME,
            "-srcfolder", stage,
            "-ov", "-format", "UDRW",
            "-fs", "HFS+",
            tmp_dmg
        ], capture_output=True, check=True)
    finally:
        shutil.rmtree(stage)

    # Монтируем и настраиваем окно через AppleScript
    mount = subprocess.run(
        ["hdiutil", "attach", "-readwrite", "-noverify", "-noautoopen", tmp_dmg],
        capture_output=True, text=True
    )
    vol = next((l.split()[-1] for l in mount.stdout.splitlines() if "/Volumes/" in l), None)

    if vol:
        time.sleep(1)
        applescript = f"""
tell application "Finder"
    tell disk "{APP_NAME}"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set bounds of container window to {{200, 120, 680, 380}}
        set theViewOptions to icon view options of container window
        set arrangement of theViewOptions to not arranged
        set icon size of theViewOptions to 96
        set background color of theViewOptions to {{61166, 61166, 61166}}
        set position of item "{APP_NAME}.app" of container window to {{140, 130}}
        set position of item "Applications" of container window to {{340, 130}}
        close
        open
        update without registering applications
        delay 2
        close
    end tell
end tell
"""
        subprocess.run(["osascript", "-e", applescript], capture_output=True)
        time.sleep(2)
        subprocess.run(["hdiutil", "detach", vol], capture_output=True)

    # Конвертируем в сжатый read-only
    if os.path.exists(out_dmg):
        os.remove(out_dmg)
    subprocess.run([
        "hdiutil", "convert", tmp_dmg,
        "-format", "UDZO", "-imagekey", "zlib-level=9",
        "-o", out_dmg
    ], capture_output=True)
    os.remove(tmp_dmg)
    return os.path.exists(out_dmg)


# ── Main ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Собираю {APP_NAME}.app...")
    path = build_app()
    print(f"✅  App: {path}")

    dmg_path = os.path.join(THIS_DIR, f"{APP_NAME}.dmg")
    print(f"Собираю DMG...", end=" ", flush=True)
    if build_dmg(path, dmg_path):
        size = os.path.getsize(dmg_path) // 1024
        print(f"✅  {dmg_path} ({size} КБ)")
    else:
        print("⚠ DMG не собрался")

    print(f"\nГотово. Открой DMG → перетащи в Applications → в Dock.")
    subprocess.run(["open", THIS_DIR])
