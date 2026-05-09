#!/bin/bash
# Собирает красивый DMG с маленьким белым окном
set -e

APP="SNI Scanner.app"
VOL="SNI Scanner"
DMG_OUT="SNI Scanner.dmg"
TMP_DMG="/tmp/sni_tmp.dmg"
STAGE="/tmp/sni_stage"

cd "$(dirname "$0")"

echo "→ Подготовка..."
rm -rf "$STAGE" "$TMP_DMG"
mkdir "$STAGE"
cp -r "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"

echo "→ Создаю rw-образ..."
hdiutil create -volname "$VOL" -srcfolder "$STAGE" \
  -ov -format UDRW -fs HFS+ "$TMP_DMG" > /dev/null

rm -rf "$STAGE"

echo "→ Монтирую..."
MOUNT_OUT=$(hdiutil attach -readwrite -noverify -noautoopen "$TMP_DMG")
# Берём путь к тому из последней строки с /Volumes/
VOL_PATH=$(echo "$MOUNT_OUT" | grep '/Volumes/' | sed 's/.*\/Volumes\//\/Volumes\//')
DISK_DEV=$(echo "$MOUNT_OUT" | grep '/Volumes/' | awk '{print $1}')
echo "   Том: $VOL_PATH (устройство: $DISK_DEV)"

sleep 2

echo "→ Настраиваю окно через Finder..."
osascript <<APPLESCRIPT
tell application "Finder"
    tell disk "$VOL"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set bounds of container window to {200, 140, 670, 370}
        set theViewOptions to icon view options of container window
        set arrangement of theViewOptions to not arranged
        set icon size of theViewOptions to 100
        set background color of theViewOptions to {65535, 65535, 65535}
        set position of item "$APP" of container window to {140, 120}
        set position of item "Applications" of container window to {330, 120}
        update without registering applications
        delay 3
        close
    end tell
end tell
APPLESCRIPT

echo "→ Жду сохранения DS_Store..."
sleep 4

# Синхронизируем
sync

echo "→ Отмонтирую..."
hdiutil detach "$DISK_DEV" > /dev/null

echo "→ Конвертирую в сжатый read-only..."
rm -f "$DMG_OUT"
hdiutil convert "$TMP_DMG" -format UDZO \
  -imagekey zlib-level=9 -o "$DMG_OUT" > /dev/null
rm -f "$TMP_DMG"

SIZE=$(du -h "$DMG_OUT" | cut -f1)
echo "✅  Готово: $DMG_OUT ($SIZE)"
