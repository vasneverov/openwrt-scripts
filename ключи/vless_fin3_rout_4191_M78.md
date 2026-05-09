# VLESS ключи для роутеров M78 серии
# main = Fin3 (144.31.66.115) relay через 5.35.84.151:4191, gRPC+Reality
# yt   = bSPB  (5.35.84.151:8853), gRPC+Reality
#
# Инбаунд main: Fin3 panel ID=2, remark=WL_rout_fin3_4191
# Инбаунд YT:   begetspb panel ID=4, remark=bSPB_direct_8853
# DNAT relay:   5.35.84.151:4191 → 144.31.66.115:4191
# pbk main:     XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw  (sid=932e706c)
# pbk YT:       me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM  (sid=ddcb53b3)

M78-04_main=vless://7903de08-9b9a-4813-ba80-19f48096df66@5.35.84.151:4191?type=grpc&security=reality&mode=gun&serviceName=&pbk=XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw&sid=932e706c&sni=www.apple.com&fp=chrome&spx=%2F#M78-04_fin3_rout
M78-04_yt=vless://73419cd1-bf11-4d6a-b1d1-377db91a4a37@5.35.84.151:8853?type=grpc&security=reality&mode=gun&serviceName=&pbk=me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM&sid=ddcb53b3&sni=www.apple.com&fp=chrome&spx=%2F#M78-04_bSPB
