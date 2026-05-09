#!/bin/sh
# podkop-fw4-fix.sh — фикс для podkop на OpenWrt 25.12 (fw4/nftables)
#
# ПРОБЛЕМА:
# На OpenWrt 25.12 (ядро 6.12, fw4/nftables) таблица inet PodkopTable
# с hook prerouting НЕ ВИДИТ forwarded трафик (с клиентов WiFi/LAN).
# Это известное ограничение: inet таблицы с prerouting видят только local трафик.
#
# Forwarded трафик видят:
#   - ip/ip6 таблицы с hook prerouting
#   - inet таблицы с hook forward
#
# РЕШЕНИЕ:
# Добавляем правила маркировки в inet fw4 mangle_forward (hook forward),
# который гарантированно видит forwarded трафик.
#
# Установка:
#   cat tools/podkop-fw4-fix.sh | ssh root@ROUTER_IP "cat > /root/podkop-fw4-fix.sh && chmod +x /root/podkop-fw4-fix.sh"
#   ssh root@ROUTER_IP "/root/podkop-fw4-fix.sh install"
#
# После обновления podkop листов:
#   /root/podkop-fw4-fix.sh update

PODKOP_TABLE="inet PodkopTable"
PODKOP_SET="podkop_subnets"
FW4_TABLE="inet fw4"
FW4_CHAIN="mangle_forward"
FW4_SET="podkop_subnets_fwd"
INTERFACE="br-lan"
MARK="0x00100000"

log() {
    echo "[podkop-fw4-fix] $1"
    logger -t podkop-fw4-fix "$1"
}

install_service() {
    cat > /etc/init.d/podkop-fw4-fix << 'INITEOF'
#!/bin/sh /etc/rc.common

START=99
STOP=

boot() {
    /root/podkop-fw4-fix.sh update
}

start() {
    /root/podkop-fw4-fix.sh update
}

reload() {
    /root/podkop-fw4-fix.sh update
}
INITEOF
    chmod +x /etc/init.d/podkop-fw4-fix
    /etc/init.d/podkop-fw4-fix enable
    log "init.d script installed and enabled"
}

update() {
    log "Updating mark rules in $FW4_TABLE $FW4_CHAIN..."

    # 1. Create set in inet fw4 if not exists
    nft add set $FW4_TABLE $FW4_SET '{ type ipv4_addr; flags interval; auto-merge; }' 2>/dev/null || true

    # 2. Flush old elements from set
    nft flush set $FW4_TABLE $FW4_SET 2>/dev/null || true

    # 3. Copy elements from inet PodkopTable podkop_subnets
    ELEMENTS=$(nft list set $PODKOP_TABLE $PODKOP_SET 2>/dev/null | \
        tr "\n" " " | \
        sed 's/.*elements = {/{/' | \
        sed 's/}.*/}/')
    if [ -n "$ELEMENTS" ] && [ "$ELEMENTS" != "{}" ]; then
        nft add element $FW4_TABLE $FW4_SET "$ELEMENTS" 2>/dev/null
        COUNT=$(echo "$ELEMENTS" | grep -o ',' | wc -l)
        COUNT=$((COUNT + 1))
        log "Copied $COUNT elements to $FW4_TABLE $FW4_SET"
    else
        log "WARNING: could not get elements from $PODKOP_TABLE $PODKOP_SET"
    fi

    # 4. Delete old rules from inet fw4 mangle_forward (by handle)
    RULES=$(nft -a list chain $FW4_TABLE $FW4_CHAIN 2>/dev/null | grep 'podkop-fw4-fix' | grep -o 'handle [0-9]*' | awk '{print $2}')
    for handle in $RULES; do
        nft delete rule $FW4_TABLE $FW4_CHAIN handle $handle 2>/dev/null || true
    done

    # 5. Add new mark rules in mangle_forward (hook forward — видит forwarded трафик)
    nft add rule $FW4_TABLE $FW4_CHAIN \
        iifname "$INTERFACE" ip daddr @$FW4_SET meta l4proto tcp \
        meta mark set $MARK counter \
        comment "podkop-fw4-fix-forward-tcp"

    nft add rule $FW4_TABLE $FW4_CHAIN \
        iifname "$INTERFACE" ip daddr @$FW4_SET meta l4proto udp \
        meta mark set $MARK counter \
        comment "podkop-fw4-fix-forward-udp"

    nft add rule $FW4_TABLE $FW4_CHAIN \
        iifname "$INTERFACE" ip daddr 198.18.0.0/15 meta l4proto tcp \
        meta mark set $MARK counter \
        comment "podkop-fw4-fix-forward-fakeip-tcp"

    nft add rule $FW4_TABLE $FW4_CHAIN \
        iifname "$INTERFACE" ip daddr 198.18.0.0/15 meta l4proto udp \
        meta mark set $MARK counter \
        comment "podkop-fw4-fix-forward-fakeip-udp"

    log "Mark rules updated in $FW4_TABLE $FW4_CHAIN"
    nft list chain $FW4_TABLE $FW4_CHAIN 2>/dev/null | grep 'podkop-fw4-fix'
}

case "${1:-}" in
    install)
        log "Installing podkop-fw4-fix..."
        update
        install_service
        log "Installation complete"
        ;;
    update)
        update
        ;;
    remove)
        log "Removing podkop-fw4-fix..."
        /etc/init.d/podkop-fw4-fix disable 2>/dev/null || true
        rm -f /etc/init.d/podkop-fw4-fix
        RULES=$(nft -a list chain $FW4_TABLE $FW4_CHAIN 2>/dev/null | grep 'podkop-fw4-fix' | grep -o 'handle [0-9]*' | awk '{print $2}')
        for handle in $RULES; do
            nft delete rule $FW4_TABLE $FW4_CHAIN handle $handle 2>/dev/null || true
        done
        nft delete set $FW4_TABLE $FW4_SET 2>/dev/null || true
        log "Removal complete"
        ;;
    *)
        echo "Usage: $0 {install|update|remove}"
        echo ""
        echo "  install - install fix and init.d script"
        echo "  update  - update mark rules (after podkop list update)"
        echo "  remove  - remove fix"
        ;;
esac
