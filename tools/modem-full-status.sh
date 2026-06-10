#!/bin/sh
S=$(curl -s --max-time 5 http://192.168.8.1/api/webserver/SesTokInfo 2>/dev/null)
SID=$(echo "$S" | sed -n 's/.*SessionID=\([^<]*\)<.*/\1/p')
TOK=$(echo "$S" | sed -n 's/.*<TokInfo>\([^<]*\)<.*/\1/p')
H="Cookie: SessionID=$SID"
V="__RequestVerificationToken: $TOK"

M=$(curl -s --max-time 5 http://192.168.8.1/api/monitoring/status -H "$H" -H "$V" 2>/dev/null)
sleep 1
D=$(curl -s --max-time 5 http://192.168.8.1/api/device/information -H "$H" -H "$V" 2>/dev/null)
sleep 1
P=$(curl -s --max-time 5 http://192.168.8.1/api/net/current-plmn -H "$H" -H "$V" 2>/dev/null)
sleep 1
F=$(curl -s --max-time 5 http://192.168.8.1/api/security/firewall-switch -H "$H" -H "$V" 2>/dev/null)
sleep 1
R=$(curl -s --max-time 5 http://192.168.8.1/api/monitoring/traffic-statistics -H "$H" -H "$V" 2>/dev/null)
sleep 1
A=$(curl -s --max-time 5 http://192.168.8.1/api/dialup/profiles -H "$H" -H "$V" 2>/dev/null)
sleep 1
Q=$(curl -s --max-time 5 http://192.168.8.1/api/device/signal -H "$H" -H "$V" 2>/dev/null)

SG=$(echo "$M" | sed -n 's/.*<SignalIcon>\([^<]*\)<.*/\1/p')
OP=$(echo "$P" | sed -n 's/.*<FullName>\([^<]*\)<.*/\1/p')
IP=$(echo "$M" | sed -n 's/.*<WanIPAddress>\([^<]*\)<.*/\1/p')
ST=$(echo "$M" | sed -n 's/.*<ConnectionStatus>\([^<]*\)<.*/\1/p')
DR=$(echo "$R" | sed -n 's/.*<CurrentDownloadRate>\([^<]*\)<.*/\1/p')
UR=$(echo "$R" | sed -n 's/.*<CurrentUploadRate>\([^<]*\)<.*/\1/p')
FW=$(echo "$F" | sed -n 's/.*<FirewallMainSwitch>\([^<]*\)<.*/\1/p')
MD=$(echo "$D" | sed -n 's/.*<DeviceName>\([^<]*\)<.*/\1/p')
FV=$(echo "$D" | sed -n 's/.*<SoftwareVersion>\([^<]*\)<.*/\1/p')
IM=$(echo "$D" | sed -n 's/.*<Imei>\([^<]*\)<.*/\1/p')
MS=$(echo "$D" | sed -n 's/.*<Msisdn>\([^<]*\)<.*/\1/p')
AP=$(echo "$A" | sed -n 's/.*<ApnName>\([^<]*\)<.*/\1/p')
TD=$(echo "$R" | sed -n 's/.*<TotalDownload>\([^<]*\)<.*/\1/p')
TU=$(echo "$R" | sed -n 's/.*<TotalUpload>\([^<]*\)<.*/\1/p')
CT=$(echo "$R" | sed -n 's/.*<CurrentConnectTime>\([^<]*\)<.*/\1/p')

RSRP=$(echo "$Q" | sed -n 's/.*<rsrp>\(-\?[0-9]*\).*/\1/p')
RSRQ=$(echo "$Q" | sed -n 's/.*<rsrq>\(-\?[0-9]*\).*/\1/p')
RSSI=$(echo "$Q" | sed -n 's/.*<rssi>\(-\?[0-9]*\).*/\1/p')
SINR=$(echo "$Q" | sed -n 's/.*<sinr>\(-\?[0-9]*\).*/\1/p')
PCI=$(echo "$Q" | sed -n 's/.*<pci>\([^<]*\)<.*/\1/p')
CELL=$(echo "$Q" | sed -n 's/.*<cell_id>\([^<]*\)<.*/\1/p')

echo "$M" | grep -q 'CurrentNetworkTypeEx>101<' && NN='4G LTE' || NN='?'

echo "{\"s\":\"${SG:-0}\",\"o\":\"${OP:-?}\",\"n\":\"$NN\",\"i\":\"${IP:-?}\",\"dr\":\"${DR:-0}\",\"ur\":\"${UR:-0}\",\"st\":\"${ST:-0}\",\"fw\":\"${FW:-1}\",\"md\":\"${MD:-?}\",\"fv\":\"${FV:-?}\",\"im\":\"${IM:-?}\",\"ms\":\"${MS:-?}\",\"ap\":\"${AP:-?}\",\"td\":\"${TD:-0}\",\"tu\":\"${TU:-0}\",\"ct\":\"${CT:-0}\",\"rsrp\":\"${RSRP:-?}\",\"rsrq\":\"${RSRQ:-?}\",\"rssi\":\"${RSSI:-?}\",\"sinr\":\"${SINR:-?}\",\"pci\":\"${PCI:-?}\",\"cell_id\":\"${CELL:-?}\"}" > /tmp/modem_status.json
