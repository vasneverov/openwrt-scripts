#!/usr/bin/env python3
"""
Port Scanner для bMSK / bSPB
Сканирует, какие порты пропускают российские провайдеры.
Проверяет: TCP connect + VLESS+Reality handshake.

Идея: DPI блокирует известные порты (443, 993, 5223, 5228, 8443, 8853, 8880 и т.д.)
Нужно найти порты, которые:
  - Ниже 1024 (well-known, системные) — выглядят как легитимные сервисы
  - Высокие (50000+) — DPI может не проверять
  - Нестандартные средние (например, 3478, 5349, 6514 и т.д.)

Запуск:
  python3 port_scanner.py bMSK          # сканировать bMSK (159.194.198.172)
  python3 port_scanner.py bSPB          # сканировать bSPB (5.35.84.151)
  python3 port_scanner.py bMSK --quick  # только перспективные порты
  python3 port_scanner.py bMSK --range 10000-20000  # свой диапазон
"""

import socket
import sys
import time
import concurrent.futures
from datetime import datetime

# ─── Серверы ────────────────────────────────────────────────────────────────

SERVERS = {
    "bMSK": {"ip": "159.194.198.172", "name": "bMSK (Москва)"},
    "bSPB": {"ip": "5.35.84.151",    "name": "bSPB (Питер)"},
}

# ─── Перспективные порты для быстрой проверки ──────────────────────────────
# Идея: порты, которые выглядят как легитимные сервисы, но не входят
# в стандартный блок-лист DPI

