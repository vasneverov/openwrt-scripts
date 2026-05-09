# VLESS ключи для роутера Ежов (cudy-01-ezhov)
# main = Fin3 (144.31.66.115) relay через 5.35.84.151:4191, gRPC+Reality
# yt   = bSPB  (5.35.84.151:8853), gRPC+Reality
#
# Инбаунд main: Fin3 panel ID=2, remark=WL_rout_fin3_4191
# Инбаунд YT:   begetspb panel ID=4, remark=bSPB_direct_8853
# DNAT relay:   5.35.84.151:4191 → 144.31.66.115:4191
# pbk main:     XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw  (sid=932e706c)
# pbk YT:       me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM  (sid=ddcb53b3)

cudy-01-ezhov_main=vless://e735be6a-7c0e-4de7-b1c2-230d00840c83@5.35.84.151:4191?type=grpc&security=reality&mode=gun&serviceName=&pbk=XJC_sc4MP6pFj2FNNGUu93SEoI6sKww2sCsh5prWWRw&sid=932e706c&sni=www.apple.com&fp=chrome&spx=%2F#e-zhov_main_Fin3
cudy-01-ezhov_yt=vless://f5dcf441-8818-48b2-9c36-24cae6458a9b@5.35.84.151:8853?type=grpc&security=reality&mode=gun&serviceName=&pbk=me9yoc9is4ZouFPS7e_TBjuBvyc8HZz6PCEogODIjSM&sid=ddcb53b3&sni=www.apple.com&fp=chrome&spx=%2F#e-zhov_yt_bSPB