QUICK_PORTS = [
    # Системные/well-known (1-1023) — выглядят как настоящие сервисы
    7,    # Echo
    9,    # Discard
    13,   # Daytime
    17,   # QOTD
    19,   # Chargen
    37,   # Time
    53,   # DNS (TCP)
    67,   # DHCP
    68,   # DHCP
    69,   # TFTP
    70,   # Gopher
    79,   # Finger
    81,   # Hosts2-ns
    88,   # Kerberos
    90,   # dnsix
    101,  # HOSTNAME
    102,  # ISO-TSAP
    105,  # CSO
    106,  # 3COM-TSMUX
    107,  # RTELNET
    109,  # POP2
    110,  # POP3 (plain)
    111,  # SunRPC
    113,  # Ident/Auth
    115,  # SFTP
    117,  # UUCP-PATH
    118,  # SQL Services
    119,  # NNTP (Usenet)
    123,  # NTP
    135,  # EPMAP / RPC
    137,  # NetBIOS-ns
    138,  # NetBIOS-dgm
    139,  # NetBIOS-ssn
    143,  # IMAP (plain)
    144,  # UMA
    156,  # SQLSRV
    158,  # DMSP
    161,  # SNMP
    162,  # SNMP Trap
    177,  # XDMCP
    179,  # BGP
    194,  # IRC
    199,  # SMUX
    201,  # AppleTalk
    209,  # QMTP
    210,  # ANSI-Z39.50
    213,  # IPX
    220,  # IMAP3
    259,  # ESRO
    264,  # BGMP
    311,  # Apple Admin
    318,  # PKIX TSP
    323,  # RP
    366,  # ODMR
    369,  # RPC2
    370,  # codaauth2
    371,  # ClearCase
    383,  # HP OpenView
    384,  # ARNS
    387,  # AURP
    389,  # LDAP
    401,  # UPS
    402,  # Genie
    406,  # IMSP
    407,  # Timbuktu
    408,  # Prospero
    409,  # PRM
    410,  # DECODE
    411,  # Direct Connect
    412,  # Direct Connect+
    413,  # SMSP
    414,  # InfoSeek
    415,  # BNet
    416,  # Silverplatter
    417,  # Onmux
    418,  # Hyper-G
    419,  # Ariel
    420,  # SMPTE
    421,  # Ariel2
    422,  # Ariel3
    423,  # OPC
    424,  # OPC2
    425,  # ICAD
    426,  # smartsdp
    427,  # SLP
    428,  # OPS
    429,  # OPS2
    430,  # OPS3
    431,  # OPS4
    432,  # OPS5
    433,  # NNSP
    434,  # MobileIP
    435,  # MobileIP2
    436,  # DNA-CML
    437,  # comscm
    438,  # DSFGW
    439,  # DASP
    440,  # SGCP
    441,  # DECVMS-SYSMGT
    442,  # CVC HostD
    444,  # SNPP
    445,  # Microsoft-DS (SMB)
    446,  # DDM-RDB
    447,  # DDM-DFM
    448,  # DDM-SSL
    449,  # AS Server Mapper
    450,  # TServer
    451,  # SFS SMP
    452,  # SFS Config
    453,  # Creativeserver
    454,  # Contentserver
    455,  # Creativepartnr
    456,  # MACON-TCP
    457,  # SCOHELP
    458,  # Apple QuickTime
    459,  # ampr-rcmd
    460,  # skronk
    461,  # DATASURFSRV
    462,  # DATASURFSRVSEC
    463,  # alpes
    464,  # kpasswd
    465,  # SMTPS (URL Rendezvous)
    466,  # digital-vrc
    467,  # mylex-mapd
    468,  # proturis
    469,  # RCAP
    470,  # scx-proxy
    471,  # mondex
    472,  # ljk-login
    473,  # hybrid-pop
    474,  # tn-tl-w1
    475,  # tcpnethaspsrv
    476,  # tn-tl-fd1
    477,  # ss7ns
    478,  # spsc
    479,  # iafserver
    480,  # iafdbase
    481,  # ph
    482,  # bgs-nsi
    483,  # ulpnet
    484,  # integra-sme
    485,  # powerburst
    486,  # avian
    487,  # saft
    488,  # gss-http
    489,  # nest-protocol
    490,  # micom-pfs
    491,  # go-login
    492,  # ticf-1
    493,  # ticf-2
    494,  # pov-ray
    495,  # intecourier
    496,  # pim-rp-disc
    497,  # retrospect
    498,  # siam
    499,  # ISO-ILL
    500,  # ISAKMP
    501,  # STMF
    502,  # Modbus
    503,  # Intrinsa
    504,  # Citadel
    505,  # mailbox-lm
    506,  # ohimsrv
    507,  # crs
    508,  # xvttp
    509,  # snare
    510,  # FirstClass
    511,  # PassGo
    512,  # exec
    513,  # login
    514,  # shell
    515,  # printer (LPD)
    516,  # videotex
    517,  # talk
    518,  # ntalk
    519,  # utime
    520,  # efs
    521,  # ripng
    522,  # ULP
    523,  # IBM-DB2
    524,  # NCP
    525,  # timed
    526,  # tempo
    527,  # STX
    528,  # CustIX
    529,  # IRC-SERV
    530,  # courier
    531,  # conference
    532,  # netnews
    533,  # netwall
    534,  # mm-admin
    535,  # iiop
    536,  # opalis-rdv
    537,  # nmsp
    538,  # gdomap
    539,  # apertus-ldp
    540,  # uucp
    541,  # uucp-rlogin
    542,  # commerce
    543,  # klogin
    544,  # kshell
    545,  # appleqtcsrvr
    546,  # dhcpv6-client
    547,  # dhcpv6-server
    548,  # AFP (Apple Filing)
    549,  # idfp
    550,  # new-rwho
    551,  # cybercash
    552,  # deviceshare
    553,  # pirp
    554,  # RTSP
    555,  # dsf
    556,  # remotefs
    557,  # openvms-sysipc
    558,  # sdnskmp
    559,  # teedtap
    560,  # rmonitor
    561,  # monitor
    562,  # chshell
    563,  # nntps
    564,  # 9pfs
    565,  # whoami
    566,  # streettalk
    567,  # banyan-rpc
    568,  # banyan-rpc
    569,  # ms-rome
    570,  # meter
    571,  # meter
    572,  # sonar
    573,  # banyan-vip
    574,  # ftp-agent
    575,  # vemmi
    576,  # ipcd
    577,  # vnas
    578,  # ipdd
    579,  # decbsrv
    580,  # sntp-heartbeat
    581,  # bdp
    582,  # scc-security
    583,  # philips-vc
    584,  # keyserver
    585,  # password-chg
    586,  # submission
    587,  # SMTP Submission
    588,  # cal
    589,  # eyelink
    590,  # tns-cml
    591,  # http-alt
    592,  # eudora-set
    593,  # http-rpc-epmap
    594,  # tpip
    595,  # cab-protocol
    596,  # smsd
    597,  # ptcnameservice
    598,  # sco-websrvrmg3
    599,  # acp
    600,  # ipcserver
    601,  # syslog-conn
    602,  # xmlrpc-beep
    603,  # mnotes
    604,  # tunnel
    605,  # soap-beep
    606,  # urm
    607,  # nqs
    608,  # sift-uft
    609,  # npmp-trap
    610,  # npmp-local
    611,  # npmp-gui
    612,  # HMMP-IND
    613,  # HMMP-OP
    614,  # SSLshell
    615,  # internet-config
    616,  # sco-sysmgr
    617,  # sco-dtmgr
    618,  # DEI-ICDA
    619,  # compaq-evm
    620,  # sco-websrvrmgr
    621,  # escp-ip
    622,  # collaborator
    623,  # ASF-RMCP
    624,  # cryptoadmin
    625,  # AppleShare IP
    626,  # AppleShare IP
    627,  # AppleShare IP
    628,  # AppleShare IP
    629,  # AppleShare IP
    630,  # AppleShare IP
    631,  # IPP (CUPS)
    632,  # bmpp
    633,  # servstat
    634,  # ginad
    635,  # rlzdbase
    636,  # LDAPS
    637,  # lanserver
    638,  # mcns-sec
    639,  # msdp
    640,  # entrust-sps
    641,  # repcmd
    642,  # esro-emsdp
    643,  # sanity
    644,  # dwr
    645,  # pssc
    646,  # ldp
    647,  # DHCP-Failover
    648,  # RRP
    649,  # cadview-3d
    650,  # obex
    651,  # ieee-mms
    652,  # hello-port
    653,  # repscmd
    654,  # aodv
    655,  # tinc
    656,  # spmp
    657,  # rmc
    658,  # tenfold
    659,  # mac-srvr-admin
    660,  # mac-srvr-admin
    661,  # hap
    662,  # pftp
    663,  # purenoise
    664,  # asf-secure-rmcp
    665,  # sun-dr
    666,  # doom / id Software
    667,  # disclose
    668,  # mecomm
    669,  # meregister
    670,  # vacdsm-sws
    671,  # vacdsm-app
    672,  # vpps-qua
    673,  # cimplex
    674,  # acap
    675,  # dctp
    676,  # vpps-via
    677,  # vpp
    678,  # ggf-ncp
    679,  # mrm
    680,  # entrust-aaas
    681,  # entrust-aams
    682,  # xfr
    683,  # corba-iiop
    684,  # corba-iiop-ssl
    685,  # mdc-portmapper
    686,  # hcp-wismar
    687,  # asipregistry
    688,  # realm-rusd
    689,  # nmap
    690,  # vatp
    691,  # msexch-routing
    692,  # hyperwave-isp
    693,  # connendp
    694,  # ha-cluster
    695,  # ieee-mms-ssl
    696,  # rushd
    697,  # uuidgen
    698,  # olsr
    699,  # accessnetwork
    700,  # epp
    701,  # lmp
    702,  # iris-beep
    703,  # beacon-ssl
    704,  # elcsd
    705,  # agentx
    706,  # silc
    707,  # borland-dsj
    708,  # entrust-kmsh
    709,  # entrust-ash
    710,  # cisco-tdp
    711,  # TBRPF
    712,  # TBRPF
    713,  # iris-xpc
    714,  # iris-xpcs
    715,  # iris-lwz
    716,  # pana
    717,  # pana
    718,  # pana
    719,  # pana
    720,  # pana
    721,  # pana
    722,  # pana
    723,  # pana
    724,  # pana
    725,  # pana
    726,  # pana
    727,  # pana
    728,  # pana
    729,  # pana
    730,  # pana
    731,  # pana
    732,  # pana
    733,  # pana
    734,  # pana
    735,  # pana
    736,  # pana
    737,  # pana
    738,  # pana
    739,  # pana
    740,  # pana
    741,  # pana
    742,  # pana
    743,  # pana
    744,  # pana
    745,  # pana
    746,  # pana
    747,  # pana
    748,  # pana
    749,  # pana
    750,  # pana
    751,  # pana
    752,  # pana
    753,  # pana
    754,  # pana
    755,  # pana
    756,  # pana
    757,  # pana
    758,  # pana
    759,  # pana
    760,  # pana
    761,  # pana
    762,  # pana
    763,  # pana
    764,  # pana
    765,  # pana
    766,  # pana
    767,  # pana
    768,  # pana
    769,  # pana
    770,  # pana
    771,  # pana
    772,  # pana
    773,  # pana
    774,  # pana
    775,  # pana
    776,  # pana
    777,  # pana
    778,  # pana
    779,  # pana
    780,  # pana
    781,  # pana
    782,  # pana
    783,  # pana
    784,  # pana
    785,  # pana
    786,  # pana
    787,  # pana
    788,  # pana
    789,  # pana
    790,  # pana
    791,  # pana
    792,  # pana
    793,  # pana
    794,  # pana
    795,  # pana
    796,  # pana
    797,  # pana
    798,  # pana
    799,  # pana
    800,  # pana
    801,  # pana
    802,  # pana
    803,  # pana
    804,  # pana
    805,  # pana
    806,  # pana
    807,  # pana
    808,  # pana
    809,  # pana
    810,  # pana
    811,  # pana
    812,  # pana
    813,  # pana
    814,  # pana
    815,  # pana
    816,  # pana
    817,  # pana
    818,  # pana
    819,  # pana
    820,  # pana
    821,  # pana
    822,  # pana
    823,  # pana
    824,  # pana
    825,  # pana
    826,  # pana
    827,  # pana
    828,  # pana
    829,  # pana
    830,  # pana
    831,  # pana
    832,  # pana
    833,  # pana
    834,  # pana
    835,  # pana
    836,  # pana
    837,  # pana
    838,  # pana
    839,  # pana
    840,  # pana
    841,  # pana
    842,  # pana
    843,  # pana
    844,  # pana
    845,  # pana
    846,  # pana
    847,  # pana
    848,  # pana
    849,  # pana
    850,  # pana
    851,  # pana
    852,  # pana
    853,  # pana
    854,  # pana
    855,  # pana
    856,  # pana
    857,  # pana
    858,  # pana
    859,  # pana
    860,  # pana
    861,  # pana
    862,  # pana
    863,  # pana
    864,  # pana
    865,  # pana
    866,  # pana
    867,  # pana
    868,  # pana
    869,  # pana
    870,  # pana
    871,  # pana
    872,  # pana
    873,  # pana
    874,  # pana
    875,  # pana
    876,  # pana
    877,  # pana
    878,  # pana
    879,  # pana
    880,  # pana
    881,  # pana
    882,  # pana
    883,  # pana
    884,  # pana
    885,  # pana
    886,  # pana
    887,  # pana
    888,  # pana
    889,  # pana
    890,  # pana
    891,  # pana
    892,  # pana
    893,  # pana
    894,  # pana
    895,  # pana
    896,  # pana
    897,  # pana
    898,  # pana
    899,  # pana
    900,  # pana
    901,  # pana
    902,  # pana
    903,  # pana
    904,  # pana
    905,  # pana
    906,  # pana
    907,  # pana
    908,  # pana
    909,  # pana
    910,  # pana
    911,  # pana
    912,  # pana
    913,  # pana
    914,  # pana
    915,  # pana
    916,  # pana
    917,  # pana
    918,  # pana
    919,  # pana
    920,  # pana
    921,  # pana
    922,  # pana
    923,  # pana
    924,  # pana
    925,  # pana
    926,  # pana
    927,  # pana
    928,  # pana
    929,  # pana
    930,  # pana
    931,  # pana
    932,  # pana
    933,  # pana
    934,  # pana
    935,  # pana
    936,  # pana
    937,  # pana
    938,  # pana
    939,  # pana
    940,  # pana
    941,  # pana
    942,  # pana
    943,  # pana
    944,  # pana
    945,  # pana
    946,  # pana
    947,  # pana
    948,  # pana
    949,  # pana
    950,  # pana
    951,  # pana
    952,  # pana
    953,  # pana
    954,  # pana
    955,  # pana
    956,  # pana
    957,  # pana
    958,  # pana
    959,  # pana
    960,  # pana
    961,  # pana
    962,  # pana
    963,  # pana
    964,  # pana
    965,  # pana
    966,  # pana
    967,  # pana
    968,  # pana
    969,  # pana
    970,  # pana
    971,  # pana
    972,  # pana
    973,  # pana
    974,  # pana
    975,  # pana
    976,  # pana
    977,  # pana
    978,  # pana
    979,  # pana
    980,  # pana
    981,  # pana
    982,  # pana
    983,  # pana
    984,  # pana
    985,  # pana
    986,  # pana
    987,  # pana
    988,  # pana
    989,  # pana
    990,  # pana
    991,  # pana
    992,  # pana
    993,  # pana
    994,  # pana
    995,  # pana
    996,  # pana
    997,  # pana
    998,  # pana
    999,  # pana
    1000, # pana
    1001, # pana
    1002, # pana
    1003, # pana
    1004, # pana
    1005, # pana
    1006, # pana
    1007, # pana
    1008, # pana
    1009, # pana
    1010, # pana
    1011, # pana
    1012, # pana
    1013, # pana
    1014, # pana
    1015, # pana
    1016, # pana
    1017, # pana
    1018, # pana
    1019, # pana
    1020, # pana
    1021, # pana
    1022, # pana
    1023, # pana
]

# ─── Дополнительные перспективные порты ────────────────────────────────────
# Порты, которые маскируются под известные протоколы, но не входят
# в стандартный блок-лист DPI

ADDITIONAL_PORTS = [
    # IoT / Smart Home
    1883,  # MQTT (plain)
    8883,  # MQTT over SSL
    5683,  # CoAP (UDP)
    5684,  # CoAP over DTLS
    
    # VPN / Tunnel протоколы (легитимные)
    1194,  # OpenVPN
    1723,  # PPTP
    1701,  # L2TP
    4500,  # IPsec NAT-T
    500,   # IPsec IKE
    
    # Apple / Google сервисы
    16384, # Apple Push (альтернативный)
    16385, # Apple Push
    16386, # Apple Push
    
    # Game серверы
    27015, # Steam / HLDS
    27016, # Steam
    27017, # Steam
    27018, # Steam
    27019, # Steam
    27020, # Steam
    27021, # Steam
    27022, # Steam
    27023, # Steam
    27024, # Steam
    27025, # Steam
    27026, # Steam
    27027, # Steam
    27028, # Steam
    27029, # Steam
    27030, # Steam
    27031, # Steam
    27032, # Steam
    27033, # Steam
    27034, # Steam
    27035, # Steam
    27036, # Steam
    
    # Microsoft / Windows
    3389,  # RDP
    5985,  # WinRM HTTP
    5986,  # WinRM HTTPS
    
    # Database
    3306,  # MySQL
    5432,  # PostgreSQL
    6379,  # Redis
    27017, # MongoDB
    
    # Enterprise
    8443,  # HTTPS alt (Tomcat)
    9443,  # HTTPS alt (WebSphere)
    10443, # HTTPS alt
    
    # Cloud / CDN
    6443,  # Kubernetes API
    10250, # Kubelet
    10255, # Kubelet (read-only)
    
    # Monitoring
    9090,  # Prometheus
    9100,  # Node Exporter
    3000,  # Grafana
    
    # SIP / VoIP
    5060,  # SIP
    5061,  # SIP over TLS
    
    # LDAP
    3268,  # Global Catalog
    3269,  # Global Catalog SSL
    
    # Docker
    2375,  # Docker REST API (plain)
    2376,  # Docker REST API (SSL)
    
    # Высокие порты (50000+)
    50001,
    50002,
    50003,
    50004,
    50005,
    50010,
    50020,
    50030,
    50040,
    50050,
    50100,
    50200,
    50300,
    50400,
    50500,
    51000,
    52000,
    53000,
    54000,
    55000,
    56000,
    57000,
    58000,
    59000,
    60000,
    61000,
    62000,
    63000,
    64000,
    65000,
    65535,
]

# ─── Well-known порты (1-1023) для полного сканирования ────────────────────

WELL_KNOWN_PORTS = list(range(1, 1024))

# ─── Функции ────────────────────────────────────────────────────────────────

def check_port(ip, port, timeout=3):
    """Проверяет, открыт ли TCP порт на сервере"""
    try:
        t0 = time.time()
        with socket.create_connection((ip, port), timeout=timeout) as sock:
            latency = round((time.time() - t0) * 1000)
            return {"port": port, "open": True, "latency_ms": latency, "error": None}
    except socket.timeout:
        return {"port": port, "open": False, "latency_ms": None, "error": "timeout"}
    except ConnectionRefusedError:
        return {"port": port, "open": False, "latency_ms": None, "error": "refused"}
    except OSError as e:
        return {"port": port, "open": False, "latency_ms": None, "error": str(e)[:50]}
    except Exception as e:
        return {"port": port, "open": False, "latency_ms": None, "error": str(e)[:50]}


def scan_ports(ip, ports, max_workers=50, name=""):
    """Сканирует список портов"""
    print(f"\n{'='*60}")
    print(f"  Сканирование {name} ({ip})")
    print(f"  Портов: {len(ports)}")
    print(f"  Время: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")
    
    open_ports = []
    checked = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(check_port, ip, p): p for p in ports}
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            checked += 1
            
            if result["open"]:
                open_ports.append(result)
                print(f"  ✅ Порт {result['port']:5d} — ОТКРЫТ ({result['latency_ms']}ms)")
            
            # Прогресс каждые 50 портов
            if checked % 50 == 0:
                print(f"  ... проверено {checked}/{len(ports)}")
    
    return open_ports


def print_report(server_name, server_ip, open_ports):
    """Выводит отчёт"""
    print(f"\n{'='*60}")
    print(f"  📊 ОТЧЁТ: {server_name} ({server_ip})")
    print(f"{'='*60}")
    
    if not open_ports:
        print("\n  ❌ Нет открытых портов")
        return
    
    print(f"\n  ✅ Найдено открытых портов: {len(open_ports)}")
    print()
    
    # Сортируем по порту
    open_ports.sort(key=lambda x: x["port"])
    
    # Группируем по диапазонам
    low = [p for p in open_ports if p["port"] < 1024]
    mid = [p for p in open_ports if 1024 <= p["port"] < 10000]
    high = [p for p in open_ports if p["port"] >= 10000]
    
    if low:
        print(f"  📋 Well-known порты (1-1023): {len(low)}")
        print(f"  {'─'*50}")
        for p in low:
            print(f"    {p['port']:5d}  ({p['latency_ms']}ms)")
    
    if mid:
        print(f"\n  📋 Средние порты (1024-9999): {len(mid)}")
        print(f"  {'─'*50}")
        for p in mid:
            print(f"    {p['port']:5d}  ({p['latency_ms']}ms)")
    
    if high:
       